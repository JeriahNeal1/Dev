"""One-command installed ECUFlash -> fake J2534 -> virtual ECU experiment.

Only the recorded, guarded PID is automated. Read, confirmation, and local raw
Save As are the complete UI action set. The real provider is never loaded.
"""
import sys
sys.dont_write_bytecode=True
import argparse,json,subprocess,time,datetime,traceback
from pathlib import Path
import session,gui,save_rom
ROOT=session.ROOT

def wait_for(predicate,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        value=predicate()
        if value:return value
        time.sleep(.1)
    raise TimeoutError('Expected guarded UI transition not observed')

def run(name,variant='baseline',fault=None):
    args=[sys.executable,'-B',str(ROOT/'tools/ecuflash_dynamic/start_virtual_read.py'),name,'--click-read','--variant',variant]
    if fault:args+=['--fault',fault]
    subprocess.run(args,check=True)
    folder=ROOT/'work/ecuflash_dynamic'/name
    spec=json.loads((folder/'session_private.json').read_text())
    app=gui.Application(backend='uia').connect(process=spec['pid'])
    main=app.window(title_re='.* - EcuFlash$',visible_only=True)
    prompt=app.window(title='Connecting to ECU',visible_only=True)
    prompt.wait('visible',timeout=15)
    initial=[x.window_text() for x in prompt.descendants(control_type='Text')]
    prompt.child_window(title='OK Enter',control_type='Button').invoke()
    print(json.dumps(dict(session=name,event='READ_STARTED',fault=fault)),flush=True)
    result=None
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        for title,outcome in (('EcuFlash success','SUCCESS'),('EcuFlash error','ERROR')):
            box=main.child_window(title=title,control_type='Window')
            if box.exists(timeout=.05):
                result=dict(schema=1,session=name,variant=variant,fault=fault,outcome=outcome,
                    initial_prompt=initial,completion_prompt=[x.window_text() for x in box.descendants(control_type='Text')],
                    physical=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
                box.child_window(title='OK Enter',control_type='Button').invoke()
                wait_for(lambda:not box.exists(timeout=.05));break
        if result:break
        if session.status(spec['pid'])!=259:raise ValueError('guarded application exited unexpectedly')
        time.sleep(.15)
    if not result:raise TimeoutError('Read operation exceeded120s fake model envelope')
    if result['outcome']=='SUCCESS':
        setup=app.window(title='Setup ROM',visible_only=True)
        setup.wait('visible',timeout=20)
        radio=setup.child_window(title='Continue using this ROM image with no definition (no editing or viewing, but saveable) Alt+C',control_type='RadioButton')
        gui.posted_click(radio.wrapper_object(),setup.wrapper_object())
        setup.child_window(title='Next > Enter',control_type='Button').wait('enabled',timeout=5)
        setup.child_window(title='Next > Enter',control_type='Button').invoke()
        wait_for(lambda:not setup.exists(timeout=.05))
        main=app.window(title_re='.* - EcuFlash$',visible_only=True)
        control=main.child_window(title='Save ROM As',control_type='Button')
        gui.posted_click(control.wrapper_object(),main.wrapper_object())
        result['save']=save_rom.save(name)
    (folder/'RUN_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    # Normal host close after recording outcome; a host close is NOT an ECU reset.
    native=gui.Application(backend='win32').connect(process=spec['pid'])
    main_hwnd=native.window(title_re='.* - EcuFlash$',visible_only=True).handle
    gui.ctypes.windll.user32.PostMessageW(main_hwnd,0x10,0,0)
    try:
        wait_for(lambda:session.status(spec['pid'])!=259,10)
        result['application_closed_normally']=True
    except TimeoutError:
        result['application_closed_normally']=False
        result['harness_forced_process_cleanup']=True
        result['cleanup_limit']='Host window did not exit after WM_CLOSE; this is not an ECU reset.'
        h=session.k.OpenProcess(1,False,spec['pid'])
        if h:session.k.TerminateProcess(h,190);session.k.CloseHandle(h)
    (folder/'RUN_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--variant',default='baseline',choices=['baseline','gaps_ff','gap_sentinels','crc_collision']);p.add_argument('--fault');a=p.parse_args()
    try:run(a.name,a.variant,a.fault)
    except Exception:
        folder=ROOT/'work/ecuflash_dynamic'/a.name
        if folder.exists():(folder/'HARNESS_ERROR.txt').write_text(traceback.format_exc())
        raise
