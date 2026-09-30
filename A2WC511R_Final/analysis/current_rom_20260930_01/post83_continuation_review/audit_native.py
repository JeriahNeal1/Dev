"""Read retained files only. Does not execute native code or load a provider."""
import datetime
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(r'C:\Dev\A2WC511R_RK03_PostTransitionOffline\continuation')
OUT = pathlib.Path(__file__).parent
REPORT = ROOT / 'reports/qualification_20260930T023001684674Z/TEST_REPORT.json'
errors, checks, verified = [], [], {}

def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))

def pin(path):
    path = pathlib.Path(path)
    data = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))

def check(name, value):
    checks.append(dict(name=name, passed=bool(value)))
    if not value:
        errors.append(name)

def walk(node):
    if isinstance(node, dict):
        if isinstance(node.get('path'), str) and isinstance(node.get('sha256'), str) and len(node['sha256']) == 64:
            actual = pin(node['path'])
            check('hash:' + node['path'], actual['sha256'] == node['sha256'])
            if 'bytes' in node:
                check('bytes:' + node['path'], actual['bytes'] == node['bytes'])
            verified[node['path']] = actual
        for value in node.values():
            walk(value)
    elif isinstance(node, list):
        for value in node:
            walk(value)

report = read(REPORT)
inputs = read(ROOT / 'INPUT_PINS.json')
fixture = inputs['fixture']
walk(report)
walk(inputs)
for name in ['build_a/BUILD.json', 'build_b/BUILD.json', 'build_a/BUILD_INPUTS.json', 'build_b/BUILD_INPUTS.json', 'reports/REUSE_PROOF.json']:
    walk(read(ROOT / name))
check('report127', report['status'] == 'PASS' and report['test_cases'] == report['passed_cases'] == len(report['cases']) == 127)
check('report_hash', pin(REPORT)['sha256'] == '9de655416e0452a60f5a20916cfc02db08f515447eec4c4e83239b59fa6ee2b0')
check('no_physical_tests', report['physical_operations'] == report['real_provider_loads'] == 0)
check('identical_builds', (ROOT / 'build_a/rk03_first_chunk_offline32.exe').read_bytes() == (ROOT / 'build_b/rk03_first_chunk_offline32.exe').read_bytes())
header = ROOT / 'src/owned_artifact.h'
check('unchanged_owned_header', header.read_bytes() == pathlib.Path(r'C:\Dev\A2WC511R_RK03_TransitionDev\src\owned_artifact.h').read_bytes())
literal = re.search(r'KERNEL_CIPHER\[\]=\{([^}]+)\}', header.read_text()).group(1)
cipher = bytes(int(s, 16) for s in re.findall(r'0x([0-9A-Fa-f]{2})', literal))
check('first_cipher_chunk_OEM_oracle', len(cipher) == 1808 and cipher[:128] == bytes.fromhex(fixture['tx'][7])[8:-1])
cleanup_names = ['PassThruStopMsgFilter', 'PassThruDisconnect', 'PassThruClose']
case_results, totals = [], dict(api_intents=0, reads=0, writes=0)
for case in report['cases']:
    name = case['case']
    rows = [json.loads(line) for line in pathlib.Path(case['journal']['path']).read_text().splitlines()]
    intents = [x for x in rows if x['type'] == 'api_intent']
    returns = [x for x in rows if x['type'] == 'api_return']
    writes = [x for x in intents if x['function'] == 'PassThruWriteMsgs']
    expected = fixture['tx'].copy()
    if name.startswith('seed_vector_'):
        vector = fixture['seed_vectors'][int(name.split('_')[-1])]
        body = b'\x27\x02' + bytes.fromhex(vector['timer_and_stored_expected_key'])
        frame = b'\x80\x10\xf0' + bytes([len(body)]) + body
        expected[4] = (frame + bytes([sum(frame) & 255])).hex()
    tx = [x['input']['message']['data_hex'] for x in writes]
    check(name + ':fixed_prefix', tx == expected[:len(tx)] and len(tx) <= 8)
    check(name + ':tx_count', len(tx) == case['tx_attempts'] == case['expected_tx_attempts'])
    check(name + ':physical_false', all(x['physical'] is False for x in intents + returns))
    check(name + ':api_count', len(intents) == case['api_intents'] and len(returns) == case['api_returns'])
    check(name + ':stack_balance', all(x['esp_before'] == x['esp_after'] for x in returns if 'esp_before' in x))
    check(name + ':qpc_order', all(x['qpc_after'] >= x['qpc_before'] for x in returns))
    cleanup = [x['function'] for x in intents if x['function'] in cleanup_names]
    check(name + ':cleanup_order', cleanup == case['cleanup_functions'] == [f for f in cleanup_names if f in cleanup])
    bad = [x for x in returns if x['status'] != 0 and x['function'] not in cleanup_names]
    check(name + ':terminal_status_no_later_TX', all(not any(w['sequence'] > b['sequence'] for w in writes) for b in bad))
    check(name + ':write_timeout', all(x['input']['timeout_ms'] == 1000 for x in writes))
    check(name + ':read_timeout', all(0 < x['input']['timeout_ms'] <= 1000 for x in intents if x['function'] == 'PassThruReadMsgs'))
    terminal = [x for x in rows if x['type'] == 'probe_terminal']
    check(name + ':one_terminal', len(terminal) == 1)
    if terminal:
        t = terminal[0]
        check(name + ':reported_outcome', t['protocol_complete'] == case['protocol_complete'] and t['cleanup_error_mask'] == case['cleanup_error_mask'] and (t['status'] == 'PASS_OFFLINE_FIRST_CHUNK_ACK_ONLY') == (case['exit_code'] == 0))
        if case['exit_code'] == 0:
            check(name + ':success_cleanup', t['cleanup_confirmed'] and not t['state']['opened'] and not t['state']['connected'] and not t['state']['filter']['active'])
            check(name + ':success_scope', len(tx) == 8 and t['state']['virtual_ms'] == 500 and t['state']['clear_mask'] == 3 and t['state']['requested_baud'] == 15625 and t['state']['baud_set_accepted'])
    totals['api_intents'] += len(intents)
    totals['reads'] += sum(x['function'] == 'PassThruReadMsgs' for x in intents)
    totals['writes'] += len(writes)
    case_results.append(dict(case=name, tx_attempts=len(tx), exit_code=case['exit_code'], cleanup=cleanup))
