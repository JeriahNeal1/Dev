"""Independent fresh-directory binary reproduction; only fake DLL is executed."""
from pathlib import Path
import json
import hashlib
import subprocess
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
source=ROOT/'integrations/prehardware/build'
out=ROOT/'work/prehardware/broker clean repeat 01'
out.mkdir(parents=True,exist_ok=False)
run=subprocess.run(['cmd.exe','/d','/c',str(source/'build.cmd')],cwd=out,capture_output=True,text=True,timeout=60)
(out/'build.log').write_text(run.stdout+run.stderr)
if run.returncode:raise SystemExit(run.stdout+run.stderr)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[{'name':name,'original':sha(source/name),'fresh_directory':sha(out/name)} for name in ['broker.exe','fake_j2534.dll']]
if any(x['original']!=x['fresh_directory'] for x in rows):raise SystemExit('Fresh-directory binary hash differs')
test=subprocess.run([str(out/'broker.exe'),'--fake'],input=b'IDENTITY\nSNAPSHOT\nCLOSE\n',capture_output=True,timeout=5)
(out/'fake.stdout.jsonl').write_bytes(test.stdout)
(out/'fake.stderr.log').write_bytes(test.stderr)
if test.returncode:raise SystemExit(test.stderr)
result={'status':'PASS','builds':rows,'directory_with_spaces':str(out),'fake_exchange_exit':test.returncode,'real_provider_loaded':False}
(ROOT/'reports/local/prehardware/BROKER_BUILD_REPRODUCIBILITY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
