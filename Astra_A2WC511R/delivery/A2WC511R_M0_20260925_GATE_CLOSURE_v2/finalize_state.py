import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=Path(__file__).parent
g=json.loads((OUT/'ENGINEERING_GATES.json').read_text());p=json.loads((ROOT/'reports/local/gate_closure_package_verification.json').read_text())
now=datetime.now(timezone.utc).isoformat();session='01a0da26-addc-7fe1-84df-8c0baa8174f8'
summary=g['summary'];delivery=p['delivery'];assert p['status']=='PASS_EVIDENCE_ENVELOPE_ONLY'
def append(name,text):
    q=ROOT/'state'/name;q.write_text(q.read_text()+'\n\n'+text+'\n',encoding='utf-8')
current=f'''# A2WC511R — current M0 checkpoint

Updated {now}; session `{session}`. Continue from the existing final05 artifact. No scratch rebuild, active launch/ALS development, or physical actions occurred in this run.

**Offline gate review completed; M0 remains unapproved.** Current gate decisions: `reports/local/gate_closure/ENGINEERING_GATES.json`. New immutable evidence package: `{delivery}`. Manifest SHA256 `{p['sha256_manifest']}`. The original experimental delivery remains hash-identical across all625 entries and is included as historical `frozen_candidate` in the new package.

PASS: {', '.join(summary['PASS'])}.

FAIL: {', '.join(summary['FAIL'])}. Allocation failures mean the ownership proof was not established, not that an actual collision was demonstrated. No alternative ROM/RAM location is certified. Remaining computed CPU/context paths and OEM single-writer invariants are explicit software proof obligations. Bench observations do not erase those gaps.

PHYSICAL/BENCH REQUIRED: {', '.join(summary['PHYSICAL/BENCH REQUIRED'])}. Absolute clock, entry stalls, interrupt response, total stack occupancy, current ECU image and TCU fault/freshness behavior remain unverified. The prepared read-only collector was exercised only against virtual transport.

## Concrete results

- Final compiler CFG: exact124-byte added stack, balanced paths, preserved integer/system state and no FPU/GBR/VBR touch; full-hook conservative562 instructions,178data accesses. Scope assumes private valid stack. Task9 nominal enqueue every8 CMT1 servicecalls,160000Pphi cycles; queued activations can execute back-to-back.
- Simulator52 tests/56forms and1024stock/patch pairs PASS; wholeFF-run accounting, sentinel/watchpoint propagation, deterministic replay and nested-writer negative evidence retained.
- ROM4regression groups/22actualinstruction scenarios PASS;4 independent CFG regression tests PASS. Entire[CE754,FFAF8) and[859BC,C0000) inspected, with exact checksum-reader and exclusive-end evidence. Defined-function exploratory frontier still has94sites;43E8 has a separate17-target guarded proof. This is not a complete program theorem.
- RAM32bytes required; identified reset/DMA/shared-stack/boot-ring paths bounded;65,536byte-index and65,536timer states checked, plus actual reset/setup probes. Exclusive ownership remainsFAIL.
- Actual installed RomRaider editor/display/approval/cancel/undo/SaveAs/reload/deadline and native logger/CSV workflows completed offline. Isolated virtualSSM uses unchanged definitions and compiled snapshots. No real provider installation changed.
- Expanded image/ECUFlash history inventory finds one unique16-pageCRC historical match: AdjustedBaseTimingANDNOCLOLD.bin SHA bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2. Current flash cannot be inferred. Future oneconnection pureSSM acquisition procedure is `reports/local/gate_closure/calibration/ONE_CONNECTION_READ_ONLY_ACQUISITION.md`.
- Project70tests PASS after the local persistentHTTP transport fix. Original firmware/stagedM0 source/builds unchanged. Three qualified IDA comments plus FA84 validator name saved afterbackup; IDB ROMhash unchanged; official IDA saved/closed and helperlistener stopped.

## Frozen identities and continuation

Source `work/MerpMod_M0/MerpMod/DiagnosticM0`; build `work/builds/m0_final_05`; repeat `work/builds/m0_final_repeat_06`; patch `work/patches/m0_final_05`.
Payload SHA256 b5004baa2863bf571eb1ab014f93f0316b3500c5b154e47de2e42f904234b2ff; ELF39de4598a5149347052d5773f7bc179f3a21fde9ad4b571fe23a0bbe6e1e9eed; raw8092a20fd37f17dd351d18c805fdf195c2207af9adecca25e388146c7a9acc37; corrected6e556dd084e69af47c230a1787d229aee7b49d957d2848bb14a39a48a69042af.

Read NEXT_ACTIONS and the gate-specific reports before further work. Do not repeat completed inventory/setup or treat a fresh chat as permission to flash. The conditional prerequisite for preparing a current-calibration-ready M0 build was not met, so that procedure is withheld; acquisition preparation is separate. Timing, fuel, boost, DBW, rev-limit, MAF and transmission torque controls remain OEM behavior.
'''
(ROOT/'state/CURRENT_STATE.md').write_text(current,encoding='utf-8')
(ROOT/'state/NEXT_ACTIONS.md').write_text('''# Continue from reviewed frozen M0

1. Read reports/local/gate_closure/ENGINEERING_GATES.json, runtime/independent_review.md and interfaces/independent_collector_review.md within that evidence directory. Preserve final05; use the new package, not older historical gate labels.
2. Remaining software proof: bound unresolved CPU control/data extents for any proposed ROM/RAM span, and prove the full task9 single-writer/context invariant. Known guarded memcpy43E8, reset/DMA, checksum and timer paths have regressions already. Do not promote an FF gap or finite bench trace to exclusive ownership.
3. A human may use the prepared pure-read SSM acquisition procedure to obtain two current1MiB reads and the six pending rawTCU channels in one physical connection. Native A0 full-ROM support and silicon/provider behavior are unvalidated; abort on denial or mismatch, with no kernel/flash fallback. Keep startup/fault-state limitations explicit.
4. After software proof passes, qualify actual stack high-water, interrupt nesting, timing/clock and the smallest RAM/DMA/reset observations on bench. No autonomous hardware actions.
5. Only once all purely offline gates pass and current calibration identity is established, prepare a current-calibration-ready M0 build procedure; preserve every calibration control table and repeat affected provenance/patch/checksum/differential reviews. No launch/ALS or active output development is authorized by this checkpoint.

All reproduction scripts, raw positive search hits, reviewed GUI screenshots/CSV and scoped test reports are in the gate_closure package. Do not redo setup, inventory or all tests unless inputs change or a new concern justifies it.
''',encoding='utf-8')
append('DECISIONS.md',f'''{now} M0 gate closure: retain exact final05 bytes. ROM/RAM exclusive ownership and OEM single-writer proof remainFAIL; no relocation justified. PASS applies only to stated evidence scopes. Silicon timing/currentROM/TCU fault behavior remainPHYSICAL/BENCH REQUIRED. Actual nativeRR GUI/editor/logger and isolatedSSM validation complete; pure-read future collector prepared without executing hardware. Current-calibration build-procedure prerequisite not met. New package {delivery}.''')
append('SESSION_LOG.md',f'''{now} session{session}: completed authorized offline gate review. {p['hashed_files']} files hash-verified in new evidence package; manifest{p['sha256_manifest']}. Original625-entrypackage/stagedsource/finalbuildunchanged. Final classifications preserved inENGINEERING_GATES. IDBbackup2ec93dadb56be292a91ce6ee7060dcc4ab63d0ca457fb1138ab4b96afc766547; aftersavebd948b6eef9f955c7369a481920da5291c05b2a1dec8bff4b346addae88fd8b6. No physicalwrites/connections.70projecttests,52simulatortests,1024pairs,22ROMscenarios and4analysisregressionsPASS; nativeinterface/collectorreports provideadditionalcounts.''')
cp=json.loads((ROOT/'state/CHECKPOINT.json').read_text());cp.update(phase='M0_OFFLINE_REVIEW_COMPLETE_NOT_APPROVED',updated_utc=now,
    session_id=session,gate_closure='reports/local/gate_closure',engineering_gates='reports/local/gate_closure/ENGINEERING_GATES.json',
    gate_summary=summary,allocation='FAIL_TO_ESTABLISH',current_vehicle_flash='UNCONFIRMED_HISTORICAL_MATCH_FOUND',
    delivery=delivery,delivery_manifest_sha256=p['sha256_manifest'],delivery_hash_verification_passed=True,
    current_calibration_ready_build_procedure_prepared=False,physical_validation=False,production_release_allowed=False,
    blocking=['exclusive_ROM_ownership','exclusive_RAM_ownership','OEM_single_writer_context_invariant','physical_timing_current_calibration_TCU_semantics'],
    next='Continue precise remaining software proofs or human read-only acquisition from persisted evidence; no rebuild/setup/active feature work.')
