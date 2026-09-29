"""Compile-only MSVC identity probe using the native05 vcvars32 bootstrap."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/rk02/host/toolchain'
SETUP=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat')
def rec(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    source=OUT/'identity_probe.cpp';source.write_text('int rk02_toolchain_probe(void) { return 0; }\n')
    command=OUT/'identify.cmd'
    command.write_text('@echo off\ncall "'+str(SETUP)+'"\nif errorlevel 1 exit /b 1\nwhere.exe cl.exe > cl_path.txt\nwhere.exe link.exe > link_path.txt\ncl /nologo /Bv /W4 /WX /EHsc /std:c++17 /MT /O2 /Brepro /c identity_probe.cpp /Foidentity_probe.obj > compiler_version.txt 2>&1\nif errorlevel 1 exit /b 1\nlink /? > linker_version.txt 2>&1\nexit /b 0\n')
    result=subprocess.run(['cmd.exe','/d','/c',str(command)],cwd=OUT,capture_output=True,text=True)
    (OUT/'bootstrap.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,'Toolchain probe compile failed'
    compiler=Path((OUT/'cl_path.txt').read_text().splitlines()[0]);linker=Path((OUT/'link_path.txt').read_text().splitlines()[0])
    build_command=ROOT/'host/build/native_05/build.cmd'
    assert 'call "'+str(SETUP)+'"' in build_command.read_text()
    report={'schema':1,'status':'PASS_COMPILE_ONLY_TOOLCHAIN_IDENTIFICATION','executable_run':False,'provider_loaded':False,
      'compiler':rec(compiler),'linker':rec(linker),'vcvars32':rec(SETUP),'native05_command':rec(build_command),
      'compiler_version_output':rec(OUT/'compiler_version.txt'),'linker_version_output':rec(OUT/'linker_version.txt'),
      'compiler_version_text':(OUT/'compiler_version.txt').read_text(),
      'linker_banner':(OUT/'linker_version.txt').read_text().splitlines()[:3],
      'scope':'Paths resolved with the same fixed vcvars32 bootstrap; compile-only probe, no generated executable is launched',
      'evidence':[rec(p) for p in (Path(__file__),command,source,OUT/'identity_probe.obj',OUT/'bootstrap.log',OUT/'cl_path.txt',OUT/'link_path.txt')]}
    target=ROOT/'evidence/rk02/host/NATIVE_TOOLCHAIN.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rec(target)))
if __name__=='__main__':main()
