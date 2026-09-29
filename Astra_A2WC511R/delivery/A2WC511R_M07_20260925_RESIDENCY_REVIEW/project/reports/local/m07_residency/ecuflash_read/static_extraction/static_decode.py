"""Bounded transforms of byte buffers only. Never load/execute the protected PE."""
import json
import re
import struct
import sys
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).parent
sys.path.insert(0,r'C:\Dev\Astra_A2WC511R\work\tools\m07_binary_audit')
import pefile
import capstone

def aplib_subset(data,limit=0x3FC000-0x14):
    """Translation of observed14100BF..1410208 literal/backreference machine."""
    pos=0;tag=0;bits=0;out=bytearray();last_offset=None;last_was_match=False;operations=0
    def byte():
        nonlocal pos
        if pos>=len(data):raise ValueError('truncated input')
        x=data[pos];pos+=1;return x
    def bit():
        nonlocal tag,bits
        if not bits:tag=byte();bits=8
        x=(tag>>7)&1;tag=(tag<<1)&255;bits-=1;return x
    def gamma():
        v=1
        for _ in range(32):
            v=(v<<1)|bit()
            if not bit():return v
        raise ValueError('gamma overflow')
    def append(v):
        if len(out)>=limit:raise ValueError('output section boundary exceeded')
        out.append(v)
    def copy(offset,length):
        if offset is None or not 0<offset<=len(out):raise ValueError('invalid backreference')
        if len(out)+length>limit:raise ValueError('output section boundary exceeded')
        for _ in range(length):append(out[-offset])
    append(byte())
    while True:
        operations+=1
        if operations>10000000:raise ValueError('operation limit')
        if not bit():
            append(byte());last_was_match=False;continue
        if bit():
            if bit():
                off=0
                for _ in range(4):off=(off<<1)|bit()
                if off:copy(off,1)
                else:append(0)
                last_was_match=False
            else:
                value=byte();off=value>>1
                if not off:break
                copy(off,2+(value&1));last_offset=off;last_was_match=True
        else:
            off=gamma()-(1 if last_was_match else 2)
            if off==0:copy(last_offset,gamma())
            else:
                off=((off-1)<<8)|byte();length=gamma()
                if off>=32000 or off<128:length+=2
                elif off>=1280:length+=1
                copy(off,length);last_offset=off
            last_was_match=True
    return bytes(out),pos,operations

source=HERE/'ecuflash.static-copy.exe'
b=source.read_bytes()
assert sha256(b).hexdigest()=='5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115'
pe=pefile.PE(data=b)
entry=pe.get_data(0x11D9000,0x70)
assert entry[:12].hex()=='565053e801000000cc5889c3'
assert entry[0x24:0x35].hex()=='bb00100000685d01522d68857b945e5350'
assert entry[0x5E:0x68].hex()=='3106011e83c60449ebf2'
stage=bytearray(pe.get_data(0x1010000,4096))
original=bytes(stage)
for a in range(0,4096,4):
    v=struct.unpack_from('<I',stage,a)[0]
    struct.pack_into('<I',stage,a,((v^0x5E947B85)+0x2D52015D)&0xFFFFFFFF)
# Inverse transform proves byte-for-byte round trip, independent of disassembly.
inverse=bytearray(stage)
for a in range(0,4096,4):
    v=struct.unpack_from('<I',inverse,a)[0]
    struct.pack_into('<I',inverse,a,((v-0x2D52015D)&0xFFFFFFFF)^0x5E947B85)
assert inverse==original
assert stage[:7].hex()=='60e80000000058'
assert stage[0x5E:0x6C].hex()=='b81440c10003c7b91202010103cf'
assert stage[0xBF:0xCB].hex()=='608b7424248b7c2428fcb280'
(HERE/'decoded_stage1_4096.bin').write_bytes(stage)
section=next(s for s in pe.sections if s.VirtualAddress==0x1010000)
stream=bytes(stage[0x212:])+pe.get_data(0x1011000,section.SizeOfRawData-4096)
out,consumed,ops=aplib_subset(stream)
(HERE/'decoded_stage2_loader.bin').write_bytes(out)
# Independent source implementation, installed side-by-side and hash pinned.
sys.path.insert(0,r'C:\Dev\Astra_A2WC511R\work\tools\m07_aplib')
import aplib
assert sha256(Path(aplib.__file__).read_bytes()).hexdigest()=='e35517800657b7f8548683675f7309d9413bf6d9b89a0619c26b3080ccada23c'
reference=aplib.APLib(stream,strict=True)
assert reference.depack()==out and reference.source.tell()==consumed
aplib.main()
(HERE/'aplib_crosscheck.json').write_text(json.dumps(dict(status='PASS',output_sha256=sha256(out).hexdigest(),
    bytes=len(out),input_consumed=consumed,module_sha256=sha256(Path(aplib.__file__).read_bytes()).hexdigest()),indent=2)+'\n')
# The next loader contains one explicit constant byte-decrement loop. Decode only
# that buffer, without following any exception-driven execution or OS calls.
assert out[0x1941:0x1952].hex()=='b9007000008dbd5219ba13fe0f474975fa'
stage3=bytearray(out)
for i in range(0x1952,0x1952+0x7000):stage3[i]=(stage3[i]-1)&255
(HERE/'decoded_stage3_loader.bin').write_bytes(stage3)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
rows=[dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in md.disasm(out[:512],0x1014014)]
(HERE/'decoded_stage2_entry.json').write_text(json.dumps(rows,indent=2)+'\n')
strings=[dict(offset=m.start(),text=m.group().decode()) for m in re.finditer(rb'[\x20-\x7e]{6,}',out)]
(HERE/'decoded_stage2_strings.json').write_text(json.dumps(strings,indent=2)+'\n')
tests=[]
for bad,limit in [(stream[:10],0x3FC000),(stream,16)]:
    try:aplib_subset(bad,limit)
    except ValueError:tests.append('PASS')
    else:raise AssertionError('invalid decompression accepted')
report=dict(executable_sha256=sha256(b).hexdigest(),transform=dict(input_rva='01010000',length=4096,
    operation='little-endian u32:((word XOR5E947B85)+2D52015D) mod2^32',input_sha256=sha256(original).hexdigest(),
    output_sha256=sha256(stage).hexdigest(),inverse_roundtrip='PASS'),
    decompressor=dict(source_code_va=['014100BF','01410209'],stream_rva='01010212',destination_rva='00C14014',
        compressed_bytes_consumed=consumed,decoded_bytes=len(out),output_sha256=sha256(out).hexdigest(),operations=ops,
        output_limit=0x3FC000-0x14,negative_controls=tests,independent_aplib_crosscheck='PASS'),
    next_transform=dict(code_va=['01015955','01015966'],buffer_va=['01015966','0101C966'],
        operation='Subtract1mod256 from eachof28672bytes.',output_sha256=sha256(stage3).hexdigest()),
    classification='STATIC_LOADER_BYTES_ONLY_NOT_APPLICATION_OR_KERNEL',native_execution=False)
(HERE/'static_decode.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
print('entry',rows[:12]);print('strings',strings[:20])
