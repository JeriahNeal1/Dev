"""Run native IDA with process-local plugin shadows; no installed-file edits."""
from pathlib import Path
import subprocess, os, json
ROOT=Path('C:/Dev/Astra_A2WC511R')
WORK=ROOT/'work/diaphora';OUT=ROOT/'reports/local/diaphora'
user=WORK/'ida_user_isolated';plugins=user/'plugins';plugins.mkdir(parents=True,exist_ok=True)
for name in ('diaphora_config','diaphora_plugin'):
    text='''import ida_idaapi
class A2WC_Skip_NAME(ida_idaapi.plugin_t):
    flags=0
    comment='Process-local shadow of duplicate installed Diaphora entry'
    help=''
    wanted_name='A2WC skip NAME'
    wanted_hotkey=''
    def init(self): return ida_idaapi.PLUGIN_SKIP
    def run(self,arg): pass
    def term(self): pass
def PLUGIN_ENTRY(): return A2WC_Skip_NAME()
'''.replace('NAME',name)
    p=plugins/(name+'.py')
    if p.exists():assert p.read_text()==text
    else:p.write_text(text)
rom=WORK/'inputs/probe_small.bin';rom.write_bytes(bytes.fromhex('E001000B0009'))
args=['C:/Program Files/IDA Professional 9.4/ida.exe','-A','-a','-TBinary','-psh4b','-b0',
      '-o'+str(WORK/'idbs/probe_small.i64'),'-L'+str(OUT/'isolated_probe.log'),
      '-S'+str(ROOT/'tools/diaphora/run_native_probe.py'),str(rom)]
assert not (WORK/'idbs/probe_small.i64').exists()
env=os.environ.copy();env['IDAUSR']=str(user);env['PYTHONDONTWRITEBYTECODE']='1'
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
with (OUT/'isolated_probe.stdout.log').open('w') as out,(OUT/'isolated_probe.stderr.log').open('w') as err:
    p=subprocess.Popen(args,cwd='C:/Dev',env=env,startupinfo=startup,stdout=out,stderr=err)
data={'pid':p.pid,'argv':args,'environment_overrides':{'IDAUSR':str(user),'PYTHONDONTWRITEBYTECODE':'1'},'installed_files_changed':False}
(OUT/'isolated_probe.launch.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data))
