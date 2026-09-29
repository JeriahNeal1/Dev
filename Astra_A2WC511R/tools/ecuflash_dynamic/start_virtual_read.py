"""Launch exact installed ECUFlash only inside the isolated fake-provider harness."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,subprocess,time
import session
ROOT=Path(__file__).resolve().parents[2]
def command(script,*args):return subprocess.run([sys.executable,'-B',str(ROOT/'tools/ecuflash_dynamic'/script),*args],check=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--click-read',action='store_true');p.add_argument('--variant',default='baseline',choices=['baseline','gaps_ff','gap_sentinels','crc_collision']);p.add_argument('--fault');a=p.parse_args()
    sys.path.insert(0,str(ROOT/'integrations/ecuflash_virtual'))
    from faults import FaultPlan
    FaultPlan(a.fault)
    s=session.create(a.name);folder=Path(s['directory']);path=folder/'session_private.json';s.update(ecuflash_extensions=True,response_mask=0x80,variant=a.variant,fault=a.fault);path.write_text(json.dumps(s,indent=2))
    command('start_rpc.py',a.name);s=json.loads(path.read_text());session.launch(s)
    for _ in range(100):
        guard=folder/'guard.log'
        if guard.exists() and 'APPDATA_REDIRECT' in guard.read_text():break
        time.sleep(.1)
    else:raise ValueError('guarded Qt startup timeout')
    time.sleep(.5);command('attach_api.py',a.name)
    import gui
    app=gui.Application(backend='win32').connect(process=s['pid']);w=app.window(title_re='^ - EcuFlash$',visible_only=False);w.wait('exists',timeout=15)
    gui.ctypes.windll.user32.ShowWindow(w.handle,4)
    if a.click_read:
        ui=gui.Application(backend='uia').connect(process=s['pid']);button=ui.window(handle=w.handle).child_window(title='sti05: Read from ECU',control_type='Button');button.wait('enabled',timeout=15);gui.posted_click(button.wrapper_object(),ui.window(handle=w.handle).wrapper_object())
    print(json.dumps({'session':a.name,'pid':s['pid'],'instrumentation':True,'physical':False,'Read_clicked':a.click_read}))
if __name__=='__main__':main()
