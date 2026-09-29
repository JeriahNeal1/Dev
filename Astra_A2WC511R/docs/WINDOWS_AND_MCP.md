Current setup entry point: **CLI_SETUP.md and tools/Prepare-CDev.ps1**. Do not run the historical Bootstrap/register-generated script instead; v3 installs scoped C:\Dev config directly.

# v3 precedence note

Current host authorization and run order are in `../AGENTS.md`, `../state/RUN_CONTRACT.md` and `CLI_SETUP.md`. Actual uploaded source/binary identities superseding older unknowns are in `DEV_SNAPSHOT_AUDIT.md`. Keep the technical details below, but do not reimpose historical per-action host permission requests or stop after the first milestone. Physical actions remain human-controlled.

---

# Windows and MCP setup — v2

Stay on the working Windows tuning installation. This package does not migrate HEW, GNUSH, IDA, Tactrix or RomRaider to WSL, replace their runtimes, enable remote desktop, or expose a server to the LAN. Codex needs a local process/filesystem environment; verify actual permissions rather than assuming desktop access from a model name.

## IDA
Use the existing official Hex-Rays IDA MCP described in IDA_OFFICIAL_MCP.md. Install one integration and attach to the current GUI database. Keep manual database saves and backups. Do not recreate the removed custom IDA bridge.

## Project and RomRaider MCPs
Open PowerShell in the extracted workspace. Supply an actual external Python 3.10+ executable, separate from IDA's embedded Python:
```powershell
.\tools\Bootstrap.ps1 -PythonExe 'C:\actual\Python312\python.exe'
```
The example path must be replaced with the discovered executable. Bootstrap makes a local .venv, verifies the package and runs Python tests. No pip dependencies or global configuration changes are required. Review `config/mcp.generated.toml` and `config/register_mcp.generated.ps1`. The generated entries use the resolved workspace and .venv paths.

Run the registration script separately after reviewing existing `codex mcp list` entries. It prompts before registering the project and RomRaider servers. An existing name should be deliberately repointed, not blindly duplicated. Set RomRaider `tool_timeout_sec=280` in the reviewed MCP configuration so a local approval dialog has time to finish. Never automatically repeat a commit after a timeout; inspect the editor/history first.

## Start the existing RomRaider with the agent
First save/close any existing editor with unsaved work. Discover the exact working Java executable, application JAR, working directory, bitness, classpath and original JVM options. Do not change the installed JAR or global JAVA_TOOL_OPTIONS.
```powershell
.\tools\Start-RomRaider.ps1 `
  -JavaExe 'C:\actual\working-java\bin\java.exe' `
  -RomRaiderJar 'C:\actual\RomRaider\RomRaider.jar'
```
This starts the same application with a per-process `-javaagent` option. Preserve any required existing JVM flags with `-JvmArguments`, and application arguments with `-RomRaiderArguments`. The source-built agent targets Java 8 bytecode and uses Java's HTTP server module; the actual runtime must have these components. A custom JRE lacking them is a precise compatibility issue, not a reason to overwrite the tuning runtime.

The agent writes a random-token connection file beneath ACL-restricted `.runtime\romraider`. Do not copy it into prompts, screenshots, logs, Git or attachments. No public/LAN HTTP listener is used. A stale connection file causes launcher refusal; confirm the old process stopped before removing that file.

Initially omit `-EnableEdits`: reads, captures and reversible previews work, persistent editor commits are blocked. After disposable-copy acceptance, repeat the launcher with `-EnableEdits`; every commit still asks for one local YES/NO changeset approval. The agent has no vehicle I/O.

## Build versus runtime
A compiled agent JAR plus source is included. To rebuild it, use a separate JDK 11+:
```powershell
.\tools\Build-RomRaiderBridge.ps1 -JdkBin 'C:\actual\jdk\bin' -RunModelTests
```
This produces Java 8 class files; it does not change the JVM used by RomRaider. Test doubles are never packaged into the deployable JAR. Compile and run the transport smoke script only against those test doubles, not a real vehicle program.
