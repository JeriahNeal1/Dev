# Independent validator review

The reviewed checker is preserved as `validate_reviewed.py`, SHA256 `09fc2641e59c1a9573d5b916dbc6700fb95693dd5180b9510e67129c9a7c462c`. `reproduce.py` constructs two deliberately invalid evidence-selection indexes in memory. It leaves the actual validator, release index, kernel and execution reports unchanged. Both invalid selections currently return software PASS; exact results are in `REPRODUCTION.json`.

The direct comparison of each retained output with a full 1 MiB fixture is correct. The compiled opcode/layout check also pins the actual kernel and verifies the 319 instruction words. The gaps are in connecting those facts to the required gate meanings:

1. Each required gate ID accepts arbitrary assertions supplied by the index. All eight IDs can point to an unrelated `FAULTS.schema == 1` assertion. Fix required gate report/field/value semantics in the checker or a separately pinned registry.
2. The names stock/composite/random can all reference the same stock fixture and same two output files. Bind fixture identities to the stock SHA and independently pinned deterministic fixture manifest; require distinct fixture hashes.
3. Aggregate coverage does not bind its kernel SHA to the pinned kernel or reconstruct its counters from sealed input coverage reports. A report with a zero kernel hash still passes. Recompute counts, edges and writes from the declared sealed inputs and check each source's identity.
4. An empty observed-write list passes vacuously. The invalid test replaces all writes with an empty list. Recomputing the aggregate and requiring the known mandatory stores prevents this loss of evidence.
5. Any nonempty text can classify an actual instruction as unreachable. The test removes the entry instruction `FFFF3004` from execution counts and supplies an arbitrary proof string. This frozen kernel has all 319 instructions executed, so no unreachable exceptions are needed for this release.

These are negative tests of the review snapshot, not evidence that the actual compiled kernel or legitimate completed simulator runs failed. The root agent owns changes and independent retesting of the final checker. No provider was loaded and no physical operation occurred.
