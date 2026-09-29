# Independent diagnostic source/build/patch review

Reviewer role: interface_audit, session `01a0da26-addc-7fe1-84df-8c0baa8174f8`. No writes to the build agent's source or release artifacts. Final authoritative revision is `m0_final_05`, repeated as `m0_final_repeat_06`; initial findings are retained for provenance. This review does not approve ROM/RAM allocation, call timing or vehicle use.

## Source and ABI closure

Reviewed `Diagnostic.c/.h`, `Bindings.c`, `DecoderHook.s`, `DiagnosticConfig.h`, `A2WC511R.h`, both linker scripts, compiler assembly/stack-usage output and emitted ELF/map. The closure compiles only diagnostic observer/binding/identity/wrapper translation units. It does not include the existing active-control MerpMod modules or their hook initializer. Configuration explicitly disables the known active features. The hardware binding reads raw byte inputs twice and always publishes freshness UNKNOWN; coherence remains unproven even when the reads agree.

The wrapper calls original decoder `147AC` first. Its only pre-original state changes are saving PR/R0 and the call itself; the delay slot restores R0. The original decoder is independently documented as a stack-independent leaf and overwrites R2 immediately, so the patched R2 indirect-call target cannot leak through that register. After the OEM result exists, the wrapper saves R0..R14, SR, MACH/MACL, calls the diagnostic sample, restores them and returns through the original PR. Emitted C closure has integer operations and no required FPU/GBR operations. The wrapper therefore leaves FPU state untouched along this audited integer closure. This depends on the compiled closure remaining free of FPU/helper additions and does not prove interrupt timing or all possible caller paths.

Initial static added stack maximum: wrapper 76 bytes (saved PR plus 15 GPRs and SR/MAC), sample C 24 bytes, observe C 24 bytes = 124 bytes. The original decoder uses no stack. This is incremental stack use, not proof of available task headroom. Main-agent evidence further identifies scheduler slot9 -> 6580 -> 11134 -> 1193A and at least eight surrounding saved-PR bytes; indirect dispatcher callbacks and RTOS/ISR context remain outside a proved whole-task bound.

## Concrete findings raised

1. **Publication initialization**: initial `m0_init` byte-cleared sequence to even zero before clearing the remaining published state, so it could expose partial reinitialization when a reader observed previously valid state. Initial `m0_observe` also explicitly restarted sequence after lazy init. Requested an odd marker through initialization, even publication last, and sequence advancement on reinitializing a valid cookie to avoid an immediate ABA. The final revision implements and tests this correction. The reader contract requires a single writer/nonreentrancy, matching valid magic/initialized fields, and equal even sequence reads before/after the fields; sequence is never communication freshness.
2. **Patch input provenance**: initial `experimental_roundtrip.py` checked status, fixed length and identifier but did not verify payload/ELF hashes against the build manifest. A changed payload of the same length could be serialized while retaining an unrelated build-manifest association. Requested exact payload/ELF hash guards and symbol-derived hook/identity addresses rather than hardcoded values, especially because the initialization change shifts code. Build agent accepted this before the next artifact revision.
3. **Comment accuracy**: initial binding/wrapper/build comments described harness-only/no hook behavior despite the explicit unapproved experimental mode. Requested final comments describe both modes. This is documentation accuracy, not a discovered active-control path.

No further source logic defect was found in the bounded review. Existing counter wrap behavior and observer-local decoded holds are explicitly described by the patch report/logger fragment: local initial invalid-nibble decode may differ from OEM-held BC1/BC2. No inference of engagement or CAN freshness is made.

## Independent artifact verification

`review_elf.py` parses ELF32 big-endian headers, sections and symbols independently of objdump text. For initial revision:

- EM_SH flags 0xB (SH2E), one allocated read-only executable `.m0` section `[E1000,E1338)` of 824 bytes including the 28-byte identity.
- Entry `E12B0`, no undefined symbols, no allocated writable/global sections.
- Extracted `.code.bin` equals the ELF section exactly; every build-manifest artifact hash matches.

`review_patch.py` independently reconstructs the image from ELF section bytes and the actual ELF entry, without using the pipeline's hardcoded expected output. Initial output passes all checks:

