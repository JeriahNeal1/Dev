"""Seal the independent stock transition evidence catalog; offline only."""
import sys
sys.dont_write_bytecode = True
import json
from pathlib import Path
from oem_transition_replay import OUT, CONTRACTS, pin


def main():
    stock = Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')
    wire = json.loads((CONTRACTS/'KWP_WIRE_CONTRACT.json').read_text())
    assert pin(stock)['sha256'] == '22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
    checks = []
    for p in wire['inputs']:
        actual = pin(p['path'])
        checks.append({'path': p['path'], 'expected_sha256': p['sha256'],
                       'actual_sha256': actual['sha256'], 'matches': actual['sha256'] == p['sha256']})
    assert all(c['matches'] for c in checks)
    assert pin(CONTRACTS/'KWP_WIRE_TRACE.json.gz')['sha256'] == wire['trace_sha256']
    physical = Path('C:/Dev/A2WC511R_ReadKernel/acquisitions/RK02_VEHICLE_03/native_api.jsonl')
    calls = [json.loads(line) for line in physical.read_text().splitlines()]
    indexed = {x['sequence']: x for x in calls if 'sequence' in x}
    delta_ms = (indexed[9]['counter']-indexed[8]['counter'])/indexed[8]['frequency']*1000
    assert indexed[8]['wire_hex'] == '80f01003c1ef8fc2'
    assert indexed[9]['wire_hex'] == '8010f002830005'
    transactions = []
    for row in wire['transactions'][1:3]:
        request, response = bytes.fromhex(row['request']), bytes.fromhex(row['executed_TDR_reply'])
        transactions.append({'request': request.hex(), 'response': response.hex(),
                             'request_total_bytes': len(request), 'request_payload_bytes': request[3],
                             'response_total_bytes': len(response), 'response_payload_bytes': response[3],
                             'request_checksum': f'{sum(request[:-1]) & 255:02x}',
                             'response_checksum': f'{sum(response[:-1]) & 255:02x}',
                             'both_checksums_valid': sum(request[:-1]) & 255 == request[-1] and sum(response[:-1]) & 255 == response[-1]})
    files = [stock, physical, CONTRACTS/'KWP_WIRE_CONTRACT.json', CONTRACTS/'KWP_WIRE_TRACE.json.gz',
             CONTRACTS/'KWP_PRODUCER_REGRESSIONS.json', CONTRACTS/'BOOT_KWP_IDA_FUNCTIONS.json',
             CONTRACTS/'verify_kwp_wire.py', CONTRACTS/'verify_kwp_contract.py',
             OUT/'oem_transition_stock_47108_48240.asm', OUT/'oem_transition_replay.py',
             OUT/'oem_transition_rx_isr_replay.json', OUT/'oem_transition_rx_isr_trace.json.gz',
             OUT/'oem_transition_gap_replay.py', OUT/'oem_transition_gap_replay.json',
             OUT/'oem_transition_gap_trace.json.gz', OUT/'oem_transition_findings.md', Path(__file__)]
    report = {'scope': 'Verified stock firmware transition; current physical ROM code unknown',
              'status': 'STOCK_REQUEST_VALIDITY_AND_TIMING_MECHANISM_VERIFIED_OFFLINE',
              'physical_cause_proven': False, 'physical_operations': 0,
              'qualified_source_or_binary_modified': False,
              'failed_physical_evidence_modified': False,
              'original_wire_evidence_pin_checks': checks,
              'ordered_stock_transactions': transactions,
              'firmware_addresses': {'request_parser': '00047F20', 'receive_ISR_body': '00047E24',
                                     'kwp_dispatcher': '000476E0', '81_validator': '000473C4',
                                     '81_body_and_session_set': '000477DE', '83_validator': '000473F0',
                                     '83_body': '000477FC', 'periodic_transport_service': '00047D94',
                                     'periodic_caller': ['000064A4', '00006542', '000470A6', '00047C66'],
                                     'periodic_task_descriptor': '00004948',
                                     'reset_counter': 'FFFF63F6', 'response_delay_counter': 'FFFF6400'},
              'stock_83_handler': {'requires_payload_length': 2, 'requires_subfunction': 0,
                                  'requires_session_63E1_mask': '20', 'valid_reply_expected': True,
                                  'changes_baud': False, 'checks_Test_Mode': False,
                                  'confidence': 'HIGH for exact bounded stock handler'},
              'interbyte_guard': {'reset_after_periodic_calls_since_last_RXI': 8,
                                  'unit_seconds': None,
                                  '81_changes_guard_or_parser': False,
                                  'long_idle_gap_guard_resets_session_bit20': False,
                                  'periodic_task_descriptor_index': 7,
                                  '0_and_7_tick_cases': 'exact positive C3 reply',
                                  '8_and_9_tick_cases': 'partial request cursor reset and no reply',
                                  'physical_5ms_gap_acceptability': 'UNKNOWN without actual timebase and transmitted spacing'},
              'physical_timing': {'C1_read_return_to_83_write_return_ms': delta_ms,
                                  'wire_gap_ms': None, 'interpretation': 'API completion interval only'},
              'evidence': [pin(p) for p in files],
              'remaining_questions': ['Actual provider defaults and emitted interbyte spacing.',
                                     'Actual periodic task timebase/current code compatibility.',
                                     'Whether physical83 request reached the ECU and whether any raw reply reached adapter.',
                                     'Historical successful exact API/configuration/wire behavior, analyzed separately.']}
    (OUT/'oem_transition_evidence.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'evidence_files': len(files), 'delta_ms': delta_ms}))


if __name__ == '__main__':
    main()
