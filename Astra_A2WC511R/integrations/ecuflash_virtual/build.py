import sys
sys.dont_write_bytecode=True
from pathlib import Path
import subprocess,json,hashlib
HERE=Path(__file__).resolve().parent
OUT=HERE/'build';OUT.mkdir(exist_ok=True)
DETOURS=Path(r'C:\Dev\Tools\MicrosoftDetours')
setup=r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat'
batch=OUT/'build.cmd'
lines=['@echo off',f'call "{setup}"','if errorlevel 1 exit /b 1']
if not (DETOURS/'lib.X86/detours.lib').exists():
    lines += [f'pushd "{DETOURS / "src"}"','nmake /nologo','if errorlevel 1 exit /b 1','popd']
common=f'cl /nologo /W4 /EHsc /std:c++17 /MT /O2 /Brepro /I"{DETOURS / "include"}"'
for name,output,extras in [('guard','a2wc_guard32.dll',f'/LD /link /DEF:"{HERE/"guard.def"}" "{DETOURS/"lib.X86/detours.lib"}" advapi32.lib'),
    ('launcher','guarded_launcher32.exe',f'/link "{DETOURS/"lib.X86/detours.lib"}"'),
    ('isolation_probe','isolation_probe32.exe','/link advapi32.lib'),
    ('provider_probe','provider_probe32.exe','/link'),
    ('provider','a2wc_ecuflash_virtual32.dll',f'/LD /link /DEF:"{HERE/"provider.def"}"')]:
    before,sep,link=extras.partition('/link')
    lines += [f'{common} {before} "{HERE/(name+".cpp")}" /Fo{name}.obj /Fe{output} /link /Brepro {link}', 'if errorlevel 1 exit /b 1']
batch.write_text('\n'.join(lines)+'\n')
p=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=OUT,capture_output=True,text=True)
(OUT/'build.log').write_text(p.stdout+p.stderr)
if p.returncode:print(p.stdout+p.stderr);raise SystemExit(p.returncode)
files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*HERE.glob('*.cpp'),*HERE.glob('*.def'),*HERE.glob('*.py'),*OUT.glob('*.exe'),*OUT.glob('*.dll'),*HERE.joinpath('vendor').glob('*')]}
(OUT/'BUILD_MANIFEST.json').write_text(json.dumps({'status':'PASS','files':files},indent=2)+'\n')
print('Native build PASS')
