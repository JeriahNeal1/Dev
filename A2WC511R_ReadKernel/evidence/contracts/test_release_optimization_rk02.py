"""Exercise actual release gates under -O; all release writes stay in memory."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,json
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import release_rk02 as release
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if sys.flags.optimize<1:raise RuntimeError('Run this negative suite with py -3 -B -O')
    inputs=[pin(Path(__file__)),pin(ROOT/'tools/release_rk02.py'),pin(ROOT/'tools/validate.py'),pin(ROOT/'tools/artifact_review.py')]
    before={str(p):pin(p) if p.exists() else None for p in (ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json',ROOT/'RELEASE_CERTIFICATE.json',ROOT/'QUALIFICATION_INPUTS.json')}
    original_read_text=Path.read_text;regpath=(ROOT/'evidence/rk02/VALIDATOR_REGRESSIONS.json').resolve()
    valid={'status':'PASS','cases':[{'status':'PASS','case':'in_memory_gate_probe_only'}],
      'validator_sha256':release.sha(ROOT/'tools/validate.py'),'artifact_review_sha256':release.sha(ROOT/'tools/artifact_review.py')}
    cases=[]
    for name,field,value,stage in [('regression_FAIL','status','FAIL','software'),
       ('regression_cases_empty','cases',[],'software'),
       ('regression_validator_stale','validator_sha256','0'*64,'software'),
       ('software_validation_FAIL',None,None,'software'),('final_validation_FAIL',None,None,'final')]:
        reg=dict(valid)
        if field is not None:reg[field]=value
        writes=[];calls=[];caught=None
        def text(p,*a,**kw):
            return json.dumps(reg) if p.resolve()==regpath else original_read_text(p,*a,**kw)
        def capture(p,d):writes.append({'path':str(p),'document':d})
        def invalid(d):
            calls.append(d);return {'software_status':'FAIL','failed_checks':['probe_validation_fail']}
        with patch.object(Path,'read_text',text),patch.object(release,'write',capture),\
             patch.object(release,'inputs',lambda *a,**kw:{'physical_gates':[]}),patch.object(release,'validate',invalid):
            try:
                if stage=='software':release.software('IN_MEMORY_OPTIMIZATION_NEGATIVE',None)
                else:release.final(None)
            except Exception as error:caught={'type':type(error).__name__,'message':str(error)}
        certificates=[x for x in writes if Path(x['path']).name in ('OFFLINE_SOFTWARE_CERTIFICATE.json','RELEASE_CERTIFICATE.json')]
        gate_case=field is not None
        ok=caught is not None and caught['type']=='ValueError' and not certificates
        ok=ok and (not writes and not calls if gate_case else len(calls)==1 and 'probe_validation_fail' in caught['message'])
        cases.append({'case':name,'status':'PASS' if ok else 'FAIL','caught':caught,
          'virtual_write_paths':[x['path'] for x in writes],'validator_calls':len(calls),'certificate_writes':len(certificates)})
    after={str(p):pin(p) if p.exists() else None for p in map(Path,before)}
    unchanged=before==after and all(pin(x['path'])==x for x in inputs)
    status='PASS' if unchanged and all(x['status']=='PASS' for x in cases) else 'FAIL'
    result={'schema':1,'status':status,'python_optimization_level':sys.flags.optimize,'inputs':inputs,
      'cases':cases,'case_count':len(cases),'real_certificate_and_index_files_unchanged':unchanged,
      'real_release_writes':0,'provider_loaded':False,'physical_operations':0,
      'method':'Actual release_rk02.software/final invoked under Python -O. Only regression-document read, input generation, validator result and release.write are process-local test doubles. All would-be release writes are retained in memory; the required ValueError must occur before any certificate issuance.',
      'limits':['These tests prove the explicit release failure gates survive optimization; they do not replace full unchanged-index validation or native/simulator qualification.']}
    with args.report.open('x',encoding='utf-8') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':status,'cases':len(cases),'report':str(args.report),'sha256':pin(args.report)['sha256']}))
    return status!='PASS'
if __name__=='__main__':raise SystemExit(main())
