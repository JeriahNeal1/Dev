"""One-time qualified recovery promotion; never overwrite either input."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(r'C:\Dev\Astra_A2WC511R')
OUT = ROOT / 'reports/local/prehardware'
BACKUP = ROOT / 'backups/prehardware_20260926'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BACKUP.mkdir(parents=True, exist_ok=True)
    marker = OUT / 'IDB_PROMOTION.json'
    if marker.exists():
        raise SystemExit('Promotion already recorded; do not replay mutations')
    seal_path = ROOT / 'reports/local/diaphora/DELIVERABLE_MANIFEST.json'
    seal = json.loads(seal_path.read_text())
    preserved, mutable = {}, {}
    for path, expected in seal['files'].items():
        p = Path(path)
        if sha(p) != expected:
            raise ValueError('Sealed input changed: ' + path)
        if p.is_relative_to(ROOT / 'state') or p.is_relative_to(ROOT / 'config'):
            dest = BACKUP / p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                assert sha(dest) == expected
            else:
                shutil.copy2(p, dest)
            mutable[path] = {'sha256': expected, 'preserved_at': str(dest)}
        else:
            preserved[path] = expected
    for folder in ('state', 'config'):
        for p in (ROOT / folder).rglob('*'):
            if not p.is_file():
                continue
            dest = BACKUP / p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(p, dest)
    original = Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER.bin.i64')
    source = ROOT / 'work/diaphora/idbs/recovery_candidate_01.i64'
    target = original.with_name('A2WC511R_STOCK_ROMRAIDER_RECOVERED_20260926.i64')
    assert sha(original) == '46f442e93535b20cc9f360403c69724d55c72900c7e9716af81bda7fd5c3357f'
    assert sha(source) == '55575c37d368665adcf89bd18cd81bcf6dd6cac7a615d17161514b4a0e4d1500'
    if target.exists():
        raise ValueError('Canonical target already exists')
    shutil.copy2(source, target)
    assert sha(target) == sha(source)
    config_path = ROOT / 'config/host_paths.json'
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    config['idb'] = str(target)
    config['damaged_idb_evidence'] = {'path': str(original), 'sha256': sha(original)}
    config['idb_promotion_record'] = str(marker)
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    discrepancy_path = ROOT / 'reports/local/diaphora/idb_reopen_audit/RECOVERY_METADATA_DISCREPANCIES.json'
    funcs = json.loads(discrepancy_path.read_text())['functions']['only_damaged']
    assert len(funcs) == 31
    queue = {'status': 'WITHHELD_NOT_IMPORTED', 'count': 31,
             'provenance': {'path': str(discrepancy_path), 'sha256': sha(discrepancy_path)},
             'review_required': ['actual SH2E decode', 'all entries and function bounds', 'inbound call/data evidence', 'no ROM byte change'],
             'functions': funcs}
    (OUT / 'UNQUALIFIED_FUNCTION_REVIEW_QUEUE.json').write_text(json.dumps(queue, indent=2) + '\n')
    report = {'status': 'PASS_EXACT_QUALIFIED_COPY_PROMOTED',
              'source': {'path': str(source), 'sha256': sha(source)},
              'canonical': {'path': str(target), 'sha256': sha(target)},
              'damaged_preserved': {'path': str(original), 'sha256': sha(original)},
              'rom_bytes_changed': False, 'metadata_replayed_this_run': 0,
              'withheld_functions': 31, 'native_health_evidence': str(ROOT / 'reports/local/diaphora/idb_reopen_audit/RECOVERY_CANDIDATE_HEALTH.json')}
    marker.write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'START_PRESERVATION.json').write_text(json.dumps({
        'prior_seal': {'path': str(seal_path), 'sha256': sha(seal_path)},
        'immutable_files': preserved, 'mutable_state_preserved': mutable,
        'external_closed_artifacts': seal['external_closed_artifacts'],
        'damaged_idb': report['damaged_preserved'], 'canonical_initial': report['canonical']}, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
