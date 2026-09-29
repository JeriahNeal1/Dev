# A2WC511R diagnostic M0 — compiled experimental package

**COMPILED; NOT RELEASED FOR FLASH.** This run completed an actual A2WC511R/2F12515306/AUTO_TRANS1 SH-2E diagnostic integration and reproducible engineering package. Allocation, task-stack/timing and current-calibration gates remain open. `ENGINEERING_GATES.json` is authoritative for release status; a passing evidence-envelope check is not engineering acceptance.

Final source/build: `source/DiagnosticM0`, `validation/final_build` (m0_final_05) and `validation/repeat_build` (m0_final_repeat_06). GNU SH13.01/GCC4.7 uses -m2e -mb -mrenesas -mieee and assembler --isa=sh2e. The module is868 bytes at provisional[E1000,E1364), with32-byte state at provisional[FFFF7400,FFFF7420). It retains the OEM decoder and adds observations/rejection reasons only. No performance-control feature is linked.

| Artifact | SHA256 |
|---|---|
| Analysis baseline | `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218` |
| Raw experimental image | `8092a20fd37f17dd351d18c805fdf195c2207af9adecca25e388146c7a9acc37` |
| Checksum-corrected experimental image | `6e556dd084e69af47c230a1787d229aee7b49d957d2848bb14a39a48a69042af` |
| Strict SharpTune patch | `806f0e61a8ff2bb4b2335e2586403de902f78c51fd19e4c10bc81b8836cba007` |

Both images are1,048,576 bytes. The raw image changes859 bytes within the single hook and diagnostic code span; the corrected image changes863 bytes including the checksum word. Raw patch removal returns the exact baseline. Corrected removal followed by the documented checksum normalization returns the exact baseline. The editor stamp remains unchanged. Raw has the expected invalid checksum; the separately named corrected image has a native-matched valid checksum. Neither is physically validated.

Validation includes64 handoff tests,461059 actual host-compiled C checks, native RomRaider acceptance, independent ELF/patch review and actual-ROM SH-2E differential execution. Exact counts, cases, input hashes and coverage limitations are in `validation/local`, `validation/patch` and `simulator/runs`. The initial31-test simulator suite exercises51 supported instruction forms;1,792 stock decoder cases and256 status cases cover both anchors. Compiled differential tests cover1,024 paired cases plus initialization/publication and changed-read scenarios. Unsupported instructions/peripherals fail explicitly. No full engine, TCU, DMA or timing simulation is claimed.

Read `validation/local/ABI_ALLOCATION_REVIEW.md`, `validation/local/interfaces/INDEPENDENT_PORT_REVIEW.md`, the nine `reviews` documents, and `HUMAN_REVIEW.md`. The remaining dependency graph names what is technically unresolved and which human information is needed. The optional native editor confirmation/display workflow remains unperformed; no confirmation was bypassed in RomRaider.

Reproduction on this pinned C:/Dev host uses the exact scripts and recorded argument arrays in `validation/final_build/manifest.json`, `source/DiagnosticM0/build.py` and `experimental_roundtrip.py`. Use fresh output paths. The patch driver deliberately requires the known baseline hash, source/ELF/payload associations and isolated hardened SharpTune tool; do not remove those guards. Source diffs and SharpTune build provenance are included. Compiler/license installations are referenced by hash rather than redistributed. `simulator/README.md` contains its replay commands and scope.

Session:01a0da26-addc-7fe1-84df-8c0baa8174f8. User programs/tunes were preserved; the existing IDB was backed up, analyzed, saved and closed through official Hex-Rays MCP. No ECU/TCU flash, live memory write, CAN injection or vehicle command occurred. All delivered hashes are listed in `SHA256SUMS.json`.
