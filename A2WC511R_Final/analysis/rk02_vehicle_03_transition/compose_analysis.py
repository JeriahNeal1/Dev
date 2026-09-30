"""Offline evidence synthesis; never imports a vehicle transport or edits source evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = Path(r'C:\Dev\A2WC511R_ReadKernel')
SESSION = PROJECT / 'acquisitions/RK02_VEHICLE_03'


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8-sig'))


def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def frame(value):
    if value is None:
        return None
    raw = bytes.fromhex(value)
    return {'wire_hex': value, 'total_bytes': len(raw), 'payload_bytes': raw[3],
            'length_valid': len(raw) == raw[3] + 5,
            'checksum_hex': f'{raw[-1]:02x}',
            'calculated_checksum_hex': f'{sum(raw[:-1]) & 255:02x}',
            'checksum_valid': raw[-1] == sum(raw[:-1]) & 255}


def main():
    native = read('native_transition_events.json')
    history = read('historical_evidence.json')
    archived = read('historical_offline_host_trace_prefix.json')
    api = {event['sequence']: event for event in archived['ordered_api_events']}
    live = {event['sequence']: event for event in native['events'] if 'sequence' in event}
    best = next(a for a in history['physical_historical_attempts'] if a['selected_best'])
    stock_reply = '80f01007c30000ff00ff0048'
    bf_reply = live[5]['wire_hex']
    stages = [('BF', 51, 52, 3, 5), ('81', 53, 54, 6, 8), ('83 00', 55, 56, 9, 10),
              ('27 01 seed', 57, 58, None, None), ('27 02 key', 60, 61, None, None),
              ('10 85 02 session', 62, 63, None, None),
              ('34 declaration first', 67, 68, None, None),
              ('34 declaration second', 69, 70, None, None),
              ('36 first RAM transfer', 71, 72, None, None)]
    comparison = []
    for stage, tx, rx, ltx, lrx in stages:
        q, r = api[tx], api[rx]
        historical_response = r['response'].get('messages', [])
        entry = {
            'stage': stage,
            'historical_successful_event': {
                'evidence_class': 'HISTORICAL_PHYSICAL_APPLICATION_LOG_ONLY',
                'request': None, 'response': None, 'J2534_calls': None,
                'source': best['source'], 'reason_null': 'Raw bytes and API details were not logged'},
            'installed_host_offline_event': {
                'evidence_class': 'ACTUAL_INSTALLED_HOST_CALLS_TO_FAKE_PROVIDER',
                'source': archived['source'], 'tx_sequence': tx, 'rx_sequence': rx,
                'request': frame(q['request']['messages'][0]['data_hex']),
                'response': frame(historical_response[0]['data_hex']) if historical_response else None,
                'tx_status': q['response']['status'], 'rx_status': r['response']['status'],
                'tx_timeout_ms': q['request']['timeout'], 'rx_timeout_ms': r['request']['timeout'],
                'response_provenance': 'SYNTHETIC_RESPONSE_NOT_HISTORICAL_PHYSICAL_BYTES'},
            'RK02_event': {
                'evidence_class': 'CURRENT_PHYSICAL_NATIVE_JOURNAL',
                'source': pin(SESSION / 'native_api.jsonl'),
                'tx_sequence': ltx, 'rx_sequence': lrx,
                'request': frame(live[ltx]['wire_hex']) if ltx is not None else None,
                'response': frame(live[lrx]['wire_hex']) if lrx is not None and live[lrx]['wire_hex'] else None,
                'tx_status': live[ltx]['status'] if ltx is not None else None,
                'rx_status': live[lrx]['status'] if lrx is not None else None,
                'message_count': live[lrx]['count'] if lrx is not None else None,
                'state': 'EXECUTED' if ltx is not None else 'NOT_REACHED'},
            'timing_delta': {'physical_success_vs_RK02_ms': None,
                             'reason': 'No historical physical API or bus timing exists'},
            'configuration_delta': 'See initial_configuration_delta; no config change between 81 and 83 in either host',
            'confidence': {'RK02_observation': 'HIGH', 'installed_host_fake_call_order': 'HIGH',
                           'historical_physical_raw_equivalence': 'UNAVAILABLE'}}
        comparison.append(entry)
    config = [
        {'parameter': 22, 'name': 'PARITY', 'installed_host': 0, 'RK02': None},
        {'parameter': 7, 'name': 'P1_MAX', 'installed_host': 1, 'RK02': None},
        {'parameter': 10, 'name': 'P3_MIN', 'installed_host': 0, 'RK02': None},
        {'parameter': 12, 'name': 'P4_MIN', 'installed_host': 0, 'RK02': None},
        {'parameter': 3, 'name': 'LOOPBACK', 'installed_host': 0, 'RK02': None},
    ]
    for item in config:
        item.update(RK02_null_reason='No SET_CONFIG or GET_CONFIG; actual provider default was not recorded',
                    confidence='HIGH_FOR_HOST_CALL_DIFFERENCE; UNKNOWN_FOR_ACTUAL_DEFAULT_VALUE')
    pins = {s['path']: s for s in history['sources']}
    for path in [SESSION / 'native_api.jsonl', SESSION / 'native.log',
                 SESSION / 'owned_physical_read32.exe',
                 PROJECT / 'host/physical_build/rk02_physical_01/native_physical.cpp',
                 PROJECT / 'host/vendor/j2534_tactrix.h',
                 PROJECT / 'host/TRANSPORT_CONTRACT.md',
                 Path(r'C:\Windows\SysWOW64\op20pt32.dll')]:
        pins[str(path)] = pin(path)
    for pattern in ['native_transition_events.json', 'installed_provider_definition_check.json',
                    'historical_*.json', 'oem_transition_*.json', 'oem_transition_*.md',
                    'ecuflash_static_*.json', 'ecuflash_static_*.md', 'ecuflash_static_*.asm']:
        for path in HERE.glob(pattern):
            pins[str(path)] = pin(path)
    result = {
        'schema': 1, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'OFFLINE_ROOT_CAUSE_ANALYSIS_NO_NEW_PHYSICAL_ATTEMPT',
        'physical_causal_root_status': 'NOT_UNIQUELY_DETERMINED',
        'last_common_event': {
            'strict_historical_physical_comparison': 'ECU identity 2F12515306; historical 81/83 raw bytes absent',
            'installed_host_and_stock_supported_comparison': '81 request accepted; C1 service-positive response',
            'RK02_full_response': '80f01003c1ef8fc2',
            'historical_full_response': None,
            'note': 'Full C1 EF 8F is physical RK02 and stock replay evidence, not a recorded historical ECUFlash response'},
        'first_divergence': {
            'configuration': 'Immediately after Connect: ECUFlash sets PARITY then timing/LOOPBACK; RK02 starts its filter without SET_CONFIG',
            'wire_outcome': '83 00 returns no message/status16 in RK02; archived fake host gets synthetic C3 and continues',
            'historical_physical_precise_divergence': None,
            'confidence': 'HIGH_FOR_SOURCE/API_DIFFERENCE; UNPROVEN_AS_PHYSICAL_SILENCE_CAUSE'},
        'timing_delta': native['timing'],
        'initial_configuration_delta': config,
        'comparison': comparison,
        'historical_physical_ordered_events': best['ordered_events_to_first_upload'],
        'installed_host_complete_API_prefix': pin(HERE / 'historical_offline_host_trace_prefix.json'),
        'RK02_complete_API_events': native['events'],
        'stock_8300_request': frame('8010f002830005'), 'stock_8300_reply': frame(stock_reply),
        'confirmed_implementation_defect': {
            'description': 'RK02 transport initialization does not reproduce the explicit serial configuration of the reviewed installed-host path; defaults are neither set nor recorded',
            'classification': 'TRANSPORT_REPRODUCIBILITY_AND_EVIDENCE_GAP',
            'physical_causation_proven': False,
            'offline_correction_scope': 'New development branch only: explicit configuration and full call-argument evidence; preserve frozen RK02'},
        'timeout_finding': {
            'status_decimal': 16, 'status_hex': '0x10', 'symbol': 'ERR_BUFFER_EMPTY',
            'ERR_TIMEOUT_is_different': '0x09', 'RK02_first_slice_ms': 1000,
            'ECUFlash_83_call_timeout_ms': 500,
            'both_hosts_treat_nonzero_read_status_as_failure': True,
            'increase_timeout_as_root_cause_fix_supported': False},
        'intentional_differences_requiring_review': [
            'RK02 full stock reply validation versus ECUFlash service-only positive predicate',
            'RK02 narrow response filter versus ECUFlash all-pass filter',
            'No programming-pin voltage API in RK02',
            'RK02 local deterministic seed-key transform versus vendor app-service call',
            'Owned RK02 0x710-byte kernel versus historical DUAL 0x1234-byte kernel',
            'Single download declaration/no retry versus two declarations in archived fake-host path',
            'RK02 omits installed-host post-key200ms, post-session100ms and pre-upload200ms delays; these later differences require separate resolution before physical qualification'],
        'qualification': 'NOT_QUALIFIED_FOR_ANOTHER_PHYSICAL_ATTEMPT',
        'evidence_paths_hashes': list(pins.values()),
        'physical_activity_in_analysis': False,
    }
    diff_path = HERE / 'RK02_VEHICLE_03_SESSION_TRANSITION_EVENT_DIFF.json'
    with diff_path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')

    rows = []
    for item in comparison:
        offline = item['installed_host_offline_event']
        rk = item['RK02_event']
        tx = offline['request']['wire_hex']
        if item['stage'] == '36 first RAM transfer':
            tx = '137-byte frame; complete bytes in event diff'
        rx = offline['response']['wire_hex'] if offline['response'] else 'none'
        actual = rk['response']['wire_hex'] if rk['response'] else ('status16, count0' if rk['state']=='EXECUTED' else 'not reached')
        rows.append(f"| {item['stage']} | `{tx}` | `{rx}` | `{actual}` |")
    evidence_rows = '\n'.join(f"| `{Path(s['path']).name}` | `{s['sha256']}` |" for s in [
        best['source'], pin(SESSION/'native_api.jsonl'), pin(SESSION/'owned_physical_read32.exe'),
        pin(PROJECT/'host/vendor/j2534_tactrix.h'), pin(Path(r'C:\Windows\SysWOW64\op20pt32.dll'))])
    markdown = f'''# RK02_VEHICLE_03 session-transition analysis

The exact host-side failure is known: after transmitting `80 10 F0 02 83 00 05`, the installed provider returned `ERR_BUFFER_EMPTY` (`16`, `0x10`) with zero messages; RK02's nonzero-status guard then terminated the invocation. The evidence does **not** uniquely establish why no physical reply reached the host.

The first verified implementation divergence occurs earlier, immediately after `PassThruConnect`: the installed ECUFlash path explicitly sets parity, receive/intermessage/interbyte timing and loopback. RK02 omits all initial `SET_CONFIG` calls and never records the inherited defaults. This is a concrete transport-reproducibility defect and a plausible contributor to the silence, not a proved single physical cause. A development correction must address that omission and reproduce the known API contract without claiming vehicle acceptance.

## Evidence boundary and preserved state

G13/ignition OFF and OEM return were confirmed by the user. No new physical check was performed. RK02 invocation count remains **1**. The complete failed acquisition directory is sealed by `FAILED_EVIDENCE_BEFORE.json`; analysis and recovery observations are outside it. No seed/key, kernel upload/start, ROM read or flash operation occurred. Both partial files are zero bytes. Finalizer exit1 correctly rejected the incomplete journal. The terminal journal contains no StopFilter/Disconnect/Close; process exit is not evidence of successful explicit provider cleanup or ECU reset.

There are three distinct comparators: historical physical **application logs**, archived actual installed-host calls to a **fake provider**, and **stock instruction execution**. Their provenance is preserved in the event diff. Neither synthetic replies nor stock replay bytes are substituted for unlogged historical physical data. The current vehicle ROM was previously edited and remains unacquired; stock instruction results do not prove its executable regions are identical.

## Best historical successful sessions

The best comparator is the August18 log, SHA256 `{best['source']['sha256']}`. It records ECU ID2F12515306 at line89, Requesting Seed90, Sending Key91, first FFFF3000/0080 RAM block93, DUAL1.07 response131, A2WC511R metadata1340–1341, and a1MiB raw save1355–1356. July26 independently records a successful read after an earlier key-stage failure; those attempts remain separate.

August's identity label is12:03:31.926; seed32.005; key32.051; upload-area32.682; first block32.698. The key-to-first-block label interval is647ms. These are application-log times, not wire/API times. No historical successful raw81/83 capture, provider call returns, configuration or bus timing was found in the scoped evidence. Consequently the last directly common historical physical observation is the ECU identity; historical full C1/C3 bytes remain unknown. See `historical_evidence.json` for exact source lines, July comparison and copy/hash provenance.

## Ordered transition through first upload

The following full byte values come from the archived installed-host **offline** API trace and the current RK02 physical journal. All historical physical raw request/response fields remain null in the machine-readable diff. The archived C1/C3/50/74 replies are minimal synthetic positives, not observed OEM responses. The table starts at the common BF operation; the JSON retains the entire API prefix, including initialization, through the first36 acknowledgement.

| Stage | Installed-host TX against fake provider | Fake reply | RK02 physical reply/outcome |
|---|---|---|---|
{chr(10).join(rows)}

The exact stock positive83 reply is `80f01007c30000ff00ff0048` (12 bytes). The83 request is7bytes, declares2payload bytes and has checksum05. C1 EF8F is8bytes, payload3, checksumC2. All captured nonempty RK02 frames have valid declared lengths and additive checksums. Complete137-byte first36 frames, their lengths/checksums, API status values and source line numbers are retained in the JSON; no upload bytes are omitted there.

## Requested fifteen-point comparison

| # | Topic | Result and confidence |
|---|---|---|
| 1 | Complete wire bytes | RK02 and installed-host offline TX match BF/81/8300 exactly. Full historical physical replies were not logged. High confidence in captured bytes; historical raw comparison unavailable. |
| 2 | Checksums/lengths | RK02 BF,81,C1 and8300 framing is valid. Verified stock accepts exact8300 and produces C30000FF00FF00. No framing defect found. |
| 3 | J2534 calls/status | RK02 Open/Connect/Filter/BF/81/83Write all return0. The next ReadMsgs returns16/count0. API arguments for Connect/filter are inferred from the hash-bound source because the native journal omits them. |
| 4 | Connect | Both host paths select protocol3/flags0x200/4800. Opaque IDs differ legitimately. ECUFlash subsequently configures the channel; RK02 does not. |
| 5 | Baud/protocol | ISO9141=3, ISO9141_NO_CHECKSUM=0x200,4800 baud through83 and security. Both plan15625 only after108502. No83 baud/protocol change is found in installed-host or verified stock code. |
| 6 | Filters | RK02 PASS_FILTER maskFFFFFF/pattern80F010; ECUFlash all-pass four-byte zero mask/pattern. Expected stockC3 has the accepted80F010 prefix. Strict filtering could conceal an unexpected frame, but no such physical frame was recorded. |
| 7 | Echo | ECUFlash explicitly LOOPBACK0; RK02 leaves default unknown and accepts bounded emptySOM/TXDONE/exactTX echoes. Real BF/81 have SOM but no echo. This failure is distinct from the corrected passive observer's SOM defect. |
| 8 | Read timeouts | ECUFlash uses BF400ms,812000ms,83500ms; RK02 uses one1000ms slice inside a2000ms upper frame bound. Both hosts fail on a nonzero API result. RK02 did not exhaust its upper bound, but increasing its wait is not supported as the root-cause correction. |
| 9 | 81→83 timing | RK02 API-return to API-return:77.0782ms;83 write-return to empty-read-return:1001.8799ms. Exact physical bus gap and successful historical gap are unknown. Offline host RPC times are not comparable electrical measurements. |
| 10 | IOCTL/config | ECUFlash explicitly PARITY22=0,P1_MAX7=1,P3_MIN10=0,P4_MIN12=0,LOOPBACK3=0, plus queue clears. RK02 omits initial configuration/clears and does not query defaults. This is the earliest verified implementation divergence. |
| 11 | Missing intermediate command | No opcode/IOCTL/delay occurs between81-positive and8300 in the selected installed caller. Later differences include vendor key app-service, explicit200ms after key,100ms after108502,200ms before upload, queue clears after baud change and two34 declarations before first36. RK02 omits those delays and sends one declaration. Those were never reached by RK02. |
| 12 | Programming/Test Mode | User confirmed active mode, CEL/fuel-pump cycling, engineOFF; intentionally disconnected fans do not negate that observation. Stock83 validation checks length/session/subfunction, with no Test Mode test in the bounded handler. No Test Mode failure is inferred. |
| 13 | ECUFlash after C1 EF8F | Static StartCommunication/generic positive predicate checks C1 service success; it does not branch on EF8F in the selected caller. It next invokes AccessTimingParameters subfunction0 with zero extra bytes, then seed only after success. |
| 14 | Actual83 request | Yes: installed-host static path and recorded fake API TX both show exactly8010f002830005. It is not an invented opcode. Historical physical application logs alone cannot independently show those bytes. |
| 15 | ECU state change at83 | Stock81 sets communication-session bit20. Stock83 returns fixed timing bytes; it does not change baud. The separate108502 transition, which RK02 never reached, changes programming state. Current edited-code equivalence is unknown. |

## Status16 and installed provider definition

The selected provider remains `C:\\Windows\\SysWOW64\\op20pt32.dll`, SHA256 `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`. Both installed OpenPort and ECUFlash SDK headers match the build header byte-for-byte: SHA256 `c559ea33654af59ad147eedfcccd56a1f2cb6e95daeb2412b53f6f4bbc76a7d9`. Their Error IDs define ERR_BUFFER_EMPTY=0x10 and ERR_TIMEOUT=0x09. Status16 is therefore an empty receive-queue result, not a negative ECU response, adapter disconnect code or a synonym for9. See `installed_provider_definition_check.json`.

The DLL resource version reads1.02.0.4868, while historical runtime ReadVersion logging reports1.02.4870/API04.04. Those are different evidence fields; no DLL was loaded to reconcile them during this analysis. The pinned binary hash identifies the selected file. Context7 was consulted but returned generic third-party J2534 guidance rather than this provider's exact behavior; installed SDK definitions and the physical journal control this finding. General vendor documentation corroborates the empty-queue meaning: [PassThruReadMsgs](https://quantexlab.de/en/develop/j2534/pt_readmsg.html). No generic retry example was adopted.

## Stock replay, causal candidates and exclusions

Independent replay executes actual stock RXI47E24 and response self-echo processing, obtaining full C1EF8F and C30000FF00FF00. No SMR/BRR/SDCR baud/protocol writes occur on that path. A separate actual-instruction replay shows that8periodic ticks between frame symbols reset the receive parser and can produce no reply to otherwise correct8300;0or7ticks pass. The tick duration and physical driver interbyte spacing are not established. Successful81 does not change the parser or this guard; a uniformly excessive gap should also affect81, so defaults alone cannot explain the different outcomes without actual cadence evidence. These tests establish a possible mechanism, not the vehicle cause. See `oem_transition_findings.md` and replay artifacts.

Ranked findings:

1. **Confirmed software contract defect:** explicit serial initialization was dropped from the reviewed installed-host path, and the physical logger omitted the argument/default evidence needed to audit it. Correct in a separate development branch; do not alter qualified RK02.
2. **Plausible physical cause:** an inherited timing/format setting produced an unacceptable frame gap or receive condition after81. Actual defaults and bus waveform are missing, so causality remains unproved.
3. **Other unresolved causes:** unexpected response hidden by the narrow filter, physical delivery/receive behavior, or a current-ROM executable difference. No observations distinguish these conclusively.
4. **Not supported:** wrong8300 checksum/length, an intentional stock baud switch/no-reply service, absent Test Mode inferred from disconnected fans, or a need simply to lengthen the timeout. ECUFlash's configured83 wait is shorter than RK02's.

BF/81 success proves communication at that stage; WriteMsgs success records provider acceptance, not ECU receipt. The final empty queue cannot alone distinguish malformed/missing electrical transmission from an ECU/parser or reception outcome.

## Development and qualification boundary

This analysis and event diff are produced before any corrective development. A new RK03-derived development branch may make the initialization contract explicit and improve argument/timing evidence, then test it against the archived host transcript and stock simulator. The frozen RK02 executable and failed acquisition remain untouched.

A valid replay must distinguish exact host requests/configuration from synthetic replies and stock instruction responses. Intentional differences—strict full replies/filtering, no programming-pin call, local seed transform, owned kernel size/content and no duplicate download/retry—require independent rationale. A fake replay cannot fill the missing successful physical83 waveform. No new physical attempt is qualified, requested or permitted in this run.

## Evidence and machine-readable diff

`RK02_VEHICLE_03_SESSION_TRANSITION_EVENT_DIFF.json` contains last-common/first-divergence records, full ordered frame comparison, physical historical event labels, timing/configuration deltas, confidence and canonical source paths/hashes. It points to the complete73-event installed-host offline API prefix and12-record RK02 journal. Unknown historical physical fields are explicitly null.

| Key evidence | SHA256 |
|---|---|
{evidence_rows}

The complete hash manifest is in the JSON rather than duplicating every path here. Original raw images and failed logs are never rewritten.
'''
    with (HERE / 'RK02_VEHICLE_03_SESSION_TRANSITION_ANALYSIS.md').open('x', encoding='utf-8') as stream:
        stream.write(markdown)
    outputs = [HERE / 'RK02_VEHICLE_03_SESSION_TRANSITION_ANALYSIS.md', diff_path]
    with (HERE/'ANALYSIS_BEFORE_DEVELOPMENT_MANIFEST.json').open('x',encoding='utf-8') as stream:
        json.dump({'created_at_utc':result['created_at_utc'],'development_started':False,
                   'files':[pin(p) for p in outputs]},stream,indent=2)
    print(json.dumps({'outputs':[pin(p) for p in outputs], 'physical_root_cause':'NOT_UNIQUELY_DETERMINED'}))


if __name__ == '__main__':
    main()
