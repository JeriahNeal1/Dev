"""Verify all frozen artifacts and original tool/authority bytes at closure."""
from pathlib import Path
from hashlib import sha256
import json,datetime
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=ROOT/'reports/local/diaphora'
def h(p):return sha256(Path(p).read_bytes()).hexdigest()
def verify(base,files):
    failed=[str(base/rel) for rel,digest in files.items() if not (base/rel).is_file() or h(base/rel)!=digest]
    assert not failed,failed
    return {'files':len(files),'status':'PASS'}
def main():
    before=json.loads((OUT/'START_PRESERVATION.json').read_text());result={'status':'PASS','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    result['current_M07_files']=verify(ROOT,before['frozen_m07_files'])
    result['earlier_manifests']=[]
    for m in before['earlier_manifests']:
        p=Path(m['path']);assert h(p)==m['sha256'];d=json.loads(p.read_text())
        base=ROOT if p.name=='M06_FROZEN_MANIFEST.json' else p.parent
        result['earlier_manifests'].append({**m,**verify(base,d['files'])})
    original=before['authoritative_IDB'];assert h(original['path'])==original['sha256'];result['damaged_authoritative_IDB_preserved']=original
    assert h('C:/Dev/A2WC511R_Sim/sh2e.py')==before['simulator_core_sha256'];result['simulator_core_sha256']=before['simulator_core_sha256']
    source=json.loads((OUT/'setup/ORIGINAL_SOURCE_HASHES.json').read_text())
    result['original_Program_Files_source']=verify(Path(source['source']),{f['path']:f['sha256'] for f in source['files']})
    actual={p.relative_to(Path(source['source'])).as_posix() for p in Path(source['source']).rglob('*') if p.is_file()}
    assert actual=={f['path'] for f in source['files']},'Original source file inventory changed'
    (OUT/'PRESERVATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':main()
