"""Process-scoped offline ECUFlash sessions. Never modifies a real provider key."""
import sys
sys.dont_write_bytecode=True
import argparse,ctypes,hashlib,json,os,secrets,shutil,subprocess,time,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'integrations/ecuflash_virtual/build'
WORK=ROOT/'work/ecuflash_dynamic'
PREFIX=r'Software\A2WC511R_VirtualRead'
EXE=Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe')
EXPECTED='5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115'
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
k.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
k.CloseHandle.argtypes=[ctypes.c_void_p]
k.TerminateProcess.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
def status(pid):
    h=k.OpenProcess(0x1000,False,pid)
    if not h:return None
    code=ctypes.c_uint32();k.GetExitCodeProcess(h,ctypes.byref(code));k.CloseHandle(h)
    return code.value
def setvalues(path,values):
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_ALL_ACCESS) as key:
        for name,value in values.items():winreg.SetValueEx(key,name,0,winreg.REG_DWORD if isinstance(value,int) else winreg.REG_SZ,value)
def remove_tree(path):
    if not path.startswith(PREFIX+'\\') or '..' in path:raise ValueError('unsafe registry removal')
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_ALL_ACCESS) as key:
            names=[winreg.EnumKey(key,i) for i in range(winreg.QueryInfoKey(key)[0])]
        for name in names:remove_tree(path+'\\'+name)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,path)
    except FileNotFoundError:pass
def create(name,probe=False):
    if not name.replace('_','').replace('-','').isalnum():raise ValueError('session name')
    folder=(WORK/name).resolve();folder.mkdir(parents=True,exist_ok=False)
    native=folder/'native';native.mkdir()
    for filename in ('a2wc_guard32.dll','a2wc_ecuflash_virtual32.dll','guarded_launcher32.exe','isolation_probe32.exe','provider_probe32.exe'):
        shutil.copyfile(BUILD/filename,native/filename)
    registry=PREFIX+'\\'+name
    try:winreg.OpenKey(winreg.HKEY_CURRENT_USER,registry).Close()
    except FileNotFoundError:pass
    else:raise ValueError('existing private registry')
    fake=str(native/'a2wc_ecuflash_virtual32.dll')
    for suffix in (r'Machine\SOFTWARE\PassThruSupport.04.04',r'Machine\SOFTWARE\WOW6432Node\PassThruSupport.04.04'):
        setvalues(registry+'\\'+suffix+r'\A2WC511R Virtual ECU',{'Name':'A2WC511R Virtual ECU - OFFLINE ONLY','Vendor':'A2WC511R Research','FunctionLibrary':fake,'ConfigApplication':'','ISO9141':1,'ISO14230':1,'CAN':1,'ISO15765':1})
    setvalues(registry+r'\User\Software\OpenECU\EcuFlash\files',{'default vehicle':'read_sti05','ROM directory':str(folder),'log directory':str(folder),'metadata directory':str(EXE.parent/'rommetadata'),'color map directory':str(EXE.parent/'colormaps')})
    # No real OpenPort serial, device path, hardware configuration or license token is copied.
    setvalues(registry+r'\User\Software\OpenECU\EcuFlash\updates',{'checkforupdates':0})
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    for part in ('Roaming','Local','Temp'):(folder/'appdata'/part).mkdir(parents=True)
    (folder/'appdata/Roaming/OpenECU/EcuFlash/logs').mkdir(parents=True)
    env.update(A2WC_APPDATA=str(folder/'appdata'),APPDATA=str(folder/'appdata/Roaming'),LOCALAPPDATA=str(folder/'appdata/Local'),TEMP=str(folder/'appdata/Temp'),TMP=str(folder/'appdata/Temp'))
    env.update(A2WC_GUARD_LOG=str(folder/'guard.log'),A2WC_NATIVE_API_LOG=str(folder/'native_api.jsonl'),A2WC_FAKE_DLL=fake,A2WC_VREG=registry)
    env['A2WC_RPC_TOKEN']=secrets.token_hex(24)
    if probe:
        sentinel=folder/'op20pt32.dll';shutil.copyfile(native/'a2wc_ecuflash_virtual32.dll',sentinel)
        env['A2WC_DENIED_TEST_DLL']=str(sentinel);target=native/'isolation_probe32.exe'
    else:
        if hashlib.sha256(EXE.read_bytes()).hexdigest()!=EXPECTED:raise ValueError('installed exe changed')
        target=EXE
    spec={'schema':2,'name':name,'directory':str(folder),'registry':registry,'probe':probe,'environment':env,'target':str(target),'guard':str(native/'a2wc_guard32.dll'),'launcher':str(native/'guarded_launcher32.exe'),'native_hashes':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in native.iterdir()}}
    (folder/'session_private.json').write_text(json.dumps(spec,indent=2))
    return spec
def launch(spec):
    env=spec['environment'];folder=Path(spec['directory'])
    logpath=folder/'launcher.log'
    with logpath.open('w') as log:
        proc=subprocess.Popen([spec['launcher'],spec['target'],spec['guard']],env=env,cwd=folder,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(100):
        lines=logpath.read_text().splitlines()
        if lines:break
        time.sleep(.05)
    launchinfo=json.loads(lines[0]);spec.update(launchinfo);spec['launcher_pid']=proc.pid
    (folder/'session_private.json').write_text(json.dumps(spec,indent=2))
    return launchinfo
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['probe','create','launch','status','terminate','remove']);p.add_argument('name');a=p.parse_args()
    if a.action in ('probe','create'):s=create(a.name,probe=a.action=='probe')
    else:s=json.loads((WORK/a.name/'session_private.json').read_text())
    if a.action in ('probe','launch'):
        info=launch(s)
        if a.action=='probe':
            for _ in range(100):
                code=status(s['pid'])
                lines=(Path(s['directory'])/'launcher.log').read_text().splitlines()
                if len(lines)>1:code=json.loads(lines[-1])['exit_code'];break
                time.sleep(.05)
            isolated=PREFIX+'\\'+a.name+r'\User\Software\A2WCIsolationProbe'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,isolated) as key:value=winreg.QueryValueEx(key,'marker')[0]
            try:winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\A2WCIsolationProbe').Close();real_exists=True
            except FileNotFoundError:real_exists=False
            report={'exit_code':code,'marker':value,'real_user_marker_exists':real_exists,'guard':(Path(s['directory'])/'guard.log').read_text()}
            report['status']='PASS' if code==0 and value==0x511 and not real_exists and 'ISOLATION_READY' in report['guard'] and 'DENIED_PROVIDER_LOAD' in report['guard'] and 'DENIED_DEVICE_OPEN' in report['guard'] and 'APPDATA_REDIRECT' in report['guard'] else 'FAIL'
            (Path(s['directory'])/'ISOLATION_PROBE.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
        else:print(json.dumps(info))
    elif a.action=='status':print(json.dumps({'pid':s.get('pid'),'exit_code':status(s['pid'])}))
    elif a.action=='terminate':
        h=k.OpenProcess(1,False,s['pid'])
        if h:k.TerminateProcess(h,190);k.CloseHandle(h)
    elif a.action=='remove':
        if s.get('pid') and status(s['pid'])==259:raise ValueError('process still running')
        remove_tree(s['registry']);print('Removed only private virtual registry')
    else:print(json.dumps({'directory':s['directory']}))
if __name__=='__main__':main()
