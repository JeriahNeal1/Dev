"""Offline byte decoding and report production only. Never loads target/provider code."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, r'C:\Dev\Astra_A2WC511R\work\tools\m07_binary_audit')
import capstone

OUT = Path(__file__).resolve().parent
ASTRA = Path(r'C:\Dev\Astra_A2WC511R')
RK = Path(r'C:\Dev\A2WC511R_ReadKernel')
IMAGE = ASTRA / 'work/ecuflash_dynamic/discovery_003/loaded_ecuflash_image.bin'
EXE = Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe')
JOURNAL = ASTRA / 'work/ecuflash_dynamic/qualification_01/j2534.jsonl'
BASE = 0xE80000
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
data = IMAGE.read_bytes()
assert sha(IMAGE) == '1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18'
assert sha(EXE) == '5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115'
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
ranges = {
    'selected_transition': (0x9B5FE, 0x9B6F8),
    'initial_configuration': (0x9BB60, 0x9BCC4),
    'start_communication': (0x41AC0, 0x41B24),
    'access_timing': (0x416C0, 0x41726),
    'generic_sid_check': (0x424D0, 0x42626),
    'named_service_dispatch': (0x42750, 0x428C0),
    'ssm_frame_reader': (0x42DE0, 0x42F17),
    'provider_read': (0x97310, 0x97462),
    'stream_read': (0x97470, 0x97580),
    'provider_write': (0x97FB0, 0x98170),
    'set_config': (0x97B50, 0x97BD9),
    'set_parity': (0x97BE0, 0x97CB4),
    'set_baud': (0x97A30, 0x97B24),
    'clear_buffers': (0x96920, 0x969A4),
    'timeout_setter': (0x310F00, 0x310F0A),
    'generic_timeout_defaults': (0x3D809, 0x3D82C),
    'selected_upload': (0x9C0F0, 0x9C1B0),
    'delay_wrapper': (0x952A0, 0x952AD),
}
exports = []
for name, (start, end) in ranges.items():
    path = OUT / f'ecuflash_static_{name}.asm'
    rows = [f'; Input {IMAGE}', f'; SHA256 {sha(IMAGE)}; capture base 0x{BASE:08X}; addresses below are RVAs']
    for i in md.disasm(data[start:end], BASE + start):
        rows.append(f'{i.address-BASE:08x} {i.bytes.hex():24} {i.mnemonic} {i.op_str}')
    path.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    exports.append({'path': str(path), 'sha256': sha(path), 'start_rva': hex(start), 'end_exclusive_rva': hex(end), 'raw_range_sha256': hashlib.sha256(data[start:end]).hexdigest()})

events = []
for line_number, line in enumerate(JOURNAL.read_text().splitlines(), 1):
    row = json.loads(line)
    if 36 <= row['sequence'] <= 72:
        events.append({'source_line': line_number, **row})
assert all(row['physical'] is False for row in events)
trace = OUT / 'ecuflash_static_host_trace.json'
trace.write_text(json.dumps({'classification': 'ARCHIVED_INSTALLED_HOST_WITH_FAKE_PROVIDER_NOT_PHYSICAL_PROOF', 'source': str(JOURNAL), 'source_sha256': sha(JOURNAL), 'events': events}, indent=2) + '\n')
inputs = [IMAGE, EXE, JOURNAL,
    ASTRA / 'reports/local/ecuflash_dynamic/api_boundary/API_ENTRY_MAP.json',
    ASTRA / 'reports/local/ecuflash_dynamic/api_boundary/SEED_KEY_CONTRACT.md',
    ASTRA / 'reports/local/ecuflash_dynamic/api_boundary/DOWNLOAD_ACK_CONTRACT.md',
    RK / 'host/vendor/j2534_tactrix.h',
    RK / 'host/physical_build/rk02_physical_01/native_physical.cpp',
    RK / 'acquisitions/RK02_VEHICLE_03/native_api.jsonl']
findings = [
 {'id': 'ORDER_MATCHES', 'status': 'CONFIRMED_STATIC_AND_ARCHIVED_HOST',
  'claim': 'Selected ECUFlash caller performs 81, checks success, performs 83 with subfunction 00 and no additional argument bytes, checks success, then calls seed/key routine. No missing intermediate command or baud/config change is present between 81 and 83 in this path.',
  'rvas': ['9B5FE-9B638', '41AC0-41B23', '416C0-41723'], 'journal_sequences': [53,54,55,56,57]},
 {'id': 'REPLY_POLICY', 'status': 'CONFIRMED_STATIC',
  'claim': '81 and 83 wrappers use generic framed reply and positive-SID checking. Generic success is response SID=request SID+0x40. StartCommunication discards response payload after the generic call; the selected caller likewise checks only the boolean from 83. No EF8F-derived timing/baud update occurs at this transition. This is looser than RK02 exact C1EF8F/C30000FF00FF00 assertions.',
  'rvas': ['41AC0-41B23', '9B606-9B638', '42583-4258E', '425E8-42623', '42DE0-42F14'],
  'limit': 'The archived fake run supplied only C1 and C3; it did not test full physical C1EF8F or demonstrate physical reply timing.'},
 {'id': 'EXPLICIT_CONFIGURATION_OMITTED_IN_RK02', 'status': 'CONFIRMED_IMPLEMENTATION_GAP_CAUSALITY_UNPROVEN',
  'claim': 'ECUFlash initializes parity=0, P1_MAX=1, P3_MIN=0, P4_MIN=0, LOOPBACK=0 before BF/81/83. RK02 opens the same ISO9141 raw 4800 channel but does not issue this initial SET_CONFIG. Therefore its timing/parity/loopback defaults were neither explicitly selected nor journaled.',
  'config': [{'parameter':22,'name':'PARITY','value':0},{'parameter':7,'name':'P1_MAX','value':1},{'parameter':10,'name':'P3_MIN','value':0},{'parameter':12,'name':'P4_MIN','value':0},{'parameter':3,'name':'LOOPBACK','value':0}],
  'rvas': ['9BBBA-9BBF1', '87B694+0x3C=97BE0', '87B694+0x5C=97B50', '97C92-97C9E', '97B90-97BA9'],
  'journal_sequences': [36,37,40,41,42,43,44],
  'limit': 'No GET_CONFIG or physical byte-spacing capture establishes the actual failed session defaults; setting these values is a reproducibility correction, not proof of the cause of silence.'},
 {'id': 'FILTER_AND_ECHO_DIFFERENCES', 'status': 'CONFIRMED_STATIC_OR_ARCHIVED_HOST',
  'claim': 'ECUFlash fake-host trace uses PASS_FILTER with four zero mask/pattern bytes and LOOPBACK=0, plus TX/RX buffer clears. RK02 uses a narrow 80F010 receive filter and recognizes an exact request echo. These are intentional policy differences, not demonstrated causes of failure. ECUFlash lower read skips RxStatus bits 0x0E and otherwise copies data; nonzero provider status fails.',
  'rvas': ['9BC06-9BC1E', '96959-96999', '9735F-973A7'], 'journal_sequences': [45,46,47,49,50],
  'limit': 'The host trace pin9 voltage OFF is not evidence that any positive programming voltage or extra physical pin action is required.'},
 {'id': 'READ_TIMEOUTS', 'status': 'CONFIRMED_ARCHIVED_HOST_AND_STATIC_MECHANISM',
  'claim': 'Archived installed-host API arguments are BF ReadMsgs timeout400ms, 81 timeout2000ms, 83 timeout500ms, seed/key timeout500ms. ECUFlash generic return restores transport timeout from object+0x20 (default500) through vtable+0x68; that setter writes transport+0x0C, which the provider read passes as its timeout. RK02 uses at most1000ms per read under a nominal2000ms transaction deadline, and aborts on first nonzero status. ECUFlash lower provider read also fails on nonzero; retrying ERR_BUFFER_EMPTY is not established as a missing ECUFlash behavior.',
  'rvas': ['3D817', '42612-4261A', '310F00-310F07', '9735F-973A7'], 'journal_sequences': [52,54,56,58,61],
  'limit': 'Fake response timestamps are synthetic and waits are capped50ms. These recorded API timeout arguments are not measured physical reply latency. RK02 failed after about1002ms at 83, longer than the archived ECUFlash requested500ms.'},
 {'id': 'AFTER_83_AND_FIRST_UPLOAD', 'status': 'CONFIRMED_STATIC_AND_ARCHIVED_HOST',
  'claim': 'After83 success:2701 seed,2702 key, explicit200ms delay call, timeout2000,108502 session, explicit100ms delay call then DATA_RATE15625. Selected upload has another200ms delay call, sends34FF300004001234 twice, then begins128-byte36 transfer atFFFF3000. No baud change occurs at81->83; kernelstart/read stages are later.',
  'rvas': ['9B638-9B6C8', '9C0F5-9C1A6'], 'journal_sequences': [57,59,60,62,64,67,69,71],
  'limit': 'The archived upload is installed DUAL1.07 length0x1234, not RK02 and not proof of current physical ECU behavior. Later34 duplication is outside the current failed transition.'},
]
report = {
 'schema':1, 'status':'COMPLETED_OFFLINE_STATIC_ANALYSIS', 'created_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'Installed ECUFlash read_sti05 transition at 81 -> 83 00; no target/provider execution, vehicle access, tests or sealed source edits.',
 'capture_base':hex(BASE), 'input_files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in inputs],
 'findings':findings, 'assembly_exports':exports,
 'trace_export':{'path':str(trace),'sha256':sha(trace)},
 'root_cause_status':'UNPROVEN_PHYSICAL_CAUSALITY; EXPLICIT_TRANSPORT_INITIALIZATION_OMISSION_CONFIRMED',
 'excluded_claims':['No proof ECU rejected83','No proof OpenPort did not put83onwire','No proof ECUFlash retriesERR_BUFFER_EMPTY','No proof provider cleanup or ECUreset from process exit','No hardware retry authorized by this report'],
}
report_path=OUT/'ecuflash_static_findings.json'
report_path.write_text(json.dumps(report,indent=2)+'\n')
md_text = '''# Installed ECUFlash 81 -> 83 00 static findings

The command order is consistent with RK02. The concrete implementation gap is RK02's omitted explicit initial serial configuration. Its causal role in the missing physical reply is not established.

This review decoded the previously captured installed ECUFlash image offline. It did not launch ECUFlash, a provider, a vehicle tool, RK02, or a test. Existing acquisition and qualification files were read only. Address references below are RVAs in the captured image at base `0xE80000`; each companion assembly file identifies its source hash. The JSON records all input/output hashes.

## Provenance

- Installed ECUFlash executable SHA256: `5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115`.
- Captured image SHA256: `1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18`.
- Archived qualification_01 journal is actual installed-host API behavior against a **fake provider/model**. All events are physical=false. Its replies C1 and C3 are synthetic hypotheses, not captured physical C1EF8F/C30000FF00FF00. Fake timestamps are synthetic and read waits capped50ms. API arguments remain useful evidence of what the installed host requested.

## Exact transition

`ecuflash_static_selected_transition.asm` RVA9B5FE loads the protocol object; 9B601 calls StartCommunication at41AC0. At9B606 success is checked. 9B623/625/627 push zero length, null data and subfunction00 for AccessTimingParameters at416C0 (call9B629). 9B62E checks success, then9B638 calls the seed/key routine9AFD0. There is no intermediate opcode, IOCTL, explicit delay, baud change or EF8F-derived setting at this transition.

The81wrapper reserves a response buffer, invokes the named generic service, and returns its boolean without inspecting the returned data. GenericSIDcheck424D0 validates the framed response and compares responseSID to requestSID+40 at42583..4258E. The83caller likewise ignores returned timing bytes. Thus fullC1EF8F has no special configuration branch in this reviewed path. RK02 deliberately requires exact full reply payloads; that stricter policy did not trigger the physical failure, because no83reply was delivered.

The archived host confirms exact frames `8010F0018102` then `8010F002830005`, then seed `8010F0022701AA` (journal lines54,56,58; sequence=source line-1).

## Explicit initial serial setup

| Setting | ECUFlash host value | Evidence |
| --- | ---: | --- |
| Protocol / flags / baud | 3 / 0x200 /4800 | journalseq36; initializer9BB7F..9BB98 |
| PARITY(22) |0| static9BBBA..9BBC1 ->97BE0 ->97C9C; seq37,40 |
| P1_MAX(7) |1| static9BBC4..9BBCD; seq41 |
| P3_MIN(10) |0| static9BBD0..9BBD9; seq42 |
| P4_MIN(12) |0| static9BBDC..9BBE5; seq43 |
| LOOPBACK(3) |0| static9BBE8..9BBF1; seq44 |

The configuration vtable at87B694 maps slot+5C to97B50, which constructs a one-item SET_CONFIG and invokesIoctl2 at97BA9. Slot+3C maps to97BE0, which routes parity through parameter22 at97C9C. The vendor header defines the parameter identifiers at lines156..178. Values are independently established by code and archived host API arguments; flags0x200 are directly established by the archived host trace.

Frozen RK02 native_physical.cpp opens protocol3/flags0x200/4800 and sets its filter but sends no initial SET_CONFIG. Its physical journal has no GET_CONFIG, so actual timing/parity/loopback defaults remain unknown. The successfully corrected passive uses explicit configuration too, but has intentional differences: P3_MIN=1 and LOOPBACK=1 versus ECUFlash's zero values. It is therefore evidence that explicit setup is available, not proof that either value set alone fixes83.

ECUFlash uses four-zero-byte PASS_FILTER, LOOPBACK0, and clearsTX/RX buffers. RK02 uses a strict80F010 filter and explicit exact-request echo handling. These differ but no evidence isolates either as the cause. The archived pin9 voltageOFF command establishes no need for positive programming voltage or a new physical pin action.

## Timeouts and receive policy

Archived requested ReadMsgs timeouts: BF400ms,81 2000ms,83 500ms,seed/key500ms (seq52,54,56,58,61). Static generic return42612..4261A restores timeout from protocol+20, default500 at3D817, through vtable+68. That slot is310F00, a setter for transport+0C. Read consumer9735F passes that value to ReadMsgs.

Read consumer9737D..973A7 fails on any nonzero API status; on successful metadata it skips RxStatus bits0x0E. Thus there is no evidence that ECUFlash would retry the ERR_BUFFER_EMPTY returned to RK02. RK02's nominal2000ms transaction deadline does not mean it waited2000ms: it aborted after its first1000ms ReadMsgs returned16. That is a concrete timing-policy difference; ECUFlash's archived83timeout is shorter, so increasing a timeout alone is not an evidence-backed cure.

## After83

On success the selected caller performs seed/key, then a200ms delay call (9B648..9B64D), sets timeout2000 (9B655..9B65C), sends108502 through the session wrapper (9B68D), then a100ms delay call and baud15625 (9B69A..9B6C5). Selected upload9C0F0 adds200ms, sends34 twice at9C154/9C164, then transfers128-byte chunks beginningFFFF3000. Archived first declaration is34FF300004001234 and first36 is seq71. This is the installed DUAL1.07/0x1234-byte kernel path, not RK02. It does not identify a missing operation before83.

## Bounded conclusion

An isolated development correction can explicitly set and journal the serial configuration beforeBF, retaining the sealed RK02 artifacts. That would address a confirmed reproducibility gap. Physical root cause remains unproven: no captured wire timing/default configuration establishes whether83was emitted, ignored, filtered, or lost; no responseNRC establishes ECU rejection. Static and fake-host evidence cannot authorize a new physical attempt. Process exit alone proves neither provider cleanup nor ECU reset.
'''
(OUT/'ecuflash_static_findings.md').write_text(md_text,encoding='utf-8')
print(json.dumps({'report':str(report_path),'sha256':sha(report_path),'markdown_sha256':sha(OUT/'ecuflash_static_findings.md'),'assembly_count':len(exports)}))
