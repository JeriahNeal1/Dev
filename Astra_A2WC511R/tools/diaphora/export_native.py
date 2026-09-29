"""Strict structural Diaphora export from native IDA; no metadata imports."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import os,sys,json,traceback,sqlite3,importlib.metadata
import ida_pro,ida_idaapi,ida_kernwin,ida_funcs,ida_auto,idautils,idc
TOOL=Path('C:/Dev/Tools/diaphora-3.4.2-a2wc')
ROOT=Path('C:/Dev/Astra_A2WC511R')

def bootstrap():
    assert sys.version_info[:2]==(3,14) and sys.maxsize>2**32
    sys.dont_write_bytecode=True
    for path in (TOOL/'vendor/py314-win_amd64',TOOL):
        assert path.is_dir()
        while str(path) in sys.path:sys.path.remove(str(path))
        sys.path.insert(0,str(path))
    previous=sys.modules.get('diaphora_config')
    if previous and Path(previous.__file__).resolve()!=TOOL/'diaphora_config.py':
        del sys.modules['diaphora_config']

def export(output):
    bootstrap()
    import diaphora,diaphora_ida
    assert Path(diaphora.__file__).resolve()==TOOL/'diaphora.py'
    assert Path(diaphora_ida.__file__).resolve()==TOOL/'diaphora_ida.py'
    assert not output.exists(),'Never silently replace an export'
    ida_auto.auto_wait()
    expected=list(idautils.Functions(0,0x100000))
    assert expected,'No function inventory; cannot accept empty export'
    bd=diaphora_ida.CIDABinDiff(str(output))
    options={'use_decompiler':False,'decompiler_available':False,'export_microcode':False,
        'use_trained_model':False,'exclude_library_thunk':False,'ida_subs':True,
        'function_summaries_only':False,'ignore_sub_names':True,'ignore_all_names':True,
        'min_ea':0,'max_ea':0x100000,'project_script':None}
    for key,value in options.items():setattr(bd,key,value)
    class FailClosed:
        def on_export_crash(self):return False
    bd.hooks=FailClosed()
    bd.export()
    assert not Path(str(output)+'-crash').exists()
    with sqlite3.connect(output) as connection:
        actual=sorted(int(r[0]) for r in connection.execute('select address from functions'))
        assert actual==sorted(expected),('Incomplete function export',len(actual),len(expected))
        assert connection.execute('pragma integrity_check').fetchall()==[('ok',)]
        counts={table:connection.execute('select count(*) from '+table).fetchone()[0]
            for table in ('functions','program','instructions','basic_blocks','callgraph')}
        assert counts['program']==1 and counts['instructions']>0 and counts['basic_blocks']>0
        connection.execute('pragma wal_checkpoint(TRUNCATE)')
    result={'status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),
        'database_path':idc.get_idb_path(),'export_path':str(output),'export_sha256':sha256(output.read_bytes()).hexdigest(),
        'counts':counts,'function_addresses':actual,'typed_options':options,
        'IDA_version':ida_kernwin.get_kernel_version(),'IDAPython_version':str(getattr(sys.modules.get('__main__'),'IDAPYTHON_VERSION',None)),
        'python':sys.version,'sys_path':sys.path,
        'package_versions':{n:importlib.metadata.version(n) for n in ('cdifflib','numpy','pandas','scikit-learn','scipy','joblib')},
        'diaphora_sources':{n:sha256((TOOL/n).read_bytes()).hexdigest() for n in ('diaphora.py','diaphora_ida.py','diaphora_config.py','diaphora_heuristics.py')},
        'no_decompiler_or_microcode':True,'no_metadata_import':True,'HCLI_used':False}
    output.with_suffix('.export.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','counts':counts,'output':str(output)}))

if __name__=='__main__':
    target=Path(os.environ['DIAPHORA_EXPORT_FILE'])
    code=0
    try:export(target)
    except BaseException:
        failure={'status':'FAIL','traceback':traceback.format_exc(),'sys_version':sys.version,'sys_path':sys.path,
            'IDA_version':ida_kernwin.get_kernel_version()}
        target.with_suffix('.failure.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
        traceback.print_exc();code=1
    finally:ida_pro.qexit(code)
