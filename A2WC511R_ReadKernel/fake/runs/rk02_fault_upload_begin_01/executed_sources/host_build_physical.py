"""COMPILE ONLY: derive one fixed physical target after offline certification.

This script never launches the generated executable and never loads a provider.
It does not accept a provider path, kernel path, address or command selection.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,re,subprocess,difflib
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import require,sha256
from host.run import load_binding,record
CERTIFICATE=ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json'
REAL_DLL=Path(r'C:\Windows\SysWOW64\op20pt32.dll')
REAL_SHA='f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf'

def build(fake_label,label):
    require(re.fullmatch('[A-Za-z0-9_-]{1,64}',label) is not None,'Simple physical build label')
    binding=load_binding(fake_label);certificate_bytes=CERTIFICATE.read_bytes();certificate=json.loads(certificate_bytes)
    require(certificate.get('schema')==1 and certificate.get('artifact_class')=='TEMP_RAM_ACQUISITION_TOOL' and certificate.get('eligible') is True,'No eligible offline acquisition certificate')
    require(certificate['kernel_sha256']==binding['kernel_sha256'] and certificate['fake_host_sha256']==binding['client_sha256'],'Certificate must bind tested exact kernel/fake host')
    tested_build=ROOT/'host/build'/fake_label/'BUILD_MANIFEST.json'
    tested=json.loads(tested_build.read_text());tested_files={Path(item['path']):item['sha256'] for item in tested['files']}
    for path in (ROOT/'host/native.cpp',ROOT/'host/vendor/j2534_tactrix.h',ROOT/'host/build'/fake_label/'owned_artifact.h'):
        require(path in tested_files and sha256(path.read_bytes())==tested_files[path],'Exact tested source/header association before physical derivation: '+str(path))
    require(sha256(REAL_DLL.read_bytes())==REAL_SHA,'Installed provider read-only hash mismatch; never loaded')
    snapshot=ROOT/'preservation/snapshot_20260927/MANIFEST.json'
    entries=json.loads(snapshot.read_text())['files'];entry=[v for v in entries if Path(v['source'])==REAL_DLL]
    require(len(entry)==1 and entry[0]['sha256']==REAL_SHA and sha256(Path(entry[0]['snapshot']).read_bytes())==REAL_SHA,'Fresh provider snapshot association')
    out=ROOT/'host/physical_build'/label;out.mkdir(parents=True,exist_ok=False)
    base=(ROOT/'host/native.cpp').read_text()
    guard='''  need(argc==4&&wcscmp(argv[1],L"--acquire-owned-readkernel")==0&&wcscmp(argv[2],L"--certificate-sha256")==0&&wcscmp(argv[3],CERTIFICATE_SHA_W)==0,"Explicit acquisition flag and exact offline certificate SHA required before provider load");
  HANDLE certificateLock=CreateFileW(CERTIFICATE_PATH,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  need(certificateLock!=INVALID_HANDLE_VALUE,"Offline certificate file lock");
  need(sha_file(certificateLock)==CERTIFICATE_SHA,"Offline certificate changed; provider not loaded");'''
    replacements=[
        ('// Fixed purpose, native x86 host for ONE pinned project-local FAKE J2534 DLL.',
         '// COMPILE-ONLY PHYSICAL TARGET: fixed pinned OpenPort DLL; never executed during qualification.'),
        ('static int selftest(){','int uninvoked_offline_selftest(){'),
        ('  if(argc==2&&wcscmp(argv[1],L"--selftest")==0)return selftest();\n  need(argc==1,"No provider/kernel/address/opcode arguments accepted");',guard),
        ('// The only DLL path is a compile-time new-project path; no registration search.',
         '// Exact installed OpenPort path only after eligible certificate; no registration search.'),
        ('need(device==1,"Fixed fake device");','/* Successful API supplies opaque device ID. */'),
        ('need(channel==100,"Fixed fake channel");','/* Successful API supplies opaque channel ID. */'),
        ('mask.intact()&&pattern.intact()&&filter==1','mask.intact()&&pattern.intact()'),
        ('\\\"physical\\\":false','\\\"physical\\\":true'),
        ('PASS_NATIVE_FAKE_TWO_FULL_READS','PASS_NATIVE_FIXED_PHYSICAL_TWO_FULL_READS'),
        ('physical=false\\n','physical=true\\n'),
        ('FreeLibrary(dll);CloseHandle(locked);','FreeLibrary(dll);CloseHandle(locked);CloseHandle(certificateLock);')]
    physical=base;changes=[]
    for before,after in replacements:
        require(physical.count(before)==1,'Reviewed transformation not unique: '+before)
        physical=physical.replace(before,after,1);changes.append({'before':before,'after':after})
    restored=physical
    for before,after in reversed(replacements):
        require(restored.count(after)==1,'Transformation reverse not unique')
        restored=restored.replace(after,before,1)
    require(restored==base,'Unknown difference in fixed physical source')
    source=out/'native_physical.cpp';source.write_text(physical)
    (out/'SOURCE_DIFF.patch').write_text(''.join(difflib.unified_diff(base.splitlines(keepends=True),physical.splitlines(keepends=True),fromfile='tested_fake/native.cpp',tofile='never_executed_physical/native_physical.cpp')))
    header=(ROOT/'host/build'/fake_label/'owned_artifact.h').read_text();tested_header=header
    old_path=str(ROOT/'fake/native/a2wc_readkernel_fake32.dll').replace('\\','\\\\');new_path=str(REAL_DLL).replace('\\','\\\\')
    require(header.count(old_path)==1 and header.count(binding['fake_sha256'])==1,'Exact one provider path/hash in tested header')
    header=header.replace(old_path,new_path).replace(binding['fake_sha256'],REAL_SHA)
    require(header.replace(new_path,old_path).replace(REAL_SHA,binding['fake_sha256'])==tested_header,'All payload/ciphertext/header bytes outside provider binding exact')
    cert_sha=sha256(certificate_bytes)
    header+='\nstatic const wchar_t CERTIFICATE_PATH[]=L"'+str(CERTIFICATE).replace('\\','\\\\')+'";\n'
    header+='static const char CERTIFICATE_SHA[]="'+cert_sha+'";\nstatic const wchar_t CERTIFICATE_SHA_W[]=L"'+cert_sha+'";\n'
    (out/'owned_artifact.h').write_text(header)
    setup=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat')
    command=out/'compile_only.cmd'
    command.write_text('@echo off\ncall "'+str(setup)+'"\nif errorlevel 1 exit /b 1\ncl /nologo /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro /I"'+str(out)+'" /I"'+str(ROOT/'host')+'" "'+str(source)+'" /Fonative_physical.obj /Feowned_physical_read32.exe /link /Brepro bcrypt.lib\nif errorlevel 1 exit /b 1\n')
    result=subprocess.run(['cmd.exe','/d','/c',str(command)],cwd=out,capture_output=True,text=True)
    (out/'compile_only.log').write_text(result.stdout+result.stderr)
    require(result.returncode==0,'Physical compile failed; no executable launched')
    binary=out/'owned_physical_read32.exe'
    report={'schema':1,'status':'COMPILED_NEVER_EXECUTED_PHYSICAL_REQUIRED','artifact_class':'TEMP_RAM_ACQUISITION_TOOL',
            'target_physical':True,'executed':False,'provider_loaded_during_build':False,
            'certificate':{'path':str(CERTIFICATE),'sha256':cert_sha,'bytes':len(certificate_bytes)},'tested_fake_binding':binding,'real_provider_path':str(REAL_DLL),'real_provider_sha256':REAL_SHA,
            'tested_build_manifest':record(tested_build),'provider_binding_evidence':record(ROOT/'host/PHYSICAL_BINDING_PLAN.json'),
            'native_binary':record(binary),'source':record(source),'source_roundtrip_to_tested_fake_exact':True,
            'allowed_source_differences':changes,'protocol_payload_and_ciphertext_unchanged':True,
            'never_executed_not_even_selftest':True,
            'remaining':'Actual provider/electrical/ECU acceptance, timing, power-cycle/OEM restoration require human bench review',
            'files':[record(p) for p in (Path(__file__),source,out/'owned_artifact.h',command,out/'compile_only.log',binary,out/'SOURCE_DIFF.patch')]}
    (out/'BUILD_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('tested_fake_build');parser.add_argument('label')
    args=parser.parse_args();build(args.tested_fake_build,args.label)
