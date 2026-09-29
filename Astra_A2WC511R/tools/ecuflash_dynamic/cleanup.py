"""Remove only closed virtual sessions' private registry keys and owned RPC jobs.

Never unload, open or modify a real J2534 provider. Evidence files are retained.
An active ECUFlash process is a visible refusal, not a reason to kill it.
"""
import sys
sys.dont_write_bytecode=True
import argparse,ctypes,datetime,json,subprocess
from pathlib import Path
import session

def process_record(pid):
    if not pid:return None
    # Numeric PID is the only interpolation. No paths, environment or secrets
    # are passed through a shell command string.
    cmd=(f"Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}' | "
         "Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress")
    value=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],
        check=True,capture_output=True,text=True).stdout.strip()
    return json.loads(value) if value else None

def argv(command):
    count=ctypes.c_int();shell=ctypes.WinDLL('shell32',use_last_error=True)
    shell.CommandLineToArgvW.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype=ctypes.POINTER(ctypes.c_wchar_p)
    ptr=shell.CommandLineToArgvW(command,ctypes.byref(count))
    if not ptr:raise ctypes.WinError(ctypes.get_last_error())
    try:return [ptr[i] for i in range(count.value)]
    finally:
        session.k.LocalFree.argtypes=[ctypes.c_void_p]
        session.k.LocalFree(ctypes.cast(ptr,ctypes.c_void_p))

def samepath(a,b):return str(Path(a).resolve()).casefold()==str(Path(b).resolve()).casefold()

def clean(folder):
    folder=folder.resolve();spec_path=folder/'session_private.json'
    if folder.parent!=session.WORK.resolve():raise ValueError('Outside virtual workspace')
    s=json.loads(spec_path.read_text())
    if s['registry']!=session.PREFIX+'\\'+folder.name or not samepath(s['directory'],folder):
        raise ValueError('Session boundary mismatch')
    host=process_record(s.get('pid'))
    if host and host.get('ExecutablePath') and samepath(host['ExecutablePath'],s['target']):
        raise ValueError('Guarded host still active; close its window before cleanup')
    rpc=process_record(s.get('server_pid'));stopped=False
    if rpc:
        arguments=argv(rpc.get('CommandLine') or '')
        expected=session.ROOT/'integrations/ecuflash_virtual/rpc_server.py'
        if (len(arguments)!=4 or arguments[1]!='-B' or
            not samepath(arguments[2],expected) or not samepath(arguments[3],spec_path) or
            not samepath(rpc.get('ExecutablePath',''),sys.executable)):
            raise ValueError('RPC PID is not the exact owned Python session; no termination')
        handle=session.k.OpenProcess(1|0x1000|0x100000,False,int(rpc['ProcessId']))
        if not handle:raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not session.k.TerminateProcess(handle,0):raise ctypes.WinError(ctypes.get_last_error())
            session.k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
            session.k.WaitForSingleObject(handle,5000)
        finally:session.k.CloseHandle(handle)
        stopped=True
    session.remove_tree(s['registry'])
    result=dict(schema=1,session=folder.name,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='PASS',rpc_owned_process_stopped=stopped,private_registry_removed=True,
        evidence_files_retained=True,real_provider_touched=False,physical=False)
    (folder/'CLEANUP.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('name',nargs='?');p.add_argument('--all-closed',action='store_true');a=p.parse_args()
    if bool(a.name)==bool(a.all_closed):p.error('Choose one session name or --all-closed')
    if a.name and (Path(a.name).name!=a.name or not a.name.replace('_','').replace('-','').isalnum()):p.error('Invalid name')
    folders=[session.WORK/a.name] if a.name else [p.parent for p in sorted(session.WORK.glob('*/session_private.json'))]
    results=[]
    for folder in folders:
        try:results.append(clean(folder))
        except Exception as e:results.append(dict(session=folder.name,status='REFUSED',reason=str(e)))
    report=session.ROOT/'reports/local/ecuflash_dynamic/SESSION_CLEANUP.json'
    report.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(report=str(report),sessions=len(results),refused=[x for x in results if x['status']!='PASS'])))
    return int(any(x['status']!='PASS' for x in results))
if __name__=='__main__':raise SystemExit(main())
