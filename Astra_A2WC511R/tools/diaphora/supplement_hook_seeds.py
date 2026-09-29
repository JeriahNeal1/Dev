"""Close a discovered coverage gap using independently validated MerpMod callsites.

The initial exact-prefix sibling seeds miss functions whose first pool offsets
changed. These additional roots are proved by each ROM's actual SH literal-load
and JSR sequence, never inferred merely from a neighboring calibration ID.
"""
from pathlib import Path
import json,subprocess,sys,hashlib
ROOT=Path('C:/Dev/Astra_A2WC511R');WORK=ROOT/'work/diaphora';HERE=Path(__file__).resolve().parent
SITES=[(0xd218,0xd21a,0xd324),(0x79b4,0x79be,0x7a04),(0x120fa,0x120fc,0x122b4),(0x125b6,0x125b8,0x127e8)]
def main():
    for base in ['A2WC510S_stock','A2WC522S_stock','A2WC522S_archive']:
        j=json.loads((WORK/'scripts/rom_jobs'/f'{base}_01.json').read_text());data=Path(j['rom']).read_bytes()
        for key in ['label','idb','export']:j[key]=j[key].replace(base+'_01',base+'_02')
        seeds={x['address']:x for x in j['function_seeds']};evidence=[]
        for load,call,pool in SITES:
            op=int.from_bytes(data[load:load+2],'big');jsr=int.from_bytes(data[call:call+2],'big')
            assert op>>12==0xd and jsr&0xf0ff==0x400b and (op>>8)&15==(jsr>>8)&15
            resolved=((load+4)&~3)+(op&255)*4;assert resolved==pool
            target=int.from_bytes(data[pool:pool+4],'big');assert target%2==0 and 0<=target<0x100000
            item={'kind':'source_validated_SH_literal_JSR','load':load,'call':call,'literal':pool,'target':target,'register':(op>>8)&15,
                  'scope':'callsite bytes/pointer only; source semantic name not automatically imported'}
            seeds.setdefault(target,{'address':target,'evidence':[]})['evidence'].append(item);evidence.append(item)
        j['function_seeds']=[seeds[x] for x in sorted(seeds)];j['additional_evidenced_roots']=evidence
        out=WORK/'scripts/rom_jobs'/f'{base}_02.json';assert not out.exists();out.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
        r=subprocess.run([sys.executable,'-B',str(HERE/'run_rom_job.py'),str(out)]);assert r.returncode==0
if __name__=='__main__':main()
