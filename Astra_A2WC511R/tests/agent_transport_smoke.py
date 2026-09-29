"""Run compiled Java agent against source-contract doubles, not actual RomRaider.
Compile Java test fixtures first with Build-RomRaiderBridge.ps1 -RunModelTests.
"""
from pathlib import Path
import json, os, secrets, subprocess, sys, tempfile, time, urllib.request, urllib.error
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'integrations'/'romraider_mcp'))
from core import Bridge

def run():
    base=ROOT/'integrations'/'romraider'
    cp=os.pathsep.join(str(base/'build'/x) for x in ['classes','test_classes'])
    assertions=0
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);conn=d/'connection.json';props=d/'bridge.properties'
        props.write_text('token='+secrets.token_hex(32)+'\nconnection='+conn.as_posix()+'\nwork='+d.as_posix()+'\nallow_apply=false\n',encoding='ascii')
        p=subprocess.Popen([os.environ.get('JAVA_EXE','java'),'-Djava.awt.headless=true','-javaagent:'+str(base/'dist'/'romraider-bridge.jar')+'='+str(props),'-cp',cp,'rombridge.FixtureApplication'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            assert p.stdout.readline().strip()=='FIXTURE_READY';assertions+=1
            for _ in range(50):
                if conn.exists():break
                time.sleep(.05)
            bridge=Bridge(conn);status=bridge.request('status',{});assert status['roms'][0]['calid']=='A2WC511R';assertions+=1
            snap=bridge.request('snapshot',{'rom_id':'rom_1'});assert len(snap['tables'])==1;assertions+=1
            before=snap['rom']['binary_sha256']
            q={'rom_id':'rom_1','expected_rom_sha256':before,'expected_model_sha256':snap['model_sha256'],'changes':[{'table':'Fixture','row':0,'column':0,'expected_raw':10,'value':6,'mode':'real','tolerance':0}],'reason':'Synthetic transport smoke test','evidence':['source-contract fixture, not vehicle data']}
            preview=bridge.request('preview',q);assert preview['rom_restored'] and preview['after_sha256']!=before;assertions+=1
            assert bridge.request('status',{})['roms'][0]['binary_sha256']==before;assertions+=1
            c=json.loads(conn.read_text())
            for headers in ({},{'Authorization':'Bearer '+c['token'],'Origin':'https://example.invalid'},{'Authorization':'Bearer '+c['token'],'Host':'example.invalid'}):
                req=urllib.request.Request(c['url'],json.dumps({'op':'status','args':{}}).encode(),headers,method='POST')
                try:urllib.request.urlopen(req,timeout=5);raise AssertionError('Invalid auth/host/origin accepted')
                except urllib.error.HTTPError as e:assert e.code==403;assertions+=1
            try:bridge.request('commit',{'preview_id':preview['preview_id']});raise AssertionError('Read-only applied')
            except RuntimeError as e:assert 'SecurityException' in str(e);assertions+=1
            assert bridge.request('status',{})['roms'][0]['binary_sha256']==before;assertions+=1
            p.stdin.close();p.wait(timeout=10)
            assert p.returncode==0 and not conn.exists();assertions+=1
        finally:
            if p.poll() is None:p.kill();p.wait(timeout=5)
    print(f'PASS {assertions} actual Java-agent HTTP/EDT assertions against a test-double host; NOT actual RomRaider/Windows.')
if __name__=='__main__':run()
