# A2WC511R — current Codex CLI instructions, v3

## Mission and working directory

Your actual working directory is **C:\Dev** on the user's existing Windows 10 Enterprise LTSC 2019 (1809, build 17763.9245) workstation. This handoff lives in `C:\Dev\Astra_A2WC511R`. Continue the existing A2WC511R / 2F12515306 / EJ255 / 5EAT MerpMod **source port**. Do not substitute a different calibration ID, rebuild an unrelated ECU, or pretend this is a clean-room replacement of the entire OEM firmware.

The user requests Astra at the locally advertised Ultra reasoning level, a long coherent run, maximum useful progress per prompt, and a compiled result for subsequent human testing. The launcher verifies the model/effort through Codex metadata; do not silently downgrade or enable Fast. A capable model still needs real evidence. Do not declare success from a compiler banner, hide unresolved assumptions, or relabel an unvalidated candidate as ready to flash.

## Explicit user authorization — host development

The user has already authorized full local development access and internet access: vendor-sourced software/dependency installation, configuration repair, source edits, local branches/staging, build-system changes, test execution, helper/MCP setup, and backed-up IDA metadata changes. Do not repeatedly request the same permission. Use those capabilities to fix remediable build problems instead of stopping at a plan.

Inspect before changing and record changes. Preserve a restorable backup before replacing tools, configurations, IDBs or generated target files. Prefer side-by-side tools and per-project configuration to breaking the existing Windows tuning stack. UAC, license activation, sign-in and physically opening/connecting hardware remain real host constraints, not abilities conferred by a prompt. Do not disable security software or change OS edition as a shortcut. No public upload of private ROMs, VINs, logs, credentials, licenses or IDBs. No purchases or use of unlicensed proprietary tools are implied.

## Human physical boundary

No autonomous ECU/TCU flash, erase, recovery, live memory writes, CAN injection, actuator commands, brake/throttle/RPM commands, vehicle driving or ECUFlash Write/Test Write clicks. Those actions are for the user after a precisely identified artifact and test plan are reviewed. Host full access is not physical vehicle control. Keep OEM oxygen sensors/exhaust configuration; the wideband-only/hood-dump idea is deferred.

The first integrated artifact is **diagnostic-only**: record/evaluate state and rejection reasons while preserving OEM timing, fueling, MAF, WGDC, rev limits, sensor control, transmission torque interventions and protections. Implement later feature modules and tests separately if useful, but do not enable launch/ALS outputs on unsupported assumptions. The requested first-run compiled deliverable is not an instruction to invent a safe calibration or skip validation.

## Read order and token discipline

On first start read `state/CURRENT_STATE.md`, `state/RUN_CONTRACT.md`, `reports/dev_snapshot/dev_audit.md`, `docs/DEV_SNAPSHOT_AUDIT.md`, `docs/MERPMOD_VERSION_AND_BUILD.md`, then the applicable integration playbooks. Consult `state/SYMBOLS.json` and the original evidence only for the current question. After compaction read the current checkpoint, next actions and decisions, not the entire archive again.

Do not dump 8 MB XMLs, a whole ROM, thousands of raw CSV lines, or screenshots already covered by an authoritative artifact into model context. Parse locally and return bounded summaries plus report paths/hashes. Use native CLI/API/MCP before GUI clicking. Cache evidence by input hash. Do not reinstall a working dependency on every run. Do not do unrelated cleanup/beautification while the actual target build is blocked.

## Actual uploaded Dev state — prioritize these facts

