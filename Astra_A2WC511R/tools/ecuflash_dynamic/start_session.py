"""Read-only preservation and registry backup before process-private virtualization."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,shutil,winreg,urllib.request
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
OUT=ROOT/'reports/local/ecuflash_dynamic'
BACK=ROOT/'backups/ecuflash_dynamic_20260926'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(root,path,view=0):
    try:key=winreg.OpenKey(root,path,0,winreg.KEY_READ|view)
    except FileNotFoundError:return None
    with key:
        children,values,_=winreg.QueryInfoKey(key)
        v={}
        for i in range(values):
            name,value,kind=winreg.EnumValue(key,i)
            v[name]={'type':kind,'value':{'hex':value.hex()} if isinstance(value,bytes) else value}
        return {'values':v,'children':{winreg.EnumKey(key,i):tree(key,winreg.EnumKey(key,i)) for i in range(children)}}
def main():
    OUT.mkdir(parents=True,exist_ok=True);BACK.mkdir(parents=True,exist_ok=False)
    seal=ROOT/'reports/local/prehardware/DELIVERABLE_MANIFEST.json'
    d=json.loads(seal.read_text());bad=[]
    for p,h in d['files'].items():
        if sha(p)!=h:bad.append(p)
    if bad:raise ValueError(bad)
    for name in ('state','config'):shutil.copytree(ROOT/name,BACK/name)
    registry={}
    for viewname,view in [('x86',winreg.KEY_WOW64_32KEY),('x64',winreg.KEY_WOW64_64KEY)]:
        for path in [r'SOFTWARE\PassThruSupport.04.04',r'SOFTWARE\PassThruSupport.05.00']:
            registry['HKLM/'+viewname+'/'+path]=tree(winreg.HKEY_LOCAL_MACHINE,path,view)
    registry['HKCU/Software/OpenECU/EcuFlash']=tree(winreg.HKEY_CURRENT_USER,r'Software\OpenECU\EcuFlash')
    registry_path=BACK/'REGISTRY_BEFORE_PRIVATE.json'
    registry_path.write_text(json.dumps(registry,indent=2)+'\n')
    extra=[Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER_RECOVERED_20260926.i64'),
           Path(r'C:\Windows\SysWOW64\op20pt32.dll'),Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe')]
    report={'status':'PASS_START','previous_seal':{'path':str(seal),'sha256':sha(seal)},
            'sealed_files':d['files'],'backup':str(BACK),'registry_backup':{'path':str(registry_path),'sha256':sha(registry_path)},
            'protected_external':{str(p):sha(p) for p in extra},'real_registry_modified':False}
    (OUT/'START_PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    source=ROOT/'integrations/ecuflash_virtual';source.mkdir(parents=True,exist_ok=True)
    vendor=source/'vendor';vendor.mkdir(exist_ok=True)
    shutil.copyfile(r'C:\Program Files (x86)\OpenECU\OpenPort 2.0\samples\common\j2534_tactrix.h',vendor/'j2534_tactrix.h')
    urllib.request.urlretrieve('https://raw.githubusercontent.com/nlohmann/json/v3.12.0/single_include/nlohmann/json.hpp',vendor/'json.hpp')
    print(json.dumps({'status':'PASS','previous_files_verified':len(d['files']),'registry_backup':str(registry_path),'private_settings_only':True}))
if __name__=='__main__':main()
