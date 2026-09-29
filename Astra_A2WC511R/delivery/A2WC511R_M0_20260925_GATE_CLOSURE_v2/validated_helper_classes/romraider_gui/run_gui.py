import concurrent.futures, hashlib, json, pathlib, secrets, subprocess, sys, time, traceback
base=pathlib.Path(__file__).parent
root=base.parents[2]
out=root/'reports/local/gate_closure/interfaces/gui_run11'
out.mkdir(parents=True,exist_ok=False)
private=root/'.runtime/gate_closure_rr';private.mkdir(parents=True,exist_ok=True)
account=subprocess.check_output(['whoami'],text=True).strip()
subprocess.run(['icacls',str(private),'/inheritance:r','/grant:r',account+':(OI)(CI)F','SYSTEM:(OI)(CI)F'],capture_output=True,check=True)
connection=private/'connection.json';properties=private/'bridge.properties'
assert not connection.exists(),'Existing bridge process must be preserved'
properties.write_text('token='+secrets.token_hex(32)+'\nconnection='+connection.as_posix()+'\nwork='+out.as_posix()+'\nallow_apply=true\n',encoding='ascii')
jar=root/'integrations/romraider/dist/romraider-bridge.jar'
args=[r'C:\Program Files\RomRaider\jdk-11.0.14.1+1-jre\bin\java.exe','-Duser.home='+str(base/'home'),'-javaagent:'+str(jar)+'='+str(properties),'-cp',';'.join([str(base/'classes'),str(jar),r'C:\Program Files\RomRaider\RomRaider.jar',r'C:\Program Files\RomRaider\lib\common\*',r'C:\Program Files\RomRaider\i18n']),'rombridge.GuiAcceptanceHost',str(base),str(out)]
(out/'command.txt').write_text(subprocess.list2cmdline(args))
sys.path.insert(0,str(root/'integrations/romraider_mcp'))
from core import Bridge
class InstrumentedBridge(Bridge):
    def request(self,op,args):
        import urllib.request,urllib.error
        from core import encoded,NoRedirect,MAX_FILE
        c=json.loads(self.connection.read_text())
        req=urllib.request.Request(c['url'],encoded({'op':op,'args':args}),{'Authorization':'Bearer '+c['token'],'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(req,timeout=260) as r:
                expected=int(r.headers['Content-Length']);assert 0<expected<=MAX_FILE
                data=bytearray()
                while len(data)<expected:
                    part=r.read(min(65536,expected-len(data)))
                    if not part:raise EOFError('Incomplete response')
                    data.extend(part)
        except urllib.error.HTTPError as e:raise RuntimeError('Bridge rejected request: '+e.read(4096).decode()) from e
        value=json.loads(data)
        if not value['ok']:raise RuntimeError(value.get('error'))
        return value['result']
class PersistentBridge(Bridge):
    conn=None
    def request(self,op,args):
        import http.client
        from urllib.parse import urlsplit
        from core import encoded,MAX_FILE
        c=json.loads(self.connection.read_text());u=urlsplit(c['url'])
        assert u.scheme=='http' and u.hostname=='127.0.0.1' and u.path=='/rpc'
        if self.conn is None:self.conn=http.client.HTTPConnection(u.hostname,u.port,timeout=260)
        self.conn.request('POST','/rpc',encoded({'op':op,'args':args}),{'Authorization':'Bearer '+c['token'],'Content-Type':'application/json'})
        r=self.conn.getresponse();data=r.read(MAX_FILE+1);assert len(data)<=MAX_FILE
        value=json.loads(data)
        if not value['ok']:raise RuntimeError(value.get('error'))
        return value['result']
b=Bridge(connection)
seq=0;events=[]
def save(name,v): (out/(name+'.json')).write_text(json.dumps(v,indent=2),encoding='utf-8')
def record(name,v):
    events.append({'check':name,'result':v});save('events',events);print(name,flush=True);return v
def wait(test,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if test():return
        if proc.poll() is not None:raise RuntimeError('Native process exited '+str(proc.returncode))
        time.sleep(.1)
    raise TimeoutError('Wait expired')
def command(op,**kwargs):
    global seq
    seq+=1;q={'op':op,**kwargs};p=out/f'command_{seq}.json';tmp=out/f'command_{seq}.tmp';tmp.write_text(json.dumps(q));tmp.rename(p)
    result=out/f'result_{seq}.json';wait(result.exists,20)
    v=json.loads(result.read_text())
    if not v['ok']:raise RuntimeError(v['error'])
    return v['result']
def snap(id='rom_1'):
    try:return b.request('snapshot',{'rom_id':id})
    except ConnectionResetError:
        record('read_only_connection_reset_retry',{'operation':'snapshot'});time.sleep(.3)
        return b.request('snapshot',{'rom_id':id})
def preview(delta=4):
    s=snap();t=next(t for t in s['tables'] if t['key']=='Idle Speed Target A');c=t['cells'][0][0]
    p=b.request('preview',{'rom_id':'rom_1','expected_rom_sha256':s['rom']['binary_sha256'],'expected_model_sha256':s['model_sha256'],'changes':[{'table':t['key'],'row':0,'column':0,'expected_raw':c['raw'],'value':c['raw']+delta,'mode':'raw','tolerance':0}],'reason':'Authorized offline actual GUI acceptance on disposable ROM','evidence':['No calibration objective: reversible native integration test only']})
    assert snap()['rom']['binary_sha256']==s['rom']['binary_sha256']
    return p
def dialog(label):
    time.sleep(.5)
    for _ in range(40):
        try:return command('inspect_dialog',label=label)
        except RuntimeError as e:
            if 'No visible native' not in str(e):raise
            time.sleep(.15)
    raise TimeoutError('Confirmation did not become visible')
def commit_ui(p,label,button='Yes',mutate=False,expire=False):
    future=executor.submit(b.request,'commit',{'preview_id':p['preview_id']})
    record(label+'_dialog',dialog(label+'_dialog'))
    if mutate:record(label+'_intervening_edit',command('native_mutation_during_dialog'))
    if expire:
        record('deadline_wait_started',{'native_request_deadline_seconds':230,'waiting_seconds':232})
        time.sleep(232)
    record(label+'_native_button',command('click_dialog',button=button))
    try:result=future.result(timeout=25)
    except RuntimeError as e:
        if button=='No' and 'cancelled' in str(e) or mutate and 'changed during approval' in str(e) or expire and 'expired' in str(e):return {'expected_rejection':str(e)}
        raise
    if button=='No' or mutate or expire:raise AssertionError('Expected rejection missing')
    assert result['binary_sha256']==p['after_sha256'];return result
def disksha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[pathlib.Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin'),pathlib.Path(r'C:\Program Files\RomRaider\RomRaider.jar'),pathlib.Path(r'C:\Program Files\RomRaider\settings.xml'),jar]
before={str(p):disksha(p) for p in protected};save('protected_before',before)
proc=None
with (out/'java.log').open('wb') as log, concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    proc=subprocess.Popen(args,cwd=base,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        wait((out/'gui_ready.json').exists,90)
        record('status',b.request('status',{}));initial=snap();save('initial_snapshot',initial)
        original=record('original_display',command('inspect',label='original_display'))
        p=record('positive_preview',preview());record('positive_commit',commit_ui(p,'positive'))
        edited=record('edited_display',command('inspect',label='edited_display'))
        assert edited['values'][0]['display']!=original['values'][0]['display']
        record('compare_original',command('compare_original'));record('compare_display',command('inspect',label='compare_display'));command('compare_off')
        p2=preview();record('cancel',commit_ui(p2,'cancel',button='No'));assert snap()['rom']['binary_sha256']==edited['sha256']
        undo=record('native_undo',command('undo'));assert undo['sha256']==original['sha256'] and undo['values'][0]['display']==original['values'][0]['display']
        p3=preview();record('stale_during_confirmation',commit_ui(p3,'stale',mutate=True));assert command('undo')['sha256']==original['sha256']
        p4=preview();record('second_positive_commit',commit_ui(p4,'second_positive'))
        editedsnap=snap();save('edited_snapshot',editedsnap);export=record('export',b.request('export_model',{'rom_id':'rom_1','expected_rom_sha256':editedsnap['rom']['binary_sha256']}))
        command('open_export',path=export['path']);time.sleep(1);record('native_export_checksum_warning',command('acknowledge_checksum',label='native_export_checksum_warning'));wait(lambda:len(b.request('status',{})['roms'])==2,45)
        exported=snap('rom_2');save('export_reopened_snapshot',exported)
        def comparable(v):
            if isinstance(v,dict):return {k:comparable(x) for k,x in v.items() if k!='original_raw'}
            if isinstance(v,list):return [comparable(x) for x in v]
            return v
        assert comparable(exported['tables'])==comparable(editedsnap['tables']) and exported['rom']['binary_sha256']==editedsnap['rom']['binary_sha256']
        record('export_reopened_display',command('select_image',index=1));command('inspect',label='export_reopened_display');command('select_image',index=0)
        command('save_as');time.sleep(.4);record('native_save_as',command('choose_save_path',label='native_save_chooser'))
        saved=base/('GUI_SAVED_'+out.name+'.NOT_FLASH_READY.bin');wait(saved.exists,20);time.sleep(.4)
        sys.path.insert(0,str(root/'reports/local/interfaces'));from checksum_audit import correction,records
        raw=pathlib.Path(export['path']).read_bytes();actual=saved.read_bytes();corrected=correction(raw)
        if isinstance(corrected,tuple):corrected=corrected[0]
        extra=[i for i,(a,c) in enumerate(zip(actual,corrected)) if a!=c]
        assert extra==list(range(0xffc4c,0xffc50)),extra
        record('save_as_byte_classification',{'disk_sha256':disksha(saved),'size':len(actual),'native_extra_vs_checksum_corrected':[hex(i) for i in extra],'native_stamp_before':raw[0xffc4c:0xffc50].hex(),'native_stamp_after':actual[0xffc4c:0xffc50].hex(),'records':records(actual)})
        command('reopen_saved');wait(lambda:len(b.request('status',{})['roms'])==3,45)
        reopened=snap('rom_3');save('native_save_reopened_snapshot',reopened)
        assert reopened['rom']['binary_sha256']==disksha(saved)
        record('native_save_reopened_display',command('select_image',index=2));command('inspect',label='native_save_reopened_display');command('select_image',index=0)
        p5=preview();record('expired_actual_commit',commit_ui(p5,'expired',expire=True))
        assert snap()['rom']['binary_sha256']==p5['before_sha256']
        after={str(p):disksha(p) for p in protected};assert before==after;save('protected_after',after)
        record('final',{'status':'PASS','actual_native_dialog_used':True,'human_click_claimed':False,'vehicle_io':False,'installed_runtime':'1.1.0','all_native_dialog_events_on_EDT':True})
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());print(traceback.format_exc(),flush=True);raise
    finally:
        if proc.poll() is None:
            try:command('stop');proc.wait(timeout=10)
            except Exception:proc.kill();proc.wait()