- MerpMod HEAD `8720d209df107a81fd171131cfba96d8cae1f118`; source path `C:\Dev\MerpMod\MerpMod`.
- SharpTune **source** HEAD `ecabea89615132dac2de37c05f72adae16d966d1`. The copied binaries have the same SHA256 `248eb7f012d0edcb84048ee01f99f7fa49094942c25a3b53e75fbfcb957de8af`; the historical executed banner was RC2-10-gfcf9fdb. Reconcile binary versus source; do not assume the exe came from current HEAD.
- SubaruDefs HEAD `9b2992eba8133fe5338b89aa77b22c1bb14d6507`.
- Existing generated target/config are **A8DH202X / Gratis_Debug / AUTO_TRANS 0**. No A2WC511R target files exist in the uploaded Targets directory. Existing objects/MOT/ELF are not the requested port.
- Actual compiler records use **SH-2E, big-endian, -m2e -mrenesas -mieee**, KPIT GNUSH 13.01/GCC 4.7. IDA's SH4B preset is not the hardware instruction-set target.
- OEM `A2WC511R.bin` and Backup `A2WC511R_STOCK_ROMRAIDER.bin` match the historical baseline hash `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`. OEM `A2WC511R_STOCK_ROMRAIDER.bin` instead hashes `a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96`; only 0xFFC4C..0xFFC4F differ, FF FF FF FF -> 26 08 23 01. That does not identify the currently flashed modified calibration.
- The uploaded Dev includes the existing `.i64` and sidecars. Keep the latest local live database; the archive is a recovery reference, not authority to overwrite newer work.
- Windows CRLF causes huge apparent Linux Git diffs. Record raw status and use `git -c core.autocrlf=true diff --ignore-space-at-eol` for semantic review. Untracked copied SharpTune source exists inside MerpMod; never `git clean -fdx`.

## Complete the offline work, not just the first checklist

Follow `state/RUN_CONTRACT.md` through inventory, interface acceptance, ABI/memory/hook audit, exact target/config, repeatable build, full binary diff, patch round-trip and checksum review, then human handoff. Search local files before asking the user for a log. Missing physical tests are not a reason to stop unrelated offline implementation/test work. Do not claim those tests passed or use fake telemetry to satisfy them.

Parallel work is permitted for independent bounded source analysis/test tasks in separate worktrees. Keep one writer to the live IDB, open RomRaider buffer, and release artifacts. Give subagents focused inputs and acceptance criteria; no duplicate full-project investigations. Prefer one lead synthesis/review over many expensive full-context agents.

## Non-negotiable evidence distinctions

- Raw gear/current/requested interpretations are supported by historical traces and logs, not literal proof of physical clutch engagement. `packed==0x11` is a gear predicate, not data freshness.
- `FFFF4CA1` is not a proven global freshness guarantee. `FFFF4C50 & 0x02` is not a proven CAN health flag. Ordinary start/drive logs alone cannot prove communication-fault behavior.
- FF-filled ROM space and no exact pointer matches do not prove memory is unused. Audit indirect/VBR/base+offset/DMA/stack/reset accesses and exact required byte span.
- Hook pointer matches establish old bytes, not the complete call ABI/timing/continuation. Trace all enabled hook side effects and feature closure.
- Existing Gratis/Flash defaults turn on more than diagnostics. Switch couples multiple systems. Do not equate disabled gains with absence of intervention.
- Simulator and metadata addresses in HEW/S-record output are not real flash addresses. Never flatten the whole MOT/ELF into a ROM.
- IDB comments, logger XML, editor ROM, on-disk ROM, stock baseline and current ECU flash are different artifacts. Track each by identity and hash.

## Tool and persistence rules

Use the existing **official Hex-Rays IDA MCP** and its discovered schema. Do not resurrect the custom IDA server or install competing IDA MCPs into the same database. Save/backup through supported vendor operations or the GUI. Never use `ida_kernwin.save_database()` (absent in this 9.4 Beta). Creating displayed disassembly does not create a persistent code item; validate/create the exact instruction before adding function/xref metadata. Distinguish data refs from real call refs. No mass undefine/reanalysis as a shortcut.

