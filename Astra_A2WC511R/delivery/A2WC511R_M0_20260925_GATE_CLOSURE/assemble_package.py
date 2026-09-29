"""Create a new immutable review package; no replacement/deletion of previous delivery."""
import argparse,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('C:/Dev/Astra_A2WC511R');EVIDENCE=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copytree(src,dest):
    shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.runtime','.git'))
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();dest=a.output.resolve()
    assert dest.parent==ROOT/'delivery','Only a fresh named delivery directory is allowed'
    assert not dest.exists(),'Preserve existing delivery; use another version name'
    gates=json.loads((EVIDENCE/'ENGINEERING_GATES.json').read_text());assert not gates['production_release_allowed']
    assert json.loads((EVIDENCE/'frozen_verification.json').read_text())['status']=='PASS'
    assert sha(EVIDENCE/gates['interface_summary']['path'])==gates['interface_summary']['sha256']
    for g in gates['gates']:
        for e in g['evidence']:assert sha(EVIDENCE/e['path'])==e['sha256'],e['path']
    copytree(EVIDENCE,dest)
    old=ROOT/'delivery/A2WC511R_M0_20260925_EXPERIMENTAL';copytree(old,dest/'frozen_candidate')
    old_sums=json.loads((old/'SHA256SUMS.json').read_text())
    entries=old_sums.get('files',old_sums)
    for rel,expected in entries.items():
        assert sha(old/rel)==expected,rel
        assert sha(dest/'frozen_candidate'/rel)==expected,rel
    sim=Path('C:/Dev/A2WC511R_Sim');(dest/'simulator').mkdir()
    for q in list(sim.glob('*.py'))+list(sim.glob('*.md')):shutil.copy2(q,dest/'simulator'/q.name)
    copytree(sim/'tests',dest/'simulator/tests')
    for folder in ['romraider/virtual','romraider/src','romraider_mcp']:
        src=ROOT/'integrations'/folder
        if src.exists():copytree(src,dest/'integration_source'/folder)
    for folder in ['gate_closure/virtual_rr','gate_closure/romraider_gui']:
        src=ROOT/'work'/folder
        if src.exists():copytree(src,dest/'validated_helper_classes'/Path(folder).name)
    sums={q.relative_to(dest).as_posix():sha(q) for q in sorted(dest.rglob('*')) if q.is_file()}
    (dest/'SHA256SUMS.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'files':sums},indent=2)+'\n')
    issues=[rel for rel,h in sums.items() if sha(dest/rel)!=h]
    assert not issues,issues
    result={'status':'PASS_EVIDENCE_ENVELOPE_ONLY','delivery':str(dest),'hashed_files':len(sums),
        'sha256_manifest':sha(dest/'SHA256SUMS.json'),'bytes':sum(q.stat().st_size for q in dest.rglob('*') if q.is_file()),
        'old_delivery_unchanged':True,'engineering_approval':False,'physical_validation':False}
    (ROOT/'reports/local/gate_closure_package_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
