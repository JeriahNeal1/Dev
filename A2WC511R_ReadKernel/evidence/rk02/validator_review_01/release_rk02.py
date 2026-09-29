"""Seal completed RK02 tests. No executable/provider is launched here."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,json
from validate import ROOT,PIN,FIXTURES,FIXED_GATES,PHYSICAL_IDS,validate
from verify_preservation import verify_all

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def write(p,d):
    with Path(p).open('x',encoding='utf-8') as f:f.write(json.dumps(d,indent=2)+'\n')
def rel(p):
    p=Path(p).resolve();return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)

def specs():
    s=ROOT/'evidence/rk02/sim/stock_full_01'
    rows=[('stock',Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin'),s/'FULL_READ.json',
           [s/f'pass_{i}.bin' for i in (0,1)],s/'coverage.json')]
    for n,f in [('composite','composite.bin'),('random','random_705827.bin')]:
        d=ROOT/'fake/runs'/('rk02_'+n+'_01')
        rows.append((n,ROOT/'host/fixtures'/f,d/'RESULT.json',[d/f'pass{i}.bin' for i in (0,1)],d/'execution_coverage.json'))
    return rows

def lossless():
    rows=[]
    for name,fixture,report,outputs,coverage in specs():
        d=json.loads(report.read_text());c=json.loads(coverage.read_text())
        assert d['status'] in ('PASS','PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS'),name
        assert c['identity']['kernel_sha256']==PIN and c['identity']['receiver_self_echo'] is True,name
        assert c['terminal']=='COMPLETE' and len(c['exchanges'])==4098 and all(x['status']=='PASS' for x in c['exchanges']),name
        assert c['instruction_counts']['FFFF3260']==2*1048576+15,name
        original=fixture.read_bytes();assert len(original)==1048576 and sha(fixture)==FIXTURES[name],name
        assert all(p.read_bytes()==original for p in outputs),name
        rows.append({'id':name,'fixture':pin(fixture),'outputs':[pin(x) for x in outputs],
          'report':pin(report),'coverage':pin(coverage),'bytes_per_pass':1048576,'passes':2,'byte_mismatches':0,
          'source':'Actual RK02 instruction execution and SCI output with ECU self-echo; no CRC substitution'})
    return {'schema':1,'status':'PASS','kernel_sha256':PIN,'failures':[],'fixtures':rows,
      'fixture_classes':['Exact stock','Address-derived','Zero and FF pages','Nonblank FF-CRC collision',
        'Historical gap sentinels','Deterministic random 1MiB'],'physical_operations':False,'current_ROM_identified':False}

def inputs(stage,handoff=None):
    files=set()
    def add(p):
        p=Path(p).resolve()
        if p.is_file():files.add(p)
    def tree(p):
        for f in Path(p).rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts:add(f)
    for name in ('src','linker','tools','sim','host','fake'):
        for p in (ROOT/name).glob('*'):
            if p.is_file():add(p)
    for folder in ('build/rk02_01','build/rk02_repro_01','build/rk02_guarded_01','host/build/native_05',
        'host/vendor','fake/native','evidence/contracts','evidence/rk02','evidence/rk01_superseded'):
        tree(ROOT/folder)
    for p in (ROOT/'fake/runs').glob('rk02_*'):tree(p)
    for n in ('evidence/RK01_SUPERSEDED.json','preservation/snapshot_20260927/MANIFEST.json','README.md','ARCHITECTURE.md','RUN_CONTRACT.md'):
        add(ROOT/n)
    for row in specs():add(row[1])
    for p in (ROOT/'host/fixtures').glob('*.json'):add(p)
    add(Path(r'C:\Dev\A2WC511R_Sim\sh2e.py'))
    m=json.loads((ROOT/'build/rk02_01/manifest.json').read_text())
    for t in m['toolchain'].values():add(t['path'])
    native=json.loads((ROOT/'evidence/rk02/host/NATIVE_TOOLCHAIN.json').read_text())
    for name in ('compiler','linker','vcvars32'):add(native[name]['path'])
    passive=Path(r'C:\Dev\Astra_A2WC511R\integrations\prehardware')
    for n in ('capture.py','transport.py','broker.cpp','build/broker.exe','build/BUILD_MANIFEST.json'):add(passive/n)
    add(Path(r'C:\Windows\SysWOW64\op20pt32.dll'))
    if handoff:add(ROOT/handoff)
    if stage=='FINAL_RK02_ACQUISITION_STACK':
        tree(ROOT/'host/physical_build/rk02_physical_01')
        for n in ('OFFLINE_SOFTWARE_CERTIFICATE.json','HUMAN_ACQUISITION_RK02.md','ENGINEERING_GATES.json'):add(ROOT/n)
    d={'schema':2,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','stage':stage,'kernel_sha256':PIN,
      'build_manifest':'build/rk02_01/manifest.json','repro_manifest':'build/rk02_repro_01/manifest.json',
      'aggregate_coverage':'evidence/rk02/sim/coverage.json',
      'software_gates':[{'id':k,'report':v[0],'assertions':[]} for k,v in FIXED_GATES.items()],
      'fixtures':[{'id':n,'fixture':rel(f),'outputs':[rel(p) for p in o],'coverage':rel(c)} for n,f,r,o,c in specs()],
      'physical_gates':[{'id':k,'status':'PHYSICAL_REQUIRED'} for k in sorted(PHYSICAL_IDS)],
      'files':[dict(pin(p),path=rel(p)) for p in sorted(files,key=str)]}
    if handoff:d['handoff_manifest']=rel(ROOT/handoff)
    if stage=='FINAL_RK02_ACQUISITION_STACK':d['physical_build_manifest']='host/physical_build/rk02_physical_01/BUILD_MANIFEST.json'
    return d

def software(label,handoff):
    regression=json.loads((ROOT/'evidence/rk02/VALIDATOR_REGRESSIONS.json').read_text())
    assert regression['status']=='PASS' and regression['cases'],'Validator regression suite required'
    assert regression['validator_sha256']==sha(ROOT/'tools/validate.py'),'Changed validator needs fresh regressions'
    assert regression['artifact_review_sha256']==sha(ROOT/'tools/artifact_review.py'),'Changed artifact checker needs fresh regressions'
    lp=ROOT/'evidence/rk02/LOSSLESS_FIXTURES.json';l=lossless()
    if lp.exists():assert json.loads(lp.read_text())==l,'Existing lossless join changed'
    else:write(lp,l)
    pp=ROOT/'evidence/rk02/FINAL_PRESERVATION.json'
    if not pp.exists():
        p=verify_all(ROOT/handoff if handoff else None);assert p['status']=='PASS',p;write(pp,p)
    index=inputs('SOFTWARE_QUALIFICATION',handoff)
    ip=ROOT/'evidence/rk02'/f'{label}_INPUTS.json';write(ip,index)
    result=validate(index);rp=ROOT/'evidence/rk02'/f'{label}_VALIDATION.json';write(rp,result)
    assert result['software_status']=='PASS',result['failed_checks']
    b=json.loads((ROOT/'host/build/native_05/binding.json').read_text())
    cert={'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','eligible':True,
      'eligibility':'OFFLINE_SOFTWARE_ONLY_PHYSICAL_ACCEPTANCE_REQUIRED','kernel_sha256':PIN,'fake_host_sha256':b['client_sha256'],
      'evidence':[pin(ip),pin(rp),pin(lp),pin(pp)],'load_address':'FFFF3000','entry':'FFFF3004',
      'kernel_version':'A2WC511R-RK02','ROM_range':['000000','100000'],'fixed_block_bytes':512,'passes':2,
      'ECU_identity':'2F12515306','physical_operations_performed':False,'not_an_ECU_ROM_release':True,
      'remaining_physical':index['physical_gates']}
    cp=ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json';write(cp,cert)
    print(json.dumps({'status':'PASS_OFFLINE_CERTIFICATE','certificate':pin(cp)}))

def final(handoff):
    index=inputs('FINAL_RK02_ACQUISITION_STACK',handoff);ip=ROOT/'QUALIFICATION_INPUTS.json';write(ip,index)
    result=validate(index);assert result['software_status']=='PASS',result['failed_checks']
    b=json.loads((ROOT/index['physical_build_manifest']).read_text())
    documents=[ip,ROOT/'tools/validate.py',ROOT/'HUMAN_ACQUISITION_RK02.md',ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json',
      ROOT/index['physical_build_manifest'],Path(b['native_binary']['path']),ROOT/'ENGINEERING_GATES.json']
    cert={'schema':1,'status':'RK02_OFFLINE_QUALIFIED_PHYSICAL_REQUIRED','artifact_class':'TEMP_RAM_ACQUISITION_TOOL',
      'kernel_sha256':PIN,'physical_host_sha256':b['native_binary']['sha256'],'fake_host_sha256':b['tested_fake_binding']['client_sha256'],
      'qualification_index':pin(ip),'validator_sha256':sha(ROOT/'tools/validate.py'),
      'procedure':pin(ROOT/'HUMAN_ACQUISITION_RK02.md'),'files':[pin(p) for p in documents],
      'current_vehicle_ROM_identified':False,'real_provider_loaded_during_qualification':False,
      'ECU_firmware_release':False,'RK01':'SUPERSEDED_NOT_FOR_HARDWARE','physical_acceptance':'PHYSICAL_REQUIRED',
      'next_action':'HUMAN_ACQUISITION_ONLY_WITH_PHYSICAL_PRECONDITIONS'}
    cp=ROOT/'RELEASE_CERTIFICATE.json';write(cp,cert)
    print(json.dumps({'status':cert['status'],'certificate':pin(cp),'sealed_files':len(index['files'])}))

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['software','final'])
    p.add_argument('--label',default='SOFTWARE_01');p.add_argument('--handoff');a=p.parse_args()
    if not a.label.replace('_','').isalnum():raise ValueError('Simple unique evidence label')
    if a.stage=='software':software(a.label,a.handoff)
    else:final(a.handoff)

if __name__=='__main__':main()
