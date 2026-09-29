"""Local readiness tests, without sending a model task. Windows host execution required.
Run after authentication. This is readiness to START the port, not a completed firmware review.
"""
from __future__ import annotations
import argparse,json,platform,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from codex_model_probe import probe as model_probe
from toolchain_probe import probe as compiler_probe
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dev',type=Path,default=Path(r'C:\Dev'));p.add_argument('--codex',type=Path,required=True)
 p.add_argument('--cc',type=Path);p.add_argument('--model',default='gpt-6-astra');p.add_argument('--effort',default='ultra');a=p.parse_args()
 out=ROOT/'reports/local/preflight';out.mkdir(parents=True,exist_ok=True)
 r={'schema':1,'generated_at':datetime.now(timezone.utc).isoformat(),'dev':str(a.dev.resolve()),'host':platform.platform(),
    'python':sys.version,'prompt_started':False,'ready_to_start_offline_port':False,'blocking':[],'warnings':[]}
 if sys.platform!='win32':r['blocking'].append('Run host preflight on the actual Windows tuning workstation, not Linux/WSL.')
 if not a.dev.is_dir():r['blocking'].append('Dev root not found')
 for n in ('MerpMod','SharpTune','SubaruDefs','SubaruRoms'):
  if not (a.dev/n).is_dir():r['blocking'].append('Missing expected tree '+n)
 test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,capture_output=True,text=True,errors='replace',timeout=240)
 (out/'python_tests.txt').write_text(test.stdout+'\n'+test.stderr,encoding='utf-8')
 r['tests_returncode']=test.returncode
 if test.returncode:r['blocking'].append('Package Python tests failed; see report')
 if not shutil.which('git'):r['blocking'].append('Git unavailable in current PATH')
 cc=a.cc
 if not cc:
  guess=Path(r'C:\Program Files (x86)\Renesas\HEW\Tools\KPIT\GNUSH-ELF\v13.01')
  hits=list(guess.rglob('sh-elf-gcc.exe')) if guess.is_dir() else []
  if len(hits)==1:cc=hits[0]
 try:
  if not cc:raise ValueError('Supply --cc with the installed GNUSH sh-elf-gcc.exe; HEW registration alone is not a compile test.')
  smoke=compiler_probe(cc,out/'sh2e_smoke');r['toolchain_ready']=smoke['toolchain_ready']
  if not smoke['toolchain_ready']:r['blocking'].append('Actual GNUSH smoke compilation/ELF architecture check failed')
 except Exception as e:r['toolchain_ready']=False;r['blocking'].append(str(e))
 try:
  m=model_probe(a.codex,a.dev,a.model,a.effort)
  # Validate this installed parser's launch/resume flags without starting a task.
  if m.get('selected'):
   from run_codex import command
   r['cli_help_checks']=[]
   for resume in (None,'00000000-0000-0000-0000-000000000000'):
    cmd=command(str(a.codex.resolve()),str(a.dev.resolve()),m['selected']['model'],m['selected']['effort'],'batch',resume,out)
    cmd=cmd[:-1]+['--help']
    h=subprocess.run(cmd,cwd=a.dev,capture_output=True,text=True,errors='replace',timeout=30)
    name='resume_help.txt' if resume else 'launch_help.txt'
    (out/name).write_text(h.stdout+'\n'+h.stderr,encoding='utf-8')
    r['cli_help_checks'].append({'kind':name,'returncode':h.returncode})
    if h.returncode:r['blocking'].append('Installed CLI rejected launch/resume flags. See '+name)
 except Exception as e:m={'ready_for_model_run':False,'prompt_started':False,'error':str(e)}
 (out/'model_probe.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8');r['model_ready']=m['ready_for_model_run']
 if not m['ready_for_model_run']:r['blocking'].append(m.get('error','Model preflight failed'))
 try:
  t=subprocess.run([str(a.codex),'mcp','list','--json'],cwd=a.dev,capture_output=True,text=True,errors='replace',timeout=60)
  # Names/config only; do not copy credentials or complete server environment variables.
  names=[]
  if t.returncode==0:
   data=json.loads(t.stdout)
   entries=data if isinstance(data,list) else data.get('servers',[])
   names=[x.get('name') for x in entries if isinstance(x,dict) and x.get('name')]
  r['configured_mcp_names']=names
  if not any('ida' in x.lower() for x in names):r['warnings'].append('Official IDA MCP was not visible in this metadata command. Install/verify vendor plugin before the main run.')
 except Exception:r['warnings'].append('MCP list metadata unavailable. Live tool capability discovery remains the first Codex task.')
 r['warnings']+=['Live IDA 9.4 Beta/RomRaider acceptance must run locally; a configured server name is not proof of a working connection.',
 'Wrong-target historical build, unproven RAM allocation and current-flash identity remain development gates, not passed checks.',
 'Normal logs do not prove communication-fault handling. No unattended vehicle actions.']
 r['ready_to_start_offline_port']=not r['blocking']
 r['status']='READY_TO_START_OFFLINE_PORT_NOT_FLASH_APPROVAL' if not r['blocking'] else 'FIX_PREFLIGHT_BLOCKERS_BEFORE_MAIN_PROMPT'
 (out/'readiness.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2))
 raise SystemExit(0 if r['ready_to_start_offline_port'] else 2)
if __name__=='__main__':main()
