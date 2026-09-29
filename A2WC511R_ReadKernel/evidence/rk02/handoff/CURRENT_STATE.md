# Finalized installed ECUFlash dynamic qualification

The next rational action is **A: offline acquisition-contract work, not the vehicle connection**. Installed ECUFlash1.44.4870 sti05 Read completed through isolated fake J2534. Two final clean processes reproduce ordered TX, captured kernel, full baseline byte coverage and native saved output. Twelve fault cases are reconciled across native/server journals.

Actual installed Read is **not unconditionally byte-exact**: a nonblank4KiB page with the CRC of an FF page is synthesized asFF, losing37bytes despite SUCCESS. Historical gaps are conditionally read, not fixed masks. A fixed raw03 virtual supplement recovers every byte but does not change the installed Read result or qualify hardware.

DUAL1.07 is4660bytes, SHA256 b0989858ec59c7c281c1368d956a7187b353454683b248be5f1739c86835b082, upload[FFFF3000,FFFF4234). Stock checksum low16 is5AA5. Conditional postACK handoff: entryFFFF3004,SPFFFFBFA0. Fresh disposable IDA/Diaphora and focused simulator evidence remain separate from the canonicalIDB. Kernel readsFFFF5444 without initializing it; zero-selector startup writes prohibitedSH7058 addressFFFFE803. Startup remains unqualified.

Captured Read sends no flash-control20..25 or CPUreset/exit command. Adapter Disconnect/Close does not prove OEM restart; successGUI requests ignitionoff. Actual OpenPort/electrical/ECUacceptance/reset is PHYSICAL_REQUIRED. No physicalprovider, vehicle operation, newECU image or activecontrol work occurred.

Read reports/local/ecuflash_dynamic/READ_QUALIFICATION.md, QUALIFICATION_SUMMARY.json, ENGINEERING_GATES.json and read_audit/FINAL_AUDIT_INDEX.md. Harness/removal instructions: integrations/ecuflash_virtual/README.md. Earlier prehardware gates remain frozen and are superseded for current decisions.

Host-native fixedBF/A8 remains supported; residency frozen with0ownedbytes. Canonical recoveredIDB, damagedIDB evidence, frozenM0/M06/M07, existingDiaphora/boot/host tools and realOpenPort installation verify unchanged across3090protectedfiles.31unqualified functions stay withheld.

Preservation incident: discovery_002 causedECUFlash to rotate7oldlogs before completeQtAppData isolation.3exact originals, includingbothhistoricalReadlogs, were restored;4remainunrecovered. All laterRead runs isolated. Evidence: backups/ecuflash_dynamic_20260926/recovered_logs. UniversalpreservationPASS is not claimed.
