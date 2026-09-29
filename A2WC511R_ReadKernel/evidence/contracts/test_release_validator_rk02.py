"""Read-only validator negatives using process-local file/index overlays.

No real artifact is mutated. The current full draft must first pass unchanged.
The expensive real-file hashes and read-only preservation check are cached
within this process, then checked again before recording success.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
PIN='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
OLD_PIN='3d70abfb8617b87e1b9c52724fd27ed4066ba231818994e780c8ba3006de273f'
sys.path.insert(0,str(ROOT/'tools'))
import validate as validator
import artifact_review
import verify_preservation

def digest(b):return hashlib.sha256(b).hexdigest()
def key(p):return os.path.normcase(os.path.abspath(os.fspath(p)))
def reference(p):
    p=Path(p).resolve();b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':digest(b)}

class Overlay:
    def __init__(self,index):
        self.index=copy.deepcopy(index);self.bytes={};self.hashes={};self.checked_paths={}
        self.original_read_bytes=Path.read_bytes;self.original_read_text=Path.read_text
        self.original_stat=Path.stat;self.original_sha=validator.sha
    def path(self,p):return (ROOT/Path(p)).resolve()
    def get_bytes(self,p):
        return self.bytes.get(key(p),None) if key(p) in self.bytes else self.original_read_bytes(Path(p))
    def get_json(self,p):return json.loads(self.get_bytes(self.path(p)))
    def set_bytes(self,p,b):self.bytes[key(self.path(p))]=bytes(b)
    def set_json(self,p,d):self.set_bytes(p,(json.dumps(d,indent=2)+'\n').encode('utf-8'))
    def change(self,p,fn):
        d=self.get_json(p);fn(d);self.set_json(p,d);return d
    def reseal_index(self):
        for item in self.index['files']:
            k=key(self.path(item['path']))
            if k in self.bytes:
                item['sha256']=digest(self.bytes[k]);item['bytes']=len(self.bytes[k])
    def sha(self,p):
        k=key(p)
        if k in self.bytes:return digest(self.bytes[k])
        if k not in self.hashes:
            self.hashes[k]=self.original_sha(p);self.checked_paths[k]=str(Path(p).resolve())
        return self.hashes[k]
    def read_text(self,p,encoding=None,errors=None,**kwargs):
        if key(p) in self.bytes:return self.bytes[key(p)].decode(encoding or 'utf-8',errors or 'strict')
        return self.original_read_text(p,encoding=encoding,errors=errors,**kwargs)
    def stat(self,p,*args,**kwargs):
        value=self.original_stat(p,*args,**kwargs)
        if key(p) in self.bytes:
            fields=list(value);fields[6]=len(self.bytes[key(p)]);return os.stat_result(fields)
        return value
    def verify_stable(self):
        changed=[]
        for k,p in self.checked_paths.items():
            if self.original_sha(p)!=self.hashes[k]:changed.append(p)
        return changed

def changes():
    cases=[]
    def add(name,expected,fn,reseal=True):cases.append((name,expected,fn,reseal))
    def fixture_path(o):return next(x['coverage'] for x in o.index['fixtures'] if x['id']=='stock')
    def fixture_identity(o,field,value):o.change(fixture_path(o),lambda d:d['identity'].__setitem__(field,value))
    add('same_build_used_as_repro','PINNED_TOOLCHAIN_SOURCE_REPRODUCIBILITY_LAYOUT',
        lambda o:o.index.__setitem__('repro_manifest',o.index['build_manifest']))
    add('empty_build_sources','PINNED_TOOLCHAIN_SOURCE_REPRODUCIBILITY_LAYOUT',
        lambda o:o.change(o.index['build_manifest'],lambda d:d.__setitem__('sources',{})))
    add('empty_build_toolchain','PINNED_TOOLCHAIN_SOURCE_REPRODUCIBILITY_LAYOUT',
        lambda o:o.change(o.index['build_manifest'],lambda d:d.__setitem__('toolchain',{})))
    add('native_files_empty','EXACT_TESTED_NATIVE_HOST_AND_SOURCE_ASSOCIATION',
        lambda o:o.change('host/build/native_05/BUILD_MANIFEST.json',lambda d:d.__setitem__('files',[])))
    add('native_wrong_client_path','EXACT_TESTED_NATIVE_HOST_AND_SOURCE_ASSOCIATION',
        lambda o:o.change('host/build/native_05/binding.json',lambda d:d.__setitem__('client_path',str(ROOT/'host/build/native_05/owned_artifact.h'))))
    add('host_source_files_empty','HOST_FINALIZER_AND_TERMINAL_TEST_ASSOCIATION',
        lambda o:o.change('evidence/rk02/host/HOST_QUALIFICATION.json',lambda d:d.__setitem__('source_files',[])))
    add('host_full_fixtures_empty','HOST_FINALIZER_AND_TERMINAL_TEST_ASSOCIATION',
        lambda o:o.change('evidence/rk02/host/HOST_QUALIFICATION.json',lambda d:d.__setitem__('full_fixtures',[])))
    def bad_fault(o):
        o.change('evidence/rk02/host/HOST_FAULTS.json',lambda d:d['cases']['read_checksum'].__setitem__('host_sha256','0'*64))
    add('host_fault_wrong_executable','REQUIRED_NATIVE_FAULTS_AND_CLOSED_TX_PREFIXES',bad_fault)
    add('fixture_model_set_empty','BYTE_FOR_BYTE_TWO_FULL_READS',lambda o:fixture_identity(o,'model_sources',{}))
    add('fixture_core_identity_empty','BYTE_FOR_BYTE_TWO_FULL_READS',lambda o:fixture_identity(o,'core_sha256',''))
    add('fixture_stale_RK01','BYTE_FOR_BYTE_TWO_FULL_READS',lambda o:fixture_identity(o,'kernel_sha256',OLD_PIN))
    add('fixture_self_echo_disabled','BYTE_FOR_BYTE_TWO_FULL_READS',lambda o:fixture_identity(o,'receiver_self_echo',False))
    add('half_duplex_model_set_empty','HALF_DUPLEX_CASES_AND_MODEL_ASSOCIATION',
        lambda o:o.change('evidence/rk02/sim/SELF_ECHO_QUALIFICATION.json',lambda d:d.__setitem__('model_sources',{})))
    add('half_duplex_required_case_missing','HALF_DUPLEX_CASES_AND_MODEL_ASSOCIATION',
        lambda o:o.change('evidence/rk02/sim/SELF_ECHO_QUALIFICATION.json',lambda d:d['cases'][0].__setitem__('case','unrelated_case')))
    add('RK01_negative_included_as_RK02','HALF_DUPLEX_CASES_AND_MODEL_ASSOCIATION',
        lambda o:o.change('evidence/rk02/sim/SELF_ECHO_QUALIFICATION.json',lambda d:d['RK01_negative_control'].__setitem__('included_in_RK02_coverage',True)))
    def wrong_model(o):
        p=ROOT/'sim/sci.py';o.set_bytes(p,o.get_bytes(p)+b'\n# In-memory review mutation only.\n')
    add('executed_model_source_changed','HALF_DUPLEX_CASES_AND_MODEL_ASSOCIATION',wrong_model)
    add('coverage_inputs_empty','FIXED_RK02_COVERAGE_INPUTS',
        lambda o:o.change(o.index['aggregate_coverage'],lambda d:d.__setitem__('inputs',[])))
    def stale_fault_coverage(o):
        p=ROOT/'evidence/rk02/sim/faults_01/coverage.json'
        o.change(p,lambda d:d.__setitem__('kernel_sha256',OLD_PIN));new=digest(o.get_bytes(p))
        o.change('evidence/rk02/sim/faults_01/FAULTS.json',lambda d:d['coverage'].__setitem__('sha256',new))
        def link(d):
            for item in d['inputs']:
                if key(o.path(item['path']))==key(p):item['sha256']=new
        o.change(o.index['aggregate_coverage'],link)
    add('branch_fault_coverage_stale_RK01','COMPILED_COVERAGE_CROSSCHECK',stale_fault_coverage)
    def absent_edge(o):
        m=o.get_json(o.index['build_manifest'])
        branch=next(i for i in m['instructions'] if i['opcode']&0xff00 in (0x8900,0x8b00))
        a=branch['address'];target=a+2
        def remove(d):
            n=len(d['edges']);d['edges']=[e for e in d['edges'] if (int(e['from'],16),int(e['to'],16))!=(a,target)]
            if len(d['edges'])==n:raise AssertionError('Baseline branch direction absent')
        o.change(o.index['aggregate_coverage'],remove)
    add('compiled_branch_direction_missing','ALL_CONDITIONAL_DIRECTIONS',absent_edge)
    add('static_store_duplicated','COMPLETE_UNIQUE_STATIC_STORE_DOMAINS',
        lambda o:o.change('evidence/contracts/BINARY_REVIEW_rk02_01.json',lambda d:d['store_domains'].__setitem__(1,copy.deepcopy(d['store_domains'][0]))))
    add('static_store_domains_empty','COMPLETE_UNIQUE_STATIC_STORE_DOMAINS',
        lambda o:o.change('evidence/contracts/BINARY_REVIEW_rk02_01.json',lambda d:d.__setitem__('store_domains',[])))
    def flash_write(o):
        o.change(o.index['aggregate_coverage'],lambda d:d['writes'].append({'address':'FFFFE800','size':1,'pc':'FFFF3202','count':1}))
    add('observed_flash_controller_write','EVERY_OBSERVED_STORE_DECLARED',flash_write)
    add('stack_bound_changed','EXACT_STACK_BOUND',
        lambda o:o.change(o.index['aggregate_coverage'],lambda d:d.__setitem__('software_stack_bytes',4)))
    add('preservation_subset_empty','RK01_PRESERVED_BYTES',
        lambda o:o.change('evidence/RK01_SUPERSEDED.json',lambda d:d.__setitem__('preserved_directory_files',[])))
    def old_file(o):
        p=o.get_json('evidence/RK01_SUPERSEDED.json')['preserved_directory_files'][0]['path']
        o.set_bytes(p,o.get_bytes(p)+b'\n')
    add('preserved_RK01_file_changed','RK01_PRESERVED_BYTES',old_file)
    add('required_software_gate_missing','REQUIRED_SOFTWARE_GATES',
        lambda o:o.index.__setitem__('software_gates',[g for g in o.index['software_gates'] if g['id']!='OEM_UPLOAD_ENTRY_CONTRACT']))
    add('physical_gate_missing','PHYSICAL_CLAIMS_SEPARATE',lambda o:o.index['physical_gates'].pop())
    add('physical_gate_replaced_by_unknown','PHYSICAL_CLAIMS_SEPARATE',lambda o:o.index['physical_gates'][0].__setitem__('id','UNRELATED_LABEL'))
    def corrupt_fixture(o):
        p=next(f['fixture'] for f in o.index['fixtures'] if f['id']=='stock');b=bytearray(o.get_bytes(o.path(p)));b[0]^=1;o.set_bytes(p,b)
    add('sealed_file_byte_corruption','BYTE_FOR_BYTE_TWO_FULL_READS',corrupt_fixture,False)
    return cases

def run(index_path,refresh_self_pin=False):
    index_raw=index_path.read_bytes();index=json.loads(index_raw)
    inputs=[reference(index_path),reference(Path(__file__)),reference(ROOT/'tools/validate.py'),reference(ROOT/'tools/artifact_review.py')]
    self_adjustment=None
    if refresh_self_pin:
        records=[x for x in index['files'] if key(ROOT/Path(x['path']))==key(Path(__file__))]
        if len(records)!=1:raise ValueError('Exactly one existing reviewer-script pin is required for isolated refresh')
        item=records[0];before=copy.deepcopy(item)
        item['sha256']=inputs[1]['sha256'];item['bytes']=inputs[1]['bytes']
        self_adjustment={'scope':'Only this reviewer script; no validator, runtime, build or evidence pin changes',
          'before':before,'after':copy.deepcopy(item),'on_disk_index_changed':False}
    original_preservation=verify_preservation.verify_all;preservation_cache={}
    def preservation(*args,**kwargs):
        k=repr((args,kwargs))
        if k not in preservation_cache:preservation_cache[k]=(args,kwargs,original_preservation(*args,**kwargs))
        return copy.deepcopy(preservation_cache[k][2])
    shared=Overlay(index);results=[];failures=[];started=time.monotonic()
    def evaluate(o):
        with patch.object(Path,'read_bytes',lambda p:o.get_bytes(p)),\
             patch.object(Path,'read_text',lambda p,*a,**kw:o.read_text(p,*a,**kw)),\
             patch.object(Path,'stat',lambda p,*a,**kw:o.stat(p,*a,**kw)),\
             patch.object(validator,'sha',o.sha),\
             patch.object(artifact_review,'sha',o.sha),\
             patch.object(verify_preservation,'verify_all',preservation):
            return validator.validate(o.index)
    baseline=evaluate(shared)
    baseline_ok=baseline['software_status']=='PASS' and baseline['next_acquisition_connection_software_eligible'] is True
    if not baseline_ok:
        failures.append('UNCHANGED_FULL_BASELINE')
    else:
        negative_cases=changes()
        print(json.dumps({'baseline':'PASS','negative_cases':len(negative_cases)}),flush=True)
        for ordinal,(name,expected,mutate,reseal) in enumerate(negative_cases,1):
            o=Overlay(index);o.hashes=shared.hashes;o.checked_paths=shared.checked_paths
            try:
                mutate(o)
                if reseal:o.reseal_index()
                result=evaluate(o)
                ok=result['software_status']=='FAIL' and result['next_acquisition_connection_software_eligible'] is False
                ok=ok and expected in result['failed_checks']
                details={'failed_checks':result['failed_checks'],'software_status':result['software_status']}
            except Exception as error:
                ok=False;details={'exception':type(error).__name__,'message':str(error)}
            results.append({'case':name,'status':'PASS' if ok else 'FAIL','expected_failed_check':expected,
              'overlay_paths':sorted(o.bytes),'self_consistent_index_reseal':reseal,'actual':details})
            if not ok:failures.append(name)
            if ordinal%5==0 or ordinal==len(negative_cases) or not ok:
                print(json.dumps({'completed':ordinal,'total':len(negative_cases),'failures':failures}),flush=True)
    stable=shared.verify_stable()
    if stable:failures.append('REAL_FILE_STABILITY')
    for args,kwargs,before in preservation_cache.values():
        if original_preservation(*args,**kwargs)!=before:failures.append('PRESERVATION_RESULT_CHANGED')
    if index_path.read_bytes()!=index_raw:failures.append('DRAFT_INDEX_CHANGED')
    for item in inputs:
        if reference(item['path'])!=item:failures.append('REVIEW_INPUT_CHANGED:'+item['path'])
    return {'schema':1,'status':'PASS' if not failures else 'FAIL','kernel_sha256':PIN,
      'validator_sha256':inputs[2]['sha256'],'artifact_review_sha256':inputs[3]['sha256'],
      'inputs':inputs,'baseline':{'status':baseline['status'],'software_status':baseline['software_status'],'failed_checks':baseline['failed_checks']},
      'reviewer_script_index_adjustment':self_adjustment,
      'case_count':len(results),'cases':results,'failures':failures,'changed_real_files':stable,
      'real_artifact_mutations':0,'physical_operations':0,'provider_loaded':False,
      'elapsed_seconds':round(time.monotonic()-started,3),'real_hashes_checked':len(shared.hashes),
      'method':'In-memory Path/sha overlays only. Mutation records are rehashed into an isolated copied index except intentional corruption. Each case must fail its specific semantic check, not merely an unrelated seal. Real hashes and read-only preservation are rechecked after the suite.',
      'limits':['This is a regression suite for the reviewed checker, not a proof against a party able to replace the checker and every evidence record.',
        'No native host, provider, physical adapter or vehicle is loaded. Full simulator/host executions are prior sealed evidence consumed by the unchanged validator.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--refresh-self-pin',action='store_true',help='Refresh only the reviewer-script record in an isolated index copy; retain the original index unchanged')
    a=p.parse_args();result=run(a.index.resolve(),a.refresh_self_pin)
    with a.report.open('x',encoding='utf-8') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'cases':result['case_count'],'failures':result['failures'],'report':str(a.report.resolve()),'sha256':reference(a.report)['sha256']}))
    return result['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
