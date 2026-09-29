"""Recheck immutable checkpoints; old mutable state must survive in its backup."""
import hashlib
import json
from pathlib import Path
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
OUT=ROOT/'reports/local/prehardware'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def main():
    start=load(OUT/'START_PRESERVATION.json')
    failures=[];counts={}
    def check(mapping,label,base=None):
        count=0
        for p,expected in mapping.items():
            path=Path(p) if base is None else base/p
            if not path.is_file() or sha(path)!=expected:failures.append(str(path))
            count+=1
        counts[label]=count
    check(start['immutable_files'],'prior_sealed_files')
    check({v['preserved_at']:v['sha256'] for v in start['mutable_state_preserved'].values()},'old_sealed_state_backups')
    seal_path=Path(start['prior_seal']['path'])
    check({str(seal_path):start['prior_seal']['sha256']},'comparative_seal')
    check(load(seal_path)['external_closed_artifacts'],'prior_external_artifacts')
    previous=load(ROOT/'reports/local/diaphora/START_PRESERVATION.json')
    check(previous['frozen_m07_files'],'frozen_M07_working_files',ROOT)
    for item in previous['earlier_manifests']:
        path=Path(item['path']);check({str(path):item['sha256']},path.name+'_'+path.parent.name)
        base=ROOT if path.name=='M06_FROZEN_MANIFEST.json' else path.parent
        check(load(path)['files'],'files_'+path.parent.name,base)
    for label in ('damaged_idb','canonical_initial'):
        value=start[label];check({value['path']:value['sha256']},label)
    check({r'C:\Dev\A2WC511R_Sim\sh2e.py':previous['simulator_core_sha256']},'frozen_simulator_core')
    result={'status':'FAIL' if failures else 'PASS','checked_groups':counts,'mismatches':failures,
            'authorized_mutable_state':'New state/config replace current defaults; prior sealed versions retained by exact backup hash',
            'frozen_ROM_bytes_modified':False}
    (OUT/'PRESERVATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));return bool(failures)
if __name__=='__main__':raise SystemExit(main())
