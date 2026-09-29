# Audit of the uploaded Dev.zip — 2026-09-25

This report is based on actual extracted archive contents, not a guess about the current desktop. The snapshot contained 1,568 ZIP entries (139,871,395 uncompressed bytes). Raw snapshot retained unchanged as evidence/Dev_2026-09-25_original.zip. Programmatic findings: reports/dev_snapshot/dev_audit.json. Local files may have advanced since upload; compare hashes before modifying.

## Actual source and binary provenance
| Item | Observed value |
|---|---|
| MerpMod HEAD | 8720d209df107a81fd171131cfba96d8cae1f118; v0.1-73-g8720d20 |
| SharpTune source HEAD | ecabea89615132dac2de37c05f72adae16d966d1; 0.1.9-RC2-12-gecabea8 |
| SubaruDefs HEAD | 9b2992eba8133fe5338b89aa77b22c1bb14d6507 |
| Both copied SharpTune.exe files | 19,368,960 bytes; SHA256 248eb7f012d0edcb84048ee01f99f7fa49094942c25a3b53e75fbfcb957de8af |
| Historical executed SharpTune banner | 0.1.9-RC2-10-gfcf9fdb; not re-executed here |

Ordinary Git status in Linux falsely appears to show pervasive changes because the checkout has Windows CRLF. With core.autocrlf=true and --ignore-space-at-eol, the substantive MerpMod changes are DefaultSession.hsf, MerpMod.tps and Targets/A8DH202X.h. SharpTune and SubaruDefs had no substantive tracked changes under that comparison. This is not permission to discard changes. An untracked copied SharpTune source tree also exists inside MerpMod: git clean -fdx would destroy user data.

## The known build is the wrong target
`MerpMod/MerpMod/TargetHeader.h` identifies A8DH202X with ECU_IDENTIFIER4312584206, Gratis/Debug. `TargetConfig.h` has AUTO_TRANS0. The linker file uses that target's E1400/FFFF96C0 placements and 33D68 rev-limit address. No A2WC511R header/map/linker/config was present in Targets. Existing Gratis_Debug objects/ELF/MOT must not be relabeled or reused as a completed A2WC511R build.

`TargetSelection.bat` calls ecumaptool and then unconditionally deletes/copies generated files. `TestRom/Update.bat` has shared wildcard .patch deletion, a missing-baseline-sensitive Copy step and a SharpTune invocation without reliable failure propagation. The prior build log's final 0Errors banner did not establish post-build success. Fix these in staging and check real output hashes/identities.

## Compiler settings recovered from actual build artifacts
HEW project settings specify SH2E, BIG, MRENESAS and MIEEE. EcuHacks.gcc contains -m2e -mrenesas -mieee, optlibinc paths to KPIT GNUSH-ELF/v13.01/GCC4.7, -DDEBUG, and the wrong -DTARGET_ECU=A8DH202X. It compiles to assembly, followed by the GNUSH assembler and linker. Link libraries include the generated MerpMod library and gcc variants. Preserve discovered settings and inspect emitted code; do not compile SH-4 merely because IDA uses SH4B to analyze the device.

Existing MerpMod.x is ELF32 big-endian, EM_SH, SH2E flags0xB. Its entry at0x00E00000 is a simulator/reset section, not real ECU flash. The generated S-record contains metadata and simulator addresses beyond the 1MiB ROM. Never flatten that entire output into a ROM.

SharpTune's project is x86 .NET Framework4.0, ToolsVersion4.0. Inspect a compatible MSBuild/reference-assembly route before migrating frameworks. Its ChecksumSubaruDBW.cs identifies the checksum module name; it is not an implemented checksum verifier on its own.

## Baseline and database are now present
| Archive path | SHA256 |
|---|---|
| SubaruRoms/OEM/A2WC511R.bin | 22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218 |
| SubaruRoms/Backup/A2WC511R_STOCK_ROMRAIDER.bin | same baseline hash |
| SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin | a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96 |

Only four bytes differ between the two variants: [0xFFC4C,0xFFC50), FF FF FF FF versus26 08 23 01. This resembles metadata but its role must be confirmed from editor/source evidence; do not silently normalize it away. The matched historical hash improves baseline consistency, not independent manufacturer provenance or knowledge of the currently flashed calibration.

The saved `.i64` (7,348,537 bytes) and .id0/.id1/.nam/.til sidecars are in SubaruRoms/OEM. Do not overwrite the user's newer live database or treat database RAM segment contents as a live ECU capture. Check input bytes/hash in the actual open IDB.

All three .bin files are1,048,576 bytes and have the expected CALID/ECUID, reset vectors and the old pointer words checked by tools/project_core.py. Expected pointer words include7A04→209C,122B4→14B20,127E8→317D8,D324→F928,FFF8→FFFFBFFB. Those checks do not prove hook semantics.

## Allocation is still unresolved
The large FF-filled spans include [0x859BC,0xC0000) and [0xCE754,0xFFAF8). E1000 lies in the second span. These are content observations, not certified free memory. FFFF7400 remains a prior RAM candidate; even an absence of exact aligned pointer references cannot exclude indirect/stack/DMA/reset use.

## Immediate value for the next run
The new session can start from a known wrong-target diagnosis, actual compiler response files, exact repository/executable identities, a baseline comparison and the existing IDB. It should not spend prompts redetecting these facts. Reconcile changed local hashes, complete the actual port/CLI build stages, and leave physical testing with the user.
