"""Negative-selection retest of the hardened current checker; no original edits."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('readkernel_current_validator',ROOT/'tools/validate.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def item(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
required=['STATIC_NO_FLASH_WRITE_PATH','SIMULATOR_EXECUTION_COVERAGE','LOSSLESS_FULL_IMAGE_FIXTURES',
 'HOST_FIXED_ALLOWLIST','FAKE_PROVIDER_ACTUAL_KERNEL_EXECUTION','FAULT_INJECTION','OEM_UPLOAD_ENTRY_CONTRACT','EVIDENCE_PRESERVATION']
paths=[ROOT/'build/attempt_03/manifest.json',ROOT/'build/reproducibility_01/manifest.json',
 ROOT/'evidence/sim/coverage.json',ROOT/'evidence/sim/faults_02/FAULTS.json',
 Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin'),ROOT/'evidence/sim/stock_full_01/pass_0.bin',
 ROOT/'evidence/sim/stock_full_01/pass_1.bin',ROOT/'evidence/sim/unit_models.json',
 ROOT/'evidence/sim/fast_parity_03.json',ROOT/'evidence/sim/model_projection_01.json']
index={'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','kernel_sha256':v.PIN,'files':[item(p) for p in paths],
 'build_manifest':'build/attempt_03/manifest.json','repro_manifest':'build/reproducibility_01/manifest.json',
 'aggregate_coverage':'evidence/sim/coverage.json',
 'software_gates':[{'id':g,'report':'evidence/sim/faults_02/FAULTS.json',
   'assertions':[{'path':['schema'],'equals':1}]} for g in required],
 'fixtures':[{'id':name,'fixture':str(paths[4]),'outputs':[str(paths[5]),str(paths[6])]} for name in ('stock','composite','random')],
 'physical_gates':[{'id':str(i),'status':'PHYSICAL_REQUIRED'} for i in range(5)]}
out=[]
for label in ('misdirected_gates_and_aliased_fixtures','wrong_coverage_identity_empty_writes_unreviewed_entry'):
    if label.startswith('wrong_'):
        cp=ROOT/'evidence/sim/validator_review_01/coverage_wrong_identity_empty_writes_unreviewed_entry.json'
        index['files'].append(item(cp));index['aggregate_coverage']=str(cp)
    r=v.validate(index)
    assert r['status']=='FAIL' and r['software_status']=='FAIL',r
    out.append({'negative':label,'observed_status':r['status'],'software_status':r['software_status'],
        'failed_checks':r['failed_checks'],'status':'PASS'})
report={'schema':1,'status':'PASS','reviewed_source':item(ROOT/'tools/validate.py'),
 'classification':'HARDENED_VALIDATOR_REJECTS_BOTH_PREVIOUSLY_ACCEPTED_INVALID_INDEXES',
 'cases':out,'positive_complete_index':'PENDING_OTHER_AGENTS_FINAL_REPORTS',
 'physical_operations':0,'provider_loaded':False}
target=HERE/'RETEST.json'
if target.exists():raise FileExistsError(target)
target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
