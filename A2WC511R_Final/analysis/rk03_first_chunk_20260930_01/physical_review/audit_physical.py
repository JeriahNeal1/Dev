"""Audit retained physical evidence using file reads and byte arithmetic only."""
import ast
import datetime
import hashlib
import json
import pathlib

S = pathlib.Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\physical_session\RK03_FIRST_CHUNK_01')
A = pathlib.Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_first_chunk_20260930_01')
O = pathlib.Path(__file__).parent
checks, errors = [], []

def pin(p):
    p = pathlib.Path(p)
    b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())

def read(p):
    return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))

def check(name, value):
    checks.append(dict(name=name, passed=bool(value)))
    if not value:
        errors.append(name)

before = [pin(p) for p in sorted(S.iterdir()) if p.is_file()]
journal_pin = pin(S / 'native_api.jsonl')
execution = read(S / 'EXECUTION.json')
begin = read(S / 'EXECUTION_BEGIN.json')
contract = read(A / 'FIRST_CHUNK_REVIEW_CONTRACT.json')
certificate = read(A / 'qualification/QUALIFICATION.json')
certificate_pin = pin(A / 'qualification/QUALIFICATION.json')
rows = [json.loads(s) for s in (S / 'native_api.jsonl').read_text().splitlines()]
intents = [x for x in rows if x['type'] == 'api_intent']
returns = [x for x in rows if x['type'] == 'api_return']
start, terminal = rows[0], rows[-1]
check('journal_hash', journal_pin['sha256'] == 'd258d9eb5b0690e8dd1c79d29f217aa86e152d866e1aeb1e938bf98aa13896a3')
check('exact_record_counts', len(rows) == 88 and len(intents) == len(returns) == 43)
check('all_records_physical', all(x['physical'] is True for x in rows))
check('43_zero_status_returns', all(x['status'] == 0 for x in returns))
check('ordered_sequences', [x['sequence'] for x in intents] == [x['sequence'] for x in returns] == list(range(43)))
for i, (a, b) in enumerate(zip(intents, returns)):
    check('paired_call:' + str(i), a['function'] == b['function'] and a['input'] == b['input'])
    check('timing:' + str(i), a['host_event_counter'] <= b['qpc_before'] <= b['qpc_after'] and b['qpc_frequency'] == 10000000 and b['api_elapsed_ticks'] == b['qpc_after'] - b['qpc_before'])
    if 'esp_before' in b:
        check('stack:' + str(i), b['esp_before'] == b['esp_after'])
    if 'canaries_intact' in b['output']:
        check('buffers:' + str(i), b['output']['canaries_intact'] is True)
check('monotonic_calls', all(returns[i]['qpc_after'] <= returns[i+1]['qpc_before'] for i in range(42)))
exchange = ['PassThruWriteMsgs', 'PassThruReadMsgs', 'PassThruReadMsgs']
expected_calls = ['PassThruOpen', 'PassThruReadVersion', 'PassThruConnect'] + ['PassThruIoctl'] * 6 + ['PassThruStartMsgFilter'] + exchange * 5 + ['MonotonicMinimumWait'] + exchange + ['MonotonicMinimumWait'] + ['PassThruIoctl'] * 3 + ['MonotonicMinimumWait'] + exchange * 2 + ['PassThruStopMsgFilter', 'PassThruDisconnect', 'PassThruClose']
check('complete_call_order_no_extra', [x['function'] for x in returns] == expected_calls)
for key in ['physical_executable', 'reproducible_build_executable', 'review_contract', 'native_test_report']:
    p = certificate[key]
    check('qualification_pin:' + key, pin(p['path'])['sha256'] == p['sha256'])
