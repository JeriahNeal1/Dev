"""Native pre-load rejection controls; never loads a provider or connects RPC."""
import sys
sys.dont_write_bytecode=True
import os,subprocess,hashlib,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EXE=ROOT/'work/ecuflash_dynamic_native_raw_build/native_raw32.exe'
EXPECTED='c49b2f7def375a62b647f7c6e546ea0ea99e071036054216ee21389eb0bd6ef1'

def main():
    if hashlib.sha256(EXE.read_bytes()).hexdigest()!=EXPECTED:raise ValueError('Native test client hash changed')
    env=os.environ.copy();env['A2WC_NATIVE_RAW_SESSION']='native_preload_control'
    env['A2WC_FAKE_DLL']=r'C:\Windows\SysWOW64\op20pt32.dll'
    tests=[]
    def reject(args,needle,name):
        result=subprocess.run([str(EXE),*args],env=env,capture_output=True,text=True,timeout=10)
        if result.returncode!=1 or needle not in result.stderr:raise ValueError('Preload negative failed: '+name)
        tests.append({'name':name,'exit_code':result.returncode,'stderr':result.stderr.strip()})
    reject([],"Only session's exact fake path",'foreign provider path rejected before LoadLibrary')
    reject([r'C:\Windows\SysWOW64\op20pt32.dll'],'No transport/path','provider path argument rejected')
    folder=Path(tempfile.mkdtemp(prefix='native_preload_negative_',dir=ROOT/'work/ecuflash_dynamic'))
    (folder/'native').mkdir();dummy=folder/'native/a2wc_ecuflash_virtual32.dll'
    dummy.write_bytes(b'NOT_AN_EXECUTABLE_A2WC_NEGATIVE_CONTROL')
    env['A2WC_NATIVE_RAW_SESSION']=folder.name;env['A2WC_FAKE_DLL']=str(dummy)
    reject([],'SHA256 pin mismatch before loading','changed fake hash rejected before LoadLibrary')
    print(json.dumps({'status':'PASS','tests':tests,'provider_DLLs_loaded':0,'RPC_calls':0,'physical':False,
                      'retained_negative_fixture':str(dummy),'fixture_sha256':hashlib.sha256(dummy.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':main()
