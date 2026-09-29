"""Run inside the installed IDA, never infer its Python ABI from a shell."""
from pathlib import Path
from datetime import datetime, timezone
import sys, platform, os, json, importlib.machinery, importlib.metadata, traceback
import ida_diskio, ida_kernwin, ida_idaapi, idaapi, idc

def capture(output=None,mode=None):
    target=Path(output or 'C:/Dev/Astra_A2WC511R/reports/local/diaphora/IDA_PYTHON_ENVIRONMENT.json')
    version_locations={}
    for module_name,module in [('idaapi',idaapi),('ida_idaapi',ida_idaapi),('__main__',sys.modules.get('__main__'))]:
        for attribute in ('IDAPYTHON_VERSION','__version__','IDA_SDK_VERSION'):
            if hasattr(module,attribute):version_locations[module_name+'.'+attribute]=str(getattr(module,attribute))
    if 'IDAPYTHON_VERSION' in globals():version_locations['script_global.IDAPYTHON_VERSION']=str(globals()['IDAPYTHON_VERSION'])
    packages={}
    for name in ('idapro','ida-domain','ida-mcp','numpy','pandas','scikit-learn','joblib','cdifflib','PySide6','PyQt5','PyQt6'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    plugin_paths=[str(p) for p in ida_diskio.get_ida_subdirs('plugins')]
    plugin_listing={p:sorted(x.name for x in Path(p).iterdir()) if Path(p).is_dir() else [] for p in plugin_paths}
    result={'captured_utc':datetime.now(timezone.utc).isoformat(),'execution_context':mode or 'native_IDA_script',
        'sys_version':sys.version,'sys_version_info':list(sys.version_info),'sys_executable':sys.executable,
        'sys_prefix':sys.prefix,'sys_base_prefix':sys.base_prefix,'platform_architecture':platform.architecture(),
        'platform_machine':platform.machine(),'sys_implementation':{'name':sys.implementation.name,
            'version':list(sys.implementation.version),'cache_tag':sys.implementation.cache_tag,
            'hexversion':sys.implementation.hexversion},
        'extension_suffixes':importlib.machinery.EXTENSION_SUFFIXES,
        'IDA_kernel_version':ida_kernwin.get_kernel_version(),'IDA_IDAPython_version_attributes':version_locations,
        'IDA_install_directory':ida_diskio.idadir(''),'IDA_user_directory':ida_diskio.get_user_idadir(),
        'plugin_directories':plugin_paths,'plugin_directory_entries':plugin_listing,
        'sys_path':list(sys.path),'selected_package_versions':packages,
        'module_locations':{name:getattr(module,'__file__',None) for name,module in [('idaapi',idaapi),('ida_idaapi',ida_idaapi),('ida_diskio',ida_diskio)]},
        'relevant_environment':{k:os.environ.get(k) for k in ('IDADIR','IDAUSR','PYTHONHOME','PYTHONPATH','PYTHONNOUSERSITE')},
        'database_path':idc.get_idb_path(),'HCLI_used':False}
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('execution_context','sys_version','sys_executable','IDA_kernel_version','IDA_IDAPython_version_attributes','IDA_user_directory')}))
    return result

if __name__=='__main__':
    try:
        capture()
    except BaseException:
        Path('C:/Dev/Astra_A2WC511R/reports/local/diaphora/ENV_PROBE_FAILURE.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
