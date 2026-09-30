"""Restore four identified preservation items with an exclusive audit backup.

No provider, vehicle, application launch, or qualification-input modification.
The registry write is limited to ECUFlash's cached last-available device string.
"""
import sys
sys.dont_write_bytecode = True

import copy
import datetime
import hashlib
import json
from pathlib import Path
import winreg

ROOT = Path(r'C:\Dev\A2WC511R_ReadKernel')
SNAP = ROOT / 'preservation/snapshot_20260927'
STATE = Path(r'C:\Dev\A2WC511R_Final\state')
MANIFEST_SHA = 'b37e221744f3268e1d9d7b7b7beb9dfc84e2c6e48b9d384a296bb29f7d77372c'
NAMES = {
    'ecuflash_log_20260726t173948.txt',
    'ecuflash_log_20260726t174613.txt',
    'ecuflash_log_20260818t120321.txt',
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_exclusive(path, document):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(document, handle, indent=2)
        handle.write('\n')


def main():
    sys.path.insert(0, str(ROOT / 'tools'))
    from preserve import registry

    manifest_path = SNAP / 'MANIFEST.json'
    require(digest(manifest_path) == MANIFEST_SHA, 'Preservation manifest changed')
    manifest = json.loads(manifest_path.read_text())
    registry_path = Path(manifest['registry_snapshot']['path'])
    require(digest(registry_path) == manifest['registry_snapshot']['sha256'], 'Registry snapshot changed')
    expected = json.loads(registry_path.read_text())
    before = registry()
    expected_value = expected['HKCU/OpenECU']['children']['EcuFlash']['children']['hardware']['children']['openport']['values']['last available']
    observed_value = before['HKCU/OpenECU']['children']['EcuFlash']['children']['hardware']['children']['openport']['values']['last available']
    require(expected_value['type'] == observed_value['type'] == winreg.REG_SZ, 'Unexpected registry type')
    projected = copy.deepcopy(before)
    projected['HKCU/OpenECU']['children']['EcuFlash']['children']['hardware']['children']['openport']['values']['last available'] = expected_value
    require(projected == expected, 'Registry differs beyond the reviewed cached device string')
    require(before != expected, 'No reviewed registry repair remains necessary')

    records = [item for item in manifest['files'] if Path(item['source']).name in NAMES]
    require(len(records) == 3 and {Path(item['source']).name for item in records} == NAMES, 'Unexpected log restoration set')
    for item in records:
        require(not Path(item['source']).exists(), 'A destination log now exists; preserve it')
        require(digest(Path(item['snapshot'])) == item['sha256'], 'Snapshot log hash mismatch')
        require(Path(item['source']).parent == Path(r'C:\Users\Jeriah Neal\AppData\Roaming\OpenECU\EcuFlash\logs'), 'Unexpected restoration destination')

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    audit = STATE / ('preconnection_preservation_restore_' + stamp)
    audit.mkdir(exist_ok=False)
    write_exclusive(audit / 'REGISTRY_BEFORE_PRIVATE.json', before)
    write_exclusive(audit / 'PLAN.json', {
        'status': 'PLANNED_RESTORE_WITH_ORIGINAL_DRIFT_PRESERVED',
        'failed_validation': str(ROOT / 'evidence/rk02/PRE_CONNECTION_VALIDATION_20260929T2150246237619Z.json'),
        'source_logs_observed_missing': records,
        'registry_change': {'key': r'HKCU\Software\OpenECU\EcuFlash\hardware\openport', 'name': 'last available', 'before': observed_value, 'restore': expected_value},
        'provider_loaded': False,
        'qualification_inputs_modified': False,
    })
    for item in records:
        with Path(item['source']).open('xb') as handle:
            handle.write(Path(item['snapshot']).read_bytes())
        require(digest(Path(item['source'])) == item['sha256'], 'Restored log hash mismatch')

    key_path = r'Software\OpenECU\EcuFlash\hardware\openport'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as key:
        current_value, current_type = winreg.QueryValueEx(key, 'last available')
        require((current_value, current_type) == (observed_value['value'], observed_value['type']), 'Registry changed during preparation')
        winreg.SetValueEx(key, 'last available', 0, expected_value['type'], expected_value['value'])
    require(registry() == expected, 'Registry restoration did not match qualified snapshot')
    result = {
        'status': 'RESTORED_REVIEWED_ITEMS_VALIDATION_PENDING',
        'audit_folder': str(audit),
        'restored_log_count': 3,
        'restored_registry_value_count': 1,
        'original_drift_retained_as_evidence': True,
        'provider_registrations_changed': False,
        'provider_loaded': False,
        'qualification_inputs_modified': False,
    }
    write_exclusive(audit / 'RESULT.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
