"""Read-only source/build/journal audit. No native process or provider is invoked."""
import datetime
import hashlib
import json
import pathlib
import re

R = pathlib.Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\first_chunk')
O = pathlib.Path(__file__).parent
P = R / 'reports/qualification_20260930T033815962561Z/TEST_REPORT.json'
EXPECTED_PE = '3a6abe4e11fc6a85682c33018e67b533897860a932962f2840976fbd35ed1c02'
EXPECTED_REPORT = 'efb46f51d94ff624587b88228492535a8f441a0a9bcd1473d7f96329dde36e7b'
checks, errors, verified, cases = [], [], {}, []

def read(p):
    return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))

def pin(p):
    p = pathlib.Path(p)
    b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())

def check(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))
    if not condition:
        errors.append(name)

def walk(node):
    if isinstance(node, dict):
        if isinstance(node.get('path'), str) and isinstance(node.get('sha256'), str) and len(node['sha256']) == 64:
            actual = pin(node['path'])
            check('hash:' + node['path'], actual['sha256'] == node['sha256'])
            if 'bytes' in node:
                check('length:' + node['path'], actual['bytes'] == node['bytes'])
            verified[node['path']] = actual
        for value in node.values():
            walk(value)
    elif isinstance(node, list):
        for value in node:
            walk(value)

report, inputs = read(P), read(R / 'INPUT_PINS.json')
fixture = inputs['fixture']
walk(report)
walk(inputs)
for name in ['build_a/BUILD.json', 'build_b/BUILD.json', 'build_a/BUILD_INPUTS.json', 'build_b/BUILD_INPUTS.json']:
    walk(read(R / name))
check('report_hash', pin(P)['sha256'] == EXPECTED_REPORT)
check('report156', report['status'] == 'PASS' and report['test_cases'] == report['passed_cases'] == len(report['cases']) == 156)
check('no_physical_test', report['physical_operations'] == report['real_provider_loads'] == 0)
check('physical_controls_unchanged', report['physical_controls_before'] == report['physical_controls_after'] and all(v is None for v in report['physical_controls_after'].values()))
exe = R / 'build_a/rk03_first_chunk_probe32.exe'
blob = exe.read_bytes()
check('same_clean_PE', pin(exe)['sha256'] == EXPECTED_PE and blob == (R / 'build_b/rk03_first_chunk_probe32.exe').read_bytes())
check('x86_PE', blob[:2] == b'MZ' and int.from_bytes(blob[int.from_bytes(blob[60:64], 'little') + 4:][:2], 'little') == 0x14c)
source = {p.name: p.read_text() for p in (R / 'src').iterdir() if p.is_file()}
prior = pathlib.Path(r'C:\Dev\A2WC511R_RK03_PostTransitionOffline\continuation\src')
for name in ['common.hpp', 'protocol.hpp', 'fixtures.hpp', 'j2534_tactrix.h']:
    check('unchanged:' + name, (R / 'src' / name).read_bytes() == (prior / name).read_bytes())
old_core = (prior / 'probe_core.hpp').read_text()
for start, end in [(' void setup(){', ' Bytes exchange('), (' template<class F> long cleanup_call(', ' void wait('), (' Bytes exchange(', ' template<class F> long cleanup_call(')]:
    check('normalized_unchanged:' + start, source['probe_core.hpp'].split(start, 1)[1].split(end, 1)[0].strip() == old_core.split(start, 1)[1].split(end, 1)[0].strip())
