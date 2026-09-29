import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,subprocess,time,hashlib
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('session');a=p.parse_args();folder=ROOT/'work/ecuflash_dynamic'/a.session;path=folder/'session_private.json';s=json.loads(path.read_text())
    if (folder/'rpc_ready.json').exists():raise ValueError('RPC server already initialized')
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'integrations/ecuflash_virtual').glob('*.py'))}
    (folder/'MODEL_INPUTS.json').write_text(json.dumps({'schema':1,'python_sources':sources,'variant':s.get('variant','baseline'),'fault':s.get('fault'),'response_mask':s.get('response_mask',0x40),'physical':False},indent=2)+'\n')
    with (folder/'server.log').open('w') as log:
        proc=subprocess.Popen([sys.executable,'-B',str(ROOT/'integrations/ecuflash_virtual/rpc_server.py'),str(path)],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(100):
        if (folder/'rpc_ready.json').exists():break
        if proc.poll() is not None:raise ValueError((folder/'server.log').read_text())
        time.sleep(.05)
    ready=json.loads((folder/'rpc_ready.json').read_text());s['environment']['A2WC_RPC_PORT']=str(ready['port']);s['server_pid']=proc.pid;path.write_text(json.dumps(s,indent=2));print(json.dumps({'port':ready['port'],'server_pid':proc.pid}))
if __name__=='__main__':main()
