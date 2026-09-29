# Independent M0.7 object ownership review

The two replacements have **162 conditional bytes of savings and zero bytes accepted as proven payload residency**. Their scoped semantic arguments pass review. Complete incoming control and internal data-consumer contracts remain unproved. This is an offline review of immutable stock ROM `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`; no firmware or IDB was changed.

| Object | Replacement | Proposed tail | Bounded entry evidence | Complete ownership |
|---|---|---|---|---|
| Division at `4260` | 68 bytes | `[42A4,430A)`, 102 bytes | Four literal callers, all to entry | FAIL |
| Switch within `1466E` | 52 bytes at `1473C` | `[14770,147AC)`, 60 bytes | One literal caller to enclosing entry | FAIL |

`ownership_peer_review.json` records separate PASS subclaims and FAIL dependencies. The independent raw encoding scan covers aligned direct branches, PC-relative MOV.W/MOV.L/MOVA and every byte offset that could contain an absolute pointer. It supplements the saved defined-code export rather than assuming the export is complete.

The division pools `1B330`, `33EE0`, `484A8` and `64318` feed ordinary calls at `1B254`, `33E72`, `483C2` and `64260`. Exact load-through-delay-slot bytes are checked. The function pointer register is not changed between each load and call. Range pool `11AD8` feeds the call at `11936` to `1466E`. No external direct branch targets either full original object, and no external PC-relative access overlaps either changed span. The shared literals at `146B4..14730` are also used by earlier functions; they are outside the changed tail and must remain unchanged. Original division padding/literals `430A..4314` are outside its changed span.

The 944 raw division pointer matches are not 944 callers. Four are aligned entry literals. Thirteen unaligned crossings are positively explained by separate MOVA/FMOV reads of adjacent floating-point constants; another 80 cross elements typed as floats by the installed inherited A2WC511R definition. There are 846 other aligned-word crossings without complete consumer classification. The single odd hit `8289D -> 4300` spans the aligned words `00000043` and `000823EA`. None of these unaligned hits is a legal aligned SH longword pointer load. Bytewise reconstruction remains a distinct, unclosed dataflow question; incidental matches are not evidence that such reconstruction occurs.

The local runtime search covered 477 library/archive files. No complete division routine, its distinctive 12-byte setup, or complete range tail matched stored bytes. Twelve GNU libgcc archives contain the generic repeated ROTCL/DIV1 sequence. That establishes neither original runtime provenance nor an object boundary. Renesas archives contain compressed runtime objects that this search did not decode. An exploratory `lbgsh -help` invocation ignored that option and began default library compilation; it was interrupted, no process remained, and no persistent output was found at the working-directory root. No generated library is used as proof. Compiler CHM files were extracted locally for static option inspection only.

**Return and interrupt contexts.** The original executed paths contain no nested calls. No external BSR/BSRF/JSR creates a return PC inside either object. Thus an ordinary nested callee cannot legitimately retain an original return PC into the reclaimed tails. Interrupts can save a PC inside whichever image is running: this does not create an independent entry contract that permits resuming old instructions after replacement. Installation must begin execution from reset or a proven quiescent state, with no pre-patch execution frames. During replacement execution, transparent ISR save/restore would preserve the interrupted computation; complete actual ISR, stack and timing contracts have not been established by this review.

**Specific remaining control sources.** `0042: JMP @R4` accepts a caller-supplied target after changing SP; the full allowed R4 domain is not established. `DE3E: JSR @R1` loads its target from descriptor+4. Starting at `DDF4`, that descriptor is `BE32(ROM[1023C + 4*u8(entryR4)]) + 8*u16(entryR5)`, with the callback case selected by a leading halfword of `FFFF`. Complete caller index domains and descriptor provenance are missing. These are concrete contracts to close, not claims that either site actually enters a proposed tail. The broad M0.7 value analysis also has an unfinished worklist and unknown targets. Its output cannot establish complete incoming control.

One previously broad frontier can be narrowed without assuming valid task-state indices. On the actual `395A/3972..3980` path, the target is the longword at `4A7C + sign8(state) - zero8(index)`. Exhausting all 65,536 byte pairs gives 127 possible aligned source words in `[4900,4AFC)`, none pointing into either object. Misaligned pairs take the architectural alignment exception and are not simulated as valid loads. `rtos_target_exclusion.json` records every source/target and a mutation control. This proves a target-specific exclusion at `3980`, not a universal RTOS state theorem.

**Semantic theorem review.** Division executes the original 32 arithmetic pairs. The countdown uses R2, restores captured T through SHAR in the branch delay slot, and leaves R2 zero before the original ADDC. It preserves final registers and the divide-by-zero error write. The additional R4 save/read requires exclusive ordinary RAM at `[initialSP-12, initialSP-8)` on the nonzero path; the previous contents of that word are not restored. The longest tested path increases from 79 to 210 instructions. The range proof correctly relies on `1466E: MOV #64,R6`, preserves all sixteen nibble cases and the T predicate, and has a concrete failure for unrestricted interior entry with another R6 value. The structural proof is sound under its stated entry, private-stack and noninterleaving conditions. Neither finite tests nor this argument prove those conditions globally.

Transparent A0/A8 ROM readback of changed instruction bytes is expected modified-image behavior and is **not itself a residency failure**. Internal firmware consumers that interpret these bytes as data, table targets, or DMA input still require exclusion or preserved semantics. No universal prohibition on reading modified ROM is imposed.

Reproduction is read-only except for these review outputs:

```powershell
& 'C:\Program Files\Python314\python.exe' .\inspect_objects.py
& 'C:\Program Files\Python314\python.exe' .\classify_uses.py
& 'C:\Program Files\Python314\python.exe' .\verify_contracts.py
& 'C:\Program Files\Python314\python.exe' .\finish_review.py
```

The 31 byte/encoding/hash checks pass, including injected direct-entry, PC-relative-reader and manufactured-return controls. The additional 65,536 RTOS input pairs pass their target-specific exclusion. Semantic source, ELF and raw-section hashes still match the reviewed manifest. These checks do not authorize flashing or claim physical validation.
