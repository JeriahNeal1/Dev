"""Independent pure comparison of the fixed RK02 physical source derivation.

verify(root, manifest, read_bytes) consumes only supplied bytes. It neither
imports the builder nor compiles/loads/executes any native program or provider.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,copy,difflib,hashlib,json

ROOT=Path(__file__).resolve().parents[2]
EXPECTED_ROOT=Path(r'C:\Dev\A2WC511R_ReadKernel')
PIN='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
HOST_SHA='4b681bcdb3c178b89382b37b207b4a7679f0a1e87ab13c7051e8cf8019c094ec'
REAL_DLL=Path(r'C:\Windows\SysWOW64\op20pt32.dll')
REAL_SHA='f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf'
FIXED={
 'host/build_physical.py':'e48ad9307bb7484c966833594a2e6d30ac285b160339c6dfaa43b2892e0a29ec',
 'host/native.cpp':'3e6b2e3b72697db9a7ed8143c47f706d4fa1ffa4125e341e8d24d6f89cf3e177',
 'host/build/native_05/owned_artifact.h':'2d281be105992b3e03971f2767464af7046ff30565e1ba76cf11e0c22787f12a',
 'host/build/native_05/binding.json':'c2022fd081d2f22313831c462627207241ea91ceb8d072273d7351aabcc39609',
 'host/build/native_05/BUILD_MANIFEST.json':'0bfe0b866c6575f1146b49b6b2b671ebaf34848191171d49bbffe4fbf07d15bd',
 'evidence/rk02/host/NATIVE_TOOLCHAIN.json':'cd89948c59d927252810e7e5ebd4d7c0f8845cc88fcf5415fe185792c2d8d36a'}
# The native source pin is the actually tested native05 input, not a field
# supplied by the physical build manifest.
GUARD='''  need(argc==4&&wcscmp(argv[1],L"--acquire-owned-readkernel")==0&&wcscmp(argv[2],L"--certificate-sha256")==0&&wcscmp(argv[3],CERTIFICATE_SHA_W)==0,"Explicit acquisition flag and exact offline certificate SHA required before provider load");
  HANDLE certificateLock=CreateFileW(CERTIFICATE_PATH,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  need(certificateLock!=INVALID_HANDLE_VALUE,"Offline certificate file lock");
  need(sha_file(certificateLock)==CERTIFICATE_SHA,"Offline certificate changed; provider not loaded");'''
REPLACEMENTS=(
 ('// Fixed purpose, native x86 host for ONE pinned project-local FAKE J2534 DLL.',
  '// COMPILE-ONLY PHYSICAL TARGET: fixed pinned OpenPort DLL; never executed during qualification.'),
 ('static int selftest(){','int uninvoked_offline_selftest(){'),
 ('  if(argc==2&&wcscmp(argv[1],L"--selftest")==0)return selftest();\n  need(argc==1,"No provider/kernel/address/opcode arguments accepted");',GUARD),
 ('// The only DLL path is a compile-time new-project path; no registration search.',
  '// Exact installed OpenPort path only after eligible certificate; no registration search.'),
 ('need(device==1,"Fixed fake device");','/* Successful API supplies opaque device ID. */'),
 ('need(channel==100,"Fixed fake channel");','/* Successful API supplies opaque channel ID. */'),
 ('mask.intact()&&pattern.intact()&&filter==1','mask.intact()&&pattern.intact()'),
 ('\\"physical\\":false','\\"physical\\":true'),
 ('PASS_NATIVE_FAKE_TWO_FULL_READS','PASS_NATIVE_FIXED_PHYSICAL_TWO_FULL_READS'),
 ('physical=false\\n','physical=true\\n'),
 ('FreeLibrary(dll);CloseHandle(locked);','FreeLibrary(dll);CloseHandle(locked);CloseHandle(certificateLock);'))

def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def text(b):
    value=b.decode('utf-8').replace('\r\n','\n')
    need('\r' not in value,'Unsupported standalone CR in source text')
    return value
def windows(value):return value.replace('\n','\r\n').encode('utf-8')
def ref(p,b):return {'path':str(p),'bytes':len(b),'sha256':sha(b)}

def expected(root,base,header,certificate,binding,toolchain):
    """Reviewed fixed transformation; never accepts manifest replacement rules."""
    source=text(base);physical=source
    for before,after in REPLACEMENTS:
        need(physical.count(before)==1,'Nonunique fixed source transformation')
        physical=physical.replace(before,after,1)
    inverse=physical
    for before,after in reversed(REPLACEMENTS):
        need(inverse.count(after)==1,'Nonunique fixed source inverse')
        inverse=inverse.replace(after,before,1)
    need(inverse==source,'Fixed inverse did not recover tested source')
    original=text(header);h=original
    fake=str(root/'fake/native/a2wc_readkernel_fake32.dll').replace('\\','\\\\')
    real=str(REAL_DLL).replace('\\','\\\\')
    need(h.count(fake)==1 and h.count(binding['fake_sha256'])==1,'Nonunique provider header fields')
    h=h.replace(fake,real).replace(binding['fake_sha256'],REAL_SHA)
    need(h.replace(real,fake).replace(REAL_SHA,binding['fake_sha256'])==original,'Header changed outside provider constants')
    cert_path=root/'OFFLINE_SOFTWARE_CERTIFICATE.json';cert_sha=sha(certificate)
    h+='\nstatic const wchar_t CERTIFICATE_PATH[]=L"'+str(cert_path).replace('\\','\\\\')+'";\n'
    h+='static const char CERTIFICATE_SHA[]="'+cert_sha+'";\nstatic const wchar_t CERTIFICATE_SHA_W[]=L"'+cert_sha+'";\n'
    out=root/'host/physical_build/rk02_physical_01';source_path=out/'native_physical.cpp'
    setup=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat')
    need(Path(toolchain['vcvars32']['path'])==setup,'Unexpected vcvars32 path')
    compiler=Path(toolchain['compiler']['path'])
    command='@echo off\ncall "'+str(setup)+'"\nif errorlevel 1 exit /b 1\nwhere.exe link.exe > resolved_linker.txt\n"'+str(compiler)+'" /nologo /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro /I"'+str(out)+'" /I"'+str(root/'host')+'" "'+str(source_path)+'" /Fonative_physical.obj /Feowned_physical_read32.exe /link /Brepro bcrypt.lib\nif errorlevel 1 exit /b 1\n'
    diff=''.join(difflib.unified_diff(source.splitlines(keepends=True),physical.splitlines(keepends=True),
      fromfile='tested_fake/native.cpp',tofile='never_executed_physical/native_physical.cpp'))
    return {'native_physical.cpp':windows(physical),'owned_artifact.h':windows(h),
      'SOURCE_DIFF.patch':windows(diff),'compile_only.cmd':windows(command)}

def verify(root,manifest,read_bytes):
    """Return PASS/FAIL. read_bytes must enforce the caller's evidence seal."""
    inputs={}
    try:
        root=Path(root).resolve();need(root==EXPECTED_ROOT,'Unexpected project root')
        out=root/'host/physical_build/rk02_physical_01'
        def take(p):
            p=(root/Path(p)).resolve();raw=read_bytes(p);need(isinstance(raw,bytes),'Reader must return bytes')
            inputs[str(p)]=ref(p,raw);return raw
        fixed={n:take(root/n) for n in FIXED}
        for name,digest in FIXED.items():need(sha(fixed[name])==digest,'Reviewed input changed: '+name)
        binding=json.loads(fixed['host/build/native_05/binding.json'])
        tested=json.loads(fixed['host/build/native_05/BUILD_MANIFEST.json'])
        toolchain=json.loads(fixed['evidence/rk02/host/NATIVE_TOOLCHAIN.json'])
        need(tested['binding']==binding,'Native05 build/binding mismatch')
        need(binding['kernel_sha256']==PIN and binding['client_sha256']==HOST_SHA,'Tested identity mismatch')
        need(binding['version_hex']==b'A2WC511R-RK02\0'.hex() and binding['kernel_bytes']==1808,'Tested payload version/size mismatch')
        cert_path=root/'OFFLINE_SOFTWARE_CERTIFICATE.json';certificate=take(cert_path);cert=json.loads(certificate)
        required={'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','eligible':True,
          'kernel_sha256':PIN,'fake_host_sha256':HOST_SHA,'kernel_version':'A2WC511R-RK02',
          'load_address':'FFFF3000','entry':'FFFF3004','fixed_block_bytes':512,'passes':2,
          'ECU_identity':'2F12515306','physical_operations_performed':False,'not_an_ECU_ROM_release':True}
        for field,value in required.items():need(cert[field]==value,'Certificate fixed field mismatch: '+field)
        d=manifest
        need(d['status']=='COMPILED_NEVER_EXECUTED_PHYSICAL_REQUIRED' and d['artifact_class']=='TEMP_RAM_ACQUISITION_TOOL','Physical manifest class/status mismatch')
        need(d['executed'] is False and d['provider_loaded_during_build'] is False and d['never_executed_not_even_selftest'] is True,'Execution claim is not compile-only')
        need(d['tested_fake_binding']==binding,'Physical manifest changes tested binding')
        need(Path(d['real_provider_path'])==REAL_DLL and d['real_provider_sha256']==REAL_SHA,'Provider binding changed')
        need(d['allowed_source_differences']==[{'before':a,'after':b} for a,b in REPLACEMENTS],'Unknown or missing transformation rule')
        need(d['source_roundtrip_to_tested_fake_exact'] is True and d['protocol_payload_and_ciphertext_unchanged'] is True,'Missing derivation claims')
        refs={'certificate':cert_path,'tested_build_manifest':root/'host/build/native_05/BUILD_MANIFEST.json',
          'native_toolchain':root/'evidence/rk02/host/NATIVE_TOOLCHAIN.json',
          'provider_binding_evidence':root/'host/PHYSICAL_BINDING_PLAN.json',
          'source':out/'native_physical.cpp','native_binary':out/'owned_physical_read32.exe'}
        for field,p in refs.items():
            item=d[field];need(Path(item['path']).resolve()==p,'Unexpected '+field+' reference path')
            need(ref(p,take(p))==item,'Reference hash/size mismatch: '+field)
        need(d['compiler']==toolchain['compiler'] and d['linker']==toolchain['linker'],'Native toolchain declaration changed')
        names={'native_physical.cpp','owned_artifact.h','compile_only.cmd','compile_only.log','resolved_linker.txt','owned_physical_read32.exe','SOURCE_DIFF.patch'}
        paths={out/n for n in names}|{root/'host/build_physical.py'}
        need(len(d['files'])==len(paths) and {Path(x['path']).resolve() for x in d['files']}==paths,'Incomplete or duplicate physical manifest files')
        for item in d['files']:
            p=Path(item['path']).resolve();need(ref(p,take(p))==item,'Physical file hash/size mismatch')
        computed=expected(root,fixed['host/native.cpp'],fixed['host/build/native_05/owned_artifact.h'],certificate,binding,toolchain)
        for name,raw in computed.items():need(take(out/name)==raw,'Independent reconstructed bytes differ: '+name)
        selected=text(take(out/'resolved_linker.txt')).splitlines()
        need(bool(selected) and Path(selected[0])==Path(toolchain['linker']['path']),'Recorded selected linker differs')
        return {'schema':1,'status':'PASS','kernel_sha256':PIN,'errors':[],
          'checks':['Fixed native05, header, builder and toolchain identities','Exactly eleven source replacements and exact inverse',
            'Exact provider/certificate header with unchanged payload and ciphertext','Exact source diff and compile command',
            'Exact paths, binding and complete eight-file physical manifest'],
          'inputs':list(inputs.values()),'native_execution':False,'provider_loaded':False,
          'scope':'Independent text/binding derivation. Native binary compilation provenance remains a separate pinned-toolchain build check; this function does not execute the binary.'}
    except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError) as error:
        return {'schema':1,'status':'FAIL','kernel_sha256':PIN,'errors':[type(error).__name__+': '+str(error)],
          'inputs':list(inputs.values()),'native_execution':False,'provider_loaded':False}

