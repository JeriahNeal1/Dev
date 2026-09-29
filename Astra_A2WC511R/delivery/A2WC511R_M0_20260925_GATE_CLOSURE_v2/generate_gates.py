"""Regenerate review decisions from pinned completed evidence, never approve by missing-file default."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).parent
ROOT=Path('C:/Dev/Astra_A2WC511R')
RUNTIME='runtime/20260925T211558.608898Z_gate_closure_runtime'
def read(p):return json.loads((OUT/p).read_text(encoding='utf-8-sig'))
def ev(p):
    f=OUT/p
    return {'path':p,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
def gate(id,status,reason,proof,dependencies=(),remaining=None):
    assert status in ('PASS','FAIL','PHYSICAL/BENCH REQUIRED')
    return {'id':id,'status':status,'reason':reason,'evidence':[ev(p) for p in proof],
            'depends_on':list(dependencies),'remaining':remaining}
runtime=read(RUNTIME+'/runtime_gate_report.json')
assert runtime['status']=='PASS' and runtime['paired_cases']==1024
assert runtime['exact_added_stack_bytes']==124
assert read('rom/routine_regression.json')['pass']
assert read('rom/analysis_regression.json')['status']=='PASS'
assert read('ram/ram_path_audit.json')['regression']['result']=='PASS'
interface=read('interfaces/interface_gate_status.json')
gates=[
 gate('FROZEN_BUILD_PROVENANCE','PASS','Original final05 payload, ELF, patches, checksums and all625 prior package entries remain hash-identical. No firmware rebuild or active-output feature changes.',
      ['frozen_verification.json']),
 gate('ROM_IDENTIFIED_ACCESS_PATHS','PASS','WholeFF runs, all raw literal/PC-relative/direct-branch matches, definition extents, vector/checksum constraints and actual bounded reader regressions reviewed. This is scoped access evidence.',
      ['rom/ROM_ALLOCATION_REVIEW.md','rom/static_audit.json','rom/definition_overlap.json','rom/routine_regression.json','rom/analysis_regression.json']),
 gate('ROM_OWNERSHIP','FAIL','Exclusive ownership of[E1000,E1364) was not established. No demonstrated collision, but remaining computed access/context paths and undocumented extents prevent approval. Alternative[859BC,C0000) is also unproved.',
      ['rom/ROM_ALLOCATION_REVIEW.md','rom/reachability.json','runtime/independent_review.json'],remaining='Close remaining computed control/data extents or supply a trustworthy original allocation contract. Finite bench observation alone cannot prove absence of an unexecuted access.'),
 gate('RAM_IDENTIFIED_ACCESS_PATHS','PASS','Actual required persistent span is32bytes. Identified reset patterns/clear, DMA buffers, shared task stack, boot stack/ring, alias and timer paths have concrete bounds and regressions.',
      ['ram/RAM_OWNERSHIP_REVIEW.md','ram/ram_path_audit.json',RUNTIME+'/ram_pattern_FA58.json',RUNTIME+'/dma_setup_C31E.json']),
 gate('RAM_OWNERSHIP','FAIL','Exclusive lifetime ownership of[FFFF7400,FFFF7420) was not established against remaining indirect CPU writers and full context/interrupt invariants. No better location is justified.',
      ['ram/RAM_OWNERSHIP_REVIEW.md','ram/ram_gate_status.json'],remaining='Finish CPU pointer/context proof. Then observe only candidate32+boundaries, stack high-water, actual DMA destinations and qualified reset/interrupt modes on bench; observation does not erase the software gap.'),
 gate('INJECTED_ABI_AND_STACK','PASS','Final compiler output has a complete injected call graph, balanced all-path frames and an exact 124-byte extra peak. The wrapper preserves the OEM decoder return state, with no FPU/GBR/VBR accesses. Proof assumes a private valid stack disjoint from state.',
      [RUNTIME+'/RUNTIME_HANDOFF.md',RUNTIME+'/runtime_gate_report.json']),
 gate('OEM_SINGLE_WRITER_INVARIANT','FAIL','M0 is intentionally nonreentrant. Actual nested-writer negative test demonstrates publication failure. Identified task priority/state guards are insufficient for the full OEM context invariant.',
      [RUNTIME+'/runtime_gate_report.json','runtime/runtime_source_addendum.md','ram/RAM_OWNERSHIP_REVIEW.md'],
      remaining='Complete task9 activation/preemption/resume invariant proving no concurrent M0 writer; do not fix this by enabling active features or assuming timing.'),
 gate('INSTRUCTION_BUDGET_AND_CADENCE_MODEL','PASS','Conservative full-hook bound562instructions/178dataaccesses; additional bound526instructions. Nominal task9 enqueue every8CMT1 service calls/160000Pphi cycles. Conditional serialized cycle envelope is explicit.',
      [RUNTIME+'/runtime_gate_report.json','runtime/runtime_source_addendum.md','ram/ram_path_audit.json']),
 gate('TASK_STACK_TIMING','PHYSICAL/BENCH REQUIRED','Absolute clock, memory/entry stalls, interrupt interference, total shared-stack occupancy and scheduling margin have not been measured on the ECU. Simulated cycle examples are conditional, not verified silicon timing.',
      [RUNTIME+'/RUNTIME_HANDOFF.md','ram/RAM_OWNERSHIP_REVIEW.md'],['RAM_OWNERSHIP','OEM_SINGLE_WRITER_INVARIANT'],
      'After software prerequisites pass, measure clock/tick/enqueue/service intervals, worst observed latency, nesting and stack high-water on the exact ECU/build.'),
 gate('SIMULATOR_REVERSE_ENGINEERING_UTILITY','PASS','52focusedtests/56forms and1024stock-v-patch pairs PASS; watchpoints, pointer/value origins, deterministic replay, full-hole accounting and negative controls are usable from Codex.',
      [RUNTIME+'/runtime_gate_report.json',RUNTIME+'/whole_hole_dynamic_summary.json','rom/routine_regression.json']),
 gate('LOCAL_CALIBRATION_SEARCH','PASS','All readable requested roots, ECUFlash registry/history/work paths,1MiB files regardless extension and archive/SRF images inventoried and classified. One saved tune uniquely matches all16 historical flash pageCRCs; no current identity inferred.',
      ['calibration/inventory.json','calibration/history_comparison.json','calibration/CURRENT_CALIBRATION_REVIEW.md']),
 gate('CURRENT_CALIBRATION','PHYSICAL/BENCH REQUIRED','No fresh fullROM read or complete attestation establishes the exact presently flashed image. The historical fullCRC match is not current byte identity.',
      ['calibration/CURRENT_CALIBRATION_REVIEW.md','calibration/ONE_CONNECTION_READ_ONLY_ACQUISITION.md'],
      ['READ_ONLY_COLLECTOR_PHYSICAL'],
      remaining='Human performs one read-only connection using the prepared collector: two full images + pendingTCU bytes. Abort unsupported or inconsistent read; no ECUFlash kernel fallback or flash command.'),
 gate('TCU_VALIDITY_SEMANTICS','PHYSICAL/BENCH REQUIRED','Raw/source/snapshot/latch/flags interpretations do not establish global freshness or physical clutch engagement. M0 continues to report unknown coherence/freshness.',
      ['calibration/ONE_CONNECTION_READ_ONLY_ACQUISITION.md'],remaining='Collect named six raw bytes with timestamped startup/communication-state labels. A normal trace alone cannot prove fault behavior; any missing fault mode remains an explicit bench gate.')
]
# Interface agent supplies exact statuses/evidence after native and isolated transport validation.
items=interface.get('gates')
assert isinstance(items,list) and items,'Interface summary must provide a nonempty gates list'
for item in items:
    dependencies=list(item.get('depends_on',()))
    if item['id']=='READ_ONLY_COLLECTOR_PHYSICAL':dependencies.append('READ_ONLY_COLLECTOR_OFFLINE')
    gates.append(gate(item['id'],item['status'],item['reason'],item['evidence'],dependencies,item.get('remaining')))
ids=[g['id'] for g in gates];assert len(ids)==len(set(ids))
gates.extend([
 gate('PHYSICAL_TEST_CANDIDATE','FAIL','Not eligible: software ownership/single-writer gates failed and current identity/timing remain unvalidated.',
      ['rom/ROM_ALLOCATION_REVIEW.md','ram/RAM_OWNERSHIP_REVIEW.md'],['ROM_OWNERSHIP','RAM_OWNERSHIP','OEM_SINGLE_WRITER_INVARIANT','TASK_STACK_TIMING','CURRENT_CALIBRATION']),
 gate('VEHICLE_VALIDATED','PHYSICAL/BENCH REQUIRED','No ECU/TCU flash, live memory write, actuator command or driving test was performed.',
      ['EVIDENCE_PLAN.md'],['PHYSICAL_TEST_CANDIDATE'])])
ids={g['id'] for g in gates}
for g in gates:assert set(g['depends_on'])<=ids,g['id']
out={'schema':2,'target':'A2WC511R','ecuid':'2F12515306','updated_utc':datetime.now(timezone.utc).isoformat(),
 'session_id':'01a0da26-addc-7fe1-84df-8c0baa8174f8','artifact':'frozen m0_final_05 diagnostic only',
 'build_complete':True,'offline_reviewed_candidate':False,'physical_validation':False,'production_release_allowed':False,
 'all_purely_offline_gates_passed':False,'current_calibration_ready_build_procedure_prepared':False,
 'build_procedure_reason':'Conditional user prerequisite not met: exclusive ROM/RAM ownership and OEM single-writer invariant remain FAIL. Acquisition tooling is prepared separately.',
 'interface_summary':ev('interfaces/interface_gate_status.json'),
 'verification_limitations':interface.get('verification_limitations',[]),
 'dependency_scope':'Dependencies describe the prepared acquisition and candidate path. Another independently reviewed current-image attestation would require a revised evidence decision; historical file identity alone is insufficient.',
 'gates':gates,'summary':{s:[g['id'] for g in gates if g['status']==s] for s in ('PASS','FAIL','PHYSICAL/BENCH REQUIRED')}}
(OUT/'ENGINEERING_GATES.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out['summary'],indent=2))
