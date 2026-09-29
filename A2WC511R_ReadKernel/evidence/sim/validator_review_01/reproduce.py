"""Read-only evidence-selection negatives against the preserved reviewed checker.

Creates only new evidence in this review directory. Does not edit the actual
validator, index, fixture, compiled object, execution report or provider.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('readkernel_reviewed_validator',HERE/'validate_reviewed.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.ROOT=ROOT
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
r=v.validate(index)
out.append({'negative':'All gate IDs redirected to an unrelated schema assertion; all three fixture IDs alias stock',
 'observed_status':r['status'],'software_status':r['software_status'],'failed_checks':r['failed_checks']})
assert r['software_status']=='PASS',r
c=json.loads((ROOT/'evidence/sim/coverage.json').read_text())
c['kernel_sha256']='0'*64;c['writes']=[]
del c['instruction_counts']['FFFF3004']
c['unreachable_instructions']=[{'address':'FFFF3004','proof':'unreviewed arbitrary string'}]
cp=HERE/'coverage_wrong_identity_empty_writes_unreviewed_entry.json'
if cp.exists():raise FileExistsError(cp)
cp.write_text(json.dumps(c,indent=2)+'\n')
index['files'].append(item(cp));index['aggregate_coverage']=str(cp)
r=v.validate(index)
out.append({'negative':'Wrong coverage kernel, empty writes and unreviewed unreachable actual entry instruction',
 'observed_status':r['status'],'software_status':r['software_status'],'failed_checks':r['failed_checks']})
assert r['software_status']=='PASS',r
report={'schema':1,'status':'FINDINGS_REPRODUCED','reviewed_source':item(HERE/'validate_reviewed.py'),
 'classification':'CONSTRUCTED_IN_MEMORY_INDEX_NEGATIVES_NOT_ACTUAL_PROJECT_RELEASE_INDEX',
 'cases':out,'physical_operations':0,'provider_loaded':False}
target=HERE/'REPRODUCTION.json';target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
