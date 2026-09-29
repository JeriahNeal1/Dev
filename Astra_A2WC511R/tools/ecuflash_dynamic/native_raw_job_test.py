"""Offline owned-child timeout/normal-exit checks; no fake DLL or RPC."""
import sys
sys.dont_write_bytecode=True
import os,json,time,hashlib
from pathlib import Path
from native_raw_job import _run_owned_job
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'reports/local/ecuflash_dynamic/native_raw_supplement/timeout_hardening_01'
    out.mkdir(parents=True,exist_ok=False)
    child=out/'heartbeat_child.py';parent=out/'sleeping_parent.py';beat=out/'heartbeat.txt'
    child.write_text('import time,sys\nfrom pathlib import Path\np=Path(sys.argv[1])\nwhile True:\n p.write_text(str(time.monotonic_ns()))\n time.sleep(.03)\n')
    parent.write_text('import subprocess,sys,time\nfrom pathlib import Path\np=subprocess.Popen([sys.executable,"-B",sys.argv[1],sys.argv[2]])\nPath(sys.argv[3]).write_text(str(p.pid))\ntime.sleep(120)\n')
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    timeout=_run_owned_job([sys.executable,'-B',str(parent),str(child),str(beat),str(out/'child_pid.txt')],out,env,out/'timeout.log',1)
    assert timeout['timed_out'] and timeout['exit_code']==124 and timeout['active_processes_before_cleanup']>=2
    assert timeout['active_processes_after_cleanup']==0 and beat.exists()
    stopped=beat.read_bytes();time.sleep(.3);assert beat.read_bytes()==stopped
    normal=_run_owned_job([sys.executable,'-B','-c','print("OWNED_NORMAL_EXIT")'],out,env,out/'normal.log',10)
    assert not normal['timed_out'] and normal['exit_code']==0 and normal['active_processes_after_cleanup']==0
    assert 'OWNED_NORMAL_EXIT' in (out/'normal.log').read_text()
    result={'schema':1,'status':'PASS','timeout_tree':timeout,'normal_exit':normal,'heartbeat_stopped':True,
            'provider_DLLs_loaded':0,'RPC_calls':0,'physical':False,
            'source_sha256':hashlib.sha256(Path(__file__).with_name('native_raw_job.py').read_bytes()).hexdigest()}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