check('sixteen_seed_vectors', len([c for c in report['cases'] if c['case'].startswith('seed_vector_')]) == 16)
sources = sorted(p for p in (ROOT / 'src').iterdir() if p.is_file())
application = '\n'.join(p.read_text() for p in sources if p.name != 'j2534_tactrix.h')
check('application_no_provider_loader', not any(s in application for s in ['LoadLibrary', 'GetProcAddress', 'op20pt32', '--physical', 'SetProgrammingVoltage', 'RegOpenKey']))
dlls = re.findall(r'^\s+([\w.-]+\.dll)\s*$', (ROOT / 'build_a/imports.txt').read_text(), re.M | re.I)
check('imports_kernel32_only', set(s.lower() for s in dlls) == {'kernel32.dll'})
print(json.dumps(dict(errors=errors, checks=len(checks), unique_hashes=len(verified), totals=totals)))
if errors:
    raise SystemExit(1)
manual = [
    ['src/main.cpp', 10, 'Exact fake-only CLI, statically linked backend, exclusive new journal and no application provider loader.'],
    ['src/common.hpp', 1, 'Reviewed x86 J2534 ABI, owned bounded buffers, raw message metadata and strict framing/echo/indicator parser preserved.'],
    ['src/probe_core.hpp', 10, 'Eight fixed stages, one declaration and first cipher128 only; no later chunk, kernel start, ROM read or flash path.'],
    ['src/probe_core.hpp', 35, 'Every nonzero status is terminal; no retry after terminal error.'],
    ['src/probe_core.hpp', 36, 'Reviewed Connect, five SET/GET configurations and broad four-zero mask/pattern/flow filter preserved.'],
    ['src/probe_core.hpp', 78, 'Ordered StopFilter, Disconnect and Close attempted after exceptions; cleanup errors cannot suppress later cleanup.'],
    ['src/probe_core.hpp', 88, '15625 SET status/output integrity followed by CLEAR_TX/CLEAR_RX. No baud GET claim.'],
    ['src/probe_core.hpp', 95, 'Exact BF/C1/C3, variable four-byte seed, full670234/5085/7484/76 ACKs, virtual200/100/200 waits and terminal cleanup.'],
    ['src/fake_backend.hpp', 1, 'Static fault fixtures require exact sequence, OEM-derived frames, virtual time and baud/queue order.'],
    ['tools/create_fixtures.py', 1, 'Primary replies and ciphertext derive from executed OEM contracts; old host fixture is a crosscheck. Sixteen inverse-seed vectors derive from actual stock producer execution.'],
    ['tools/build_probe.cmd', 1, 'Only main.cpp and local headers compiled, x86 /W4 /WX, matching reproducible builds.'],
]
limits = [
    'Fake-only qualification; no real provider, physical timing or vehicle programming admission established.',
    'Virtual200/100/200 waits and requested15625 plus queue clearing follow selected ECUFlash host scheduling; no minimum ECU delays or real effective baud established.',
    'Initial five configuration values are GET-verified in fixtures. Post-session baud is SET status/output integrity only.',
    'Separate exact-stock/current loader replay supports one declaration and first accepted chunk with explicit admitted-loader, ready/TEND and watchdog inputs; asynchronous physical admission is outside scope.',
    'No full upload, kernel start, ROM read, finalizer, reset, physical dispatcher or permission for a physical attempt.',
    'Current physical capture contains edited calibration data; reviewed relevant instruction regions match stock, but the complete image is not factory stock.',
    'Generic CRT loader imports are present; reviewed application source contains no provider loader. Provider/CRT internals are outside this review.',
]
result = dict(schema=1, status='PASS_INDEPENDENT_OFFLINE_NATIVE_CONTINUATION_REVIEW', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), reviewer='oem_transition', reviewer_native_executions=0, reviewer_provider_loads=0, physical_authorization=False, unresolved_findings=[], test_report=pin(REPORT), offline_executable=pin(ROOT / 'build_a/rk03_first_chunk_offline32.exe'), source_closure=[pin(p) for p in sources], audit_script=pin(__file__), reuse_proof=pin(ROOT / 'reports/REUSE_PROOF.json'), root_runner_review=pin(OUT.parent / 'offline_continuation_review/ROOT_REVIEW.json'), OEM_evidence=[pin(OUT.parent / 'post83_oem_review' / f) for f in ['OEM_POST83_REVIEW.json', 'FIRST_BLOCK_REPLAY.json', 'MANIFEST.json']], input_count=len(inputs['inputs']), unique_hashed_files=len(verified), case_count=127, totals=totals, manual_review=manual, checks=checks, case_audit=case_results, verified_files=list(verified.values()), limits=limits)
target = OUT / 'NATIVE_REVIEW.json'
assert not target.exists(), 'Review already exists; do not overwrite'
target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
summary = OUT / 'NATIVE_REVIEW.md'
summary.write_text('# Independent native continuation review\n\n' + result['status'] + '\n\nNo unresolved source/build findings. Reviewed existing 127-case results without running native code or loading a provider. Both clean x86 builds match SHA256 e16d47a1d7fda7058016cf0f392aca1b64d1a6077353185eda8d3bb33ed68c86. Test report SHA256: 9de655416e0452a60f5a20916cfc02db08f515447eec4c4e83239b59fa6ee2b0.\n\nThe application accepts only static offline fixtures. Its eight fixed requests stop after one download declaration and the first128-byte owned-kernel chunk. Sixteen seed vectors come from actual OEM producer execution. Strict ACKs, terminal handling and ordered cleanup passed the reviewed cases.\n\nVerified ' + str(len(verified)) + ' unique file hashes and ' + str(totals['api_intents']) + ' API intents across127 cases. Root separately reviewed the independent runner.\n\nThe200/100/200ms waits are virtual. Baud15625 uses SET status and returned-object integrity only; no baud GET or measured effective baud is claimed. Independent admitted-loader stock/current replay supports single34 and first36 ACK with its explicit simulation inputs retained.\n\nThis result covers offline behavior through the first acknowledged chunk only. It provides no physical authorization or qualification of a complete acquisition path.\n', encoding='utf8')
manifest = OUT / 'MANIFEST.json'
manifest.write_text(json.dumps(dict(schema=1, status=result['status'], files=[pin(__file__), pin(target), pin(summary)], checks=len(checks), errors=[]), indent=2) + '\n', encoding='utf8')
print(json.dumps(dict(review=pin(target), markdown=pin(summary), manifest=pin(manifest)), indent=2))
