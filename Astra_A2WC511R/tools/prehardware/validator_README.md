# Read-only prehardware image validator

Run from any working directory, including a directory containing spaces:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\prehardware\validator.py C:\Dev\SubaruRoms\OEM\A2WC511R.bin --output-dir C:\Dev\Astra_A2WC511R\reports\local\prehardware\validator\my_unique_run
```

The output directory must be new. The command writes `VALIDATION.json` and boot-model evidence only. It never writes the supplied ROM, emits a reconstructed ROM, accesses J2534/OpenPort, invokes an installer/compiler, or performs a vehicle operation. Patch reconstruction and inverse checks remain in memory.

The result is `PASS`, `CONDITIONAL`, or `FAIL`, with one result per requirement. Direct Python exit codes are0,2,3 respectively; PowerShell wrappers may map any nonzero native exit to their own failure code. `flash_authorized` is always false. A local offline result does not identify the image currently inside an ECU or authorize a flash.

The supported registry currently contains the exact stock image and both frozen checksum-corrected M0.7 research images. Known stock remains `CONDITIONAL` because boot/readiness and physical identity/timing are not fully established. Both frozen M0.7 images remain `FAIL`: executable residency was rejected in their authoritative review. An unknown/tuned/orphan image returns `FAIL`, even if its CAL ID and checksum are valid. Optional `--artifact stock|one_page|two_pages` selects which registered requirements to diagnose against; it never bypasses exact hash association.

Every normal CLI run invokes the pinned `A2WC511R_Sim/preflash_boot/boot.py` comparison against stock. It requires the same model dependencies, exact ordered writes/control, complete terminal integer/system state, the same stopping boundary, and an empty difference allowlist. Evidence includes gzip JSON traces whose hashes are checked after the process exits. The default model reaches application entry `1150` and stops at `4B4C` on `SYSCR2=3C88` after 57,658 retired instructions. That is an explicit clock/register-model boundary. SCI/SSM startup is not proved, so prefix agreement remains distinct from completed boot. Synthetic model cycles are not silicon timing.

`deterministic_verdict_sha256` covers image/registry/validator identity, individual check statuses, and the path-independent boot trace hashes, terminal state, scenario and milestones. Generated artifact locations appear in the complete report, whose file hash therefore can differ between run directories. A clean-process stock repeat was verified to have the same deterministic verdict.

The validator checks image length, CAL/ECU IDs, big-endian reset words, initial SP, all 14 checksum records and their fixed geometry, original/proposed diagnostic hook bytes, unchanged active-control hooks, compiled instruction words, branch/delay-slot contracts, changed-byte allowlists, prohibited boot/vector regions, 412 native calibration extents, ROM/RAM declarations, inverse/forward patch equality, and association with retained reproducible-build artifacts. Native table extents are incomplete OEM data documentation; the stricter whole-image change allowlist additionally protects every byte outside the exact registered edits. Any checksum-correction exceptions are limited to their four-byte correction words.

`validator_registry.json` is a project provenance registry, not a user-supplied approval manifest. Its exact SHA256 is pinned in `validator.py`; every referenced source/build/review dependency is independently hashed. The program has no `--manifest PASS` or `--ownership PASS` input. A fabricated approval or unknown image cannot inherit the status of a similarly named artifact. This is local integrity pinning, not an external digital signature: an administrator who edits both code and its pinned digest changes the trusted program and must repeat review.

`validator_registry_build.py` is a maintainer-only preparation script, **not** a run prerequisite. It copies declarations from reviewed frozen evidence and requires deliberate review/repinning before a changed registry can be accepted. It cannot turn the frozen M0.7 ownership failure into a pass. Registering a future image requires new independently reviewed code/resource/ownership/build evidence; matching a ROM family or re-running finite scenarios is insufficient.

Regression command:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\prehardware\validator_tests.py --output C:\Dev\Astra_A2WC511R\reports\local\prehardware\validator\ADVERSARIAL.json
```

Tests mutate real image bytes only in memory and assert the specific applicable check fails, in addition to the overall failure. They cover disabled/malformed checksums, endian and SP errors, branch-into-data/odd-target/delay-slot violations, code and calibration corruption, active-hook alteration, undeclared RAM, missing/altered provenance, forged registry approvals, mismatched boot evidence, and unproved readiness. They do not write mutated vehicle images.

Acceptance evidence: `reports/local/prehardware/validator/ADVERSARIAL_FINAL.json` contains 42 passing regression groups; `acceptance_01/ACCEPTANCE.json` records four real clean-process CLI runs from an unrelated working directory containing spaces. Both frozen M0.7 images fail exactly their residency check; stock and its repeat remain conditional. Use `validator_acceptance.py --output-dir <new-directory>` to repeat that acceptance when a substantive tool/model change warrants it.