check('qualified_session', certificate['status'] == 'PASS_OFFLINE_QUALIFIED_FIRST_CHUNK_ONLY' and certificate['session_id'] == execution['session_id'] == start['session_id'] == contract['session_id'] == 'RK03_FIRST_CHUNK_01')
check('bound_executable', start['exe_sha256'] == execution['executable_sha256'] == certificate['physical_executable']['sha256'] == '3a6abe4e11fc6a85682c33018e67b533897860a932962f2840976fbd35ed1c02')
check('bound_contract', start['contract_sha256'] == execution['contract_sha256'] == certificate['review_contract']['sha256'] == 'a7482b0eba224c9642745b830c71b3fff14f987988a58cdc1376e45dc0aa839c')
check('bound_certificate', execution['qualification_sha256'] == certificate_pin['sha256'] == '51f42896bc04e63b62fdcbb57b490ef8212af69f906e71e5e51c577ce12a6af4')
check('fixed_provider_pin', start['provider_sha256'] == pin(start['provider_path'])['sha256'] == 'f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf')
expected_authorization = 'PROCEED RK03 FIRST CHUNK PROBE\nSESSION_ID=RK03_FIRST_CHUNK_01\nEXE_SHA256=' + start['exe_sha256'] + '\nCONTRACT_SHA256=' + start['contract_sha256'] + '\n'
expected_marker = 'RK03_FIRST_CHUNK_01\n' + start['exe_sha256'] + '\n' + start['contract_sha256'] + '\n'
check('exact_authorization', (S / 'AUTHORIZATION.txt').read_bytes() == expected_authorization.encode('ascii'))
check('both_once_markers', (S / 'launch.reserved').read_bytes() == (S / 'invocation.once').read_bytes() == expected_marker.encode('ascii'))
check('native_gate_flags', all(start[k] is True for k in ['authorization_verified', 'root_reservation_verified', 'native_invocation_reserved']))
check('execution_exit', execution['exit_code'] == 0 and execution['process_exited'] is True and execution['bookkeeping_error'] is None and execution['retry_allowed'] is False)
check('begin_provenance', all(execution[k] == value for k, value in begin.items()))
for name in ['PRELAUNCH_CLIENT_CHECK.json', 'POSTEXIT_CLIENT_CHECK.json']:
    client = read(S / name)
    check(name, client['pass'] is True and not client['known_conflicting_clients'] and not client['provider_module_users'] and not client['module_inspection_failures'] and client['real_provider_loaded_by_check'] is False)
check('connect', returns[2]['input']['protocol'] == 3 and returns[2]['input']['flags'] == 512 and returns[2]['input']['baud'] == 4800)
configuration = contract['set_config_order']
for i, value in enumerate(configuration):
    row = returns[3+i]
    check('initial_SET:' + str(i), row['input']['ioctl'] == 2 and row['input']['config']['owned_buffer_entries'] == row['output']['config']['owned_buffer_entries'] == [value] and row['output']['config']['pointer_matches_owned'] and row['output']['config']['returned_num_params'] == 1)
get = returns[8]
check('GET_effective_five', get['input']['ioctl'] == 1 and get['input']['input_present'] and not get['input']['output_present'] and get['output']['config']['owned_buffer_entries'] == configuration and get['output']['config']['pointer_matches_owned'] and get['output']['config']['returned_num_params'] == 5)
filter_row = returns[9]
check('filter_nonnull_arguments', filter_row['input']['filter_type'] == 1 and all(filter_row['input'][k] is True for k in ['mask_present', 'pattern_present', 'flow_present', 'filter_output_present']))
for field in ['mask', 'pattern', 'flow']:
    m = filter_row['output'][field]
    check('broad_filter:' + field, m == filter_row['input'][field] and m['data_hex'] == '00000000' and m['data_size'] == 4 and m['protocol'] == 3 and m['rx_status'] == m['tx_flags'] == m['extra_data_index'] == 0)
