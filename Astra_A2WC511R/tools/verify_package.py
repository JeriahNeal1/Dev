"""Verify the initial handoff manifest. Run before editing the extracted package."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
failed=[]
for entry in manifest['files']:
 p=(root/entry['path']).resolve()
 if not p.is_relative_to(root):raise SystemExit('Invalid manifest path')
 if not p.is_file():failed.append((entry['path'],'missing'));continue
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if h!=entry['sha256'] or p.stat().st_size!=entry['size']:failed.append((entry['path'],'changed'))
print(json.dumps({'checked':len(manifest['files']),'passed':not failed,'failures':failed},indent=2))
sys.exit(1 if failed else 0)