cp['completed']=[x for x in cp.get('completed',[]) if x!='native_romraider_acceptance_except_human_gui_confirmation']
for item in ['native_romraider_editor_and_logger_offline_acceptance',
             'whole_ROM_run_and_identified_reader_review',
             'identified_RAM_reset_DMA_stack_and_timer_review',
             'exact_injected_ABI_stack_and_conditional_timing_model',
             'focused_simulator_watchpoints_propagation_and_replay',
             'expanded_calibration_inventory_and_historical_CRC_comparison',
             'sealed_read_only_collector_offline_validation',
             'evidence_linked_gate_classification_and_immutable_package']:
    if item not in cp['completed']:cp['completed'].append(item)
cp['verification_limitations']=g.get('verification_limitations',[])
(ROOT/'state/CHECKPOINT.json').write_text(json.dumps(cp,indent=2)+'\n')
sp=ROOT/'state/SYMBOLS.json';symbols=json.loads(sp.read_text());existing={s['address']:s for s in symbols['symbols']}
for address,name,kind,notes in [
 ('0x0000FA84','oem_validate_rom_checksum_range','function','Exact range predicate and7boundarycases verified; name persisted inIDB.'),
 ('0x0000F75E','oem_additive_checksum_inner_loop','instruction_fragment','Actual32-bitBE loop tested onstock/payload/endchunks. Descriptor0 reads throughFFAF4. Commentonly persisted; label descriptive.'),
 ('0x0007A79C','calibration_scan_exclusive_end_load','instruction','LoadsCE754 from7A820. Boundedrolling-sum cases andwrong-boundnegativecontrol verified. Commentonly persisted; finishingFPUhelper notverified.')]:
    row={'address':address,'name':name,'kind':kind,'confidence':'LOCAL_OPCODE_AND_SCOPED_EXECUTION_VERIFIED',
        'evidence':['reports/local/gate_closure/rom/routine_regression.json','reports/local/gate_closure/ida/metadata_changes.json'],'notes':notes,'units':None}
    if address in existing:existing[address].update(row)
    else:symbols['symbols'].append(row)
sp.write_text(json.dumps(symbols,indent=2)+'\n')
print(json.dumps({'phase':cp['phase'],'delivery':delivery,'gate_summary':summary},indent=2))
