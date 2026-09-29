"""Sequential native exports with immutable retry labels and resumable completion."""
from pathlib import Path
import json,subprocess,sys,hashlib
ROOT=Path('C:/Dev/Astra_A2WC511R');HERE=Path(__file__).resolve().parent;WORK=ROOT/'work/diaphora'
ORDER=['A2WC511R_stock_03','A2WC510S_stock_01','M07_one_page_01','M07_two_page_01','A2WC522S_stock_01','A2WC522S_archive_01',
       'A2WC510R_stock_01','A2WC521R_stock_01','A2WC500R_stock_01','A2WC412D_stock_01','A2WC510C_stock_01','A2WC521C_stock_01','A2WF200R_stock_01']
def main():
    jobs=WORK/'scripts/rom_jobs'
    retry=jobs/'A2WC511R_stock_03.json'
    if not retry.exists():
        j=json.loads((jobs/'A2WC511R_stock_02.json').read_text())
        for k in ['label','idb','export']:j[k]=j[k].replace('stock_02','stock_03')
        retry.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
    for label in ORDER:
        identity=WORK/'exports'/f'{label}.identity.json'
        if identity.exists():
            manifest=json.loads(identity.read_text())
            for item in manifest.values():assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
            print('Verified completed '+label,flush=True);continue
        print('Starting '+label,flush=True)
        r=subprocess.run([sys.executable,'-B',str(HERE/'run_rom_job.py'),str(jobs/f'{label}.json')])
        if r.returncode:raise SystemExit(r.returncode)
if __name__=='__main__':main()
