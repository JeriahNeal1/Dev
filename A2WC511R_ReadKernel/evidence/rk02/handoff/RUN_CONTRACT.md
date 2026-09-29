# Full offline run contract

## What “complete” means for this run
The objective is a compiled A2WC511R diagnostic integration and its reproducible review package, not the entire Subaru OEM source tree and not an automatically validated performance/anti-lag calibration. The OEM firmware remains the foundation; MerpMod supplies selected new code. A first diagnostic integration is meaningful compiled progress, not an excuse to stop at a header template.

Host environment preparation and engineering completion are different gates:
- **Preflight ready**: actual CLI model/effort advertised, local utility tests pass, source trees present, installed SH-2E compiler executes the smoke test.
- **Build complete**: exact target source compiles and all external patch stages succeed with fresh expected artifacts.
- **Offline reviewed candidate**: binary provenance, allocation, ABI, feature closure, checksum evidence, calibration and repeatability reviews are complete.
- **Vehicle validated**: human-run physical testing supplied measurements. This cannot be inferred from the first three gates.

## Stage A — establish actual state and interfaces
Read reports/dev_snapshot/dev_audit.json and compare changed files/hashes on this host. Inventory newest tuning directories, logs, active IDB, actual ECU ROM read, program versions and existing configurations. Do not replace the current IDB or repositories. Save/backup through supported IDA operations. Verify official IDA MCP identity/open database, supported tools and a small known-code read; record raw capabilities. Test RomRaider status and read-only snapshot on a disposable ROM; then perform its documented rollback/quantization/stale-state acceptance tests before editing real candidates. A GUI dependency unavailable to one branch must not block all offline source work.

Expected artifacts: config/host_paths.json, reports/local/capabilities.json, backups/change ledger, baseline manifest, input hashes. The root C:\Dev is not a single Git repo; use separate clean staging/worktrees, not git init/clean over everything.

## Stage B — resolve source/generation and build-system defects
Preserve the observed MerpMod commit and substantive dirty changes. Reconcile SharpTune executable RC2-10 provenance with source RC2-12; inspect its x86 .NET Framework4.0 project. Build matching source side by side if needed, retaining the existing exe. Inspect idatohew.xml and generated-header precedence. Capture GNUSH response files, version, library paths, linker pseudo-sections, ABI, floating point and big-endian settings.

Use the actual response files as a starting point for a repeatable CLI driver rather than requiring HEW mouse automation. Do not globally search/replace the wrong CALID in binary object files or reuse their symbols. All compilation units, preprocessing, libraries, assembler/linker and final metadata need the correct target. Add explicit native exit-code and artifact identity checks to staged target-selection/post-build phases; get rid of wildcard cleanup in shared directories. Retain a full build trace.

## Stage C — close enabled-symbol and allocation gates
Map only symbols actually needed by the diagnostic feature set. Audit prologue/epilogue, delay slots, calling convention, register/FPU preservation, interrupt state, call cadence and original continuation. Verify original hook bytes from the exact baseline before writing a patch. Examine RAM reset extent, stack/ISR depth, indirect/VBR/base+offset/DMA accesses and alignment. Determine exact code/data/RAM sizes from the proposed link; reassess allocation when sizes change. Never declare FFFF7400 free because no exact pointer literal was found.

Keep TCU status candidate comments qualified. Examine source/snapshot update and invalid/stale behavior; consume a local six-channel log if available, but normal-operation samples do not prove fault coverage. M0 can report unknown/freshness status rather than control outputs. Separate required implementation gates from later physical experiments and continue independent work.

## Stage D — complete the diagnostic-only source port
Create the exact A2WC511R target map/header/linker/config from verified information. Keep provenance for every symbol, type, unit and mask. Implement diagnostic state/reasons and instrumentation only. Preserve OEM output calculation and behavior, not just a disabled UI flag. Audit EcuHacks.h/initializer/RamVariables and preprocessing for implicit feature enablement. Do not take Gratis.h, Flash.h or Switch.h wholesale: each enables non-diagnostic features.

The included scaffolds/diagnostic_observer.* are host-testable examples for snapshot/reason decoding only; they have no hardware bindings or hooks and are NOT the completed ECU port. Integrate or replace them with documented ABI/memory choices. Add target-independent tests for all packed values, invalid/stale states, state transitions and initialization. If later feature modules are developed, keep them separately compiled/tested with no active outputs in M0.

## Stage E — actual SH build and offline patch round-trip
Compile the actual A2WC511R target using the verified GNUSH toolchain. Inspect assembly/disassembly for instruction set, symbol resolution and ABI, and link map for actual section placement/overlap/size. Separate ELF/S-record simulator and metadata sections from real patch contents. Use the matched SharpTune patch path on an immutable-baseline COPY only; record all artifacts and inspect generated definitions. Investigate every warning that affects code generation or pointers.

Do a full byte diff, classify every changed range, verify expected before bytes, and round-trip patch removal to baseline under a documented checksum/edit-stamp policy. A raw reversible patch round-trip and a later checksum-corrected image are distinct artifacts. Prove the actual subarudbw checksum workflow; the checked-in ChecksumSubaruDBW name-only class is not by itself a checksum validator. No autonomous vehicle connection is necessary for offline checksum investigation.

## Stage F — clean reproducibility and independent review
Repeat the build in a clean output tree with the same pinned inputs/tools/settings. Normalize only documented nonfunctional build metadata (date/version stamping); report every difference and prove functional bytes match. An independent reviewer/task may audit the patch/ABI/feature-closure results without concurrent writes to shared artifacts. Do not enable many unbounded reviewer agents or repeat all work with unchanged inputs.

## Stage G — human-test package
Write a delivery folder containing actual source/patch/binary outputs, target definitions/logger, identity/sha256 manifests, generated map/disassembly, build logs, all changed-byte ranges and evidence-linked reviews. Use tools/release_check.py as an envelope check, not a replacement for engineering review. Identify the exact current calibration compatible with the installed hardware before a running-car candidate is recommended. A stock baseline may be suitable for offline code analysis but is not automatically a safe running tune for the VF52/3-port/3-inch MAF.

Provide a human-operated initial test procedure, expected diagnostic signals, abort/recovery criteria, backup/read-back plan and uncertainty list. Physical actions stay manual. A returned binary must say whether it is merely compiled, offline reviewed, or physically validated. Nothing in this run is claimed physically validated without actual evidence.

## Continue/stop policy
The user's authorization covers routine remediable host problems. Fix a missing package, wrong target selection, generated-file bug or compile error and continue. Stop only for an irreducible missing license/permission, necessary physical datum, unresolved architecture/allocation that cannot yet be proven, or exhausted service capability. Before stopping, finish independent feasible work and save the exact minimal blocker set plus a checkpoint. Never end the main run with only setup observations if a compiled implementation remains feasible.

No fixed overall run-time limit is imposed by these instructions. Individual hung commands have bounded deadlines and diagnoses. No indefinite automatic model re-prompting is installed. Session/usage limits can still interrupt; resume the exact saved session and disk checkpoint rather than starting over.
