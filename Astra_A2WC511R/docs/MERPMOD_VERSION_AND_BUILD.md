# v3 precedence note

Current host authorization and run order are in `../AGENTS.md`, `../state/RUN_CONTRACT.md` and `CLI_SETUP.md`. Actual uploaded source/binary identities superseding older unknowns are in `DEV_SNAPSHOT_AUDIT.md`. Keep the technical details below, but do not reimpose historical per-action host permission requests or stop after the first milestone. Physical actions remain human-controlled.

---

# Exact MerpMod generation and build workflow

## Version identity — observed versus proposed
| Component | Evidence | Required treatment |
|---|---|---|
| MerpMod | Historical build writes`GITVERSION v0.1-73-g8720d20`; full matching commit`8720d209df107a81fd171131cfba96d8cae1f118` | Use this as the known source basis; inspect current host HEAD/dirty changes before any checkout. |
| SharpTune | Executed binary banner`0.1.9-RC2-10-gfcf9fdb`; upstream resolves to`fcf9fdbafc2ba5bf04674fcad253fbda404aa171` | Hash executable and compare local source. A banner alone does not prove a clean source build. |
| Starter SharpTune pin |`ecabea89615132dac2de37c05f72adae16d966d1` | Now verified as the uploaded SharpTune source HEAD (RC2-12); the copied executable still needs source/binary reconciliation. |
| Starter SubaruDefs pin |`9b2992eba8133fe5338b89aa77b22c1bb14d6507` | Now verified as the uploaded SubaruDefs HEAD; compare newer local changes before use. |
| Actual historical target/config |`A8DH202X`, `Gratis_Debug` | Wrong target for this port; do not reuse resulting object/patch as A2WC511R. |

Raw evidence:`evidence/original/Pasted text(20260823-200955).txt`. The log ran`SharpTune.exe ecumaptool ... A8DH202X Gratis_Debug`, compiled/linked, then failed to copy`A8DH202X.bin` into`patched.bin`. The exception in`rommod hewbuild` makes post-build failure explicit. Its final0Errors/2Warnings summarizes the compiler, not the success of all external phases. `Error finding scaling ChecksumFix` and pointer-type warnings also require investigation.

## This is NOT the old compatibility-list installation method
Use the source tree, target map translation and patch generation for the exact CALID. The old`Release/Gratis` prebuilt set is not the authority for an unsupported A2WC511R port. At the inspected source revision the README calls Gratis deprecated, Flash its successor, and Switch alpha/untested. This describes the upstream feature/config generations, not certification of our automatic launch implementation. [MM-README.]

The upstream README_PORTING has **Flash-build scope**. Use its disassembly/map identification guidance, then audit actual source feature dependencies; do not assume it documents every Switch/advanced-launch path. The default bundled calibration tables are explicitly not base maps for a car. The upstream MerpMod README does not promise RomRaider editor support for inserted patch tables; generated ECUFlash definitions and logger definitions serve different purposes. [MM-PORT, MM-README.]

## Existing tree and phase conventions
Repository root`C:\Dev\MerpMod`; source/project subfolder`MerpMod\`. Inspect these exact files from the local matched revision:

| Files | Why read them |
|---|---|
|`README.md`, `README_PORTING.md`| Workflow and original assumptions/warnings. |
|`MerpMod\MerpMod.hwp`, root`.hws`| Actual HEW configuration, files, flags, sections and custom phases. |
|`MerpMod\Targets\TargetSelection.bat`, `idatohew.xml`| How CALID, map names, masks, target header/config and linker script are generated. Case/spelling may differ on host. |
|`MerpMod\TestRom\Update.bat`| Post-build ROMcopy/SharpTunecommands and failure handling. |
|`MerpMod\EcuHacks.h`, `TargetHeader.h`, `TargetConfig.h`, `GitVersion.h`| Compile-time interface and actual effective settings. |
|`Initializer.c`, `RamVariables.h`, `ResetHandler.s`, `Metadata.c`, `Definition.c`| RAM layout, initialization, hooks/metadata/definition generation. |
|`RevLimiter.c`, `RevLimiterTables.c`, `SwitchChecks.c`| Automatic activation and rev-limit implementation. |
|`TimingHacks.c`, `FuelHacks.c`, `BlendAndSwitch.c`, `PullRamHooks.c`| Feature coupling; whether OEM table paths remain intact. |
|`Flash.h`, `Gratis.h`, `Switch.h` if present| Feature defaults, not an approval to activate them. |

The readme describes HEW placeholders`TARGETROM` and`TESTROMDIR`, target-selection first and update-test-ROM last. Existing map entries override generated header entries; persistent stale header entries can survive unless explicitly removed/overridden. Do not edit generated files as the only source of truth. Reconcile all references with the exact current`idatohew.xml` and source. [MM-README, MM-EH.]

## Observe, then make build invocation reproducible
First record:
```powershell
git -C C:\Dev\MerpMod rev-parse HEAD
git -C C:\Dev\MerpMod describe --tags --long --always
git -C C:\Dev\MerpMod status --porcelain=v1
git -C C:\Dev\SharpTune rev-parse HEAD
```
These are examples using reported paths. Actual paths may differ. Hash the actual SharpTune.exe used by the HEW project, not just the one in another folder. Capture GNUSH `--version` from the executable referenced by HEW and record CPU/endian/FPU/ABI/optimization flags and generated assembly.

Observed command shapes (for reference, **not ready-to-run commands with missing target files**):
```text
SharpTune.exe ecumaptool idatohew.xml <CALID>.map <CALID>.h <CALID>.txt <CALID> <BUILDCONFIG>
SharpTune.exe rommod hewbuild partial-patch.mot patched.bin <BUILDCONFIG>
```
Before executing, read CLI parsing at the actual SharpTune commit and create an isolated offline output directory. Never use wildcard deletion against the user's project/root. Check native exit codes immediately in PowerShell; configure .bat phases to propagate failure, and verify expected output existence/hash/identity. A general-purpose MSBuild installation builds SharpTune's C# project, not the SuperH ROM code. Inspect its .csproj/framework/bitness rather than converting it to a new framework to silence errors.

## Minimal diagnostic-only design
Do not simply select Switch or set launch gains to0. In the inspected`EcuHacks.h`, TIMING_HACKS and POLF_HACKS can force SWITCH_HACKS; other hooks are selected by symbol availability. Inspect the complete preprocessed config and generated patch footprint. A new diagnostic-only path should evaluate candidate eligibility and rejection reasons without replacing OEM timing/fueling/MAF/WGDC/limit/torque-intervention behavior. Existing main-hook dispatch and initialization may still change execution/RAM and need proof. The old starter's`LAUNCH_ONLY_HACKS` notes are proposals, not implemented features.

No A2WC511R target template in this package is claimed complete. Keep intentional #error/placeholders in the archived template until the new ledger resolves all enabled symbols and holes. No 'stock-looking' FF space or successful linker run certifies it.
