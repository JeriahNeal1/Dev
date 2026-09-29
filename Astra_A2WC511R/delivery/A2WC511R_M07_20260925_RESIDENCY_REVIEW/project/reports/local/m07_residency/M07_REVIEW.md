# M0.7: host observations complete; ECU residency not established

M0.7 delivers a supported offline host observation tool and two separately built ECU research protocols. It does **not** deliver an approved ECU-resident diagnostic image. Two OEM executable replacements conditionally save 162 bytes, enough for either measured payload, but zero bytes meet the requested complete ownership standard. Frozen M0 and M0.6 remain unchanged. No physical connection, flash operation, ECUFlash/provider launch, or active-control development occurred.

## Smallest implemented raw-observation protocol

The preferred solution uses the existing OEM A8 request and needs **zero new ECU code or RAM**. A 25-byte request obtains six raw bytes in a 12-byte E8 response. All predicates run on the host. This is also the smallest wire exchange among the implemented six-observation alternatives.

The smallest implemented custom ECU extension is **100 payload bytes**, plus a 12-byte replacement of the live default-command sequence and the 68-byte replacement of the original 170-byte division routine. It accepts one exact BE/version1/page0/address-list request and returns FC with length7 and six raw bytes. Its request/response sizes are also 25/12 bytes. These are measured implementations, not a proof of globally optimal code size.

A two-page alternative uses **148 payload bytes**, fragmented into 88 and60 bytes. Page0 returns FC/length5/four raw bytes; page1 returns FD/length3/two raw bytes. Request sizes are19/13 bytes and responses10/8 bytes:50 total for all observations. The exact echoed request, selected profile, version/page opcode, length, direction and checksum must match. The research decoder rejects a checksum-valid reply from the wrong page or profile. Future incompatible versions must use distinct response discriminators.

Both custom adapters preserve the OEM RX/header/checksum and address-classifier gates and reuse its A8 producer. They clear continuous polling and accept only fixed reviewed address lists. The existing TX progress counter prevents the discarded refill from reading the sources again: actual software-event wire execution observes six, four or two reads as appropriate. No new refill hook, request-buffer mutation, persistent state, interrupt masking or ECU predicate calculation is needed. The new FC/FD protocol uses its separate research codec; ordinary native RomRaider logging stays on A8/E8.

See [protocol specification](protocol/PROTOCOL_TRADEOFFS.md), [codec review](protocol/CODEC_REVIEW.md) and [wire evidence](protocol/execution_01/compiled_protocol_fixtures.json).

## Supported host tool

[The service](../../../integrations/m07/README.md) exposes source `FFFF4C75`, snapshot `FFFF4C8D`, latch `FFFF4CA1`, flags `FFFF4C50`, target `FFFF4BC1` and current `FFFF4BC2`. JSONL retains the six bytes, address mapping, complete frames, UTC/monotonic request/response timestamps, provenance and host predicates. Unknown freshness/coherence stays explicit; host timestamps are not ECU sample timestamps and sequential OEM reads are not an atomic snapshot.

The supported backends are finite deterministic replay and the actual installed RomRaider encoder/parser in an isolated virtual JVM. Fifteen regression groups and eight scenarios through each backend pass. There is one outstanding request, terminal failure on malformed/late replies, no silent replay of exhausted fixtures, exclusive output creation and owned-process cleanup. No physical backend or global provider replacement is present. This meets the current offline reverse-engineering objective; a live adapter remains a separate future implementation and qualification task.

From `C:\Dev`, use a new capture filename:

```powershell
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\capture.py --backend native-virtual --output C:\Dev\Astra_A2WC511R\reports\local\m07_residency\host\my_capture.jsonl
```

## Executable replacements and exact candidate ranges

| OEM object | Original/replacement bytes | Proposed reclaimed tail | Accepted ownership |
|---|---:|---|---|
| Signed division at `4260` |170 /68|`[42A4,430A)`,102 bytes|FAIL;0 accepted|
| Switch within `1466E`, changed at `1473C` |112 /52|`[14770,147AC)`,60 bytes|FAIL;0 accepted|

