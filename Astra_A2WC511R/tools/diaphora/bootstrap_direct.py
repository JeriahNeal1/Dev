"""Second-path acceptance: explicit source and matching-ABI dependency paths."""
from pathlib import Path
from datetime import datetime,timezone
import sys,os,json,traceback,importlib.metadata
import ida_idaapi,ida_pro,ida_kernwin
ROOT=Path('C:/Dev/Tools/diaphora-3.4.2-a2wc')
REPORT=Path('C:/Dev/Astra_A2WC511R/reports/local/diaphora')
try:
    assert sys.version_info[:2]==(3,14) and sys.maxsize>2**32
    sys.dont_write_bytecode=True
    vendor=ROOT/'vendor/py314-win_amd64'
    for path in (vendor,ROOT):
        assert path.is_dir()
        while str(path) in sys.path:sys.path.remove(str(path))
        sys.path.insert(0,str(path))
    # A plugin shadow is not Diaphora configuration; never retain it for export.
    previous=sys.modules.get('diaphora_config')
    if previous is not None and Path(previous.__file__).resolve()!=ROOT/'diaphora_config.py':
        (REPORT/'DISPLACED_CONFIG_MODULE.json').write_text(json.dumps({'file':previous.__file__,'reason':'Scope bootstrap to full writable package instead of auto-loader shadow'},indent=2)+'\n')
        del sys.modules['diaphora_config']
    status={'utc':datetime.now(timezone.utc).isoformat(),'sys_version':sys.version,
        'IDA':ida_kernwin.get_kernel_version(),'sys_path':sys.path,
        'packages':{n:importlib.metadata.version(n) for n in ('cdifflib','numpy','pandas','scikit-learn','scipy','joblib')}}
    (REPORT/'BOOTSTRAP_NATIVE_ENVIRONMENT.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    error=ida_idaapi.IDAPython_ExecScript(str(ROOT/'diaphora.py'),globals(),True)
    if error:raise RuntimeError(error)
except BaseException:
    (REPORT/'BOOTSTRAP_FAILURE.txt').write_text(traceback.format_exc(),encoding='utf-8')
    traceback.print_exc()
    ida_pro.qexit(1)