cipher = bytes(int(s, 16) for s in re.findall(r'0x([0-9a-fA-F]{2})', source['owned_artifact.h'].split('KERNEL_CIPHER[128]', 1)[1]))
check('only128_embedded_cipher', len(cipher) == 128 and cipher == bytes.fromhex(fixture['tx'][7])[8:-1])
old_cipher = bytes(int(s, 16) for s in re.findall(r'0x([0-9A-Fa-f]{2})', (prior / 'owned_artifact.h').read_text().split('KERNEL_CIPHER', 1)[1]))
kernel = pathlib.Path(r'C:\Dev\A2WC511R_ReadKernel\build\rk02_01\kernel.bin').read_bytes()
check('full_kernel_absent_from_PE', len(old_cipher) == 1808 and old_cipher not in blob and kernel not in blob)
check('one_physical_loader_site', source['main.cpp'].count('LoadLibraryExW(') == 1 and 'LoadLibrary' not in source['main.cpp'].split('const Bindings b=physical_bindings();', 1)[0])
check('offline_bootstrap_no_loader', not re.search(r'\b(?:LoadLibrary\w*|GetProcAddress|physical_bindings)\s*\(', source['bootstrap_tests.hpp']))
cleanup_names = ['PassThruStopMsgFilter', 'PassThruDisconnect', 'PassThruClose']
counts = dict(virtual=0, real_clock=0, bootstrap=0, api_intents=0, reads=0, writes=0, measured_waits=0)
physical_log = pathlib.Path(r'C:\Dev\A2WC511R_RK03_TransitionProbe\physical_session\RK03_TRANSITION_PROBE_01\native_api.jsonl')
actual_rx = [x['output']['message'] for x in map(json.loads, physical_log.read_text().splitlines()) if x.get('type') == 'api_return' and x['function'] == 'PassThruReadMsgs']
for case in report['cases']:
    mode, name = case['mode'], case['case']
    label = mode + ':' + name
    counts[mode] += 1
    check(label + ':offline_CLI', case['command'][1] == {'virtual': '--offline-fixture', 'real_clock': '--offline-real-clock-fixture', 'bootstrap': '--offline-bootstrap'}[mode])
    rows = [json.loads(x) for x in pathlib.Path(case['journal']['path']).read_text().splitlines()]
    check(label + ':physical_false', all(x.get('physical') is False for x in rows))
    if mode == 'bootstrap':
        check(label + ':bootstrap_hard_boundary', len(rows) == 1 and rows[0]['type'] == 'offline_bootstrap_result' and rows[0]['provider_load_attempts'] == rows[0]['api_calls'] == 0)
        check(label + ':bootstrap_result', rows[0]['status'] == 'PASS_OFFLINE_BOOTSTRAP_TEST' and case['exit_code'] == 0 and rows[0]['phase'] == case['phase'])
        cases.append(dict(mode=mode, case=name, phase=case['phase'], tx_attempts=0))
        continue
    intents = [x for x in rows if x['type'] == 'api_intent']
    returns = [x for x in rows if x['type'] == 'api_return']
    writes = [x for x in intents if x['function'] == 'PassThruWriteMsgs']
    tx = [x['input']['message']['data_hex'] for x in writes]
    expected = fixture['tx'].copy()
    if name.startswith('seed_vector_'):
        key = bytes.fromhex(fixture['seed_vectors'][int(name.split('_')[-1])]['timer_and_stored_expected_key'])
        partial = b'\x80\x10\xf0\x06\x27\x02' + key
        expected[4] = (partial + bytes([sum(partial) & 255])).hex()
    check(label + ':fixed_prefix', len(tx) <= 8 and tx == expected[:len(tx)])
    check(label + ':tx_count', len(tx) == case['tx_attempts'] == case['expected_tx_attempts'])
    check(label + ':api_count', len(intents) == case['api_intents'] and len(returns) == case['api_returns'])
    check(label + ':ABI_stack', all(x['esp_before'] == x['esp_after'] for x in returns if 'esp_before' in x))
    check(label + ':QPC_order', all(x['qpc_after'] >= x['qpc_before'] for x in returns))
    cleanup = [x['function'] for x in intents if x['function'] in cleanup_names]
    check(label + ':cleanup_order', cleanup == case['cleanup_functions'] == [n for n in cleanup_names if n in cleanup])
    nonzero = [x for x in returns if x['status'] != 0 and x['function'] not in cleanup_names]
    check(label + ':no_TX_after_error', all(not any(w['sequence'] > b['sequence'] for w in writes) for b in nonzero))
    check(label + ':retained_timeouts', all(x['input']['timeout_ms'] == 1000 for x in writes) and all(0 < x['input']['timeout_ms'] <= 1000 for x in intents if x['function'] == 'PassThruReadMsgs'))
    terminal = [x for x in rows if x['type'] == 'probe_terminal']
    check(label + ':one_terminal', len(terminal) == 1)
    if terminal:
        t = terminal[0]
        check(label + ':reported_terminal', t['protocol_complete'] == case['protocol_complete'] and t['cleanup_error_mask'] == case['cleanup_error_mask'] and (t['status'] == 'PASS_OFFLINE_FIRST_CHUNK_ACK_ONLY') == (case['exit_code'] == 0))
        if case['exit_code'] == 0:
            check(label + ':success_boundary', len(tx) == 8 and t['cleanup_confirmed'] and not t['state']['opened'] and not t['state']['connected'] and not t['state']['filter']['active'] and t['state']['clear_mask'] == 3 and t['state']['baud_set_accepted'])
    if mode == 'real_clock':
        waits = [x for x in returns if x['function'] == 'MonotonicMinimumWait']
        check(label + ':measured_wait_schedule', [x['input']['milliseconds'] for x in waits] == [200, 100, 200])
        for i, w in enumerate(waits):
            elapsed = w['qpc_after'] - w['qpc_before']
            minimum = (w['qpc_frequency'] * w['input']['milliseconds'] + 999) // 1000
            check(label + ':actual_minimum:' + str(i), elapsed >= minimum and w['output']['minimum_satisfied'] is True and w['output']['elapsed_qpc_ticks'] == elapsed)
            counts['measured_waits'] += 1
    if name == 'physical_transition_replay':
        replay_rx = [x['output']['message'] for x in returns if x['function'] == 'PassThruReadMsgs'][:6]
        check(label + ':exact_physical_RX_replay', replay_rx == actual_rx)
    counts['api_intents'] += len(intents)
    counts['reads'] += sum(x['function'] == 'PassThruReadMsgs' for x in intents)
    counts['writes'] += len(writes)
    cases.append(dict(mode=mode, case=name, tx_attempts=len(tx), exit_code=case['exit_code'], cleanup=cleanup))
