"""Inspect the explicitly authorized live ECUFlash diagnostic process.

Single-use Read click only; no Write, Test Write, or application launch API.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import argparse
import ctypes
import datetime
import json
import os

VENDOR = Path(r'C:\Dev\Tools\ecuflash-virtual-python')
sys.path[:0] = [str(VENDOR), str(VENDOR/'win32'), str(VENDOR/'win32/lib'), str(VENDOR/'Pythonwin')]
dll_cookie = os.add_dll_directory(str(VENDOR/'pywin32_system32'))
from pywinauto import Application


def posted_click(control, window):
    if not control.is_enabled() or not control.is_visible():
        raise RuntimeError('Control is not enabled and visible')
    class Point(ctypes.Structure):
        _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]
    point = Point()
    ctypes.windll.user32.ClientToScreen(window.handle, ctypes.byref(point))
    rect = control.rectangle()
    x, y = (rect.left + rect.right)//2 - point.x, (rect.top + rect.bottom)//2 - point.y
    if not (0 <= x <= 65535 and 0 <= y <= 65535):
        raise RuntimeError('Control outside window client')
    for message, flags in ((0x201, 1), (0x202, 0)):
        if not ctypes.windll.user32.PostMessageW(window.handle, message, flags, x | (y << 16)):
            raise ctypes.WinError()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    parser.add_argument('--action', choices=['inspect', 'read', 'continue_read', 'ack_error'], default='inspect')
    args = parser.parse_args()
    state = json.loads((args.folder/'START.json').read_text(encoding='utf-8-sig'))
    app = Application(backend='uia').connect(process=state['pid'])
    windows = app.windows(visible_only=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    records = []
    for index, window in enumerate(windows):
        controls = []
        for control in window.descendants():
            controls.append({'title': control.window_text(), 'type': control.element_info.control_type,
                             'enabled': control.is_enabled(), 'visible': control.is_visible(),
                             'rect': str(control.rectangle())})
        screenshot = args.folder/f'ui_{stamp}_{index}.png'
        window.capture_as_image().save(screenshot)
        records.append({'title': window.window_text(), 'handle': window.handle,
                        'screenshot': str(screenshot), 'controls': controls})
    with (args.folder/f'ui_{stamp}.json').open('x', encoding='utf-8') as handle:
        json.dump(records, handle, indent=2)
    print(json.dumps([{'title': item['title'], 'handle': item['handle'], 'screenshot': item['screenshot'],
                       'named_controls': [{'title': control['title'], 'type': control['type'], 'enabled': control['enabled']}
                                          for control in item['controls'] if control['title']]}
                      for item in records]))
    if args.action == 'read':
        matches = []
        for window in windows:
            matches.extend((window, item) for item in window.descendants(control_type='Button')
                           if item.window_text() == 'sti05: Read from ECU')
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one verified sti05 Read button')
        window, button = matches[0]
        if not button.is_enabled() or not button.is_visible():
            raise RuntimeError('Read button unavailable')
        with (args.folder/'READ_CLICK_ONCE.json').open('x', encoding='utf-8') as handle:
            json.dump({'utc': stamp, 'pid': state['pid'], 'button': button.window_text(),
                       'status': 'CLICK_RESERVED_NO_RETRY'}, handle, indent=2)
        posted_click(button, window)
        print(json.dumps({'status': 'READ_BUTTON_CLICK_POSTED', 'pid': state['pid']}))
    elif args.action == 'continue_read':
        if not (args.folder/'READ_CLICK_ONCE.json').is_file():
            raise RuntimeError('No authorized Read click recorded')
        dialogs = [window for window in windows if window.window_text() == 'Connecting to ECU']
        if len(dialogs) != 1:
            raise RuntimeError('Expected exact Connecting to ECU dialog')
        dialog = dialogs[0]
        text = '\n'.join(item.window_text() for item in dialog.descendants(control_type='Text'))
        if 'If your ignition is already on from a previous' not in text:
            raise RuntimeError('Connection dialog text changed')
        button = app.window(handle=dialog.handle).child_window(title='OK Enter', control_type='Button').wrapper_object()
        with (args.folder/'READ_CONTINUE_ONCE.json').open('x', encoding='utf-8') as handle:
            json.dump({'utc': stamp, 'pid': state['pid'], 'dialog': text,
                       'physical_state': 'Ignition already ON; engine OFF; Test Mode disconnected, explicitly confirmed by user',
                       'status': 'CONTINUE_RESERVED_NO_RETRY'}, handle, indent=2)
        posted_click(button, dialog)
        print(json.dumps({'status': 'READ_CONTINUE_CLICK_POSTED', 'pid': state['pid']}))
    elif args.action == 'ack_error':
        candidates = []
        for window in windows:
            candidates.extend([window] + window.descendants(control_type='Window'))
        errors = {window.handle: window for window in candidates if window.window_text() == 'EcuFlash error'}
        if len(errors) != 1:
            raise RuntimeError('Expected exact EcuFlash error dialog')
        dialog = next(iter(errors.values()))
        text = '\n'.join(item.window_text() for item in dialog.descendants(control_type='Text'))
        if text.strip() != 'An error occurred. See the log for details.':
            raise RuntimeError('Unexpected error text')
        buttons = [item for item in dialog.descendants(control_type='Button') if item.window_text() == 'OK Enter']
        if len(buttons) != 1:
            raise RuntimeError('Expected exact error acknowledgement button')
        posted_click(buttons[0], dialog)
        print(json.dumps({'status': 'ERROR_ACKNOWLEDGED', 'pid': state['pid']}))


if __name__ == '__main__':
    main()
