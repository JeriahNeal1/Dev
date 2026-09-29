"""Build fixed native host from one reviewed new-project kernel manifest."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,subprocess,argparse
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import sha256,require,encrypt_upload,stock_entry_checksum,VERSION
OLD=Path(r'C:\Dev\Astra_A2WC511R')
FAKE_SOURCE=OLD/'work/ecuflash_dynamic/qualification_collision_native/native/a2wc_ecuflash_virtual32.dll'
FAKE_SHA='58be9aaad8e004eb5bd04a600e53394a1139752f1b698ca1832124dbbb4d5cc0'
HEADER_SOURCE=OLD/'integrations/ecuflash_virtual/vendor/j2534_tactrix.h'
HEADER_SHA='c559ea33654af59ad147eedfcccd56a1f2cb6e95daeb2412b53f6f4bbc76a7d9'

def copy_pinned(source,target,expected):
    data=source.read_bytes();require(sha256(data)==expected,'Pinned read-only input changed: '+str(source))
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():require(target.read_bytes()==data,'Existing scoped copy differs')
    else:
        with target.open('xb') as f:f.write(data)

def build(manifest_path,label):
    import re
    require(re.fullmatch('[A-Za-z0-9_-]{1,64}',label) is not None,'Simple build label')
    manifest_path=Path(manifest_path).resolve();require(manifest_path.is_relative_to(ROOT/'build'),'Kernel manifest must be in new project build tree')
    manifest=json.loads(manifest_path.read_text());sim=manifest
    path=Path(manifest['kernel_path']);path=path if path.is_absolute() else manifest_path.parent/path
    require(path.resolve().is_relative_to(ROOT/'build'),'Owned build kernel only')
    kernel=path.read_bytes();require(sha256(kernel)==manifest['kernel_sha256'],'Compiled kernel hash')
    require(8<=len(kernel)<=8192 and len(kernel)%4==0 and stock_entry_checksum(kernel)==0x5AA5,'Aligned fixed RAM upload/checksum')
    num=lambda v:int(v,0) if isinstance(v,str) else int(v)
    require(num(sim['load_address'])==0xFFFF3000 and num(sim['entry'])==0xFFFF3004,'Fixed stock load/entry')
    require(VERSION in kernel,'Project-specific version present')
    fake=ROOT/'fake/native/a2wc_readkernel_fake32.dll'
    header=ROOT/'host/vendor/j2534_tactrix.h'
    copy_pinned(FAKE_SOURCE,fake,FAKE_SHA);copy_pinned(HEADER_SOURCE,header,HEADER_SHA)
    out=ROOT/'host/build'/label;out.mkdir(parents=True,exist_ok=False)
    cipher=encrypt_upload(kernel)
    generated=out/'owned_artifact.h'
    generated.write_text('// Generated from exact owned build; not user-selectable at runtime.\n'
        +'static const wchar_t FAKE_DLL_PATH[]=L"'+str(fake).replace('\\','\\\\')+'";\n'
        +'static const char FAKE_DLL_SHA[]="'+FAKE_SHA+'";\n'
        +'static const char KERNEL_SHA[]="'+sha256(kernel)+'";\n'
        +'static const unsigned KERNEL_SIZE='+str(len(kernel))+'u;\n'
        +'static const unsigned char KERNEL_VERSION[]={'+','.join(str(b) for b in VERSION)+'};\n'
        +'static const unsigned char KERNEL_CIPHER[]={'+','.join('0x%02X'%b for b in cipher)+'};\n')
    setup=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat')
    command=out/'build.cmd';source=ROOT/'host/native.cpp'
    command.write_text('@echo off\ncall "'+str(setup)+'"\nif errorlevel 1 exit /b 1\ncl /nologo /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro /I"'+str(out)+'" "'+str(source)+'" /Fonative.obj /Feowned_read32.exe /link /Brepro bcrypt.lib\nif errorlevel 1 exit /b 1\n')
    result=subprocess.run(['cmd.exe','/d','/c',str(command)],cwd=out,capture_output=True,text=True)
    (out/'build.log').write_text(result.stdout+result.stderr)
    require(result.returncode==0,'Native compile failed; retained build.log')
    binary=out/'owned_read32.exe'
    test=subprocess.run([str(binary),'--selftest'],capture_output=True,text=True,timeout=10)
    (out/'selftest.log').write_text(test.stdout+test.stderr);require(test.returncode==0,'Native offline controls failed')
    binding={'schema':1,'kernel_path':str(path.resolve()),'kernel_sha256':sha256(kernel),
             'manifest_path':str(manifest_path),'manifest_sha256':sha256(manifest_path.read_bytes()),
             'client_path':str(binary),'client_sha256':sha256(binary.read_bytes()),
             'fake_path':str(fake),'fake_sha256':FAKE_SHA,'kernel_bytes':len(kernel),
             'load_address':'FFFF3000','entry_address':'FFFF3004','version_hex':VERSION.hex(),
             'physical':False,'physical_provider_supported':False}
    (out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    files=[source,Path(__file__),ROOT/'host/protocol.py',header,fake,generated,binary,command,out/'selftest.log',out/'build.log',out/'binding.json']
    report={'schema':1,'status':'PASS_NATIVE_FAKE_HOST_BUILD','physical':False,'binding':binding,
            'files':[{'path':str(p),'sha256':sha256(p.read_bytes())} for p in files]}
    (out/'BUILD_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return binding

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('manifest');parser.add_argument('label')
    args=parser.parse_args();build(args.manifest,args.label)
