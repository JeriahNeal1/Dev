"""Regenerate evidence-linked M0.7 gates and exact per-fragment ownership limits."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
ROOT=Path('C:/Dev/Astra_A2WC511R'); OUT=ROOT/'reports/local/m07_residency'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(relative):return json.loads((OUT/relative).read_text(encoding='utf-8-sig'))
def evidence(*paths):
    return [{'path':p,'sha256':sha(OUT/p)} for p in paths]
def main():
    build=read('build_audit_02/BUILD_AUDIT.json');assert build['status']=='PASS'
    peer=read('ownership_review/ownership_peer_review.json')
    objects=read('semantic/candidate_manifest.json')['candidates']
    host=read('host/host_evidence_manifest.json');assert host['regression_groups']==15
    for relative in ('semantic/semantic_structural_proof.json','semantic/TARGET_DOMAIN_CLOSURE.json',
            'semantic/one_page_CFG_frame_proof.json','semantic/two_page_CFG_frame_proof.json'):
        assert (OUT/relative).is_file(),relative
    profiles={}
    for profile in ('one_page','two_pages'):
        overlay=read('protocol/execution_01/'+profile+'_overlay.json')
        fragments=[]
        for f in overlay['fragments']:
            a=f['address'];data=bytes.fromhex(f['after_hex']);b=a+len(data)
            parent='division' if 0x4260<=a<0x430A else 'range_tail' if 0x1473C<=a<0x147AC else 'SSM_live_default'
            is_payload='adapter' in f['label'] or 'two-page' in f['label']
            fragments.append({'role':'payload' if is_payload else 'existing_executable_replacement',
                'label':f['label'],'start':a,'end_exclusive':b,'hex_range':[f'{a:08X}',f'{b:08X}'],
                'bytes':len(data),'parent_object':parent,'before_sha256':sha256(bytes.fromhex(f['before_hex'])).hexdigest(),
                'after_sha256':sha256(data).hexdigest(),'before_hex':f['before_hex'],'after_hex':f['after_hex'],
                'ownership_status':'FAIL','owned_bytes':0,
                'semantic_scope':'Intentional exact project-request extension; original default fallback preserved' if parent=='SSM_live_default' else 'Bounded original-function contract passes; complete incoming-control/internal-consumer closure fails',
                'unclosed':['all calculated entries and internal code-as-data consumers','whole-context stack/interrupt contract'],
                'evidence':evidence('protocol/execution_01/'+profile+'_overlay.json',
                    'protocol/DEFAULT_STUB_REFERENCES.json' if parent=='SSM_live_default' else 'ownership_review/ownership_peer_review.json')})
        profiles[profile]={'raw_sha256':overlay['rom_sha256'],'payload_bytes':100 if profile=='one_page' else 148,
            'additional_adapter_stack':8,'persistent_project_RAM_bytes':0,
            'payload_capacity_arithmetic':'PASS','accepted_residency':'FAIL','fragments':fragments}
    own={'schema':1,'classification':'CONDITIONAL_EXECUTABLE_SAVINGS_NOT_APPROVED_OWNERSHIP',
        'stock_sha256':build['stock_sha256'],'conditional_tail_bytes':162,'provably_owned_bytes':0,
        'status':'FAIL','objects':{},'profiles':profiles,
        'allowed_modified_image_behavior':'Transparent OEM diagnostic ROM readback exposes the modified bytes; it need not emulate the old ROM.',
        'not_allowed_as_proof':'No finite test count, missing literal reference or capacity calculation closes an unknown pointer domain.',
        'evidence':evidence('ownership_review/ownership_peer_review.json','semantic/TARGET_DOMAIN_CLOSURE.json',
            'semantic/semantic_structural_proof.json','semantic/abstract_concrete_crosscheck.json')}
    for name,c in objects.items():
        own['objects'][name]={'entry':0x4260 if name=='division' else 0x1466E,
            'changed_prefix':[c['start'],c['replacement_end_exclusive']],
            'original_changed_span':[c['start'],c['original_end_exclusive']],
            'candidate_tail':[c['replacement_end_exclusive'],c['original_end_exclusive']],
            'conditional_saved_bytes':c['bytes_saved'],'proven_owned_bytes':0,
            'replacement_sha256':c['binary_sha256'],'entry_and_inbound_evidence':peer['objects'][name],
            'semantic_equivalence':'PASS_UNDER_DECLARED_ENTRY_PRIVATE_STACK_NONINTERLEAVING_CONTRACT',
            'ownership_status':'FAIL'}
    (OUT/'OWNERSHIP_FRAGMENTS.json').write_text(json.dumps(own,indent=2)+'\n',encoding='utf-8')
    gates=[]
    def gate(id,status,scope,reason,paths,remaining=None,depends=None):
        assert status in ('PASS','FAIL','PHYSICAL/BENCH REQUIRED')
        gates.append({'id':id,'status':status,'scope':scope,'reason':reason,
            'evidence':evidence(*paths),'remaining':remaining,'depends_on':depends or []})
    gate('FROZEN_M0_M06_PRESERVATION','PASS','Immutable historical artifacts',
         'All 211 frozen M0.6 and 1522 M0 delivery hashes unchanged; M0.7 files are separate.',
         ['M06_FROZEN_MANIFEST.json','build_audit_02/BUILD_AUDIT.json'])
    gate('HOST_A8_OBSERVATION_SERVICE','PASS','Supported offline host tool',
         'Six raw observations, host predicates, full frames, UTC/monotonic timestamps, serialization, terminal failure, provenance and finite replay; 15 regression groups.',
         ['host/HOST_SERVICE_REVIEW.md','host/host_evidence_manifest.json','host/INDEPENDENT_HOST_REVIEW.md'])
    gate('HOST_NATIVE_ROMRAIDER_INTEGRATION','PASS','Installed native codec over isolated virtual transport',
         'Eight stock-OEM executed fixtures through actual RomRaider encoder/parser plus eight replay captures. No physical provider.',
         ['host/capture_native_final.jsonl','host/capture_replay_final.jsonl','host/host_evidence_manifest.json'])
    gate('PROJECT_PERSISTENT_RAM','PASS','Architecturally eliminated',
         'Zero new persistent RAM; no 32-byte reservation and no publication buffer. Private stack is a separate obligation.',
         ['protocol/one_page_01/manifest.json','protocol/two_pages_01/manifest.json','host/HOST_SERVICE_REVIEW.md'])
    gate('NEW_BACKGROUND_WRITER_AND_SINGLE_WRITER','PASS','Architecturally eliminated',
         'No background M0 writer/publication lifecycle. Observations use OEM synchronous response storage and stack-local saved registers.',
         ['protocol/PROTOCOL_TRADEOFFS.md','build_audit_02/BUILD_AUDIT.json'])
    gate('TASK9_PUBLICATION_AND_PERIODIC_CADENCE','PASS','Architecturally eliminated',
         'Task9 pointers unchanged; no diagnostic work without a project request. OEM replacement timing remains a separate gate.',
         ['protocol/PROTOCOL_TRADEOFFS.md','build_audit_02/BUILD_AUDIT.json'])
    gate('RAW_PROTOCOL_DISCRIMINATION','PASS','Exact compiled v1 profiles',
         '100-byte one-page or148-byte two-page adapter, fixed address/version/page requests, FC/FD plus length distinction; wrong-page valid responses rejected.',
         ['protocol/CODEC_REVIEW.md','protocol/codec_evidence_manifest.json','protocol/execution_01/compiled_protocol_fixtures.json'])
    gate('DISCARDED_REFILL_SUPPRESSION','PASS','Existing OEM A8 progress contract',
         'No custom refill hook; each source read once per accepted exchange, including the discarded post-four-byte callback.',
         ['protocol/PROTOCOL_TRADEOFFS.md','protocol/execution_01/compiled_protocol_fixtures.json'])
    gate('OEM_DIAGNOSTIC_BEHAVIOR_SCOPED','PASS','Declared dispatcher/function-entry and private-stack contracts',
         'Exact project ingress is the only intended protocol change; OEM validation/classifier unchanged. Full dispatcher ABI and selected stock/native wire comparisons pass. Transparent ROM readback may expose new code bytes.',
         ['semantic/one_page_dispatch_abi.json','semantic/two_page_dispatch_abi.json','protocol/DEFAULT_STUB_REFERENCES.json','protocol/execution_01/compiled_protocol_fixtures.json'],
         'Not a universal interrupt/MMIO or every-session proof; existing B0/B8 MMIO paths are not silently stubbed.')
    gate('NO_ACTIVE_CONTROL_FEATURES','PASS','Project feature closure',
         'No new timing/fuel/boost/MAF/DBW/rev-limit/launch/ALS/transmission-torque control. Only observational SSM output and bounded OEM-equivalence replacements.',
         ['protocol/PROTOCOL_TRADEOFFS.md','semantic/SEMANTIC_REPLACEMENTS.md','build_audit_02/BUILD_AUDIT.json'])
    gate('SEMANTIC_EXECUTABLE_COMPRESSION','PASS','Bounded entry/private-stack/noninterleaving contracts',
         'Division32-step projection and complete nibble partition proof; registers, SR/PR/SP, RAM/MMIO writes and calls compared. Extra4-byte division stack traffic explicit.',
         ['semantic/semantic_structural_proof.json','semantic/semantic_differential.json','ownership_review/ownership_peer_review.json'])
    gate('COMPILED_ABI_FRAME_AND_INSTRUCTION_BOUNDS','PASS','Local compiled paths; no silicon or whole-interrupt claim',
         'Adapter8-byte frame, dispatcher36 total; division12 total; no FPU operations. Fixed-loop CFG and instruction bounds retained with timing assumptions.',
         ['semantic/one_page_CFG_frame_proof.json','semantic/two_page_CFG_frame_proof.json','semantic/SEMANTIC_REPLACEMENTS.md'])
    gate('SIMULATOR_SEMANTIC_AND_OWNERSHIP_UTILITY','PASS','Reverse-engineering tool contracts',
         'Strict75-form core preserved; bounded abstract/concrete cross-check, semantic comparison, negative controls, computed-target reports and unknown-frontier failure.',
         ['semantic/abstract_concrete_crosscheck.json','semantic/simulator_freeze_manifest.json','semantic/TARGET_DOMAIN_CLOSURE.json','ownership_review/ownership_peer_review.json'])
    gate('BUILD_DIFF_INVERSE_AND_NATIVE_CHECKSUM','PASS','Reproducible research artifacts only',
         'All executable sections reproduce; sole range-ELF FILE-path difference explained. Both raw/fixed images reverse exactly; actual installed RomRaider checksum agrees.',
         ['build_audit_02/BUILD_AUDIT.json','build_audit_02/one_page.native_checksum.json','build_audit_02/two_pages.native_checksum.json'])
    gate('LIVE_IDA_METADATA_PRESERVATION','PASS','Official existing database',
         'Backup, three qualified comments, unchanged mapped ROM bytes, supported save/close; helper stopped.',
         ['ida/M07_METADATA_WRITES.json','ida/FINAL_IDB_IDENTITY.json','ida/stopped_server.json'])
    gate('EXECUTABLE_TAIL_ROM_OWNERSHIP','FAIL','Complete requested ownership standard',
         '162 conditional saved bytes, zero accepted. Direct/literal inbound facts pass; computed entries and internal consumers remain unclosed. Boot path admits caller-directed R4 target.',
         ['OWNERSHIP_FRAGMENTS.json','ownership_review/OWNERSHIP_PEER_REVIEW.md','semantic/TARGET_DOMAIN_CLOSURE.json'],
         'Establish complete admissible entry and internal data-consumer contracts, or use host-only diagnostics. More finite cases cannot prove this.')
    gate('WHOLE_FIRMWARE_VALUE_SET_EXCLUSION','FAIL','Conservative fallback, not required if object ownership closes',
         '2585 candidate roots, unfinished100000-transfer worklist,80601 unknown frontiers. Opaque/data seeds are not certified reachability; no unknown is discarded to claim exclusion.',
         ['static_analysis/20260926T011704.827676Z/summary.json','semantic/TARGET_DOMAIN_CLOSURE.json'],
         'Close relevant unknown domains with admissible-entry/descriptor/consumer contracts; no universal anonymous-area ownership claim.')
    gate('GLOBAL_EXECUTION_CONTEXT_CONTRACT','FAIL','Complete firmware software contract',
         'Additional private stack and legitimate entry/preemption assumptions are explicit but not globally established. Caller-directed boot execution prevents unconditional target exclusion.',
         ['semantic/TARGET_DOMAIN_CLOSURE.json','ownership_review/ownership_peer_review.json'],
         'Prove context/stack exclusivity and relevant interrupt behavior in addition to later bench margin.')
    gate('SUFFICIENT_PROVABLY_OWNED_M07_BYTES','FAIL','ECU-resident integration',
         '100 and148 payload bytes fit102 and162 conditional capacity, respectively; accepted capacity is0.',
         ['OWNERSHIP_FRAGMENTS.json'],depends=['EXECUTABLE_TAIL_ROM_OWNERSHIP','GLOBAL_EXECUTION_CONTEXT_CONTRACT'])
    gate('A0_FULL_IMAGE_ATTESTATION','FAIL','Withdrawn acquisition claim',
         'OEM masking means equal1MiB views need not equal actual flash. Frozen old collector is not approved for exact-image acquisition.',
         ['host/HOST_SERVICE_REVIEW.md','ecuflash_read/ECUFLASH_READ_AUDIT.md'],
         'Replace with independently qualified exact-coverage mechanism; no80-minute A0 procedure.')
    for id,reason,remaining in [
        ('ECUFLASH_INSTALLED_KERNEL_IDENTITY','Exact installed DUAL kernel and full temporary RAM/MMIO effects not recovered; historical4660-byte upload is not complete execution footprint.','Recover hash-matched kernel/application Read path or vendor evidence.'),
        ('ECUFLASH_EXACT_READ_COVERAGE','Historical logs explicitly cover614400bytes;434176 lack read-area evidence. SynthesizedFF cannot attest exact live contents.','Prove/read every byte under documented exact coverage semantics.'),
        ('ECUFLASH_READ_FLASH_WRITE_EXCLUSION','Separate Read/Write log events do not prove all installed initialization/error branches exclude flash operations.','Recover complete command/host/kernel boundaries; Read is a RAM-upload execution workflow.'),
        ('ECUFLASH_EXIT_RESET_CLEANUP','Interface close logs do not establish kernel exit, reset or restored OEM RAM/peripheral state.','Qualify success/failure cleanup and reinitialization sequence.')]:
        gate(id,'FAIL','Installed acquisition implementation, offline software gap',reason,
             ['ecuflash_read/ECUFLASH_READ_AUDIT.md','ecuflash_read/static_extraction/STATIC_EXTRACTION_REVIEW.md','ecuflash_read/manifest.json'],remaining)
    gate('LIVE_HOST_TRANSPORT_IMPLEMENTATION','FAIL','Future live-host capability, deferred and not required for offline tool',
         'Current supported service intentionally has no physical backend; offline acceptance does not imply provider integration.',
         ['host/HOST_SERVICE_REVIEW.md'],'A separately authorized fixed-read adapter implementation and qualification are needed for live use.')
    for id,reason,paths,remaining in [
        ('CURRENT_ROM_IDENTIFICATION','No physical acquisition this run; stock and historical matches do not identify exact current flash.', ['ecuflash_read/ECUFLASH_READ_AUDIT.md'],'Obtain exact untouched image through a software-qualified mechanism.'),
        ('SILICON_TIMING_AND_INTERRUPT_STACK_MARGIN','Wait states, ISR interference, actual stack high water/watchdog and transport timing are not software-event or cycle-model results.', ['semantic/SEMANTIC_REPLACEMENTS.md','semantic/one_page_CFG_frame_proof.json','semantic/two_page_CFG_frame_proof.json'],'After ownership/context closure, measure all affected OEM callers including slower division/range routines; not just request cadence.'),
        ('TCU_VALIDITY_AND_FRESHNESS','Raw predicates do not prove physical clutch/gear, freshness, CAN health or fault validity.', ['host/HOST_SERVICE_REVIEW.md'],'Retain unknown status; eventual passive pre-kernel six-byte capture and separately scoped physical interpretation.'),
        ('PHYSICAL_TRANSPORT_ACCEPTANCE','No hardware, electrical/echo/interrupt or live adapter acceptance performed.', ['host/HOST_SERVICE_REVIEW.md','protocol/PROTOCOL_TRADEOFFS.md'],'Only after a separately implemented/reviewed live transport; no physical action requested now.')]:
        gate(id,'PHYSICAL/BENCH REQUIRED','Deferred physical evidence',reason,paths,remaining)
    gate('ECU_PHYSICAL_TEST_CANDIDATE','FAIL','Release readiness',
         'Current-ROM identification and bench timing alone do not resolve software ownership/context failures.',
         ['OWNERSHIP_FRAGMENTS.json','M07_REVIEW.md'],depends=['SUFFICIENT_PROVABLY_OWNED_M07_BYTES','GLOBAL_EXECUTION_CONTEXT_CONTRACT','CURRENT_ROM_IDENTIFICATION','SILICON_TIMING_AND_INTERRUPT_STACK_MARGIN'])
    summary={s:[g['id'] for g in gates if g['status']==s] for s in ('PASS','FAIL','PHYSICAL/BENCH REQUIRED')}
    result={'schema':2,'architecture':'M07_HOST_NATIVE_A8_PREFERRED_AND_UNAPPROVED_EXECUTABLE_TAIL_RESEARCH',
        'evidence_base_in_workspace':str(OUT),'evidence_base_in_review_bundle':'project/reports/local/m07_residency',
        'generated_utc':datetime.now(timezone.utc).isoformat(),'session_id':'01a0da26-addc-7fe1-84df-8c0baa8174f8',
        'release_allowed':False,'physical_actions_performed':False,'host_offline_tool_supported':True,
        'current_rom_plus_bench_only_sufficient_for_ECU_candidate':False,
        'all_purely_offline_ECU_gates_pass':False,'provably_owned_bytes':0,'conditional_saved_bytes':162,
        'old_failures_eliminated':['32-byte persistent project RAM allocation','new diagnostic single-writer publication invariant','task9 background publishing','diagnostic periodic cadence'],
        'old_failure_remaining':['ROM ownership replaced with explicit executable-object obligation, not declared solved'],
        'gates':gates,'summary':summary}
    (OUT/'ENGINEERING_GATES.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'counts':{k:len(v) for k,v in summary.items()},'owned_bytes':0,'release_allowed':False}))
if __name__=='__main__':main()