check('filter_type', terminal['state']['filter']['type'] == 1 and terminal['state']['filter']['returned_objects_valid'] is True)
tx_rows = [r for r in returns if r['function'] == 'PassThruWriteMsgs']
rx_rows = [r for r in returns if r['function'] == 'PassThruReadMsgs']
tx = [r['input']['message']['data_hex'] for r in tx_rows]
rx = [r['output']['message']['data_hex'] for r in rx_rows if r['output']['message']['rx_status'] == 0]
check('eight_TX_sixteen_RX', len(tx) == 8 and len(rx_rows) == 16 and len(rx) == 8)
for i, r in enumerate(tx_rows):
    check('TX_metadata:' + str(i), r['input']['message'] == r['output']['message'] and r['output']['count'] == 1 and r['input']['timeout_ms'] == 1000)
for i, r in enumerate(rx_rows):
    m = r['output']['message']
    check('RX_metadata:' + str(i), r['output']['count'] == 1 and m['protocol'] == 3 and m['tx_flags'] == 0 and m['data_size'] == len(bytes.fromhex(m['data_hex'])) == m['logged_bytes'] and not m['data_truncated'] and 0 < r['input']['timeout_ms'] <= 1000 and m['rx_status'] == (2 if i % 2 == 0 else 0) and m['extra_data_index'] == m['data_size'])
for i, wire in enumerate(tx + rx):
    data = bytes.fromhex(wire)
    check('frame:' + str(i), len(data) == data[3] + 5 and (sum(data[:-1]) & 255) == data[-1] and data[:3] == (b'\x80\x10\xf0' if i < 8 else b'\x80\xf0\x10'))
check('BF_identity', bytes.fromhex(rx[0])[8:13].hex() == '2f12515306')
seed = bytes.fromhex(rx[3])[6:-1]
key = bytes.fromhex(tx[4])[6:-1]
protocol_path = pathlib.Path(r'C:\Dev\A2WC511R_ReadKernel\host\protocol.py')
assignments = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(protocol_path.read_text()).body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ['TABLE', 'SEED_KEYS']}
left, right = int.from_bytes(seed[:2], 'big'), int.from_bytes(seed[2:], 'big')
for round_key in assignments['SEED_KEYS']:
    expanded = (right ^ round_key) * 0x10001
    value = sum(assignments['TABLE'][(expanded >> shift) & 31] << shift for shift in (0, 4, 8, 12))
    left, right = right, left ^ (((value >> 3) | (value << 13)) & 65535)
calculated_key = right.to_bytes(2, 'big') + left.to_bytes(2, 'big')
check('actual_seed_key', seed.hex() == 'a917a34f' and key.hex() == '4015f497' and calculated_key == key)
for i, item in enumerate(contract['ordered_requests']):
    if i != 4:
        check('fixed_request:' + str(i), tx[i] == item['wire_hex'])
expected_rx = [None, '80f01003c1ef8fc2', '80f01007c30000ff00ff0048', '80f010066701a917a34fa0', '80f0100367023420', '80f01002508557', '80f0100274847a', '80f0100176f7']
for i in range(1, 8):
    check('strict_ACK:' + str(i), rx[i] == expected_rx[i])
check('single_fixed_chunk', tx[7] == contract['fixed_transfer']['frame_hex'] and len(bytes.fromhex(tx[7])[8:-1]) == 128 and bytes.fromhex(tx[7])[4:8].hex() == '36ff3000')
waits = [r for r in returns if r['function'] == 'MonotonicMinimumWait']
wait_evidence = []
for i, (row, ms) in enumerate(zip(waits, [200, 100, 200])):
    ticks = row['qpc_after'] - row['qpc_before']
    minimum = (row['qpc_frequency'] * ms + 999) // 1000
    check('real_wait:' + str(i), row['input']['requested_ms'] == ms and ticks >= minimum and row['output']['elapsed_qpc_ticks'] == ticks and row['output']['minimum_satisfied'] and row['output']['overshoot_qpc_ticks'] == ticks - minimum)
    wait_evidence.append(dict(sequence=row['sequence'], reason=row['input']['reason'], requested_ms=ms, actual_ms=ticks*1000/row['qpc_frequency'], overshoot_ms=(ticks-minimum)*1000/row['qpc_frequency']))
