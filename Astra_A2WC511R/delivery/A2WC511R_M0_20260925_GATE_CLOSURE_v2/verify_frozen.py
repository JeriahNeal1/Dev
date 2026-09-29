import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=Path(__file__).parent
old=ROOT/'delivery/A2WC511R_M0_20260925_EXPERIMENTAL'
manifest=json.loads((old/'SHA256SUMS.json').read_text());issues=[]
for p,h in manifest['files'].items():
    if hashlib.sha256((old/p).read_bytes()).hexdigest()!=h:issues.append('frozen package: '+p)
source=ROOT/'work/MerpMod_M0/MerpMod/DiagnosticM0'
checked=[]
for p in (old/'source/DiagnosticM0').rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(old/'source/DiagnosticM0');q=source/rel
    if not q.is_file() or p.read_bytes()!=q.read_bytes():issues.append('frozen source: '+str(rel))
    checked.append(str(rel))
artifact_checks=[]
for p in (old/'validation/final_build').iterdir():
    if not p.is_file():continue
    q=ROOT/'work/builds/m0_final_05'/p.name
    if not q.is_file() or p.read_bytes()!=q.read_bytes():issues.append('final build: '+p.name)
    artifact_checks.append(p.name)
out={'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS' if not issues else 'FAIL','errors':issues,
 'frozen_package_files':len(manifest['files']),'frozen_package_manifest_sha256':hashlib.sha256((old/'SHA256SUMS.json').read_bytes()).hexdigest(),
 'staged_source_files':checked,'final_build_files':artifact_checks,'firmware_rebuilt_this_run':False,
 'active_features_enabled_this_run':False,'physical_device_access_performed':False,
 'ida_after_sha256':hashlib.sha256(Path('C:/Dev/SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin.i64').read_bytes()).hexdigest(),
 'ida_before_backup_sha256':hashlib.sha256((ROOT/'backups/gate_closure_20260925/idb/A2WC511R_STOCK_ROMRAIDER.bin.i64').read_bytes()).hexdigest()}
(OUT/'frozen_verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'frozen_files':len(manifest['files']),'errors':issues}));raise SystemExit(bool(issues))