The division loop projects onto the original32 arithmetic pairs, preserves the T/Q/M behavior and divide-by-zero error write, and returns identical registers under its entry/private-stack contract. Its nonzero path uses12 stack bytes instead of8. The range replacement exhausts the16 nibble partitions and preserves the T predicate under the enclosing routine's `R6=64` contract; arbitrary interior entry with a different R6 has an explicit counterexample. Both implementations preserve SR/PR/SP and GPR results under those contracts, perform no FPU operation, and call no subroutine. Extra private division-stack traffic is recorded, not hidden as equality. Structural proofs supplement1,401 division and1,792 complete range-function differential pairs.

All aligned raw branch/PC-relative encodings were scanned, entry literal callers classified, and manufactured return PCs checked. Four division callers target4260; one range caller targets1466E. No external encoded branch or PC-relative read into the changed spans was found. These bounded facts do not close computed control or internal code-as-data consumers. Ordinary A0/A8 readback showing the new bytes is allowed modified-image behavior and is not itself an ownership failure.

The final target analysis narrows descriptor callbacks and the RTOS indirect path but also identifies a caller-directed boot execution path through0042. The whole-firmware worklist remains incomplete and unknown internal readers/DMA contexts are not excluded. This is a concrete limit of the complete ownership claim, not evidence that ordinary operation enters either tail. Restricting the entry contract silently would not satisfy the requested proof.

The one-page adapter experimentally occupies `[42A4,4308)` and needs only division compression. The two-page matcher occupies `[42A4,42FC)` and its main adapter `[14770,147AC)`. Both replace the default sequence `[484B0,484BC)`. Neither touchesE1000, the setter/getter table representation, or task9 hook pointers. [OWNERSHIP_FRAGMENTS.json](OWNERSHIP_FRAGMENTS.json) records each exact fragment, original/replacement identity, parent object and failed dependencies. No fragment is labeled owned merely because it fits.

[The candidate catalog](CANDIDATE_CATALOG.md) distinguishes the two implemented rewrites from earlier dispatch, duplicate boolean and no-op screening, and from preserved consumers. The small leaves cannot supply the required capacity; the live command handlers cannot simply be discarded. Frozen M0.6 table compaction is retained only for comparison. A broader enumeration of functions or more finite payload examples would not close the remaining calculated-entry and internal-consumer contracts.

## ABI, timing and simulator scope

Each adapter adds an8-byte private frame to the existing28-byte dispatcher frame. The two-page helper uses no additional stack and relies on the unchanged OEM PR save/restore. The complete dispatcher peak is36 bytes; the division replacement's12-byte frame is accounted separately in its callers. These are local compiled-path frame bounds, not a whole-system interrupt/high-water theorem.

The simulator gained bounded semantic contracts, original/replacement register/write/call comparison, structural opcode proofs, abstract/concrete address cross-checks, compiled CFG frame analysis and machine-readable ownership evidence. Its existing watchpoints, propagation, deterministic replay and differential framework remain in use. The strict75-form core is unchanged; unsupported operations and unknown abstract frontiers do not pass by assumption.

Compaction increases existing OEM execution cost even with no project request: the longest tested division path rises from 79 to 210 instructions; the range path rises from 42 to 68. Under the explicitly conditional F=D=2 serialized model, division rises from 478 to 1266 modeled cycles. The two-page adapter bounds are 142/107 instructions for page0/page1 and 136 for rejection, excluding the OEM baseline. All timing reports retain external interference and wait-state assumptions. No number is presented as measured silicon timing. The one-page build avoids the range replacement and its timing cost.

The final one-page CFG proof partitions all requests by their first differing longword, or all six equal. These seven control partitions cover every reachable compiled instruction without adding concrete scenario examples. It bounds acceptance at 61 instructions/25 data accesses and rejection at 53/23, including the default-entry trampoline. Under the same conditional F=D=2 assumptions these are 391/341 cycles, excluding OEM baseline and external interference. It verifies the exact division-only research image, unlike the earlier prototype ABI harness that also carried an unrelated range overlay outside the executed path.

