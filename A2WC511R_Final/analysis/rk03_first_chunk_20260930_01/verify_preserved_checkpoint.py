from pathlib import Path
from datetime import datetime, timezone
import hashlib,json

here=Path(__file__).resolve().parent
old=here.parent/'current_rom_20260930_01'
manifest=old/'run_completion_20260930_01/PRESERVATION_MANIFEST.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if sha(manifest)!='7db57fe5689293b423da6e8e9f5e304f7a85c9dd9f173711cca77411308e1d45':
    raise RuntimeError('Historical final preservation manifest changed')
rows=json.loads(manifest.read_text())['files']
fail=[]
for r in rows:
    p=Path(r['path'])
    if not p.is_file() or sha(p)!=r['sha256']: fail.append(r)
rom=Path(r'C:\Dev\SubaruRoms\current.bin')
if sha(rom)!='bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2': fail.append({'path':str(rom)})
result=dict(status='PASS' if not fail else 'FAIL',checked_utc=datetime.now(timezone.utc).isoformat(),
    source_manifest={'path':str(manifest),'sha256':sha(manifest)},files_checked=len(rows),failures=fail,
    current_rom_sha256=sha(rom),note='Hash verification only; no ROM ingestion, code comparison, historical discovery or prior qualification rerun.')
with (here/'PRESERVED_CHECKPOINT_VERIFICATION.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
if fail: raise SystemExit(1)