Use the native RomRaider bridge only after actual local acceptance on disposable offline copies. It supports model snapshots, proposal/quantization preview and one local confirmation per batch, not per-cell manual entry. Its implementation keeps that confirmation; build staging does not need you to bypass it. Preserve logs and tables; no screen-based speculative editing or invented universal optimizer. Hash-linked logs, units, filters, table selection, sample timing and achieved values are mandatory.

At every completed milestone or genuine interruption update `state/CURRENT_STATE.md`, `state/NEXT_ACTIONS.md`, `state/DECISIONS.md`, `state/SYMBOLS.json` as applicable, `state/SESSION_LOG.md`, and `state/CHECKPOINT.json`. Record exact commands and full logs on disk, plus a compact result. Keep the explicit Codex session ID. Clear IDA console text only after saving output. A session or context reset must not force repetition.

## Completion and stopping

Do not end with an offer to do the actual work later, a skeleton target, or only a list of tasks if the remaining work is executable offline. Finish a reproducible diagnostic port and review package when evidence allows. If a hard physical/licensing/architectural prerequisite remains after reasonable alternatives, preserve every completed artifact, produce an exact blocking dependency graph and one minimal human action list, and stop without fabricated success. Do not spin or re-prompt indefinitely to consume allowance. A rate limit or session interruption is a checkpoint/resume event, not a reason to start a new project chat.

## Emulator is a first-class parallel project

During the A2WC511R MerpMod source-port run, maintain `C:\Dev\A2WC511R_Sim` as an isolated software-validation environment. Its purpose is to reduce dependence on live-car logging for firmware/memory reverse engineering. It is not a physical engine/transmission simulator and its success never proves a calibration or active-control strategy physically safe.

### Persistent rules

- Target CPU semantics are SH-2E big-endian for the real SH7058 ECU. IDA's SH4B analysis module is not the executable target.
- Prefer an existing lawful, auditable SH-2/SH-2E core if it fits. If implementing a core, support only needed instructions first and fail explicitly on unsupported opcodes.
- Never silently stub an unknown instruction/peripheral in a way that can make a test falsely pass.
- Load ROMs read-only and identify every run by SHA-256. Apply patches as overlays or disposable copies.
- Simulator code/data/metadata must never be flattened into a 1MiB ECU candidate.
- Keep stock-vs-patched differential tests deterministic.
- Keep one writer for live IDA and live RomRaider editor state.
- Use official Hex-Rays IDA MCP for static evidence; use emulator traces as dynamic evidence; neither alone proves all code paths.
- Preserve candidate/unverified labels for unknown RAM semantics.
- Model 5EAT software-visible state and virtual sensors/switches; do not spend the main run building physically realistic engine or hydraulic dynamics.
- Build an address-propagation/watchpoint facility specifically for reverse engineering RAM and function interactions.
- Aim for unchanged RomRaider logger-definition compatibility through a virtual SSM/J2534 or RomRaider simulator backend, installed side-by-side with the real Tactrix stack.
- Never overwrite/replace the real OpenPort/J2534 provider globally.
- Each independently verified routine/address should gain a regression test.
- A simulator regression failure blocks reliance on the simulator for that path; it does not authorize guessing.
- A simulator pass may reduce live-car testing but does not replace bench/vehicle tests for timing-sensitive peripherals, analog/electrical behavior, combustion, boost, AFR, knock, transmission hydraulics, watchdog/interrupt timing not actually modeled, or any active-control safety decision.

### Priority order

1. Memory model + trace/watchpoint API.
2. Function harness for known A2WC511R routines.
3. Virtual sensors/switches + 5EAT state/scenarios.
4. Stock-vs-patched differential execution.
5. Table/Pull2D/Pull3D validation.
6. Unchanged-definition virtual RomRaider logging transport/backend.
7. Wider CPU/peripheral coverage only when demanded by a concrete tested path.

Do not let pursuit of perfect emulation prevent completion of the diagnostic-only A2WC511R port. Report precise coverage and limitations instead.
