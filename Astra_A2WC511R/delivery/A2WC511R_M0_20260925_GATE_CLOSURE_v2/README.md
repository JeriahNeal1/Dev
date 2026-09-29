# A2WC511R M0 offline gate-closure evidence

This run continued the frozen diagnostic-only `m0_final_05` artifact. It did not rebuild firmware, relocate allocations, develop launch/ALS, flash an ECU, or enable timing, fuel, boost, DBW, rev-limit, MAF or transmission torque changes.

**The artifact remains unapproved for physical installation.** `ENGINEERING_GATES.json` is the current authoritative gate decision file. The prior delivery inside `frozen_candidate` retains its original historical gate file and all625 hash-identical entries; its status is superseded by this package's top-level decisions.

[GATE_DECISIONS.md](GATE_DECISIONS.md) lists all 21 final gates: 12 PASS, 4 FAIL and 5 PHYSICAL/BENCH REQUIRED, with the scope of each result.

| Outcome | Evidence |
|---|---|
| Whole-ROM-hole and bounded reader analysis completed; exclusive ownership failed to be established | `rom/ROM_ALLOCATION_REVIEW.md` |
| Actual32-byte RAM requirement, reset/DMA/stack/cadence paths bounded; exclusive ownership failed to be established | `ram/RAM_OWNERSHIP_REVIEW.md` |
| Complete injected call graph, exact124-byte extra stack and conservative562-instruction full-hook bound | `runtime/20260925T211558.608898Z_gate_closure_runtime/RUNTIME_HANDOFF.md` |
| Remaining OEM single-writer/context invariant not established; silicon timing unmeasured | Same runtime report and `runtime/runtime_source_addendum.md` |
| Installed native RomRaider editor and logger exercised offline; virtual transport and future collector reviewed | `interfaces/INTERFACE_CLOSURE_REVIEW.md` |
| All readable local images/history classified; one unique historical16-pageCRC match; current ECU image still unknown | `calibration/CURRENT_CALIBRATION_REVIEW.md` |
| One future human-operated connection can attempt pure-read SSM ROM acquisition and six raw TCU channels | `calibration/ONE_CONNECTION_READ_ONLY_ACQUISITION.md` |

No better ROM or RAM allocation was proved. Relocating into another unproved hole would not close the gates. The remaining software proof obligations are kept separate from physical observations: finite bench coverage cannot prove that unexecuted firmware never uses an address. The conditional prerequisite for preparing a current-calibration-ready M0 build was therefore not met. No such build is presented as ready.

The simulator passed52 tests covering56 focused instruction forms and1024 stock/patch pairs. Root checksum/range/boundary tests passed22 actual-instruction scenarios across4 groups, including a wrong-bound negative control; four additional CFG analysis regressions passed. The broader project suite passed70 tests after the local RomRaider client transport fix. Individual report files identify their test inputs and limits.

IDA changes were three evidence-qualified comments and the verified checksum-range-validator name only, after a restorable backup. IDB ROM bytes and all firmware files stayed unchanged. IDA was saved and closed through the official Hex-Rays MCP. Loopback transport fixes do not replace the vendor MCP or the real J2534 installation.

Reproduction commands and hashes are in each branch report. `SHA256SUMS.json` verifies this evidence envelope; it does not override an engineering FAIL or count as physical validation. The original M0 source, patch, ELF, disassembly and ROM artifacts are preserved under `frozen_candidate`; new simulator/integration sources and validated local helper classes are included for review.
