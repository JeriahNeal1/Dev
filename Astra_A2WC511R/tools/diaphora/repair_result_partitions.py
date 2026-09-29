"""Regenerate only results affected by discarded tentative-match reporting."""
from pathlib import Path
import json,sys,subprocess,hashlib
ROOT=Path('C:/Dev/Astra_A2WC511R');WORK=ROOT/'work/diaphora';HERE=Path(__file__).resolve().parent
JOBS=[('stock_511R_vs_412D_04','stock_511R_vs_412D_05'),('stock_511R_vs_500R_03','stock_511R_vs_500R_04'),
      ('stock_511R_vs_521C_03','stock_511R_vs_521C_04'),('stock_511R_vs_521R_03','stock_511R_vs_521R_04'),('stock_511R_vs_F200R_03','stock_511R_vs_F200R_04'),
      ('stock_511R_vs_412D_04','stock_511R_vs_412D_repeat_05')]
def main():
    for old,new in JOBS:
        source=WORK/'comparisons'/old/'comparison.json';d=json.loads(source.read_text());out=WORK/'comparisons'/new
        assert not out.exists()
        command=[sys.executable,'-B',str(HERE/'compare_exports.py'),d['left_export']['path'],d['right_export']['path'],'--output-dir',str(out)]
        for side in ['left','right']:
            for kind in ['rom','idb']:command+=['--'+side+'-'+kind,d[side+'_'+kind]['path']]
        print('Rechecking affected comparison '+new,flush=True)
        done=subprocess.run(command,cwd='C:/Windows/Temp');assert done.returncode==0
        (out/'REPLACES_REPORT.json').write_text(json.dumps({'prior_report':str(source),'prior_report_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'reason':'Final chooser cleanup can discard tentative pairs; derive unmatched from retained result addresses. No matcher proposals or export inputs altered.'},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
