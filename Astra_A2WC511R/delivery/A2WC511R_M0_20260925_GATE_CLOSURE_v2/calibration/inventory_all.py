"""Read-only exhaustive size/signature inventory of requested roots; no device use."""
import os, json, hashlib, zipfile, re
from pathlib import Path
from datetime import datetime, timezone
OUT=Path(__file__).parent
BASE=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
ROOTS=[Path(p) for p in ['C:/Dev','C:/Tuning','C:/Users/Jeriah Neal/Desktop',
 'C:/Users/Jeriah Neal/Documents','C:/Users/Jeriah Neal/Downloads',
 'C:/Users/Jeriah Neal/AppData/Roaming/OpenECU','C:/Users/Jeriah Neal/AppData/Local/OpenECU',
 'C:/Users/Jeriah Neal/AppData/Local/VirtualStore','C:/Program Files (x86)/OpenECU',
 'C:/Program Files/OpenECU','C:/Users/Jeriah Neal/.RomRaider',
 'C:/SubaruDefs','C:/WorkSpace','C:/Temp','C:/Users/Jeriah Neal/AppData/Local/Temp']]
ERRORS=[]; FILES=[]; ROMS=[]; ARCHIVES=[]; HISTORY=[]; UNIQUE={}; OTHER_1MIB=[]; SKIPPED_LINKS=[]
def digest(b):return hashlib.sha256(b).hexdigest()
def ranges(a,b):
    changed=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]; out=[]
    for n in changed:
        if out and out[-1][1]==n:out[-1][1]+=1
        else:out.append([n,n+1])
    return changed,out
def classify(label,b,**extra):
    if len(b)!=0x100000:return
    if b[0x2000:0x2008]!=b'A2WC511R':
        OTHER_1MIB.append({'path':label,'sha256':digest(b),'header_at_2000_hex':b[0x2000:0x2008].hex(),
            'printable_calid':b[0x2000:0x2008].decode('ascii') if all(32<=c<127 for c in b[0x2000:0x2008]) else None})
        return
    h=digest(b)
    if h not in UNIQUE:
        changed,rr=ranges(BASE,b)
        UNIQUE[h]={'sha256':h,'changed_bytes':len(changed),'changed_ranges':rr,
            'rom_run_ff': all(x==255 for x in b[0xCE754:0xFFAF8]),
            'hook':b[0x11ADC:0x11AE0].hex(),'stamp':b[0xFFC4C:0xFFC50].hex(),
            'first_seen_path':label,'checksum_words':b[0xFFB80:0xFFC28].hex(),
            'classification':'stock' if not changed else 'editor_stamp_only' if all(0xFFC4C<=x<0xFFC50 for x in changed) else 'historical_tuned' if h in (
                '1aac3214ec276822f1343e66fc1b8af83be8e61866d2d182882beb88317b4920',
                '2f9c2f8af56e337e9fa31fd5efd4b1f01d3474f78396065ad3fc9a0bd132cbdc',
                'bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2',
                'd2dc34e1b21985c89b49996c9dedd88494c90c65e2da0c0a735d31d54ca92171') else 'M0_generated_or_test' if 'Astra_A2WC511R' in label else 'unclassified'}
    ROMS.append({'path':label,'sha256':h,**extra})
def scan_payload(label,b,**extra):
    if len(b)==0x100000:classify(label,b,**extra)
    elif label.lower().endswith('.srf'):
        for m in re.finditer(b'A2WC511R',b):
            off=m.start()-0x2000
            if off>=0 and off+0x100000<=len(b):classify(label+'::payload@'+hex(off),b[off:off+0x100000],container_sha256=digest(b),**extra)
seen=set()
for root in ROOTS:
    if not root.exists():
        ERRORS.append({'path':str(root),'status':'not_present'});continue
    for directory,dirs,files in os.walk(root,followlinks=False,onerror=lambda e:ERRORS.append({'path':e.filename,'error':str(e)})):
        for d in dirs:
            p=Path(directory,d)
            if p.is_symlink() or p.is_junction():SKIPPED_LINKS.append({'path':str(p),'target':str(p.resolve())})
        dirs[:]=[d for d in dirs if not Path(directory,d).is_symlink() and not Path(directory,d).is_junction()]
        for name in files:
            p=Path(directory,name); key=str(p).lower()
            if key in seen:continue
            seen.add(key)
            try:
                st=p.stat(); FILES.append({'path':str(p),'size':st.st_size})
                if st.st_size==0x100000 or p.suffix.lower()=='.srf':
                    scan_payload(str(p),p.read_bytes(),mtime_utc=datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat())
                if p.suffix.lower() in ('.zip','.jar','.nupkg','.7z','.rar','.tar','.gz'):
                    row={'path':str(p),'size':st.st_size,'format':p.suffix.lower()};ARCHIVES.append(row)
                    if zipfile.is_zipfile(p):
                        with zipfile.ZipFile(p) as z:
                            targets=[i for i in z.infolist() if i.file_size==0x100000 or i.filename.lower().endswith('.srf')]
                            row['scanned_members']=[i.filename for i in targets]
                            for i in targets:scan_payload(str(p)+'::'+i.filename,z.read(i))
                    elif p.suffix.lower() not in ('.jar','.nupkg'):row['status']='requires_format_followup'
                if ('openecu' in key or 'ecuflash' in key) and p.suffix.lower() in ('.txt','.log','.ini','.cfg') and st.st_size<2000000 and 'rommetadata' not in key:
                    txt=p.read_text(errors='replace');hits=[]
                    for n,line in enumerate(txt.splitlines(),1):
                        if re.search(r'A2WC|\.bin|\.srf|flash|checksum|read|writ|success|fail|roms|directory',line,re.I):hits.append({'line':n,'text':line})
                    if hits:HISTORY.append({'path':str(p),'sha256':digest(p.read_bytes()),'matches':hits})
            except Exception as e:ERRORS.append({'path':str(p),'error':repr(e)})
result={'utc':datetime.now(timezone.utc).isoformat(),'roots':[str(p) for p in ROOTS],
 'files_enumerated':len(FILES),'images':ROMS,'unique_images':list(UNIQUE.values()),'other_1MiB_files':OTHER_1MIB,
 'archives':ARCHIVES,'errors':ERRORS,'skipped_directory_links':SKIPPED_LINKS,
 'current_flashed_identity':None,'identity_rule':'No file date/name or operation log without byte identity proves current ECU contents.'}
(OUT/'inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(OUT/'enumerated_files.json').write_text(json.dumps(FILES),encoding='utf-8')
(OUT/'ecuflash_history.json').write_text(json.dumps(HISTORY,indent=2),encoding='utf-8')
print(json.dumps({'files':len(FILES),'images':len(ROMS),'unique':list(UNIQUE.values()),'errors':ERRORS,
 'archive_followup':[r for r in ARCHIVES if r.get('status')],'history_files':len(HISTORY)},indent=2))
