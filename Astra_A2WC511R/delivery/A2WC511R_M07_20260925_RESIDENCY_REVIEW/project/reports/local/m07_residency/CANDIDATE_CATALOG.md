# OEM compression and reclamation candidate catalog

Two OEM function rewrites were implemented in M0.7. Their scoped semantic proofs support **162 conditional saved bytes and zero bytes accepted as payload residency**. Earlier M0.6 investigations also screened the SSM dispatcher, duplicate leaves and tiny no-op handlers, and implemented a table representation experiment. A routine listed for preservation or consumer analysis is not thereby a compression candidate.

This catalog reads the existing reports only; no additional finite tests, firmware changes or gate changes were made. It is not an exhaustive survey of all firmware functions. Addresses are ROM offsets and all intervals are end-exclusive. Body/envelope sizes can include literals, overlapping rows must not be summed, and the duplicate-leaf savings estimate belongs to the pair. Full machine-readable scopes and source hashes are in [CANDIDATE_CATALOG.json](CANDIDATE_CATALOG.json).

## Implemented M0.7 function rewrites

| Routine | Original changed span | Replacement | Conditional tail | Decision |
|---|---|---:|---|---|
| Signed division sub_4260 | `00004260..0000430A` (170 bytes) | 68 bytes | `000042A4..0000430A` (102 bytes) | Scoped equivalence; residency unresolved |
| Switch tail within sub_1466E | `0001473C..000147AC` (112 bytes) | 52 bytes | `00014770..000147AC` (60 bytes) | Scoped equivalence; residency unresolved |

Division executes the original 32 arithmetic pairs in a counted loop. Its structural argument and 1,401 differential pairs preserve final state and the divide-by-zero error write, under the declared entry/private-stack/noninterleaving contract. The nonzero path adds one private four-byte stack word; the longest observed instruction count grows 79 to 210. Range-tail replacement has 52 bytes versus 112 original bytes, with 16 nibble partitions and 1,792 whole-function pairs checked. It requires the unchanged `1466E` setup `R6=64`; arbitrary interior entry has a demonstrated counterexample. Neither proof establishes global ownership, private-stack margin or hardware timing.

The range function metadata is `[1466E,147AC)` (318 bytes), but only `[1473C,147AC)` is replaced. Shared literals `[146B4,14730)` stay unchanged. Division padding/literals `[430A,4314)` stay outside its changed object. The ownership review identifies four division entry callers and one enclosing range-function entry caller, but unresolved computed entry/internal-consumer contracts prevent residency acceptance. Transparent diagnostic reads of modified ROM are expected image-identity changes, not by themselves a residency failure.

Evidence: [semantic replacements](semantic/SEMANTIC_REPLACEMENTS.md), [manifest](semantic/candidate_manifest.json), [object inventory](semantic/object_inventory.json), [ownership review](ownership_review/OWNERSHIP_PEER_REVIEW.md).

## M0.6 reclaim screening and implemented lookup experiment

| Routine/object | Examined span; bytes | Disposition and reason |
|---|---|---|
| SSM command dispatcher envelope | `0004828C..000484D4`; 584 | SCREENED_NOT_IMPLEMENTED: The 584-byte envelope includes shared literals and live command bodies; repeated flag writes cannot be merged without changing intermediate writes/interruption behavior. |
| SSM A0 handler body | `0004835C..000483B6`; 90 | SCREENED_NOT_IMPLEMENTED: Identified live OEM command body; no complete dead/unneeded handler or semantics-preserving compression was proved. Preserve existing behavior. |
| SSM A8 handler body | `000483B6..000483D6`; 32 | SCREENED_NOT_IMPLEMENTED: Identified live OEM command body; no complete dead/unneeded handler or semantics-preserving compression was proved. Preserve existing behavior. |
| SSM B0 handler body | `000483D6..0004841E`; 72 | SCREENED_NOT_IMPLEMENTED: Identified live OEM command body; no complete dead/unneeded handler or semantics-preserving compression was proved. Preserve existing behavior. |
| SSM B8 handler body | `0004841E..00048460`; 66 | SCREENED_NOT_IMPLEMENTED: Identified live OEM command body; no complete dead/unneeded handler or semantics-preserving compression was proved. Preserve existing behavior. |
| SSM BF handler body | `00048460..00048472`; 18 | SCREENED_NOT_IMPLEMENTED: Identified live OEM command body; no complete dead/unneeded handler or semantics-preserving compression was proved. Preserve existing behavior. |
| SSM 9F handler body | `00048472..00048486`; 20 | SCREENED_NOT_IMPLEMENTED: Identified live OEM command body; no complete dead/unneeded handler or semantics-preserving compression was proved. Preserve existing behavior. |
| SSM default handler body | `000484B0..000484BC`; 12 | SCREENED_NOT_IMPLEMENTED: Live reject behavior sets 649B reject bit and clears 649A automatic-repeat bit; deleting it is not a no-op. |
| Duplicate boolean leaf | `00048A70..00048A7E`; 14 | SCREENED_NOT_IMPLEMENTED: Both 14-byte leaves read bit 0 of FFFF649C; sharing one might save roughly 10 bytes, insufficient to justify another hook. |
| Duplicate boolean leaf | `00048A7E..00048A8C`; 14 | SCREENED_NOT_IMPLEMENTED: Both 14-byte leaves read bit 0 of FFFF649C; sharing one might save roughly 10 bytes, insufficient to justify another hook. |
| Existing RTS/NOP setter leaf | `0004A096..0004A09A`; 4 | SCREENED_NOT_IMPLEMENTED: Already a four-byte RTS/NOP leaf; not a useful contiguous payload region. Distinct original pointer identities are retained by the table dictionary. |
| Existing RTS/NOP setter leaf | `0004A0EA..0004A0EE`; 4 | SCREENED_NOT_IMPLEMENTED: Already a four-byte RTS/NOP leaf; not a useful contiguous payload region. Distinct original pointer identities are retained by the table dictionary. |
| Existing RTS/NOP setter leaf | `0004A0EE..0004A0F2`; 4 | SCREENED_NOT_IMPLEMENTED: Already a four-byte RTS/NOP leaf; not a useful contiguous payload region. Distinct original pointer identities are retained by the table dictionary. |
| SSM setter dispatch table representation | `0004F310..0004F950`; 1600 | IMPLEMENTED_FINITE_LOOKUP_EQUIVALENCE: 400 pointers include 383 identical default entries. 400-byte indices + 72-byte dictionary + 92-byte helper conditionally save 1036 bytes. |
| SSM getter resolver | `00048968..000489F0`; 136 | IMPLEMENTED_LOOKUP_SITE_REDIRECTION: Only the eight-byte table-lookup site is redirected through the shared compact lookup; original security classification, handler call and continuation remain. |
| SSM setter resolver | `000489F0..00048A70`; 128 | IMPLEMENTED_LOOKUP_SITE_REDIRECTION: Only the eight-byte table-lookup site is redirected through the shared compact lookup; original security classification, handler call and continuation remain. |

