"""Compile a standalone SH-2E temporary RAM object; never create an ECU ROM."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,json,re,struct,subprocess,datetime
ROOT=Path(__file__).resolve().parents[1]
TOOLS=Path(r'C:\Program Files (x86)\Renesas\Hew\Tools\KPIT\GNUSH-ELF\v13.01\sh-elf\bin')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build(name):
    if not re.fullmatch('[A-Za-z0-9_-]+',name):raise ValueError('Simple unique build name')
    out=ROOT/'build'/name;out.mkdir(parents=True,exist_ok=False)
    calls=[]
    def run(args,log):
        args=[str(a) for a in args]
        r=subprocess.run(args,capture_output=True,text=True,cwd=out)
        (out/log).write_text(r.stdout+r.stderr,encoding='utf-8')
        calls.append({'argv':args,'exit_code':r.returncode,'log':log})
        r.check_returncode();return r.stdout
    tools={n:{'path':str(TOOLS/(n+'.exe')),'sha256':sha(TOOLS/(n+'.exe'))}
           for n in ('sh-elf-gcc','sh-elf-as','sh-elf-ld','sh-elf-objcopy','sh-elf-objdump','sh-elf-nm')}
    if tools['sh-elf-gcc']['sha256']!='55efba44b61d6a1e00187d605a44cee3d7e77c89d442e7ef24a67a8b2a3ed810':raise ValueError('Pinned KPIT compiler mismatch')
    run([TOOLS/'sh-elf-gcc.exe','--version'],'compiler_version.txt')
    run([TOOLS/'sh-elf-as.exe','-big','-renesas','--isa=sh2e',ROOT/'src/kernel.S','-o','kernel.o'],'assemble.log')
    def link(value,stem):
        run([TOOLS/'sh-elf-ld.exe','-EB','-T',ROOT/'linker/kernel.ld','--defsym',f'loader_checksum={value}',
             '-Map',stem+'.map','-o',stem+'.elf','kernel.o'],stem+'.link.log')
        run([TOOLS/'sh-elf-objcopy.exe','-O','binary','-j','.entry','-j','.text','-j','.rodata','-j','.vectors','-j','.integrity',
             stem+'.elf',stem+'.bin'],stem+'.extract.log')
        return (out/(stem+'.bin')).read_bytes()
    provisional=link(0,'provisional')
    assert len(provisional)%4==0 and len(provisional)<8192
    value=(0x5aa5-sum(struct.unpack('>'+str(len(provisional)//4)+'I',provisional)))&0xffff
    binary=link(value,'kernel')
    assert sum(struct.unpack('>'+str(len(binary)//4)+'I',binary))&0xffff==0x5aa5
    elf=(out/'kernel.elf').read_bytes()
    assert elf[:6]==b'\x7fELF\x01\x02' and struct.unpack_from('>H',elf,18)[0]==42
    entry=struct.unpack_from('>I',elf,24)[0];flags=struct.unpack_from('>I',elf,36)[0]
    assert entry==0xffff3004 and flags&31==11, (hex(entry),hex(flags))
    dis=run([TOOLS/'sh-elf-objdump.exe','-d','-msh2e','kernel.elf'],'kernel.disassembly.txt')
    run([TOOLS/'sh-elf-objdump.exe','-h','-s','kernel.elf'],'kernel.sections.txt')
    nm=run([TOOLS/'sh-elf-nm.exe','-an','kernel.elf'],'kernel.symbols.txt')
    symbols={m[3]:int(m[1],16) for line in nm.splitlines() if (m:=re.fullmatch(r'([0-9a-fA-F]+)\s+(\S)\s+(.+)',line))}
    instructions=[]
    for line in dis.splitlines():
        if m:=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{2}) ([0-9a-f]{2})\s+(.+)',line):
            a=int(m[1],16)
            if entry<=a<symbols['code_end']:
                instructions.append({'address':a,'opcode':int(m[2]+m[3],16),'assembly':m[4].strip()})
    assert len(instructions)*2==symbols['code_end']-entry
    assert all(x['assembly'].split()[0] not in ('.word','fmov','fadd','fmul','fdiv') for x in instructions)
    manifest={'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','name':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'physical_operations':False,'ECU_flash_image':False,'target':{'cpu':'SH-2E','mcu':'SH7058','endian':'big','ELF_flags':flags},
        'kernel_path':str(out/'kernel.bin'),'kernel_sha256':sha(out/'kernel.bin'),'kernel_bytes':len(binary),
        'load_address':0xffff3000,'entry':entry,'upload_end':symbols['upload_end'],
        'symbols':symbols,'instruction_addresses':[x['address'] for x in instructions],'instructions':instructions,
        'executable_ranges':[[entry,symbols['code_end']]],'unreachable_header':{'range':[0xffff3000,entry],'reason':'Fixed stock loader entry skips two header NOPs.'},
        'private_ram_ranges':[[symbols['work_start'],symbols['work_end']]],
        'stack_low':symbols['stack_low'],'stack_high':symbols['stack_top'],'inherited_sp':0xffffbfa0,
        'vector_base':symbols['vector_table'],'vector_size':1024,'rx_poll':symbols['rx_poll'],
        'halt_fail':symbols['halt_fail'],'halt_complete':symbols['halt_complete'],'halt_exception':symbols['halt_exception'],
        'ram_layout':[{'role':'uploaded_code_constants_vectors_checksum','start':0xffff3000,'end':symbols['upload_end'],'writable_after_entry':False},
                      {'role':'private_rx_guards_exception_stack','start':symbols['work_start'],'end':symbols['work_end'],'writable_after_entry':True}],
        'protocol':{'identity_ascii':'A2WC511R-RK02\u0000','identity_hex':b'A2WC511R-RK02\0'.hex(),'commands':[1,3],
                    'read_request_body_bytes':8,'read_response_body_bytes':518,'block_bytes':512,'ROM_range':[0,0x100000],'passes':2,
                    'strict_sequential':True,'CRC_substitution':False},
        'loader_checksum':{'word_address':symbols['upload_checksum_word'],'word_value':value,'BE32_sum_low16':0x5aa5},
        'sources':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'src/kernel.S',ROOT/'linker/kernel.ld',Path(__file__).resolve()]},
        'toolchain':tools,'commands':calls,'elf_sha256':sha(out/'kernel.elf')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':str(out/'manifest.json'),'kernel_bytes':len(binary),'instructions':len(instructions),
        'kernel_sha256':manifest['kernel_sha256'],'takeover_end':hex(symbols['takeover_end'])}))
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');build(p.parse_args().name)
