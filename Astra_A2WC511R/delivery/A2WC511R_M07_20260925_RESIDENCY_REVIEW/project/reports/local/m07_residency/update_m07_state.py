"""Point current state at the sealed M0.7 result; retain historical decisions."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=ROOT/'reports/local/m07_residency'
STATE=ROOT/'state';DELIVERY=ROOT/'delivery/A2WC511R_M07_20260925_RESIDENCY_REVIEW'
SESSION='01a0da26-addc-7fe1-84df-8c0baa8174f8'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def main():
    gates=json.loads((OUT/'ENGINEERING_GATES.json').read_text())
    manifest=DELIVERY/'SHA256SUMS.json';files=json.loads(manifest.read_text())['files']
    for rel,h in files.items():assert sha(DELIVERY/rel)==h,rel
    stamp=datetime.now(timezone.utc).isoformat()
    delivery_sha=sha(manifest)
    checkpoint={'schema':2,'phase':'M07_OFFLINE_REVIEW_COMPLETE_RESIDENCY_NOT_ESTABLISHED',
        'updated_utc':stamp,'session_id':SESSION,'current_architecture':'Preferred supported offline stock-A8 host service; separate unapproved M07 ECU research',
        'compiled_a2wc511r_port':True,'build_complete':True,'offline_reviewed_candidate':False,
        'physical_validation':False,'production_release_allowed':False,'ECU_physical_test_candidate':False,
        'host_offline_service_supported':True,'current_source':'work/M07',
        'current_build':'reports/local/m07_residency/protocol/execution_01',
        'checksum_corrected_research_builds':'reports/local/m07_residency/build_audit_02',
        'current_evidence':'reports/local/m07_residency','engineering_gates':'reports/local/m07_residency/ENGINEERING_GATES.json',
        'gate_summary':gates['summary'],'delivery':str(DELIVERY),'delivery_manifest_sha256':delivery_sha,
        'delivery_hash_verification_passed':True,'delivery_files':len(files),
        'current_vehicle_flash':'UNIDENTIFIED; NO PHYSICAL ACQUISITION THIS RUN',
        'current_calibration_ready_build_procedure_prepared':False,'A0_exact_image_acquisition':'WITHDRAWN',
        'ECUFlash_Read_exact_coverage_kernel_cleanup_flash_exclusion':'FAIL_SOFTWARE_EVIDENCE_INCOMPLETE',
        'old_M0_frozen':True,'old_M06_frozen':True,
        'old_M0_delivery':'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2',
        'old_M0_manifest_sha256':'b597dd48fd4f587f53c1bd9a7be3c915072f531e423d6aeb51bb7d497010d115',
        'm06_frozen_manifest':'reports/local/m07_residency/M06_FROZEN_MANIFEST.json',
        'm06_frozen_manifest_sha256':'577853392c842f75aca92a5902f1d0d50f0ee81e99c4f4f863cca80cb4cccaff',
        'conditional_reclaimed_ROM_bytes':162,'provably_owned_ROM_bytes':0,
        'new_persistent_RAM_bytes':0,'new_periodic_diagnostic_hook':False,
        'new_single_writer_publication_invariant_required':False,
        'completed':['supported offline six-byte native-A8 host observations','actual native RomRaider virtual acceptance',
            'raw-only discriminated100/148-byte research protocols','existing TX-state discarded-refill suppression',
            'two scoped structural OEM executable-equivalence proofs','per-fragment ownership failure evidence',
            'target-specific static closure and caller-directed boot counterexample to unconditional exclusion',
            'fresh builds, whole-byte diff/inverse and installed native checksum comparison',
            'offline ECUFlash inventory/log/kernel boundary and static protector recovery',
            'official IDB qualified comments saved after backup; ROM bytes unchanged',
            'frozen preservation and sealed review bundle'],
        'blocking':['complete executable-object ownership and internal consumers','global valid-entry/private-stack/interrupt contracts',
            'qualified exact-current-ROM acquisition mechanism','later physical identity/timing/stack/transport/TCU evidence'],
        'next':'Use supported host observation tool for offline work. ECU branch requires explicit closure of retained ownership/context contracts, not more finite cases. Physical acquisition and active controls remain deferred.'}
    (STATE/'CHECKPOINT.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    (STATE/'CURRENT_STATE.md').write_text(f'''# A2WC511R M0.7 checkpoint

The authorized offline M0.7 review is complete. **ECU ROM residency remains FAIL.**
The supported diagnostic tool is `integrations/m07`: fixed native A8 observation
of six existing OEM bytes, host predicates, complete raw frames and UTC/monotonic
timestamps, with finite replay and installed native RomRaider virtual backends.
It needs no ECU patch. No physical backend or provider is used.

Separate raw-only research adapters compile to100 bytes (one page) or148 bytes
(two fragments/pages), with explicit request/version/page and FC/FD response
discrimination. Both reuse OEM A8 TX progress and avoid the discarded second
sample. There is no persistent project RAM, publication buffer, new single-writer
invariant, task9 hook or periodic diagnostic cadence.

OEM division4260 compresses170 to68 bytes and conditionally leaves
`[42A4,430A)` (102 bytes). The range switch1473C within1466E compresses112 to52,
conditionally leaving `[14770,147AC)` (60 bytes). Structural/differential proofs
pass only their stated entry/private-stack contracts. Complete calculated-entry
and internal-consumer ownership does not pass:162 conditional bytes,0 accepted.
The boot path0042 accepts a caller-supplied R4 execution target. Bounded literal
caller/descriptor/RTOS target results must not be promoted to global closure.
The100-byte adapter needs only division compression; the148-byte variant also
changes range execution cost. Silicon timing and total interrupt stack margin
remain unmeasured. Current-ROM identity and bench timing alone are insufficient
for an ECU physical-test candidate while ownership/context gates fail.

Fresh builds reproduce executable bytes; range ELF differs only in its STT_FILE
object path. Both overlays reverse exactly to stock and installed RomRaider
checksums agree. Corrected research hashes:

- One page:140736b11e14ed80290832ceef3ae67757f967a3751a6ddb2b6d8afa0cc9afbd.
- Two pages:17ce75b3514891f2c5c30f0ec10bc5b4e3bf50b9004959fd906c600f7fb8797e.

Read `reports/local/m07_residency/M07_REVIEW.md`, `ENGINEERING_GATES.json`,
`OWNERSHIP_FRAGMENTS.json` and `CANDIDATE_CATALOG.md` there for exact scope.
Delivery:`{DELIVERY}`. Its {len(files)}-file manifest SHA256 is
`{delivery_sha}`. This is an offline review bundle, not an approved flash image.

Frozen M0 (1522 entries) and M0.6 (211 files and unchanged file set) are verified
unchanged. The existing official IDB was backed up, given three qualified comments,
saved/closed, and its mapped ROM bytes remain unchanged. No physical connection,
ECUFlash/provider execution, flash/write/test-write or active-control development
occurred. Simulator75-form core remains unchanged.

The A0 full-image attestation procedure is WITHDRAWN. ECUFlash historical Read
uploads4660 RAM bytes and explicitly logs614400 ROM bytes;434176 lack read-area
coverage evidence. Static Themida recovery reached loader layers but not the
installed DUAL kernel/Read/cleanup implementation. Exact coverage, complete RAM
effects, flash-operation exclusion and reset/cleanup remain software FAIL gates.
No replacement physical procedure is approved. Eventual ordering is passive
six-byte observations before a separately qualified kernel Read, then proven
exit/reset and renewed OEM identity. No extra passive channel was needed.

Session:`{SESSION}`. Updated:{stamp}.
''',encoding='utf-8')
    (STATE/'NEXT_ACTIONS.md').write_text('''# M0.7 continuation boundaries

The completed offline result is in reports/local/m07_residency and the sealed
M07 review delivery. Use integrations/m07/README.md for supported virtual/native
host observations. Preserve frozen M0/M0.6 and the sealed M07 review package.

Further ECU work requires new proof inputs or a bounded method for the remaining
computed-entry/internal-consumer/private-stack contracts. The caller-directed
boot trampoline is a real domain boundary. More finite cases or anonymous FF
space do not solve it. Do not relabel162 conditional saved bytes as owned.

Do not request/perform the withdrawn80-minute A0 image attestation. Before a
future human physical acquisition, qualify exact Read coverage, installed kernel
identity/effects, Read flash-exclusion, and exit/reset. The current host service
has no physical backend. Six pre-kernel raw observations are sufficient; no
additional passive address was added by M0.7.

No current-calibration build/flash procedure is approved. No active launch/ALS,
timing, fuel, boost, MAF, DBW, rev-limit or transmission-torque development is
authorized until diagnostic residency/context and bench gates are crossed.
''',encoding='utf-8')
    marker='## M0.7 final offline residency review'
    for filename,text in [('DECISIONS.md',f'''{marker}
Prefer stock native-A8 host observations: zero new ECU code/RAM. Preserve frozen
M0/M0.6. Custom research protocols use100/148 bytes and host-only predicates;
existing OEM TX progress suppresses discarded refill reads. Two executable
replacements yield162 conditional bytes but0 accepted ownership. Caller-directed
boot execution and incomplete internal-consumer/context contracts remain FAIL;
do not infer universal safety from direct-xref scans or semantic test counts.
ECUFlash exact Read/kernel/cleanup remains unresolved despite bounded static
protector recovery. A0 attestation remains withdrawn. No physical procedure or
active-control feature approved. Review manifest:{delivery_sha}.
'''),('SESSION_LOG.md',f'''{marker}
{stamp}, session {SESSION}. Host service15 groups and8+8 captures pass.
Compiled raw100/148-byte protocols, scoped division/range structural equivalence,
ABI/CFG and native stock-v-research wire evidence preserved. Fresh functional
build bytes/inverse/native checksums pass. IDB comments only after backup,
official save/close; helper stopped. Frozen211 M06 and1522 M0 files verified.
ECUFlash/provider never run; no hardware action. Final residency0 owned bytes;
162 conditional. Delivery:{DELIVERY}; {len(files)} files, manifest:{delivery_sha}.
''')]:
        p=STATE/filename;old=p.read_text(encoding='utf-8-sig')
        assert marker not in old,'State milestone already recorded; review before rerun'
        p.write_text(old+'\n\n'+text,encoding='utf-8')
    symbols=json.loads((STATE/'SYMBOLS.json').read_text(encoding='utf-8-sig'))
    symbols['M07_research_ledger']={'scope':'Qualified evidence, not generated addresses or ownership acceptance',
        'evidence':'reports/local/m07_residency/OWNERSHIP_FRAGMENTS.json',
        'division':{'entry':'0x4260','candidate_tail':['0x42A4','0x430A'],'conditional_bytes':102,'owned_bytes':0},
        'range_switch':{'entry':'0x1466E','changed_start':'0x1473C','candidate_tail':['0x14770','0x147AC'],'conditional_bytes':60,'owned_bytes':0},
        'default_live_path':'0x484B0; project extension point, not unused code',
        'caller_directed_boot_target':'0x0042 JMP @R4; incomplete admissible target restriction',
        'IDA_metadata_report':'reports/local/m07_residency/ida/M07_METADATA_WRITES.json',
        'host_observation_addresses':['0xFFFF4C75','0xFFFF4C8D','0xFFFF4CA1','0xFFFF4C50','0xFFFF4BC1','0xFFFF4BC2']}
    (STATE/'SYMBOLS.json').write_text(json.dumps(symbols,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS_STATE_UPDATED','delivery_manifest_sha256':delivery_sha,'files':len(files)}))
if __name__=='__main__':main()
