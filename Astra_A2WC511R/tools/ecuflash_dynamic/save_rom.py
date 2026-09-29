"""Save the guarded ECUFlash Read buffer as raw bytes via its native dialog."""
import sys
sys.dont_write_bytecode=True
import argparse,json,time,hashlib
from pathlib import Path
import gui

def save(name):
    folder=gui.ROOT/'work/ecuflash_dynamic'/name
    spec=json.loads((folder/'session_private.json').read_text())
    if not (folder/'API_ATTACH.json').is_file():raise ValueError('not instrumented')
    target=folder/'ECUFLASH_READ_OUTPUT.bin'
    if target.exists():raise ValueError('never overwrite captured ROM')
    app=gui.Application(backend='win32').connect(process=spec['pid'])
    dialog=app.window(title='Choose a filename to save ROM as',class_name='#32770')
    dialog.wait('visible',timeout=15)
    combos={x.handle:x for x in dialog.descendants(class_name='ComboBox')}
    format_controls=[x for x in combos.values() if 'Raw ROM export (*.bin)' in x.texts()]
    if len(format_controls)!=1:raise ValueError('raw export selector not unique')
    format_controls[0].select('Raw ROM export (*.bin)')
    edits={x.handle:x for x in dialog.descendants(class_name='Edit')}
    names=[x for x in edits.values() if x.window_text() in ('read_image','read_image.srf','read_image.bin')]
    if len(names)!=1:raise ValueError('filename field not uniquely recognized')
    names[0].set_edit_text(str(target))
    dialog.child_window(title='&Save',class_name='Button').click()
    for _ in range(100):
        if target.is_file() and target.stat().st_size:break
        time.sleep(.1)
    else:raise ValueError('saved output not observed')
    actual=target.read_bytes();expected=(folder/'synthetic_flash.bin').read_bytes()
    report=dict(schema=1,session=name,method='INSTALLED_NATIVE_SAVE_AS_RAW_ROM_EXPORT',path=str(target),
        length=len(actual),sha256=hashlib.sha256(actual).hexdigest(),expected_sha256=hashlib.sha256(expected).hexdigest(),
        exact_equal=actual==expected,physical=False)
    (folder/'SAVE_RESULT.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('session');a=p.parse_args();print(json.dumps(save(a.session)))
