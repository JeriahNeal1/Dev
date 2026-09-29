"""Verify the pristine package once; later preserve evidence and report intentional edits.
This is integrity bookkeeping, not a security boundary or permission to trust arbitrary code.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def check(root: Path) -> dict:
    root = root.resolve()
    manifest_path = root / 'PACKAGE_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest_hash = sha(manifest_path)
    stamp_path = root / '.runtime' / 'package_accepted.json'
    accepted = json.loads(stamp_path.read_text(encoding='utf-8')) if stamp_path.exists() else None
    if accepted and accepted.get('manifest_sha256') != manifest_hash:
        raise ValueError('Package manifest changed since initial acceptance. Preserve work and review the package replacement explicitly.')
    changes = []
    for entry in manifest['files']:
        p = (root / entry['path']).resolve()
        if not p.is_relative_to(root):
            raise ValueError('Manifest path escapes package root')
        if not p.is_file():
            changes.append({'path': entry['path'], 'status': 'missing'})
        elif p.stat().st_size != entry['size'] or sha(p) != entry['sha256']:
            changes.append({'path': entry['path'], 'status': 'changed'})
    evidence_changes = [x for x in changes if x['path'].replace('\\', '/').startswith('evidence/')]
    if not accepted and changes:
        raise ValueError('Initial package differs from its manifest: ' + json.dumps(changes[:20]))
    if evidence_changes:
        raise ValueError('Immutable original evidence changed: ' + json.dumps(evidence_changes[:20]))
    if not accepted:
        stamp_path.parent.mkdir(parents=True, exist_ok=True)
        stamp_path.write_text(json.dumps({'manifest_sha256': manifest_hash,
            'accepted_at': datetime.now(timezone.utc).isoformat()}, indent=2) + '\n', encoding='utf-8')
    result = {'passed': True, 'initial_acceptance': not bool(accepted),
              'checked_files': len(manifest['files']), 'workspace_changes': changes,
              'note': 'Post-acceptance working code/state may change; originals under evidence/ remain immutable. Review recorded changes and retain local history.'}
    report = root / 'reports' / 'local' / 'package_integrity.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    a = p.parse_args()
    r = check(a.root)
    print(json.dumps({k: v for k, v in r.items() if k != 'workspace_changes'}, indent=2))
    if r['workspace_changes']:
        print('Changed working files:', len(r['workspace_changes']), '- see reports/local/package_integrity.json')
if __name__ == '__main__':
    main()
