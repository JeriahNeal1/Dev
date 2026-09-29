"""Preserve the current research checkpoint before comparative analysis."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json, shutil
ROOT=Path('C:/Dev/Astra_A2WC511R')
OUT=ROOT/'reports/local/diaphora'
WORK=ROOT/'work/diaphora'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=OUT/'START_PRESERVATION.json'
    assert not manifest.exists(),'Resume existing comparative session instead of replacing baseline'
    backup=ROOT/'backups'/('diaphora_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir();shutil.copytree(ROOT/'state',backup/'state')
    idb=Path('C:/Dev/SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin.i64')
    shutil.copy2(idb,backup/idb.name)
    for rel in ('idbs','exports','comparisons','reports','scripts','inputs'):
        (WORK/rel).mkdir(parents=True,exist_ok=True)
    disposable=WORK/'idbs/environment_probe.i64'
    assert not disposable.exists();shutil.copy2(idb,disposable)
    roots=['work/M07','reports/local/m07_residency','integrations/m07']
    frozen={p.relative_to(ROOT).as_posix():sha(p) for r in roots for p in (ROOT/r).rglob('*') if p.is_file()}
    old=[]
    for rel in ('delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2/SHA256SUMS.json',
                'reports/local/m07_residency/M06_FROZEN_MANIFEST.json',
                'delivery/A2WC511R_M07_20260925_RESIDENCY_REVIEW/SHA256SUMS.json'):
        p=ROOT/rel;old.append({'path':str(p),'sha256':sha(p)})
    data={'created_utc':datetime.now(timezone.utc).isoformat(),'backup':str(backup),
        'authoritative_IDB':{'path':str(idb),'sha256':sha(idb)},'probe_copy':str(disposable),
        'frozen_m07_files':frozen,'earlier_manifests':old,
        'simulator_core_sha256':sha(Path('C:/Dev/A2WC511R_Sim/sh2e.py')),
        'scope':'Original M0/M06/M07 and authoritative IDB remain separate. No HCLI or physical interface.'}
    manifest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','backup':str(backup),'probe_copy':str(disposable),'frozen_M07_files':len(frozen),'authoritative_IDB_sha256':sha(idb)}))
if __name__=='__main__':main()
