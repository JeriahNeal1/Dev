import sys
sys.dont_write_bytecode=True
import argparse,json,subprocess,time,hashlib
from pathlib import Path
import session
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--stress',type=int,default=0);a=p.parse_args();s=session.create(a.name);folder=Path(s['directory']);path=folder/'session_private.json'
    if not 0<=a.stress<=20000:raise ValueError('stress bounds')
    if a.stress:s['environment']['A2WC_RPC_STRESS']=str(a.stress);path.write_text(json.dumps(s,indent=2))
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/ecuflash_dynamic/start_rpc.py'),a.name],check=True)
    s=json.loads(path.read_text());s['target']=str(folder/'native/provider_probe32.exe');path.write_text(json.dumps(s,indent=2));session.launch(s)
    for _ in range(1000):
        lines=(folder/'launcher.log').read_text().splitlines()
        if lines and 'exit_code' in lines[-1]:break
        time.sleep(.05)
    exitcode=json.loads(lines[-1])['exit_code'];events=[json.loads(x) for x in (folder/'j2534.jsonl').read_text().splitlines()]
    functions=sorted(set(e['request']['function'] for e in events))
    report={'status':'PASS' if exitcode==0 and len(functions)==14 and len(events)==15+a.stress else 'FAIL','stress_messages':a.stress,'exit_code':exitcode,'functions':functions,'calls':len(events),'real_provider_loaded':False,'installed_ECUFlash_acceptance':False,'trace_sha256':hashlib.sha256((folder/'j2534.jsonl').read_bytes()).hexdigest()}
    (folder/'PROVIDER_SMOKE.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    h=session.k.OpenProcess(1,False,s['server_pid'])
    if h:session.k.TerminateProcess(h,0);session.k.CloseHandle(h)
    if exitcode:raise SystemExit(exitcode)
if __name__=='__main__':main()
