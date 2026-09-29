# Final M0 engineering decisions

**Review completed: 12 PASS, 4 FAIL, 5 PHYSICAL/BENCH REQUIRED. The frozen diagnostic-only artifact remains unapproved for installation.** These decisions supersede the historical gate labels inside the original experimental delivery. [ENGINEERING_GATES.json](ENGINEERING_GATES.json) binds each decision to evidence hashes and records its dependencies.

| Gate | Status | Scope or remaining requirement |
|---|---|---|
| FROZEN_BUILD_PROVENANCE | PASS | Original 625-file manifest, staged M0 source and final compiler outputs remain unchanged. |
| ROM_IDENTIFIED_ACCESS_PATHS | PASS | Entire surrounding FF runs, vectors, checksums, definitions, related maps and bounded reader paths reviewed. |
| ROM_OWNERSHIP | FAIL | Neither E1000 nor the alternate run has an exclusive-ownership proof; remaining computed control/data paths are not bounded. No collision is claimed. |
| RAM_IDENTIFIED_ACCESS_PATHS | PASS | Exact 32-byte requirement and identified reset, DMA, stack, alias, ring and timer footprints established within their stated contracts. |
| RAM_OWNERSHIP | FAIL | Remaining indirect CPU access and context invariants prevent lifetime-ownership approval of FFFF7400..FFFF741F. No better allocation is proved. |
| INJECTED_ABI_AND_STACK | PASS | Complete injected call graph; exact 124-byte extra stack peak; balanced frames and preservation of the OEM return state; no FPU state touched. |
| OEM_SINGLE_WRITER_INVARIANT | FAIL | Deliberate nested execution breaks publication. Identified scheduler guards do not yet prove the complete nonreentrancy invariant. |
| INSTRUCTION_BUDGET_AND_CADENCE_MODEL | PASS | Conservative full-hook bound of 562 instructions and 178 data accesses; nominal enqueue cadence derived. Cycle model is conditional on explicit hardware parameters. |
| TASK_STACK_TIMING | PHYSICAL/BENCH REQUIRED | Measure actual clock, memory stalls, interrupt interference, scheduling and total stack occupancy after software prerequisites close. |
| SIMULATOR_REVERSE_ENGINEERING_UTILITY | PASS | Watchpoints, address/value origins, deterministic replay and differential execution; 52 tests and 1,024 stock/patch pairs pass. |
| LOCAL_CALIBRATION_SEARCH | PASS | 93 image paths, 18 hashes, all readable requested roots and historical flash-page comparisons. |
| CURRENT_CALIBRATION | PHYSICAL/BENCH REQUIRED | The unique historical CRC match does not establish the current flash. Obtain a fresh full image with the prepared collector. |
| TCU_VALIDITY_SEMANTICS | PHYSICAL/BENCH REQUIRED | Collect the six raw channels with startup/communication-state labels; normal traces alone cannot prove fault freshness or physical engagement. |
| NATIVE_ROMRAIDER_GUI | PASS | Installed editor's actual confirmation, display, cancel, stale rejection, undo, deadline, Save As and reopen workflows on disposable images. |
| NATIVE_ROMRAIDER_HTTP_TRANSPORT | PASS | Persistent loopback connection fixed repeat-request resets; no automatic replay of uncertain mutations. |
| VIRTUAL_NATIVE_SSM | PASS | 8,599 native protocol/definition checks against compiled snapshots and full virtual ROM reconstruction. |
| NATIVE_VIRTUAL_LOGGER_GUI | PASS | 300 displayed values and all 6,667 native CSV rows match compiled simulator snapshots. |
| READ_ONLY_COLLECTOR_OFFLINE | PASS | Exact sealed launcher, two full virtual ROM reads, 260 six-channel samples and 285 independent command-policy checks. |
| READ_ONLY_COLLECTOR_PHYSICAL | PHYSICAL/BENCH REQUIRED | Actual provider/device behavior and OEM A0 full-ROM access have not been exercised. |
| PHYSICAL_TEST_CANDIDATE | FAIL | Blocked by ownership, single-writer, current-image and timing prerequisites. |
| VEHICLE_VALIDATED | PHYSICAL/BENCH REQUIRED | No physical connection, flash or vehicle validation occurred. |

PASS applies to each stated scope. Finite simulation or bench observations do not prove that unexecuted OEM code cannot access a proposed allocation. The remaining software proof failures are not relabelled as hardware-only gates.

The [one-connection read-only acquisition procedure](calibration/ONE_CONNECTION_READ_ONLY_ACQUISITION.md) is prepared for a future human-run collection. Its physical mode was not executed. The user's prerequisite for preparing a current-calibration-ready M0 build procedure was not met, so no such build procedure was prepared. Firmware and calibration controls remain unchanged.

Automatic approval review rejected an optional project-local junction-creation regression before execution. The collector's reparse-point guard was inspected, but an actual junction probe was not run. Hidden-file rejection and the real sealed inventory checks passed; the limitation is retained in the interface report and gate JSON.
