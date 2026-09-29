"""Launch one persistent Codex CLI run at C:\\Dev with verified Astra + effort.
No background retry loop. Resume by explicit session ID. Authentication stays in Codex.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def command(codex:str,dev:str,model:str,effort:str,mode:str,resume:str|None,out:Path):
 base=[codex,'-C',dev,'-s','danger-full-access','-a','never','--search','-m',model,
       '-c','model_reasoning_effort='+json.dumps(effort)]
 if mode=='interactive':
  if resume:return base+['resume',resume]
  return base+['Read Astra_A2WC511R/START_CODEX_PROMPT.txt and execute the complete offline run contract. This is the main authorized run, not a planning-only request.']
 if resume:return base+['exec','resume',resume,'--json','--output-last-message',str(out/'last_message.md'),'-']
 return base+['exec','--skip-git-repo-check','--json','--output-last-message',str(out/'last_message.md'),'-']

def validate_readiness(readiness:dict,probe:dict,codex:Path,dev:Path,max_age=86400):
 if not readiness.get('ready_to_start_offline_port') or not probe.get('ready_for_model_run'):raise ValueError('Run/fix Prepare-CDev preflight first')
 for record in (readiness,probe):
  dt=datetime.fromisoformat(record['generated_at'])
  if dt.tzinfo is None or not 0<=(datetime.now(timezone.utc)-dt).total_seconds()<=max_age:raise ValueError('Preflight older than 24h/future-dated; re-run metadata readiness checks')
 if Path(probe['codex_exe']).resolve()!=codex.resolve() or hashlib.sha256(codex.read_bytes()).hexdigest()!=probe['codex_sha256']:raise ValueError('Codex executable changed since preflight')
 if Path(probe['cwd']).resolve()!=dev.resolve():raise ValueError('Preflight was for a different working directory')
 selected=probe.get('selected',{})
 if selected.get('effort')!='ultra' or 'astra' not in (selected.get('model','')+' '+str(selected.get('display_name',''))).lower():raise ValueError('Preflight did not verify Astra / ultra')
 return selected

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dev',type=Path,default=Path(r'C:\Dev'));p.add_argument('--codex',type=Path,required=True)
 p.add_argument('--mode',choices=['interactive','batch'],default='batch');p.add_argument('--resume');a=p.parse_args()
 if a.resume and not re.fullmatch(r'[A-Za-z0-9_-]{8,100}',a.resume):raise SystemExit('Invalid explicit session ID')
 if ROOT.name!='Astra_A2WC511R' or ROOT.parent.resolve()!=a.dev.resolve():raise SystemExit('Extract this package as C:\\Dev\\Astra_A2WC511R (or matching --dev parent).')
 pre=ROOT/'reports/local/preflight';r=json.loads((pre/'readiness.json').read_text());m=json.loads((pre/'model_probe.json').read_text());selected=validate_readiness(r,m,a.codex,a.dev)
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=ROOT/'reports/local/runs'/stamp;out.mkdir(parents=True,exist_ok=False)
 cmd=command(str(a.codex.resolve()),str(a.dev.resolve()),selected['model'],selected['effort'],a.mode,a.resume,out)
 (out/'launch.json').write_text(json.dumps({'argv':cmd,'mode':a.mode,'resume':a.resume,'generated_at':datetime.now(timezone.utc).isoformat()},indent=2)+'\n',encoding='utf-8')
 print('Working directory:',a.dev);print('Model:',selected['model'],'effort:',selected['effort']);print('Full host access; vehicle actions remain manual. Reports:',out,flush=True)
 if a.mode=='interactive':
  rc=subprocess.call(cmd,cwd=a.dev);print('Save the explicit session ID shown by Codex for same-chat resume.');raise SystemExit(rc)
 prompt=(ROOT/'START_CODEX_PROMPT.txt').read_text(encoding='utf-8') if not a.resume else (ROOT/'RESUME_CODEX_PROMPT.txt').read_text(encoding='utf-8')
 session=a.resume
 with (out/'events.jsonl').open('w',encoding='utf-8') as ev, (out/'stderr.log').open('w',encoding='utf-8') as err:
  proc=subprocess.Popen(cmd,cwd=a.dev,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',errors='replace',bufsize=1)
  proc.stdin.write(prompt);proc.stdin.close()
  try:
   for line in proc.stdout:
    ev.write(line);ev.flush()
    try:event=json.loads(line)
    except ValueError:continue
    if event.get('type')=='thread.started':
     session=event.get('thread_id') or session
     (ROOT/'state/LAST_CODEX_SESSION.json').write_text(json.dumps({'session_id':session,'run_dir':str(out),'cwd':str(a.dev)},indent=2)+'\n',encoding='utf-8')
     print('Session:',session,flush=True)
    if event.get('type') in ('turn.completed','turn.failed','error'):
     print(event.get('type'),json.dumps(event.get('usage',event.get('error',{}))),flush=True)
    item=event.get('item',{})
    if event.get('type')=='item.completed' and item.get('type')=='agent_message':print(item.get('text',''),flush=True)
   rc=proc.wait()
  except KeyboardInterrupt:
   proc.terminate();rc=proc.wait(timeout=15);print('Interrupted. Resume the saved session rather than starting over.')
  finally:proc.stdout.close()
 (out/'process_exit.json').write_text(json.dumps({'returncode':rc,'session_id':session},indent=2)+'\n',encoding='utf-8')
 print('Codex exited:',rc,'Session:',session)
 print('No automatic re-prompt was sent. A zero CLI exit is not proof the firmware deliverable passed its review gates.')
 raise SystemExit(rc)
if __name__=='__main__':main()
