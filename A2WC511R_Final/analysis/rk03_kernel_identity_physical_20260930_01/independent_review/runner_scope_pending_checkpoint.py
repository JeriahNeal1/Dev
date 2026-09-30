"""INCOMPLETE DRAFT: inherited full-upload runner, not release qualification.

Identity TX versus receive-only scope awaits user clarification. This checkpoint
has no completed identity suffix adaptation and must not execute any candidate.
The inherited implementation is retained as the future regression starting point.

Authored by passive_review; root owns independent review.
This runner never selects the physical backend and never loads a provider DLL.
Every invocation and output is retained in a new report directory.
Earlier physical probes and287/156-case qualification remain immutable.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import re
import struct
import subprocess
import traceback

PROBE = Path(__file__).resolve().parents[1]
CONTRACT = Path(r'C:\Dev\A2WC511R_Final\analysis\current_rom_20260930_01\PROBE_REVIEW_CONTRACT.json')
FIRST_CHUNK_CONTRACT = Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_first_chunk_20260930_01\FIRST_CHUNK_REVIEW_CONTRACT.json')
FULL_UPLOAD_CONTRACT = Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_full_upload_no_start_20260930_01\FULL_UPLOAD_NO_START_CONTRACT.json')
PHYSICAL_CONTRACT = Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_full_upload_physical_20260930_01\PHYSICAL_FULL_UPLOAD_REVIEW_CONTRACT.json')
PHYSICAL_CONTRACT_SHA = '0b56e15ae2dcf749666679effd559c54b7a7c2e202fc2ad2902e24c2a54b1e51'
OFFLINE_RUNNER = Path(r'C:\Dev\A2WC511R_RK03_FullUploadNoStart\full_upload_no_start\tools\test_full_upload_independent.py')
OFFLINE_REPORT = Path(r'C:\Dev\A2WC511R_RK03_FullUploadNoStart\full_upload_no_start\reports\qualification_20260930T043538633340Z\TEST_REPORT.json')

PHYSICAL_FIRST_CHUNK_LOG = Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\physical_session\RK03_FIRST_CHUNK_01\native_api.jsonl')
FIRST_CHUNK_RUNNER = Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\first_chunk\tools\test_first_chunk_independent.py')
FIRST_CHUNK_REPORT = Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\first_chunk\reports\qualification_20260930T033815962561Z\TEST_REPORT.json')
SUCCESSFUL_PHYSICAL_LOG = Path(r'C:\Dev\A2WC511R_RK03_TransitionProbe\physical_session\RK03_TRANSITION_PROBE_01\native_api.jsonl')
PREVIOUS_RUNNER = Path(r'C:\Dev\A2WC511R_RK03_PostTransitionOffline\continuation\tools\test_continuation_independent.py')
PREVIOUS_REPORT = Path(r'C:\Dev\A2WC511R_RK03_PostTransitionOffline\continuation\reports\qualification_20260930T023001684674Z\TEST_REPORT.json')
RK02_LOG = Path(r'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_03\native_api.jsonl')
ORACLE = PROBE/'fixtures/full_upload_oracle.json'
KWP = Path(r'C:\Dev\A2WC511R_ReadKernel\evidence\contracts\KWP_WIRE_CONTRACT.json')
UPLOAD = Path(r'C:\Dev\A2WC511R_ReadKernel\evidence\contracts\UPLOAD_WIRE_CONTRACT_RK02.json')
OEM_REPLAY = Path(r'C:\Dev\A2WC511R_Final\analysis\current_rom_20260930_01\post83_oem_review\FIRST_BLOCK_REPLAY.json')
SEEDS = Path(r'C:\Dev\A2WC511R_ReadKernel\evidence\contracts\KWP_PRODUCER_REGRESSIONS.json')
KERNEL = Path(r'C:\Dev\A2WC511R_ReadKernel\build\rk02_01\kernel.bin')
KERNEL_SHA = '3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
TX = ['8010f001bf40', '8010f0018102', '8010f002830005', '8010f0022701aa',
      '8010f0062702e78f1f2165', '8010f0031085021a', '8010f00834ff30000400071006',
      '8010f08436ff30002178b10a345b1076fd256f75f05ba033e301ed7bbae243b735e6aedbc143c40be01bf9b6caab4599eccaacb23d3eeb06dddf471ed3b0238f2bf0553861e117054bad87079a8cbb9681c01303b7825b2d199bc7e5c4dd5bcf85cf1a64050df3ab050df3ab2a45f9b476963b1f16baea94084e321a79bd4cf9c0f25912ab9d7b8df4']
BF = '80f01039ffa210112f1251530673facba62b81fea800000060ce54f9b1e4000c200000000000dc00005d1f3080f226000043fb00e1000000000000c1f0c2'
RX = [BF, '80f01003c1ef8fc2', '80f01007c30000ff00ff0048', '80f0100667011234567802',
      '80f0100367023420', '80f01002508557', '80f0100274847a', '80f0100176f7']
# The preserved upload contract includes a final kernel-start frame. Deliberately
# import only remaining upload frames2..15; preflight pins and checks the boundary.
UPLOAD_FRAMES = json.loads(UPLOAD.read_text())['frames']
TX += [r['request'] for r in UPLOAD_FRAMES[2:16]]
RX += [r['reply_from_executed_TDR'] for r in UPLOAD_FRAMES[2:16]]
CONFIG = [{'parameter': p, 'value': v} for p, v in [(22, 0), (7, 1), (10, 0), (12, 0), (3, 0)]]
SENTINEL = 0xD15EA5ED
CLEANUP = ['PassThruStopMsgFilter', 'PassThruDisconnect', 'PassThruClose']
SUCCESS = ['success', 'fragmented', 'indicators_fragmented', 'version_nonascii', 'extra_index_size', 'queued_stale_rx',
           *[f'seed_vector_{i}' for i in range(16)], 'physical_transition_replay', 'physical_first_chunk_replay']
CASES = SUCCESS + [
    'physical_83_buffer_empty', 'wrong_bf', 'wrong_81', 'wrong_83',
    'bad_checksum_bf', 'bad_checksum_81', 'bad_checksum_83', 'unexpected_frame',
    'open_fail', 'version_fail', 'version_unterminated', 'connect_fail',
    *[f'set_fail_{i}' for i in range(5)], 'set_mutation', 'get_fail',
    *[f'get_wrong_{i}' for i in range(5)], 'get_sentinel', 'get_count_zero',
    'get_count_large', 'get_pointer_null', 'get_pointer_invalid', 'get_parameter',
    'filter_fail', 'filter_mutation', 'write_fail', 'write_count_zero',
    'write_count_large', 'write_mutation', 'read_count_zero', 'read_count_large',
    'read_error_output', 'rx_oversize', 'rx_protocol', 'rx_flags', 'rx_extra',
    'rx_unknown_status', 'rx_combined_status', 'rx_nonempty_indicator', 'rx_wrong_echo',
    'rx_indicator_flood', 'rx_indicator_after_data', 'rx_empty', 'rx_trailing',
    'rx_wrong_direction', 'rx_zero_length', 'rx_marker_only', 'cleanup_stop_fail',
    'cleanup_disconnect_fail', 'cleanup_close_fail', 'cleanup_all_fail',
    'physical_83_cleanup_all_fail', 'journal_failure_after_filter',
    'fail_baud', 'mutate_baud', 'clear_tx_fail', 'clear_rx_fail',
    *[f'{prefix}_{i}' for prefix in ('wait_fail', 'wait_short') for i in range(3)],
    *[f'{prefix}_{i}' for prefix in ('bad_ack', 'negative_ack', 'bad_checksum', 'status16', 'truncated') for i in range(3, 8)],
    'short_ack_4', 'short_ack_5', 'short_ack_6', 'extra_ack_7', 'upload_unknown_status', 'upload_wrong_echo',
    'seed_short', 'seed_extra', 'seed_wrong_subfunction', 'upload_rx_extra',
    *[f'{prefix}_{stage}' for prefix in ('bad_ack', 'negative_ack', 'bad_checksum', 'status16', 'truncated',
                                       'short_ack', 'extra_ack', 'write_fail', 'write_count_zero', 'write_count_large', 'write_mutation')
      for stage in range(8, 22)],
]
REAL_CLOCK_CASES = ['success', 'fragmented', 'indicators_fragmented', 'physical_first_chunk_replay']


BOOTSTRAP_EXPORTS = ['PassThruOpen', 'PassThruClose', 'PassThruConnect', 'PassThruDisconnect', 'PassThruReadMsgs',
                     'PassThruWriteMsgs', 'PassThruStartMsgFilter', 'PassThruStopMsgFilter', 'PassThruReadVersion', 'PassThruIoctl']
BOOTSTRAP_LABELS = ['open', 'close', 'connect', 'disconnect', 'read', 'write', 'filter', 'stop_filter', 'version', 'ioctl']
BOOTSTRAP_CASES = ['valid_gates_no_load', 'wrong_session_path', 'wrong_auth_path', 'missing_auth', 'malformed_auth',
                   'wrong_exe_hash', 'wrong_auth_contract', 'wrong_contract_hash', 'missing_contract', 'missing_reservation',
                   'wrong_reservation', 'consumed_marker', 'wrong_provider_hash', 'missing_provider',
                   *['missing_export_' + name for name in BOOTSTRAP_LABELS]]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')


def framed(body_hex, receive=False):
    body = bytes.fromhex(body_hex)
    data = bytes.fromhex('80f010' if receive else '8010f0') + bytes([len(body)]) + body
    return (data + bytes([sum(data) & 255])).hex()


def expected_wires(case):
    tx, rx = TX.copy(), RX.copy()
    if case.startswith('seed_vector_'):
        vector = json.loads(SEEDS.read_text())['seed_cases'][int(case.rsplit('_', 1)[1])]
        tx[4] = framed('2702' + vector['timer_and_stored_expected_key'])
        rx[3] = framed('6701' + vector['wire_seed'], receive=True)
    if case == 'physical_first_chunk_replay':
        tx[4] = '8010f00627024015f4978f'
        rx[3] = '80f010066701a917a34fa0'
    return tx, rx


def expected_tx_count(case):
    if case in SUCCESS or case.startswith('cleanup_'):
        return 22
    if case.startswith('upload_') or case == 'extra_ack_7':
        return 8
    if case.startswith('physical_83') or case in ('wrong_83', 'bad_checksum_83'):
        return 3
    if case in ('wrong_81', 'bad_checksum_81'):
        return 2
    if case.startswith(('open_', 'version_', 'connect_', 'set_', 'get_', 'filter_', 'journal_')):
        return 0
    if case.startswith('seed_'):
        return 4
    if case in ('fail_baud', 'mutate_baud', 'clear_tx_fail', 'clear_rx_fail'):
        return 6
    if case.startswith(('wait_fail_', 'wait_short_')):
        return 5 if case.endswith('_0') else 6
    if re.fullmatch(r'(bad_ack|negative_ack|bad_checksum|status16|truncated|short_ack|extra_ack|write_fail|write_count_zero|write_count_large|write_mutation)_\d+', case):
        return int(case.rsplit('_', 1)[1]) + 1
    return 1


def check_message(message):
    fields = {'protocol', 'rx_status', 'tx_flags', 'timestamp', 'data_size', 'extra_data_index',
              'buffer_capacity', 'logged_bytes', 'data_truncated', 'data_hex'}
    check(fields <= message.keys(), 'Incomplete PASSTHRU_MSG record')
    check(message['buffer_capacity'] == 4128, 'Incorrect physical message capacity')
    count = min(message['data_size'], 4128)
    check(message['logged_bytes'] == count, 'Bounded logging length mismatch')
    check(len(bytes.fromhex(message['data_hex'])) == count, 'Missing or excess logged bytes')
    check(message['data_truncated'] == (message['data_size'] > 4128), 'Incorrect truncation flag')


def check_config(config, count):
    check(config['list_present'] and config['owned_capacity'] == count, 'Config capacity/presence')
    check(len(config['owned_buffer_entries']) == count, 'Owned config entries not fully logged')


def check_zero_filter(message):
    check_message(message)
    expected = {'protocol': 3, 'rx_status': 0, 'tx_flags': 0, 'timestamp': 0,
                'data_size': 4, 'extra_data_index': 0, 'data_hex': '00000000'}
    check(all(message[k] == value for k, value in expected.items()), 'Filter differs from archived four-zero object')


def check_state(state):
    required = {'connection_contract', 'opened', 'device', 'connected', 'channel', 'tx_attempts',
                'requested_configuration', 'successful_set_calls', 'observed_configuration',
                'effective_configuration_valid', 'filter'}
    check(isinstance(state, dict) and required <= state.keys(), 'Missing per-call active state')
    check(state['connection_contract'] == {'protocol': 3, 'flags': 512, 'baud': 4800}, 'Active connection contract changed')
    requested = state['requested_configuration']
    check(requested == CONFIG[:len(requested)] and len(requested) <= 5, 'Requested configuration state is not ordered prefix')
    check(0 <= state['successful_set_calls'] <= len(requested), 'SET success accounting')
    check(0 <= state['tx_attempts'] <= 22, 'Active state TX ceiling')
    check({'clock_model', 'requested_baud', 'baud_set_accepted', 'clear_mask'} <= state.keys(), 'Missing continuation state')
    check(state['requested_baud'] in (4800, 15625) and 0 <= state['clear_mask'] <= 3, 'Invalid baud/clear state')
    check(state['clock_model'] in ('VIRTUAL_ONLY_NOT_PHYSICAL_TIME', 'QPC_MONOTONIC_MINIMUM'), 'Unexpected clock model')
    if state['clock_model'] == 'VIRTUAL_ONLY_NOT_PHYSICAL_TIME':
        check(0 <= state['virtual_ms'] <= 500 and 'monotonic_ms' not in state, 'Invalid virtual schedule state')
    else:
        check(state['monotonic_ms'] > 0 and 'virtual_ms' not in state, 'Invalid real clock state')
    if state['observed_configuration'] is not None:
        check(len(state['observed_configuration']) == 5, 'Returned configuration state missing entries')
    if state['effective_configuration_valid']:
        check(state['observed_configuration'] == CONFIG, 'Effective configuration contradicts returned values')
    filt = state['filter']
    check({'requested', 'active', 'id', 'type', 'requested_mask_hex', 'requested_pattern_hex',
           'requested_flow_hex', 'protocol', 'flags', 'returned_objects_valid', 'observed_mask',
           'observed_pattern', 'observed_flow'} <= filt.keys(), 'Incomplete active filter state')
    check(filt['type'] == 1 and filt['protocol'] == 3 and filt['flags'] == 0, 'Filter state contract changed')
    check(all(filt[key] == '00000000' for key in ('requested_mask_hex', 'requested_pattern_hex', 'requested_flow_hex')), 'Filter state masks changed')
    for key in ('observed_mask', 'observed_pattern', 'observed_flow'):
        if filt[key] is not None:
            check_message(filt[key])
        if filt['returned_objects_valid']:
            check_zero_filter(filt[key])


def inspect_successful_physical_replay(rows):
    source = [json.loads(line) for line in SUCCESSFUL_PHYSICAL_LOG.read_text().splitlines()]
    original = [r for r in source if r.get('type') == 'api_return']
    replay = [r for r in rows if r.get('type') == 'api_return']
    original_rx = [r for r in original if r['function'] == 'PassThruReadMsgs']
    replay_rx = [r for r in replay if r['function'] == 'PassThruReadMsgs'][:6]
    check(len(original_rx) == len(replay_rx) == 6, 'Successful physical SOM/BF/SOM/C1/SOM/C3 sequence missing')
    for old, new in zip(original_rx, replay_rx):
        check(old['status'] == new['status'] == 0 and old['output'] == new['output'],
              'Successful physical RX bytes/count/full metadata not reproduced')
    original_version = next(r for r in original if r['function'] == 'PassThruReadVersion')
    replay_version = next(r for r in replay if r['function'] == 'PassThruReadVersion')
    check(original_version['status'] == replay_version['status'] == 0
          and original_version['output'] == replay_version['output'], 'Physical ReadVersion buffers not reproduced exactly')
    original_tx = [r for r in original if r['function'] == 'PassThruWriteMsgs']
    replay_tx = [r for r in replay if r['function'] == 'PassThruWriteMsgs'][:3]
    check(len(original_tx) == len(replay_tx) == 3, 'Physical request prefix missing')
    for old, new in zip(original_tx, replay_tx):
        check(old['status'] == new['status'] == 0 and old['output'] == new['output'],
              'Physical transmitted bytes/count/metadata not reproduced')
        for key in ('message', 'timeout_ms', 'input_count', 'message_capacity', 'count_pointer_present'):
            check(old['input'][key] == new['input'][key], 'Physical TX input contract differs')
    # Device/channel/filter handles remain explicitly synthetic. Host QPC/UTC
    # also belongs to this replay and is never compared as historical bus timing.
    check(next(r for r in original if r['function'] == 'PassThruOpen')['output']['device'] == 1
          and next(r for r in replay if r['function'] == 'PassThruOpen')['output']['device'] == 700,
          'Documented physical/fake device mapping changed')
    check(next(r for r in original if r['function'] == 'PassThruConnect')['output']['channel'] == 3
          and next(r for r in replay if r['function'] == 'PassThruConnect')['output']['channel'] == 701,
          'Documented physical/fake channel mapping changed')
    check(next(r for r in original if r['function'] == 'PassThruStartMsgFilter')['output']['filter_id'] == 0
          and next(r for r in replay if r['function'] == 'PassThruStartMsgFilter')['output']['filter_id'] == 702,
          'Documented physical/fake filter mapping changed')


def inspect_physical_first_chunk_prefix(rows):
    originals = [json.loads(line) for line in PHYSICAL_FIRST_CHUNK_LOG.read_text().splitlines()]
    original = [r for r in originals if r.get('type') == 'api_return' and r['function'] not in CLEANUP]
    actual = [r for r in rows if r.get('type') == 'api_return' and r['function'] not in CLEANUP][:len(original)]
    check(len(original) == len(actual) == 40, 'Complete physical first-chunk API prefix missing')

    def mapped(value, replay=False):
        if isinstance(value, list):
            return [mapped(item, replay) for item in value]
        if not isinstance(value, dict):
            return value
        out = {}
        for key, item in value.items():
            if key in ('config_pointer', 'owned_buffer_pointer'):
                # Native positive pointer integrity is separately asserted. ASLR
                # addresses cannot be historical replay identities.
                out[key] = 'OWNED_CONFIG_BUFFER'
            elif replay and key in ('device', 'channel', 'filter_id'):
                expected = {'device': (700, 1), 'channel': (701, 3), 'filter_id': (702, 0)}[key]
                check(item == expected[0], 'Unexpected synthetic resource identifier')
                out[key] = expected[1]
            else:
                out[key] = mapped(item, replay)
        return out

    def projected(row, replay=False):
        name = row['function']
        if name in ('OfflineClockAdvance', 'MonotonicMinimumWait'):
            return {'function': 'REQUESTED_MINIMUM_WAIT', 'status': row['status'],
                    'milliseconds': row['input']['milliseconds'], 'reason': row['input']['reason']}
        return {'function': name, 'status': row['status'],
                'input': mapped(row['input'], replay), 'output': mapped(row['output'], replay)}

    check(all(row['status'] == 0 for row in original + actual), 'Physical success prefix contains an API failure')
    for old, new in zip(original, actual):
        check(projected(old) == projected(new, True), 'Physical first-chunk API input/output/order replay mismatch')
    original_rx = [r for r in original if r['function'] == 'PassThruReadMsgs']
    actual_rx = [r for r in actual if r['function'] == 'PassThruReadMsgs']
    check(len(original_rx) == len(actual_rx) == 16
          and all(a['output'] == b['output'] for a, b in zip(original_rx, actual_rx)),
          'Physical first-chunk sixteen RX bytes/metadata records changed')
    original_tx = [r for r in original if r['function'] == 'PassThruWriteMsgs']
    check(len(original_tx) == 8 and original_tx[4]['input']['message']['data_hex'] == '8010f00627024015f4978f',
          'Physical seed-derived key oracle changed')
    check(original_rx[7]['output']['message']['data_hex'] == '80f010066701a917a34fa0', 'Physical seed oracle changed')


def inspect_case(case, rows, returncode, stdout, real_clock=False):
    expected_tx, expected_rx = expected_wires(case)
    check(rows, 'Empty journal')
    start = [r for r in rows if r.get('type') == 'full_upload_start']
    check(len(start) == 1 and rows[0] == start[0], 'Missing unique backend selection evidence')
    check(start[0]['backend'] == 'STATIC_IN_PROCESS_FAKE' and start[0]['physical'] is False
          and start[0]['provider_loaded'] is False,
          'Wrong backend selection')
    check(start[0]['fixture'] == case and start[0]['kernel_sha256'] == KERNEL_SHA and start[0]['declaration_size'] == 1808,
          'Start fixture/kernel binding')
    check(start[0]['embedded_cipher_bytes'] == 1808 and start[0]['contract_sha256'] == sha(PHYSICAL_CONTRACT)
          and start[0]['time_model'] == ('QPC_MONOTONIC_MINIMUM' if real_clock else 'VIRTUAL_ONLY_NOT_PHYSICAL_TIME'),
          'Scope/timing limits missing')
    for row in rows:
        if 'physical' in row:
            check(row['physical'] is False, 'Physical backend event in offline test')
        if 'state' in row:
            check(row['state']['clock_model'] == ('QPC_MONOTONIC_MINIMUM' if real_clock else 'VIRTUAL_ONLY_NOT_PHYSICAL_TIME'),
                  'Clock model differs from selected fake mode')
    intents = [r for r in rows if r.get('type') == 'api_intent']
    returns = [r for r in rows if r.get('type') == 'api_return']
    terminal = [r for r in rows if r.get('type') == 'probe_terminal']
    check(len(terminal) == 1 and rows[-1] == terminal[0], 'Missing or nonterminal final result')
    terminal = terminal[0]
    check_state(terminal['state'])
    check([r['sequence'] for r in intents] == list(range(len(intents))), 'Call intent sequence gaps/repeats')
    paired = {r['sequence']: r for r in returns}
    check(len(paired) == len(returns), 'Duplicate API return')
    missing = [r for r in intents if r['sequence'] not in paired]
    if case != 'journal_failure_after_filter':
        check(not missing and len(intents) == len(returns), 'Unpaired API call')
    else:
        check(len(missing) == 1 and missing[0]['function'] == 'PassThruStartMsgFilter', 'Unexpected journal-failure gap')
    prior_qpc = -1
    for intent in intents:
        check_state(intent['state'])
        check(intent['function'] in ['PassThruOpen', 'PassThruReadVersion', 'PassThruConnect',
              'PassThruIoctl', 'PassThruStartMsgFilter', 'PassThruWriteMsgs', 'PassThruReadMsgs',
              'MonotonicMinimumWait' if real_clock else 'OfflineClockAdvance'] + CLEANUP,
              'Unexpected API call in fixed probe')
        check(intent['host_event_counter'] >= prior_qpc, 'Nonmonotonic call timing')
        if intent['sequence'] not in paired:
            continue
        ret = paired[intent['sequence']]
        check_state(ret['state'])
        check(ret['function'] == intent['function'] and ret['input'] == intent['input'], 'Call input/return identity changed')
        check(isinstance(ret['status'], int), 'Missing native return status')
        check(intent['host_event_counter'] <= ret['qpc_before'] <= ret['qpc_after'], 'API timing includes impossible order')
        check(ret['api_elapsed_ticks'] == ret['qpc_after'] - ret['qpc_before'], 'API elapsed ticks mismatch')
        check(ret['qpc_frequency'] > 0 and ret['utc_filetime'] >= intent['utc_filetime'], 'Invalid clock evidence')
        prior_qpc = ret['qpc_after']
        if 'esp_before' in ret:
            check(ret['esp_before'] == ret['esp_after'], 'x86 call stack changed')
        for record in (intent['input'], ret['output']):
            if 'message' in record:
                check_message(record['message'])
            for key in ('mask', 'pattern', 'flow'):
                if key in record:
                    check_message(record[key])

    tx = [r for r in intents if r['function'] == 'PassThruWriteMsgs']
    check(len(tx) == expected_tx_count(case), 'Wrong failure boundary / TX count')
    check([r['input']['message']['data_hex'] for r in tx] == expected_tx[:len(tx)], 'Wire whitelist/order violated')
    check(len(tx) <= 22 and terminal['state']['tx_attempts'] == len(tx), 'Transmit accounting or ceiling')
    for record in tx:
        check(record['input']['timeout_ms'] == 1000 and record['input']['input_count'] == 1
              and record['input']['message_capacity'] == 1, 'Write timeout/count/capacity changed')
        message = record['input']['message']
        check(message['protocol'] == 3 and message['rx_status'] == message['tx_flags'] == message['timestamp'] == message['extra_data_index'] == 0,
              'TX metadata changed')
    for record in intents:
        if record['function'] == 'PassThruReadMsgs':
            check(1 <= record['input']['timeout_ms'] <= 1000, 'Read slice exceeds existing bound')
            check(record['input']['input_count'] == 1 and record['input']['message_capacity'] == 1, 'Read count/capacity changed')

    connects = [r for r in intents if r['function'] == 'PassThruConnect']
    if connects:
        check(all(connects[0]['input'][k] == v for k, v in {'device': 700, 'protocol': 3, 'flags': 512, 'baud': 4800}.items()), 'Connect contract changed')
    all_sets = [r for r in intents if r['function'] == 'PassThruIoctl' and r['input']['ioctl'] == 2]
    baud_sets = [r for r in all_sets if r['input']['config']['owned_buffer_entries'][0]['parameter'] == 1]
    sets = [r for r in all_sets if r not in baud_sets]
    gets = [r for r in intents if r['function'] == 'PassThruIoctl' and r['input']['ioctl'] == 1]
    check(all(r['input']['ioctl'] in (1, 2, 7, 8) for r in intents if r['function'] == 'PassThruIoctl'), 'Unexpected IOCTL')
    for index, record in enumerate(sets):
        inp = record['input']
        check(index < 5 and inp['input_present'] and not inp['output_present'] and inp['channel'] == 701, 'SET_CONFIG argument contract')
        check_config(inp['config'], 1)
        check(inp['config']['returned_num_params'] == 1 and inp['config']['pointer_matches_owned'], 'SET_CONFIG input list')
        check(inp['config']['owned_buffer_entries'] == [CONFIG[index]], 'SET_CONFIG order/value')
        check_config(paired[record['sequence']]['output']['config'], 1)
    check(len(gets) <= 1, 'GET_CONFIG retried')
    if gets:
        record = gets[0]
        check(len(sets) == 5 and sets[-1]['sequence'] + 1 == record['sequence'], 'GET not immediately after five SET calls')
        check(record['input']['input_present'] and not record['input']['output_present'], 'GET list must use pInput')
        inp = record['input']['config']
        check_config(inp, 5)
        check(inp['returned_num_params'] == 5 and inp['pointer_matches_owned'], 'GET input list integrity')
        check(inp['owned_buffer_entries'] == [{'parameter': v['parameter'], 'value': SENTINEL} for v in CONFIG], 'GET input values not sentinel initialized')
        check_config(paired[record['sequence']]['output']['config'], 5)
    filters = [r for r in intents if r['function'] == 'PassThruStartMsgFilter']
    check(len(filters) <= 1, 'Filter retried')
    if filters:
        record = filters[0]
        inp = record['input']
        check(len(gets) == 1 and gets[0]['sequence'] + 1 == record['sequence'], 'Filter not immediately after GET round trip')
        returned = paired[gets[0]['sequence']]['output']['config']
        check(returned['owned_buffer_entries'] == CONFIG and returned['returned_num_params'] == 5 and returned['pointer_matches_owned'], 'Filter after invalid effective config')
        check(inp['filter_type'] == 1 and inp['channel'] == 701, 'Broad filter type/channel')
        check(all(inp[k] is True for k in ('mask_present', 'pattern_present', 'flow_present', 'filter_output_present')), 'Nonnull flow/filter pointers missing')
        for key in ('mask', 'pattern', 'flow'):
            check_zero_filter(inp[key])
    if tx:
        check(len(sets) == 5 and len(gets) == 1 and len(filters) == 1, 'TX before full setup')
        check(filters[0]['sequence'] < tx[0]['sequence'], 'BF before filter')

    # The exact non-read control sequence rules out duplicate downloads, retries,
    # seed/key before C3, baud before acknowledged session and progress after a failure.
    def action(record):
        name, inp = record['function'], record['input']
        if name == 'PassThruIoctl':
            if inp['ioctl'] in (1, 2):
                return (name, inp['ioctl'], inp['config']['owned_buffer_entries'][0]['parameter'])
            return (name, inp['ioctl'])
        if name == 'PassThruWriteMsgs':
            return (name, inp['message']['data_hex'])
        if name in ('OfflineClockAdvance', 'MonotonicMinimumWait'):
            return (name, inp['milliseconds'], inp['reason'])
        return (name,)
    schedule = [(name,) for name in ('PassThruOpen', 'PassThruReadVersion', 'PassThruConnect')]
    schedule += [('PassThruIoctl', 2, x['parameter']) for x in CONFIG]
    schedule += [('PassThruIoctl', 1, 22), ('PassThruStartMsgFilter',)]
    schedule += [('PassThruWriteMsgs', wire) for wire in expected_tx[:5]]
    wait_name = 'MonotonicMinimumWait' if real_clock else 'OfflineClockAdvance'
    schedule += [(wait_name, 200, 'post_key_ack'), ('PassThruWriteMsgs', expected_tx[5]),
                 (wait_name, 100, 'post_session_ack'), ('PassThruIoctl', 2, 1),
                 ('PassThruIoctl', 7), ('PassThruIoctl', 8),
                 (wait_name, 200, 'pre_download_declaration'),
                 ('PassThruWriteMsgs', expected_tx[6])]
    schedule += [('PassThruWriteMsgs', wire) for wire in expected_tx[7:]]
    actual_schedule = [action(r) for r in intents if r['function'] not in CLEANUP + ['PassThruReadMsgs']]
    check(actual_schedule == schedule[:len(actual_schedule)] and len(actual_schedule) <= len(schedule),
          'Continuation control sequence/order or single34 boundary changed')
    waits = [r for r in intents if r['function'] == wait_name]
    wait_measurements = []
    for index, record in enumerate(waits):
        inp, ret = record['input'], paired[record['sequence']]
        out = ret['output']
        before = [0, 200, 300][index]
        duration = [200, 100, 200][index]
        expected_delta = 0 if case == f'wait_fail_{index}' else duration - (case == f'wait_short_{index}')
        check(inp['milliseconds'] == inp['requested_ms'] == duration, 'Exact requested wait changed')
        if not real_clock:
            check(inp['model'] == 'VIRTUAL_ONLY_NOT_PHYSICAL_TIME' and inp['virtual_before'] == before,
                  'Wait input schedule/model changed')
            check(out['virtual_after'] == before + expected_delta, 'Injected virtual wait duration not observed')
        else:
            check(inp['model'] == 'QPC_MONOTONIC_MINIMUM' and out['requested_ms'] == duration,
                  'Real minimum-wait model/request missing')
            ticks, hz = ret['api_elapsed_ticks'], ret['qpc_frequency']
            minimum = (hz * duration + 999) // 1000
            check(ticks * 1000 >= duration * hz and ticks >= minimum, 'Real-clock wait shorter than requested minimum')
            check(out['minimum_satisfied'] is True and out['minimum_qpc_ticks'] == minimum
                  and out['elapsed_qpc_ticks'] == ticks and out['qpc_frequency'] == hz,
                  'Wait output disagrees with independent QPC call timing')
            check(out['overshoot_qpc_ticks'] == ticks - minimum
                  and out['monotonic_after_ms'] >= inp['monotonic_before_ms'] + duration,
                  'Wait overshoot or monotonic millisecond evidence incorrect')
            wait_measurements.append({'requested_ms': duration, 'elapsed_qpc_ticks': ticks,
                                      'qpc_frequency': hz, 'minimum_qpc_ticks': minimum,
                                      'overshoot_qpc_ticks': ticks - minimum})
    check(len(baud_sets) <= 1, 'Baud SET repeated')
    if baud_sets:
        record = baud_sets[0]
        inp, ret = record['input'], paired[record['sequence']]
        check(inp['channel'] == 701 and inp['input_present'] and not inp['output_present'], 'Baud SET arguments')
        check_config(inp['config'], 1)
        check(inp['config']['owned_buffer_entries'] == [{'parameter': 1, 'value': 15625}], 'Baud request changed')
        check_config(ret['output']['config'], 1)
        returned_baud = 15626 if case == 'mutate_baud' else 15625
        check(ret['output']['config']['owned_buffer_entries'] == [{'parameter': 1, 'value': returned_baud}], 'Baud output not preserved')
        check(ret['status'] == (7 if case == 'fail_baud' else 0), 'Baud status fixture mismatch')
        check(ret['state']['baud_set_accepted'] == (ret['status'] == 0), 'Baud accepted state contradicts API return')
    clears = [r for r in intents if r['function'] == 'PassThruIoctl' and r['input']['ioctl'] in (7, 8)]
    for record in clears:
        check(record['input']['channel'] == 701 and not record['input']['input_present'] and not record['input']['output_present'],
              'Queue clear pointer/channel contract')
    if len(tx) >= 7:
        check(len(waits) == 3 and len(baud_sets) == 1 and len(clears) == 2, 'Upload before waits/baud/queue clears')
        check((real_clock or tx[6]['state']['virtual_ms'] == 500) and tx[6]['state']['clear_mask'] == 3 and tx[6]['state']['baud_set_accepted'],
              'Download before accepted continuation state')

    # Successful allocations require cleanup even when subsequent output validation fails.
    acquired = {r['function'] for r in returns if r['status'] == 0}
    expected_cleanup = []
    if 'PassThruStartMsgFilter' in acquired or case == 'journal_failure_after_filter':
        expected_cleanup.append(CLEANUP[0])
    if 'PassThruConnect' in acquired:
        expected_cleanup.append(CLEANUP[1])
    if 'PassThruOpen' in acquired:
        expected_cleanup.append(CLEANUP[2])
    cleanup = [r for r in intents if r['function'] in CLEANUP]
    check([r['function'] for r in cleanup] == expected_cleanup, 'Missing/reordered/repeated cleanup')
    if cleanup:
        check(intents[-len(cleanup):] == cleanup, 'Protocol operation after cleanup started')
    cleanup_mask = 0
    for record in cleanup:
        ret = paired[record['sequence']]
        if ret['status']:
            cleanup_mask |= 1 << CLEANUP.index(record['function'])
    check(terminal['cleanup_error_mask'] == cleanup_mask, 'Cleanup status not reflected in outcome')
    expected_cleanup_mask = {'cleanup_stop_fail': 1, 'cleanup_disconnect_fail': 2,
                             'cleanup_close_fail': 4, 'cleanup_all_fail': 7,
                             'physical_83_cleanup_all_fail': 7}.get(case, 0)
    check(cleanup_mask == expected_cleanup_mask, 'Expected cleanup failure was not injected')
    check(terminal['cleanup_confirmed'] == (cleanup_mask == 0), 'Cleanup confirmation contradicts returns')
    noncleanup = [r for r in returns if r['function'] not in CLEANUP]
    errors = [r for r in noncleanup if r['status']]
    if errors:
        check(len(errors) == 1 and errors[0] == noncleanup[-1], 'Progress/retry after nonzero API status')
    success = case in SUCCESS
    check(returncode == (0 if success else 1), 'Unexpected process exit code')
    check(terminal['status'] == ('PASS_OFFLINE_FULL_KERNEL_UPLOAD_NO_START_ONLY' if success else 'FAIL_TERMINAL'), 'Terminal status mismatch')
    check(('PASS_OFFLINE_FULL_KERNEL_UPLOAD_NO_START_ONLY' in stdout) == success, 'Console success mismatch')
    check(terminal['protocol_complete'] == (success or case.startswith('cleanup_')), 'Protocol-complete claim at wrong stage')
    if success:
        check(not errors and not cleanup_mask and not terminal['log_failed'], 'Success with API/cleanup/log error')
        assembled = []
        stage = -1
        for record in noncleanup:
            if record['function'] == 'PassThruWriteMsgs':
                stage += 1
                assembled.append('')
            elif record['function'] == 'PassThruReadMsgs' and record['output']['message']['rx_status'] == 0:
                assembled[stage] += record['output']['message']['data_hex']
        check(assembled == expected_rx, 'Successful native parser did not consume exact expected full replies')
        check(actual_schedule == schedule and (real_clock or terminal['state']['virtual_ms'] == 500), 'Success without complete schedule')

    # Prove each hostile fixture reached its intended injected condition, not an unrelated early error.
    last = noncleanup[-1]
    if case.startswith('set_fail_'):
        check(len(sets) == int(case[-1]) + 1 and last['status'] == 7 and not gets, 'SET failure not injected at requested index')
    if case == 'set_mutation':
        check(last['output']['config']['owned_buffer_entries'][0]['value'] == 99 and not gets, 'SET mutation not observed')
    if case.startswith('get_'):
        check(len(gets) == 1 and not filters, 'GET failure advanced to filter')
        config = last['output']['config']
        if case.startswith('get_wrong_'):
            check(config['owned_buffer_entries'][int(case[-1])]['value'] == 99, 'Wrong GET value not logged')
        if case == 'get_fail':
            check(last['status'] == 7 and config['owned_buffer_entries'] == CONFIG, 'GET error outputs discarded')
        if case == 'get_sentinel':
            check(all(x['value'] == SENTINEL for x in config['owned_buffer_entries']), 'Unchanged GET sentinels not logged')
        if case.startswith('get_count_'):
            check(config['returned_num_params'] == (0 if case.endswith('zero') else 6), 'Malformed GET count not logged')
        if case.startswith('get_pointer_'):
            check(config['config_pointer'] == (0 if case.endswith('null') else 1) and not config['pointer_matches_owned'], 'Malformed GET pointer not logged')
        if case == 'get_parameter':
            check(config['owned_buffer_entries'][2]['parameter'] == 99, 'Malformed GET parameter not logged')
    if case == 'filter_mutation':
        check(last['output']['flow']['data_hex'] == '01000000', 'Filter mutation not logged')
    if case in ('write_count_zero', 'write_count_large', 'read_count_zero', 'read_count_large'):
        check(last['output']['count'] == (0 if case.endswith('zero') else 2) and last['status'] == 0, 'Count bound fixture not injected')
    if case == 'write_mutation':
        check(last['output']['message']['data_hex'] != TX[0], 'Write mutation missing')
    if case == 'read_error_output':
        check(last['status'] == 16 and last['output']['count'] == 1 and last['output']['message']['data_hex'] == BF, 'Error-return data not preserved')
    if case.startswith('physical_83'):
        check(last['function'] == 'PassThruReadMsgs' and last['status'] == 16 and last['output']['count'] == 0, 'Recorded status16 outcome changed')
        originals = [json.loads(line) for line in RK02_LOG.read_text().splitlines()]
        originals = [r for r in originals if r.get('function') == 'PassThruReadMsgs']
        replay = [r for r in noncleanup if r['function'] == 'PassThruReadMsgs']
        check(len(originals) == len(replay) == 5, 'Recorded SOM/BF/SOM/C1/error sequence changed')
        mapping = {'protocol': 'protocol', 'rx_status': 'rx_status', 'tx_flags': 'tx_flags',
                   'timestamp': 'timestamp', 'data_size': 'data_size', 'extra': 'extra_data_index', 'wire_hex': 'data_hex'}
        for original, record in zip(originals, replay):
            check(original['status'] == record['status'] and original['count'] == record['output']['count'], 'Recorded RX status/count changed')
            check(all(original[old] == record['output']['message'][new] for old, new in mapping.items()), 'Recorded RX bytes/metadata changed')
    if case == 'physical_transition_replay':
        inspect_successful_physical_replay(rows)
    if case == 'physical_first_chunk_replay':
        inspect_physical_first_chunk_prefix(rows)
    direct_error = {'open_fail': 'PassThruOpen', 'version_fail': 'PassThruReadVersion',
                    'connect_fail': 'PassThruConnect', 'filter_fail': 'PassThruStartMsgFilter',
                    'write_fail': 'PassThruWriteMsgs'}
    if case in direct_error:
        check(last['function'] == direct_error[case] and last['status'] == 7, 'Named API failure was not injected')
    stage_cases = {'wrong_bf': 0, 'wrong_81': 1, 'wrong_83': 2,
                   'bad_checksum_bf': 0, 'bad_checksum_81': 1, 'bad_checksum_83': 2}
    if case in stage_cases:
        expected = bytearray.fromhex(RX[stage_cases[case]])
        if case.startswith('bad_checksum'):
            expected[-1] ^= 1
        else:
            expected[8 if case == 'wrong_bf' else 4] ^= 1
            expected[-1] = sum(expected[:-1]) & 255
        check(last['output']['message']['data_hex'] == expected.hex(), 'Wrong reply/checksum fixture not observed')
    if case == 'unexpected_frame':
        check(last['output']['message']['data_hex'] == RX[1], 'Unexpected complete frame not observed')
    read_returns = [r for r in noncleanup if r['function'] == 'PassThruReadMsgs']
    if case == 'rx_indicator_flood':
        check(len(read_returns) == 5 and all(r['output']['message']['rx_status'] == 2 for r in read_returns), 'Indicator flood boundary changed')
    if case == 'rx_indicator_after_data':
        check(len(read_returns) == 2 and read_returns[0]['output']['message']['data_hex'] == '80'
              and read_returns[1]['output']['message']['rx_status'] == 2, 'Post-data marker fixture not observed')
    if case == 'rx_marker_only':
        check(len(read_returns) == 2 and read_returns[0]['output']['message']['rx_status'] == 2
              and last['status'] == 16 and last['output']['count'] == 0, 'Marker-only exhaustion not terminal')
    if case == 'rx_wrong_echo':
        check(last['output']['message']['rx_status'] == 1 and last['output']['message']['data_hex'] == '8110f001bf40', 'Wrong echo not preserved')
    if case == 'rx_trailing':
        check(last['output']['message']['data_hex'] == BF + '00', 'Trailing-byte fixture not observed')
    if case in ('rx_wrong_direction', 'rx_zero_length'):
        expected = bytearray.fromhex(BF)
        expected[1 if case == 'rx_wrong_direction' else 3] = 0x10 if case == 'rx_wrong_direction' else 0
        check(last['output']['message']['data_hex'] == expected.hex(), 'Malformed framing fixture not observed')
    mutations = {'rx_oversize': ('data_size', 5000), 'rx_protocol': ('protocol', 4), 'rx_flags': ('tx_flags', 1),
                 'rx_extra': ('extra_data_index', 1), 'rx_unknown_status': ('rx_status', 256),
                 'rx_combined_status': ('rx_status', 3), 'rx_nonempty_indicator': ('rx_status', 2), 'rx_empty': ('data_size', 0)}
    if case in mutations:
        field, value = mutations[case]
        check(last['output']['message'][field] == value, 'Malformed RX field missing from journal')
    if case == 'version_nonascii':
        version = next(r for r in returns if r['function'] == 'PassThruReadVersion')
        check(version['output']['dll']['raw_buffer_hex'].startswith('ff'), 'Non-ASCII version byte not preserved')
    if case == 'version_unterminated':
        check(not last['output']['dll']['nul_terminated'] and len(bytes.fromhex(last['output']['dll']['raw_buffer_hex'])) == 80, 'Unterminated version not bounded/logged')
    if case == 'journal_failure_after_filter':
        check(terminal['log_failed'] and len(cleanup) == 3, 'Journal failure did not fail closed and clean up')
    # The inherited names bad_checksum_81/83 name service bytes, not stage indices.
    indexed = re.fullmatch(r'(bad_ack|negative_ack|bad_checksum|status16|truncated|short_ack|extra_ack)_([3-9]|1[0-9]|2[01])', case)
    if indexed:
        kind, stage = indexed.group(1), int(indexed.group(2))
        check(len(tx) == stage + 1, 'Later-stage rejection boundary changed')
        if kind == 'status16':
            check(last['function'] == 'PassThruReadMsgs' and last['status'] == 16 and last['output']['count'] == 0,
                  'Later-stage status16 not preserved')
        elif kind == 'truncated':
            tail = [r for r in noncleanup if r['sequence'] > tx[-1]['sequence']]
            check(len(tail) == 2 and tail[0]['output']['message']['data_hex'] == expected_rx[stage][:6]
                  and tail[1]['status'] == 16 and tail[1]['output']['count'] == 0, 'Truncated later reply did not fail without retry')
        else:
            bad = bytearray.fromhex(expected_rx[stage])
            if kind == 'bad_ack':
                bad[4] ^= 1
                bad[-1] = sum(bad[:-1]) & 255
            elif kind == 'negative_ack':
                bad = bytearray.fromhex(framed('7f' + expected_tx[stage][8:10] + '22', receive=True))
            elif kind == 'bad_checksum':
                bad[-1] ^= 1
            elif kind == 'short_ack':
                del bad[-2]
                bad[3] -= 1
                bad[-1] = sum(bad[:-1]) & 255
            elif kind == 'extra_ack':
                bad.insert(len(bad) - 1, 0)
                bad[3] += 1
                bad[-1] = sum(bad[:-1]) & 255
            check(last['output']['message']['data_hex'] == bad.hex() and last['status'] == 0,
                  'Later malformed reply did not reach native validator')
    if case in ('seed_short', 'seed_extra', 'seed_wrong_subfunction', 'extra_ack_7'):
        bad = bytearray.fromhex(RX[7 if case == 'extra_ack_7' else 3])
        if case == 'seed_short':
            del bad[-2]
            bad[3] -= 1
        elif case == 'seed_wrong_subfunction':
            bad[5] = 2
        else:
            bad.insert(len(bad) - 1, 0)
            bad[3] += 1
        bad[-1] = sum(bad[:-1]) & 255
        check(last['output']['message']['data_hex'] == bad.hex() and last['status'] == 0, 'Malformed payload fixture missing')
    if case.startswith('upload_'):
        message = last['output']['message']
        check(last['status'] == 0 and len(tx) == 8, 'Upload metadata fixture rejected at unrelated stage')
        if case == 'upload_unknown_status':
            check(message['rx_status'] == 256 and message['data_size'] == 0, 'Upload unknown RX status missing')
        elif case == 'upload_wrong_echo':
            check(message['rx_status'] == 1 and message['data_hex'] == '81' + TX[7][2:], 'Upload echo mutation missing')
        elif case == 'upload_rx_extra':
            check(message['extra_data_index'] == 1 and message['data_hex'] == RX[7], 'Upload extra-index mutation missing')
    if case.startswith('wait_fail_'):
        check(last['function'] == 'OfflineClockAdvance' and last['status'] == 7, 'Wait failure not injected')
    if case.startswith('wait_short_'):
        check(last['function'] == 'OfflineClockAdvance' and last['status'] == 0, 'Short wait did not reach duration guard')
    if case in ('fail_baud', 'mutate_baud', 'clear_tx_fail', 'clear_rx_fail'):
        check(last['function'] == 'PassThruIoctl' and len(tx) == 6, 'Baud/queue failure advanced to download')
        if case.startswith('clear_'):
            check(last['input']['ioctl'] == (7 if case == 'clear_tx_fail' else 8) and last['status'] == 7,
                  'Named queue clear failure not injected')
    later_write = re.fullmatch(r'(write_fail|write_count_zero|write_count_large|write_mutation)_(\d+)', case)
    if later_write:
        kind, stage = later_write.group(1), int(later_write.group(2))
        check(last['function'] == 'PassThruWriteMsgs' and len(tx) == stage + 1,
              'Later write fault did not stop at intended chunk')
        if kind == 'write_fail':
            check(last['status'] == 7 and last['output']['count'] == 1, 'Later write error status/count not preserved')
        elif kind == 'write_count_zero':
            check(last['status'] == 0 and last['output']['count'] == 0, 'Later zero write count not injected')
        elif kind == 'write_count_large':
            check(last['status'] == 0 and last['output']['count'] == 2, 'Later excess write count not injected')
        else:
            check(last['status'] == 0 and last['output']['count'] == 1
                  and last['output']['message']['data_hex'] == '81' + expected_tx[stage][2:], 'Later write mutation not preserved')
    return {'tx_attempts': len(tx), 'api_intents': len(intents), 'api_returns': len(returns),
            'cleanup_functions': expected_cleanup, 'cleanup_error_mask': cleanup_mask,
            'last_protocol_api_status': last['status'], 'protocol_complete': terminal['protocol_complete'],
            'wait_calls': len(waits), 'clock_model': terminal['state']['clock_model'],
            'virtual_ms': terminal['state'].get('virtual_ms'), 'real_wait_measurements': wait_measurements,
            'queue_clears_attempted': len(clears),
            'baud_set_calls': len(baud_sets),
            'status': 'PASS'}


def verify_pin_entries(entries):
    check(isinstance(entries, list) and entries, 'Empty or malformed input pins')
    for item in entries:
        check(sha(item['path']) == item['sha256'].lower(), 'Input changed: ' + item['path'])




def inspect_bootstrap(case, rows, returncode, stdout, journal):
    check(len(rows) == 1 and rows[0]['type'] == 'offline_bootstrap_result', 'Unexpected bootstrap journal activity')
    row = rows[0]
    check(row['physical'] is False and row['fixture'] == case and row['fixture_token'] == 'OFFLINE_BOOTSTRAP_TEST_ONLY',
          'Bootstrap selected physical bindings or wrong case')
    check(row['provider_load_attempts'] == row['api_calls'] == 0, 'Offline bootstrap reached a loader/API call')
    check(returncode == 0 and row['status'] == 'PASS_OFFLINE_BOOTSTRAP_TEST' and 'PASS_OFFLINE_BOOTSTRAP_TEST' in stdout,
          'Native bootstrap fixture did not satisfy expected result')
    phase_by_case = {
        'valid_gates_no_load': 'OFFLINE_HARD_STOP_BEFORE_LOADER',
        'wrong_session_path': 'FIXED_PATH', 'wrong_auth_path': 'FIXED_PATH',
        'missing_contract': 'CONTRACT_HASH', 'wrong_contract_hash': 'CONTRACT_HASH',
        'missing_auth': 'AUTHORIZATION', 'malformed_auth': 'AUTHORIZATION',
        'wrong_exe_hash': 'AUTHORIZATION', 'wrong_auth_contract': 'AUTHORIZATION',
        'missing_reservation': 'ROOT_RESERVATION', 'wrong_reservation': 'ROOT_RESERVATION',
        'consumed_marker': 'NATIVE_ONCE', 'wrong_provider_hash': 'PROVIDER_HASH', 'missing_provider': 'PROVIDER_HASH',
    }
    phase = 'EXPORTS' if case.startswith('missing_export_') else phase_by_case[case]
    check(row['phase'] == phase, 'Bootstrap failed at an unrelated boundary')
    valid = case == 'valid_gates_no_load'
    check(row['reached_hard_stop'] == valid and bool(row['error']) != valid, 'Bootstrap hard-stop/error claim incorrect')
    after_once = phase in ('PROVIDER_HASH', 'EXPORTS', 'OFFLINE_HARD_STOP_BEFORE_LOADER')
    opened_provider = after_once and case != 'missing_provider'
    check(row['marker_consumed'] == after_once and row['provider_file_opened'] == opened_provider,
          'Bootstrap allocation/reservation boundary incorrect')
    exports = BOOTSTRAP_EXPORTS if valid else []
    if case.startswith('missing_export_'):
        index = BOOTSTRAP_LABELS.index(case[len('missing_export_'):])
        exports = BOOTSTRAP_EXPORTS[:index + 1]
    check(row['requested_exports'] == exports, 'Shared export validation order/failure boundary changed')
    fixture = Path(str(journal) + '.fixture')
    check(fixture.is_dir() and fixture.parent == journal.parent, 'Bootstrap fixture directory escaped report')
    for name, content in [('fixture_executable.bin', b'OFFLINE DUMMY EXECUTABLE BYTES; NEVER EXECUTED\n'),
                          ('fixture_contract.json', b'OFFLINE DUMMY CONTRACT BYTES\n'),
                          ('fixture_provider.bin', b'OFFLINE DUMMY PROVIDER BYTES; NEVER LOADED\n')]:
        check((fixture/name).read_bytes() == content, 'Bootstrap used unexpected executable/contract/provider bytes')
    exe_sha, contract_sha = sha(fixture/'fixture_executable.bin'), sha(fixture/'fixture_contract.json')
    auth_exe = '0' * 64 if case == 'wrong_exe_hash' else exe_sha
    auth_contract = '0' * 64 if case == 'wrong_auth_contract' else contract_sha
    auth = ('OFFLINE_BOOTSTRAP_TEST_ONLY\nSESSION_ID=OFFLINE_BOOTSTRAP_FIXTURE\nEXE_SHA256=' + auth_exe
            + '\nCONTRACT_SHA256=' + auth_contract + '\n')
    if case == 'malformed_auth':
        auth += 'EXTRA_LINE\n'
    if case == 'missing_auth':
        check(not (fixture/'AUTHORIZATION.txt').exists(), 'Missing authorization was not actually missing')
    else:
        check((fixture/'AUTHORIZATION.txt').read_bytes() == auth.encode('ascii'), 'Bootstrap authorization mutation differs')
    reserved = 'OFFLINE_BOOTSTRAP_FIXTURE\n' + exe_sha + '\n' + contract_sha + '\n'
    if case == 'missing_reservation':
        check(not (fixture/'launch.reserved').exists(), 'Missing root reservation was not missing')
    else:
        value = reserved + ('EXTRA_LINE\n' if case == 'wrong_reservation' else '')
        check((fixture/'launch.reserved').read_bytes() == value.encode('ascii'), 'Bootstrap reservation mutation differs')
    marker = fixture/'invocation.once'
    if case == 'consumed_marker':
        check(marker.read_bytes() == b'PREVIOUS OFFLINE FIXTURE INVOCATION\n', 'Consumed native marker overwritten')
    elif after_once:
        check(marker.read_bytes() == reserved.encode('ascii'), 'New native reservation not persisted')
    else:
        check(not marker.exists(), 'Native reservation consumed before required gate checks')
    return {'status': 'PASS', 'tx_attempts': 0, 'phase': phase, 'marker_consumed': row['marker_consumed'],
            'provider_load_attempts': 0, 'api_calls': 0, 'fixture_directory': str(fixture),
            'requested_exports': exports}


def verify_first_chunk_contract():
    check(sha(FIRST_CHUNK_CONTRACT) == 'a7482b0eba224c9642745b830c71b3fff14f987988a58cdc1376e45dc0aa839c',
          'First-chunk review contract changed')
    contract = json.loads(FIRST_CHUNK_CONTRACT.read_text())
    check(contract['connect'] == {'protocol': 3, 'flags': 512, 'baud': 4800}
          and contract['set_config_order'] == CONFIG, 'Physical first-chunk transport contract differs')
    requests = contract['ordered_requests']
    check(len(requests) == 8 and [r['stage'] for r in requests] == list(range(8)), 'Eight-stage contract changed')
    for stage, request in enumerate(requests):
        if stage != 4:
            check(request['wire_hex'] == TX[stage], 'Fixed request differs from first-chunk contract')
    check(requests[4]['wire_hex'] == 'DERIVED_FROM_EXACT_FOUR_BYTE_SEED_BY_PINNED_ALGORITHM',
          'Variable-key request contract changed')
    transfer = contract['fixed_transfer']
    frame = bytes.fromhex(TX[7])
    cipher = frame[8:-1]
    check(len(frame) == 137 and len(cipher) == 128 and transfer['length'] == transfer['embedded_payload_bytes'] == 128,
          'Fixed first128-byte transfer bound changed')
    check(transfer['ram_address'] == 'FFFF3000' and transfer['end_exclusive'] == 'FFFF3080'
          and frame[4:8] == bytes.fromhex('36ff3000'), 'Fixed RAM range changed')
    check(transfer['cipher_hex'] == cipher.hex() and hashlib.sha256(cipher).hexdigest() == transfer['cipher_sha256']
          and hashlib.sha256(frame).hexdigest() == transfer['frame_sha256'], 'First-chunk bytes/hash differ from contract')
    check(transfer['frame_hex'] == TX[7] and transfer['download_declaration_size'] == 1808
          and transfer['source_kernel_sha256'] == KERNEL_SHA, 'Declaration/kernel source binding changed')
    check(hashlib.sha256(KERNEL.read_bytes()[:128]).hexdigest() == transfer['plaintext_sha256'],
          'Independent plaintext first128-byte pin differs')
    check(not contract['full_acquisition_allowed'] and not contract['automatic_retry_allowed']
          and contract['maximum_physical_invocations'] == 1, 'Qualification scope widened')
    verify_pin_entries(contract['reused_evidence'])
    check(sha(SUCCESSFUL_PHYSICAL_LOG) == '57352963c842fa8cef0f45769a8c0f9613994df9c198fe434ee78e73d262a68b',
          'Successful physical replay source changed')
    check(sha(PREVIOUS_RUNNER) == 'cb4d7d9f3f72f808967ec808bf10796d689f4f9f19d80d82f34be6422e2f156a'
          and sha(PREVIOUS_REPORT) == '9de655416e0452a60f5a20916cfc02db08f515447eec4c4e83239b59fa6ee2b0',
          'Previous127 qualification source/report changed')
    previous = json.loads(PREVIOUS_REPORT.read_text())
    check(previous['status'] == 'PASS' and previous['passed_cases'] == 127
          and {c['case'] for c in previous['cases']} <= set(CASES), 'Previous127 cases not retained')
    check(sha(FIRST_CHUNK_RUNNER) == '01bc991fb80ad10634cea7fbcebf9f3c4064c202568314e285fe3de8421fa921'
          and sha(FIRST_CHUNK_REPORT) == 'efb46f51d94ff624587b88228492535a8f441a0a9bcd1473d7f96329dde36e7b',
          'Previous156 qualification source/report changed')
    first = json.loads(FIRST_CHUNK_REPORT.read_text())
    check(first['status'] == 'PASS' and first['passed_cases'] == 156
          and {c['case'] for c in first['cases'] if c['mode'] == 'virtual'} <= set(CASES),
          'Previous128 virtual cases not retained; previous156 evidence invalid')
    check(sha(PHYSICAL_FIRST_CHUNK_LOG) == 'd258d9eb5b0690e8dd1c79d29f217aa86e152d866e1aeb1e938bf98aa13896a3',
          'Successful physical first-chunk source changed')
    return contract


def physical_control_snapshot():
    # Fake-only qualification must not create or alter a real physical session.
    return {'new_worktree_physical_session_exists': (PROBE.parent/'physical_session').exists()}


def verify_full_upload_contract():
    check(sha(FULL_UPLOAD_CONTRACT) == '3861d397a625a252394ab2c0fdd58af9bbf03c9996a7c98ec7de239270779a5f',
          'Offline full-upload review contract changed')
    contract = json.loads(FULL_UPLOAD_CONTRACT.read_text())
    check(contract['physical_entry_point'] is False and contract['provider_loader'] is False
          and contract['physical_authorization'] is False and contract['maximum_physical_invocations'] == 0,
          'Offline-only contract widened')
    check(contract['automatic_retry_allowed'] is False and contract['maximum_tx'] == 22
          and contract['download_declarations'] == 1 and contract['transfers'] == 15, 'Upload count/retry contract changed')
    check(contract['connect'] == {'protocol': 3, 'flags': 512, 'baud': 4800}
          and contract['set_config_order'] == CONFIG and contract['waits_ms'] == [200, 100, 200]
          and contract['baud_set'] == 15625 and contract['queue_clears_in_order'] == [7, 8],
          'Transport/schedule contract differs from independent oracle')
    check(contract['upload_start_inclusive'] == 'FFFF3000' and contract['upload_end_exclusive'] == 'FFFF3710'
          and contract['upload_bytes'] == 1808 and contract['payload_lengths'] == [128] * 14 + [16],
          'Fixed upload range/length contract changed')
    check(contract['kernel_sha256'] == KERNEL_SHA and contract['excluded_historical_frame_index'] == 16
          and contract['excluded_historical_frame_hex'] == '8010f003310101b6', 'Kernel source/handoff exclusion changed')
    requests = contract['ordered_requests']
    check(len(requests) == 22 and [r['stage'] for r in requests] == list(range(22)), 'Contract dispatch stages changed')
    for index, request in enumerate(requests):
        check(request['sample_wire_hex'] == TX[index] and request['expected_reply_hex'] == RX[index],
              'Contract sample request/reply differs from retained execution')
        check(request['wire_hex'] == (None if index == 4 else TX[index]), 'Fixed request/dynamic key boundary changed')
        check(request['dynamic_rule'] == ('2702 plus reviewed key derived from validated four-byte seed' if index == 4 else None),
              'Dynamic content allowed outside seed-derived key')
    cipher = b''.join(bytes.fromhex(wire)[8:-1] for wire in TX[7:])
    check(len(cipher) == 1808 and hashlib.sha256(cipher).hexdigest() == contract['cipher_sha256'],
          'Complete ciphertext differs from root contract')
    verify_pin_entries(contract['reused_evidence'])
    return contract


def verify_physical_contract():
    check(sha(PHYSICAL_CONTRACT) == PHYSICAL_CONTRACT_SHA, 'Physical release review contract changed')
    contract = json.loads(PHYSICAL_CONTRACT.read_text())
    check(sha(OFFLINE_RUNNER) == 'd96ca60e6a97ab6fba06e0956424eca2ac6ea8e162c8b567956b1b5308c6abea'
          and sha(OFFLINE_REPORT) == 'bb3a7813be188705492ff5d265a27ede1d741b2cedd4df673b429b4002d79aa5',
          'Sealed offline287 runner/report changed')
    previous = json.loads(OFFLINE_REPORT.read_text())
    check(previous['status'] == 'PASS' and previous['passed_cases'] == 287
          and [(c['mode'], c['case']) for c in previous['cases']]
          == [('virtual', c) for c in CASES] + [('real_clock', c) for c in REAL_CLOCK_CASES],
          'Offline287 fixture sequence changed')
    check(contract['physical_entry_point'] is True and contract['provider_loader'] is True
          and contract['physical_authorization'] is False and contract['maximum_physical_invocations'] == 1,
          'Physical scope/authorization boundary changed')
    check(contract['session_id'] == 'RK03_FULL_UPLOAD_NO_START_01'
          and Path(contract['session_path']) == PROBE.parent/'physical_session/RK03_FULL_UPLOAD_NO_START_01'
          and contract['requires_exact_human_authorization'] == 'PROCEED RK03 FULL UPLOAD NO START',
          'Fixed physical session/token differs')
    old = json.loads(FULL_UPLOAD_CONTRACT.read_text())
    for key in ('automatic_retry_allowed', 'maximum_tx', 'download_declarations', 'transfers', 'connect',
                'set_config_order', 'waits_ms', 'baud_set', 'queue_clears_in_order', 'upload_start_inclusive',
                'upload_end_exclusive', 'upload_bytes', 'payload_lengths', 'kernel_sha256', 'cipher_sha256',
                'excluded_historical_frame_index', 'excluded_historical_frame_hex', 'ordered_requests'):
        check(contract[key] == old[key], 'Physical protocol differs from sealed offline contract: ' + key)
    check(contract['simplified_physical_gates'] == ['IGNITION OFF', 'TEST MODE ON']
          and contract['recovery_gates'] == ['IGNITION OFF', 'NORMAL MODE ON'], 'Gate/recovery contract changed')
    check(set(contract['forbidden']) >= {'kernel start', 'kernel execution', 'kernel version', 'ROM read',
          'flash operation', 'arbitrary address', 'arbitrary payload', 'sixteenth36', 'retry'}, 'Scope exclusion missing')
    check(contract['physical_provider']['sha256'] == 'f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf'
          and Path(contract['physical_provider']['path']) == Path(r'C:\Windows\SysWOW64\op20pt32.dll'),
          'Provider hash/path changed')
    verify_pin_entries([contract[k] for k in ('physical_provider', 'offline_qualification', 'offline_manifest', 'fixed_upload_manifest')])
    verify_pin_entries(contract['reused_evidence'])
    return contract


def preflight(args):
    verify_first_chunk_contract()
    verify_full_upload_contract()
    verify_physical_contract()
    builds = [json.loads(path.read_text(encoding='utf-8-sig')) for path in (args.build_a, args.build_b)]
    executable_paths = [Path(b['exe_path']).resolve() for b in builds]
    binary = executable_paths[0]
    check(all(PROBE.resolve() in p.parents for p in executable_paths), 'Build executable outside isolated probe')
    hashes = [sha(p) for p in executable_paths]
    check(hashes[0] == hashes[1] == builds[0]['exe_sha256'] == builds[1]['exe_sha256'], 'Clean builds do not reproduce exact PE bytes')
    check(executable_paths[0] != executable_paths[1], 'Clean builds must use independent output paths')
    for build in builds:
        check(build['status'] == 'PASS_BUILD_ONLY', 'Build did not pass')
        verify_pin_entries(build['source_inputs'])
        verify_pin_entries([build[k] for k in ('compiler', 'linker', 'build_log', 'imports', 'headers')])
    check(builds[0]['source_inputs'] == builds[1]['source_inputs'], 'Clean builds used different source inputs')
    source_paths = {str(Path(x['path']).resolve()) for x in builds[0]['source_inputs']}
    check(all(str(p.resolve()) in source_paths for p in (PROBE/'src').iterdir() if p.is_file()), 'Build source closure missing a probe source file')
    blob = binary.read_bytes()
    check(blob[:2] == b'MZ', 'Not a PE executable')
    pe = struct.unpack_from('<I', blob, 0x3c)[0]
    check(blob[pe:pe+4] == b'PE\0\0' and struct.unpack_from('<H', blob, pe+4)[0] == 0x14c, 'Not x86 PE')
    pins_obj = json.loads(args.input_pins.read_text(encoding='utf-8-sig'))
    pins = pins_obj if isinstance(pins_obj, list) else pins_obj['inputs']
    verify_pin_entries(pins)
    contract = json.loads(CONTRACT.read_text())
    check(contract['wire_whitelist_in_order'] == TX[:3] and contract['set_config_order'] == CONFIG, 'Independent initial contract differs from oracle')
    check(contract['expected_81_response'] == RX[1] and contract['expected_83_response'] == RX[2], 'Response oracle differs from sealed contract')
    old = [json.loads(line) for line in RK02_LOG.read_text().splitlines()]
    check(BF in [r.get('wire_hex') for r in old] and RX[1] in [r.get('wire_hex') for r in old], 'BF/C1 not bound to physical RK02 evidence')
    check(old[-2]['status'] == 16 and old[-2]['count'] == 0, 'Recorded83 failure oracle changed')
    oracle = json.loads(ORACLE.read_text())
    check(oracle['tx'] == TX and oracle['rx'] == RX and oracle['config'] == CONFIG, 'Independent continuation oracle differs')
    check(oracle['virtual_waits_ms'] == [200, 100, 200] and oracle['kernel_sha256'] == KERNEL_SHA
          and oracle['kernel_size'] == 1808, 'Continuation timing/kernel contract differs')
    check(sha(KERNEL) == KERNEL_SHA and KERNEL.stat().st_size == 1808, 'Owned kernel changed')
    for wire in TX + RX:
        raw = bytes.fromhex(wire)
        check(len(raw) == raw[3] + 5 and raw[-1] == sum(raw[:-1]) & 255, 'Independent wire framing/checksum invalid')
    check(len(bytes.fromhex(TX[7])) == 137 and bytes.fromhex(TX[7])[4:8] == bytes.fromhex('36ff3000'),
          'First chunk address/128-byte payload boundary changed')
    kwp = json.loads(KWP.read_text())['transactions']
    for index in range(1, 6):
        check(any(r.get('request') == TX[index] and r.get('executed_TDR_reply') == RX[index] for r in kwp),
              'Reply not supported by retained actual stock execution')
    upload = json.loads(UPLOAD.read_text())['frames']
    check(sha(UPLOAD) == 'b1c5431141f9b249b16dd15938c290f20b99593e7ab8512caebcde1906c37f50', 'Stock upload wire contract changed')
    check(len(TX) == len(RX) == 22 and len(upload) == 17, 'Fixed complete-upload transmission count changed')
    for index in range(16):
        check(upload[index]['request'] == TX[index + 6] and upload[index]['reply_from_executed_TDR'] == RX[index + 6],
              'Declaration/upload chunk differs from retained actual stock execution')
    check(upload[16]['request'] == '8010f003310101b6' and upload[16]['request'] not in TX, 'Forbidden kernel start entered request table')
    offset = 0
    for index, wire in enumerate(TX[7:]):
        raw = bytes.fromhex(wire)
        length = 128 if index < 14 else 16
        check(raw[4] == 0x36 and int.from_bytes(raw[5:8], 'big') == 0xff3000 + offset
              and len(raw[8:-1]) == length and len(raw) == length + 9, 'Upload address/length ordering changed')
        check(RX[index + 7] == '80f0100176f7', 'Upload acknowledgement is not exact76')
        offset += length
    check(offset == 1808 and 0xffff3000 + offset == 0xffff3710, 'Full upload RAM coverage changed')
    seeds = json.loads(SEEDS.read_text())['seed_cases']
    check(len(seeds) == 16 and oracle['seed_vectors'] == seeds, 'Seed vectors differ from independent CPU producer evidence')
    check(sha(OEM_REPLAY) == '23f1526b7a831d2034ea849c039ea5f2ad3b1fa295c942c410b89fb9aebd6967',
          'Stock/current first-block replay changed')
    # Inspect only the new source closure. Inherited probe/history is not compiled.
    main_source = (PROBE/'src/main.cpp').read_text()
    core_source = (PROBE/'src/probe_core.hpp').read_text()
    runtime = '\n'.join((PROBE/'src'/name).read_text() for name in ('main.cpp', 'probe_core.hpp', 'common.hpp', 'protocol.hpp', 'fake_backend.hpp'))
    check('stage<22' in core_source and 'next_tx<22' in core_source
          and 'sizeof(KERNEL_CIPHER)==1808' in core_source, 'Fixed full-upload dispatch/embedding bounds changed')
    owned = (PROBE/'src/owned_artifact.h').read_text()
    match = re.search(r'KERNEL_CIPHER\[1808\]\s*=\s*\{([^}]+)\}', owned)
    check(match is not None, 'Embedded payload is not an exact1808-byte array')
    embedded = bytes(int(token, 16) for token in re.findall(r'0x([0-9a-fA-F]{2})', match.group(1)))
    check(embedded == b''.join(bytes.fromhex(wire)[8:-1] for wire in TX[7:]), 'Embedded fixed chunks differ from independent wire oracle')
    old_base = FIRST_CHUNK_RUNNER.parents[1]
    old_core = (old_base/'src/probe_core.hpp').read_text()
    new_common, old_common = (PROBE/'src/common.hpp').read_text(), (old_base/'src/common.hpp').read_text()
    check(new_common.split('struct Stream{', 1)[1] == old_common.split('struct Stream{', 1)[1], 'Reviewed parser changed')
    for begin, end in [(' void setup(){', ' Bytes exchange('), (' template<class F> long cleanup_call(', ' void wait(')]:
        check(core_source.split(begin, 1)[1].split(end, 1)[0].strip() == old_core.split(begin, 1)[1].split(end, 1)[0].strip(),
              'Reviewed setup/cleanup normalized source changed')
    check((PROBE/'src/protocol.hpp').read_text() == (old_base/'src/protocol.hpp').read_text(), 'Seed/framing helper changed')
    # Only the reviewed physical boundary and result labels may differ from sealed offline core.
    offline_base = OFFLINE_RUNNER.parents[1]
    expected_core = (offline_base/'src/probe_core.hpp').read_text()
    check(expected_core.count('require(!p,"Only static offline API allowed");') == 1,
          'Sealed offline constructor pattern changed')
    expected_core = expected_core.replace('require(!p,"Only static offline API allowed");',
                                         'require(!p||real,"Physical mode requires monotonic minimum waits");')
    check(expected_core.count('pass?"PASS_OFFLINE_FULL_KERNEL_UPLOAD_NO_START_ONLY":') == 2,
          'Sealed offline terminal pattern changed')
    expected_core = expected_core.replace('pass?"PASS_OFFLINE_FULL_KERNEL_UPLOAD_NO_START_ONLY":',
        'pass?(physical?"PASS_FULL_UPLOAD_NO_START_ONLY":"PASS_OFFLINE_FULL_KERNEL_UPLOAD_NO_START_ONLY"):')
    check(core_source == expected_core, 'Native core differs beyond three approved physical-boundary changes')
    for name in ('common.hpp', 'protocol.hpp', 'fake_backend.hpp', 'fixtures.hpp', 'owned_artifact.h',
                 'real_clock.hpp', 'physical_replay.hpp', 'first_physical_replay.hpp', 'j2534_tactrix.h'):
        check((PROBE/'src'/name).read_text() == (offline_base/'src'/name).read_text(),
              'Reviewed offline implementation changed: ' + name)
    for name in ('bootstrap.hpp', 'bootstrap_tests.hpp'):
        check((PROBE/'src'/name).read_text() == (FIRST_CHUNK_RUNNER.parents[1]/'src'/name).read_text(),
              'Reviewed first-chunk gate implementation changed: ' + name)
    pins_source = (PROBE/'src/pins.hpp').read_text()
    check('CONTRACT_SHA="' + PHYSICAL_CONTRACT_SHA + '"' in pins_source
          and 'PROVIDER_SHA="f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf"' in pins_source
          and 'SESSION_ID="RK03_FULL_UPLOAD_NO_START_01"' in pins_source
          and 'AUTH_TOKEN="PROCEED RK03 FULL UPLOAD NO START"' in pins_source,
          'Compiled fixed authorization bindings differ from reviewed contract')
    expected_pins = (FIRST_CHUNK_RUNNER.parents[1]/'src/pins.hpp').read_text()
    for before, after in [
        ('a7482b0eba224c9642745b830c71b3fff14f987988a58cdc1376e45dc0aa839c', PHYSICAL_CONTRACT_SHA),
        ('RK03_FIRST_CHUNK_01', 'RK03_FULL_UPLOAD_NO_START_01'),
        ('PROCEED RK03 FIRST CHUNK PROBE', 'PROCEED RK03 FULL UPLOAD NO START'),
        ('rk03_first_chunk_20260930_01', 'rk03_full_upload_physical_20260930_01'),
        ('FIRST_CHUNK_REVIEW_CONTRACT.json', 'PHYSICAL_FULL_UPLOAD_REVIEW_CONTRACT.json'),
        ('A2WC511R_RK03_FirstChunkPhysical', 'A2WC511R_RK03_FullUploadPhysical')]:
        expected_pins = expected_pins.replace(before, after)
    check(pins_source == expected_pins, 'Compiled path/token/provider bindings changed outside reviewed substitutions')
    check('Api api=fake::api()' in main_source and 'Probe probe(api,journal.value,false,real_fake)' in main_source,
          'Offline modes do not bind the actual shared core to the static fake API')
    check('resolve_api(resolver,real_clock::minimum_wait,real_clock::milliseconds)' in main_source
          and 'Probe probe(api,journal.value,true,true)' in main_source,
          'Physical mode does not use the tested core/real-clock helper')
    check('real_clock::minimum_wait(ms)' in main_source and 'api.wait_ms=real_fake_wait' in main_source,
          'Real-clock fake mode does not exercise physical minimum-wait helper')
    offline_prefix = main_source.split('const Bindings b=physical_bindings();', 1)[0]
    check(not re.search(r'\b(?:LoadLibrary\w*|GetProcAddress)\s*\(', offline_prefix),
          'Provider loader reachable in offline dispatcher prefix')
    boot_source = (PROBE/'src/bootstrap_tests.hpp').read_text()
    check('gate.prepare(b,supplied_session,supplied_auth)' in boot_source and 'gate.lock_provider(b)' in boot_source
          and '(void)resolve_api(resolver,nullptr,nullptr)' in boot_source, 'Bootstrap tests bypass shared physical gate/export code')
    check('OFFLINE_HARD_STOP_BEFORE_LOADER' in boot_source and 'OFFLINE_BOOTSTRAP_TEST_ONLY' in boot_source
          and not re.search(r'\b(?:LoadLibrary\w*|GetProcAddress|physical_bindings)\s*\(', boot_source),
          'Offline bootstrap lost its hard no-loader boundary')
    bootstrap_names = re.findall(r'"([a-z0-9_]+)"', boot_source.split('CASES[]={', 1)[1].split('};', 1)[0])
    check(set(bootstrap_names) == set(BOOTSTRAP_CASES) and len(bootstrap_names) == len(BOOTSTRAP_CASES),
          'Bootstrap fixture coverage differs from compiled table')
    source = (PROBE/'src/fake_backend.hpp').read_text()
    declaration = source.split('CASES[]={', 1)[1].split('};', 1)[0]
    fixture_names = re.findall(r'"([a-z0-9_]+)"', declaration)
    check(set(fixture_names) == set(CASES) and len(fixture_names) == len(CASES), 'Fixture coverage list differs from actual fake backend')
    return binary, pins, {'binary': reference(binary), 'physical_executable_tested_in_fake_modes': reference(binary),
                          'reproducible_executable_sha256': hashes[0],
                          'source_inputs': builds[0]['source_inputs'],
                          'build_artifacts': [{key: b[key] for key in ('compiler', 'linker', 'build_log', 'imports', 'headers')} for b in builds],
                          'clean_builds': [reference(args.build_a), reference(args.build_b)],
                          'clean_build_executables': [reference(p) for p in executable_paths],
                          'input_pins': reference(args.input_pins), 'contract': reference(CONTRACT),
                          'first_chunk_review_contract': reference(FIRST_CHUNK_CONTRACT),
                          'full_upload_no_start_contract': reference(FULL_UPLOAD_CONTRACT),
                          'physical_release_contract': reference(PHYSICAL_CONTRACT),
                          'previous287_runner': reference(OFFLINE_RUNNER), 'previous287_report': reference(OFFLINE_REPORT),
                          'successful_physical_first_chunk': reference(PHYSICAL_FIRST_CHUNK_LOG),
                          'previous156_runner': reference(FIRST_CHUNK_RUNNER), 'previous156_report': reference(FIRST_CHUNK_REPORT),
                          'successful_physical_transition': reference(SUCCESSFUL_PHYSICAL_LOG),
                          'previous127_runner': reference(PREVIOUS_RUNNER), 'previous127_report': reference(PREVIOUS_REPORT),
                          'continuation_oracle': reference(ORACLE), 'kwp_execution': reference(KWP),
                          'upload_execution': reference(UPLOAD), 'seed_execution': reference(SEEDS),
                          'stock_current_first_block_replay': reference(OEM_REPLAY), 'owned_kernel': reference(KERNEL),
                          'physical_failure_oracle': reference(RK02_LOG), 'runner': reference(Path(__file__))}


def main():
    raise SystemExit('INCOMPLETE_DRAFT_SCOPE_UNRESOLVED: no tests or executable invocation permitted')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-a', type=Path, default=PROBE/'build_a/BUILD.json')
    parser.add_argument('--build-b', type=Path, default=PROBE/'build_b/BUILD.json')
    parser.add_argument('--input-pins', type=Path, default=PROBE/'INPUT_PINS.json')
    args = parser.parse_args()
    run = PROBE/'reports'/('qualification_' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'status': 'FAIL', 'scope': 'SAME_PHYSICAL_CAPABLE_PE_FULL_UPLOAD_NO_START_OFFLINE_QUALIFICATION_ONLY',
              'runner_author': 'passive_review', 'independent_reviewers': ['root'],
              'physical_operations': 0, 'real_provider_loads': 0, 'cases': [],
              'limits': ['Synthetic API cases do not establish real provider timing, defaults or vehicle success.',
                         'Seed/key and fifteen fixed upload requests execute in the offline host against retained OEM replies.',
                         'OEM execution evidence separately uses explicit ready/TEND and programming-admission inputs.',
                         'Virtual waits verify schedule; real-clock fake cases measure host QPC minimum waits without a provider.',
                         'Baud SET status and output integrity are checked; no baud GET or physical effective baud is established.',
                         'The tested PE includes a gated physical dispatcher; this runner never selects it and grants no authorization.',
                         'This runner grants no physical authorization or vehicle-success claim; kernel start, ROM read and finalization remain excluded.',
                         'The sealed287 fixtures are reused unchanged;24 disposable bootstrap fixtures test shared gate code with a hard stop before loading.']}
    try:
        binary, pins, inputs = preflight(args)
        report['inputs'] = inputs
        report['physical_controls_before'] = physical_control_snapshot()
        check(not any(report['physical_controls_before'].values()), 'Offline worktree unexpectedly has a physical session')
        jobs = [('virtual', case, '--offline-fixture') for case in CASES]
        jobs += [('real_clock', case, '--offline-real-clock-fixture') for case in REAL_CLOCK_CASES]
        jobs += [('bootstrap', case, '--offline-bootstrap') for case in BOOTSTRAP_CASES]
        for mode, case, option in jobs:
            case_id = mode + '__' + case
            journal = run/(case_id + '.jsonl')
            command = [str(binary), option, case, '--journal', str(journal)]
            result = {'case': case, 'mode': mode, 'command': command,
                      'expected_tx_attempts': 0 if mode == 'bootstrap' else expected_tx_count(case), 'status': 'FAIL'}
            try:
                cp = subprocess.run(command, cwd=PROBE, capture_output=True, timeout=20)
                (run/(case_id+'.stdout.txt')).write_bytes(cp.stdout)
                (run/(case_id+'.stderr.txt')).write_bytes(cp.stderr)
                result.update(exit_code=cp.returncode, journal=reference(journal))
                rows = [json.loads(line) for line in journal.read_text(encoding='utf-8').splitlines()]
                stdout = cp.stdout.decode('utf-8', errors='replace')
                if mode == 'bootstrap':
                    result.update(inspect_bootstrap(case, rows, cp.returncode, stdout, journal))
                else:
                    result.update(inspect_case(case, rows, cp.returncode, stdout, real_clock=mode == 'real_clock'))
            except Exception:
                result['error'] = traceback.format_exc()
            report['cases'].append(result)
            save(run/'TEST_REPORT.json', report)
        verify_pin_entries(pins)
        verify_pin_entries(inputs['source_inputs'])
        verify_pin_entries([v for v in inputs.values() if isinstance(v, dict) and 'path' in v and 'sha256' in v])
        check(sha(args.input_pins) == inputs['input_pins']['sha256'], 'Input manifest changed during tests')
        check(sha(Path(__file__)) == inputs['runner']['sha256'], 'Runner changed during tests')
        check(sha(binary) == inputs['binary']['sha256'], 'Probe executable changed during tests')
        report['physical_controls_after'] = physical_control_snapshot()
        check(report['physical_controls_before'] == report['physical_controls_after'], 'Offline tests changed physical authorization/session controls')
        report['test_cases'] = len(report['cases'])
        report['passed_cases'] = sum(c['status'] == 'PASS' for c in report['cases'])
        report['status'] = 'PASS' if report['passed_cases'] == len(jobs) else 'FAIL'
        report['input_pins_unchanged'] = True
    except Exception:
        report['preflight_or_integrity_error'] = traceback.format_exc()
    report['artifacts'] = [reference(p) for p in sorted(run.rglob('*')) if p.is_file() and p.name != 'TEST_REPORT.json']
    save(run/'TEST_REPORT.json', report)
    summary = {'status': report['status'], 'report': reference(run/'TEST_REPORT.json')}
    save(PROBE/'reports/LATEST_QUALIFICATION.json', summary)
    print(json.dumps(summary, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
