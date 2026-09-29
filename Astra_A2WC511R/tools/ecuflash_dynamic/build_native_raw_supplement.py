"""Build only the separate fixed fake-DLL client; preserve existing native builds."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'work/ecuflash_dynamic_native_raw_build'
SOURCE=Path(__file__).with_name('native_raw_supplement.cpp')
HEADER=ROOT/'integrations/ecuflash_virtual/vendor/j2534_tactrix.h'

def main():
    OUT.mkdir(exist_ok=True)
    setup=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat')
    command=OUT/'build.cmd'
    command.write_text(f'@echo off\ncall "{setup}"\nif errorlevel 1 exit /b 1\ncl /nologo /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro "{SOURCE}" /Fonative_raw.obj /Fenative_raw32.exe /link /Brepro bcrypt.lib\nif errorlevel 1 exit /b 1\n')
    build=subprocess.run(['cmd.exe','/d','/c',str(command)],cwd=OUT,capture_output=True,text=True)
    (OUT/'build.log').write_text(build.stdout+build.stderr)
    if build.returncode:print(build.stdout+build.stderr);raise SystemExit(build.returncode)
    binary=OUT/'native_raw32.exe'
    test=subprocess.run([str(binary),'--selftest'],capture_output=True,text=True)
    (OUT/'selftest.log').write_text(test.stdout+test.stderr)
    if test.returncode:print(test.stdout+test.stderr);raise SystemExit(test.returncode)
    files=[SOURCE,HEADER,Path(__file__),binary,command,OUT/'build.log',OUT/'selftest.log']
    report={'schema':1,'status':'PASS','architecture':'x86','selftest':test.stdout.strip(),'physical':False,
            'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (OUT/'BUILD_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
