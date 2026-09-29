# Decisions
- Current architecture: OEM A2WC511R firmware as foundation; retain stock feedback and original exhaust/O2 setup.
- Source port from the observed MerpMod revision, not a downloaded Gratis/prebuilt image for a different CALID.
- First runnable modification, if/when approved, is diagnostic-only. No actuator changes in that stage.
- Keep original evidence, even when incorrect, but quarantine old templates/tune proposals.
- Target/current nibble meaning is strongly supported; exact mechanical engagement and freshness remain distinct questions.
- Do not certify `4CA1` as global validity from its name or a normal drive. Earlier promotion was too strong.
- Manual IDA saves, durable scripts/reports, read-only MCP first. No full arbitrary desktop/ECU write automation.
- No automated public repo push, no license redistribution, no silent toolchain upgrade.

## v2 integration decisions
- Replace custom IDA MCP with one existing official vendor MCP; community alternative only if deliberately selected for a recorded compatibility reason.
- Use the actual RomRaider native model rather than independent table encoding or GUI-coordinate automation.
- Broad table access does not imply all values have a inferable optimum. Proposals retain calculation provenance and leave unsupported/evidence-poor cells untouched.
- Editor buffer, saved file, checksum-corrected file and physically flashed image are separate states with separate hashes.
- Batch commits are operator-confirmed in the editor; no per-cell typing, automatic flash or live ECU writes.


## v3 current user authorization and objective
C:\Dev is the root; use native Codex CLI on LTSC, locally advertised Astra/Ultra, full host development/install permissions after backups, no repeated permission queries. Complete all feasible offline phases in one coherent run; physical actions remain manual. Actual uploaded audit supersedes old baseline/source unknowns. No guaranteed first-flash success is claimed.

- Main run 01a0da26: use only official Hex-Rays MCP, installed side-by-side and bound to loopback. Existing IDB is the stamp variant; compile/patch baseline remains separately hashed.
- Diagnostic hook candidate is the sole packed-decoder pointer at11ADC, preserving OEM execution. Experimental linkage can support simulator/static review while all allocation/stack/cadence gates stay explicit; no promotion to flash review on absence of literals.

- Final main run: freeze m0_final_05/repeat06; diagnostic-only OEM-first packed decoder hook; no legacy active module closure. Preserve raw and checksum-corrected artifacts separately.
- Code868 bytes, state32 bytes and124 extra stack are compiled/measured facts, not allocation or task-budget acceptance. Experiment remains nonflashable with explicit blocker graph.
- Current ECU calibration is not inferred from Desktop filenames or baseline checksum validity. No new road/fault-driving test is requested by this software milestone.
- Native RomRaider confirmations retained. SharpTune scoped offline opt-in is separately restricted to the experimental identity/build/root; original exe and settings retained.


2026-09-25T21:50:22.855972+00:00 M0 gate closure: retain exact final05 bytes. ROM/RAM exclusive ownership and OEM single-writer proof remainFAIL; no relocation justified. PASS applies only to stated evidence scopes. Silicon timing/currentROM/TCU fault behavior remainPHYSICAL/BENCH REQUIRED. Actual nativeRR GUI/editor/logger and isolatedSSM validation complete; pure-read future collector prepared without executing hardware. Current-calibration build-procedure prerequisite not met. New package C:\Dev\Astra_A2WC511R\delivery\A2WC511R_M0_20260925_GATE_CLOSURE_v2.


## M0.7 final offline residency review
Prefer stock native-A8 host observations: zero new ECU code/RAM. Preserve frozen
M0/M0.6. Custom research protocols use100/148 bytes and host-only predicates;
existing OEM TX progress suppresses discarded refill reads. Two executable
replacements yield162 conditional bytes but0 accepted ownership. Caller-directed
boot execution and incomplete internal-consumer/context contracts remain FAIL;
do not infer universal safety from direct-xref scans or semantic test counts.
ECUFlash exact Read/kernel/cleanup remains unresolved despite bounded static
protector recovery. A0 attestation remains withdrawn. No physical procedure or
active-control feature approved. Review manifest:511377781e94b712297deb1e4a5a477ec494c13175c904b491c09f58cb0534b3.

2026-09-26T09:23:13.532019+00:00 Diaphora comparative closure:12,431correspondence rows/12pairs; independentrow/hash reviewPASS. FourarchivedMerpModliteralhooks/nineinsertedfunctions/120BcompiledRAM established; range190instructionbytesandthreeproposalsrejectedsafetransplant. ZeroownedROMbytes; freezeECUresidentbranch, noM08build, host-nativeA8supported. Qualifiedhealthy913-functionIDBrecoverycandidatepreparedandcompared;31unqualifiedfunctiondefinitionswithheld;authorityunchanged. FrozenhashesPASS. reports/local/diaphora/DELIVERABLES.md andENGINEERING_GATES.json arecurrent.


2026-09-26 — Qualified recovery promoted as a new canonical file; damaged IDB and31 unqualified function definitions retained as evidence. Host-native A8 remains supported; current task may add prehardware host tests only. No real J2534 provider loaded.


2026-09-26 — Prehardware qualification complete with open gates. DecisionA: exact installedRead software qualification before onecombined acquisition. IDB promoted undernewfilename; BF/A8 fixed-read backend16groups/boot64checks/validator42groups accepted offline. StockCONDITIONAL/M07FAIL; no physicalprovider/flash/activecontrol. All pinned preservation checks pass. See reports/local/prehardware/REPORT.md.


## ECUFLASH_DYNAMIC_READ_CHARACTERIZED_EXACTNESS_REJECTED

InstalledRead is characterized through actual kernel extraction, two final repeat runs and twelve fault/cleanup captures. Its CRC constant-page substitution loses37bytes in a successful native save; exactness remainsFAIL. Virtual fixedraw03 recovery proves a minimal lossless extension, not physical acceptance. KernelFFFF5444/prohibitedE803 startup and OEMreset remain unqualified. No acquisitionconnection released; hostBF/A8 supported, residentbranch frozen. Preserve7-log rotation incident:3exact restored,4unrecovered.