## Artifact and IDA audit

[BUILD_AUDIT.json](build_audit_02/BUILD_AUDIT.json) proves fresh reproduction of all four assembly groups, exact executable bytes, full changed-byte classification, raw and checksum-corrected inverse restoration to stock, and agreement with the actual installed RomRaider checksum implementation. The range ELF differs only in the STT_FILE absolute object path and dependent string metadata; every other section/symbol/program header matches and the normalized ELF is identical. The failed first strict full-ELF comparison is retained rather than erased.

The two checksum-corrected research images are:

- One page: `140736b11e14ed80290832ceef3ae67757f967a3751a6ddb2b6d8afa0cc9afbd`.
- Two pages: `17ce75b3514891f2c5c30f0ec10bc5b4e3bf50b9004959fd906c600f7fb8797e`.

Both filenames say `RESEARCH_NOT_RESIDENCY_PROVEN`; a correct checksum does not approve either image. The stock baseline is `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`, not the identified current vehicle calibration.

The existing official IDA database was backed up, read, annotated with three qualified research comments, saved and closed. Its mapped ROM bytes remain the original stamp variant; no instruction bytes, functions or names were rewritten. IDA evidence and saved database identity are under `ida/`. All211 frozen M0.6 files and1,522 original M0 delivery entries verify unchanged.

## ECUFlash Read and eventual one-connection acquisition

[The installed Read audit](ecuflash_read/ECUFLASH_READ_AUDIT.md) identifies the signed host binary, target definitions and historical DUAL V1.07 kernel workflow. Historical uploads changed4,660 RAM bytes at `[FFFF3000,FFFF4234)`; the complete kernel RAM/MMIO footprint and cleanup are still unknown. Read logs cover614,400 ROM bytes, with434,176 bytes in `[86000,C0000)` and `[CF000,FF000)` lacking explicit read-area evidence. FF-filled saved gaps do not prove live byte identity. Flash enable/erase/commit appear in a separate Write log but not the two Read logs; that is not a complete Read-path flash-exclusion proof.

Static analysis identified Themida and recovered4.17MB of protector data with independently matched decompression and another loader layer. It still did not recover the exact installed kernel or application Read/cleanup control flow. The source-available reference kernel has separately proved RAM-clearing effects, including the six observation addresses, but is not substituted for the installed DUAL kernel. ECUFlash and its provider were never executed.

The previous A0 full-image attestation remains withdrawn. No executable replacement acquisition procedure is warranted yet. The minimal eventual ordering is: six timestamped raw observations while OEM firmware runs; close the logger; perform only a separately qualified exact-ROM Read with explicit coverage and kernel identity; apply its proven human-operated exit/reset; re-establish OEM identity before any post-kernel observations. The audit contains the precise dependencies. No additional passive channel is required, and the frozen collector has not been altered or reauthorized.

## Remaining gates

[ENGINEERING_GATES.json](ENGINEERING_GATES.json) separates three outcomes. Persistent new RAM, a background diagnostic writer, the new single-writer invariant and task9 cadence are eliminated by design. Host service, protocol/ABI contracts, scoped semantic replacements, build/checksum/inverse and preservation pass their stated offline scopes. Complete ECU code ownership, global execution contracts and exact installed Read implementation remain software failures.

Genuine later physical work includes current-ROM identification with a qualified acquisition path; silicon timing of all affected OEM callers and diagnostic transport; interrupt/stack margin, watchdog and peripheral behavior; and live TCU validity/freshness interpretation. Data freshness stays unknown meanwhile and confers no control authority.

**Current-ROM identification and bench timing alone are not enough to make an M0.7 ECU test candidate.** Residency and execution-context contracts must close first. The supported stock-A8 host design already avoids that dependency. No current-calibration patch/flash procedure is issued, and no launch/ALS, timing, fuel, boost, MAF, DBW, rev-limit or transmission-torque changes are enabled.
