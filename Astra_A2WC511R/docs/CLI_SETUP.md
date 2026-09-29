# Windows LTSC + Codex CLI: setup without spending a model task

## Target layout
Extract this archive into C:\Dev. It adds a new C:\Dev\Astra_A2WC511R folder alongside MerpMod, SharpTune, SubaruDefs and SubaruRoms. It does not replace those trees. The embedded Dev snapshot is archival only. Keep the package folder name for the launcher's relative instruction path.

C:\Dev\AGENTS.md receives one backed-up managed instruction block during preparation. C:\Dev\.codex\config.toml receives only the two project/RomRaider MCP entries; other tables remain intact. Global auth/config is not overwritten. Trust C:\Dev in the Codex UI if the client requires it; opening the CLI without sending a task is distinct from starting the main model request.

## CLI and external Python
Use a native Codex executable >=0.153.0 and an external Python3.11+ (separate from IDA's embedded interpreter). Current model IDs/efforts are discovered from the signed-in account. The requested default is `gpt-6-astra` with `ultra`, but neither a marketing label nor a hardcoded string establishes availability. The preflight stops rather than silently substituting a different model/effort.

OpenAI's current official standalone Windows installer is at https://chatgpt.com/codex/install.ps1, also linked by https://github.com/openai/codex. A standalone CLI avoids Microsoft Store and npm/Node runtime dependencies. Use the vendor route rather than random Store-repair scripts. Downloading/installing a CLI does not mean this old LTSC build has been tested by us; running --version and the local preflight is required.

Official install command (runs the vendor installer; no model task):
```powershell
powershell -ExecutionPolicy Bypass -c "irm https://chatgpt.com/codex/install.ps1 | iex"
```
A more inspectable alternative is to download that script to a file, inspect it, record its hash, then execute it. Keep existing working tooling and avoid changing OS edition solely for the Store app. Sign in using `codex login`, then locate the native executable:
```powershell
Get-Command codex -All | Select-Object Source, CommandType
where.exe codex
```
Supply the actual codex.exe to the preparation script. An npm .ps1/.cmd launcher is not a native executable and is deliberately rejected by the Python metadata probe. Locate its underlying executable or use the official standalone install. Do not rename a script to .exe.

## Prepare (no model generation)
Start with automatic discovery (no model task):
```powershell
& C:\Dev\Astra_A2WC511R\tools\Prepare-CDev.ps1
```
If an executable is missing or ambiguous, supply the discovered paths explicitly:
```powershell
Set-Location C:\Dev
& .\Astra_A2WC511R\tools\Prepare-CDev.ps1 `
  -PythonExe 'C:\ACTUAL\PATH\python.exe' `
  -CodexExe 'C:\ACTUAL\PATH\codex.exe' `
  -GnushGcc 'C:\ACTUAL\KPIT\BIN\sh-elf-gcc.exe'
```
The three ACTUAL paths must be real discovered executables, not copied placeholders. Omitting -GnushGcc searches the recorded KPIT v13.01 directory; if multiple compiler copies exist, specify the correct one.

The script verifies initial package hashes, makes a local venv without installing Python packages, installs the backed-up C:\Dev instruction/MCP entries, audits the current Dev tree, runs utility tests, compiles/links/disassembles a non-firmware SH2E smoke object and queries authenticated Codex metadata. On the first preparation it checks every original manifest entry. Later preparation runs preserve immutable evidence and record intentional working-file changes instead of rejecting normal checkpoint/source edits; a changed manifest still requires explicit review. It uses initialize/model-list/config/usage methods, not thread/start or turn/start. It creates no ECU firmware and performs no vehicle I/O.

The model probe also checks `codex login status` and the configured provider. It checks advertised Ultra support and rejects a detected Fast/priority setting for this efficiency-first run. It does not purchase credits or redeem resets. Unsupported metadata/schema/account responses produce a bounded precise error instead of launching a speculative paid prompt.

Result: reports\local\preflight\readiness.json. READY_TO_START_OFFLINE_PORT is not a claim the code is built or safe. Local MCP application acceptance remains part of the actual run. Preflight failures require remediation, not endless retries.

## IDA and RomRaider
Keep the existing IDB open and saved/backed up. Install/verify official Hex-Rays IDA MCP using docs/IDA_OFFICIAL_MCP.md. The current vendor route is `uvx ida-hcli mcp install`. Inspect the local beta's idalib availability and the vendor tool schema. Do not install a second competing IDA MCP. It may need a one-time app/plugin restart; no prompt can replace license activation or UAC.

Prepare uses a root-scoped project MCP and package-scoped RomRaider MCP. The latter's launch/connection path remains in this package's .runtime directory. Start RomRaider read-only on a disposable offline copy using tools/Start-RomRaider.ps1; use the actual installed Java and RomRaider JAR. All real editor acceptance still follows docs/ROMRAIDER_ACCEPTANCE.md. Do not start competing vehicle clients.

## Main run
```powershell
& C:\Dev\Astra_A2WC511R\tools\Start-Astra.ps1 `
  -CodexExe 'C:\ACTUAL\PATH\codex.exe'
```
After successful preflight, `Start-Astra.ps1` can also be run without arguments: it reuses the verified executable path. Default is one long **batch** run with persisted JSON events and final output. It reads START_CODEX_PROMPT.txt from disk, uses the verified model/effort and launches at C:\Dev with danger-full-access, approval never, and live web search. For the terminal chat interface add `-Mode interactive`. These settings grant host permissions, not missing GUI tools, admin rights or unlimited usage.

No arbitrary overall timeout is imposed by the launcher. It does not automatically re-prompt when a turn finishes. Each command can have a sensible timeout without imposing a short time limit on the whole engineering task. Rate limits, context, connectivity and process exits still exist.

## Resume the same chat
The batch launcher writes state\LAST_CODEX_SESSION.json when it receives thread.started. Resume by that explicit ID:
```powershell
& C:\Dev\Astra_A2WC511R\tools\Start-Astra.ps1 `
  -CodexExe 'C:\ACTUAL\PATH\codex.exe' -Resume 'ACTUAL_SESSION_ID'
```
Refresh the deterministic preflight after24h or if the CLI binary changed. Interactive sessions expose their own ID; copy it rather than blindly selecting --last from another project. Disk checkpoints protect continuity even if a transcript is compacted. Do not use --ephemeral.

## Practical host preparation
Back up the working IDB/source/config and maintain sufficient disk space. Keep stable AC/network and prevent sleep for the planned work session using your normal Windows settings. Close conflicting vehicle clients and disconnect Tactrix while unattended installation/build work runs. Do not disable Windows security or upgrade the OS blindly. Codex can make targeted reversible setup fixes under the user's authorization; physical flashing and driving stay manual.

## Sources (checked 2026-09-25)
- https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex
- https://learn.chatgpt.com/docs/app-server
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/developer-commands?surface=cli
- https://learn.chatgpt.com/docs/windows/windows-sandbox
- https://github.com/openai/codex
- https://github.com/HexRaysSA/ida-mcp
