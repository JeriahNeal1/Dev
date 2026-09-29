# v3 precedence note

Current host authorization and run order are in `../AGENTS.md`, `../state/RUN_CONTRACT.md` and `CLI_SETUP.md`. Actual uploaded source/binary identities superseding older unknowns are in `DEV_SNAPSHOT_AUDIT.md`. Keep the technical details below, but do not reimpose historical per-action host permission requests or stop after the first milestone. Physical actions remain human-controlled.

---

# Corrections and statements NOT to carry forward as established facts

This document explicitly qualifies earlier conversation claims. Original evidence and terminology are preserved in `evidence/`; this is an engineering review, not a silent rewrite of sources.

## 1. 4CA1 is not proven global freshness
The trace shows set1 at15B66, later testing and clear paths. It also shows the set adjacent to copying4C7F->4C95, a previous-value comparison4CA0 vs4C95, and counters. That can support a monitoring/initialization latch hypothesis, not a universal guarantee that packed gear4C8D was freshly received. `sResetTcuDerivedSnapshot` zeroes4C8D without directly clearingCA1. Full packet/descriptor/error-path analysis is still needed. Keep raw logger values; do not encode `1=safe` or use it as the sole fail-safe. A normal startup/drive/shutdown log cannot by itself prove network-loss coverage.

## 2. 4C50 mask02 is only a known bit test
The helper returns whether the bit is set. Part of the updater gates its monitoring on that condition; the snapshot copy occurs earlier in the visible flow. Therefore 'the whole snapshot updater only runs when this bit is set' is too broad. The source setter, scheduling and all exits must be inspected. A mask of0x02 means bit1, not a numerical boolean equal to1; evaluate `(x & 2) != 0` when analyzing raw bytes.

## 3. Gear is not selector validity, current is not clutch engagement
E8/E9 map Reverse to1. BC1/BC2 map Park8 to0. Packed4C8D retains8/7/0/1..5. The observed upper-before-lower transitions support target/current reported-state labels; they do not prove instantaneous hydraulic completion. `packed==0x11` rejects observed non-first states but can still be stale. Reading source and snapshot in one CSV row is not an atomic ECU snapshot. No 'last driving test' promise removes remaining fault validation.

## 4. The historical HEW build was not successful A2WC511R integration
It actually selected A8DH202X/Gratis_Debug. Link completion and the0Errors banner do not undo the missing-ROM/patch exception in the custom post-build phase. Track compile, link, metadata generation, patch application and definitions as separate exit criteria. MerpMod's default maps are not a tune for this vehicle.

## 5. Version identity is evidence-based
Observed MerpMod8720d20 is supported by the build banner. Observed SharpTunefcf9fdb differs from the starter's ecabea pin. The remote current branch, a proposed setup script and an installed executable can differ. Inspect all three; do not replace local work to make a guessed version match.

## 6. IDA interface mistakes
`ida_kernwin.save_database()` failed. Use manual editor saving. `msg_clear()` only clears output, not Python globals or the IDB. Python helper functions disappear on restart or may not have been executed in snippet scope. Successful forced instruction printing does not define a code head. Persist verified entry/caller instructions before `add_func`/`add_cref`. `XrefsTo` includes data references; print xref type. Use `XREF_USER` for explicitly created user call xrefs where appropriate. Do not decode pointer pools as executable code merely to remove <undecoded> text.

## 7. Memory/architecture
IDA SH4B preset does not make the target SH-4. Confirm SH-2E-compatible code generation. `0xFFF8` and `0xFFFF8` are distinct ROM locations. FF-filled ROM or unreferenced RAM is not sufficient safety proof. `3180E` is a patch marker candidate, not a generic end-of-function. The related-ROM header is a source of hypotheses only.

## 8. Baseline/tune claims
The two archived old ROM reads are not certified OEM. The locally named STOCK_ROMRAIDER image has not been copied into this archive or hashed here. Old R3 timing/POLF tables and anti-lag advice remain historical artifacts, not endorsed values. Fine-learning locked/disabled and unresolved stalls/smoke/boost faults must not be assumed acceptable because the car is track-only.

## 9. Windows/Codex access and continuity
Official Windows docs currently recommend Windows11 and describe fully updated Windows10 as best-effort. Preserve the working Win10 tools, but verify actual Codex permissions/platform support. An installed desktop app does not prove access to all apps, real-time uninterrupted supervision, hardware, or admin surfaces. MCP tool replies expose selected data, not a transparent live desktop. One chat still has context limits; local checkpoints are required.

## 10. Wideband idea deferred
An aftermarket controller is not automatically a more accurate/compatible substitute for the OEM front A/F feedback interface. No external-wideband primary-control patch has been implemented. Retain the present hardware pending a separately validated future design.
