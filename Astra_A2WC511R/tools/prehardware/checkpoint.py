"""Persist the new authorized run without rewriting the frozen comparative seal."""
import json
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
STATE=ROOT/'state'
report=json.loads((ROOT/'reports/local/prehardware/IDB_PROMOTION.json').read_text())
checkpoint=json.loads((STATE/'CHECKPOINT.json').read_text())
checkpoint.update({'phase':'PREHARDWARE_QUALIFICATION_IN_PROGRESS','updated_utc':datetime.now(timezone.utc).isoformat(),
 'authoritative_idb':report['canonical'], 'damaged_idb_preserved':report['damaged_preserved'],
 'idb_unqualified_function_queue':'reports/local/prehardware/UNQUALIFIED_FUNCTION_REVIEW_QUEUE.json',
 'current_evidence':'reports/local/prehardware', 'current_architecture':'HOST_NATIVE_A8_SUPPORTED_ECU_RESIDENCY_FROZEN',
 'physical_provider_loaded_this_run':False,'ECU_physical_test_candidate':False,
 'prehardware_progress':['Qualified IDB promoted under a new canonical filename',
 'Physical read-only backend compiled and exercised only with instrumented fake J2534',
 'Native/replay/common snapshot caller regression passed',
 'Native SSM lacks a qualified full-page checksum service; installed kernel Read remains separate conditional acquisition tier']})
(STATE/'CHECKPOINT.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
(STATE/'CURRENT_STATE.md').write_text('''# A2WC511R pre-hardware qualification in progress

The validated recovered IDB is now canonical at `C:/Dev/SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER_RECOVERED_20260926.i64`, SHA256 `55575c37d368665adcf89bd18cd81bcf6dd6cac7a615d17161514b4a0e4d1500`. The damaged original remains under its original filename/hash. Config and the new canonical launcher use the promoted path. All31 unqualified later function definitions remain withheld in `reports/local/prehardware/UNQUALIFIED_FUNCTION_REVIEW_QUEUE.json`.

The accepted M07 caller now has a side-by-side fixed-read J2534 worker in `integrations/prehardware`; only an instrumented fake provider has been loaded. Its two possible wire frames are exact BF identity and the six-address A8 request. Replay/native-virtual share the same SnapshotClient. Tests pass for malformed operations, all opcode values, native process rejection and provider failures. Electrical acceptance is still physical-only.

Reset qualification and the mandatory image validator are being integrated under `A2WC511R_Sim/preflash_boot` and `tools/prehardware`. They must retain visible conditional peripheral/startup results. ECUFlash Read is audited as TEMPORARY_RAM_READ_KERNEL, distinct from flash programming; exact installed kernel/full coverage/cleanup still require offline closure. No acquisition session is yet qualified.

ECU residency remains frozen:0owned bytes,162conditional M07 bytes, no M08 or active-control image. No sibling search, real provider load, vehicle operation or flash occurred. The prior comparative seal and its state/config snapshot are preserved; new authorized state changes have backups under `backups/prehardware_20260926`.

Current work: `reports/local/prehardware`; prior final comparative evidence: `reports/local/diaphora`. Session `01a0da26-addc-7fe1-84df-8c0baa8174f8`.
''')
for name,text in [('DECISIONS.md','Qualified recovery promoted as a new canonical file; damaged IDB and31 unqualified function definitions retained as evidence. Host-native A8 remains supported; current task may add prehardware host tests only. No real J2534 provider loaded.'),
                  ('SESSION_LOG.md','Prehardware milestone: preserved comparative seal/state, promoted exact55575c37 recovery copy, implemented x86 fixed BF/A8 broker and fake provider, common replay/native API and read-only negative controls pass. Boot/validator integration and final gates pending.')]:
    with (STATE/name).open('a',encoding='utf-8') as f:f.write('\n\n2026-09-26 — '+text+'\n')
print('Checkpoint saved')
