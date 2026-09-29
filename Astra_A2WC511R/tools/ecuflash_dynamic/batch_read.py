"""Sequential isolated Read experiments; no real transport exists in this tool."""
import sys
sys.dont_write_bytecode=True
import argparse,json,traceback
import run_read
sys.path.insert(0,str(run_read.ROOT/'integrations/ecuflash_virtual'))
from faults import FaultPlan

def main():
    p=argparse.ArgumentParser();p.add_argument('group',choices=['coverage','faults','repeat']);p.add_argument('--prefix',required=True);a=p.parse_args()
    cases=[('baseline',None),('gaps_ff',None),('gap_sentinels',None),('crc_collision',None)] if a.group=='coverage' else [('baseline',None)]*2 if a.group=='repeat' else [('baseline',f) for f in FaultPlan.NAMES]
    results=[]
    for index,(variant,fault) in enumerate(cases,1):
        name=f'{a.prefix}_{index:02d}'
        try:results.append(run_read.run(name,variant,fault))
        except Exception:
            print(traceback.format_exc(),flush=True)
            raise
    target=run_read.ROOT/'reports/local/ecuflash_dynamic'/f'{a.prefix}_BATCH.json'
    target.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'batch':str(target),'runs':len(results),'physical':False}),flush=True)
if __name__=='__main__':main()
