"""READ ONLY transport: verify a fixed-host capture and retain immutable raw copies.

No DLL, socket, subprocess or hardware API is imported. Pure HostState/stream
helpers are internal offline replay oracles, not generic uploader interfaces.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,re,argparse,os
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import require,sha256
from host.state import HostState
from host.stream import ResponseAssembler

def record(path,used_bytes=None):
    raw=path.read_bytes() if used_bytes is None else used_bytes
    return {'path':str(path),'sha256':sha256(raw),'bytes':len(raw)}

def require_sources_unchanged(sources):
    for path,used_bytes in sources:
        require(path.read_bytes()==used_bytes,'Capture input changed during validation: '+path.name)

def replay_native(events,kernel,kernel_sha,physical):
    """Every API and TX is checked; all RX bytes come from the native journal."""
    require(type(events) is list and events,'Complete native journal required')
    last_counter=-1;frequency=None
    for index,event in enumerate(events):
        require(event.get('sequence')==index and event.get('status')==0 and event.get('physical') is physical,'Native sequence/status/provenance')
        require(event.get('esp_before')==event.get('esp_after') and type(event.get('esp_before')) is int,'Native ABI evidence')
        for field in ('protocol','rx_status','tx_flags','timestamp','data_size','extra','utc_filetime','counter','frequency'):
            require(type(event.get(field)) is int and event[field]>=0,'Missing/invalid native metadata: '+field)
        require(event['utc_filetime']>0 and event['frequency']>0 and event['counter']>=last_counter,'Native timestamp association')
        if frequency is None:frequency=event['frequency']
        require(event['frequency']==frequency,'Native monotonic clock frequency changed')
        last_counter=event['counter']
        raw=bytes.fromhex(event['wire_hex']);require(len(raw)==event['data_size'],'Native byte/size association')
    cursor=0
    def consume(name):
        nonlocal cursor
        require(cursor<len(events) and events[cursor]['function']==name,'Wrong/missing fixed API step '+name)
        event=events[cursor];cursor+=1
        if name not in ('PassThruWriteMsgs','PassThruReadMsgs'):
            require(event['count']==0 and event['wire_hex']=='' and all(event[field]==0 for field in ('protocol','rx_status','tx_flags','timestamp','data_size','extra')),'Non-message API must have exact zero message shape')
        return event
    consume('PassThruOpen');consume('PassThruConnect');consume('PassThruStartMsgFilter')
    host=HostState(kernel,kernel_sha);baud=4800;TX=0;RX=0;fragments=0
    while host.pending:
        step=host.pending
        if step.baud!=baud:
            if step.baud==15625:consume('PassThruIoctl')
            elif step.baud==62500:
                consume('PassThruStopMsgFilter');consume('PassThruIoctl');consume('PassThruStartMsgFilter')
            else:raise ValueError('Unknown embedded baud transition')
            baud=step.baud
        tx=consume('PassThruWriteMsgs');wire=bytes.fromhex(tx['wire_hex'])
        require(tx['count']==1 and tx['protocol']==3 and tx['rx_status']==tx['tx_flags']==0 and wire==step.wire,'Actual TX outside fixed image/sequence')
        TX+=1;assembler=ResponseAssembler(wire);reply=None
        while reply is None:
            rx=consume('PassThruReadMsgs');require(rx['count']==1,'Exactly one native RX message')
            message={key:rx[key] for key in ('protocol','rx_status','tx_flags','timestamp','extra')}
            message['data_hex']=rx['wire_hex'];reply=assembler.consume(message);RX+=1
        if assembler.pieces>1:fragments+=1
        host.accept(reply)
    consume('PassThruStopMsgFilter');consume('PassThruDisconnect');consume('PassThruClose')
    require(cursor==len(events) and host.status=='PASS','Trailing calls or incomplete acquisition')
    return host,{'status':'PASS_NATIVE_JOURNAL_ONLY','API_calls':len(events),'TX_frames':TX,'RX_messages':RX,
                 'assembled_responses_with_multiple_messages':fragments,'host_replay':host.summary(),
                 'native_ESP_equal_calls':len(events),'timestamps_retained':True,
                 'timing_scope':'Timestamps retained; exact GetTickCount64 receive-deadline start is not reconstructed from QPC log, and no physical timing claim is made'}

def load_release(label,physical):
    require(re.fullmatch('[A-Za-z0-9_-]{1,64}',label) is not None,'Fixed local release label')
    directory=ROOT/'host'/('physical_build' if physical else 'build')/label
    release=json.loads((directory/'BUILD_MANIFEST.json').read_text())
    if physical:
        require(release['status']=='COMPILED_NEVER_EXECUTED_PHYSICAL_REQUIRED' and release['target_physical'] is True,'Explicit physical target release')
        certificate=Path(release['certificate']['path'])
        require(certificate==ROOT/'OFFLINE_SOFTWARE_CERTIFICATE.json' and sha256(certificate.read_bytes())==release['certificate']['sha256'],'Exact certified software')
        cert=json.loads(certificate.read_text());require(cert['eligible'] is True,'Offline acquisition ineligible')
        binding=release['tested_fake_binding'];binary=release['native_binary'];name='owned_physical_read32.exe'
        require(cert['kernel_sha256']==binding['kernel_sha256'] and cert['fake_host_sha256']==binding['client_sha256'],'Certificate/kernel/host association')
    else:
        require(release['status']=='PASS_NATIVE_FAKE_HOST_BUILD','Explicit fake target release')
        binding=release['binding'];binary={'sha256':binding['client_sha256'],'path':binding['client_path']};name='owned_read32.exe'
    require(sha256(Path(binary['path']).read_bytes())==binary['sha256'],'Release executable changed')
    kernel=Path(binding['kernel_path']).read_bytes();require(sha256(kernel)==binding['kernel_sha256'],'Release kernel changed')
    require(sha256(Path(binding['manifest_path']).read_bytes())==binding['manifest_sha256'],'Release kernel manifest changed')
    return release,binding,binary,name,kernel

def finalize(build_label,capture,physical=False):
    capture=Path(capture).resolve();require(capture.is_dir(),'Existing capture directory')
    release,binding,binary,name,kernel=load_release(build_label,physical)
    capture_binary=capture/name;capture_binary_bytes=capture_binary.read_bytes()
    require(sha256(capture_binary_bytes)==binary['sha256'],'Capture executable differs from fixed release')
    journal=capture/'native_api.jsonl';journal_bytes=journal.read_bytes()
    events=[json.loads(line) for line in journal_bytes.decode().splitlines()]
    host,proof=replay_native(events,kernel,binding['kernel_sha256'],physical)
    expected_banner='PASS_NATIVE_FIXED_PHYSICAL_TWO_FULL_READS' if physical else 'PASS_NATIVE_FAKE_TWO_FULL_READS'
    banner=capture/'native.log';banner_bytes=banner.read_bytes()
    require(expected_banner in banner_bytes.decode(),'Successful native terminal banner required')
    raws=[]
    for index in (0,1):
        path=capture/f'pass{index}.partial.bin';raw=path.read_bytes()
        require(raw==host.images[index] and len(raw)==0x100000,'Raw file not exactly reconstructed from actual RX')
        raws.append(raw)
    require(raws[0]==raws[1],'Two raw passes differ')
    used_sources=[(capture_binary,capture_binary_bytes),(journal,journal_bytes),(banner,banner_bytes)]+[(capture/f'pass{i}.partial.bin',raws[i]) for i in (0,1)]
    require_sources_unchanged(used_sources)
    destination=capture/'finalized';destination.mkdir(exist_ok=False)
    output=[]
    for index,raw in enumerate(raws):
        target=destination/f'raw_pass{index}.bin'
        with target.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        target.chmod(0o444);output.append(record(target))
    result={'schema':1,'status':'PASS_RAW_CAPTURE_INTEGRITY','classification':'USER_PHYSICAL_CAPTURE_REQUIRES_SESSION_ASSOCIATION' if physical else 'VIRTUAL_FIXTURE_CAPTURE_NOT_CURRENT_ECU_ROM',
            'provider_loaded_by_finalizer':False,'physical_transport_used_by_finalizer':False,'capture_declared_physical':physical,
            'physical_session_association_proven':False,'current_ROM_identified':False,
            'kernel_sha256':binding['kernel_sha256'],'client_sha256':binary['sha256'],'native_journal':record(journal,journal_bytes),
            'native_banner':record(banner,banner_bytes),'proof':proof,'raw_copies':output,'copies_windows_readonly_bit':True,
            'input_raw_files':[record(capture/f'pass{i}.partial.bin',raws[i]) for i in (0,1)],
            'provenance_hashes_derived_from_exact_validated_buffers':True,'inputs_rechecked_before_publication':True,
            'current_ROM_attestation':'Conditional on independent physical session association; never inferred for a virtual fixture',
            'CAL_ID_literal_offsets':[i for i in range(len(raws[0])) if raws[0].startswith(b'A2WC511R',i)],
            'close_is_ECU_reset':False,'source':record(Path(__file__))}
    out=destination/'FINALIZATION.json'
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    out.chmod(0o444);print(json.dumps({'status':result['status'],'report':record(out)},indent=2));return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--fake-build');group.add_argument('--physical-build');parser.add_argument('capture')
    args=parser.parse_args();finalize(args.physical_build or args.fake_build,args.capture,args.physical_build is not None)
