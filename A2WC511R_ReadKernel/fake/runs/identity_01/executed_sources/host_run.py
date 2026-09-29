"""One-command fixed fake-only native acquisition or named fault qualification."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,os,re,secrets,subprocess,time,argparse
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import require,sha256
from host.state import HostState
from host.owned_job import _run_owned_job
from fake.server import FAULTS
FAKE=ROOT/'fake/native/a2wc_readkernel_fake32.dll'
FAKE_SHA='58be9aaad8e004eb5bd04a600e53394a1139752f1b698ca1832124dbbb4d5cc0'

def record(path):
    return {'path':str(path),'sha256':sha256(path.read_bytes()),'bytes':path.stat().st_size}

def load_binding(label):
    require(re.fullmatch('[A-Za-z0-9_-]{1,64}',label) is not None,'Simple build label')
    directory=ROOT/'host/build'/label
    manifest=json.loads((directory/'BUILD_MANIFEST.json').read_text())
    for file in manifest['files']:
        require(sha256(Path(file['path']).read_bytes())==file['sha256'],'Host build association changed: '+file['path'])
    binding=json.loads((directory/'binding.json').read_text())
    require(binding==manifest['binding'],'Orphan binding rejected')
    require(Path(binding['fake_path'])==FAKE and binding['fake_sha256']==FAKE_SHA and sha256(FAKE.read_bytes())==FAKE_SHA,'Only exact scoped fake DLL')
    require(Path(binding['client_path'])==directory/'owned_read32.exe','Fixed build client path')
    require(Path(binding['kernel_path']).resolve().is_relative_to(ROOT/'build'),'Owned kernel build only')
    require(sha256(Path(binding['kernel_path']).read_bytes())==binding['kernel_sha256'],'Kernel changed')
    require(sha256(Path(binding['manifest_path']).read_bytes())==binding['manifest_sha256'],'Kernel manifest changed')
    return binding

def validate(folder,binding,fixture):
    native=[json.loads(line) for line in (folder/'native_api.jsonl').read_text().splitlines()]
    events=[json.loads(line) for line in (folder/'provider.jsonl').read_text().splitlines()]
    require(all('function' in event for event in native),'Native terminal error')
    require(len(native)==len(events),'Native/provider call cardinality')
    machine=HostState(Path(binding['kernel_path']).read_bytes(),binding['kernel_sha256'])
    pending=False
    for index,(a,b) in enumerate(zip(native,events)):
        q,r=b['request'],b['response']
        require(a['sequence']==index and a['function']==q['function'] and a['status']==r['status']==0,'Native/provider API correspondence')
        require(a['esp_before']==a['esp_after'],'Native stack imbalance')
        if q['function']=='PassThruWriteMsgs':
            require(not pending and machine.pending is not None,'Unexpected or repeated TX')
            wire=bytes.fromhex(a['wire_hex']);require(wire==bytes.fromhex(q['messages'][0]['data_hex'])==machine.pending.wire,'Native fixed-plan TX mismatch')
            pending=True
        elif q['function']=='PassThruReadMsgs':
            require(pending and len(r['messages'])==1,'RX cardinality/order')
            wire=bytes.fromhex(a['wire_hex']);require(wire==bytes.fromhex(r['messages'][0]['data_hex']),'Native/provider RX mismatch')
            machine.accept(wire);pending=False
    require(machine.status=='PASS' and not pending,'Entire host state machine must complete')
    require(events[-1]['request']['function']=='PassThruClose','Provider must close')
    expected=Path(fixture['path']).read_bytes()
    for pass_number in (0,1):
        raw=(folder/f'pass{pass_number}.partial.bin').read_bytes()
        require(raw==machine.images[pass_number]==expected and len(raw)==0x100000,'Every output byte must come from corresponding CPU RX and match fixture')
        (folder/f'pass{pass_number}.bin').write_bytes(raw)
    coverage=json.loads((folder/'execution_coverage.json').read_text())
    require(coverage['terminal']=='COMPLETE' and len(coverage['exchanges'])==4098,'Actual compiled startup/version/two passes must complete')
    require(all(item['status']=='PASS' for item in coverage['exchanges']),'Every compiled exchange must pass')
    return {'status':'PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS','host_replay':machine.summary(),
            'native_calls':len(native),'native_ESP_equal_calls':len(native),'CPU_kernel_executed':True,
            'kernel_terminal':coverage['terminal'],'kernel_exchanges':len(coverage['exchanges']),
            'fixture_sha256':fixture['sha256'],'full_bytes_per_pass':0x100000,
            'returned_files':[record(folder/f'pass{i}.bin') for i in (0,1)],
            'execution_coverage':record(folder/'execution_coverage.json')}

def run(build_label,fixture_name,label,fault='none'):
    require(re.fullmatch('[A-Za-z0-9_-]{1,80}',label) is not None,'Simple new session label')
    require(fault in FAULTS+('host_termination',),'Named fault only')
    binding=load_binding(build_label)
    fixtures=json.loads((ROOT/'host/fixtures/FIXTURES.json').read_text())['fixtures']
    require(fixture_name in fixtures,'Named fixed local fixture only');fixture=fixtures[fixture_name]
    require(sha256(Path(fixture['path']).read_bytes())==fixture['sha256'],'Fixture changed')
    folder=ROOT/'fake/runs'/label;folder.mkdir(parents=True,exist_ok=False)
    native=folder/'owned_read32.exe';native.write_bytes(Path(binding['client_path']).read_bytes())
    sources=folder/'executed_sources';sources.mkdir()
    source_records=[]
    for parent in ('host','fake','sim'):
        for path in sorted((ROOT/parent).glob('*.py')):
            destination=sources/(parent+'_'+path.name);destination.write_bytes(path.read_bytes())
            source_records.append({'original':str(path),**record(destination)})
    native_source=sources/'native.cpp';native_source.write_bytes((ROOT/'host/native.cpp').read_bytes());source_records.append(record(native_source))
    token=secrets.token_hex(32)
    spec={'folder':str(folder),'binding':binding,'fixture':fixture,'token':token,'fault':'none' if fault=='host_termination' else fault,'physical':False}
    spec_path=folder/'session_private.json';spec_path.write_text(json.dumps(spec,indent=2)+'\n')
    report={'schema':1,'status':'FAIL','artifact_class':'TEMP_RAM_ACQUISITION_TOOL_VIRTUAL_TEST','physical':False,
            'label':label,'fault':fault,'binding':binding,'fixture':fixture,'sources':source_records,
            'OEM_negotiation':'EXPLICIT_MODEL;NOT_FULL_OEM_PARSER_EXECUTION',
            'real_provider_loaded':False,'physical_backend_qualified':False,'close_is_ECU_reset':False}
    server=None
    with (folder/'server.log').open('x') as serverlog:
        try:
            env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
            server=subprocess.Popen([sys.executable,'-B',str(ROOT/'fake/server.py'),str(spec_path)],cwd=ROOT,env=env,stdout=serverlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            report['owned_server_pid']=server.pid
            deadline=time.monotonic()+10
            while not (folder/'ready.json').exists():
                require(server.poll() is None,'Owned fake server startup failed')
                require(time.monotonic()<deadline,'Owned fake server startup timeout');time.sleep(.02)
            ready=json.loads((folder/'ready.json').read_text())
            env.update(A2WC_RPC_TOKEN=token,A2WC_RPC_PORT=str(ready['port']),A2WC_NATIVE_API_LOG=str(folder/'fake_native_api.jsonl'))
            lifetime=_run_owned_job([str(native)],folder,env,folder/'native.log',1 if fault=='host_termination' else 7200)
            report['owned_client_lifetime']=lifetime
            deadline=time.monotonic()+5
            while not (folder/'provider_state.json').exists() and time.monotonic()<deadline:time.sleep(.02)
            if fault=='none':
                require(not lifetime['timed_out'] and lifetime['exit_code']==0,'Native fixed host failed; retained partial files')
                report.update(validate(folder,binding,fixture))
            else:
                require(lifetime['timed_out'] or lifetime['exit_code']!=0,'Fault case unexpectedly succeeded')
                require(lifetime['active_processes_after_cleanup']==0,'Native process survived termination')
                events=[json.loads(line) for line in (folder/'provider.jsonl').read_text().splitlines()]
                writes=[e for e in events if e['request']['function']=='PassThruWriteMsgs']
                # Every transmission before the terminal failure still belongs
                # to the one fixed protocol; no erase/write/reset APIs exist.
                require(all(e['request']['function'] in ('PassThruOpen','PassThruConnect','PassThruStartMsgFilter','PassThruWriteMsgs','PassThruReadMsgs','PassThruIoctl','PassThruStopMsgFilter','PassThruDisconnect','PassThruClose') for e in events),'Unexpected native API')
                report.update(status='PASS_EXPECTED_TERMINAL_FAULT',observed_native_failure=True,native_requests=len(events),wire_requests=len(writes),incomplete_files=[record(p) for p in sorted(folder.glob('pass*.partial.bin'))])
        except Exception as error:
            report.update(status='FAIL',error=type(error).__name__+': '+str(error))
        finally:
            if server is not None:
                if server.poll() is None:server.terminate()
                try:server.wait(timeout=5)
                except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
                report['owned_server_stopped']=server.poll() is not None
            report['private_session_credentials_retained_locally']=True
    report['evidence_files']=[record(p) for p in sorted(folder.glob('*')) if p.is_file() and p.name not in ('session_private.json','RESULT.json')]
    (folder/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'result':record(folder/'RESULT.json'),'error':report.get('error')},indent=2))
    return 0 if report['status'].startswith('PASS_') else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('build');parser.add_argument('fixture');parser.add_argument('label');parser.add_argument('--fault',default='none',choices=FAULTS+('host_termination',))
    args=parser.parse_args();raise SystemExit(run(args.build,args.fixture,args.label,args.fault))
