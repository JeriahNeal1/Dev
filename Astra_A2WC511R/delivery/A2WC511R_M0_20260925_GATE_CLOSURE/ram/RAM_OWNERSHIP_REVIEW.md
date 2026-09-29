# A2WC511R M0 RAM ownership gate

**Exclusive ownership: FAIL TO ESTABLISH. Identified reset, DMA, shared-stack and timer paths: PASS within the stated scope. Physical ECU validation: NOT PERFORMED.**

This report does not authorize a flashable image, active controls, or a claim that FFFF7400 is free RAM. The frozen `m0_final_05` build and original ROM/IDB were not changed. The required persistent allocation is exactly 32 bytes, `[FFFF7400,FFFF7420)`. No larger MerpMod RAM allocation is implied.

## Inputs and reproduction

- Immutable baseline: `C:\Dev\SubaruRoms\OEM\A2WC511R.bin`, SHA-256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`.
- Frozen payload: `work/builds/m0_final_05/m0.EXPERIMENTAL_UNAPPROVED.code.bin`, SHA-256 `b5004baa2863bf571eb1ab014f93f0316b3500c5b154e47de2e42f904234b2ff`; manifest RAM32/base7400 are checked by the script.
- Root's read-only IDA exports: `../ida/defined_code_export.json` and `../ida/raw_decodable_code.json`. All defined code words match the baseline. Defined IDA code covers only about 23.2% of the conservative executable envelope; this is not whole-ROM analysis coverage.
- `ram_static_inventory.py` writes the complete literal/xref search inventory. `ram_path_audit.py` derives actual PC-relative loads, checks the cited instructions/tables, runs bounds regressions and writes `ram_path_audit.json` plus 18 disassembly windows. The disassembler is the installed KPIT SH toolchain with `-m sh2e -EB`.

Run from `C:\Dev`:

```powershell
& 'C:\Program Files\Python314\python.exe' 'C:\Dev\Astra_A2WC511R\reports\local\gate_closure\ram\ram_static_inventory.py'
& 'C:\Program Files\Python314\python.exe' 'C:\Dev\Astra_A2WC511R\reports\local\gate_closure\ram\ram_path_audit.py'
```

The path audit passes 65,536 combinations of unconstrained byte indices for the identified asynchronous DMA source/destination arithmetic, every 65,536-state timer counter value, precise copy-dispatch target checks, and two negative copy-contract mutations. These are extraction/arithmetic regressions. Actual instruction execution is independently recorded in `../runtime/20260925T211558.608898Z_gate_closure_runtime/`.

## What is established

| Path | Exact evidence and resulting bound | Candidate effect |
|---|---|---|
| Required state | Frozen linked implementation/manifest allocates 32 bytes; earlier exact-code execution records writes through offset 31 | No additional persistent space requested |
| Direct references | Whole 1 MiB byte-aligned32-bit literal scan, aligned PC-relative word/long loads and defined IDA xrefs find no direct reference in `[FFFF7400,FFFF7420)` | Negative search evidence only |
| Highest ordinary scalar literal | FFFF736C writes at 71CA0/71CC4/71CE4 are byte stores; highest observed end 736D | Does not overlap; the 147-byte gap is not an allocation certificate |
| Boot pattern test | FA58 called by F928 with FFF4/FFF8 bounds; independent simulator executes 0x24BF longwords | Writes both 5AA5A55A and A55A5AA5 through the complete candidate |
| Boot DMA clear | F9BC programs DMA0 source fixed/destination increment/longword, TCR0=0x24BF | Clears `[FFFF2D00,FFFFBFFC)`, including all 32 bytes |
| Runtime asynchronous RX | C31E..C376 programs DMA3 destination 315A+2*(u8)[31AE], two byte transfers | Conservative span `[FFFF315A,FFFF335A)` excludes candidate |
| Runtime asynchronous TX | Same setup programs DMA2 source 310A+40*(u8)[31AC]+2*(u8)[31AE]; destination SCI1 transmit | Even unconstrained byte indices give source span `[FFFF310A,FFFF5AE2)`; no candidate read/write |
| Synchronous SCI DMA | Only identified C5CA caller 45D3A supplies TX 6368, RX 6390, count 20; each iteration transfers two bytes | TX `[FFFF6368,FFFF6390)`, RX `[FFFF6390,FFFF63B8)` |
| DMA fault/interrupt handling | 53A6/53B4/53F4/5404 clear channel TE;530A writes DMAOR | Identified handlers do not introduce a new DMA destination |
| Runtime task stack | ROM 4880 contains FFFF119C;3FF8 initializes context SP12BC;3966 saves predecessor SP in task state + 4;3DF8 saves preempted SP;3F62 restores it | Shared descending task stack is below 119C under valid context invariants;11E4 is task 9 state, not a stack base |
| Temporary boot stack | 4BB8 stores old SP at BFF8 and changes SP there; F928's switched interval calls leaf FA58 and D1AC with 12-byte frame and leaf helpers | Identified temporary stack writes `[FFFFBFEC,FFFFBFFC)`, then 4BBE restores old SP |
| Upper boot ring | 04F4/0540 use B4E0+8*(u16 index);0564 initializes indices; producer/consumer wrap at 100 | Nominal ring `[FFFFB4E0,FFFFB800)`; B4E0 is not an observed SP |
| Hardware RAM alias | SH7058 RAMER remaps physical `[FFFF0000,FFFF1000)`; candidate is elsewhere;51DC disables RAMER | Candidate is outside this hardware alias |

The simulator independently passed actual FA58 full-span, empty, reversed, single-word and injected corruption cases. Both boundary sentinels 2CFC and BFFC stayed intact. Actual C31E..C376 setup execution covers 80 index combinations and four detailed corner traces; it does not emulate a DMA engine or accept arbitrary MMIO. Its 1,024 stock/wrapper comparisons also check declared RAM/code-hole watchpoints within their executed paths.

Boot clearing is compatible with lazy initialization only because the diagnostic hook runs after the boot stage in the identified path. The state cannot be advertised as retained across resets. A cookie that survives a reset path can preserve software counters; publication sequence is a software counter, not a TCU heartbeat. Counter wrap, coherent-reader checks and first-observation reconstruction caveats in the frozen build remain applicable.

## New task 9 activation evidence

Descriptor 4968 identifies task 9, state FFFF11E4, entry 6580, priority 2 and initial activation capacity 2. D3EC calls 3A28 with task ID 9. Its only raw pointer is callback-table entry 101A4, index 2 of the table at 1019C.

CMT1 handler 5EA0 clears CMF at FFFFF718 and jumps to D936. D936 always invokes callback index 0; it increments byte 31F2, and on an odd result increments word 31F0. It then chooses the first set bit through the fixed index map `[1,2,4,5,6,7,8,9,10]`. Callback index 2 therefore fires when the incremented word modulo 4 equals 2: once every 8 D936 service calls, initially calls 3, 11, 19,... from zero. The alternative table dispatches at DABA and DBF0 have fixed indices 21 and 23, so they do not call task 9.

D904/D922 program CMT1 divider 8 and compare 2499. The manual's compare timing yields 20,000 peripheral-clock periods per interrupt and 160,000 per nominal task 9 enqueue. Absolute board clock, interrupt latency and task completion deadline are not established. Pending activations can cause delayed/back-to-back work, so enqueue cadence is not a guaranteed observer sampling period.

At 3BCC/3BCE, incoming priority 2 does not request an immediate context switch if the current priority is 2 or higher;3A28 follows the no-switch path when enqueue returns 0. Before an ordinary preemptive dispatch, 3DC8 sets the previous task's state 4. Dispatcher 3930 starts a task entry only when state is0; nonzero state follows a context-restore table. These are useful reentry guards, but the complete interrupt/context invariant is still a separate software proof obligation. The independent nested-writer negative test fails coherent publication as expected; that assumption must not be silently promoted to a guarantee.

## Additional indirect control closure

The generic copy jump at 43E8 is bounded by the unsigned size check at 43DE..43E2. Sizes above 64 take 447C. Valid aligned sizes 0..64 select 17 entries at 4438..447B, exactly 4432, 442E, ... 43F2. Each entry performs the expected descending longword copies and joins the common return. Misaligned table loads fault rather than supply another architecturally valid target. The regression rejects an enlarged bound and a table entry redirected to E1000. This closes the control targets at 43E8; it does not establish ownership of caller-supplied destination memory.

## What remains software-incomplete

Root's `../rom/reachability.json` still records 94 unresolved transfers for the known-function-root closure. Broader PC-pointer seeding has additional undecodable and indirect frontiers. These include calibration/helper dispatch, boot transfers and scheduler context paths. Literal scanning and the identified DMA/register paths do not exhaust arbitrary CPU base+offset writes, pointer values loaded from RAM, all boot/programming paths, or every interrupt interleaving.

The related local A2WC510S target header has the same 7400/E1000 hole constants, but a different calibration and ECU identifier. Its SHA-256 is `894ab81a6f6930450dab88d74e649c037c0cbcc9159053ad048c6bee34ca54af`. This supports the origin of the candidate, not target ownership. No better location is justified: moving the state elsewhere in the unproven gap would move the same missing proof.

Installed RomRaider's host protocol supports B0/B8 RAM-write commands as well as A0/A8 reads. That does not prove which writes this OEM ECU accepts or their permitted ranges. No command was sent to an ECU. The virtual logger backend's write rejection cannot certify OEM diagnostic-service ownership.

## Smallest physical observation, separate from the software gap

After the remaining software ownership/context review, a controlled bench validation can concentrate on the 32-byte candidate and its boundaries: observe accesses/writer PCs after the known boot clear and first initialization, across the actual task/interrupt/CAN modes being qualified; confirm that subsequent candidate writes come only from the exact observer/init code. Observe cold and warm-reset transitions and actual shared-stack high-water/interrupt nesting during the same run. Compare observed DMA register destinations and timer service intervals with the precise bounds above.

A passing finite observation supports the exercised modes; it does not eliminate unresolved software paths. It must not be used to relabel this report's exclusive-ownership gate as PASS. No physical action, live RAM mutation, bus traffic, flash or active control was performed by this investigation.

Primary hardware reference: [SH7058 hardware manual, REJ09B0046-0300H Rev.3.00](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual), sections 9.2.2, 10.2, 14.2/14.4 and 24.1/24.2. All firmware addresses and behavior above are derived from the local immutable ROM and saved IDA exports.
