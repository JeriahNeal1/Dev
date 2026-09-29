"""Freeze the M0.6 checkpoint before separate M0.7 work."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,shutil
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=Path(__file__).parent
BACK=ROOT/'backups/m07_residency_20260925'
def sha(p):return sha256(p.read_bytes()).hexdigest()
assert not (OUT/'M06_FROZEN_MANIFEST.json').exists()
BACK.mkdir(exist_ok=True);shutil.copytree(ROOT/'state',BACK/'state')
idb=Path('C:/Dev/SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin.i64')
shutil.copy2(idb,BACK/idb.name)
folders=['work/M06','work/builds/m06_04','work/builds/m06_repeat_05','reports/local/m06_architecture','integrations/m06']
files={p.relative_to(ROOT).as_posix():sha(p) for f in folders for p in sorted((ROOT/f).rglob('*')) if p.is_file()}
core=Path('C:/Dev/A2WC511R_Sim/sh2e.py');shutil.copy2(core,BACK/'sh2e_75form.py')
frozen={'created_utc':datetime.now(timezone.utc).isoformat(),'files':files,'idb_sha256':sha(idb),'core_sha256':sha(core),
 'M0_manifest_sha256':sha(ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2/SHA256SUMS.json'),
 'scope':'Freeze current M06 source/build/evidence/integrations; no future mutation permitted by M07 work.'}
(OUT/'M06_FROZEN_MANIFEST.json').write_text(json.dumps(frozen,indent=2)+'\n')
status={'checkpoint':'M06_ARCHITECTURAL_RESEARCH_FROZEN_FOR_M07','raw_sha256':'11c92f72d7b3623d52956ecdc069d1c554aefe296cd653f3676d591cd5626fd4',
 'code_bytes':536,'persistent_ram_bytes':0,'max_added_stack':36,'periodic_hook':False,
 'ROM_ownership':'FAIL','strict_original_ROM_read_response_identity':'FAIL_CONCRETE_COUNTEREXAMPLE',
 'full_OEM_RX_TX_BE_and_fixed_A8':'PASS_EXPLICIT_SOFTWARE_SCI_EVENTS',
 'extended_OEM_B0_B8_wire_test':'FAIL_UNSUPPORTED_MMIO_FFFFEC0A_WORD_NO_STUB',
 'lookup_all_u16_domains':'PASS_131072_PAIRS','ABI_frames':'PASS_BOUNDED_COMPILER_PROOF',
 'silicon_timing':'PHYSICAL/BENCH REQUIRED','current_image':'PHYSICAL/BENCH REQUIRED',
 'A0_full_image_attestation':'FAIL_WITHDRAWN_MASKED_READ_ADMISSION',
 'host_A8_service':'PREFERRED_BY_USER_M07','new_m07_objective':'Provable executable-function tail residency; raw-only discriminated ECU protocol; durable host observations; offline ECUFlashRead/kernel audit',
 'frozen_manifest_sha256':sha(OUT/'M06_FROZEN_MANIFEST.json'),'physical_actions':False,'release_allowed':False}
(OUT/'M06_FROZEN_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
state=ROOT/'state';stamp=datetime.now(timezone.utc).isoformat()
d=json.loads((state/'CHECKPOINT.json').read_text());d.update(phase='M07_PROVABLE_ROM_RESIDENCY_IN_PROGRESS',updated_utc=stamp,
 current_architecture='Preferred host nativeA8; separate raw-only ECU M07 research',current_source='work/M07',current_build=None,
 current_evidence='reports/local/m07_residency',m06_frozen_manifest='reports/local/m07_residency/M06_FROZEN_MANIFEST.json',
 current_calibration_ready_build_procedure_prepared=False,old_M0_frozen=True,old_M06_frozen=True,
 next='Durable host tool, raw-only page/version discrimination and executable-object compression/ownership proofs; offline ECUFlashRead analysis')
(state/'CHECKPOINT.json').write_text(json.dumps(d,indent=2)+'\n')
(state/'CURRENT_STATE.md').write_text('''# A2WC511R — M0.7 provable ROM residency in progress

The active user objective is M0.7, not more finite tests of the compacted setter table. Preferred diagnostics is the host-only nativeA8 service. Frozen M0 and current M0.6 source/build/reports/integration are preserved by reports/local/m07_residency/M06_FROZEN_MANIFEST.json. The M0.6 freeze status is alongside it. No physical acquisition, flashing or active control development is authorized.

M0.6 removed32-byte persistent RAM, task9 publication and the new single-writer lifecycle. Its536-byte payload and36-byte maximum added frame remain research only. Table lookup equivalence passed both65536-index domains, but unknown ROM consumers remain and nativeROM readback sees changed bytes. Actual OEM RX/echo/parser/TX replay passed bothBEpages and nativeA8pages with supplied SCIevents; extendedB0/B8 replay stopped on unsupportedEC0A MMIO. No guessed peripheral completion.

The old A0 full1MiB acquisition procedure is WITHDRAWN. Native read masks returnFF for boot/vector and checksum-tail spans. Two equal masked views passed the unchanged collector, proving its image-attestation claim invalid. See reports/local/m06_architecture/protocol/ACQUISITION_COVERAGE_ADVISORY.md. Six raw TCU channels remain sufficient.

M0.7 work lives separately in reports/local/m07_residency, integrations/m07 and work/M07. Root owns protocol/ownership synthesis and officialIDA; simulator agent owns bounded executable-equivalence tools/candidates; interface agent owns durable timestamped host observations; build_port agent audits installedECUFlashRead/kernel offline. No FFhole or compacted settertable is the preferred residency strategy. Each reclaimed tail requires explicit entry/reference/equivalence evidence, unknownsFAIL. Physical acquisition remains deferred.
''')
(state/'NEXT_ACTIONS.md').write_text('''# Continue M0.7

1. Preserve M06_FROZEN_MANIFEST and originalM0 manifest. Do not modify those source/build/report trees.
2. Finish supported nativeA8 host observation CLI/JSONL with six raw values, rawwire, UTC/monotonic stamps and host reason predicates, using isolated virtual/native infrastructure only.
3. Minimize separate ECU raw-only protocol: page/version-specific response discrimination and existingTX-state check to skip discardedrefill; no persistentnewstate.
4. Enumerate/rewrite bounded OEM executable functions. Prove entries/inbounds/tail exclusion, differential ABI/state/writes/calls, and exact reclaimable spans. Unknown/unsupported pathsFAIL.
5. Audit actual installedECUFlashRead/kernel offline and distinguish temporaryRAMkernel writes fromflashwrites; no physical launch/provideraccess.
6. Regenerate M07 gates, ownership fragment manifest, finalhandoff/state. No active launch/ALS/engine/transmissioncontrol.
''')
with (state/'SESSION_LOG.md').open('a') as f:f.write(f'\n## {stamp} M07 objective accepted\nCurrentM06 frozen by {status["frozen_manifest_sha256"]}. HostnativeA8 preferred. A0fullimageattestation withdrawn. Separate executable-replacement residency andECUFlashRead audit begun; nophysicalactions.\n')
print(json.dumps({'status':'M06_FROZEN_M07_STARTED','files':len(files),'manifest_sha256':status['frozen_manifest_sha256']}))
