"""Publish completed dynamic evidence; previous checkpoints stay backed up."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import datetime,json,shutil
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'reports/local/ecuflash_dynamic';state=ROOT/'state'
    summary=json.loads((out/'QUALIFICATION_SUMMARY.json').read_text())
    gates=json.loads((out/'ENGINEERING_GATES.json').read_text())
    backup=ROOT/'backups/ecuflash_dynamic_20260926/active_checkpoint_before_finalize'
    backup.mkdir(parents=True,exist_ok=True)
    for name in ('CHECKPOINT.json','CURRENT_STATE.md','NEXT_ACTIONS.md','DECISIONS.md','SESSION_LOG.md'):
        if not (backup/name).exists():shutil.copyfile(state/name,backup/name)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    path=state/'CHECKPOINT.json';d=json.loads(path.read_text())
    d.update(phase=gates['phase'],updated_utc=now,current_task='Completed installed ECUFlash Read qualification; exactness rejected',
        current_evidence='reports/local/ecuflash_dynamic',engineering_gates='reports/local/ecuflash_dynamic/ENGINEERING_GATES.json',
        qualification_summary='reports/local/ecuflash_dynamic/QUALIFICATION_SUMMARY.json',
        next_action=summary['single_smallest_remaining_offline_blocker'],next_rational_action=summary['next_rational_action'],
        B_connection_qualified=False,installed_ECUFlash_dynamic_Read_complete=True,installed_ECUFlash_exact_image_acquisition=False,
        captured_kernel=summary['kernel'],gate_summary=gates['summary'],physical_provider_loaded_this_run=False,physical_validation=False,
        previous_frozen_checkpoint='backups/ecuflash_dynamic_20260926/state/CHECKPOINT.json',
        historical_log_preservation='FAIL_7_ROTATED_3_EXACT_RESTORED_4_UNRECOVERED',
        frozen_preservation_status='PASS',frozen_preservation_mismatches=[])
    path.write_text(json.dumps(d,indent=2)+'\n')
    current='''# Finalized installed ECUFlash dynamic qualification

The next rational action is **A: offline acquisition-contract work, not the vehicle connection**. Installed ECUFlash1.44.4870 sti05 Read completed through isolated fake J2534. Two final clean processes reproduce ordered TX, captured kernel, full baseline byte coverage and native saved output. Twelve fault cases are reconciled across native/server journals.

Actual installed Read is **not unconditionally byte-exact**: a nonblank4KiB page with the CRC of an FF page is synthesized asFF, losing37bytes despite SUCCESS. Historical gaps are conditionally read, not fixed masks. A fixed raw03 virtual supplement recovers every byte but does not change the installed Read result or qualify hardware.

DUAL1.07 is4660bytes, SHA256 b0989858ec59c7c281c1368d956a7187b353454683b248be5f1739c86835b082, upload[FFFF3000,FFFF4234). Stock checksum low16 is5AA5. Conditional postACK handoff: entryFFFF3004,SPFFFFBFA0. Fresh disposable IDA/Diaphora and focused simulator evidence remain separate from the canonicalIDB. Kernel readsFFFF5444 without initializing it; zero-selector startup writes prohibitedSH7058 addressFFFFE803. Startup remains unqualified.

Captured Read sends no flash-control20..25 or CPUreset/exit command. Adapter Disconnect/Close does not prove OEM restart; successGUI requests ignitionoff. Actual OpenPort/electrical/ECUacceptance/reset is PHYSICAL_REQUIRED. No physicalprovider, vehicle operation, newECU image or activecontrol work occurred.

Read reports/local/ecuflash_dynamic/READ_QUALIFICATION.md, QUALIFICATION_SUMMARY.json, ENGINEERING_GATES.json and read_audit/FINAL_AUDIT_INDEX.md. Harness/removal instructions: integrations/ecuflash_virtual/README.md. Earlier prehardware gates remain frozen and are superseded for current decisions.

Host-native fixedBF/A8 remains supported; residency frozen with0ownedbytes. Canonical recoveredIDB, damagedIDB evidence, frozenM0/M06/M07, existingDiaphora/boot/host tools and realOpenPort installation verify unchanged across3090protectedfiles.31unqualified functions stay withheld.

Preservation incident: discovery_002 causedECUFlash to rotate7oldlogs before completeQtAppData isolation.3exact originals, includingbothhistoricalReadlogs, were restored;4remainunrecovered. All laterRead runs isolated. Evidence: backups/ecuflash_dynamic_20260926/recovered_logs. UniversalpreservationPASS is not claimed.
'''
    (state/'CURRENT_STATE.md').write_text(current)
    (state/'NEXT_ACTIONS.md').write_text('''# Next actions after exact-Read rejection

1. Do not repeat setup, ordinary coverage fixtures, sibling searches or residency attempts. The installedCRC-fill shortcut has a captured counterexample; unconditional exactness cannot pass unchanged.
2. Qualify the fixed full-range command03 supplement as the minimum lossless acquisition change. Preserve its narrow protocol; do not expose generic kernel/control methods or loadOpenPort during offline development.
3. The smallest unclosed startup obligation is incomingFFFF5444 and the zero-branch prohibitedFFFFE803 write. Establish a supportedSH7058 entry contract or qualified acquisition kernel. A guessed selector or absence of literalxrefs is insufficient.
4. Keep actual electrical/OpenPort/ECUacceptance/reset/OEMrestart PHYSICAL_REQUIRED. No one-connection procedure is released until software acquisition/startup gates close. CurrentvehicleROM remains unknown.
5. Preserve canonicalIDB/frozenartifacts and supportedBF/A8 backend. No vehicle image or activecontrol. Current evidence: reports/local/ecuflash_dynamic/QUALIFICATION_SUMMARY.json.
''')
    marker='ECUFLASH_DYNAMIC_READ_CHARACTERIZED_EXACTNESS_REJECTED'
    decision='''

## ECUFLASH_DYNAMIC_READ_CHARACTERIZED_EXACTNESS_REJECTED

InstalledRead is characterized through actual kernel extraction, two final repeat runs and twelve fault/cleanup captures. Its CRC constant-page substitution loses37bytes in a successful native save; exactness remainsFAIL. Virtual fixedraw03 recovery proves a minimal lossless extension, not physical acceptance. KernelFFFF5444/prohibitedE803 startup and OEMreset remain unqualified. No acquisitionconnection released; hostBF/A8 supported, residentbranch frozen. Preserve7-log rotation incident:3exact restored,4unrecovered.
'''
    p=state/'DECISIONS.md'
    if marker not in p.read_text(encoding='utf-8-sig'):
        with p.open('a',encoding='utf-8') as f:f.write(decision)
    p=state/'SESSION_LOG.md'
    if marker not in p.read_text(encoding='utf-8-sig'):
        with p.open('a',encoding='utf-8') as f:f.write('\n'+now+' '+marker+' session01a0da26-addc-7fe1-84df-8c0baa8174f8. DUAL1.07 captured; two final native repeats;12faults;37-byte CRC loss and virtualraw recovery; entry3004/SPBFA0/checksum5AA5; unknown5444/prohibitedE803. No physicalprovider/hardware/image.3090protectedfilesverify. reports/local/ecuflash_dynamic holds gates and evidence.\n')
    print(json.dumps({'phase':d['phase'],'decision':summary['decision'],'checkpoint':str(path)}))
if __name__=='__main__':main()
