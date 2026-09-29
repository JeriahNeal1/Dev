"""Install only this handoff's root instruction block and project MCP entries.
Back up before each edit. Never edits the source repositories, IDB, or a ROM.
Python 3.11+ (tomllib). No model calls.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys, tomllib
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BEGIN='<!-- ASTRA_A2WC511R_V3_BEGIN -->';END='<!-- ASTRA_A2WC511R_V3_END -->'

def backup_write(path:Path, text:str, backup_dir:Path):
 data=text.encode('utf-8')
 if path.exists() and path.read_bytes()==data:return {'path':str(path),'changed':False}
 record={'path':str(path),'changed':True,'backup':None}
 if path.exists():
  old=path.read_bytes();digest=hashlib.sha256(old).hexdigest()
  backup_dir.mkdir(parents=True,exist_ok=True)
  dest=backup_dir/(path.name+'.'+digest[:16]+'.bak')
  if dest.exists() and dest.read_bytes()!=old:raise ValueError('Backup collision')
  if not dest.exists():dest.write_bytes(old)
  record.update(backup=str(dest),before_sha256=digest)
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.a2wc-tmp');tmp.write_bytes(data);tmp.replace(path)
 record['after_sha256']=hashlib.sha256(data).hexdigest();return record

def root_instructions(dev:Path, package:Path):
 rel=package.relative_to(dev).as_posix()
 return f'''{BEGIN}
# A2WC511R: current Codex CLI mission (v3)
Working directory is `{dev}`. The active handoff is `{rel}`.
Read `{rel}/AGENTS.md`, `{rel}/state/CURRENT_STATE.md`,
`{rel}/state/RUN_CONTRACT.md`, and `{rel}/START_CODEX_PROMPT.txt` first.
This supersedes earlier A2WC511R handoff planning/permission defaults, not unrelated project rules.
The user authorizes full local development access, vendor-sourced installs, setup repair,
backed-up IDA metadata changes, source edits, offline builds and tests without repeated permission questions.
Do not stop at a plan or re-request that authorization. Complete all feasible offline stages.
No autonomous ECU flash/erase, live vehicle writes/actuation or driving. Actual hardware actions remain human-run.
Keep original inputs and the existing IDB/repositories; use staged builds and exact hashes.
Use official Hex-Rays IDA MCP, never restore the removed custom IDA server.
Record decisions/checkpoints under `{rel}/state` and reports under `{rel}/reports/local`.
Do not treat evidence archives or old handoff copies as active instructions.
{END}
'''

def put_block(old:str,new:str):
 if old.count(BEGIN)!=old.count(END) or old.count(BEGIN)>1:raise ValueError('Malformed prior managed instruction block')
 if BEGIN in old:return re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?',lambda _:new,old,flags=re.S)
 return new+'\n'+old

def mcp_tables(package:Path, dev:Path, py:Path):
 q=lambda x:json.dumps(str(x))
 return {
 'mcp_servers.a2wc511r_project':f'''[mcp_servers.a2wc511r_project]
command = {q(py)}
args = [{q(package/'integrations/project_mcp/server.py')}, "--root", {q(dev)}]
startup_timeout_sec = 30
tool_timeout_sec = 120
''',
 'mcp_servers.romraider':f'''[mcp_servers.romraider]
command = {q(py)}
args = [{q(package/'integrations/romraider_mcp/server.py')}, "--root", {q(package)}, "--connection", {q(package/'.runtime/romraider/connection.json')}]
startup_timeout_sec = 30
tool_timeout_sec = 280
'''}

def replace_tables(old:str, additions:dict):
 parsed=tomllib.loads(old)
 # This managed edit supports standalone TOML table declarations. Preserve all others.
 for name,block in additions.items():
  parts=name.split('.');node=parsed
  present=True
  for k in parts:
   if not isinstance(node,dict) or k not in node:present=False;break
   node=node[k]
  header='['+name+']'
  matches=list(re.finditer(r'(?m)^\['+re.escape(name)+r'\][ \t]*(?:#[^\n]*)?\r?$',old))
  if present and not matches:raise ValueError('Existing inline/quoted table needs manual merge: '+name)
  if len(matches)>1:raise ValueError('Duplicate table '+name)
  if matches:
   start=matches[0].start();tail=old[matches[0].end():]
   nxt=re.search(r'(?m)^\[',tail);end=matches[0].end()+nxt.start() if nxt else len(old)
   old=old[:start]+block+'\n'+old[end:]
  else:old=old.rstrip()+'\n\n'+block
 old=old.rstrip()+'\n'
 tomllib.loads(old);return old

def install(dev:Path, package:Path, py:Path):
 dev=dev.resolve();package=package.resolve();py=py.resolve()
 if not package.is_relative_to(dev):raise ValueError('Extract package inside the intended C:\\Dev tree first')
 backups=package/'.runtime/setup_backups';changes=[]
 a=dev/'AGENTS.md';old=a.read_text(encoding='utf-8-sig') if a.exists() else ''
 changes.append(backup_write(a,put_block(old,root_instructions(dev,package)),backups))
 cfg=dev/'.codex/config.toml';old=cfg.read_text(encoding='utf-8-sig') if cfg.exists() else ''
 changes.append(backup_write(cfg,replace_tables(old,mcp_tables(package,dev,py)),backups))
 r={'generated_at':datetime.now(timezone.utc).isoformat(),'dev_root':str(dev),'package':str(package),
    'python_exe':str(py),'changes':changes,'official_ida':'configured separately by the vendor plugin',
    'note':'No global Codex auth/config, compiler, ROM, source repository or database modified.'}
 (package/'config/host_paths.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dev',type=Path,default=Path(r'C:\Dev'));p.add_argument('--python',type=Path,default=Path(sys.executable));a=p.parse_args()
 print(json.dumps(install(a.dev,ROOT,a.python),indent=2))
if __name__=='__main__':main()
