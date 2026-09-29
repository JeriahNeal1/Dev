# ROM ownership review — frozen M0 final05

**ROM_OWNERSHIP: FAIL (proof incomplete, not a demonstrated collision).** Provisional `[0xE1000,0xE1364)` remains unapproved. The alternate run also lacks an exclusive-ownership proof; no relocation or payload rebuild was performed. Calling an alternative “free” would repeat the same unsupported inference.

All work used stock SHA256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218` and the existing IDB's separately identified editor-stamp variant. Raw bytes and old delivery were preserved.

## Whole-run evidence

`audit.py` examines the complete maximal FF runs, including 128 bytes on each side, all byte-aligned 32-bit values, every even-address SH PC-relative word/long/address load, direct relative branches, defined immediate operands, and all existing IDA xrefs. Results are in `static_audit.json`.

| Property | Run containing E1000 | Alternate run |
|---|---:|---:|
| Maximal FF interval | CE754..FFAF8 | 859BC..C0000 |
| Bytes | 201636 | 239172 |
| Existing defined code / xrefs into interval | 0 / 0 | 0 / 0 |
| Raw byte-aligned 32-bit numeric matches | 144 | 21109 |
| Raw even PC-relative matches | 5 | 65 |
| Raw direct branch matches | 0 | 34 |

The raw matches include data decoded as instructions and small packed integers. They are retained rather than silently discarded. No matched PC-relative or direct-branch source is an existing defined code head. That qualification is not a proof of unreachability: the IDB is incomplete.

Two unlabelled but real instructions, 7A79C and7A7B4, load CE754 from7A820. Inspection and execution show it is an **exclusive upper limit**, not a dereferenced destination. Routine7A77C processes up to128 halfwords from[C0034,CE754), then another region[2034,858B4). Initialized pointer storage is6FD8/6FDC, sums6FE0/6FE2, status6FE4/6FE5. Dynamic tests cover first/middle/last calibration chunks and first/last code chunks; a deliberately wrong CE756 bound produces the expected watched read atCE754. Finishing floating-point conversion paths were not simulated or claimed verified.

The other two apparent MOV.L matches,8548A/8551A, occur in descriptor data at85584/855AC containing000F0800. The MOV.W match atCE636 points beyond the calibration-data boundary and comes from raw data decoding. Referenced apparent longword pointers in752C8/752DC/752F0 and other table/array records remain numerically documented; their existence is not treated as real32-bit address use. `immediate_propagation.py` adds MOV-immediate, word/long literal, extension, shifts and arithmetic constant construction searches. Its branch/join resets and unmodelled instructions are explicit: this search is not a complete abstract interpreter.

## Reset, vectors, checksums and neighboring data

Reset vectors0/8 identify AAC, with SP=FFFFBFA0. The runtime entryFFFF8 identifiesF60C; its VBR load isFFC50. The proposed868bytes overlap neither reset/vector tables nor the checksum descriptors beginningFFB80. Vector values and VBR instructions are exported in `static_audit.json`; potential vector roots were also included in raw CFG exploration.

The first non-FF bytes after the run are atFFAF8; the preceding bytes atCE6D4..CE754 contain calibration values and zeros. E1000 is interior to the run, well clear of both boundaries. The alternate run begins after code/table material at859BC and ends at theC0000 calibration block; moving there provides no stronger ownership evidence.

The OEM checksum loopF706 reads descriptor0 `(2000,FFAF7,correction)` and sums32-bit words throughFFAF4, i.e. effective interval[2000,FFAF8). It therefore **does read the proposed allocation**. FA84's alignment/range validation and actual inner loopF75E..F766 were executed against stock and payload-boundary chunks. The checksum correction policy is necessary, not evidence that the hole is wholly unread. Full reset/watchdog/peripheral execution was not stubbed to manufacture coverage.

`definitions.py` resolves A2WC511R→A2WC510C→32BITBASE and checks412 ROM-backed extents from the installed native RomRaider model, including stored axes and checksum/switch spans. None overlaps either run. This does not establish that undocumented OEM tables are absent. Six related A2WC map/header pairs were inspected: A2WC510S/522S/522N/501L use E1000;412I usesE1400;012E has a different ROM layout. These are historical MerpMod annotations, not original-linker allocation contracts. The local image inventory contains no independent related-family1MiB ROM that can prove the A2WC511R hole's ownership.

## Reachability and dynamic limits

The read-only IDA exports contain63588 defined instructions,913 functions,95356 xrefs, and250903 raw-decodable even words below859BC. `reachability.py` follows direct branches, constant-resolved indirect transfers and existing code xrefs, retaining every unknown transfer. It does not convert raw decode into persistent code.

| Root set | Words visited | Unresolved transfers | Undecodable frontier | Hole entries |
|---|---:|---:|---:|---:|
| Potential reset/runtime vectors | 9902 | 54 | 0 | 0 |
| Above plus existing functions | 69091 | 94 | 0 | 0 |
| Above plus potential loaded code pointers | 196858 | 1380 | 530 | 1 in alternate run |

The final set intentionally includes false data seeds. Its alternate-hole entry is therefore not a demonstrated executable collision. This is exploratory reachability, not a sound whole-program overapproximation. The first two sets are incomplete because computed callback/context/table targets and indirect data extents are not universally bounded. Examples include RTOS3980, runtime callback interfaces, boot dispatch and table helpers. The exact frontier is machine-readable; the RAM review supplies additional narrow dispatcher bounds. Independent review tightened constant resolution at joins/implicit pointer writes and separated normal entry into a delay-slot address from delay-slot execution. No empty-xref claim substitutes for closing these edges.

One of the94 tool-frontier sites,43E8, now has a separate guarded target proof: valid aligned sizes0..64 select the17 entries4438..447B, each confined to the copy routine; larger sizes take447C. Two mutated-contract regressions reject a larger bound and an E1000 redirect. The generic walker deliberately does not treat this local size invariant as unconditional knowledge for arbitrary entry states. Caller-supplied source/destination extents remain separate. Thus94 is a reproducible exploration result, not94 equally unreviewed or irreducible obligations.

The refreshed1024 stock/patch differential pairs also watch/fetch-account for both full runs. Only declared M0 payload accesses occur in the exercised patched path; stock has none in those routine scenarios. The separate OEM checksum tests establish a legitimate hole reader. Neither scenario coverage nor observed sentinels establishes universal lifetime ownership.

## Decision and remaining executable proof obligation

The known-path checks and22 actual-instruction scenarios pass, including the completed-scan guards executed up to the finishing-helper boundary. The exclusive-allocation gate fails because computed control/data accesses outside the covered paths have not been bounded. To promote any location, close the remaining callback/context invariants and ROM-reading extents against all relevant operating modes, or obtain a trustworthy original section/allocation contract. A bench trace can supplement this work but cannot logically prove the absence of an unexecuted software access. E1000 was not forced, and the alternate[859BC,C0000) was not relabelled proven.

Reproduce with `audit.py`, `reachability.py`, `immediate_propagation.py`, `definitions.py` and `test_rom_routines.py` using Python3.14. Their JSON inputs/outputs preserve all positive matches and scope limits. Official IDA changes were limited to three evidence-qualified comments and the verified FA84 validator name after the backed-up IDB and regression pass.
