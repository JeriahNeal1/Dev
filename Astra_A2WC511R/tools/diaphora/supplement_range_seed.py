"""Promote an independently recovered Forester range entry in a fresh IDB only."""
from pathlib import Path
import json,subprocess,sys,hashlib
ROOT=Path('C:/Dev/Astra_A2WC511R');WORK=ROOT/'work/diaphora'
j=json.loads((WORK/'scripts/rom_jobs/A2WC412D_stock_01.json').read_text())
for k in ['label','idb','export']:j[k]=j[k].replace('stock_01','stock_02')
report=Path('C:/Dev/A2WC511R_Sim/diaphora_crossrom/runs/20260926T025326.453332Z/crossrom_regression.json')
j['function_seeds'].append({'address':0x1447c,'evidence':[{'kind':'independently_recovered_range_CFG_and_differential_contract','report':str(report),'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'ownership_proven':False}]})
j['function_seeds'].sort(key=lambda x:x['address'])
out=WORK/'scripts/rom_jobs/A2WC412D_stock_02.json';assert not out.exists();out.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
raise SystemExit(subprocess.call([sys.executable,'-B',str(Path(__file__).with_name('run_rom_job.py')),str(out)]))