- Raw 1 MiB image equals immutable baseline plus `.m0` and the verified `11ADC` pool word; 815 actual changed bytes.
- Every S3 byte count/checksum is valid, records are disjoint, and all addresses belong to code, metadata or the strict original-byte area. Payload and expected originals exactly match ELF/baseline.
- No simulator or `80001000` patch metadata was flattened into the image.
- Raw removal is exact baseline. Corrected removal followed by the explicitly documented checksum correction returns exact baseline.
- The corrected derivative equals independent native-matched checksum arithmetic. Only checksum bytes `FFB88..FFB8B` differ from raw; editor stamp remains unchanged.
- All patch-output/build-manifest hashes match their records.

Reviewed SharpTune's staged semantic diff: caught CLI exceptions now return failure; isolated settings avoid global saves/plugins; automated offline apply is restricted by explicit environment opt-in, exact experimental identity/build name, and path beneath the isolated output directory. This is separate from RomRaider's retained human changeset confirmation. Pipeline checks native return codes, exact fresh artifacts, output bytes and negative wrong-hook/modified-removal cases. No wildcard cleanup or vehicle interface is used.

## Remaining analysis and packaging decision

The useful bounded follow-up was RTOS task-owner discovery via `FFFF12D8`, pool `4880` and dispatcher call chain. The main agent performed it and identified a more precise owner chain. It does not prove exclusive lifetime ownership of `FFFF7400..741F`, worst-case task-stack/ISR nesting, or cadence. A complete conclusion cannot be obtained from FF ROM bytes, the nearest scalar, or sparse exact pointer matches. No short remaining local analysis is known to guarantee those facts without broader verified coverage or external measurements.

After the two concrete code/provenance findings are resolved and final build/simulator/patch checks pass, packaging an explicitly blocked experimental result is justified. It must remain unapproved for flash with the exact unresolved dependency list; this review is not a substitute for those gates.

## Final revision

Final authoritative build is `work/builds/m0_final_05`, repeated in `work/builds/m0_final_repeat_06`; patch/ROM derivatives are in `work/patches/m0_final_05`. Both substantive findings are resolved. `m0_init` now sets an odd sequence before clearing other fields, advances the sequence for a valid prior cookie, and publishes even last. `m0_observe` continues from the post-init sequence. The singlewriter/nonreentrant reader contract and counter-wrap caveat are explicit. Final host regression count is 461,059; explicit reinitialization advancement is included. Simulator branch independently added instruction/memory-trace publication checks; its report is separate evidence.

The final pipeline hashes current source files and every recorded build artifact, parses the actual ELF `.m0` section and symbol table, verifies payload equality and manifest symbol equality, then derives hook/identity addresses. The negative same-size modified-payload test rejects before generating candidate output (`reports/local/build/final_build_review.json`). Comments now cover both harness and explicitly unapproved experimental modes. These changes close the source/provenance finding; they do not establish allocation acceptance.

Independent frozen-artifact checks in `elf_review_m0_final_05.json` and `patch_review_m0_final_05.json` pass. Exact identities:

| Artifact | SHA256 |
|---|---|
| ELF | `39de4598a5149347052d5773f7bc179f3a21fde9ad4b571fe23a0bbe6e1e9eed` |
| 868-byte payload | `b5004baa2863bf571eb1ab014f93f0316b3500c5b154e47de2e42f904234b2ff` |
| Raw 1 MiB image | `8092a20fd37f17dd351d18c805fdf195c2207af9adecca25e388146c7a9acc37` |
| Checksum-corrected 1 MiB image | `6e556dd084e69af47c230a1787d229aee7b49d957d2848bb14a39a48a69042af` |

Final `.m0` interval is `[E1000,E1364)`, entry `E12DC`; the raw image changes 859 bytes from immutable baseline. The independent full-byte and S3/round-trip checks described above were repeated against final05 and pass. Every current source hash and recorded artifact hash matches the final manifest. Final05 and repeat06 functional artifacts match byte-for-byte; no functional normalization was required.

Actual installed native RomRaider checksum validation was executed against byte-identical revision03 raw/corrected images: raw reports block1 invalid, corrected reports0 valid, and native recalculation of raw produces exactly the corrected SHA above (`native_checksum_final.json`). Final05 raw/corrected bytes are independently verified equal, so the same native evidence applies by hash without redundant recalculation. `frozen_source_and_binary_binding.json` records final source hashes, final/repeat equivalence and that native-evidence association.

Final conclusion: PASS for the bounded diagnostic source closure, build envelope, byte provenance, patch serialization/removal and checksum review. No unresolved local code/provenance defect remains from this review. The artifact remains **EXPERIMENTAL_UNAPPROVED** because ROM/RAM ownership, task-stack/ISR/timing bounds, current vehicle tune identity and physical validation are not established.
