"""Record the narrow RK01-to-RK02 host transition without transport calls."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/rk02/host'
OLD=ROOT/'evidence/rk02/input_snapshot'
def rec(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert (ROOT/'host/native.cpp').read_bytes()==(OLD/'host/native.cpp').read_bytes()
    assert (ROOT/'host/protocol.py').read_text()==(OLD/'host/protocol.py').read_text().replace("b'A2WC511R-RK01\\0'","b'A2WC511R-RK02\\0'")
    for name in ('host/build.py','host/state.py','host/stream.py','host/finalize.py','fake/server.py'):
        assert (ROOT/name).read_bytes()==(OLD/name).read_bytes(),name
    changed=[];files=[]
    for part in ('host','fake'):
        for path in sorted((ROOT/part).glob('*')):
            if not path.is_file() or path.suffix not in ('.py','.cpp'):continue
            files.append(rec(path));prior=OLD/part/path.name
            if prior.exists() and prior.read_bytes()!=path.read_bytes():
                patch=OUT/(part+'_'+path.name+'.patch')
                patch.write_text(''.join(difflib.unified_diff(prior.read_text().splitlines(keepends=True),path.read_text().splitlines(keepends=True),fromfile=str(prior),tofile=str(path))))
                changed.append({'old':rec(prior),'new':rec(path),'diff':rec(patch)})
    report={'schema':1,'status':'PASS_NARROW_RK02_HOST_TRANSITION','native_transport_source_identical':True,
        'native05_changed_embedded_artifact_only':True,'protocol_change':'RK01 to RK02 identity constant only',
        'model_change':'Explicit receiver_self_echo=True; kernel replies still executed CPU only',
        'runner_change':'Require CPU kernel identity and explicit receiver self echo in successful full evidence',
        'tests_change':'New output destinations and RK01 rejection/RK02 acceptance; all old reports preserved',
        'changes':changed,'current_sources':files,'native05_build':rec(ROOT/'host/build/native_05/BUILD_MANIFEST.json'),
        'physical_provider_loaded':False,'old_reports':[rec(OLD/'host/HOST_QUALIFICATION.json'),rec(OLD/'host/HOST_FAULTS.json')]}
    target=OUT/'SOURCE_TRANSITION.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rec(target)))
if __name__=='__main__':main()
