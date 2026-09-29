"""Seal reviewed local collector inputs; never invokes a physical transport."""
import hashlib,json,pathlib
src=pathlib.Path(__file__).parent;root=src.parents[2];classes=root/'work/gate_closure/virtual_rr/classes'
record=lambda p:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
java=pathlib.Path(r'C:\Program Files (x86)\Java\jre1.8.0_503\bin\java.exe')
provider=pathlib.Path(r'C:\Windows\SysWOW64\op20pt32.dll')
snapshot=pathlib.Path(r'C:\Dev\A2WC511R_Sim\runs\20260925T210127.390057Z_gate_scenarios\virtual_ram_snapshots.json')
rom=root/'work/patches/m0_final_05/A2WC511R.M0.EXPERIMENTAL_UNAPPROVED.raw.bin'
libraries=[pathlib.Path(r'C:\Program Files\RomRaider\RomRaider.jar'),root/'integrations/romraider/dist/romraider-bridge.jar',*sorted(pathlib.Path(r'C:\Program Files\RomRaider\lib\common').glob('*.jar'))]
directories=[classes,pathlib.Path(r'C:\Program Files\RomRaider\i18n')]
for directory in directories:
    for p in [directory,*directory.rglob('*')]:
        assert not getattr(p.lstat(),'st_file_attributes',0)&0x400, f'Reparse point forbidden in runtime directory: {p}'
paths=[java,provider,*libraries,*[p for directory in directories for p in sorted(directory.rglob('*')) if p.is_file()],*sorted((src/'src').rglob('*.java')),src/'Invoke-ReadOnlySSM.ps1']
assert not (classes/'com/romraider').exists(),'Collector must not contain GUI factory shadows'
v={'schema':1,'classification':'OFFLINE_VERIFIED_COLLECTOR_PHYSICAL_USE_REQUIRES_HUMAN_AND_BENCH_ACCEPTANCE','java':record(java),'provider':record(provider),'snapshot':record(snapshot),'rom':record(rom),'classpath':[str(classes),*[str(p) for p in libraries],str(directories[1])],'runtime_directories':[{'path':str(directory),'files':[str(p) for p in sorted(directory.rglob('*')) if p.is_file()]} for directory in directories],'artifacts':[record(p) for p in paths],'provider_was_loaded':False}
p=src/'collector_runtime_manifest.json';p.write_text(json.dumps(v,indent=2));print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'artifacts':len(paths)}))
