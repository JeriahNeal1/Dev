"""Generate local Codex MCP snippets; never edit global config automatically."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
py=ROOT/'.venv/Scripts/python.exe'
def q(v):return json.dumps(str(v))
def ps(v):return "'"+str(v).replace("'","''")+"'"
text=f'''# Merge only reviewed entries. IDA is installed separately using the official Hex-Rays plugin.
# Do not register an additional IDA server if the official plugin already registered it.
[mcp_servers.a2wc511r_project]
command = {q(py)}
args = [{q(ROOT/'integrations/project_mcp/server.py')}, "--root", {q(ROOT)}]
startup_timeout_sec = 20
tool_timeout_sec = 60

[mcp_servers.romraider]
command = {q(py)}
args = [{q(ROOT/'integrations/romraider_mcp/server.py')}, "--root", {q(ROOT)}, "--connection", {q(ROOT/'.runtime/romraider/connection.json')}]
startup_timeout_sec = 20
tool_timeout_sec = 280
'''
(ROOT/'config/mcp.generated.toml').write_text(text,encoding='utf-8')
script=f'''# REVIEW; no installs, admin elevation or automatic editor launch.
$ErrorActionPreference = 'Stop'
codex mcp list
if ($LASTEXITCODE -ne 0) {{ throw 'Inspect installed codex mcp --help.' }}
$Answer = Read-Host 'After checking name conflicts, type REGISTER for project and RomRaider MCPs'
if ($Answer -cne 'REGISTER') {{ throw 'Cancelled.' }}
codex mcp add a2wc511r_project -- {ps(py)} {ps(ROOT/'integrations/project_mcp/server.py')} --root {ps(ROOT)}
if ($LASTEXITCODE -ne 0) {{ throw 'Project MCP registration failed.' }}
codex mcp add romraider -- {ps(py)} {ps(ROOT/'integrations/romraider_mcp/server.py')} --root {ps(ROOT)} --connection {ps(ROOT/'.runtime/romraider/connection.json')}
if ($LASTEXITCODE -ne 0) {{ throw 'RomRaider MCP registration failed.' }}
codex mcp list
# Set RomRaider tool_timeout_sec=280 in the reviewed config to allow local approval.
# Official IDA setup: uvx ida-hcli mcp install ; see docs/IDA_OFFICIAL_MCP.md.
'''
(ROOT/'config/register_mcp.generated.ps1').write_text(script,encoding='utf-8')
print('Generated project/RomRaider snippets only. Official IDA setup is separate.')
