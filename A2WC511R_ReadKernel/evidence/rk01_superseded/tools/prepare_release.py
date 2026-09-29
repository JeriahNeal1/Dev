"""Join completed, named offline reports; never execute a native program."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
from validate import ROOT,PIN,FIXTURES,FIXED_GATES
from verify_preservation import verify_all

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def write(path,document):
    with Path(path).open('x',encoding='utf-8') as f:f.write(json.dumps(document,indent=2)+'\n')

def main():
    specs=[('stock',Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin'),ROOT/'evidence/sim/stock_full_01/FULL_READ.json',
           [ROOT/f'evidence/sim/stock_full_01/pass_{i}.bin' for i in (0,1)],ROOT/'evidence/sim/stock_full_01/coverage.json'),
      ('composite',ROOT/'host/fixtures/composite.bin',ROOT/'fake/runs/composite_native04/RESULT.json',
           [ROOT/f'fake/runs/composite_native04/pass{i}.bin' for i in (0,1)],ROOT/'fake/runs/composite_native04/execution_coverage.json'),
      ('random',ROOT/'host/fixtures/random_705827.bin',ROOT/'fake/runs/random_01/RESULT.json',
           [ROOT/f'fake/runs/random_01/pass{i}.bin' for i in (0,1)],ROOT/'fake/runs/random_01/execution_coverage.json')]
    rows=[]
    for name,fixture,report,outputs,coverage in specs:
        d=json.loads(report.read_text());c=json.loads(coverage.read_text())
        assert d['status'] in ('PASS','PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS'),name
        assert c['identity']['kernel_sha256']==PIN and c['terminal']=='COMPLETE',name
        assert len(c['exchanges'])==4098 and all(x['status']=='PASS' for x in c['exchanges']),name
        assert c['instruction_counts']['FFFF3260']==2*1048576+15,name
        original=fixture.read_bytes()
        assert len(original)==1048576 and sha(fixture)==FIXTURES[name],name
        assert all(p.read_bytes()==original for p in outputs),name
        rows.append({'id':name,'fixture':pin(fixture),'outputs':[pin(x) for x in outputs],
           'report':pin(report),'coverage':pin(coverage),'bytes_per_pass':1048576,'passes':2,
           'byte_mismatches':0,'executed_raw_loads_plus_identity':c['instruction_counts']['FFFF3260'],
           'terminal':'COMPLETE','source':'Actual compiled instruction execution and SCI output; no CRC substitution'})
    lossless={'schema':1,'status':'PASS','kernel_sha256':PIN,'failures':[],'fixtures':rows,
      'classes':['Exact stock','Address-derived full image','All-zero and all-FF pages','Preserved nonblank FF-CRC collision page',
                 'Historical gap sentinels','Full deterministic random image'],
      'physical_operations':False,'current_vehicle_ROM_identified':False}
    path=ROOT/'evidence/LOSSLESS_FIXTURES.json';write(path,lossless)
    preservation=verify_all();assert preservation['status']=='PASS',preservation
    before=ROOT/'evidence/PRESERVATION_PRE_CERTIFICATE.json';write(before,preservation)
    evidence=[pin(path),pin(before)]
    for gate,(relative,requirements) in FIXED_GATES.items():
        if gate=='EVIDENCE_PRESERVATION':continue
        p=ROOT/relative;d=json.loads(p.read_text())
        assert all(d.get(k)==v for k,v in requirements.items()),(gate,requirements)
        evidence.append(pin(p))
    binding=ROOT/'host/build/native_04/binding.json';b=json.loads(binding.read_text())
    assert b['kernel_sha256']==PIN and sha(b['client_path'])==b['client_sha256']
    h=json.loads((ROOT/'host/HOST_QUALIFICATION.json').read_text())
    assert h['final_fake_host_sha256']==b['client_sha256']
    evidence.extend([pin(binding),pin(Path(__file__)),pin(ROOT/'tools/validate.py')])
    certificate={'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','eligible':True,
      'eligibility':'OFFLINE_SOFTWARE_CONTRACT_ONLY_PHYSICAL_ACCEPTANCE_REQUIRED',
      'kernel_sha256':PIN,'fake_host_sha256':b['client_sha256'],'evidence':evidence,
      'load_address':'FFFF3000','entry':'FFFF3004','ROM_range':['000000','100000'],
      'fixed_block_bytes':512,'passes':2,'ECU_identity':'2F12515306','physical_operations_performed':False,
      'not_an_ECU_ROM_release':True,
      'remaining_physical':['Real adapter/UART','Actual ECU/current boot acceptance','Clock and intact RAM upload',
       'External watchdog and electrical behavior','Verified power-loss/reset and renewed OEM BF identity']}
    cert=ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json';write(cert,certificate)
    print(json.dumps({'status':'PASS_OFFLINE_CERTIFICATE','certificate':pin(cert),'fixture_reports':len(rows)}))

if __name__=='__main__':main()
