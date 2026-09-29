# Independent ROM and calibration review

Review completed against the pinned sources in `independent_review.json`. The root agent fixed all three concrete issues raised during review: backward constants now stop at incoming joins and implicit pointer updates; ordinary-entry visitation is separate from delay-slot accounting; the completed rolling-checksum guard case now executes up to the finishing-helper boundary instead of skipping the scenario.

`../rom/test_analysis.py` extracts the actual reachability function bodies without rerunning or overwriting the full-ROM analysis. Four tests pass: a delay-slot address entered normally, a branch that skips a pointer load, implicit predecrement/postincrement pointer changes, and an unchanged straight-line positive control. The SH-2E interpreter independently confirms the delayed-branch execution sequence. `../rom/analysis_regression.json` pins the tested source and test hashes.

The 22 actual-ROM checksum/range scenarios remain appropriately limited: the completed guard stops before unsupported FPU work; the additive checksum tests execute bounded chunks rather than full reset or peripheral behavior. The mutated exclusive-bound test demonstrates that the whole-hole watchpoint detects an actual read when the bound is wrong.

The whole-hole scans include byte-unaligned 32-bit values, even-word PC-relative pools and direct branches, loaded-definition extents, and a limited immediate-construction search. Those are useful positive searches. Unresolved indirect targets, computed data access, unexplored instruction semantics and undocumented definitions prevent an exclusive-ownership theorem. The updated reachability description correctly calls the graph exploratory. **Exclusive ROM allocation: FAIL.**

The calibration inventory distinguishes 17 hashes across 73 discovered candidates, and the recorded historical flash has one candidate matching all 16 logged CRC pages. It correctly leaves current ECU identity unset: the historical CRC log neither provides cryptographic byte identity nor excludes later writes. Missing roots and the one denied temporary directory are visible in the inventory. **Current flashed calibration identity: PHYSICAL/BENCH REQUIRED.**

Reproduce the focused analysis checks with `py -3.14 C:\Dev\Astra_A2WC511R\reports\local\gate_closure\rom\test_analysis.py`. This review changed no frozen M0 payload, original evidence, release state or active control code.
