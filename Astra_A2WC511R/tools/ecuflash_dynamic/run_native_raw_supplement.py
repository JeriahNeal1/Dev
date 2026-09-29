"""Run only the pinned x86 fixed-read client through the isolated native fake DLL."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
from native_raw_job import _run_owned_job
ROOT=Path(__file__).resolve().parents[2]
CLIENT=ROOT/'work/ecuflash_dynamic_native_raw_build/native_raw32.exe'
CLIENT_SHA='c49b2f7def375a62b647f7c6e546ea0ea99e071036054216ee21389eb0bd6ef1'
EXE_SHA='5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115'
MAP_SHA='6b49cc2394f9f7a35c776b8c112cab03e983cfa84f8fcb3dd08443cf3e0cd63b'
PINS={'a2wc_ecuflash_virtual32.dll':'58be9aaad8e004eb5bd04a600e53394a1139752f1b698ca1832124dbbb4d5cc0',
      'a2wc_guard32.dll':'ce33218627c52238b737005935d78971e3f34c0a70c662850b04ab98dad24f4f',
      'guarded_launcher32.exe':'3d9d14b50c04870967c2fe0ddf5a4cf845fe2277d12b5b6dbfe7942fc18b0d8c'}

def sha(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(path.read_text())
def require(condition,message):
    if not condition:raise ValueError(message)

def preflight(name):
    require(re.fullmatch('[A-Za-z0-9_-]{1,80}',name) is not None,'Simple session name')
    folder=(ROOT/'work/ecuflash_dynamic'/name).resolve()
    spec,attach,ready,live,run=[load(folder/n) for n in ['session_private.json','API_ATTACH.json','rpc_ready.json','live_state.json','RUN_RESULT.json']]
    require(Path(spec['directory']).resolve()==folder and spec['name']==name and spec['probe'] is False,'Session identity')
    target=Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe')
    require(Path(spec['target']).resolve()==target.resolve() and sha(target.read_bytes())==EXE_SHA,'Installed host pin')
    require(sha(CLIENT.read_bytes())==CLIENT_SHA,'Native fixed client pin')
    for filename,digest in PINS.items():
        path=folder/'native'/filename
        require(sha(path.read_bytes())==digest and spec['native_hashes'][str(path)]==digest,'Native isolation/fake pin')
    require(attach['status']=='PASS_INSTRUMENTATION_INSTALLED' and attach['pid']==spec['pid'] and attach['api_mapping_sha256']==MAP_SHA
            and len(attach['verified_entries'])==14 and attach['physical'] is False and attach['modified_on_disk_executable'] is False,'API attachment')
    require(run['outcome']=='SUCCESS' and run['physical'] is False and run['application_closed_normally'] is True,'Completed installed Read required')
    require(live['stage']=='KERNEL' and ready['physical'] is False and str(ready['port'])==spec['environment']['A2WC_RPC_PORT'],'Live virtual kernel/port association')
    guard=(folder/'guard.log').read_text()
    require('ISOLATION_READY Software\\A2WC511R_VirtualRead\\'+name in guard,'Original isolation record')
    require('DLL_LOADED '+str(folder/'native/a2wc_ecuflash_virtual32.dll') in guard,'Original fake load record')
    require(not re.search(r'(?im)DLL_LOADED [^\r\n]*(op20pt32\.dll|ftd2xx\.dll)',guard),'Real provider observed')
    before=(folder/'j2534.jsonl').read_bytes();rows=[json.loads(x) for x in before.splitlines()]
    require(len(rows)==live['calls'] and all(r['sequence']==i and r['physical'] is False for i,r in enumerate(rows)),'Original trace order')
    closed=[r for r in rows if r['request']['function'] in ('PassThruOpen','PassThruClose')]
    require(closed[-1]['request']['function']=='PassThruClose' and closed[-1]['response']['status']==0,'Host provider closed')
    require(len((folder/'ECUFLASH_READ_OUTPUT.bin').read_bytes())==0x100000,'Saved1MiB evidence')
    return folder,spec,before

def validate(out,folder,before):
    native=[json.loads(x) for x in (out/'NATIVE_API.jsonl').read_text().splitlines()]
    provider_bytes=(folder/'j2534.jsonl').read_bytes()
    require(provider_bytes.startswith(before),'Original trace prefix changed')
    rows=[json.loads(x) for x in provider_bytes[len(before):].splitlines()]
    require(len(native)==len(rows)==4104,'Exact native/provider call count')
    require(all(a['sequence']==i and a['function']==b['request']['function'] and a['status']==b['response']['status']==0
                and a['esp_before']==a['esp_after'] and a['physical'] is False for i,(a,b) in enumerate(zip(native,rows))),
            'Native stdcall/API/provider correspondence')
    tx=[r for r in rows if r['request']['function']=='PassThruWriteMsgs']
    require(len(tx)==2049,'Exact version plus read sequence')
    reconstructed=bytearray();commands=[]
    for i,(api,event) in enumerate(zip(native,rows)):
        fn=api['function']
        if fn=='PassThruWriteMsgs':
            wire=bytes.fromhex(event['request']['messages'][0]['data_hex']);commands.append(wire[4])
            require(api['wire_hex']==wire.hex() and event['response']['count']==1,'Native TX wire equality')
            if wire[4]==3:
                require(wire[:5]==bytes.fromhex('beef000703') and int.from_bytes(wire[5:9],'big')==len(reconstructed)
                        and wire[9:11]==b'\x02\x00' and sum(wire[:-1])&255==wire[-1],'Fixed ascending raw request')
        if fn=='PassThruReadMsgs':
            messages=event['response']['messages'];require(len(messages)==1,'One native RX')
            wire=bytes.fromhex(messages[0]['data_hex']);require(api['wire_hex']==wire.hex(),'Native RX bytes equal provider')
            if wire[4]==0x83:
                require(len(wire)==518 and wire[:5]==bytes.fromhex('beef020183') and sum(wire[:-1])&255==wire[-1],'Raw RX framing')
                reconstructed.extend(wire[5:-1])
    require(commands==[1]+[3]*2048,'No extra kernel command')
    data=(out/'NATIVE_RETURNED_BYTES.bin').read_bytes()
    require(len(data)==0x100000 and data==reconstructed,'Output actually reconstructed from native RX')
    expected=(folder/'synthetic_flash.bin').read_bytes();saved=(out/'post_read_snapshot/ECUFLASH_READ_OUTPUT.bin').read_bytes()
    require(data==expected,'Exact synthetic flash bytes')
    guard=(out/'guard.log').read_text()
    require('ISOLATION_READY' in guard and 'DLL_LOADED '+str(folder/'native/a2wc_ecuflash_virtual32.dll') in guard,'Native client guard/fake-load evidence')
    require(not re.search(r'(?im)DLL_LOADED [^\r\n]*(op20pt32\.dll|ftd2xx\.dll)',guard),'Real provider loaded')
    (out/'COMBINED_PROVIDER_TRACE.jsonl').write_bytes(provider_bytes)
    mismatches=[i for i,(a,b) in enumerate(zip(data,saved)) if a!=b]
    return {'status':'PASS_NATIVE_FAKE_ABI_VIRTUAL_ONLY','native_stdcall_api_calls':4104,'stack_pointer_preserved_calls':4104,
            'raw_blocks':2048,'returned_bytes':len(data),'returned_sha256':sha(data),'synthetic_sha256':sha(expected),
            'saved_native_Read_sha256':sha(saved),'recovered_difference_offsets':mismatches,'recovered_difference_count':len(mismatches),
            'original_trace_prefix_preserved':True,'provider_trace_sha256':sha(provider_bytes),'native_api_trace_sha256':sha((out/'NATIVE_API.jsonl').read_bytes()),
            'kernel_commands':{'01':1,'03':2048},'real_provider_loaded':False,'provider_closed':True}

def run(name):
    folder,spec,before=preflight(name)
    out=ROOT/'reports/local/ecuflash_dynamic/native_raw_supplement'/name;out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'post_read_snapshot';snapshot.mkdir()
    for filename in ['j2534.jsonl','rpc_intents.jsonl','guard.log','live_state.json','API_ATTACH.json','RUN_RESULT.json','MODEL_INPUTS.json','ECUFLASH_READ_OUTPUT.bin']:
        (snapshot/filename).write_bytes((folder/filename).read_bytes())
    require((snapshot/'j2534.jsonl').read_bytes()==before==(folder/'j2534.jsonl').read_bytes(),'Trace changed before launch')
    native=out/'native_raw32.exe';native.write_bytes(CLIENT.read_bytes())
    env=dict(spec['environment']);env.update(A2WC_NATIVE_RAW_SESSION=name,A2WC_GUARD_LOG=str(out/'guard.log'),A2WC_NATIVE_API_LOG=str(out/'fake_native_api.jsonl'))
    report={'schema':1,'status':'FAIL','session':name,'physical':False,'kernel_executed':False,'installed_Read_exactness_changed':False,
            'scope':'Fixed native x86 stdcall -> pinned fakeJ2534 DLL -> authenticated loopback model only',
            'client_sha256':CLIENT_SHA,'fake_dll_sha256':PINS['a2wc_ecuflash_virtual32.dll'],
            'original_trace':{'path':str(snapshot/'j2534.jsonl'),'sha256':sha(before),'bytes':len(before),'events':len(before.splitlines())},
            'physical_transport_qualified':False,'host_close_is_ECU_reset':False}
    try:
        lifetime=_run_owned_job([spec['launcher'],str(native),spec['guard']],out,env,out/'launcher.log',120)
        report['owned_process_lifetime']=lifetime
        records=[]
        for line in (out/'launcher.log').read_text().splitlines():
            try:records.append(json.loads(line))
            except ValueError:pass
        require(not lifetime['timed_out'] and lifetime['exit_code']==0 and records and records[-1].get('exit_code')==0,
                'Native client failed or timed out; owned process tree stopped before reporting failure')
        report.update(validate(out,folder,before));report['native_pid']=records[0]['pid']
    except Exception as error:
        report.update(status='FAIL',error=type(error).__name__+': '+str(error))
    (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return 0 if report['status'].startswith('PASS_') else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('session')
    raise SystemExit(run(parser.parse_args().session))
