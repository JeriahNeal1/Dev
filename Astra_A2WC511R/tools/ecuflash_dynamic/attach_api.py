"""Verify exact built-in API prefixes then invoke our guard's cdecl bridges."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import ctypes as c,json,argparse,hashlib
sys.path.insert(0,r'C:\Dev\Tools\ecuflash-virtual-python')
import pefile
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args();folder=ROOT/'work/ecuflash_dynamic'/a.name;s=json.loads((folder/'session_private.json').read_text())
    assert 'ISOLATION_READY' in (folder/'guard.log').read_text()
    mp=ROOT/'reports/local/ecuflash_dynamic/api_boundary/API_ENTRY_MAP.json';mapping=json.loads(mp.read_text())
    assert hashlib.sha256(Path(s['target']).read_bytes()).hexdigest()==mapping['installed_exe_sha256']
    assert hashlib.sha256(Path(s['guard']).read_bytes()).hexdigest()==s['native_hashes'][s['guard']]
    k=c.WinDLL('kernel32',use_last_error=True);ps=c.WinDLL('psapi',use_last_error=True)
    k.OpenProcess.argtypes=[c.c_uint32,c.c_int,c.c_uint32];k.OpenProcess.restype=c.c_void_p;k.CloseHandle.argtypes=[c.c_void_p]
    k.ReadProcessMemory.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
    k.CreateRemoteThread.argtypes=[c.c_void_p,c.c_void_p,c.c_size_t,c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32)];k.CreateRemoteThread.restype=c.c_void_p
    k.WaitForSingleObject.argtypes=[c.c_void_p,c.c_uint32];k.GetExitCodeThread.argtypes=[c.c_void_p,c.POINTER(c.c_uint32)]
    ps.EnumProcessModulesEx.argtypes=[c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32),c.c_uint32];ps.GetModuleFileNameExW.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_uint32]
    h=k.OpenProcess(0x43A,False,s['pid']);assert h
    try:
        arr=(c.c_void_p*1024)();needed=c.c_uint32();assert ps.EnumProcessModulesEx(h,arr,c.sizeof(arr),c.byref(needed),3)
        modules={}
        for mod in arr[:needed.value//c.sizeof(c.c_void_p)]:
            path=c.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mod,path,len(path));modules[str(Path(path.value).resolve())]=mod
        assert not any(Path(p).name.lower()=='op20pt32.dll' for p in modules)
        base=modules[str(Path(s['target']).resolve())];guardbase=modules[str(Path(s['guard']).resolve())];checked=[]
        for entry in mapping['entries']:
            prefix=entry['prefix'];expected=bytearray.fromhex(prefix['captured_bytes'])
            for fix in prefix['image_address_fixups']:expected[fix['offset']:fix['offset']+4]=(base+int(fix['target_rva'],16)).to_bytes(4,'little')
            buf=(c.c_ubyte*len(expected))();count=c.c_size_t();address=base+int(entry['rva'],16)
            assert k.ReadProcessMemory(h,address,buf,len(buf),c.byref(count)) and count.value==len(buf)
            assert bytes(buf)==expected,(entry['name'],'prefix mismatch')
            checked.append({'name':entry['name'],'address':address,'bytes':bytes(buf).hex(),'cdecl':True})
        pe=pefile.PE(s['guard']);export=next(x for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name==b'A2WCInstallApi')
        tid=c.c_uint32();thread=k.CreateRemoteThread(h,None,0,guardbase+export.address,None,0,c.byref(tid));assert thread,c.get_last_error()
        try:
            wait=k.WaitForSingleObject(thread,10000);assert wait==0,wait
            code=c.c_uint32();assert k.GetExitCodeThread(thread,c.byref(code))
        finally:k.CloseHandle(thread)
        report={'schema':1,'status':'PASS_INSTRUMENTATION_INSTALLED' if code.value==0 else 'FAIL','thread_exit':code.value,'pid':s['pid'],'api_mapping_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'verified_entries':checked,'normal_generic_provider_selection':False,'modified_on_disk_executable':False,'physical':False}
        (folder/'API_ATTACH.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'thread_exit':code.value,'verified_entries':len(checked)}))
        if code.value:raise SystemExit(code.value)
    finally:k.CloseHandle(h)
if __name__=='__main__':main()