check('case_partition', (counts['virtual'], counts['real_clock'], counts['bootstrap']) == (128, 4, 24))
print(json.dumps(dict(errors=errors, checks=len(checks), unique_hashed_files=len(verified), counts=counts)))
if errors:
    raise SystemExit(1)
manual = [
    'Physical CLI accepts fixed session/authorization only; physical_bindings has no external provider, address, payload, length or clock overrides.',
    'Shared Gate verifies locked executable, compiled contract hash, exact authorization text and root reservation; persists CREATE_NEW invocation.once before opening/loading the pinned provider.',
    'The only provider loader follows native reservation, journal creation and locked-provider SHA. Offline modes return before that branch. Offline bootstrap has dummy files and noninvoked dummy export pointers only.',
    'The 128-byte ciphertext array targets FFFF3000..FFFF307F. Declaration retains1808 bytes; one34 and one36 only. Full76 ACK is followed solely by StopFilter/Disconnect/Close.',
    'No further chunk, kernel-start, custom-kernel execution, ROM-read or flash code path exists in the reviewed compiled closure.',
    'Physical minimum_wait uses QPC, rounds minimum ticks upward and loops until satisfied. Physical logs distinguish real clock from virtual fixtures and include requested/elapsed/overshoot timing.',
    'Initial serial setup, five SET/GET values, broad filter, parser, exchange, seed transform, baud SET/queue sequence and cleanup retain reviewed behavior. All nonzero statuses are terminal.',
    'Bootstrap hash object lifetime, typed x86 stdcall export resolution, owned bounds, API call timing and cleanup ownership were reviewed. Provider lock remains held through module unload.',
    'Runner new bootstrap, physical transcript and real-clock evidence checks were inspected. All qualification commands select only offline modes; final same-PE evidence is pinned.',
]
limits = [
    'This is independent offline qualification review, not physical authorization; fresh operator gates and exact new token remain mandatory.',
    'Real-clock fake cases establish host minimum-wait behavior, not actual ECU/provider programming admission, electrical timing or physical baud.',
    'Baud15625 evidence is SET status and returned-object integrity only; no baud GET or electrical waveform is established.',
    'Independent OEM instruction replay used explicit admitted-loader, ready/TEND and watchdog inputs. Physical post83/first36 behavior remains untested at this review.',
    'A failed36 can have already changed RAM before checksum/ACK. Neither failure nor cleanup guarantees OEM return, and no retry is authorized.',
    'Current image is CURRENT_PHYSICAL_CAPTURE with edited calibration data; relevant executable instructions match verified stock, not the complete ROM.',
    'The qualified scope ends at first accepted128-byte RAM chunk; it cannot establish full upload/start/read/finalizer readiness.',
]
result = dict(schema=1, status='PASS_INDEPENDENT_OFFLINE_FIRST_CHUNK_NATIVE_REVIEW', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), reviewer='oem_transition', reviewer_native_executions=0, reviewer_provider_loads=0, physical_authorization=False, unresolved_findings=[], physical_executable=pin(exe), test_report=pin(P), contract=pin(O.parent / 'FIRST_CHUNK_REVIEW_CONTRACT.json'), audit_script=pin(__file__), source_closure=[pin(p) for p in sorted((R / 'src').iterdir()) if p.is_file()], build_scripts=[pin(R / 'tools' / n) for n in ['build_probe.py', 'build_probe.cmd', 'prepare_sources.py']], launcher_review=pin(O / 'LAUNCHER_REVIEW.json'), original_offline_review=pin(pathlib.Path(r'C:\Dev\A2WC511R_Final\analysis\current_rom_20260930_01\post83_continuation_review\NATIVE_REVIEW.json')), OEM_review=pin(pathlib.Path(r'C:\Dev\A2WC511R_Final\analysis\current_rom_20260930_01\post83_oem_review\OEM_POST83_REVIEW.json')), direct_inputs=len(inputs['inputs']), unique_hashed_files=len(verified), checks=checks, counts=counts, cases=cases, verified_files=list(verified.values()), manual_review=manual, limits=limits)
target = O / 'NATIVE_REVIEW.json'
assert not target.exists(), 'Do not replace an existing final review'
target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
md = O / 'NATIVE_REVIEW.md'
md.write_text('# Independent first-chunk native review\n\n' + result['status'] + '\n\nNo unresolved native source/build findings. Both clean x86 builds match SHA256 ' + EXPECTED_PE + '. The final same-PE offline report passed156 cases (128 virtual,4 real-clock fake,24 bootstrap) and has SHA256 ' + EXPECTED_REPORT + '.\n\nVerified ' + str(len(verified)) + ' unique file hashes, ' + str(counts['api_intents']) + ' API intents and all12 real minimum waits. The compiled payload contains only128 cipher bytes; the fixed protocol stops after one34 and one36 at FFFF3000, exact76 ACK and cleanup. The physical provider loader is reachable only through fixed authorization, contract, provider-hash and exclusive invocation controls. Both offline modes and bootstrap tests hard-return before the loader.\n\nThis reviewer performed read-only audits only: no native process or provider was invoked. Fresh operator gates and the exact new token are still required; this review grants no physical authorization. Baud SET acceptance does not establish physical effective baud. Post83 programming admission and the first physical chunk remain untested here. Full upload, kernel start, ROM read and flash are excluded.\n', encoding='utf8')
manifest = O / 'NATIVE_REVIEW_MANIFEST.json'
manifest.write_text(json.dumps(dict(schema=1, status=result['status'], files=[pin(__file__), pin(target), pin(md)], errors=[]), indent=2) + '\n', encoding='utf8')
print(json.dumps(dict(review=pin(target), markdown=pin(md), manifest=pin(manifest)), indent=2))
