# Existing IDA MCP — official default
Source checked 2026-09-25: https://github.com/HexRaysSA/ida-mcp (official Hex-Rays).
The current README requires Git and uv in PATH, IDA 9.4+ **with idalib**, and Python 3.11+. A version label alone does not establish that the user's beta installation includes a compatible idalib/Python arrangement. Inventory first.

## One installation route, not all routes at once
The vendor's automatic installation route is:
```powershell
uvx ida-hcli mcp install
```
It installs the GUI plugin and offers supported agent integrations. If that already configures Codex, do not also register another IDA MCP. Record the installed versions after successful setup and retain that tested environment.

The vendor's documented manual route is:
```powershell
uvx ida-hcli plugin install https://github.com/HexRaysSA/ida-mcp
codex plugin marketplace add HexRaysSA/codex-marketplace
codex plugin add ida-mcp@HexRaysSA
```
Use the actual installed Codex/hcli help if commands differ. Review installations and any permission prompts; do not run every alternative hoping one sticks.

A vendor-documented generic stdio alternative, only when no IDA entry already exists, is equivalent to:
```toml
[mcp_servers.ida]
command = "uvx"
args = ["--exclude-newer=1s", "ida-mcp", "stdio", "--agent=codex-a2wc511r"]
```
The upstream unpinned uvx invocation resolves a current release; record/pin the tested environment afterward. Do not overwrite the whole Codex configuration. Official Codex MCP documentation: https://developers.openai.com/codex/mcp

## GUI database smoke test
Save and make a consistent backup through IDA before enabling metadata edits. Ask Codex to enumerate the open IDA GUI databases and attach to the existing A2WC511R project. The GUI plugin supports the GUI route; without it the server can work headlessly, which is not a reason to reopen the same live IDB independently.

Use the discovered vendor tool schema to inspect processor, endian, input path, ROM size, CALID at 0x2000, and the functions at 0x147AC, 0x24950, 0x15A02 and 0x15A2C. Their existing labels and boundaries are in state/SYMBOLS.json. Record actual tool names/results in reports/IDA_SMOKE_TEST.md.

Do not assume an MCP connection enables a SuperH decompiler. The disassembler/processor support and decompiler licensing/support are distinct. This project can continue using disassembly and explicit byte/control-flow analysis.

## Community alternative
Existing community implementation: https://github.com/mrexodia/ida-pro-mcp
Use it only as a deliberate alternative if already working or if a concrete official-server compatibility issue is recorded. Follow its own pinned README and tool schemas. Do not run competing IDA MCPs against the same active project. Do not present a community plugin as vendor support.

## Permissions and migration
The official MCP can expose broader capabilities than the removed custom bridge. This package does **not** enforce a vendor-side read-only mode. Restrict tasks/permissions through the actual harness/plugin features and AGENTS.md; the user has authorized backed-up IDB metadata changes; record them without re-requesting permission, keep backups, and never use arbitrary debugger execution or ROM-byte patches as part of setup.

The custom integrations/ida directory is absent in v2. Stop its old server if still loaded (save IDA and restart the application after removing its registration). Inspect `codex mcp list`; remove the old custom entry only by the exact name present, historically `a2wc511r_ida`. Do not remove the vendor plugin or all MCP entries. Preserve all existing IDB names/comments/functions.

The retained tools/ida_checkpoint_export.py is an optional standalone static export helper, **not an MCP server**. Prefer vendor structured tools. It contains no auto-save call.
