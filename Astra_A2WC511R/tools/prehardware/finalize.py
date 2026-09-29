"""Seal prehardware evidence and state. Never promotes any ECU image."""
from pathlib import Path
import hashlib
import json
from datetime import datetime,timezone
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
OUT=ROOT/'reports/local/prehardware'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):Path(p).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def evidence(rel):
    p=OUT/rel
    return {'path':str(p),'sha256':sha(p)}

def main():
    if (OUT/'DELIVERABLE_MANIFEST.json').exists():raise SystemExit('Already sealed; review before resealing')
    backend=load(OUT/'READ_ONLY_BACKEND_TESTS.json')
    boot=load(OUT/'boot/BOOT_CONTRACT.json')
    validator=load(OUT/'validator/acceptance_01/ACCEPTANCE.json')
    negative=load(OUT/'validator/ADVERSARIAL_FINAL.json')
    preservation=load(OUT/'PRESERVATION.json')
    promotion=load(OUT/'IDB_PROMOTION.json')
    assert backend['status']==validator['status']==negative['status']=='PASS'
    assert boot['status']=='CONDITIONAL' and boot['regression_checks_passed']==64
    assert [x['status'] for x in validator['runs']]==['CONDITIONAL','FAIL','FAIL','CONDITIONAL']
    previous=load(ROOT/'reports/local/diaphora/ENGINEERING_GATES.json')
    gates=previous['gates']
    for gate in gates:gate['carried_from_frozen_comparative_review']=True
    def put(id,status,scope,reason,files,remaining=None,depends=()):
        row={'id':id,'status':status,'scope':scope,'reason':reason,'evidence':[evidence(f) for f in files],
             'remaining':remaining,'depends_on':list(depends),'carried_from_frozen_comparative_review':False}
        for i,item in enumerate(gates):
            if item['id']==id:gates[i]=row;break
        else:gates.append(row)
    put('LIVE_IDA_METADATA_PRESERVATION','PASS','New canonical qualified recovery',
        'Exact qualified recovery promoted under a new filename; damaged original preserved.31unqualified functions remain withheld.',
        ['IDB_PROMOTION.json','UNQUALIFIED_FUNCTION_REVIEW_QUEUE.json'])
    put('LIVE_HOST_TRANSPORT_IMPLEMENTATION','PASS','Software/fake-provider acceptance only',
        'x86 J2534 worker implements only immutable BF and fixed six-address A8; common M07 client,16test groups and independent ABI/cleanup review pass. Real provider never loaded.',
        ['READ_ONLY_BACKEND_TESTS.json','READ_ONLY_BACKEND_REVIEW.md','BROKER_BUILD_REPRODUCIBILITY.json'],
        'Physical electrical/echo/driver behavior remains unverified.')
    put('RESET_BOOT_HARNESS_IMPLEMENTATION','PASS','Accurate finite reset prefix with visible limitations',
        'Actual1MiB stock reset executes57658instructions/801PCs;64regressions pass. Full writes/control/terminal-state differential has no allowlist exceptions.',
        ['boot/BOOT_CONTRACT.json','BOOT_MODEL_REVIEW.md'])
    put('COMPLETE_RESET_TO_SSM_QUALIFICATION','CONDITIONAL','Model frontier, not physical timing success',
        'Stops before SYSCR2=3C88 at4B4C. Main RAM init, actual ISR execution, sensor recovery and SCI/SSM readiness remain unreached.',
        ['boot/BOOT_CONTRACT.json'],
        'Model exact clock transition and subsequently reached peripheral contracts; no synthetic zero/default success.')
    put('MANDATORY_PREFLASH_VALIDATOR','PASS','Tool acceptance, not image approval',
        '42adversarial groups; exact registry/source/build associations, inverse/calibration/branch checks and live boot differential. Clean-process verdict hashes match. StockCONDITIONAL; bothM07FAILownership.',
        ['validator/acceptance_01/ACCEPTANCE.json','validator/ADVERSARIAL_FINAL.json','validator/VALIDATOR_REVIEW.md'])
    put('NATIVE_FULL_PAGE_ATTESTATION','FAIL','No qualified native external full-page vector',
        'Ordinary SSM six-command dispatcher and BF/9F producers contain no exposed pageCRC. Historical16pageCRC is post-kernel and identifies a past image only.',
        ['acquisition/NATIVE_SSM_ATTESTATION.json','acquisition/ACQUISITION_REVIEW.md'],
        'Use separately qualified TEMPORARY_RAM_READ_KERNEL acquisition; do not revive masked A0 full-image procedure.')
    for id,reason in [
        ('ECUFLASH_INSTALLED_KERNEL_IDENTITY','Exact installed4660-byte DUAL1.07 kernel and startup RAM/stack/peripheral effects are not recovered.'),
        ('ECUFLASH_EXACT_READ_COVERAGE','434176bytes in two historical gaps lack actual payload or qualified skip/attestation semantics.'),
        ('ECUFLASH_READ_FLASH_WRITE_EXCLUSION','Installed initialization/Read/error paths are not completely shown to exclude flash enable/erase/commit.'),
        ('ECUFLASH_EXIT_RESET_CLEANUP','Exact success/abort exit and renewed OEM execution contract remains unqualified.')]:
        put(id,'FAIL','Offline software evidence still required',reason,
            ['acquisition/INSTALLED_READ_QUALIFICATION.json','acquisition/ACQUISITION_REVIEW.md'],reason)
    put('RAM_READ_KERNEL_TIER_DISTINCTION','PASS','Acquisition architecture',
        'Temporary RAM upload/takeover is explicitly distinguished from flash erase/program; real Read is a reasonable method to qualify, not yet approved.',
        ['acquisition/INSTALLED_READ_QUALIFICATION.json'])
    put('SINGLE_ACQUISITION_CONNECTION','FAIL','B withheld; next action A',
        'Exact BF/A8 command and one-connection order are prepared. Current Read contract cannot yet support complete image acquisition and qualified return to OEM.',
        ['ACQUISITION_SESSION.md','acquisition/RUN_STATUS.json'],
        'Close installed kernel/Read/coverage/exit obligations offline before releasing B.',
        ['LIVE_HOST_TRANSPORT_IMPLEMENTATION','ECUFLASH_INSTALLED_KERNEL_IDENTITY','ECUFLASH_EXACT_READ_COVERAGE','ECUFLASH_READ_FLASH_WRITE_EXCLUSION','ECUFLASH_EXIT_RESET_CLEANUP'])
    put('MINIMUM_WRITE_ARCHITECTURE_CONTRACT','PASS','Design only; no resident build',
        'At most one outputs-disabled near-final architecture write before a separately reviewed active write. Compile/link/runtime permission closure and evidence prerequisites specified; no spare ECU assumed.',
        ['MINIMUM_WRITE_ARCHITECTURE.md'],
        'Executable ownership/context remains FAIL; this plan does not authorize a hook-only experiment or an unqualified image.')
    put('FROZEN_ARTIFACT_PRESERVATION',preservation['status'],'Exact-byte preservation audit',
        'Pinned ROM/source/core/deliveries/Diaphora and old state backups checked; see mismatches for any cache incident exception.',
        ['PRESERVATION.json','REPAIR_LOG.md'],None if preservation['status']=='PASS' else preservation['mismatches'])
    summary={s:[g['id'] for g in gates if g['status']==s] for s in ['PASS','CONDITIONAL','FAIL','PHYSICAL/BENCH REQUIRED']}
    gate_report={'schema':4,'architecture':'HOST_NATIVE_A8_SUPPORTED_ECU_RESIDENCY_FROZEN',
        'next_rational_action':'A_OFFLINE_INSTALLED_READ_QUALIFICATION','B_connection_qualified':False,
        'release_allowed':False,'ECU_physical_test_candidate':False,'provably_owned_ROM_bytes':0,
        'conditional_M07_ROM_bytes':162,'new_ECU_image_built':False,'physical_actions_performed':False,
        'real_provider_loaded':False,'gates':gates,'summary':summary}
    write(OUT/'ENGINEERING_GATES.json',gate_report)
    decision={'decision':'A_ANOTHER_OFFLINE_SOFTWARE_TASK','B_connection_qualified':False,
        'next_task':'Qualify exact installed sti05/DUAL1.07 Read: kernel identity/effects, flash-exclusion, full coverage and OEM-restoration.',
        'parallel_preflash_task':'Resolve documented clock transition at4B4C, then only actually reached initialization/interrupt/SCI paths.',
        'no_spare_ECU_assumed':True,'normal_flash_budget':{'acquisition':0,'outputs_disabled_architecture_before_active':1},
        'host_supported_path':'integrations/prehardware (frozen M07 API reused)',
        'residency_search_resumed':False,'active_control_enabled':False,
        'current_ROM_identified':False,'evidence':[evidence('ENGINEERING_GATES.json'),evidence('ACQUISITION_SESSION.md')]}
    write(OUT/'END_STATE_DECISION.json',decision)
    now=datetime.now(timezone.utc).isoformat()
    cache_note=('All pinned preservation checks pass.' if preservation['status']=='PASS' else
        'Preservation exception: a review import regenerated one frozen protocol.pyc. ROM/source/core/deliveries remain unchanged; exact-cache recovery and mismatches are documented.')
    report=f'''# Pre-hardware qualification: A — continue offline

The next rational action is the exact installed ECUFlash Read qualification, not
a vehicle connection. The future combined acquisition order is prepared but
withheld. No real provider was loaded, physical operation performed, ECU image
built or flashed, or active intervention enabled.

| Deliverable | Result | Evidence |
|---|---|---|
| Qualified authoritative IDB | PASS; new canonical filename,31functions withheld | [promotion](IDB_PROMOTION.json), [queue](UNQUALIFIED_FUNCTION_REVIEW_QUEUE.json) |
| Fixed-read J2534 host backend | PASS software/fake; physical acceptance pending | [16regression groups](READ_ONLY_BACKEND_TESTS.json), [independent review](READ_ONLY_BACKEND_REVIEW.md) |
| Broker fresh-directory reproduction | PASS, identical x86 binaries, spaces supported | [hash comparison](BROKER_BUILD_REPRODUCIBILITY.json) |
| Actual reset harness |64checks PASS;57658instructions,801PCs | [boot contract](boot/BOOT_CONTRACT.json), [root review](BOOT_MODEL_REVIEW.md) |
| Complete boot/SSM readiness | CONDITIONAL at4B4C clock change; later ISR/sensor/SCI unreached | [boot audit](boot/BOOT_AUDIT.md) |
| Mandatory validator |42adversarial groups PASS; deterministic clean-process verdicts | [acceptance](validator/acceptance_01/ACCEPTANCE.json), [review/command](validator/VALIDATOR_REVIEW.md) |
| Stock / frozen M07 decisions | Stock CONDITIONAL; M07 one-/two-page FAIL ownership | [validation runs](validator/acceptance_01/ACCEPTANCE.json) |
| Native full-page CRC attestation | Not qualified; historicalCRC is post-kernel | [acquisition audit](acquisition/ACQUISITION_REVIEW.md) |
| Single acquisition session | Prepared, B withheld | [command/order](ACQUISITION_SESSION.md) |
| Minimum-write firmware strategy | Design only; first-image outputs structurally off | [architecture contract](MINIMUM_WRITE_ARCHITECTURE.md) |

Canonical IDB: `{promotion['canonical']['path']}`, SHA256
`{promotion['canonical']['sha256']}`. The damaged original remains untouched.
Config and `tools/prehardware/Open-CanonicalIDA.ps1` select the promoted file.
No unqualified metadata was imported.

The host worker can construct only BF identity and one fixed six-address A8
frame. Caller bytes/addresses/opcodes cannot be submitted to J2534. Exact echo,
length, checksum and identity checks apply; all faults are terminal. Timestamps,
raw values/frames and host reason predicates survive across replay,
native-virtual and J2534 backends. The actual OpenPort provider remains unloaded.
See [host tool usage/limits](../../../integrations/prehardware/README.md).

The remaining acquisition blockers are the exact installed4660-byte DUAL1.07
kernel/effects, Read-path exclusion of flash operations,434176unattested bytes
in two historical coverage gaps, and success/abort return to OEM operation.
Temporary RAM upload is a distinct tier, not equated with flash writing. The37
local ROM catalog and old16pageCRC vector do not identify the current ECU image.

For future firmware qualification, the reset harness still stops at the
documented clock transition and has no complete SSM/interrupt/sensor result.
Its synthetic16cycles/instruction are not silicon timing. Zero ROM bytes have
become independently owned; the resident branch stays frozen. Current-image
identity plus bench timing alone does not remove that architectural blocker.

{cache_note} [Preservation](PRESERVATION.json) and [repair journal](REPAIR_LOG.md)
record the exact outcome. Prior sealed state/config are retained in
`backups/prehardware_20260926`; the frozen comparative reports are unchanged.

All gate classifications: [ENGINEERING_GATES.json](ENGINEERING_GATES.json).
Decision: [END_STATE_DECISION.json](END_STATE_DECISION.json).
'''
    (OUT/'REPORT.md').write_text(report,encoding='utf-8')
    state={'schema':3,'phase':'PREHARDWARE_QUALIFICATION_COMPLETE_WITH_OPEN_GATES','updated_utc':now,
        'session_id':'01a0da26-addc-7fe1-84df-8c0baa8174f8','current_task':'Pre-hardware qualification and minimum-write vehicle development',
        'current_evidence':'reports/local/prehardware','engineering_gates':'reports/local/prehardware/ENGINEERING_GATES.json',
        'current_architecture':gate_report['architecture'],'ECU_resident_branch_frozen':True,
        'authoritative_idb':promotion['canonical'],'authoritative_idb_reopen_status':'PASS_QUALIFIED_NATIVE_SAVE_REOPEN_RECOVERY_PROMOTED_EXACT_COPY',
        'damaged_idb_preserved':promotion['damaged_preserved'],'authoritative_IDB_promoted_new_filename':True,
        'original_damaged_IDB_overwritten':False,'unqualified_function_queue':'reports/local/prehardware/UNQUALIFIED_FUNCTION_REVIEW_QUEUE.json',
        'physical_provider_loaded_this_run':False,'physical_validation':False,'production_release_allowed':False,
        'ECU_physical_test_candidate':False,'new_ECU_image_built':False,'M08_built':False,
        'host_native_A8_supported':True,'physical_backend_software_qualified':True,'physical_transport_accepted':False,
        'current_vehicle_flash':'UNIDENTIFIED','B_connection_qualified':False,'next_rational_action':decision['decision'],
        'next_action':decision['next_task'],'boot_frontier':'4B4C SYSCR2=3C88; complete SSM readiness CONDITIONAL',
        'provably_owned_ROM_bytes':0,'conditional_M07_ROM_bytes':162,'gate_summary':summary,
        'previous_frozen_checkpoint':'backups/prehardware_20260926/state/CHECKPOINT.json',
        'frozen_preservation_status':preservation['status'],'frozen_preservation_mismatches':preservation['mismatches']}
    write(ROOT/'state/CHECKPOINT.json',state)
    (ROOT/'state/CURRENT_STATE.md').write_text(f'''# A2WC511R pre-hardware qualification checkpoint

Decision **A: another offline software task**. Qualify exact installed sti05/DUAL1.07 Read/kernel/coverage/exit before releasing the single acquisition-only connection. No real provider, physical acquisition, flash or active control was executed.

Canonical IDB is `{promotion['canonical']['path']}`, SHA256 `{promotion['canonical']['sha256']}`. The damaged original remains at its old filename/hash.31unqualified function definitions remain withheld. Config/default launcher now select the recovered authority.

The new `integrations/prehardware` backend reuses the frozen M07 SnapshotClient across replay/native-virtual and fixed BF/A8 J2534.16groups, independent ABI/cleanup checks and clean binary reproduction PASS using only a fake provider. Real electrical acceptance remains physical-only.

The actual1MiB reset harness reaches57658instructions/801PCs;64checks PASS. Full register/write/control comparison matches the frozen M07 prefix. Complete boot/SSM remains CONDITIONAL at4B4C's clock change. The mandatory `tools/prehardware/validator.py` has42adversarial groups and deterministic clean-process acceptance: stockCONDITIONAL, bothM07FAILownership. No future ECU image is vehicle-testable without its exact validator report and all applicable gates.

Read `reports/local/prehardware/REPORT.md`, `ENGINEERING_GATES.json`, `END_STATE_DECISION.json`, `ACQUISITION_SESSION.md` and `MINIMUM_WRITE_ARCHITECTURE.md`. Residency is frozen:0owned bytes/162conditional; no new sibling/residency search or M08 build. Current ROM remains unidentified. Temporary Read RAM upload is distinguished from erase/program, but exactkernel/effects,434176coverage-gap bytes, flash-exclusion and OEM-restoration remain offline FAIL.

{cache_note} Prior sealed state/config backups are under `backups/prehardware_20260926`.
Session `01a0da26-addc-7fe1-84df-8c0baa8174f8`.
''',encoding='utf-8')
    (ROOT/'state/NEXT_ACTIONS.md').write_text('''# Next actions — A, offline software

1. Close the exact installed sti05/DUAL1.07 Read contract: recover/hash the kernel and bound startup/error/exit RAM/peripheral effects, exclude erase/program paths, prove full1MiB coverage including both historical gaps, and qualify OEM restoration. See reports/local/prehardware/acquisition/ACQUISITION_REVIEW.md. Do not use a different source/version as an exact-artifact substitute.
2. For future pre-flash qualification, continue only the actual4B4C clock-transition/peripheral path. No generic CPU expansion, synthetic SSM startup PASS or silicon timing inference.
3. Release the prepared single acquisition-only connection only after Read qualification. Its exact BF/A8 command and order are in reports/local/prehardware/ACQUISITION_SESSION.md. No Write/TestWrite, no spare ECU assumed.
4. Keep host-native A8 supported. Resident work is frozen until independently owned objects and execution-context proof exist; do not restart finite sibling/anonymous-ROM searches. No launch/ALS or active-control tuning.

Use the new canonical IDB from config/host_paths.json. Keep31unqualified function definitions in review. Preserve all prior frozen reports and candidate images. Run the mandatory image validator for every proposed future ECU image; currentM07FAIL cannot be bypassed by a successful boot prefix.
''',encoding='utf-8')
    symbols=load(ROOT/'state/SYMBOLS.json')
    symbols['comparative_evidence'].update(authoritative_IDB=promotion['canonical']['path'],candidate_not_promoted=False)
    symbols['prehardware_evidence']={'IDB_promotion':'reports/local/prehardware/IDB_PROMOTION.json',
        'unqualified_function_queue':'reports/local/prehardware/UNQUALIFIED_FUNCTION_REVIEW_QUEUE.json',
        'new_persisted_names_or_function_boundaries':0,'ordinary_SSM_identity_evidence':'reports/local/prehardware/acquisition/NATIVE_SSM_ATTESTATION.json',
        'BF_response_length':62,'BF_ECU_ID_frame_offsets':[8,13],'ROM_residency_status':'FAIL_FROZEN'}
    write(ROOT/'state/SYMBOLS.json',symbols)
    for name in ('DECISIONS.md','SESSION_LOG.md'):
        with (ROOT/'state'/name).open('a',encoding='utf-8') as f:
            f.write('\n\n2026-09-26 — Prehardware qualification complete with open gates. DecisionA: exact installedRead software qualification before onecombined acquisition. IDB promoted undernewfilename; BF/A8 fixed-read backend16groups/boot64checks/validator42groups accepted offline. StockCONDITIONAL/M07FAIL; no physicalprovider/flash/activecontrol. '+cache_note+' See reports/local/prehardware/REPORT.md.\n')
    files={}
    for folder in [OUT,ROOT/'tools/prehardware',ROOT/'integrations/prehardware',ROOT/'state',ROOT/'config',Path(r'C:\Dev\A2WC511R_Sim\preflash_boot')]:
        for p in sorted(folder.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p!=OUT/'DELIVERABLE_MANIFEST.json':files[str(p)]=sha(p)
    manifest={'schema':1,'status':'SEALED_PREHARDWARE_REVIEW_NOT_A_VEHICLE_IMAGE',
        'decision':'A_OFFLINE_SOFTWARE','physical_actions':False,'files':files,
        'prior_comparative_manifest':{'path':str(ROOT/'reports/local/diaphora/DELIVERABLE_MANIFEST.json'),'sha256':sha(ROOT/'reports/local/diaphora/DELIVERABLE_MANIFEST.json')},
        'frozen_preservation_status':preservation['status']}
    write(OUT/'DELIVERABLE_MANIFEST.json',manifest)
    print(json.dumps({'decision':'A','manifest_sha256':sha(OUT/'DELIVERABLE_MANIFEST.json'),'files':len(files),'gate_counts':{k:len(v) for k,v in summary.items()},'preservation':preservation['status']}))

if __name__=='__main__':main()
