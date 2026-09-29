import json, re, zlib, hashlib, zipfile
from pathlib import Path
OUT=Path(__file__).parent
inv=json.loads((OUT/'inventory.json').read_text())
log=Path('C:/Users/Jeriah Neal/AppData/Roaming/OpenECU/EcuFlash/logs/ecuflash_log_20260818t134942.txt')
txt=log.read_text(); tail=txt.split('verifying result...')[-1]
pages=[{'segment':m[0],'start':int(m[1],16),'length':int(m[2],16),'ecu_crc32':int(m[3],16),'image_crc32':int(m[4],16),'equal':m[5]=='YES'} for m in re.findall(r'(FB\d+)\s+([0-9A-F]{8})\s+([0-9A-F]{8})\s+([0-9A-F]{8})\s+([0-9A-F]{8})\s+(YES|NO)',tail)]
def load_image(label):
    if '::' not in label:return Path(label).read_bytes()
    p,member=label.split('::',1)
    if member.startswith('payload@'):return Path(p).read_bytes()[int(member.split('@')[1],16):][:0x100000]
    with zipfile.ZipFile(p) as z:return z.read(member)
images={u['sha256']:load_image(u['first_seen_path']) for u in inv['unique_images']}
matches=[]
for u in inv['unique_images']:
    b=images[u['sha256']]
    pp=[{'start':p['start'],'calculated':zlib.crc32(b[p['start']:p['start']+p['length']]),'logged':p['image_crc32']} for p in pages]
    for p in pp:p['matches']=p['calculated']==p['logged']
    matches.append({'sha256':u['sha256'],'path':u['first_seen_path'],'page_matches':sum(p['matches'] for p in pp),'total':len(pp),'pages':pp})
known=[u for u in inv['unique_images'] if u['changed_bytes']>=1800 and u['rom_run_ff']]
def diff(a,b):
    rr=[]
    for n,(x,y) in enumerate(zip(a,b)):
        if x==y:continue
        if rr and rr[-1]['end']==n:rr[-1]['end']+=1
        else:rr.append({'start':n,'end':n+1})
    return {'count':sum(r['end']-r['start'] for r in rr),'ranges':rr}
pairwise=[{'from':u['sha256'],'to':v['sha256'],**diff(images[u['sha256']],images[v['sha256']])} for i,u in enumerate(known) for v in known[i+1:]]
result={'log':str(log),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'flash_correct_recorded':'flash correct! exiting.' in tail,
 'logged_pages':pages,'comparisons':matches,'tune_history_pairwise':pairwise,'current_flashed_identity':None,
 'scope':'Historical CRC equality is not cryptographic byte identity or proof of no later write. No fresh ECU read performed.'}
(OUT/'history_comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'historical_page_match':[{k:v for k,v in r.items() if k!='pages'} for r in matches], 'pairwise':pairwise},indent=2))
