"""Independent read-only consistency review; no simulation or provider call."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    errors, checked = [], []
    docs = {}
    filenames = ['oem_transition_evidence.json', 'oem_transition_gap_replay.json',
                 'oem_transition_rx_isr_replay.json',
                 'RK02_VEHICLE_03_SESSION_TRANSITION_EVENT_DIFF.json']
    for filename in filenames:
        docs[filename] = json.loads((ROOT/filename).read_text())
    for filename in filenames:
        doc = docs[filename]
        candidates = doc.get('evidence', []) + doc.get('inputs', [])
        if 'trace' in doc:
            candidates.append(doc['trace'])
        if filename.endswith('EVENT_DIFF.json'):
            candidates += [p for p in doc['evidence_paths_hashes'] if 'oem_transition_' in p.get('path', '')]
        for expected in candidates:
            actual = pin(expected['path'])
            match = actual['sha256'] == expected['sha256']
            if not match:
                errors.append({'type': 'stale_evidence_pin', 'container': filename,
                               'expected': expected, 'actual': actual})
            checked.append({'container': filename, 'path': expected['path'],
                            'expected_sha256': expected['sha256'], 'actual_sha256': actual['sha256'],
                            'match': match})
    event = docs[filenames[-1]]
    for name, expected in [('stock_8300_request', '8010f002830005'),
                           ('stock_8300_reply', '80f01007c30000ff00ff0048')]:
        if event[name]['wire_hex'] != expected or not event[name]['checksum_valid'] or not event[name]['length_valid']:
            errors.append({'type': 'incorrect_stock_frame', 'field': name})
    gaps = docs['oem_transition_gap_replay.json']
    if gaps['status'] != 'PASS_STOCK_INTERBYTE_PERIODIC_TICK_BOUNDARY':
        errors.append({'type': 'gap_replay_not_passing'})
    for case in gaps['cases']:
        ticks = case['periodic_ticks_between_header_byte0_and_byte1']
        expected = '80f01007c30000ff00ff0048' if ticks < 8 else ''
        if case['response_after_83'] != expected or case['tick_duration_seconds'] is not None:
            errors.append({'type': 'gap_case_scope_or_result', 'ticks': ticks})
        if case['state_at_gap_end']['session_63E1'] != 32:
            errors.append({'type': 'gap_unexpected_session_change', 'ticks': ticks})
    rxi = docs['oem_transition_rx_isr_replay.json']
    for case in rxi['cases']:
        tx = case['transactions'][1]
        if tx['reply'] != '80f01007c30000ff00ff0048':
            errors.append({'type': 'RXI_83_reply_mismatch'})
        if any(item['address'] in ['FFFFF010', 'FFFFF011', 'FFFFF016'] for item in tx['mmio_writes']):
            errors.append({'type': 'unexpected_baud_or_mode_MMIO_write'})
    report = {'status': 'PASS_SCOPED_OEM_ANALYSIS_REVIEW' if not errors else 'FAIL_SCOPED_OEM_ANALYSIS_REVIEW',
              'scope': 'OEM claims in root analysis/event diff and final OEM artifact consistency only',
              'errors': errors, 'hash_checks': checked,
              'manual_review': {
                  'exact_83_request_and_stock_response_correct': True,
                  'stock_current_vehicle_code_distinction_preserved': True,
                  '81_uses_same_receive_parser_and_eight_tick_guard': True,
                  'periodic_tick_duration_correctly_unknown': True,
                  '83_does_not_change_baud_in_bounded_stock_path': True,
                  '83_Test_Mode_check_absent_in_bounded_stock_validator': True,
                  'physical_interbyte_spacing_and_physical_cause_correctly_unproved': True,
                  'actual_RXI_and_periodic_execution_distinguished_from_electrical_or_scheduling_simulation': True,
                  'new_qualification_or_physical_acceptance_not_claimed': True},
              'reviewed_files': [pin(ROOT/name) for name in filenames + ['oem_transition_findings.md',
                                 'RK02_VEHICLE_03_SESSION_TRANSITION_ANALYSIS.md',
                                 'oem_transition_replay.py', 'oem_transition_gap_replay.py']],
              'review_script': pin(__file__), 'physical_operations': 0,
              'simulation_reruns': 0, 'qualified_files_modified': False,
              'failed_session_modified': False}
    (ROOT/'oem_transition_review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'hash_checks': len(checked), 'errors': errors}))


if __name__ == '__main__':
    main()
