"""Fresh read-only source snapshots. No application, provider or registry writes."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,json,shutil,stat,datetime,winreg
ROOT=Path(__file__).resolve().parents[1]
OLD=Path(r'C:\Dev\Astra_A2WC511R')
SNAP=ROOT/'preservation/snapshot_20260927'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def tree(root,path,view=0):
    try:key=winreg.OpenKey(root,path,0,winreg.KEY_READ|view)
    except FileNotFoundError:return None
    with key:
        children,values,_=winreg.QueryInfoKey(key);result={}
        for i in range(values):
            name,value,kind=winreg.EnumValue(key,i)
            result[name]={'type':kind,'value':{'hex':value.hex()} if isinstance(value,bytes) else value}
        return {'values':result,'children':{winreg.EnumKey(key,i):tree(key,winreg.EnumKey(key,i)) for i in range(children)}}

def registry():
    r={}
    for name,view in [('x86',winreg.KEY_WOW64_32KEY),('x64',winreg.KEY_WOW64_64KEY)]:
        for p in (r'SOFTWARE\PassThruSupport.04.04',r'SOFTWARE\PassThruSupport.05.00'):
            r['HKLM/'+name+'/'+p]=tree(winreg.HKEY_LOCAL_MACHINE,p,view)
    r['HKCU/OpenECU']=tree(winreg.HKEY_CURRENT_USER,r'Software\OpenECU')
    return r

def create():
    SNAP.mkdir(parents=True,exist_ok=False)
    seal=OLD/'reports/local/ecuflash_dynamic/DELIVERABLE_MANIFEST.json'
    sealed=json.loads(seal.read_text());bad=[]
    for p,v in sealed['files'].items():
        if sha(OLD/p)!=v['sha256']:bad.append(p)
    if bad:raise ValueError('Prior seal mismatch: '+repr(bad))
    sources=[('ecuflash_install',Path(r'C:\Program Files (x86)\OpenECU\EcuFlash')),
             ('openport_install',Path(r'C:\Program Files (x86)\OpenECU\OpenPort 2.0')),
             ('roaming_OpenECU',Path.home()/'AppData/Roaming/OpenECU'),
             ('local_OpenECU',Path.home()/'AppData/Local/OpenECU'),
             ('state',OLD/'state'),('config',OLD/'config')]
    records=[]
    for label,source in sources:
        if not source.exists():records.append({'source':str(source),'absent':True});continue
        for p in sorted(source.rglob('*')):
            if not p.is_file():continue
            dest=SNAP/label/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
            before=sha(p);shutil.copy2(p,dest)
            if sha(dest)!=before or sha(p)!=before:raise ValueError('Snapshot race '+str(p))
            dest.chmod(stat.S_IREAD)
            records.append({'source':str(p),'snapshot':str(dest),'sha256':before,'bytes':p.stat().st_size})
    for p in [Path(r'C:\Windows\SysWOW64\op20pt32.dll'),Path(r'C:\Windows\System32\op20pt32.dll'),
              Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER_RECOVERED_20260926.i64'),
              Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER.bin.i64')]:
        if not p.exists():records.append({'source':str(p),'absent':True});continue
        dest=SNAP/'external'/p.drive.replace(':','')/p.relative_to(p.anchor)
        dest.parent.mkdir(parents=True,exist_ok=True);before=sha(p);shutil.copy2(p,dest)
        if sha(dest)!=before:raise ValueError('Snapshot mismatch')
        dest.chmod(stat.S_IREAD);records.append({'source':str(p),'snapshot':str(dest),'sha256':before,'bytes':p.stat().st_size})
    private=SNAP/'REGISTRY_PRIVATE.json';private.write_text(json.dumps(registry(),indent=2)+'\n');private.chmod(stat.S_IREAD)
    manifest={'schema':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'PASS_FRESH_SNAPSHOT','immutable_policy':'Exclusive directory, read-only copied files, hash manifest; not OS-enforced WORM.',
        'prior_seal':{'path':str(seal),'sha256':sha(seal),'verified_files':len(sealed['files'])},
        'registry_snapshot':{'path':str(private),'sha256':sha(private),'private_values_not_printed':True},
        'files':records,'source_writes':False,'provider_loaded':False}
    target=SNAP/'MANIFEST.json';target.write_text(json.dumps(manifest,indent=2)+'\n');target.chmod(stat.S_IREAD)
    return {'status':manifest['status'],'copied_files':sum('snapshot'in x for x in records),'prior_files_verified':len(sealed['files']),'manifest':str(target),'sha256':sha(target)}

def verify():
    manifest=json.loads((SNAP/'MANIFEST.json').read_text());bad=[];changed=[]
    for x in manifest['files']:
        if x.get('absent'):continue
        if sha(x['snapshot'])!=x['sha256']:bad.append(x['snapshot'])
        if not Path(x['source']).exists() or sha(x['source'])!=x['sha256']:changed.append(x['source'])
    before=json.loads(Path(manifest['registry_snapshot']['path']).read_text())
    return {'snapshot_status':'PASS' if not bad else 'FAIL','snapshot_mismatches':bad,'changed_sources':changed,
            'real_registry_unchanged':registry()==before,'provider_loaded':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps(verify() if a.verify else create()))