The setter-table representation is a data-object rewrite, not proof that an OEM executable function was removable. It conditionally reduced 1600 bytes to 564 bytes and preserved 131,072 full-domain getter/setter selections at the selected-handler entry. Both resolver hooks are necessary because getter indices 400..799 alias the setter table. The 16-byte added helper stack and unknown internal consumers remain obligations. This is frozen M0.6 research, not M0.7 approved residency. The table helper savings do not add to the 162-byte M0.7 claim.

Evidence: [M0.6 reclamation review](../m06_architecture/rom_reclamation/ROM_RECLAMATION_REVIEW.md), [complete audit](../m06_architecture/rom_reclamation/reclamation_audit.json), [lookup manifest](../m06_architecture/rom_reclamation/lookup_overlay_manifest.json).

## Preserved routines and neighboring consumers, not additional compression candidates

The following 15 distinct setter handlers were enumerated by body span/hash and original table index. The three four-byte no-op targets are already listed above. None of these 15 was implemented as a compressed function; exhaustive lookup validation compares the selected handler entry state rather than executing every possible handler.

| Handler | Body span; bytes | Original index | Scope |
|---|---|---|---|
| `0004A090` | `0004A090..0004A096`; 6 | 0 | Original target preserved; body hash recorded |
| `0004A09A` | `0004A09A..0004A0A0`; 6 | 96 | Original target preserved; body hash recorded |
| `0004A0A0` | `0004A0A0..0004A0B2`; 18 | 111 | Original target preserved; body hash recorded |
| `0004A0B2` | `0004A0B2..0004A0C8`; 22 | 112 | Original target preserved; body hash recorded |
| `0004A0C8` | `0004A0C8..0004A0DE`; 22 | 113 | Original target preserved; body hash recorded |
| `0004A0DE` | `0004A0DE..0004A0E4`; 6 | 137 | Original target preserved; body hash recorded |
| `0004A0E4` | `0004A0E4..0004A0EA`; 6 | 138 | Original target preserved; body hash recorded |
| `0004A0F2` | `0004A0F2..0004A106`; 20 | 223 | Original target preserved; body hash recorded |
| `0004A106` | `0004A106..0004A10C`; 6 | 224 | Original target preserved; body hash recorded |
| `0004A114` | `0004A114..0004A138`; 36 | 225 | Original target preserved; body hash recorded |
| `0004A138` | `0004A138..0004A13E`; 6 | 226 | Original target preserved; body hash recorded |
| `0004A13E` | `0004A13E..0004A144`; 6 | 227 | Original target preserved; body hash recorded |
| `0004A144` | `0004A144..0004A14A`; 6 | 228 | Original target preserved; body hash recorded |
| `0004A14A` | `0004A14A..0004A15A`; 16 | 232 | Original target preserved; body hash recorded |
| `0004A1E0` | `0004A1E0..0004A210`; 48 | 288 | Original target preserved; body hash recorded |

`4A1E0..4A210` also has documented tail calls to `285DC/285EC` and optional call `285FC`; those callees were not themselves proposed as compression candidates. The neighboring map readers at `[4986E,4988A)` and `[4988A,498A6)` are 28 bytes each. Each has 59 selected getter indices with bounded map reads under the selected-index contract; an arbitrary direct argument can underflow into the setter table. They were audited as consumers and preserved. The original 1600-byte getter table `[4ECD0,4F310)` was also preserved; its out-of-range alias explains the coupled getter hook.

No table scan, raw pointer absence, sparse IDA metadata, successful finite test set, or count of analysis roots is promoted here into a universal firmware ownership claim. Full-ROM A0 image attestation remains separately withdrawn.
