"""Read-only bounded local tuning/program inventory, with no device access."""
import csv, hashlib, json, pathlib, zipfile
from datetime import datetime, timezone

OUT = pathlib.Path(__file__).parent
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def info(p):
    return dict(path=str(p), size=p.stat().st_size, modified=datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(), sha256=h(p))

roots = [pathlib.Path(p) for p in [r'C:\Tuning', r'C:\Dev\SubaruRoms', r'C:\Users\Jeriah Neal\Desktop']]
base=pathlib.Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin').read_bytes()
roms=[]; logs=[]
for root in roots:
    for p in root.rglob('*'):
        if not p.is_file(): continue
        if p.suffix.lower() in ('.bin','.srf'):
            row=info(p); b=p.read_bytes()
            if len(b)==len(base):
                row['calid_at_2000']=b[0x2000:0x2009].decode('ascii','replace').rstrip('\0')
                row['different_bytes_from_baseline']=sum(x!=y for x,y in zip(base,b))
            roms.append(row)
        elif p.suffix.lower()=='.csv':
            row=info(p)
            with p.open(encoding='utf-8-sig',errors='replace',newline='') as f:
                it=csv.reader(f); row['headers']=next(it,[]); row['rows']=sum(1 for _ in it)
            logs.append(row)
programs=[]
for p in [pathlib.Path(x) for x in [r'C:\Program Files\RomRaider\RomRaider.jar',r'C:\Program Files (x86)\RomRaider\RomRaider.jar',r'C:\Program Files\RomRaider\jdk-11.0.14.1+1-jre\bin\java.exe',r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe',r'C:\Program Files\RomRaider\settings.xml',r'C:\Users\Jeriah Neal\.RomRaider\settings.xml',r'C:\Dev\SubaruDefs\RomRaider\ecu\standard\ecu_defs.xml',r'C:\Tuning\Romraider\ECU\ecu_defs.xml']]:
    row=info(p)
    if p.suffix=='.jar':
        with zipfile.ZipFile(p) as z: row['manifest']=z.read('META-INF/MANIFEST.MF').decode()
    programs.append(row)
result=dict(captured_utc=datetime.now(timezone.utc).isoformat(),roots=[str(p) for p in roots],programs=programs,roms=roms,logs=sorted(logs,key=lambda r:r['path']),note='File names and modification times do not prove the current ECU calibration. No vehicle clients started.')
(OUT/'local_inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(dict(roms=roms,log_count=len(logs),newest_logs=sorted(logs,key=lambda r:r['modified'],reverse=True)[:4],programs=[{k:v for k,v in r.items() if k!='manifest'} for r in programs]),indent=2))