def self_test(report):
    """Create synthetic derivative bytes in memory; never write build outputs."""
    original={str((ROOT/n).resolve()):(ROOT/n).read_bytes() for n in FIXED}
    plan=ROOT/'host/PHYSICAL_BINDING_PLAN.json';original[str(plan)]=plan.read_bytes()
    binding=json.loads(original[str(ROOT/'host/build/native_05/binding.json')])
    toolchain=json.loads(original[str(ROOT/'evidence/rk02/host/NATIVE_TOOLCHAIN.json')])
    cert={'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','eligible':True,'kernel_sha256':PIN,
      'fake_host_sha256':HOST_SHA,'kernel_version':'A2WC511R-RK02','load_address':'FFFF3000','entry':'FFFF3004',
      'fixed_block_bytes':512,'passes':2,'ECU_identity':'2F12515306','physical_operations_performed':False,'not_an_ECU_ROM_release':True}
    cert_path=ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json';original[str(cert_path)]=(json.dumps(cert,indent=2)+'\n').encode()
    out=ROOT/'host/physical_build/rk02_physical_01'
    derived=expected(ROOT,original[str(ROOT/'host/native.cpp')],original[str(ROOT/'host/build/native_05/owned_artifact.h')],original[str(cert_path)],binding,toolchain)
    for name,raw in derived.items():original[str(out/name)]=raw
    original[str(out/'compile_only.log')]=b'SYNTHETIC; no compiler invocation.\r\n'
    original[str(out/'resolved_linker.txt')]=windows(toolchain['linker']['path']+'\n')
    original[str(out/'owned_physical_read32.exe')]=b'SYNTHETIC_NONEXECUTABLE_PLACEHOLDER'
    def item(p):return ref(p,original[str(p)])
    names=['native_physical.cpp','owned_artifact.h','compile_only.cmd','compile_only.log','resolved_linker.txt','owned_physical_read32.exe','SOURCE_DIFF.patch']
    manifest={'status':'COMPILED_NEVER_EXECUTED_PHYSICAL_REQUIRED','artifact_class':'TEMP_RAM_ACQUISITION_TOOL',
      'executed':False,'provider_loaded_during_build':False,'never_executed_not_even_selftest':True,
      'tested_fake_binding':binding,'real_provider_path':str(REAL_DLL),'real_provider_sha256':REAL_SHA,
      'allowed_source_differences':[{'before':a,'after':b} for a,b in REPLACEMENTS],
      'source_roundtrip_to_tested_fake_exact':True,'protocol_payload_and_ciphertext_unchanged':True,
      'certificate':item(cert_path),'tested_build_manifest':item(ROOT/'host/build/native_05/BUILD_MANIFEST.json'),
      'native_toolchain':item(ROOT/'evidence/rk02/host/NATIVE_TOOLCHAIN.json'),'provider_binding_evidence':item(plan),
      'source':item(out/'native_physical.cpp'),'native_binary':item(out/'owned_physical_read32.exe'),
      'compiler':toolchain['compiler'],'linker':toolchain['linker'],
      'files':[item(ROOT/'host/build_physical.py')]+[item(out/n) for n in names]}
    def evaluate(d,data):return verify(ROOT,d,lambda p:data[str(p)])
    positive=evaluate(manifest,original);cases=[]
    def run(name,mutate):
        d=copy.deepcopy(manifest);data=dict(original);mutate(d,data)
        # Deliberately refresh all manifest hashes. Unknown edits must fail
        # the reconstructed contract, not merely a stale file hash.
        for row in d['files']:
            if row['path'] in data:row.update(ref(Path(row['path']),data[row['path']]))
        for field in ('certificate','source','native_binary'):
            row=d[field]
            if row['path'] in data:row.update(ref(Path(row['path']),data[row['path']]))
        result=evaluate(d,data);cases.append({'case':name,'status':'PASS' if result['status']=='FAIL' else 'FAIL','rejection':result['errors']})
    run('unreviewed_source_edit',lambda d,b:b.__setitem__(str(out/'native_physical.cpp'),b[str(out/'native_physical.cpp')]+b'// extra\r\n'))
    run('source_guard_removed',lambda d,b:b.__setitem__(str(out/'native_physical.cpp'),b[str(out/'native_physical.cpp')].replace(b'argc==4',b'argc>=1',1)))
    run('header_payload_changed',lambda d,b:b.__setitem__(str(out/'owned_artifact.h'),b[str(out/'owned_artifact.h')].replace(b'KERNEL_CIPHER[]={0x21',b'KERNEL_CIPHER[]={0x20',1)))
    run('header_certificate_constant_changed',lambda d,b:b.__setitem__(str(out/'owned_artifact.h'),b[str(out/'owned_artifact.h')].replace(sha(b[str(cert_path)]).encode(),b'0'*64,1)))
    run('compile_command_extra_define',lambda d,b:b.__setitem__(str(out/'compile_only.cmd'),b[str(out/'compile_only.cmd')].replace(b' /O2 ',b' /O2 /DUNREVIEWED ',1)))
    run('source_diff_changed',lambda d,b:b.__setitem__(str(out/'SOURCE_DIFF.patch'),b''))
    run('source_rules_empty',lambda d,b:d.__setitem__('allowed_source_differences',[]))
    run('files_empty',lambda d,b:d.__setitem__('files',[]))
    run('file_duplicate',lambda d,b:d['files'].__setitem__(1,copy.deepcopy(d['files'][0])))
    run('provider_path_changed',lambda d,b:d.__setitem__('real_provider_path',r'C:\Dev\other.dll'))
    run('provider_hash_changed',lambda d,b:d.__setitem__('real_provider_sha256','0'*64))
    run('binding_changed',lambda d,b:d['tested_fake_binding'].__setitem__('client_sha256','0'*64))
    run('source_reference_redirected',lambda d,b:d['source'].__setitem__('path',str(out/'owned_artifact.h')))
    run('certificate_ineligible',lambda d,b:b.__setitem__(str(cert_path),json.dumps({**cert,'eligible':False}).encode()))
    run('wrong_linker_selected',lambda d,b:b.__setitem__(str(out/'resolved_linker.txt'),b'C:\\wrong\\link.exe\r\n'))
    result={'schema':1,'status':'PASS' if positive['status']=='PASS' and all(x['status']=='PASS' for x in cases) else 'FAIL',
      'kernel_sha256':PIN,'checker':ref(Path(__file__),Path(__file__).read_bytes()),
      'positive':positive,'cases':cases,'negative_count':len(cases),
      'scope':'Synthetic in-memory source/header/manifest contract only. The EXE and compile log are visibly nonexecuted synthetic placeholders; no actual physical build qualification is claimed.',
      'actual_inputs':[ref(ROOT/n,(ROOT/n).read_bytes()) for n in FIXED],
      'builder_invocations':0,'native_execution':False,'provider_loaded':False,'physical_operations':0}
    with report.open('x',encoding='utf-8') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'negative_count':len(cases),'report':str(report),'sha256':sha(report.read_bytes())}))
    return result['status']!='PASS'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--self-test-report',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(self_test(args.self_test_report))
