# Astra / Codex CLI handoff v3 — extract to C:\Dev

**Active root: C:\Dev. Package: C:\Dev\Astra_A2WC511R.**

This full package preserves the v2 evidence and RomRaider native integration, adds the user's original Dev.zip unchanged, and provides an audited C:\Dev-based long-run contract plus deterministic host/model preflight. It uses the existing official Hex-Rays IDA MCP, not a custom IDA replacement.

Read docs/CLI_SETUP.md, then run tools/Prepare-CDev.ps1 ; it discovers Python/native Codex and the recorded GNUSH location, or asks for exact paths if missing/ambiguous. This performs local tests/metadata queries without sending a model task. Authenticate Codex first. Then run tools/Start-Astra.ps1 for one persistent Astra/Ultra full-access run at C:\Dev. The launcher passes START_CODEX_PROMPT.txt automatically in batch mode; do not paste the whole archive into the model.

## Most important audit result
The uploaded generated build is still **A8DH202X / Gratis_Debug / AUTO_TRANS0**, not A2WC511R. No matching A2WC511R target files were found. The stock baseline matching the prior hash and the saved IDB are now included. See docs/DEV_SNAPSHOT_AUDIT.md before touching source or claiming completion.

## What this archive does and does not deliver
It delivers the context, original resources, exact snapshot audit, installed-tool/model preflight, full-run instructions, native editor integration, deterministic analysis/build/report tools and tests. It does **not** contain a newly built validated A2WC511R ECU firmware. That is the next run's objective. Preflight readiness is not a guarantee every engineering uncertainty is resolved. A compiled binary is not physical validation.

The main run must complete all feasible offline phases rather than stop at setup or a plan. Original inputs stay preserved. Unresolved memory/hook/calibration/physical issues must be stated precisely, never filled with invented success. The first integrated vehicle-test objective is diagnostic-only with OEM outputs retained.

## Map
- AGENTS.md — current permissions, efficiency and evidence rules.
- START_CODEX_PROMPT.txt / RESUME_CODEX_PROMPT.txt — first run / same-session continuation.
- state/RUN_CONTRACT.md — every offline milestone and acceptance criterion.
- state/CURRENT_STATE.md, SYMBOLS.json, CHECKPOINT.json — durable state.
- reports/dev_snapshot — actual uploaded-tree audit, hashes, generation settings.
- evidence/Dev_2026-09-25_original.zip — the original source/IDB snapshot; do NOT extract over live C:\Dev.
- evidence/original — earlier logs, transcripts, files and images preserved from v2.
- integrations/romraider and romraider_mcp — existing native model bridge and MCP.
- integrations/project_mcp — readonly file/ROM/log analysis MCP.
- tools — preparation, model metadata probe, compiler smoke test, session launcher, build runner, release envelope validation, prior analysis utilities.
- scaffolds — host-testable diagnostic observer only, not an ECU target.
- docs / sources — source pins, official docs, program playbooks, history and references.

No global Codex auth files are replaced. Initial C:\Dev/AGENTS.md and project MCP updates are backed up. Old handoff copies stay historical. Use PACKAGE_MANIFEST.json to check initial package integrity; manifests are not a substitute for software review.
