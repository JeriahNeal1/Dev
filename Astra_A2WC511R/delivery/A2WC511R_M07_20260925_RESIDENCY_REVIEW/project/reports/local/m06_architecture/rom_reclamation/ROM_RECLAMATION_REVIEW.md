# M0.6 OEM diagnostic-table reclamation

The best candidate is a representation change to the existing SSM setter dispatch table at `[0x4F310,0x4F950)`. It contains 400 pointers, of which 383 select the same four-byte no-op handler. A 400-byte index array, 72-byte dictionary of all 18 original pointer values, and compiled 92-byte lookup helper leave **1,036 bytes at `[0x4F544,0x4F950)`** for the request-scoped diagnostic implementation. This uses an identified OEM object; it does not assume the prior FF-filled E1000 region is free.

Status: the complete finite lookup representation model passes for both original 16-bit domains, 131,072 mappings total. The compiled helper and overlay are experimental analysis artifacts. Independent actual-instruction differential validation passed all 65,536 getter indices and all 65,536 setter indices, comparing the complete selected-handler entry state. No OEM ROM, frozen M0 source/build, IDB, or physical device was modified by this branch. Complete unknown-consumer exclusion is not claimed from raw reference scans.

## Exact input and reproduction

The immutable source is `C:\Dev\SubaruRoms\OEM\A2WC511R.bin`, 1 MiB, SHA-256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`. The analysis also reads the existing saved IDA defined-code export and checks all 63,588 exported instruction words against this source. IDA's stamped image differs only in the previously documented external stamp bytes.

From `C:\Dev`:

```powershell
& 'C:\Program Files\Python314\python.exe' 'C:\Dev\Astra_A2WC511R\reports\local\m06_architecture\rom_reclamation\analyze_reclamation.py'
& 'C:\Program Files\Python314\python.exe' 'C:\Dev\Astra_A2WC511R\reports\local\m06_architecture\rom_reclamation\build_lookup.py'
```

`reclamation_audit.json` records extracted table values, all handler indices/spans, expected instruction regressions, raw inbound-reference scans, neighboring consumers, full-domain mapping checks and negative counterexamples. `lookup_overlay_manifest.json` records the compiled helper's exact fragments, expected original bytes, source and ELF hashes, entry symbols and contract. The assembler is the existing KPIT GNUSH 13.01 toolchain, `-big -renesas --isa=sh2e`; linking uses `-EB`. Source, linker script, object, ELF, extracted helper bytes, map and command logs are preserved here. No flattened ECU image is produced.

## Stock command dispatch and rejected alternatives

The SSM dispatcher starts at `4828C`, with a 28-byte saved-register frame. It reads request byte `FFFF6408+4` and selects:

| Command | Handler start | Handler code end | Bytes before next handler/pool |
|---|---:|---:|---:|
| A0 | 4835C | 483B6 | 90 |
| A8 | 483B6 | 483D6 | 32 |
| B0 | 483D6 | 4841E | 72 |
| B8 | 4841E | 48460 | 66 |
| BF | 48460 | 48472 | 18 |
| 9F | 48472 | 48486 | 20 |
| Other | 484B0 | 484BC | 12 |

All commands join the common epilogue at `484BC..484D4`. Identified direct callers are `48018` and `48128`. The apparent raw branch at `48C0E` and unaligned literal at `751DB` are preserved in the scan as raw matches, not asserted executable entries. Root owns the upstream acceptance and response lifetime audit.

The default handler is live code: it sets the reject-state bit in `FFFF649B` and clears the automatic-repeat bit in `FFFF649A`. It cannot be deleted as an unsupported no-op. The pool `[48318,4835C)` is shared with preceding routines, including response startup, so the whole 584-byte dispatcher envelope is not exclusively executable payload space. Combining the dispatcher's repeated flag read/modify/write operations would also change intermediate writes and interruption behavior; that compaction is not relied on.

`48A70` and `48A7E` are equivalent 14-byte boolean leaf readers of bit zero at `FFFF649C`, referenced separately by `49920` and `49926`. Sharing one could save roughly ten bytes, insufficient to justify another hook. The existing setter no-op at `4A096` is already only `rts; nop`; separate no-ops at `4A0EA` and `4A0EE` are also four bytes. None is a useful contiguous payload region.

## Table ownership evidence and exact consumers

The setter table spans exactly 400 longwords, ending at the next byte map at `4F950`. Its original SHA-256 is `b49a50665f5da43369b099900945bb8d916fd36df60cd5eb87fb7e3c272bca1b`. The 17 nondefault indices are `0, 96, 111, 112, 113, 137, 138, 221, 222, 223, 224, 225, 226, 227, 228, 232, 288`. Their complete original targets, code spans and hashes are in the audit; all 18 pointer values, including distinct no-op addresses, remain distinct in the dictionary.

The direct setter resolver is `489F0..48A70`. Its table path loads the index from `FFFF63F4`, zero-extends it, multiplies by four and reads `4F310 + 4*index` at `48A30..48A38`. The existing handler call and its preceding memory/security classification remain in place. B8 admission at `48436` rejects 24-bit values at least 400; `486D6..486FE` copies the accepted index and data into the existing request state. The helper does not rely on that normal bound.

The getter resolver at `48968` similarly reads from `4ECD0 + 4*index` at `48988..48990`. **Getter indices 400 through 799 alias the original setter table.** A setter-only compaction would change those results; the negative regression demonstrates this with index 400. The design therefore redirects both lookup sites through the shared helper.

The whole-image, every-byte-alignment literal scan finds exactly one value pointing into the setter table: pool `48AAC`, value `4F310`. Its identified PC-relative consumer is `48A30`. All 330 raw relative-branch opcode matches into the table are low halfwords of pointers in the identified getter/setter tables; none is an independently identified executable branch. The audit also finds no overlap with any of the native RomRaider table/axis extents. These are scoped positive ownership and consumer facts, not a proof against every unrecognized computed pointer in the firmware.

The neighboring byte map at `4F950` is read by `4986E` and `4988A` with offset `(u16)r4 - 142`. Across both complete original lookup domains, each handler is selected by exactly 59 getter indices, none by a setter index. Their minimum selected indices are 142 and 174; their maxima are 378 and 385. With the selected index supplied to the handler, all such reads stay in `[4F950,4FA44)`. All literal references to these handlers are the corresponding getter-table entries. An arbitrary direct call with `r4=0` would instead underflow into the setter table; this is explicitly not declared safe for arbitrary arguments or unexplained interleavings of the existing index state.

ROM checksum walks and ordinary A0 ROM reads also read these physical bytes. Their changed results are an intentional image-identity consequence, requiring the ordinary checksum and full-diff review. The helper does not conceal changed image bytes from a raw ROM read.

## Compiled representation and finite proof

| Region | Purpose | Bytes |
|---|---|---:|
| 4F310..4F4A0 | Byte index for each of the 400 original entries | 400 |
| 4F4A0..4F4E8 | All 18 original 32-bit pointers | 72 |
| 4F4E8..4F544 | Exact compiled SH-2E helper and literals | 92 |
| 4F544..4F950 | Remaining space within the replaced OEM object | 1,036 |

Let `B` be the original getter or setter table base and `i` the zero-extended 16-bit input. Compute `a = B + 4*i`. If `4F310 <= a < 4F950`, the helper obtains `j = (a - 4F310)/4` and returns `dictionary[index[j]]`, which equals the original word at `a` by construction. Otherwise it performs the original direct word read at `a`. Neither base can overflow a 32-bit sum over this domain. Every address is aligned. This proves both the ordinary 400-entry behavior and the exceptional original word reads outside it. The Python audit checks all 65,536 inputs for each base and rejects corruption of an index, a target, a missing out-of-range fallback, or omission of the getter alias case.

The setter entry is `4F4E8`; the getter entry is `4F4F2`. Proposed instruction hooks occupy exactly `48A30..48A38` and `48988..48990`; their existing literal slots are `48AAC` and `489D8`. The original `jsr @r2` and delay slot are unchanged at both sites. The helper returns the original `r0` base, original result in `r2`, the setter's original shifted index in `r1`, and unchanged getter `r1`. Other GPRs and SR are preserved. It uses no FPU, GBR, VBR, MACH or MACL operations and allocates no persistent RAM.

There are 16 added transient stack bytes, balanced on every path. Their residual bytes differ from stock below the restored SP; they must be included in the request-context stack accounting. The helper call temporarily changes PR, but stepping the original handler `jsr` and delay slot restores the exact OEM PR (`48994` or `48A3C`) at handler entry. Comparing before that original call while demanding equal PR would be the wrong contract. No handler should be executed during exhaustive out-of-range differential tests because an original out-of-range word need not be an executable address.

## Remaining review boundary

The compact object and exhaustive mapping proof remove the need to claim a new unused FF hole. They do not by themselves prove the new request producer, receive/transmit lifetime, full interrupt context, timing, physical protocol behavior or current vehicle calibration. Root owns those analyses and final integration. Independent actual-instruction tests passed: `../lookup_validation/20260925T221333.336500Z/lookup_differential.json`, SHA-256 `10f2eeef70d4d32a7ecd50d45d6568a9d291e52f3a2013c4973d33558d00a894`. The run executed 786,432 stock and 3,742,352 candidate instructions, compared GPR/SR/MACH/MACL/PR/SP and selected PC, and observed exactly four longword writes to the declared 16-byte transient stack. It also passed 18 abstract/concrete helper cross-checks. Invalid selected pointers were compared without executing those handlers. Unknown computed consumers remain an explicit scope limitation rather than a fabricated whole-program theorem.
