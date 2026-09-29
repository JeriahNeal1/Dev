"""Run one immutable ROM job, then pin closed IDB/export identities."""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib
HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('config',type=Path);a=p.parse_args()
    j=json.loads(a.config.read_text());cmd=[sys.executable,'-B',str(HERE/'native_job.py'),'--input',j['rom'],'--new-output',j['idb'],
        '--script',str(HERE/'prepare_export_native.py'),'--label',j['label'],'--export',j['export'],'--config',str(a.config.resolve()),'--wait']
    r=subprocess.run(cmd);assert r.returncode==0,('Native job failed',r.returncode)
    manifest={}
    for name,path in [('rom',j['rom']),('idb',j['idb']),('export',j['export']),('config',a.config),('analysis',Path(j['export']).with_suffix('.analysis.json'))]:
        path=Path(path);manifest[name]={'path':str(path.resolve()),'size':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    Path(j['export']).with_suffix('.identity.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');print(json.dumps(manifest))
if __name__=='__main__':main()