check('three_waits', len(waits) == 3)
check('baud_SET', returns[30]['input']['ioctl'] == 2 and returns[30]['input']['config']['owned_buffer_entries'] == returns[30]['output']['config']['owned_buffer_entries'] == [{'parameter': 1, 'value': 15625}] and returns[30]['output']['config']['pointer_matches_owned'])
check('clear_TX_RX', [returns[i]['input']['ioctl'] for i in [31, 32]] == [7, 8] and all(not returns[i]['input']['input_present'] and not returns[i]['input']['output_present'] for i in [31, 32]))
check('no_baud_GET_claim', sum(r['function'] == 'PassThruIoctl' and r['input']['ioctl'] == 1 for r in returns) == 1)
check('terminal_cleanup', terminal['status'] == 'PASS_FIRST_CHUNK_PROBE_ONLY' and terminal['protocol_complete'] and terminal['cleanup_confirmed'] and terminal['cleanup_error_mask'] == 0 and not terminal['log_failed'] and terminal['failure'] == '' and not terminal['state']['opened'] and not terminal['state']['connected'] and not terminal['state']['filter']['active'] and terminal['state']['tx_attempts'] == 8)
check('only_cleanup_after76', [r['function'] for r in returns if r['sequence'] > rx_rows[-1]['sequence']] == ['PassThruStopMsgFilter', 'PassThruDisconnect', 'PassThruClose'])
old_path = pathlib.Path(r'C:\Dev\A2WC511R_RK03_TransitionProbe\physical_session\RK03_TRANSITION_PROBE_01\native_api.jsonl')
old = [r for r in map(json.loads, old_path.read_text().splitlines()) if r['type'] == 'api_return']
old_tx = [r['input']['message']['data_hex'] for r in old if r['function'] == 'PassThruWriteMsgs']
old_rx = [r['output']['message']['data_hex'] for r in old if r['function'] == 'PassThruReadMsgs' and r['output']['message']['rx_status'] == 0]
check('old_successful_BF81_83_bytes', old_tx == tx[:3] and old_rx == rx[:3])
check('same_provider_versions', next(r['output'] for r in old if r['function'] == 'PassThruReadVersion') == returns[1]['output'])
after = [pin(p['path']) for p in before]
check('raw_files_unchanged', before == after)
print(json.dumps(dict(errors=errors, checks=len(checks), waits=wait_evidence)))
if errors:
    raise SystemExit(1)
