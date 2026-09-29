"""Publish the evidence decision and continuation state without touching ECU artifacts."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from collections import Counter
import json,sqlite3
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=ROOT/'reports/local/diaphora';WORK=ROOT/'work/diaphora'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def h(p):return sha256(Path(p).read_bytes()).hexdigest()
def evidence(rel):
    p=OUT/rel;assert p.is_file();return {'path':str(p),'sha256':h(p)}
def write(name,data):
    p=OUT/name;assert not p.exists(),p;p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def main():
    now=datetime.now(timezone.utc).isoformat()
    audit=read(OUT/'comparison_audit/COMPARISON_SUMMARY.json');assert audit['status']=='PASS'
    peer=read(OUT/'correspondence_independent_review/FINAL_CORRESPONDENCE_AUDIT.json');assert peer['status'].startswith('PASS')
    preservation=read(OUT/'PRESERVATION.json');assert preservation['status']=='PASS'
    deterministic=read(OUT/'correspondence_final_01/DETERMINISM.json');assert deterministic['status']=='PASS'
    recovery=read(OUT/'idb_reopen_audit/RECOVERY_CANDIDATE_HEALTH.json')
    range_review=read(OUT/'range_ownership_review/RANGE_OWNERSHIP.json');assert range_review['gate']=='FAIL'
    mapping=read(OUT/'merpmod_mapping/MERPMOD_MAPPING.json')
    inputs=['merpmod_mapping/REVIEWED_MATCHES.json','merpmod_mapping/MERPMOD_MAPPING.json','range_ownership_review/RANGE_OWNERSHIP.json',
            'range_ownership_review/SMALLER_CANDIDATE_FACTS.json','idb_reopen_audit/CURRENT_METADATA_FROM_FORENSIC_COPY.json']
    write('correspondence_final_01/GENERATOR_INPUTS.json',{'evidence':[evidence(x) for x in inputs],
          'generator':{'path':str(ROOT/'tools/diaphora/build_correspondence.py'),'sha256':h(ROOT/'tools/diaphora/build_correspondence.py')},
          'all_effective_review_overrides_crosschecked_against_final_rows':True,'closed_exports':'SUMMARY.json',
          'scoped_simulator_evidence':'C:/Dev/A2WC511R_Sim/diaphora_crossrom/runs/20260926T025326.453332Z/crossrom_regression.json'})
    exports={}
    for p in sorted((WORK/'exports').glob('*.identity.json')):
        item=read(p)
        for v in item.values():assert h(v['path'])==v['sha256']
        exports[p.stem.removesuffix('.identity')]=item
    write('EXPORT_INDEX.json',{'exports':exports,'scope':'All completed full-ROM native exports; strict function-set checks retained beside each export. No decompiler/microcode/model.'})
    write('RESULT_INDEX.json',{'selected':audit['selected_comparisons'],'scope':'These are the final accepted results. Earlier superseded report files remain evidence, not current correspondence inputs.'})
    review_evidence=[evidence(x) for x in ['correspondence_final_01/DETERMINISM.json','comparison_audit/COMPARISON_SUMMARY.json',
        'correspondence_independent_review/FINAL_CORRESPONDENCE_AUDIT.json','merpmod_mapping/MERPMOD_MAPPING.json',
        'range_ownership_review/RANGE_OWNERSHIP.json','range_ownership_review/SMALLER_CANDIDATE_FACTS.json',
        'idb_reopen_audit/RECOVERY_CANDIDATE_HEALTH.json','PRESERVATION.json']]
    decision={'schema':1,'created_utc':now,'decision':'FREEZE_ECU_RESIDENT_BRANCH_RETAIN_HOST_NATIVE_A8',
              'M08_payload_designed_or_built':False,'physical_actions':False,'active_control_changes':False,
              'provably_owned_bytes':0,'conditional_M07_bytes':162,'smallest_existing_M07_raw_payload_bytes':100,
              'current_ROM_identification_and_bench_timing_alone_sufficient':False,
              'candidates':[{'range':[0x42a4,0x430a],'conditional_bytes':102,'owned_bytes':0,'status':'FAIL','reason':'Complete admissible computed-entry, internal-consumer and extra-stack/context contracts remain unclosed; no smaller division found in existing acquired images.'},
                            {'range':[0x14770,0x147ac],'conditional_bytes':60,'owned_bytes':0,'status':'FAIL','reason':'Range family has95 reachable instructions in all10 images; smaller span is pool layout. Arbitrary interior and computed entry domains not excluded.'},
                            {'source':0x195e8,'sibling':0x17dfc,'owned_bytes':0,'status':'FAIL','reason':'Full-entry simulator counterexample4 vs0; sibling drops behavior.'},
                            {'source':[0x31fc,0x3214],'owned_bytes':0,'status':'FAIL','reason':'Apparent savings aggregate separated/shared interrupt chunks and changed callees/SR/MMIO behavior.'}],
              'remaining_software_contracts':[
                  {'site':0x42,'domain':'JMP@R4 after boot target atFFFFBFA0 is assembled from four input bytes','result':'Unconstrained32-bit domain includes both tails. Normal-operating-mode exclusion is not proved.'},
                  {'site':0xde3e,'domain':'Callback pointer at descriptor+4; descriptor selected via1023C +4*u8(R4), then8*u16(R5)','result':'33 bounded literal-caller slices are insufficient to close all selector/index/descriptor provenance and transitive dispatch.'},
                  {'site':0x3980,'domain':'RTOS pointer source includesROM[4AA4]=40','result':'Direct tail exclusion does not exclude downstream R4 trampoline targets.'},
                  {'domain':'Internal code-as-data and calculated reads, DMA/context restore','result':'Unknown ranges remain universal; broad analysis unfinished.'},
                  {'domain':'Saved-PC/interrupt transparency and private division stack word atinitialSP-12..initialSP-8','result':'No global execution-context or hardware margin proof.'}],
              'reopen_criterion':'A new independently checkable admissible-entry/data-consumer/context contract or exclusive executable object, not more finite ROM-family tests. Preserve OEM validation and request behavior.',
              'supported_path':'integrations/m07 host-native A8 observation service; six raw OEM observations, host predicates, UTC/monotonic timestamps, virtual/native RomRaider integration; physical backend remains unqualified.',
              'future_passive_fields_added':0,'A0_full_image_attestation':'WITHDRAWN','evidence':review_evidence}
    write('ARCHITECTURAL_DECISION.json',decision)
    old=read(ROOT/'reports/local/m07_residency/ENGINEERING_GATES.json')
    gates=[]
    for item in old['gates']:
        item=dict(item);item['carried_from_frozen_M07']=True
        for e in item.get('evidence',[]):
            p=Path(e['path'])
            if not p.is_absolute():e['path']=str(ROOT/'reports/local/m07_residency'/p)
        if item['id']=='LIVE_IDA_METADATA_PRESERVATION':
            item['status']='FAIL';item['reason']='Historical save was not sufficient: current authoritativeIDB lacks21RootNode records. Original preserved; qualified healthy recovery candidate is separatelyPASS and not promoted.'
            item['evidence']=[evidence('idb_reopen_audit/RECOVERY_CANDIDATE_HEALTH.json')]
            item['remaining']='Replacement is outside this completed candidate/review action; no silent overwrite.'
        gates.append(item)
    additions=[('DIAPHORA_NATIVE_STRUCTURAL_PIPELINE','PASS','Accepted native/scripted export and real result chooser; scopedABI/vendor. No installation/probe/self-test rerun.','setup/matcher_partition_repair/MANIFEST.json'),
               ('COMPLETE_RESULT_REPORTING','PASS','Matched/unmatched exact partitions on both sides; correctedlabels and discarded-cache omission.','comparison_audit/COMPARISON_SUMMARY.json'),
               ('DETERMINISTIC_CORRESPONDENCE','PASS','12431rows,12comparisons, exactSQLite/JSONL clean-process hashes; independent audit.','correspondence_final_01/DETERMINISM.json'),
               ('METADATA_IMPORT_REVIEW','PASS','16queuedproposalsheld; no automaticauthoritativeimport. Qualifiedhistoricalcomments replayedonly toseparaterecoverycandidate.','correspondence_final_01/METADATA_IMPORT_REVIEW_QUEUE.json'),
               ('ARCHIVED_MERPMOD_STRUCTURAL_RECONSTRUCTION','PASS','Sevenoperations; fourliteralhooks; nineinsertedfunctions; compiledRAMspan established; limitedfunctionidentities independentlychecked.','merpmod_mapping/MERPMOD_MAPPING.json'),
               ('RANGE_FAMILY_OWNERSHIP_REVIEW','PASS','Semantic/densityquestionresolved andtransplantproposals rejected where unsupported; ownership itself remainsFAIL.','range_ownership_review/RANGE_OWNERSHIP.json'),
               ('QUALIFIED_IDB_RECOVERY_CANDIDATE','PASS','913functions,70names,61commentaddresses; threequalifiedcommentsreplayed. Native save/close/reopen andzero-corruptionvalidationPASS;31unqualifiedlaterfunctiondefinitionswithheld.','idb_reopen_audit/RECOVERY_CANDIDATE_HEALTH.json'),
               ('FROZEN_ARTIFACT_PRESERVATION','PASS','M0/M06/M07,originalDiaphora,damagedauthorityandstrictsimulatorcoreunchanged.','PRESERVATION.json'),
               ('M08_RESIDENCY_AND_EXECUTION_CONTEXT','FAIL','Zeroownedbytes; neither100-byteexistingpayload nor anewresidentpayload has sufficientclosedresidency/context.','ARCHITECTURAL_DECISION.json')]
    for ident,status,reason,path in additions:gates.append({'id':ident,'status':status,'reason':reason,'evidence':[evidence(path)]})
    output={'schema':3,'created_utc':now,'architecture':decision['decision'],'release_allowed':False,'ECU_physical_test_candidate':False,
            'current_ROM_plus_bench_only_sufficient':False,'all_purely_offline_ECU_gates_pass':False,'current_comparative_task_completed':True,
            'provably_owned_bytes':0,'conditional_bytes':162,'physical_actions_performed':False,'M08_build':None,'gates':gates,'counts':dict(Counter(g['status'] for g in gates))}
    write('ENGINEERING_GATES.json',output)
    report='''# A2WC511R comparative decision

**Freeze the ECU-resident branch. Keep host-native A8 observations as the supported path.** The comparative work is complete; it establishes0 owned resident bytes. No M0.8 payload was designed or built. Current-ROM identification and bench timing alone cannot close the remaining software contracts.

The final correspondence contains12,431 rows across12 comparisons, with16 metadata proposals held for review. Both result sides exactly partition their exported function inventories. The SQLite and JSONL files reproduce byte-for-byte in clean generator processes; repaired matching also has a clean-process deterministic result. Eight narrowly scoped division identities reuse the existing evidence; no further division search was performed.

The archived A2WC522S MerpMod pair changes4,280 bytes in seven operations: two identifiers, four call-pointer literals and4,317 bytes at[E1000,E20DD). None of the stock-defined instruction words changes. Nine inserted functions account for1,410 recognized instruction bytes. Other payload bytes are separately inventoried; absence of disassembly does not establish data ownership. The compiled archive clears[FFFF73B0,FFFF7428),120 bytes, unlike the current510S source'sFFFF7400 base. Historical use of these locations proves neither ROM nor RAM ownership on511R.

Six510S-to511R structural identities have independently checked chunks/calls/literals. External MAF/rev-limit calibration pointers differ, so identical instructions do not imply interchangeable behavior. Three misleading matcher proposals were rejected, including archive continuation31912→511R31814; the actual six-byte continuation maps to3180E. The archived control routine is called from the MAF path, unlike the current source's separate hook strategy. None was enabled or transplanted.

All ten recovered range bodies contain95 reachable instructions/190 bytes. Forester's232-byte entry-to-return span versus318 is a pool-layout change. The strongest other smaller-body proposal,195E8→17DFC, removes behavior: full-entry execution with actual callees produces counter4 versus0; its negative control produces0/0. The31FC/3214 apparent savings are noncontiguous/shared interrupt chunks and separately called code, with changed SR/MMIO contracts.

The existing division/range replacements leave102+60 conditional bytes, but neither tail is owned. The boot0042 target can be assembled from four unrestricted bytes; the admitted domain includes both tails. Complete DE3E descriptor provenance, transitive RTOS targets, internal code-as-data consumers and interrupt/private-stack contracts also remain unclosed. The complete boundaries and local call proofs strengthen the evidence without eliminating those obligations.

The healthy recovery candidate was made from the newest known-good backup, retaining913functions and replaying only three qualified M07 comments. It has70names and61commentaddresses, all matching recovered damaged-copy metadata. Native save/close/reopen and zero-corruption validation pass. The31 later unqualified function definitions remain in the discrepancy report. The damaged authoritative IDB and forensic reconstruction remain unchanged; no replacement or uncertain import occurred.

See [architectural decision](ARCHITECTURAL_DECISION.json), [engineering gates](ENGINEERING_GATES.json), [deliverable index](DELIVERABLES.md), [MerpMod reconstruction](merpmod_mapping/MERPMOD_MAPPING.md), [range/ownership review](range_ownership_review/RANGE_OWNERSHIP_REVIEW.md), and [IDB recovery review](idb_reopen_audit/RECOVERY_CANDIDATE_REVIEW.md).
'''
    (OUT/'COMPARATIVE_ANALYSIS.md').write_text(report,encoding='utf-8')
    (OUT/'FUTURE_EVIDENCE.md').write_text('''# Minimum evidence after the residency freeze

No physical acquisition was performed or newly required to finish this run. Do not resume resident development merely to collect more family comparisons or finite execution cases.

To reopen residency, provide an independently checkable operating/entry contract and proof excluding or preserving all admitted computed entries/internal code-as-data consumers of the proposed bytes, plus saved-PC/interrupt/private-stack behavior. In particular, the boot target domain, DE3E descriptors and transitive RTOS0040 route cannot be silently excluded. A benign bench trace alone does not establish universal software exclusion.

For the eventual single human physical connection, retain the existing six raw OEM observations with complete request/response frames, ECU/TCU identities, UTC and monotonic timestamps and passive TCU validity/freshness context. This analysis adds no passive address or field. Capture pre-kernel observations before any qualified full-ROM read. Exact current-ROM identification requires a complete byte image and hash; a calibration ID or filename is insufficient.

The prior A0 full-image attestation remains withdrawn. ECUFlash Read remains only a prospective acquisition mechanism until its exact installed kernel, temporary RAM effects, full coverage, flash-write exclusion and exit/reset cleanup are independently qualified. This report does not authorize an unqualified read/write/test-write operation or a physical transport implementation.

After software residency/context closure and exact current-image identification, bench-only gates still include physical transport acceptance, silicon latency/watchdog/interrupt behavior and stack margins, and TCU validity/freshness semantics. Those gates are additional requirements, not substitutes for ownership. Host-native A8 remains the supported offline/native-virtual diagnostic path in integrations/m07.
''',encoding='utf-8')
    index='''# Diaphora comparative deliverables

Working tool: `C:/Dev/Tools/diaphora-3.4.2-a2wc`. Native IDA9.4 build9.4.260610.6c3b13fe, IDAPython9.4.0, CPython3.14.7 AMD64. Original Program Files copy is unchanged. HCLI, decompiler/microcode and trained ML model are not required.

Durable smoke command (already accepted; not rerun during this continuation):
```powershell
py -3.14 C:/Dev/Astra_A2WC511R/tools/diaphora/smoke.py
```

| Deliverable | Location |
|---|---|
| Decision and final gates | [COMPARATIVE_ANALYSIS.md](COMPARATIVE_ANALYSIS.md), [ENGINEERING_GATES.json](ENGINEERING_GATES.json) |
| Native environment | [IDA_PYTHON_ENVIRONMENT.json](IDA_PYTHON_ENVIRONMENT.json), [tool README](../../../tools/diaphora/README.md) |
| Dependency/source provenance | [setup](setup), retained package/wheel/vendor manifests |
| All current source patches | [combined diff](setup/matcher_partition_repair/COMPATIBILITY_PATCH_ALL.diff), [manifest](setup/matcher_partition_repair/MANIFEST.json), [repair journal](SETUP_REPAIR_LOG.md) |
| Exports and exact ROM/IDB/SQLite/config hashes | [EXPORT_INDEX.json](EXPORT_INDEX.json) |
| Final comparison databases and hashes | [RESULT_INDEX.json](RESULT_INDEX.json), [partition/reproducibility audit](comparison_audit/COMPARISON_SUMMARY.json) |
| Function correspondence database | [FUNCTION_CORRESPONDENCE.sqlite](correspondence_final_01/FUNCTION_CORRESPONDENCE.sqlite) |
| JSONL and deterministic hashes | [FUNCTION_CORRESPONDENCE.jsonl](correspondence_final_01/FUNCTION_CORRESPONDENCE.jsonl), [DETERMINISM.json](correspondence_final_01/DETERMINISM.json) |
| Metadata review queue | [16 held proposals](correspondence_final_01/METADATA_IMPORT_REVIEW_QUEUE.json) |
| Smaller implementation candidates | [three reviewed proposals](correspondence_final_01/SMALLER_IMPLEMENTATION_CANDIDATES.json) |
|510S↔511R homologs | [homolog report](A2WC510S_A2WC511R_HOMOLOGS.md), [qualified hook mappings](merpmod_mapping/MERPMOD_MAPPING.md) |
| Archived522S stock-vs-patched reconstruction | [MerpMod mapping](merpmod_mapping/MERPMOD_MAPPING.md), [source/archive provenance](merpmod_reference/MERPMOD_REFERENCE.md) |
| Range/density/caller/interior ownership | [range review](range_ownership_review/RANGE_OWNERSHIP_REVIEW.md) |
| Simulator regressions | `C:/Dev/A2WC511R_Sim/diaphora_crossrom`, [range counterexample](range_ownership_review/195E8_COUNTEREXAMPLE.json), [archived clear](merpmod_mapping/archived_clear_leaf_regression.json) |
| Independent review | [correspondence audit](correspondence_independent_review/FINAL_CORRESPONDENCE_AUDIT.json), [MerpMod peer review](correspondence_independent_review/MERPMOD_MAPPING_PEER_REVIEW.json) |
| Qualified recovery candidate and discrepancies | [recovery review](idb_reopen_audit/RECOVERY_CANDIDATE_REVIEW.md), [health](idb_reopen_audit/RECOVERY_CANDIDATE_HEALTH.json) |
| Preservation | [PRESERVATION.json](PRESERVATION.json) |
| Minimum new evidence | [FUTURE_EVIDENCE.md](FUTURE_EVIDENCE.md) |

Score1 is a proposal. VERIFIED_IDENTITY is scoped to independent routine-byte/literal/simulator evidence and never implies whole-firmware ownership. Old superseded results remain retained for audit. The selected final index is authoritative for this comparative package; no ECU image is approved for physical use.
'''
    (OUT/'DELIVERABLES.md').write_text(index,encoding='utf-8')
    with sqlite3.connect(OUT/'correspondence_final_01/FUNCTION_CORRESPONDENCE.sqlite') as db:
        counts=dict(db.execute('select confidence,count(*) from correspondence where comparison=? group by confidence',('stock_511R_vs_510S_03',)))
    (OUT/'A2WC510S_A2WC511R_HOMOLOGS.md').write_text(f'''# A2WC510S and A2WC511R homolog review

Final comparison stock_511R_vs_510S_03 has1,023 retained proposal rows: {counts}. There are999 distinct target functions and1,010 distinct source functions represented;137 additional source functions are explicitly unmatched. Multiple proposals remain ambiguous, not separate verified functions.

A2WC510S is the source-supported MT profile; A2WC511R is the5EAT target. CAL ID proximity does not establish calibration or transmission equivalence. No exact compiled510S patched image was found; the compiled archive comparison uses independently pinned522S, explicitly distinguished.

Six source function identities have independent chunk/call/literal assertions: Pull2D209C, Pull3D2150, MAF caller79A8, resetF928, WGDC14B20 andrev-limit317D8. Their external calibration pointers/callees are retained. These are structural homologs, not approved active-control transfers. See merpmod_mapping/MERPMOD_MAPPING.md for exactcall/delays/continuations and20negativecontrols.

The range routine1466E has the same190 executable bytes under the recovered full-entry contract; no smaller510S replacement exists. Division4260 reuses the already established identical170-byte object evidence. Neither relationship closes arbitrary interiorentry, computedcontrol, code-as-data or hardwarecontext contracts. The final database records raw chunks, literaldependencies, CFGstatistics, callers/callees, constants, names, provenance and confidence for every retained match.16 source-symbol proposals remain held in the reviewqueue; none was imported into authority.
''',encoding='utf-8')
    # Update current handoff only. Frozen M07 source, reports and delivery stay intact.
    state=ROOT/'state';checkpoint=read(state/'CHECKPOINT.json')
    checkpoint.update({'phase':'DIAPHORA_COMPARATIVE_COMPLETE_ECU_RESIDENCY_FROZEN','updated_utc':now,
        'current_architecture':decision['decision'],'current_evidence':'reports/local/diaphora','engineering_gates':'reports/local/diaphora/ENGINEERING_GATES.json',
        'gate_summary':{status:[g['id'] for g in gates if g['status']==status] for status in ['PASS','FAIL','PHYSICAL/BENCH REQUIRED']},
        'current_comparative_task_complete':True,'ECU_resident_branch_frozen':True,'M08_built':False,'provably_owned_ROM_bytes':0,
        'conditional_saved_ROM_bytes':162,'host_offline_service_supported':True,'ECU_physical_test_candidate':False,
        'production_release_allowed':False,'physical_validation':False,'authoritative_IDB_replaced':False,
        'recovery_candidate':'work/diaphora/idbs/recovery_candidate_01.i64','recovery_candidate_sha256':'55575c37d368665adcf89bd18cd81bcf6dd6cac7a615d17161514b4a0e4d1500',
        'function_correspondence':'reports/local/diaphora/correspondence_final_01/FUNCTION_CORRESPONDENCE.sqlite',
        'function_correspondence_sha256':h(OUT/'correspondence_final_01/FUNCTION_CORRESPONDENCE.sqlite'),
        'next_action':'Use supported host-nativeA8; reopenresidentworkonlywithnewentry/data-consumer/contextproof, notmorefinitefamilytests.'})
    (state/'CHECKPOINT.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    (state/'CURRENT_STATE.md').write_text('''# A2WC511R comparative closure checkpoint

The Diaphora comparative run is complete. ECU residency is **frozen**:0 ownedbytes,162 conditionalM07bytes; noM08 payload built. Host-nativeA8 in integrations/m07 remains the supported diagnostic path. No physical acquisition, provider operation, flash or active-control feature was performed.

Read reports/local/diaphora/COMPARATIVE_ANALYSIS.md and DELIVERABLES.md. Final correspondence is correspondence_final_01/FUNCTION_CORRESPONDENCE.sqlite:12,431rows/12comparisons, independently audited, deterministicSQL/JSONL hashes. Final resultlists partition both sourceinventories; unmatchedlabels and stale-cache omissions are repaired. Existing installs/exports were reused; onlyaffectedresults were regenerated.

Archived522S MerpMod has four literalhooks, nine insertedfunctions and a120-byte compiledRAM clear atFFFF73B0. That allocation is historical evidence, not ownership. All rangefamily bodies are190instructionbytes; three smaller proposals were rejected. The boot0042 inputtarget domain includes bothtails; DE3E/RTOS/context/data-consumer contracts remain incomplete. ExactcurrentROM plusbench timing alone is insufficient.

Original damagedauthority46f442… remains preserved. Healthy qualified recovery candidate work/diaphora/idbs/recovery_candidate_01.i64 SHA55575c37d368665adcf89bd18cd81bcf6dd6cac7a615d17161514b4a0e4d1500 passesnativeclose/reopen.70names/61commentaddresses agree withdamagedmetadata;31unqualifiedlaterfunctiondefinitions withheld. No automaticpromotion/import.

M0/M06/M07,oldreviewdeliveries,originalDiaphora source andstrictsimulatorcore retainallpinnedhashes. Currentgates: reports/local/diaphora/ENGINEERING_GATES.json. New taskmustrespectthefreeze; see state/NEXT_ACTIONS.md. Session01a0da26-addc-7fe1-84df-8c0baa8174f8.
''',encoding='utf-8')
    (state/'NEXT_ACTIONS.md').write_text('''# Continuation after comparative closure

Use integrations/m07 host-nativeA8 offline/native-virtual observations. Do not rerun accepted Diaphora installation/probes/exports or stockselfchecks without changedinputs. Reuse tools/diaphora and the final selectedindexes.

ECU-resident research is frozen. Do not add finiteROMfamilytests, shrinkanotherambiguouschunk, claimFFownership, enableactivecontrols orbuildM08. Reopen only for independentlycheckable admission/entry/data-consumer/context evidence capable of excluding the documentedcomputedfrontiers. CurrentROMidentification andbenchtiming alone do notsolve those software obligations.

The qualifiedIDBrecoverycandidate andpre-replacement review are complete; originaldamagedauthority is evidence. Do not silentlypromote31unqualifiedfunctionboundaries or uncertaincross-ROMnames. See recoveryreview before any laterreplacementaction.

Futurephysicalevidence remains deferred: exactcompletecurrentROM after qualifiedReadimplementation, sixexistingrawobservations+timestamps/passiveTCUvalidity, then hardwaretiming/stack/context/transport checks aftersoftwareclosure. A0full-imageattestation stayswithdrawn. Thisrunadds0passivefields.
''',encoding='utf-8')
    for name in ['DECISIONS.md','SESSION_LOG.md']:
        with (state/name).open('a',encoding='utf-8') as f:f.write(f'\n{now} Diaphora comparative closure:12,431correspondence rows/12pairs; independentrow/hash reviewPASS. FourarchivedMerpModliteralhooks/nineinsertedfunctions/120BcompiledRAM established; range190instructionbytesandthreeproposalsrejectedsafetransplant. ZeroownedROMbytes; freezeECUresidentbranch, noM08build, host-nativeA8supported. Qualifiedhealthy913-functionIDBrecoverycandidatepreparedandcompared;31unqualifiedfunctiondefinitionswithheld;authorityunchanged. FrozenhashesPASS. reports/local/diaphora/DELIVERABLES.md andENGINEERING_GATES.json arecurrent.\n')
    (state/'ECU_RESIDENCY_FREEZE.json').write_text(json.dumps(decision,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'COMPLETE','decision':decision['decision'],'owned_bytes':0,'gate_counts':output['counts'],'exports_indexed':len(exports)}))
if __name__=='__main__':main()
