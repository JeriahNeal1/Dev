"""Hash-linked stock, research, sibling, and archived MerpMod comparisons."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path('C:/Dev/Astra_A2WC511R');WORK=ROOT/'work/diaphora';HERE=Path(__file__).resolve().parent
PAIRS=[('stock_determinism_01','A2WC511R_stock_02','A2WC511R_stock_03'),
       ('stock_511R_vs_510S_01','A2WC511R_stock_02','A2WC510S_stock_02'),
       ('stock_vs_M07_one_01','A2WC511R_stock_02','M07_one_page_01'),
       ('stock_vs_M07_two_01','A2WC511R_stock_02','M07_two_page_01'),
       ('stock_522S_vs_archive_01','A2WC522S_stock_02','A2WC522S_archive_02'),
       ('archive_522S_vs_511R_01','A2WC522S_archive_02','A2WC511R_stock_02'),
       ('stock_511R_vs_510S_repeat_01','A2WC511R_stock_02','A2WC510S_stock_02')]
PAIRS += [(f'stock_511R_vs_{name}_01','A2WC511R_stock_02',f'A2W{pre}_stock_01') for name,pre in [('510R','C510R'),('521R','C521R'),('500R','C500R'),('412D','C412D'),('510C','C510C'),('521C','C521C'),('F200R','F200R')]]
def main():
    for original_label,left,right in PAIRS:
        label=original_label.removesuffix('_01')+'_03'
        output=WORK/'comparisons'/label
        if (output/'comparison.json').exists():
            previous=json.loads((output/'comparison.json').read_text());assert previous['status']=='PASS';print('Completed '+label,flush=True);continue
        identities=[]
        for side in [left,right]:
            file=WORK/'exports'/f'{side}.identity.json';deadline=time.monotonic()+1800
            while not file.exists():
                assert time.monotonic()<deadline,('Missing export',side)
                time.sleep(2)
            identities.append(json.loads(file.read_text()))
        command=[sys.executable,'-B',str(HERE/'compare_exports.py'),str(WORK/'exports'/f'{left}.sqlite'),str(WORK/'exports'/f'{right}.sqlite'),'--output-dir',str(output)]
        for side,identity in zip(['left','right'],identities):
            command += ['--'+side+'-rom',identity['rom']['path'],'--'+side+'-idb',identity['idb']['path']]
        if label.startswith('stock_determinism'):command+=['--require-self-identity']
        print('Starting '+label,flush=True)
        # A clean standalone matching process for every pair; unrelated cwd.
        r=subprocess.run(command,cwd='C:/Windows/Temp');assert r.returncode==0,(label,r.returncode)
if __name__=='__main__':main()
