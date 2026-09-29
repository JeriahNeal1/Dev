# Runtime source addendum

This addendum links the completed RAM/RTOS investigation to immutable run `20260925T211558.608898Z_gate_closure_runtime`. Its 52 tests and 1,024 differential pairs remain valid; simulator code and frozen final05 payload are unchanged after that run.

Pinned source: `../ram/ram_path_audit.json`, SHA-256 `f9160fbb359508181a6cdbbd9e44a71236345742b2e6a7d01190206fdedecea5`. Reproduction and independent gate classification are in `../ram/ram_path_audit.py`, `../ram/RAM_OWNERSHIP_REVIEW.md`, and `../ram/ram_gate_status.json`.

The identified normal path uses CMT1 with peripheral clock divided by eight and compare register 2499. The documented next-clock compare behavior gives 20,000 peripheral clocks per timer invocation. The software scheduler selects task 9 every eight such invocations, first at invocation three from zero state: 160,000 peripheral clocks per normal enqueue. This is an enqueue period under the decoded configuration, not a measured completion interval. **Identified software cadence arithmetic: PASS. Absolute cadence and deadline margin: PHYSICAL/BENCH REQUIRED.**

The enqueue priority comparison at `3BCC` does not request immediate dispatch for incoming priority two while current priority is at least two. The task-state path also distinguishes initial dispatch from resumption. These are scoped static guards; a complete invariant over every valid context, interrupt and alternative dispatcher has not been established. The explicit nested-writer negative fixture remains relevant: the observer itself cannot safely publish under reentry. **Unconditional observer reentrancy: FAIL. Actual task reentry exclusion and full context stack margin: PHYSICAL/BENCH REQUIRED.**

The shared descending stack starts at `FFFF119C`; `FFFF11E4` is the task-state address rather than a stack base. This helps bound identified normal paths but does not accept exclusive state ownership. The actual FA58 reset test overwrites `FFFF7400..741F`, and the finite DMA setup regression establishes only the decoded ordinary buffer bounds. **Identified routine regressions: PASS. Exclusive RAM ownership remains the separate RAM gate.**
