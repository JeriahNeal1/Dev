"""Explicit-path native IDA launcher with process-local plugin isolation."""
from pathlib import Path
from datetime import datetime,timezone
import os,sys,json,subprocess,argparse
ROOT=Path('C:/Dev/Astra_A2WC511R');WORK=ROOT/'work/diaphora';OUT=ROOT/'reports/local/diaphora'
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--script',type=Path,required=True)
    p.add_argument('--label',required=True)
    p.add_argument('--new-output',type=Path)
    p.add_argument('--export',type=Path)
    p.add_argument('--config',type=Path)
    p.add_argument('--wait',action='store_true')
    p.add_argument('--no-analysis',action='store_true')
    args=p.parse_args()
    assert args.input.is_file() and args.script.is_file()
    assert all(c.isalnum() or c in '-_' for c in args.label)
    directory=OUT/'jobs'/args.label;directory.mkdir(parents=True,exist_ok=False)
    if args.new_output:assert not args.new_output.exists()
    if args.export:assert not args.export.exists()
    command=['C:/Program Files/IDA Professional 9.4/ida.exe','-A','-L'+str(directory/'ida.log')]
    if args.no_analysis:command+=['-a']
    if args.new_output:command+=['-TBinary','-psh4b','-b0','-o'+str(args.new_output.resolve())]
    command+=['-S'+str(args.script.resolve()),str(args.input.resolve())]
    env=os.environ.copy();env['IDAUSR']=str(WORK/'ida_user_isolated');env['PYTHONDONTWRITEBYTECODE']='1'
    overrides={k:env[k] for k in ('IDAUSR','PYTHONDONTWRITEBYTECODE')}
    if args.export:
        env['DIAPHORA_AUTO']='1';env['DIAPHORA_EXPORT_FILE']=str(args.export.resolve())
        overrides.update({k:env[k] for k in ('DIAPHORA_AUTO','DIAPHORA_EXPORT_FILE')})
    if args.config:
        env['A2WC_DIAPHORA_JOB']=str(args.config.resolve());overrides['A2WC_DIAPHORA_JOB']=env['A2WC_DIAPHORA_JOB']
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    with (directory/'stdout.log').open('w') as stdout,(directory/'stderr.log').open('w') as stderr:
        process=subprocess.Popen(command,cwd='C:/Dev',env=env,startupinfo=startup,stdout=stdout,stderr=stderr)
    record={'created_utc':datetime.now(timezone.utc).isoformat(),'pid':process.pid,'argv':command,'environment_overrides':overrides,'uses_HCLI':False}
    (directory/'launch.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pid':process.pid,'directory':str(directory)}),flush=True)
    if args.wait:
        result=process.wait(timeout=3600);record['exit_code']=result
        (directory/'completion.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'exit_code':result,'directory':str(directory)}));sys.exit(result)
if __name__=='__main__':main()
