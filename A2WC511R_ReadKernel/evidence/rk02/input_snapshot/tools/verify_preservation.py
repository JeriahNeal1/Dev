"""Verify prior evidence and fresh snapshots without running any old tool."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
from preserve import verify,sha,OLD,ROOT,SNAP

def verify_all(handoff=None):
    result=verify();allowed={}
    if handoff:
        document=json.loads(Path(handoff).read_text())
        for item in document['authorized_state_updates']:
            path=Path(item['path']).resolve()
            if path.parent!=OLD/'state' or path.name not in {'CURRENT_STATE.md','NEXT_ACTIONS.md','DECISIONS.md','SESSION_LOG.md','CHECKPOINT.json','RUN_CONTRACT.md'}:
                raise ValueError('Only exact handoff state filenames may change')
            if sha(path)!=item['after_sha256']:raise ValueError('Handoff hash changed')
            allowed[str(path)]=item
    seal_path=OLD/'reports/local/ecuflash_dynamic/DELIVERABLE_MANIFEST.json'
    frozen=json.loads(seal_path.read_text());failures=[];updates=[]
    snapshot=json.loads((SNAP/'MANIFEST.json').read_text())
    if sha(seal_path)!=snapshot['prior_seal']['sha256']:failures.append('Prior seal itself changed')
    for rel,record in frozen['files'].items():
        path=OLD/rel
        if not path.exists() or sha(path)!=record['sha256']:
            a=allowed.get(str(path.resolve()))
            if not a or a['before_sha256']!=record['sha256']:failures.append(str(path))
            else:updates.append(a)
    for source in result['changed_sources']:
        if str(Path(source).resolve()) not in allowed:failures.append(source)
    failures+=result['snapshot_mismatches']
    if not result['real_registry_unchanged']:failures.append('J2534/OpenECU registry changed')
    return {'schema':1,'status':'PASS' if not failures else 'FAIL','failures':sorted(set(failures)),
      'fresh_snapshot_manifest_sha256':sha(SNAP/'MANIFEST.json'),'fresh_snapshot_files':sum('snapshot' in x for x in snapshot['files']),
      'prior_deliverable_manifest_sha256':sha(seal_path),'prior_sealed_files_checked':len(frozen['files']),
      'real_registry_unchanged':result['real_registry_unchanged'],'authorized_state_updates':list(allowed.values()),
      'historical_unrecovered_logs':'Prior loss of four logs is preserved as a prior failure; no universal historical preservation claim.',
      'physical_provider_loaded':False,'ECUFlash_application_launched':False}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--handoff',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify_all(a.handoff)
    with a.output.open('x',encoding='utf-8') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'failures':result['failures'],'output':str(a.output),'sha256':sha(a.output)}))
    raise SystemExit(result['status']!='PASS')
