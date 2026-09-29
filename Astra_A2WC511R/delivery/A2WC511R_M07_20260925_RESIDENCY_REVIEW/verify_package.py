from pathlib import Path
from hashlib import sha256
import json
root=Path(__file__).resolve().parent
manifest=root/'SHA256SUMS.json'
expected=json.loads(manifest.read_text())['files']
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=manifest}
assert actual==set(expected),'Package file set differs'
for rel,value in expected.items():
    assert sha256((root/rel).read_bytes()).hexdigest()==value,rel
print(json.dumps({'status':'PASS','files':len(expected),'manifest_sha256':sha256(manifest.read_bytes()).hexdigest()}))