events = [dict(sequence=r['sequence'], function=r['function'], status=r['status'], input=r['input'], output=r['output'], qpc_before=r['qpc_before'], qpc_after=r['qpc_after'], qpc_frequency=r['qpc_frequency']) for r in returns]
limits = ['Eight full positive replies demonstrate this one first-chunk session through ACK76; no independent RAM readback was performed.', 'Only one128-byte RAM-transfer frame was sent. No second36, full upload, kernel-start, ROM-read or flash command was issued by this host.', 'The15625 setting is evidenced by successful SET_CONFIG and subsequent exchanges, not baud GET or an electrical waveform measurement.', 'QPC timings measure host API boundaries and waits; they are not exact on-wire bit/interbyte timing.', 'The new physical success does not uniquely identify the cause of the historical RK02 failure, because the qualified path contains multiple reviewed differences.', 'Cleanup and process exit do not establish OEM return; that requires the separately gated passive recovery result. No additional physical attempt is authorized by this report.', 'The current ROM remains CURRENT_PHYSICAL_CAPTURE with edited calibration data, not factory stock.']
result = dict(schema=1, status='PASS_INDEPENDENT_PHYSICAL_FIRST_CHUNK_AUDIT', reviewer='oem_transition', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), session_id='RK03_FIRST_CHUNK_01', reviewer_native_executions=0, reviewer_provider_loads=0, physical_invocations_recorded=1, additional_physical_authorization=False, unresolved_findings=[], qualification=certificate_pin, contract=pin(A / 'FIRST_CHUNK_REVIEW_CONTRACT.json'), physical_executable=pin(certificate['physical_executable']['path']), provider=pin(start['provider_path']), audit_script=pin(__file__), protocol_calculation_source=pin(protocol_path), raw_evidence_before=before, raw_evidence_after=after, native_journal=journal_pin, execution=execution, call_count=43, J2534_call_count=40, TX_count=8, RX_record_count=16, full_response_count=8, all_return_statuses_zero=True, ECU_BF_identity='2F12515306', actual_seed=seed.hex(), actual_key=key.hex(), calculated_key=calculated_key.hex(), request_frames=tx, response_frames=rx, initial_GET_values=configuration, actual_waits=wait_evidence, baud_status='SET15625_ACCEPTED_WITH_INTACT_OUTPUT_NO_BAUD_GET', first_chunk=dict(address='FFFF3000', end_exclusive='FFFF3080', cipher_bytes=128, wire_sha256=hashlib.sha256(bytes.fromhex(tx[7])).hexdigest(), ACK=rx[7], RAM_readback=False, kernel_start=False), cleanup_statuses=[dict(function=r['function'], status=r['status']) for r in returns[-3:]], comparison_to_prior_transition=dict(evidence=pin(old_path), same_BF81_83_TX_RX_bytes=True, same_provider_version_buffers=True, current_C1_read_exit_to_83_write_entry_ms=(returns[16]['qpc_before']-returns[15]['qpc_after'])/10000, current_83_write_exit_to_C3_read_exit_ms=(returns[18]['qpc_after']-returns[16]['qpc_after'])/10000), ordered_events=events, checks=checks, limits=limits)
target = O / 'PHYSICAL_REVIEW.json'
assert not target.exists(), 'Do not overwrite independent evidence'
target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
md = O / 'PHYSICAL_REVIEW.md'
md.write_text('# Independent physical first-chunk audit\n\nPASS_INDEPENDENT_PHYSICAL_FIRST_CHUNK_AUDIT. The one recorded invocation exited0 at2026-09-30T03:54:59.367746Z with PASS_FIRST_CHUNK_PROBE_ONLY. All40 J2534 calls and3 wait calls returned0. All9 raw session files remained byte-identical during this audit.\n\nThe exact qualified PE sent eight requests: BF,81,8300,2701,2702,108502, one34 and one36. ECU identity was2F12515306; seed a917a34f produced key4015f497 and the ECU returned full670234. Full5085,7484 and76 replies followed. The final reply was80f0100176f7. The only transfer carried the fixed128 cipher bytes toFFFF3000..FFFF307F. No second transfer, kernel-start, ROM-read or flash command followed.\n\nInitial five SET/GET values and the broad four-zero filter matched the contract. Measured minimum waits were203.774ms,102.1152ms and200.4695ms. Baud15625 SET succeeded, then CLEAR_TX and CLEAR_RX succeeded. This establishes accepted configuration and subsequent communication; it is not a baud GET or waveform measurement.\n\nAfter76, the only calls were StopMsgFilter, Disconnect and Close, all successful. The launcher recorded process exit and both client scans passed. This audit invoked no native program or provider.\n\nBF/81/83 request and response bytes match the earlier successful transition exactly. This success does not isolate the historical RK02 failure cause or qualify a full upload/read. ACK acceptance is not independent RAM readback. OEM return requires the separate human-gated passive recovery check.\n', encoding='utf8')
manifest = O / 'MANIFEST.json'
manifest.write_text(json.dumps(dict(schema=1, status=result['status'], files=[pin(__file__), pin(target), pin(md)], checks=len(checks), errors=[]), indent=2) + '\n', encoding='utf8')
print(json.dumps(dict(review=pin(target), markdown=pin(md), manifest=pin(manifest)), indent=2))
