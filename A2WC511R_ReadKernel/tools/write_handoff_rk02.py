"""Create the human-only RK02 documents and backed-up project handoff.

No application, provider, physical executable, transport or ECU is opened.
Exclusive outputs make this a one-time release preparation operation.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import datetime,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
OLD=Path(r'C:\Dev\Astra_A2WC511R')
sys.path.insert(0,str(ROOT/'tools'))
from validate import PIN,HOST_SHA,PHYSICAL_IDS
from verify_preservation import verify_all

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def write(p,text):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def js(p,d):write(p,json.dumps(d,indent=2)+'\n')

def main():
    physical=ROOT/'host/physical_build/rk02_physical_01/BUILD_MANIFEST.json'
    build=json.loads(physical.read_text());cert=ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json'
    require(build['status']=='COMPILED_NEVER_EXECUTED_PHYSICAL_REQUIRED','Compile-only manifest required')
    require(build['executed'] is False and build['provider_loaded_during_build'] is False,'No physical execution permitted')
    require(build['tested_fake_binding']['kernel_sha256']==PIN,'Wrong kernel')
    exe=Path(build['native_binary']['path']);exe_sha=sha(exe);cert_sha=sha(cert)
    require(exe_sha==build['native_binary']['sha256'] and cert_sha==build['certificate']['sha256'],'Physical derivation changed')
    review=json.loads((ROOT/'evidence/rk02/PHYSICAL_DERIVATION_REVIEW.json').read_text())
    require(review['status']=='PASS','Independent physical source/header derivation review required')
    require(verify_all()['status']=='PASS','Preservation must pass before handoff')
    for p in (ROOT/'HUMAN_ACQUISITION_RK02.md',ROOT/'ENGINEERING_GATES.json',ROOT/'evidence/rk02/FINAL_QUALIFICATION.md',ROOT/'evidence/rk02/handoff'):
        require(not p.exists(),'Exclusive release output already exists: '+str(p))
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    session=ROOT/'acquisitions/RK02_VEHICLE_01'
    observer=OLD/'integrations/prehardware/capture.py'
    validator=ROOT/'tools/validate.py'
    finalizer=ROOT/'host/finalize.py'
    copied=session/'owned_physical_read32.exe'
    procedure=rf'''# RK02: one human-operated acquisition-only session

Release class: **TEMP_RAM_ACQUISITION_TOOL**. Offline software is qualified; hardware remains **PHYSICAL_REQUIRED**. This procedure was prepared, not executed. It authorizes no flash Write, Test Write, erase, program, commit, persistent modification or active engine/transmission control. Installed ECUFlash Read, DUAL1.07 and RK01 are excluded.

## Fixed identities

| Item | Exact binding |
|---|---|
| RK02 kernel SHA256 | `{PIN}` |
| Kernel | 1808 bytes, SH-2E / SH7058, big endian |
| Upload / entry | `[FFFF3000,FFFF3710)` / `FFFF3004` |
| Total temporary takeover / private stack | `[FFFF3000,FFFF3730)` / `[FFFF371C,FFFF372C)` |
| Version | `A2WC511R-RK02` followed by NUL |
| ECU BF identity | `2F12515306` |
| Physical host SHA256 | `{exe_sha}` |
| Offline certificate SHA256 | `{cert_sha}` |
| Qualified fake host SHA256 | `{HOST_SHA}` |
| Provider | `C:\Windows\SysWOW64\op20pt32.dll` |
| Provider SHA256 | `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf` |

`RELEASE_CERTIFICATE.json` binds this document, the exact physical executable, qualification index and checker. Preserve the whole project at its qualified paths. The executable accepts no provider, kernel, address or opcode selection. It embeds the RK02 bytes and certificate hash. Its real-provider path was only hashed during qualification; the executable has never been launched, including self-test.

## Before connecting

Use the actual stationary vehicle with engine OFF. Have its correct service procedure for diagnostic/programming-mode admission, stable electrical power and **verified ECU power-down/reset** available before starting. Confirm the physical conditions for the OEM RAM-loader session, supported SH7058 clock/SCI path and watchdog behavior. No connector jumper, pin meaning or numerical key-off interval is certified by this software package. If those conditions or the power-down method are unknown, stop before takeover; do not improvise wiring or assume a timed wait proves RAM loss. Disconnecting USB alone is not ECU reset.

Close ECUFlash, RomRaider and every other J2534 client. No concurrent client is allowed. Keep ignition off until the applicable service procedure calls for it; never start the engine during this session. Record operator, vehicle association, UTC, ignition events, power support and the chosen power-down verification method in the session notes. A matching BF identity does not by itself identify the current calibration or prove that a tuned image retained its stock loader.

Run this **offline-only** check first in PowerShell. Require exit code 0, `software_status: PASS`, overall `CONDITIONAL`, and only the documented physical gates. FAIL, missing data or changed hashes stop the session.

```powershell
py -3.14 -B {validator} --report {ROOT}\evidence\rk02\PRE_CONNECTION_VALIDATION.json
if ($LASTEXITCODE -ne 0) {{ throw 'RK02 qualification failed; do not connect or upload' }}
```

The report filename is exclusive. If it already exists, retain it and choose a new report filename; never remove qualification evidence. Create a new acquisition folder and copy only the pinned executable. These commands are preparation and do not load a provider:

```powershell
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath '{session}') {{ throw 'Session path already exists; preserve it' }}
New-Item -ItemType Directory -Path '{session}' | Out-Null
Copy-Item -LiteralPath '{exe}' -Destination '{copied}'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath '{copied}').Hash.ToLowerInvariant() -ne '{exe_sha}') {{ throw 'Wrong acquisition executable' }}
```

## Single connection and acquisition order

1. Connect the OpenPort according to the vehicle service procedure. Establish the documented ignition-on, engine-off diagnostic state. Do not open ECUFlash or another logger.
2. Obtain passive OEM **BF identity first**. The following fixed observer command performs BF before any A8 request and refuses an ECU identity other than `2F12515306`.
3. Capture the six fixed raw observations with their request/response timestamps and host reason predicates: `FFFF4C75`, `FFFF4C8D`, `FFFF4CA1`, `FFFF4C50`, `FFFF4BC1`, `FFFF4BC2`.

```powershell
py -3.14 -B {observer} --backend physical-j2534 --authorize-physical-read-only --count 120 --interval-ms 250 --output {session}\pre_kernel_A8.jsonl
if ($LASTEXITCODE -ne 0) {{ throw 'Passive OEM capture failed; do not enter RAM session' }}
```

4. Confirm `PASS_CAPTURE_ONLY`, 120 samples, null error/cleanup_error, expected BF identity, and that the observer and its broker have exited. Its raw observations are untouched OEM evidence; their reason predicates do not certify TCU freshness or fault coverage. Retain the JSONL and provider stderr file. Close the passive observer fully before continuing.
5. Enter the reviewed OEM RAM-upload session using **only** the fixed executable below. It repeats BF, performs the reviewed session/security sequence and fails on any unexpected reply. This is a temporary RAM takeover, not flash programming.
6. The same invocation uploads exactly the embedded, hash-pinned RK02 object to `[FFFF3000,FFFF3710)` in fixed reviewed chunks. No arbitrary upload is possible through its interface.
7. It starts exactly `FFFF3004` through the reviewed OEM start command.
8. It verifies the exact RK02 identity/version before accepting any ROM block.
9. It reads `[000000,100000)` twice, 2048 ascending 512-byte blocks per pass. Every response must match opcode, pass, address, size and checksum. There is no CRC-based page substitution.

Run the following **once**, manually. This is the first command in this document that performs temporary ECU RAM writes. `cmd.exe` redirection retains an ASCII/UTF-8-compatible native log instead of PowerShell 5 UTF-16 redirection. Keep the terminal until the process exits; do not launch it again on a failure.

```powershell
cmd.exe /d /c "{copied} --acquire-owned-readkernel --certificate-sha256 {cert_sha} > {session}\native.log 2>&1"
$acquisitionExit = $LASTEXITCODE
```

10. Require exit code 0 and `PASS_NATIVE_FIXED_PHYSICAL_TWO_FULL_READS` in `native.log`. The host compares every second-pass block with the first; both raw files must be exactly 1,048,576 bytes. Run the offline finalizer to replay the entire journal, verify the strict transmitted command sequence and actual received bytes, and require equal SHA256 hashes:

```powershell
if ($acquisitionExit -ne 0) {{ throw 'Terminal acquisition failure; follow the failure exit below' }}
py -3.14 -B {finalizer} --physical-build rk02_physical_01 {session}
if ($LASTEXITCODE -ne 0) {{ throw 'Capture integrity failed; follow the failure exit below' }}
Get-FileHash -Algorithm SHA256 -LiteralPath '{session}\finalized\raw_pass0.bin', '{session}\finalized\raw_pass1.bin'
```

11. Preserve both original `pass0.partial.bin` / `pass1.partial.bin`, `native_api.jsonl`, `native.log`, executable and the read-only finalized raw copies with `FINALIZATION.json`. Do not normalize checksums, fill gaps, edit, resave through a ROM editor or rename an incomplete result as the current ROM. The finalizer must report `PASS_RAW_CAPTURE_INTEGRITY`; its physical-session association deliberately remains unproved by software. Associate the real vehicle and capture using the operator notes plus pre/post BF records. Missing or unexpected A2WC511R identity literals are a reason for offline review, never correction of the raw capture.
12. Confirm transport close. On the successful path the last native API records are StopMsgFilter, Disconnect and Close; the process exits. The kernel stays in its private terminal state. Adapter close does not restart OEM software.
13. Turn ignition OFF and apply the pre-established vehicle-specific **verified power-down** method. Record actual evidence and elapsed interval. Do not substitute an arbitrary wait or USB removal for ECU power loss. Do not leave the vehicle in the RAM-kernel session.
14. Restore ignition ON, engine OFF, according to the service procedure. OEM reset must occur from ROM after RAM loss; no jump-back command is sent.
15. Verify fresh OEM BF identity `2F12515306` with the same passive-only observer. This also captures the optional six observations in step 16:

```powershell
py -3.14 -B {observer} --backend physical-j2534 --authorize-physical-read-only --count 8 --interval-ms 250 --output {session}\post_restart_A8.jsonl
if ($LASTEXITCODE -ne 0) {{ throw 'OEM return not confirmed; stop and follow the approved vehicle recovery procedure' }}
```

16. Retain the optional eight post-restart six-channel snapshots and compare BF identity with the pre-kernel record. Require `PASS_CAPTURE_ONLY` and confirmed broker cleanup. This is an OEM-return check, not validation of engine/transmission outputs or any active feature.
17. Close all clients and disconnect OpenPort according to the vehicle procedure. Preserve the session folder and an independent backup of both raw images. Return to offline analysis; this procedure includes no vehicle firmware write.

## Failure exit

At the first identity, upload, start, version, read, checksum, transport or finalizer failure: preserve all partial files and journals, label the capture **INCOMPLETE_NOT_CURRENT_ROM**, and do not retry, re-upload, invoke another provider/tool or fall back to ECUFlash. The host stops issuing J2534 calls on a terminal fault. Its process exit releases host resources, but that is not a proved ECU reset or an explicitly successful provider Close. Confirm the client has exited, then use the pre-established ignition OFF/verified power-down/ON sequence and passive BF check. If OEM return is not confirmed, stop and use the vehicle's approved recovery process. No erase/program/reset opcode is an allowed recovery action here.

## Evidence this session can close

The session can associate two byte-identical, lossless raw captures with this actual ECU, record real provider/session acceptance, and demonstrate OEM BF return after independently verified power-down. It does not prove every silicon timing margin, arbitrary NMI/watchdog behavior, calibration safety, or firmware residency. Those physical claims must be recorded from actual observations; no software PASS is a substitute. Read-only file attributes and hash seals make alteration detectable; they are not WORM storage or a signature against a same-user attacker.
'''
    write(ROOT/'HUMAN_ACQUISITION_RK02.md',procedure)
    report_refs={
      'CLEAN_REPRODUCIBLE_RK02_BINARY':'evidence/rk02/build/ARTIFACT_REVIEW_FINAL.json',
      'INDEPENDENT_BINARY_STORE_CONTROL_REVIEW':'evidence/contracts/BINARY_REVIEW_rk02_01.json',
      'UNREACHABLE_HEADER_AND_ALIGNMENT_PADDING':'evidence/contracts/UNREACHABLE_PADDING_RK02.json',
      'ACTUAL_STOCK_LOADER_UPLOAD_RECONSTRUCTION_ENTRY':'evidence/contracts/UPLOAD_WIRE_CONTRACT_RK02.json',
      'OEM_SESSION_SECURITY_AND_QUIESCENCE_CONTRACT':'evidence/contracts/OEM_ACQUISITION_CONTRACT_RK02.json',
      'SCI2_HALF_DUPLEX_SELF_ECHO':'evidence/rk02/sim/SELF_ECHO_QUALIFICATION.json',
      'RK02_ENTRY_RAM_AND_PERIPHERAL_CONTRACT':'evidence/rk02/ENTRY_PERIPHERAL_CONTRACT.json',
      'COMPLETE_INSTRUCTION_BRANCH_STORE_STACK_COVERAGE':'evidence/rk02/sim/QUALIFICATION.json',
      'LOSSLESS_TWO_FULL_READS_ALL_FIXTURE_CLASSES':'evidence/rk02/LOSSLESS_FIXTURES.json',
      'FIXED_NATIVE_HOST_ABI_ALLOWLIST':'evidence/rk02/host/HOST_QUALIFICATION.json',
      'TERMINAL_HOST_FAULTS':'evidence/rk02/host/HOST_FAULTS.json',
      'FINALIZER_ADVERSARIAL_CONTROLS':'evidence/rk02/host/tests/FINALIZER_TESTS.json',
      'VALIDATOR_FAIL_CLOSED_NEGATIVE_CONTROLS':'evidence/rk02/VALIDATOR_REGRESSIONS.json',
      'RELEASE_GATES_SURVIVE_PYTHON_OPTIMIZATION':'evidence/rk02/RELEASE_OPTIMIZATION_REGRESSIONS.json',
      'INDEPENDENT_COMPILE_ONLY_PHYSICAL_HOST_DERIVATION':'evidence/rk02/PHYSICAL_DERIVATION_REVIEW.json',
      'PRIOR_ARTIFACT_INSTALLATION_REGISTRY_PRESERVATION':'evidence/rk02/FINAL_PRESERVATION.json',
      'RK01_PERMANENT_SUPERSESSION':'evidence/RK01_SUPERSEDED.json'}
    gates={'schema':1,'checkpoint':'RK02_SOFTWARE_QUALIFIED_PHYSICAL_ACQUISITION_ONLY','updated_utc':now,
      'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','status':'CONDITIONAL','software_status':'PASS',
      'kernel_sha256':PIN,'kernel_bytes':1808,'physical_host_sha256':exe_sha,'fake_host_sha256':HOST_SHA,
      'physical_host_executed':False,'real_provider_loaded_this_run':False,'current_ROM_identified':False,
      'ECU_flash_image_release':False,'new_MerpMod_firmware':False,'next_rational_action':'B_SINGLE_HUMAN_ACQUISITION_ONLY_SUBJECT_TO_PHYSICAL_PREFLIGHT',
      'software_gates':[{'id':key,'status':'PASS','report':path,'sha256':sha(ROOT/path)} for key,path in report_refs.items()],
      'physical_gates':[{'id':key,'status':'PHYSICAL_REQUIRED'} for key in sorted(PHYSICAL_IDS)],
      'historical_excluded_paths':[
        {'id':'RK01','status':'SUPERSEDED_NOT_FOR_HARDWARE','permanent':True},
        {'id':'ECUFLASH_UNIVERSAL_EXACT_IMAGE_ACQUISITION','status':'FAIL','permanent':True,'reason':'Captured successful CRC substitution loses 37 nonblank bytes'},
        {'id':'DUAL1_07_STARTUP_CONTRACT','status':'FAIL','reason':'Inherited FFFF5444 and prohibited FFFFE803 path; no dependency remains'},
        {'id':'ECU_RESIDENT_BRANCH_OWNERSHIP','status':'FAIL','frozen':True,'owned_bytes':0},
        {'id':'HISTORICAL_LOG_PRESERVATION','status':'FAIL','reason':'Earlier 7-log loss, 3 restored, 4 unrecovered; not erased by current preservation PASS'}],
      'scope':'PASS is limited to pinned offline software/model contracts. Real clock, entry, UART/electrical, watchdog, reset and current-vehicle association remain physical.',
      'procedure':{'path':'HUMAN_ACQUISITION_RK02.md','sha256':sha(ROOT/'HUMAN_ACQUISITION_RK02.md')}}
    js(ROOT/'ENGINEERING_GATES.json',gates)
    write(ROOT/'evidence/rk02/FINAL_QUALIFICATION.md',f'''# RK02 final software qualification

The next rational action is **B: one human-operated acquisition-only connection**, subject to the physical preflight and stop conditions in [the immutable procedure](../../HUMAN_ACQUISITION_RK02.md). All required software gates pass for the exact objects below. Overall status is **CONDITIONAL**, not physical acceptance and not an ECU firmware release. No real provider was loaded and no physical executable was run.

Kernel SHA256 `{PIN}`; 1808 bytes, 335 executable instructions; upload `[FFFF3000,FFFF3710)`, entry `FFFF3004`, total temporary RAM `[FFFF3000,FFFF3730)`. The independent clean builds have identical raw and ELF bytes. The fixed physical host SHA256 is `{exe_sha}`; its reviewed fake predecessor is `{HOST_SHA}`. The physical host is compile-only with exact protocol/ciphertext preservation and a certificate gate before provider loading.

RK02 uses receive-only SCR10 between requests and transmit-only SCR20 for every response. It checks stale receive/error state before TDR, tracks both pending TDR and shifting TSR, waits for final TEND and restores RX only after completion. The model checks start-bit receive admission. Every-byte, delayed-completion, final-byte, fragmentation, immediately adjacent RX and error cases are covered. A genuinely new start after RX is restored can reject the session; unlimited electrical echo delay is not assumed. RK01 reproduces the self-echo/overrun failure and remains permanently SUPERSEDED_NOT_FOR_HARDWARE.

All 335 emitted executable instructions and all 80 directions of 40 conditional branches execute in the new qualification. Three header/alignment NOPs outside that executable set have an explicit no-entry/no-fallthrough proof. The bounded suite includes 535 kernel fault/fuzz cases, 14 closed-world negatives, 13 echo cases, 16 model test groups and 42,276 steps compared against the frozen CPU implementation. Normal software stack use is zero; one admitted hardware exception pushes 8 bytes into a 16-byte private stack. Repeated NMI arrivals before the handler and the pre-private-entry window remain physical assumptions.

The independent final disassembly identifies 22 CPU store sites: four private RAM sites and 18 documented MMIO sites. All execute, with every observed destination inside its static domain; injected exception stores are separately classified. There are no reachable flash enable/unlock/erase/program/commit paths, prohibited E803 accesses, arbitrary targets, inherited RAM reads or unsupported executed instructions/peripherals. The SCI2/MMIO model is an explicit deterministic contract, not a silicon timing measurement.

The actual stock loader executes 479,183 instructions across 17 upload/start frames, writes 452 ordered longwords and reconstructs the exact 1808-byte RK02 object before fixed-entry handoff. The independently recovered OEM session/security contract stays intact. OEM loader buffers/stack and its quiescence effects are separately documented; the kernel does not jump back into the overwritten OEM runtime.

Exact stock, composite and deterministic-random 1MiB fixtures each complete two byte-identical reads. The composite contains address-derived data, zero/FF pages, the nonblank FF-CRC collision and sentinels throughout historical gaps. Each complete run emits 2,142,228 modeled TX characters with self-echo ignored under RE0 and zero accepted echo/overrun; the two native fake-provider runs execute the actual uploaded RK02 binary for every kernel response. No page is synthesized from a CRC.

The final native fake host passes all 22 terminal faults, 33 pure contract checks, 32 fragmented positives and 28 adversarial finalizer checks. Native x86 ABI and fixed command-prefix evidence are hash-linked. Reordered, duplicate, stale pass/address, malformed and interrupted results cannot be promoted. On a terminal transport error no further J2534 call is issued; process exit is not claimed to perform ECU reset. Incomplete captures retain their partial designation.

The validator rechecks exact file bytes, source/toolchain/build associations, runtime-model identity, disassembled stores, aggregate instruction/edge counts, each complete fixture, host allowlist/finalizer evidence and live preservation. Independent mutations must fail even when a mutated report is re-sealed; release gates also reject under Python -O. The final certificate binds the index, validator, procedure and exact physical host. The standard command is `py -3.14 -B C:\\Dev\\A2WC511R_ReadKernel\\tools\\validate.py`.

All frozen M0/M06/M07, Diaphora, canonical/damaged IDB, prior dynamic Read and RK01 evidence remain unchanged. A fresh snapshot covers 943 files plus registry views; the prior 1667-file seal is checked with only six explicit backed-up handoff files allowed to change. The earlier four unrecovered historical logs remain a prior FAIL. The 31 unqualified IDB functions remain withheld. Installed ECUFlash exactness stays permanently rejected; DUAL1.07 is preserved and unused.

Actual OpenPort/electrical behavior, current ECU loader acceptance, clock/intact upload/entry, external watchdog/NMI, verified power-down/OEM restart and physical capture association remain PHYSICAL_REQUIRED. No numerical key-off delay or wiring procedure is invented. The human procedure must stop before takeover if its vehicle-specific physical preconditions are unavailable. There is no launch/ALS, fuel, timing, boost/WGDC, MAF, DBW, rev-limit or transmission-torque work, and no new flash image.
''')
    # These are the only writes in the earlier project. Preserve exact original
    # bytes first and record before/after hashes for the live preservation gate.
    dest=ROOT/'evidence/rk02/handoff';dest.mkdir()
    names=('CURRENT_STATE.md','NEXT_ACTIONS.md','DECISIONS.md','SESSION_LOG.md','CHECKPOINT.json','RUN_CONTRACT.md')
    originals={name:(OLD/'state'/name).read_bytes() for name in names}
    for name,raw in originals.items():
        p=dest/name
        with p.open('xb') as f:f.write(raw)
        p.chmod(0o444)
    current=f'''# RK02 software-qualified acquisition checkpoint

The next rational action is **B: one human-operated acquisition-only Subaru connection**, subject to the explicit physical preflight and stop conditions in `{ROOT}/HUMAN_ACQUISITION_RK02.md`. No physical operation was performed in this run. Overall status is CONDITIONAL; every required pinned software gate is PASS. Actual adapter/electrical/ECU acceptance, clock/entry/watchdog and verified power-down/OEM restart remain PHYSICAL_REQUIRED. If the vehicle-specific physical preconditions are unavailable, stop before RAM takeover.

The supported observational path remains host-native fixed BF/A8. RK02 is a separate TEMP_RAM_ACQUISITION_TOOL: 1808 bytes, SHA256 {PIN}, fixed upload FFFF3000 / entry FFFF3004, no inherited RAM or flash-write path. Its half-duplex SCI2 correction disables receive for every response and waits for the final TEND before restoring RX. RK01 is permanently SUPERSEDED_NOT_FOR_HARDWARE; its preserved directory is unchanged. The physical acquisition host SHA256 is {exe_sha}; compiled only, never launched.

All 335 instructions and 80/80 conditional directions execute in the new binary; 22 store sites independently bounded, stack 0 software / 8 bytes one admitted exception / 16-byte capacity. Three 1MiB fixtures each pass two complete byte-identical reads with self-echo; composite includes the nonblank FF-CRC collision and historical-gap sentinels. All 22 native host fault cases and 28 adversarial finalizer controls pass. Read the complete evidence at `{ROOT}/evidence/rk02/FINAL_QUALIFICATION.md` and gates at `{ROOT}/ENGINEERING_GATES.json`. The mandatory no-provider validator is `{ROOT}/tools/validate.py`; final release certificate `{ROOT}/RELEASE_CERTIFICATE.json`.

Current vehicle ROM is still UNIDENTIFIED. The future session is passive BF/six A8 first, close observer, fixed owned RAM session/upload/start/version, two raw 1MiB reads, exact hashes/raw preservation, transport close, verified ignition power loss and fresh OEM BF return. No flash Write/Test Write/erase/program/commit, no fallback ECUFlash and no active-control work. Installed ECUFlash universal exactness remains permanently FAIL because CRC substitution loses 37 nonblank bytes while reporting success. DUAL1.07 startup remains rejected; the new tool has no dependency on it.

Residency research remains frozen at zero owned ROM bytes; no M0/M06/M07/M08 changes or new ECU firmware image. Canonical recovered IDB, damaged evidence and 31 unqualified functions remain unchanged. Prior 1667-file seal and fresh 943-file snapshot/registry checks pass with this six-file backed-up handoff. Historical four unrecovered logs remain a prior FAIL, not repaired by the current preservation result. Handoff backup/authorization: `{dest}/MANIFEST.json`.
'''
    next_actions=f'''# Next action: human-only RK02 acquisition

1. Preserve the qualified tree and frozen prior evidence. Run `{ROOT}/tools/validate.py`; any software FAIL stops the procedure.
2. Read `{ROOT}/HUMAN_ACQUISITION_RK02.md` in full. Verify its exact kernel/host/certificate hashes and vehicle-specific power/admission/reset prerequisites before connecting or taking over RAM. No real provider has been loaded during qualification.
3. Perform at most the single manual acquisition-only connection described there: passive OEM BF/A8, fixed RK02 upload/start, two exact full reads, close, verified power loss and OEM BF return. Stop at the first discrepancy; retain incomplete evidence and use only the documented physical exit model.
4. Afterward associate both immutable raw images with the vehicle/session and perform offline current-calibration review. No active feature or vehicle flash image is authorized by this acquisition-tool certificate.
5. Do not requalify RK01, ECUFlash CRC/fill exactness or DUAL1.07 startup, resume sibling-ROM/residency searching, or rerun unaffected fixtures. Current-ROM identity is still unknown until an actual evidenced acquisition.
'''
    note=f'\n\n{now} RK02_SOFTWARE_QUALIFIED_PHYSICAL_ACQUISITION_ONLY, session 01a0da26-addc-7fe1-84df-8c0baa8174f8. Owned kernel {PIN}; physical host {exe_sha}, compile-only. All scoped software gates PASS;335/335 instructions,80/80 branch directions,three fixtures/two reads each,22 host faults,28 finalizer controls. Next action B only subject to documented physical prerequisites. No real provider/hardware/flash/active control. RK01 permanently superseded; ECUFlash exactness permanently rejected; residency frozen/currentROM unknown. Evidence {ROOT}; backed-up six-file handoff {dest}/MANIFEST.json.\n'
    checkpoint=json.loads(originals['CHECKPOINT.json'])
    checkpoint.update({'schema':4,'phase':'RK02_SOFTWARE_QUALIFIED_PHYSICAL_ACQUISITION_ONLY','updated_utc':now,
      'current_task':'Completed RK02 half-duplex correction and software release qualification',
      'current_evidence':str(ROOT/'evidence/rk02'),'engineering_gates':str(ROOT/'ENGINEERING_GATES.json'),
      'qualification_summary':str(ROOT/'evidence/rk02/FINAL_QUALIFICATION.md'),
      'acquisition_tool_certificate':str(ROOT/'RELEASE_CERTIFICATE.json'),
      'acquisition_tool_software_status':'PASS','acquisition_tool_status':'CONDITIONAL_PHYSICAL_REQUIRED',
      'owned_RAM_kernel':{'version':'A2WC511R-RK02','sha256':PIN,'bytes':1808,'entry':'FFFF3004','total_RAM':['FFFF3000','FFFF3730']},
      'physical_host':{'path':str(exe),'sha256':exe_sha,'executed':False},
      'physical_provider_loaded_this_run':False,'physical_validation':False,'physical_transport_accepted':False,
      'current_vehicle_flash':'UNIDENTIFIED','production_release_allowed':False,'ECU_physical_test_candidate':False,
      'B_connection_qualified':False,'B_connection_software_eligible':True,
      'B_connection_status':'SOFTWARE_ELIGIBLE_SUBJECT_TO_PHYSICAL_PREFLIGHT',
      'next_rational_action':'B_SINGLE_HUMAN_ACQUISITION_ONLY_SUBJECT_TO_PHYSICAL_PREFLIGHT',
      'next_action':str(ROOT/'HUMAN_ACQUISITION_RK02.md'),
      'previous_frozen_checkpoint':str(dest/'CHECKPOINT.json'),'handoff_manifest':str(dest/'MANIFEST.json'),
      'RK01':'SUPERSEDED_NOT_FOR_HARDWARE','DUAL1_07_used_by_owned_tool':False,
      'prior_gate_summary_retained':checkpoint.get('gate_summary',{}),
      'gate_summary':{'PASS':list(report_refs),'PHYSICAL_REQUIRED':sorted(PHYSICAL_IDS),
        'FAIL_HISTORICAL_EXCLUDED':['ECUFLASH_UNIVERSAL_EXACT_IMAGE_ACQUISITION','DUAL1_07_STARTUP_CONTRACT','ECU_RESIDENT_BRANCH_OWNERSHIP','HISTORICAL_LOG_PRESERVATION']}})
    replacements={'CURRENT_STATE.md':current,'NEXT_ACTIONS.md':next_actions,'CHECKPOINT.json':json.dumps(checkpoint,indent=2)+'\n'}
    for name in ('DECISIONS.md','SESSION_LOG.md','RUN_CONTRACT.md'):
        replacements[name]=originals[name].decode('utf-8')+note
    updates=[]
    for name,text in replacements.items():
        p=OLD/'state'/name
        require(p.read_bytes()==originals[name],'State changed during preparation: '+name)
        with p.open('w',encoding='utf-8',newline='\n') as f:f.write(text)
        updates.append({'path':str(p),'before_sha256':hashlib.sha256(originals[name]).hexdigest(),
          'after_sha256':sha(p),'backup':str(dest/name),'backup_sha256':sha(dest/name)})
    handoff={'schema':1,'utc':now,'scope':'Only six project handoff files; no frozen artifact edits',
      'authorized_state_updates':updates,'physical_operations':False}
    js(dest/'MANIFEST.json',handoff)
    checked=verify_all(dest/'MANIFEST.json');require(checked['status']=='PASS',str(checked['failures']))
    js(dest/'PRESERVATION_AFTER_HANDOFF.json',checked)
    print(json.dumps({'status':'PASS_DOCUMENTED_BACKED_UP_HANDOFF','procedure_sha256':sha(ROOT/'HUMAN_ACQUISITION_RK02.md'),
      'physical_host_sha256':exe_sha,'handoff_manifest':str(dest/'MANIFEST.json'),'state_files':len(updates)}))

if __name__=='__main__':main()
