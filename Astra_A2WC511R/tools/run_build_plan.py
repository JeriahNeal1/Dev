"""Run an explicitly reviewed offline build plan in a NEW output directory.
Captures argv, exit codes, output hashes and logs. It does not infer success from HEW's banner.
This is orchestration, not an OS security boundary. No ECU/J2534 actions belong in a plan.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from project_core import sha256

def run(plan:dict,base:Path,out:Path):
 if plan.get('target_calid')!='A2WC511R':raise ValueError('Target must be A2WC511R')
 if plan.get('reviewed') is not True:raise ValueError('Build plan must be reviewed, populated and marked reviewed=true first')
 if out.exists():raise ValueError('Use a new run directory; never silently reuse stale artifacts')
 base=base.resolve();out=out.resolve();out.mkdir(parents=True)
 report={'schema':1,'started_at':datetime.now(timezone.utc).isoformat(),'target':'A2WC511R','passed':False,'steps':[],'out':str(out)}
 def save(): (out/'build_run.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 try:
  for inp in plan.get('inputs',[]):
   p=(base/inp['path']).resolve()
   if not p.is_relative_to(base) or not p.is_file() or sha256(p)!=inp['sha256']:raise ValueError('Build input mismatch: '+inp['path'])
  if not plan.get('inputs') or not plan.get('steps'):raise ValueError('Plan needs hashed inputs and commands')
  def expand(s):return str(s).replace('${OUT}',str(out)).replace('${BASE}',str(base))
  for n,step in enumerate(plan['steps']):
   cmd=[expand(x) for x in step['argv']]
   if not cmd or Path(cmd[0]).name.lower().startswith(('ecuflash','j2534')):raise ValueError('Vehicle-facing executable prohibited in offline build plan')
   exe=Path(cmd[0]);cwd=Path(expand(step.get('cwd','${BASE}'))).resolve()
   if not exe.is_absolute() or not exe.is_file():raise ValueError('Use a discovered absolute tool executable path')
   if 'exe_sha256' not in step or sha256(exe)!=step['exe_sha256']:raise ValueError('Tool executable hash mismatch')
   outputs=[Path(expand(x)).resolve() for x in step.get('outputs',[])]
   if any(not p.is_relative_to(out) for p in outputs):raise ValueError('Declared artifacts must be inside this new run directory')
   if any(p.exists() for p in outputs):raise ValueError('Step output already exists before command')
   record={'name':step.get('name',str(n)),'argv':cmd,'cwd':str(cwd)};report['steps'].append(record);save()
   start=time.monotonic();log=out/f'{n:02d}.log'
   try:
    with log.open('w',encoding='utf-8') as f:
     f.write('ARGV '+json.dumps(cmd)+'\n');f.flush()
     p=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,text=True,timeout=step.get('timeout_sec',1800))
    record['returncode']=p.returncode
    if p.returncode:raise ValueError('Build command returned nonzero: '+record['name'])
   except subprocess.TimeoutExpired as e:raise ValueError('Command deadline exceeded: '+record['name']) from e
   record['duration_sec']=round(time.monotonic()-start,3);record['log']=log.name
   missing=[str(p) for p in outputs if not p.is_file() or not p.stat().st_size]
   if missing:raise ValueError('Expected nonempty output missing: '+repr(missing))
   record['artifacts']=[{'path':str(p.relative_to(out)),'size':p.stat().st_size,'sha256':sha256(p)} for p in outputs];save()
  report['passed']=True
 except Exception as e:report['error']=str(e)
 finally:report['finished_at']=datetime.now(timezone.utc).isoformat();report['note']='Successful commands/artifacts do not equal flash approval. Run independent identity, diff, checksum, ABI/memory and calibration reviews.';save()
 return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=run(json.loads(a.plan.read_text(encoding='utf-8-sig')),a.base,a.out);print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 2)
if __name__=='__main__':main()
