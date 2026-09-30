"""Build only an x86 fixed-read broker and instrumented fake provider."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
OUT = HERE / 'build'
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    setup = Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat')
    batch = OUT / 'build.cmd'
    batch.write_text('@echo off\ncall "' + str(setup) + '"\nif errorlevel 1 exit /b 1\n'
        + 'cl /nologo /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro "' + str(HERE/'broker.cpp')
        + '" /Febroker.exe /Fobroker.obj /link /Brepro\nif errorlevel 1 exit /b 1\n'
        + 'cl /nologo /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro /LD "' + str(HERE/'fake_j2534.cpp')
        + '" /Fefake_j2534.dll /Fofake_j2534.obj /link /Brepro /DEF:"' + str(HERE/'fake_j2534.def')
        + '"\nexit /b %errorlevel%\n')
    run = subprocess.run(['cmd.exe','/d','/c',str(batch)], cwd=OUT, capture_output=True, text=True)
    (OUT/'build.log').write_text(run.stdout+run.stderr)
    if run.returncode:
        raise SystemExit(run.stdout+run.stderr)
    paths = [HERE/n for n in ['broker.cpp','j2534_abi.h','fake_j2534.cpp','fake_j2534.def','build_broker.py']]
    paths += [OUT/'broker.exe',OUT/'fake_j2534.dll']
    record = {'status':'PASS_BUILD_ONLY_NO_PROVIDER_LOADED','architecture':'x86',
              'compiler':str(setup), 'files':{str(p):digest(p) for p in paths},
              'real_provider_loaded':False,
              'installed_provider_read_only_hash':digest(Path(r'C:\Windows\SysWOW64\op20pt32.dll'))}
    (OUT/'BUILD_MANIFEST.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))

if __name__ == '__main__':
    main()
