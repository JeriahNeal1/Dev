"""Inspect/control only a guarded process explicitly recorded in a virtual session."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import os,site,json,argparse,ctypes
VENDOR=Path(r'C:\Dev\Tools\ecuflash-virtual-python')
sys.path[:0]=[str(VENDOR),str(VENDOR/'win32'),str(VENDOR/'win32/lib'),str(VENDOR/'Pythonwin')]
dll_cookie=os.add_dll_directory(str(VENDOR/'pywin32_system32'))
from pywinauto import Application
ROOT=Path(__file__).resolve().parents[2]
def posted_click(control,window):
    if not control.is_enabled():raise ValueError('disabled control')
    class Point(ctypes.Structure):_fields_=[('x',ctypes.c_long),('y',ctypes.c_long)]
    pt=Point();ctypes.windll.user32.ClientToScreen(window.handle,ctypes.byref(pt));r=control.rectangle();x=(r.left+r.right)//2-pt.x;y=(r.top+r.bottom)//2-pt.y
    if x<0 or y<0 or x>65535 or y>65535:raise ValueError('outside client')
    ctypes.windll.user32.PostMessageW(window.handle,0x201,1,x|(y<<16));ctypes.windll.user32.PostMessageW(window.handle,0x202,0,x|(y<<16))
def main():
    p=argparse.ArgumentParser();p.add_argument('session');p.add_argument('--backend',default='win32',choices=['win32','uia']);p.add_argument('--tree',action='store_true');p.add_argument('--menu');p.add_argument('--title');p.add_argument('--text');p.add_argument('--click');p.add_argument('--select');p.add_argument('--screenshot',action='store_true');p.add_argument('--show',action='store_true');p.add_argument('--log',action='store_true');a=p.parse_args()
    folder=ROOT/'work/ecuflash_dynamic'/a.session;s=json.loads((folder/'session_private.json').read_text())
    if not 'ISOLATION_READY' in (folder/'guard.log').read_text():raise ValueError('guard not initialized')
    app=Application(backend=a.backend).connect(process=s['pid'])
    windows=app.windows(visible_only=False)
    rows=[]
    for w in windows:
        rows.append({'handle':w.handle,'title':w.window_text(),'class':w.class_name(),'visible':w.is_visible(),'enabled':w.is_enabled(),'rect':str(w.rectangle())})
    (folder/('windows_'+a.backend+'.json')).write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows))
    if a.title:w=app.window(title_re=a.title,visible_only=False).wrapper_object()
    else:w=app.top_window().wrapper_object()
    if a.show:ctypes.windll.user32.ShowWindow(w.handle,4)
    if a.select:app.window(handle=w.handle).child_window(title=a.select,control_type='TreeItem').click_input()
    if a.tree:
        app.window(handle=w.handle).print_control_identifiers()
    if a.menu:
        if any(b in a.menu.lower() for b in ('write','erase','test')):raise ValueError('forbidden UI action')
        w.menu_select(a.menu)
    if a.click:
        if any(b in a.click.lower() for b in ('write','erase','test write')):raise ValueError('forbidden UI action')
        control=app.window(handle=w.handle).child_window(title=a.click).wrapper_object()
        if a.click in ('sti05: Read from ECU','Save ROM As'):posted_click(control,w)
        elif a.backend=='uia' and control.element_info.control_type=='RadioButton':posted_click(control,w)
        elif a.backend=='uia':control.invoke()
        else:control.click()
    if a.text:
        edits=w.descendants(control_type='Edit') if a.backend=='uia' else w.descendants(class_name='Edit')
        edits[0].set_edit_text(a.text)
    if a.screenshot:w.capture_as_image().save(folder/'window.png')
    if a.log:
        for i,edit in enumerate(w.descendants(control_type='Edit')):
            try:text=edit.iface_value.CurrentValue
            except Exception:
                try:text=edit.iface_legacy_iaccessible.CurrentValue
                except Exception:text=edit.window_text()
            (folder/f'gui_edit_{i}.txt').write_text(text,encoding='utf-8');print(text[-8000:])
if __name__=='__main__':main()
