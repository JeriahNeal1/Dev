"""Static binary evidence only; no executable, DLL or kernel is executed."""
import json
import math
import re
import sys
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).parent
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
sys.path.insert(0,str(ROOT/'work/tools/m07_binary_audit'))
import pefile
import capstone

exe=Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe')
pe=pefile.PE(str(exe))
entry=pe.OPTIONAL_HEADER.AddressOfEntryPoint
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
rows=[dict(address=f'{i.address:08X}', bytes=i.bytes.hex(), mnemonic=i.mnemonic, operands=i.op_str)
      for i in md.disasm(pe.get_data(entry,512),pe.OPTIONAL_HEADER.ImageBase+entry)]
(HERE/'installed_entry_disassembly.json').write_text(json.dumps(rows,indent=2)+'\n')

def entropy(b):
    return -sum(n/len(b)*math.log2(n/len(b)) for n in Counter(b).values())
sections=[dict(name=s.Name.hex(),raw_size=s.SizeOfRawData,entropy=entropy(s.get_data())) for s in pe.sections]

kernel=ROOT/'work/M07_reference/FastECU/kernels/ssmk_kline_sh7058.bin'
data=kernel.read_bytes()
# Exact byte guard on the reference kernel's bounded entry, independent from
# source lineage. The backward loop decrements r1 and stores0 until r1==r0.
assert data[:0x1A].hex()=='00090009d108d007e20031008901affc2124d103df01410b0009'
be32=lambda off:int.from_bytes(data[off:off+4],'big')
stack,main,bss_begin,bss_end=[be32(i) for i in (0x1C,0x20,0x24,0x28)]
assert (stack,main,bss_begin,bss_end)==(0xFFFFBFFC,0xFFFF3FE4,0xFFFF47A8,0xFFFF6CF8)
assert bss_begin < bss_end and (bss_end-bss_begin)==0x2550
# Negative guard: changing any protected entry byte invalidates identity.
mutated=bytearray(data)
mutated[0x10]^=1
assert mutated[:0x1A] != data[:0x1A]
six=(0xFFFF4C75,0xFFFF4C8D,0xFFFF4CA1,0xFFFF4C50,0xFFFF4BC1,0xFFFF4BC2)
references=[
 ROOT/'work/M07_reference/FastECU/modules/ecu/flash_ecu_subaru_denso_sh705x_kline.cpp',
 ROOT/'work/M07_reference/FastECU/kernelcomms.h',ROOT/'work/M07_reference/FastECU/config/protocols.cfg',
 ROOT/'work/M07_reference/FastECU-kernels/main.c',ROOT/'work/M07_reference/FastECU-kernels/start_ssm.s',
 ROOT/'work/M07_reference/FastECU-kernels/mfg_ssm.c',ROOT/'work/M07_reference/FastECU-kernels/cmd_parser.c',
 ROOT/'work/M07_reference/FastECU-kernels/pl_flash_705x_180nm.c']
installed=[exe,
 Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\rommetadata\read templates\read_sti05.xml'),
 Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\rommetadata\subaru\Outback XT\A2WC511R.xml'),
 Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\drivers\openport 2.0\op20pt32.dll')]
historical=[]
for p in (ROOT/'evidence/original').glob('ECUFlashRead*.bin'):
    d=p.read_bytes()
    historical.append(dict(path=str(p),size=len(d),sha256=sha256(d).hexdigest(),
       gap_checks=[dict(start=f'{a:06X}',end=f'{b:06X}',all_FF=(d[a:b]==b'\xff'*(b-a))) for a,b in ((0x86000,0xC0000),(0xCF000,0xFF000))] if len(d)==0x100000 else []))
out=dict(status='INSTALLED_INTERNAL_READ_IMPLEMENTATION_UNRESOLVED',
         installed_hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in installed},
         PE_entry_rva=f'{entry:08X}',entry_disassembly_sha256=sha256((HERE/'installed_entry_disassembly.json').read_bytes()).hexdigest(),
         sections=sections,
         packed_inference='High-entropy executable content, irregular expanded sections, two imports, and absent application/kernel strings support packed/obfuscated representation. Exact packer not established.',
         reference_kernel=dict(path=str(kernel),sha256=sha256(data).hexdigest(),size=len(data),
             version_strings=[m.group().decode() for m in re.finditer(rb'FastECU[^\x00]{5,80}',data)],
             bounded_entry_regression='PASS',stack=f'{stack:08X}',main=f'{main:08X}',
             BSS_clear_halfopen=[f'{bss_begin:08X}',f'{bss_end:08X}'],BSS_clear_bytes=bss_end-bss_begin,
             six_TCU_addresses_cleared=[f'{a:08X}' for a in six if bss_begin<=a<bss_end],
             provenance_limit='Different kernel from installed historical DUAL V1.07, different length; no installed-kernel equivalence claimed. Current FastECU-kernels source was not rebuilt or matched to this binary.'),
         reference_source_hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in references},
         historical_images=historical,
         no_execution=['No EcuFlash process launched','No provider DLL loaded','No kernel executed','No hardware connection','No flash or RAM device write'])
(HERE/'binary_boundaries.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('installed_hashes','reference_source_hashes','sections')},indent=2))
