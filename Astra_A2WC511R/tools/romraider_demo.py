"""Synthetic demonstration of history, comparison, timeline and bounded proposals.
No editor connection, no real ECU values, no writes outside the requested output folder.
"""
from pathlib import Path
import argparse, copy, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'integrations/romraider_mcp'))
from core import Store

def run(out):
    out.mkdir(parents=True,exist_ok=True);store=Store(out)
    def table(key,rows,unit,static=False):
        return {'key':key,'name':key,'rows':len(rows),'columns':len(rows[0]),'static':static,'locked':False,'edit_capability':'static_not_rom_backed' if static else 'numeric_native_preview_required','scale':{'units':unit},'cells':[[{'real':v,'raw':None if static else v,'static_text':str(v) if static else None} for v in row] for row in rows]}
    snapshot={'schema':'rr-model-snapshot-v1','captured_utc':'2026-09-25T00:00:00Z','label':'SYNTHETIC DEMO - not car calibration','bridge_session':'synthetic_no_editor','rom':{'rom_id':'synthetic','binary_sha256':'0'*64,'calid':'SYNTHETIC_NOT_A_ROM'},'model_sha256':'1'*64,'tables':[table('Demonstration Surface',[[10,20],[30,40]],'arbitrary units'),table('Demonstration Surface::x',[[0,1]],'fraction',True),table('Demonstration Surface::y',[[1000,2000]],'rpm',True)]}
    old=store.put('snapshots',snapshot);changed=copy.deepcopy(snapshot);changed['label']='SYNTHETIC alternate';changed['tables'][0]['cells'][0][0].update(real=11,raw=11);new=store.put('snapshots',changed)
    (out/'synthetic.csv').write_text('Time (msec),Fraction,RPM,Measured Error\n0,0,1000,0.5\n20,0.25,1250,1.0\n40,0.5,1500,1.5\n60,0.75,1750,1.0\n80,1,2000,0.5\n',encoding='utf-8')
    log=store.ingest_log('synthetic.csv',old,'unverified_candidate_association','Synthetic rows: not a vehicle or flashed-ROM assertion')['log_id']
    overlay=store.overlay(log,'Demonstration Surface',{'x':{'column':'Fraction','unit':'fraction','factor':1,'offset':0},'y':{'column':'RPM','unit':'rpm','factor':1,'offset':0}},'Measured Error','Time (msec)','ms',[], 'Synthetic demonstration, not firmware active-table proof')
    proposal=store.calculate(old,'Demonstration Surface','old + mean',[{'row':0,'column':0}],{}, {'minimum':0,'maximum':100,'max_abs_delta':2,'min_samples':2,'tolerance':0.1},'Synthetic example: not a tune recommendation',['synthetic fixture'],overlay['overlay_id'])
    report={'warning':'SYNTHETIC ONLY; no editor connection, ROM or vehicle action','comparison':store.compare(old,new),'overlay':overlay,'proposal':proposal}
    (out/'DEMO_INDEX.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
