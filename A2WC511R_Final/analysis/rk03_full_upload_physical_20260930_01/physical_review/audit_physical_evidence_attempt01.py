"""Read-only audit of completed, preserved evidence. Never invokes a native executable."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
A = Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_full_upload_physical_20260930_01')
P = Path(r'C:\Dev\A2WC511R_RK03_FullUploadPhysical\full_upload_physical')
S = P.parent/'physical_session/RK03_FULL_UPLOAD_NO_START_01'
OUT = A/'physical_review'
SID = 'RK03_FULL_UPLOAD_NO_START_01'


def pin(path):
    path = Path(path)
    blob = path.read_bytes()
    return {'path': str(path), 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(name, obj):
    with (OUT/name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    OUT.mkdir(exist_ok=True)
    expected_result = '41d0b333b1fd01c43ae6f11154e33e10a1740f8d9735694d3895bb0e47b4d1a0'
    result_path = A/'physical_result/PHYSICAL_RESULT.json'
    assert pin(result_path)['sha256'] == expected_result
    result = read(result_path)
    assert result['RK03_FULL_UPLOAD_NO_START_PHYSICAL'] == 'PASS'
    assert result['physical_invocations'] == 1 and result['session_id'] == SID
    sources = [pin(x) for x in sorted(S.iterdir()) if x.is_file()]
    assert sources == result['source_evidence'] and len(sources) == 9
    for item in sources:
        duplicate = A/'physical_result/evidence'/Path(item['path']).name
        assert pin(duplicate)['sha256'] == item['sha256']
    for item in read(A/'physical_result/MANIFEST.json')['files']:
        assert pin(item['path'])['sha256'] == item['sha256']

    execution = read(S/'EXECUTION.json')
    begin = read(S/'EXECUTION_BEGIN.json')
    assert result['execution'] == execution
    assert all(execution[k] == v for k, v in begin.items())
    assert execution['pid'] == 21608 and execution['exit_code'] == 0
    assert execution['process_exited'] is True and execution['bookkeeping_error'] is None
    assert execution['retry_allowed'] is False and execution['session_id'] == SID
    started = datetime.fromisoformat(execution['started_utc'])
    exited = datetime.fromisoformat(execution['exited_utc'])
    assert started < exited

    cert_path = A/'qualification/QUALIFICATION.json'
    contract_path = A/'PHYSICAL_FULL_UPLOAD_REVIEW_CONTRACT.json'
    cert, contract = read(cert_path), read(contract_path)
    assert pin(cert_path)['sha256'] == execution['qualification_sha256']
    assert cert['status'] == 'PASS_OFFLINE_QUALIFIED_PHYSICAL_FULL_UPLOAD_NO_START_ONLY'
    assert cert['session_id'] == SID and cert['maximum_physical_invocations'] == 1
    assert pin(cert['physical_executable']['path']) == cert['physical_executable']
    assert cert['physical_executable']['sha256'] == execution['executable_sha256']
    assert pin(contract_path) == cert['review_contract']
    assert cert['review_contract']['sha256'] == execution['contract_sha256']
    assert pin(contract['physical_provider']['path']) == contract['physical_provider']
    qualified_pins = 0
    for item in cert['files']:
        assert pin(item['path'])['sha256'] == item['sha256'], item['path']
        qualified_pins += 1
    assert execution['command_argv'] == [cert['physical_executable']['path'], '--physical-full-upload-no-start',
        '--session', str(S), '--authorization-file', str(S/'AUTHORIZATION.txt')]
    exe_sha, contract_sha = execution['executable_sha256'], execution['contract_sha256']
    token = 'PROCEED RK03 FULL UPLOAD NO START'
    expected_auth = f'{token}\nSESSION_ID={SID}\nEXE_SHA256={exe_sha}\nCONTRACT_SHA256={contract_sha}\n'.encode('ascii')
    expected_once = f'{SID}\n{exe_sha}\n{contract_sha}\n'.encode('ascii')
    assert (S/'AUTHORIZATION.txt').read_bytes() == expected_auth
    assert (S/'launch.reserved').read_bytes() == (S/'invocation.once').read_bytes() == expected_once
    gate_blob = (A/'FULL_UPLOAD_GATE_STATE.json').read_bytes()
    gates = json.loads(gate_blob)
    with (OUT/'GATE_STATE_READ_SNAPSHOT.json').open('xb') as f:
        f.write(gate_blob)
    assert gates['session_id'] == SID and gates['qualification_sha256'] == execution['qualification_sha256']
    gate_times = []
    for row, reply in zip(gates['completed_pre_probe_gates'], ['IGNITION OFF', 'TEST MODE ON']):
        assert row['reply'] == reply and row['source'] == 'user' and row['session_id'] == SID
        assert row['qualification_sha256'] == execution['qualification_sha256']
        gate_times.append(datetime.fromisoformat(row['received_utc']))
    assert len(gates['completed_pre_probe_gates']) == 2
    auth = gates['commit_authorization']
    assert auth['reply'] == token and auth['source'] == 'user' and auth['session_id'] == SID
    assert auth['qualification_sha256'] == execution['qualification_sha256']
    assert gate_times[0] < gate_times[1] < datetime.fromisoformat(auth['received_utc']) < started

    runner_path = P/'tools/test_full_physical_independent.py'
    assert pin(runner_path)['sha256'] == 'ccc470742171ff164c93341eed9d3647e4b34f6d768ef378c4ba3cf763c8411a'
    helpers = load('review_helpers_no_main', runner_path)
    protocol_path = Path(r'C:\Dev\A2WC511R_ReadKernel\host\protocol.py')
    stock_contract = read(Path(r'C:\Dev\A2WC511R_ReadKernel\evidence\contracts\UPLOAD_WIRE_CONTRACT_RK02.json'))
    protocol_pin = next(p for p in stock_contract['inputs'] if Path(p['path']) == protocol_path)
    assert pin(protocol_path)['sha256'] == protocol_pin['sha256']
    protocol = load('review_pure_byte_contract_no_devices', protocol_path)

    rows = [json.loads(line) for line in (S/'native_api.jsonl').read_text().splitlines()]
    start, terminal = rows[0], rows[-1]
    assert start['type'] == 'full_upload_start' and start['physical'] is True
    assert start['session_id'] == SID and start['exe_sha256'] == exe_sha and start['contract_sha256'] == contract_sha
    assert start['provider_path'] == contract['physical_provider']['path']
    assert start['provider_sha256'] == contract['physical_provider']['sha256']
    assert all(start[k] is True for k in ['authorization_verified', 'root_reservation_verified', 'native_invocation_reserved'])
    assert start['time_model'] == 'QPC_MONOTONIC_MINIMUM'
    assert start['embedded_cipher_bytes'] == start['declaration_size'] == 1808
    assert terminal['type'] == 'probe_terminal' and terminal['physical'] is True
    assert terminal['status'] == 'PASS_FULL_UPLOAD_NO_START_ONLY'
    assert terminal['protocol_complete'] and terminal['cleanup_confirmed']
    assert not terminal['cleanup_error_mask'] and not terminal['log_failed'] and not terminal['failure']
    assert terminal['state']['tx_attempts'] == 22
    assert not any(terminal['state'][k] for k in ['opened', 'connected', 'filtered'] if k in terminal['state'])
    assert terminal['state']['filter']['active'] is False
    intents, returns = rows[1:-1:2], rows[2:-1:2]
    assert len(rows) == 172 and len(intents) == len(returns) == 85
    prior_qpc, prior_utc = -1, -1
    epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    for sequence, (before, after) in enumerate(zip(intents, returns)):
        assert before['type'] == 'api_intent' and after['type'] == 'api_return'
        assert before['sequence'] == after['sequence'] == sequence
        assert before['physical'] is after['physical'] is True
        assert before['function'] == after['function'] and before['input'] == after['input']
        assert after['status'] == 0
        assert prior_qpc <= before['host_event_counter'] <= after['qpc_before'] <= after['qpc_after']
        assert prior_utc <= before['utc_filetime'] <= after['utc_filetime']
        assert after['qpc_frequency'] > 0 and after['api_elapsed_ticks'] == after['qpc_after'] - after['qpc_before']
        assert started <= epoch + timedelta(microseconds=before['utc_filetime']//10) <= exited
        assert started <= epoch + timedelta(microseconds=after['utc_filetime']//10) <= exited
        if 'esp_before' in after:
            assert after['esp_before'] == after['esp_after']
        for r in [before, after]:
            helpers.check_state(r['state'])
        for obj in [before['input'], after['output']]:
            if 'message' in obj:
                helpers.check_message(obj['message'])
            for key in ['mask', 'pattern', 'flow']:
                if key in obj:
                    helpers.check_zero_filter(obj[key])
        if 'canaries_intact' in after['output']:
            assert after['output']['canaries_intact'] is True
        prior_qpc, prior_utc = after['qpc_after'], after['utc_filetime']

    tx = [r for r in returns if r['function'] == 'PassThruWriteMsgs']
    rx = [r for r in returns if r['function'] == 'PassThruReadMsgs']
    assert len(tx) == 22 and len(rx) == 44
    responses, stages = [], []
    for stage, sent in enumerate(tx):
        raw = bytes.fromhex(sent['input']['message']['data_hex'])
        protocol.parse_ssm(raw)
        if stage != 4:
            assert raw.hex() == contract['ordered_requests'][stage]['wire_hex']
        assert sent['input']['message'] == sent['output']['message'] and sent['output']['count'] == 1
        assert sent['input']['timeout_ms'] == 1000
        msg = sent['input']['message']
        assert msg['protocol'] == 3 and msg['rx_status'] == msg['tx_flags'] == msg['timestamp'] == msg['extra_data_index'] == 0
        end_sequence = tx[stage+1]['sequence'] if stage < 21 else returns[-3]['sequence']
        received = [r for r in rx if sent['sequence'] < r['sequence'] < end_sequence]
        assert len(received) == 2
        som, data = [r['output']['message'] for r in received]
        assert som['rx_status'] == 2 and som['data_size'] == 0 and som['data_hex'] == ''
        assert data['rx_status'] == 0 and data['data_size'] == len(bytes.fromhex(data['data_hex']))
        for r in received:
            m = r['output']['message']
            assert r['output']['count'] == 1 and m['protocol'] == 3 and m['tx_flags'] == 0
            assert m['extra_data_index'] in (0, m['data_size'])
            assert r['input']['input_count'] == r['input']['message_capacity'] == 1 and r['input']['count_pointer_present'] is True
            assert 1 <= r['input']['timeout_ms'] <= 1000
        reply = bytes.fromhex(data['data_hex'])
        payload = protocol.parse_ssm(reply, response=True)
        if stage == 3:
            assert len(payload) == 6 and payload[:2] == b'\x67\x01'
        else:
            assert reply.hex() == contract['ordered_requests'][stage]['expected_reply_hex']
        responses.append(reply.hex())
        stages.append({'stage': stage, 'tx_sequence': sent['sequence'], 'request_hex': raw.hex(),
            'request_sha256': hashlib.sha256(raw).hexdigest(), 'rx_records': received,
            'reply_hex': reply.hex(), 'complete_reply_status': 0})
    seed = bytes.fromhex(responses[3])[6:10]
    key = protocol.seed_key(seed)
    assert tx[4]['input']['message']['data_hex'] == protocol.ssm(b'\x27\x02'+key).hex()
    chunks, ciphertext = [], bytearray()
    for index, row in enumerate(stages[7:]):
        frame = bytes.fromhex(row['request_hex'])
        assert frame == bytes.fromhex(stock_contract['frames'][index+1]['request'])
        cipher = frame[8:-1]
        size = 128 if index < 14 else 16
        assert len(cipher) == size and int.from_bytes(frame[5:8], 'big') == 0xff3000 + index*128
        assert frame[4] == 0x36 and row['reply_hex'] == '80f0100176f7'
        ciphertext.extend(cipher)
        chunks.append({'chunk': index+1, 'address': f'{0xffff3000+index*128:08X}', 'bytes': size,
            'wire_hex': frame.hex(), 'wire_sha256': row['request_sha256'],
            'cipher_sha256': hashlib.sha256(cipher).hexdigest(), 'ack_hex': row['reply_hex'],
            'tx_sequence': row['tx_sequence'], 'ack_sequence': row['rx_records'][-1]['sequence']})
    assert len(ciphertext) == 1808 and hashlib.sha256(ciphertext).hexdigest() == contract['cipher_sha256']
    kernel = Path(r'C:\Dev\A2WC511R_ReadKernel\build\rk02_01\kernel.bin').read_bytes()
    assert protocol.decrypt_upload(bytes(ciphertext)) == kernel
    assert hashlib.sha256(kernel).hexdigest() == contract['kernel_sha256']

    device = returns[0]['output']['device']
    channel = next(r['output']['channel'] for r in returns if r['function'] == 'PassThruConnect')
    filter_row = next(r for r in returns if r['function'] == 'PassThruStartMsgFilter')
    fid = filter_row['output']['filter_id']
    assert (device, channel, fid) == (1, 3, 0)
    def action(r):
        name, inp = r['function'], r['input']
        if name == 'PassThruWriteMsgs': return (name, inp['message']['data_hex'])
        if name == 'PassThruIoctl': return (name, inp['ioctl'], inp.get('config', {}).get('owned_buffer_entries'))
        if name == 'MonotonicMinimumWait': return (name, inp['requested_ms'], inp['reason'])
        return (name,)
    setup = [('PassThruOpen',), ('PassThruReadVersion',), ('PassThruConnect',)]
    setup += [('PassThruIoctl', 2, [x]) for x in helpers.CONFIG]
    setup += [('PassThruIoctl', 1, [{'parameter': x['parameter'], 'value': helpers.SENTINEL} for x in helpers.CONFIG]), ('PassThruStartMsgFilter',)]
    wanted = setup + [('PassThruWriteMsgs', r['request_hex']) for r in stages[:5]]
    wanted += [('MonotonicMinimumWait', 200, 'post_key_ack'), ('PassThruWriteMsgs', stages[5]['request_hex']),
        ('MonotonicMinimumWait', 100, 'post_session_ack'), ('PassThruIoctl', 2, [{'parameter': 1, 'value': 15625}]),
        ('PassThruIoctl', 7, None), ('PassThruIoctl', 8, None), ('MonotonicMinimumWait', 200, 'pre_download_declaration')]
    wanted += [('PassThruWriteMsgs', r['request_hex']) for r in stages[6:]]
    wanted += [(name,) for name in helpers.CLEANUP]
    assert [action(r) for r in returns if r['function'] != 'PassThruReadMsgs'] == wanted
    for r in returns:
        name, inp, output = r['function'], r['input'], r['output']
        if 'device' in inp: assert inp['device'] == device
        if 'channel' in inp: assert inp['channel'] == channel
        if name == 'PassThruOpen': assert inp == {'name_present': False, 'device_output_present': True}
        if name == 'PassThruConnect': assert inp == {'device': device, 'protocol': 3, 'flags': 512, 'baud': 4800, 'channel_output_present': True}
        if name == 'PassThruReadVersion':
            assert inp == {'device': device, 'firmware_capacity': 80, 'dll_capacity': 80, 'api_capacity': 80}
            for k in ['firmware', 'dll', 'api']:
                v = output[k]
                assert v['capacity'] == 80 and v['nul_terminated'] is True
                assert len(bytes.fromhex(v['raw_buffer_hex'])) == 80
                assert bytes.fromhex(v['raw_buffer_hex']).split(b'\0', 1)[0] == v['value'].encode('ascii')
        if name == 'PassThruWriteMsgs':
            assert inp['input_count'] == inp['message_capacity'] == 1 and inp['count_pointer_present'] is True
        if name == 'PassThruIoctl':
            assert inp['output_present'] is False
            if inp['ioctl'] in (1, 2):
                assert inp['input_present'] is True
                count = 5 if inp['ioctl'] == 1 else 1
                for config in [inp['config'], output['config']]:
                    helpers.check_config(config, count)
                    assert config['returned_num_params'] == count and config['pointer_matches_owned'] is True
                    assert config['config_pointer'] == config['owned_buffer_pointer'] and config['config_pointer'] != 0
                expected = helpers.CONFIG if inp['ioctl'] == 1 else inp['config']['owned_buffer_entries']
                assert output['config']['owned_buffer_entries'] == expected
            else:
                assert inp['input_present'] is False
    assert filter_row['input']['filter_type'] == 1
    assert all(filter_row['input'][k] is True for k in ['mask_present', 'pattern_present', 'flow_present', 'filter_output_present'])
    for k in ['mask', 'pattern', 'flow']:
        assert filter_row['input'][k] == filter_row['output'][k]
    waits = [r for r in returns if r['function'] == 'MonotonicMinimumWait']
    for r, ms in zip(waits, [200, 100, 200]):
        inp, output = r['input'], r['output']
        ticks, hz = r['api_elapsed_ticks'], r['qpc_frequency']
        minimum = (ms*hz+999)//1000
        assert inp['requested_ms'] == inp['milliseconds'] == output['requested_ms'] == ms
        assert inp['model'] == 'QPC_MONOTONIC_MINIMUM' and ticks >= minimum
        assert output['minimum_satisfied'] is True and output['minimum_qpc_ticks'] == minimum
        assert output['elapsed_qpc_ticks'] == ticks and output['qpc_frequency'] == hz
        assert output['overshoot_qpc_ticks'] == ticks - minimum
        assert output['monotonic_after_ms'] >= inp['monotonic_before_ms'] + ms
    assert [r['function'] for r in returns[-4:]] == ['PassThruReadMsgs', *helpers.CLEANUP]
    assert returns[-3]['input'] == {'channel': channel, 'filter_id': fid, 'filter_id_present': True}
    assert returns[-2]['input'] == {'channel': channel} and returns[-1]['input'] == {'device': device}
    for name in ['PRELAUNCH_CLIENT_CHECK.json', 'POSTEXIT_CLIENT_CHECK.json']:
        client = read(S/name)
        assert client['pass'] is True and client['real_provider_loaded_by_check'] is False
        assert not client['known_conflicting_clients'] and not client['provider_module_users'] and not client['module_inspection_failures']
    assert (S/'console.log').read_text().strip() == 'PASS_FULL_UPLOAD_NO_START_ONLY physical=true tx_attempts=22'
    assert all(pin(x['path']) == x for x in sources)

    report = {'schema': 1, 'status': 'PASS_INDEPENDENT_PHYSICAL_FULL_UPLOAD_NO_START_REVIEW',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'passive_review',
        'review_mode': 'Read-only completed evidence audit; no provider/client/native executable invocation',
        'physical_operations_by_reviewer': 0, 'recorded_physical_invocations': 1,
        'blocking_findings': [], 'session_id': SID, 'execution': execution,
        'auth_source': 'Root-recorded user gate receipts, exact session authorization and reservation bytes',
        'qualified_file_hashes_verified': qualified_pins, 'source_evidence': sources,
        'result': pin(result_path), 'qualification': pin(cert_path), 'contract': pin(contract_path),
        'review_source': pin(Path(__file__)), 'review_helpers': pin(runner_path), 'pure_byte_reference': pin(protocol_path),
        'gate_snapshot': pin(OUT/'GATE_STATE_READ_SNAPSHOT.json'), 'journal_records': len(rows),
        'journal_call_returns': 85, 'provider_API_calls': 82, 'host_wait_calls': 3,
        'all_call_statuses_zero': True, 'TX': 22, 'RX': 44,
        'start_of_message_records': 22, 'complete_response_records': 22,
        'BF_identity': '2F12515306', 'responses': responses, 'seed_hex': seed.hex(), 'key_hex': key.hex(),
        'fixed_declarations': 1, 'fixed_chunks': chunks, 'cipher_bytes': len(ciphertext),
        'cipher_sha256': hashlib.sha256(ciphertext).hexdigest(),
        'offline_decrypted_transmitted_bytes_sha256': hashlib.sha256(kernel).hexdigest(),
        'physical_RAM_readback_performed': False, 'wire_addresses_verified_big_endian': True,
        'upload_start_inclusive': 'FFFF3000', 'upload_end_exclusive': 'FFFF3710',
        'actual_handles': {'device': device, 'channel': channel, 'filter': fid},
        'serial_readback': next(r['output'] for r in returns if r['function']=='PassThruIoctl' and r['input']['ioctl']==1),
        'broad_filter': filter_row, 'waits': waits,
        'waits_ms_actual': [r['api_elapsed_ticks']*1000/r['qpc_frequency'] for r in waits],
        'baud_SET_status_zero': True, 'baud_effective_readback_performed': False,
        'queue_clear_order': [7, 8], 'cleanup': returns[-3:], 'provider_version': returns[1]['output'],
        'all_QPC_UTC_ordering_valid': True, 'process_elapsed_seconds': (exited-started).total_seconds(),
        'kernel_start_requests': 0, 'custom_kernel_version_requests': 0, 'ROM_read_requests': 0, 'flash_operations': 0,
        'recovery_evaluated': False,
        'limits': ['PASS is scoped to accepted fixed upload followed by clean transport exit; it does not assert physical RAM readback.',
            'Plaintext equality is derived offline from the transmitted ciphertext with the pinned reference transform, not by reading ECU RAM.',
            'No kernel start, custom-kernel execution, ROM acquisition or flash operation occurred in the recorded request sequence.',
            'This audit does not establish OEM-return recovery; that later passive result must be reviewed separately.',
            'QPC measurements establish host waits and call timing, not electrical K-line waveform timing.']}
    save('PHYSICAL_REVIEW.json', report)
    with (OUT/'PHYSICAL_REVIEW.md').open('x', encoding='utf-8', newline='\n') as f:
        f.write('# Independent physical full-upload review\n\n')
        f.write('PASS: one authorized session, 22 transmissions, one declaration and fifteen fixed transfers with fifteen exact `76` acknowledgements. All 85 logged calls (82 provider API calls and three host waits) returned zero. Cleanup ended with StopMsgFilter, Disconnect and Close; the child exited0 and the post-exit client scan passed.\n\n')
        f.write(f'The actual seed was `{seed.hex()}` and the independently recomputed key was `{key.hex()}`. All fifteen frame bytes, checksums, addresses and payload order match the pinned upload contract: fourteen128-byte chunks plus one16-byte chunk. Offline decryption of the transmitted ciphertext matches the pinned1,808-byte kernel. No physical RAM readback is claimed.\n\n')
        f.write('The five SET_CONFIG calls and immediate GET_CONFIG, broad four-zero filter, requested200/100/200ms waits, accepted15625baud SET and TX-then-RX queue clears match the qualified sequence. Actual measured waits were '+', '.join(f'{v:.4f}ms' for v in report['waits_ms_actual'])+'. All API arguments, raw provider records, timing order, output guards and cleanup records were checked.\n\n')
        f.write('Authorization, session, certificate, executable, provider and source/copy hashes agree. No later kernel-start/version request, ROM request, flash request or retry appears. This read-only review invoked no provider or executable. OEM-return recovery is outside this report.\n\nExact frame and evidence hashes are in PHYSICAL_REVIEW.json.\n')
    save('MANIFEST.json', {'status': report['status'], 'files': [pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]})
    print(json.dumps({'status': report['status'], 'report': pin(OUT/'PHYSICAL_REVIEW.json'), 'qualified_pins': qualified_pins}))


if __name__ == '__main__':
    main()
