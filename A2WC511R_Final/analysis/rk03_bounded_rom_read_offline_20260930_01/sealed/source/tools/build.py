"""Deterministic clean zipapp packaging; never imports a provider or simulator."""
from pathlib import Path
import hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
NAMES=('__main__.py','fixed_data.py','bounded_model.py')
def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ('a','b'):raise SystemExit('Use build.py a OR b')
    out=ROOT/('build_'+sys.argv[1]);out.mkdir(exist_ok=False)
    artifact=out/'rk03_bounded_rom_read_offline.pyz'
    pins=[]
    with zipfile.ZipFile(artifact,'x',compression=zipfile.ZIP_STORED) as z:
        for name in NAMES:
            data=(ROOT/'src'/name).read_bytes();compile(data,name,'exec')
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_STORED;info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,data);pins.append({'name':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    manifest={'format':'PYTHON_ZIPAPP_STATIC_OFFLINE_MODEL','physical':False,'source':pins,
        'output':{'name':artifact.name,'bytes':artifact.stat().st_size,'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest()},
        'build_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'python_version':sys.version,'archive_mode':'stored, sorted fixed names, fixed timestamps and permissions'}
    (out/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(manifest['output']))
if __name__=='__main__':main()
