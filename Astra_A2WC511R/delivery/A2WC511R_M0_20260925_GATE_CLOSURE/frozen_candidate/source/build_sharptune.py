"""Side-by-side source-exact SharpTune rebuild, using pinned .NET 4 references."""
from pathlib import Path
import subprocess,json,hashlib
BASE=Path(r'C:\Dev\Astra_A2WC511R')
SRC=BASE/'work/SharpTune_ecabea8/SharpTune'
REF=BASE/'work/tooling/net40-referenceassemblies/1.0.3/build'
OUT=BASE/'work/tooling/sharptune_offline_ecabea8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    template=(SRC/'Properties/AssemblyInfoTemplate.cs').read_text(encoding='utf-8-sig')
    (SRC/'Properties/AssemblyInfo.cs').write_text(template.replace('$GITVERSIONPLACEHOLDER$','0.1.9-RC2-12-gecabea8+offline-m0'),encoding='utf-8-sig')
    cmd=[r'C:\Windows\Microsoft.NET\Framework\v4.0.30319\MSBuild.exe',str(SRC/'RomMod.csproj'),'/t:Rebuild','/p:Configuration=Release','/p:Platform=x86','/p:PreBuildEvent=','/p:PostBuildEvent=',
         '/p:TargetFrameworkRootPath='+str(REF)+'\\','/p:FrameworkPathOverride='+str(REF/'.NETFramework/v4.0'),'/p:OutputPath='+str(OUT)+'\\','/verbosity:minimal']
    p=subprocess.run(cmd,cwd=SRC,capture_output=True,text=True,timeout=90)
    (BASE/'reports/local/build/sharptune_offline_build.log').write_text(json.dumps(cmd)+'\nEXIT '+str(p.returncode)+'\n'+p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    inputs={str(f.relative_to(SRC)):sha(f) for f in SRC.rglob('*') if f.is_file() and 'obj' not in f.parts and 'bin' not in f.parts}
    report={'source_head':'ecabea89615132dac2de37c05f72adae16d966d1','target_framework':'v4.0','architecture':'x86',
        'local_changes':['Program.cs caught exception returns false','SharpTuner.cs optional isolated offline settings without settings Save','Mod.cs explicit env opt-in applies only M0_Offline_Debug/A2WC511R.M0.EXPERIMENTAL.v1 to files beneath private offline directory','generated AssemblyInformationalVersion includes +offline-m0'],
        'pre_post_events':'Both disabled; original wildcard external copies never run',
        'source_and_embedded_resource_hashes':inputs,'original_exe_sha256':sha(Path(r'C:\Dev\MerpMod\SharpTune.exe')),
        'matched_pristine_build_sha256':sha(BASE/'work/tooling/sharptune_matching_ecabea8/SharpTune.exe'),
        'offline_exe_sha256':sha(OUT/'SharpTune.exe'),'command':cmd,
        'reference_package':{'url':'https://api.nuget.org/v3-flatcontainer/microsoft.netframework.referenceassemblies.net40/1.0.3/microsoft.netframework.referenceassemblies.net40.1.0.3.nupkg','sha256':sha(BASE/'work/tooling/net40-referenceassemblies/referenceassemblies.zip')}}
    (BASE/'reports/local/build/sharptune_provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built '+str(OUT/'SharpTune.exe')+' '+report['offline_exe_sha256'])
if __name__=='__main__':main()
