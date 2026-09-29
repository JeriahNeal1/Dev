"""Seal this run's local evidence without changing frozen earlier manifests."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,json,datetime
from finalize import ROOT,OUT,sha

def make():
    files={}
    for directory in ('integrations/ecuflash_virtual','tools/ecuflash_dynamic',
                      'reports/local/ecuflash_dynamic','work/ecuflash_dynamic',
                      'work/ecuflash_dynamic_native_raw_build',
                      'backups/ecuflash_dynamic_20260926'):
        for p in sorted((ROOT/directory).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts:continue
            if p.parent==OUT and p.name in ('DELIVERABLE_MANIFEST.json','DELIVERABLE_VERIFY.json'):continue
            files[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size,
                'local_private':p.name=='session_private.json' or 'PRIVATE' in p.name}
    for p in sorted((ROOT/'state').glob('*')):
        if p.is_file():files[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size,'current_checkpoint':True}
    report={'schema':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'root':str(ROOT),'scope':'LOCAL_EVIDENCE_ONLY; NOT_A_FLASH_ARTIFACT_OR_PHYSICAL_QUALIFICATION',
        'private_file_policy':'Local files are hashed only. Do not publish environment/token/registry snapshots or proprietary input material.',
        'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files.values())}
    (OUT/'DELIVERABLE_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def verify():
    path=OUT/'DELIVERABLE_MANIFEST.json';report=json.loads(path.read_text());bad=[]
    for relative,info in report['files'].items():
        p=ROOT/relative;actual=sha(p) if p.exists() else None
        if actual!=info['sha256']:bad.append({'path':relative,'expected':info['sha256'],'actual':actual})
    result={'schema':1,'status':'PASS' if not bad else 'FAIL','checked_files':len(report['files']),
        'manifest_sha256':sha(path),'mismatches':bad,'physical':False}
    (OUT/'DELIVERABLE_VERIFY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));return int(bool(bad))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    if not args.verify:make()
    raise SystemExit(verify())
