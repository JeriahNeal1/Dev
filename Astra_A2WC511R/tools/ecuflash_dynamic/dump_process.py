"""Read only the image of our guarded ECUFlash process; never attach to others."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import ctypes as c,json,argparse,hashlib
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args();folder=ROOT/'work/ecuflash_dynamic'/a.name;s=json.loads((folder/'session_private.json').read_text())
    assert 'ISOLATION_READY' in (folder/'guard.log').read_text()
    k=c.WinDLL('kernel32',use_last_error=True);ps=c.WinDLL('psapi',use_last_error=True)
    k.OpenProcess.argtypes=[c.c_uint32,c.c_int,c.c_uint32];k.OpenProcess.restype=c.c_void_p;k.CloseHandle.argtypes=[c.c_void_p]
    k.ReadProcessMemory.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
    ps.EnumProcessModulesEx.argtypes=[c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32),c.c_uint32]
    ps.GetModuleFileNameExW.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_uint32]
    class MI(c.Structure):_fields_=[('base',c.c_void_p),('size',c.c_uint32),('entry',c.c_void_p)]
    ps.GetModuleInformation.argtypes=[c.c_void_p,c.c_void_p,c.POINTER(MI),c.c_uint32]
    h=k.OpenProcess(0x410,False,s['pid']);assert h
    try:
        arr=(c.c_void_p*1024)();needed=c.c_uint32();assert ps.EnumProcessModulesEx(h,arr,c.sizeof(arr),c.byref(needed),3)
        modules=[]
        for mod in arr[:needed.value//c.sizeof(c.c_void_p)]:
            path=c.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mod,path,len(path));mi=MI();assert ps.GetModuleInformation(h,mod,c.byref(mi),c.sizeof(mi))
            modules.append({'path':path.value,'base':mi.base,'size':mi.size,'entry':mi.entry})
        assert not any(Path(m['path']).name.lower()=='op20pt32.dll' for m in modules)
        target=next(m for m in modules if Path(m['path']).name.lower()=='ecuflash.exe')
        assert Path(target['path']).resolve()==Path(s['target']).resolve()
        out=bytearray(target['size']);missing=[]
        for offset in range(0,len(out),4096):
            n=min(4096,len(out)-offset);buf=(c.c_ubyte*n)();count=c.c_size_t()
            if k.ReadProcessMemory(h,target['base']+offset,buf,n,c.byref(count)) and count.value==n:out[offset:offset+n]=bytes(buf)
            else:missing.append([offset,offset+n,c.get_last_error()])
        destination=folder/'loaded_ecuflash_image.bin';destination.write_bytes(out)
        report={'pid':s['pid'],'source':'GUARDED_LIVE_PROCESS_IMAGE_NOT_ON_DISK_REPLACEMENT','image':str(destination),'sha256':hashlib.sha256(out).hexdigest(),'target':target,'modules':modules,'unreadable_zero_placeholders':missing}
        (folder/'loaded_ecuflash_image.json').write_text(json.dumps(report,indent=2));print(json.dumps({'image':str(destination),'sha256':report['sha256'],'base':target['base'],'size':target['size'],'unreadable_pages':len(missing),'real_provider_loaded':False}))
    finally:k.CloseHandle(h)
if __name__=='__main__':main()
