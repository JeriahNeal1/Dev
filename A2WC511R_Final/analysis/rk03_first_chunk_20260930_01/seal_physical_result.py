"""Preserve and validate the single completed first-chunk invocation. Read-only on ECU."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil

HERE=Path(__file__).resolve().parent
SESSION=Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\physical_session\RK03_FIRST_CHUNK_01')
OUT=HERE/'physical_result'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))
def require(ok,why):
    if not ok:raise RuntimeError(why)
def new_json(p,d):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2);f.write('\n')
execution=read(SESSION/'EXECUTION.json')
require(execution['process_exited'] is True and execution['exit_code']==0 and execution['bookkeeping_error'] is None,'Confirmed clean process exit required')
gates=read(HERE/'FIRST_CHUNK_GATE_STATE.json')
require(gates['probe_invocation_count']==1 and gates['launch_reserved'] and gates['process_exited'],'Single launched invocation')
require(gates['commit_authorization']['reply']=='PROCEED RK03 FIRST CHUNK PROBE' and gates['commit_authorization']['source']=='user','Exact authorization provenance')
for name in ['PRELAUNCH_CLIENT_CHECK.json','POSTEXIT_CLIENT_CHECK.json']:
    require(read(SESSION/name)['pass'] is True,'Diagnostic clients/provider users absent')
cert=read(HERE/'qualification/QUALIFICATION.json')
require(sha(HERE/'qualification/QUALIFICATION.json')==execution['qualification_sha256'],'Qualified certificate binding')
require(sha(cert['physical_executable']['path'])==execution['executable_sha256']==cert['physical_executable']['sha256'],'Actual qualified executable')
contract=read(HERE/'FIRST_CHUNK_REVIEW_CONTRACT.json')
rows=[json.loads(x) for x in (SESSION/'native_api.jsonl').read_text().splitlines()]
end=rows[-1]
require(end['status']=='PASS_FIRST_CHUNK_PROBE_ONLY' and end['physical'] and end['protocol_complete'],'Native physical completion')
require(end['cleanup_confirmed'] and not end['cleanup_error_mask'] and not end['log_failed'] and not end['failure'],'Native cleanup and journal')
returns=[r for r in rows if r.get('type')=='api_return'];intents=[r for r in rows if r.get('type')=='api_intent']
require(len(returns)==len(intents)==43 and [r['sequence'] for r in returns]==list(range(43)),'Complete paired journal')
require(all(r['status']==0 for r in returns),'All physical calls succeeded')
tx=[r for r in returns if r['function']=='PassThruWriteMsgs']
rx=[r for r in returns if r['function']=='PassThruReadMsgs']
require(len(tx)==8 and len(rx)==16,'Expected8requests and16receivedrecords')
for i,r in enumerate(tx):
    if i!=4:require(r['input']['message']['data_hex']==contract['ordered_requests'][i]['wire_hex'],'Fixed request differs at stage'+str(i))
    require(r['output']['count']==1,'Transmit count')
responses=[]
for i in range(8):
    indicator,data=rx[i*2:i*2+2]
    require(indicator['output']['message']['rx_status']==2 and indicator['output']['message']['data_hex']=='','Expected empty START_OF_MESSAGE')
    require(data['output']['message']['rx_status']==0 and data['output']['count']==1,'Complete data record')
    raw=bytes.fromhex(data['output']['message']['data_hex'])
    require(raw[:3]==bytes.fromhex('80f010') and len(raw)==raw[3]+5 and sum(raw[:-1])&255==raw[-1],'Reply framing/checksum')
    responses.append(raw.hex())
require(responses[1]=='80f01003c1ef8fc2' and responses[2]=='80f01007c30000ff00ff0048','Physical transition exact responses')
require(bytes.fromhex(responses[0])[8:13].hex()=='2f12515306','Physical BF identity')
require(bytes.fromhex(responses[3])[4:6]==bytes.fromhex('6701') and len(bytes.fromhex(responses[3]))==11,'Physical seed response')
require(responses[4:]==['80f0100367023420','80f01002508557','80f0100274847a','80f0100176f7'],'Exact key/session/declaration/firstchunkACKs')
state=end['state'];require(state['observed_configuration']==contract['set_config_order'] and state['effective_configuration_valid'],'Initial5 effective settings')
require(state['requested_baud']==15625 and state['baud_set_accepted'] and state['clear_mask']==3,'Baud and queue transitions accepted')
cleanup=returns[-3:]
require([r['function'] for r in cleanup]==['PassThruStopMsgFilter','PassThruDisconnect','PassThruClose'],'Final cleanup order')
waits=[dict(reason=r['input']['reason'],requested_ms=r['input']['milliseconds'],elapsed_ms=r['api_elapsed_ticks']*1000/r['qpc_frequency'],qpc_before=r['qpc_before'],qpc_after=r['qpc_after'],qpc_frequency=r['qpc_frequency']) for r in returns if r['function']=='MonotonicMinimumWait']
require([r['requested_ms'] for r in waits]==[200,100,200] and all(r['elapsed_ms']>=r['requested_ms'] for r in waits),'Physical measured waits')
OUT.mkdir(exist_ok=False);evidence=OUT/'evidence';evidence.mkdir()
preserved=[]
for p in sorted(SESSION.iterdir()):
    require(p.is_file(),'Unexpected physical session directory')
    dest=evidence/p.name
    with dest.open('xb') as f:f.write(p.read_bytes())
    require(sha(dest)==sha(p),'Evidence copy mismatch')
    preserved.append(dict(source=pin(p),preserved=pin(dest)))
new_json(OUT/'GATE_STATE_AT_RESULT.json',gates)
result=dict(schema=1,created_utc=datetime.now(timezone.utc).isoformat(),RK03_FIRST_CHUNK_PHYSICAL='PASS',
    session_id=gates['session_id'],physical_invocations=1,retry_allowed=False,process_exited=True,exit_code=0,
    ecu_identity='2F12515306',physical_C1=responses[1],physical_C3=responses[2],
    seed_response=responses[3],key_request=tx[4]['input']['message']['data_hex'],key_ack=responses[4],
    session_ack=responses[5],download_declarations=1,download_declaration=tx[6]['input']['message']['data_hex'],download_ack=responses[6],
    transfer_count=1,transfer_bytes=128,transfer_target='FFFF3000',transfer_end_exclusive='FFFF3080',
    transfer_frame_sha256=hashlib.sha256(bytes.fromhex(tx[7]['input']['message']['data_hex'])).hexdigest(),transfer_ack=responses[7],
    j2534_calls=40,logged_wait_calls=3,all_api_statuses_zero=True,all_received_records_preserved=True,
    initial_requested_configuration=state['requested_configuration'],initial_effective_configuration=state['observed_configuration'],
    broad_filter=contract['filter'],baud_set_requested=15625,baud_set_accepted=True,baud_get_performed=False,
    tx_rx_queue_clears=[7,8],measured_waits=waits,cleanup_confirmed=True,
    cleanup=[dict(function=r['function'],status=r['status']) for r in cleanup],postexit_client_check='PASS',
    kernel_start_sent=False,custom_kernel_execution=False,rom_read=False,flash_operation=False,
    full_kernel_uploaded=False,OEM_RETURN_AFTER_FIRST_CHUNK='PENDING_RECOVERY',
    next_gate='IGNITION OFF',next_stage='Only after recovery and passive OEM return: prepare FULL_KERNEL_UPLOAD_NO_START offline, never execute it in this run',
    evidence=preserved,qualification=pin(HERE/'qualification/QUALIFICATION.json'),review_contract=pin(HERE/'FIRST_CHUNK_REVIEW_CONTRACT.json'),validator=pin(Path(__file__)),
    limits=['One bounded physical first-chunk success, not full kernel upload or acquisition qualification.',
            'Baud SET succeeded and the ECU acknowledged the transfer; electrical waveform and effective baud GET were not measured.',
            'This combined transport/session path succeeded; no individual change is isolated as the cause of the older RK02 failure.',
            'Transport cleanup is confirmed; OEM return remains pending the human recovery states and passive check.'])
new_json(OUT/'PHYSICAL_RESULT.json',result)
with (OUT/'PHYSICAL_RESULT.md').open('x',encoding='utf-8',newline='\n') as f:
    f.write('# First-chunk physical result\n\nRK03_FIRST_CHUNK_PHYSICAL = PASS\n\n')
    f.write('One authorized invocation made eight requests. BF2F12515306, exact C1/C3, seed/key, session admission, one34 declaration and one fixed128-byte36 transfer all succeeded. The final response was `80 F0 10 01 76 F7`. No second transfer or later protocol action occurred.\n\n')
    f.write('All40 J2534 calls returned0. Initial five settings were read back as requested; broad filtering was installed. Baud15625 SET and TX/RX queue clears succeeded. Requested200/100/200ms waits measured203.774/102.1152/200.4695ms. StopFilter, Disconnect and Close succeeded; process exit0 and post-exit client scan passed.\n\n')
    f.write('Raw evidence and hash-pinned copies are preserved. No kernel start, ROM read or flash occurred. OEM return is pending IGNITION OFF, then NORMAL MODE ON, followed by passive BF/A8. The subsequent full-kernel-upload-no-start stage may be prepared offline only after recovery.\n')
new_json(OUT/'MANIFEST.json',dict(status='SEALED_FIRST_CHUNK_PHYSICAL_PASS',files=[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()]))
for p in list(SESSION.iterdir())+list(OUT.rglob('*')):
    if p.is_file():p.chmod(0o444)
# Update only the result fields; never overwrite a human gate recorded concurrently.
g=read(HERE/'FIRST_CHUNK_GATE_STATE.json')
g.update(first_chunk_physical='PASS',RK03_FIRST_CHUNK_PHYSICAL='PASS',physical_result=pin(OUT/'PHYSICAL_RESULT.json'),cleanup_confirmed=True,updated_utc=result['created_utc'])
(HERE/'FIRST_CHUNK_GATE_STATE.json').write_text(json.dumps(g,indent=2)+'\n',encoding='utf-8')
sp=Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json');s=read(sp)
s.update(first_chunk_physical_status='PASS',RK03_FIRST_CHUNK_PHYSICAL='PASS',first_chunk_result=str(OUT/'PHYSICAL_RESULT.json'),
    first_chunk_physical_invocations=1,first_chunk_cleanup_confirmed=True,RAM_upload_this_run=True,first_chunk_ram_transfer_bytes=128,
    first_chunk_kernel_started=False,first_chunk_ROM_read=False,first_chunk_flash_operation=False,updated_utc=result['created_utc'])
if not g['completed_recovery_gates']:
    s.update(phase='RK03_FIRST_CHUNK_PASS_WAITING_IGNITION_OFF',human_required=['IGNITION OFF'],next_action='Fresh IGNITION OFF then NORMAL MODE ON, then passive BF/A8 OEM return; no programming retry')
sp.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='RK03_FIRST_CHUNK_PHYSICAL_PASS',result=pin(OUT/'PHYSICAL_RESULT.json'),physical_files_preserved=len(preserved),next_gate=g['next_gate'])))
