# M0.7 semantic replacement evidence

These are compiled experiments within existing OEM executable objects. They do not use FF space or the M0.6 compact setter table, and no full ECU ROM was written. The immutable baseline is `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`. The 75-form simulator remains unchanged from `C:/Dev/A2WC511R_Sim/backups/m07_start_75form_20260925/sh2e.py`, SHA-256 `b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff`.

| Candidate | Compiled replacement | Proposed original-code tail | Bytes | Stack change |
| --- | --- | --- | ---: | --- |
| Signed division | `4260..42A3` | `[42A4,430A)` | 102 | 8 to 12 bytes on nonzero path |
| Range switch within function `1466E` | `1473C..1476F` | `[14770,147AC)` | 60 | None |

The combined 162 bytes are proposed savings, not accepted payload residency. The original instruction at `1473A` remains unchanged; the switch replacement starts at the following aligned address. The build rejects an ELF entry that differs from its overlay manifest.

The division replacement uses the original 32 `ROTCL R1; DIV1 R0,R3` pairs in a counted loop. Its `MOVT R4; DT R2; BF/S; SHAR R4` control sequence restores the original T bit after testing the count, without loading SR or changing interrupt masking. R2 returns to zero before the original ADDC. R4 is saved in one additional private stack word and restored. Original R2/R3 save addresses, all final GPRs, SR, PR, MACH/MACL and the divide-by-zero write of `0000044E` at `FFFF130C` remain identical. The additional four-byte stack write/read is explicitly different memory traffic and requires independently established stack space.

The switch replaces repeated comparisons/branches with a sixteen-byte lookup. It preserves the original output and T predicate `(nibble<=8 || nibble==15)`. Its proof uses the enclosing function's unchanged `mov #64,r6` and the unchanged path to `1473A`. It is not equivalent for arbitrary interior entry with R6 unconstrained; a concrete negative control demonstrates that failure. There are no calls in either replacement, and no FPU instructions are reachable.

`semantic_differential.json` records 1,401 original/replacement division pairs and 1,792 complete range-function pairs. It compares all sixteen GPRs, SR/PR/MACH/MACL, return PC, SP, final RAM and ordered RAM/MMIO accesses. Only the additional division stack word is excluded from equality, while its access is still traced. The longest executed nonzero division paths are 79 original versus 210 replacement instructions. Range paths observed at most 68 versus 42 instructions.

`semantic_structural_proof.json` checks the compiled-word projection and the 32-step division induction. The loop scaffold is checked for both T values at every count 1..32. The range proof checks all sixteen nibble partitions, incoming T values and representative high bits, with masking establishing independence of all higher R5 bits. This supports the stated function-entry contracts beyond the sampled quotient values; it does not prove interrupted execution or whole-firmware ownership.

`abstract_concrete_crosscheck.json` has eight explicit stock/replacement execution contracts. Every observed fetch, data address/value and branch target fits the abstract predictions; these contracts complete with zero unknowns. Three controls detect an omitted T save, a corrupt lookup value and insufficient additional stack space. This uses the existing conservative value-set implementation with explicit fixture assumptions; it is not a new whole-firmware acceptance result.

`object_inventory.json` preserves function/chunk metadata, external exported xrefs, defined direct branches, all-offset big-endian pointer matches and defined PC-relative reads. Every defined instruction in the candidate functions matches the immutable baseline even though the IDA export identifies the four-byte stamp variant. Zero pointer matches are not an ownership theorem. Unknown computed entries/readers, generic ROM reads, exception contexts and incomplete defined-code coverage remain unresolved. The parent-owned ownership review extends these scans.

- Scoped semantic equivalence: **PASS**.
- Complete entry/read ownership and payload residency: **FAIL** pending the separate ownership proof.
- Silicon timing, preemption behavior and total stack margin: **PHYSICAL/BENCH REQUIRED**.

The conditional serialized timing envelope remains `5*N + (F-1)*N + (D-1)*A + entry_stalls + external_interference`. With the illustrative assumptions F=D=2, nonzero division changes from 478 to 1266 modeled cycles (79/210 instructions and 4/6 stack accesses). This is an increase of 788 under those assumptions, not verified SH7058 latency. No time-sensitive caller is accepted from that estimate.

Sources are `C:/Dev/Astra_A2WC511R/work/M07/semantic`. ELF, raw replacement sections, maps, commands, disassembly and expected-before bytes are pinned in `candidate_manifest.json`. Reproduction from `C:/Dev/A2WC511R_Sim`:

```powershell
py -3.14 m07_semantic_build.py
py -3.14 m07_semantic.py
py -3.14 m07_semantic_proof.py
py -3.14 m07_analysis_crosscheck.py
```

The first command rebuilds only these experimental replacement artifacts. The others use read-only stock ROM plus explicitly labeled in-memory overlays. No physical interface or vehicle action is performed.

The separate conservative firmware attempt is under `../static_analysis/20260926T011704.827676Z`. It used the frozen 75-form core, 2,585 candidate entries and a declared 100,000-transfer budget. It retained 80,601 unknown frontiers and an unfinished worklist. Reads of both changed objects and both proposed tails remain **FAIL** to exclude. Counts describe explored abstract states, including opaque/data paths, not certified reachable firmware.

The parent-built `../protocol/two_pages_01` prototype fits an 88-byte matcher at `42A4` and a 60-byte main adapter at `14770`. `two_page_dispatch_abi.json` independently overlays those fragments, both semantic replacements and the default-entry trampoline, then executes the complete OEM dispatcher from `4828C` through its return. All 7,638 rejected single-byte mutation pairs preserve full return state and original writes outside the explicit eight-byte adapter stack area. Twelve mutations select existing OEM commands and are reserved for the parent's complete wire suite. Both accepted pages pass 160 flag/error/SR combinations with only declared response fields differing.

`two_page_CFG_frame_proof.json` derives equal frame depth at every compiled CFG join, an eight-byte adapter peak and a 36-byte complete dispatcher frame including its existing 28 bytes. The matcher uses zero stack. PR is allowed to change during its helper call: the original dispatcher restores caller PR at `484C4` before RTS. R2/R3 are overwritten by the original continuation; R1/R4 are saved and restored. The common CLRT restores the T=0 condition established by the original default-command path. Other SR bits, MACH/MACL and FPU state are untouched.

Payload bounds including the entry trampoline are 142 instructions/50 data accesses for page0, 107/38 for page1 and 136/49 for the longest rejected case. The only loop counts down from 12 or 18. Every statically reachable payload instruction is covered by accepted or rejected cases. Under the illustrative F=D=2 timing assumptions these bounds become 902, 680 and 865 cycles plus unbounded external/entry terms; they are not silicon measurements. This adapter reuses the native response producer and adds no refill hook, background hook or persistent state.

Reproduce the final protocol checks with `py -3.14 m07_two_page_abi.py` and `py -3.14 m07_two_page_cfg_proof.py`. The combined experimental in-memory image hash is `9dc63ee19afaef524755e00e1da3ca958b12f76ceeaf8e36c70cd3a9e3bf57a1`. These results establish scoped compiled behavior and ABI only; the parent owns actual OEM parser/producer/wire validation and complete residency decisions.
