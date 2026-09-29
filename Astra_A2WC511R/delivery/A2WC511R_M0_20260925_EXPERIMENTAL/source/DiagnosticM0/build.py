"""Pinned SH-2E build: non-flash harness or explicitly unapproved experimental ELF."""
from pathlib import Path
import argparse, hashlib, json, struct, subprocess

ROOT = Path(__file__).resolve().parent
GNUSH = Path(r'C:\Program Files (x86)\Renesas\Hew\Tools\KPIT\GNUSH-ELF\v13.01\sh-elf\bin')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse_elf(path):
    data=path.read_bytes()
    assert data[:6]==b'\x7fELF\x01\x02' and struct.unpack_from('>H',data,18)[0]==42
    assert struct.unpack_from('>I',data,36)[0]&15==11
    shoff=struct.unpack_from('>I',data,32)[0]
    size,count,stridx=struct.unpack_from('>HHH',data,46)
    assert size==40
    sections=[struct.unpack_from('>10I',data,shoff+i*size) for i in range(count)]
    names=data[sections[stridx][4]:sections[stridx][4]+sections[stridx][5]]
    def name(table,off):return table[off:table.index(0,off)].decode('ascii')
    byname={name(names,s[0]):s for s in sections}
    m0=byname['.m0'];payload=data[m0[4]:m0[4]+m0[5]]
    symtab=byname['.symtab'];strings=sections[symtab[6]]
    symnames=data[strings[4]:strings[4]+strings[5]];symbols={}
    for off in range(symtab[4],symtab[4]+symtab[5],symtab[9]):
        n,val,length,info,other,idx=struct.unpack_from('>IIIBBH',data,off)
        nm=name(symnames,n)
        if nm.startswith('_m0_'):symbols[nm]=val
    return {'base':m0[3],'payload':payload,'symbols':symbols}

def build(out, experimental=False):
    out = out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit('Use a fresh output directory; no stale artifact reuse allowed')
    out.mkdir(parents=True, exist_ok=True)
    commands = []
    def run(argv, name):
        p = subprocess.run([str(a) for a in argv], cwd=out, capture_output=True, text=True, timeout=60)
        (out / (name+'.log')).write_text('ARGV '+json.dumps([str(a) for a in argv])+'\nEXIT '+str(p.returncode)+'\n'+p.stdout+'\nSTDERR\n'+p.stderr)
        commands.append({'argv':[str(a) for a in argv], 'returncode':p.returncode})
        if p.returncode:
            raise RuntimeError(name+' failed: '+p.stderr)
        return p.stdout
    cc, assembler, ld = (GNUSH / ('sh-elf-'+x+'.exe') for x in ('gcc','as','ld'))
    flags=['-m2e','-mb','-mrenesas','-mieee','-ffreestanding','-fno-builtin','-nostdinc','-Os','-fno-common','-fno-strict-aliasing','-fstack-usage','-Wall','-Wextra','-Werror','-std=c99','-I',str(ROOT),'-DTARGET_ECU=A2WC511R']
    objects=[]
    run([cc,'--version'],'compiler_version')
    for name in ('Diagnostic','Bindings','Identifier'):
        args=flags+['-S',str(ROOT/(name+'.c')),'-o',str(out/(name+'.s'))]
        response_args=[a.replace('\\','/') for a in args]
        (out/(name+'.gcc')).write_text('\n'.join('"'+a+'"' if ' ' in a else a for a in response_args)+'\n')
        run([cc,'@'+str(out/(name+'.gcc'))],name+'_compile')
        run([assembler,'-big','-renesas','--isa=sh2e',str(out/(name+'.s')),'-o',str(out/(name+'.o'))],name+'_assemble')
        objects.append(out/(name+'.o'))
    run([assembler,'-big','-renesas','--isa=sh2e',str(ROOT/'DecoderHook.s'),'-o',str(out/'DecoderHook.o')],'hook_assemble')
    objects.append(out/'DecoderHook.o')
    run([ld,'-EB','-r',*objects,'-o',str(out/'A2WC511R_DiagnosticM0.relocatable.o')],'relocatable_link')
    label='EXPERIMENTAL_UNAPPROVED' if experimental else 'HARNESS_ONLY'
    linker=ROOT/('experimental_only.ld' if experimental else 'harness_only.ld')
    elf=out/('A2WC511R_DiagnosticM0.'+label+'.elf')
    run([ld,'-EB','-T',str(linker),'-Map='+str(out/'harness.map'),*objects,'-o',str(elf)],'harness_link')
    dis=run([GNUSH/'sh-elf-objdump.exe','-d','-r','-t','-h',str(elf)],'disassembly')
    (out/'harness.disassembly.txt').write_text(dis)
    payload=out/('m0.'+label+'.code.bin')
    run([GNUSH/'sh-elf-objcopy.exe','-O','binary','-j','.m0',str(elf),str(payload)],'extract_harness_code')
    run([cc,*flags,'-E','-dM',str(ROOT/'Bindings.c')], 'effective_macros')
    header=elf.read_bytes()[:52]
    assert header[:6] == b'\x7fELF\x01\x02' and struct.unpack_from('>H',header,18)[0] == 42
    assert struct.unpack_from('>I',header,36)[0] & 15 == 11
    report={'target':'A2WC511R','ecuid':'2F12515306','auto_trans':1,'status':'COMPILED_'+label,
            'real_rom_allocation_accepted':False,'real_ram_allocation_accepted':False,'hook_abi_accepted':False,
            'ram_bytes':32,'code_base':'0x000E1000' if experimental else '0x07001000','ram_base':'0xFFFF7400' if experimental else '0x70000000',
            'code_bytes':payload.stat().st_size,'flags':flags,'commands':commands,
            'sources':{p.name:digest(p) for p in ROOT.iterdir() if p.suffix in ('.c','.h','.s','.ld','.py')},
            'tools':{str(p):digest(p) for p in (cc,assembler,ld,GNUSH/'sh-elf-objcopy.exe',GNUSH/'sh-elf-objdump.exe')},
            'artifacts':{p.name:digest(p) for p in out.iterdir() if p.suffix in ('.o','.elf','.bin','.map','.s','.su')}}
    parsed=parse_elf(elf);symbols=parsed['symbols']
    assert parsed['payload']==payload.read_bytes()
    assert all(k in symbols for k in ('_m0_decoder_hook','_m0_identifier','_m0_state','_m0_sample_hardware'))
    report['symbols']={k:hex(v) for k,v in symbols.items()}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','code_bytes','ram_bytes')}))
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True)
    p.add_argument('--experimental-unapproved-allocation',action='store_true',help='Only static/emulator engineering; never release approval')
    args=p.parse_args();build(args.out,args.experimental_unapproved_allocation)
