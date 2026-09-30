"""Validate/preserve one completed physical session. No provider or subprocess launch."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
from launch_identity_once import HERE,SESSION,SESSION_ID,GATES,STATE,TOKEN,read,require,write_new,digest

def pin(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
def seed_key(seed):
    table=(5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8)
    keys=(0x88F0,0x6E74,0x6B70,0x3563,0x9D34,0xDBA3,0x503D,0xAFB8,0x3608,0x834F,0x3382,0x7CA3,0x437D,0x72EB,0x33BC,0x53DA)
    left,right=int.from_bytes(seed[:2],'big'),int.from_bytes(seed[2:],'big')
    for key in keys:
        expanded=(right^key)*0x10001
        sub=sum(table[(expanded>>shift)&31]<<shift for shift in (0,4,8,12))
        rotated=((sub>>3)|(sub<<13))&0xffff
        left,right=right,left^rotated
    return right.to_bytes(2,'big')+left.to_bytes(2,'big')
def wire(body):
    b=bytes.fromhex('8010f0')+bytes([len(body)])+body
    return (b+bytes([sum(b)&255])).hex()
def validate_rows(rows,contract,physical=True,bindings=None):
    require(rows and rows[0]['type']=='kernel_identity_start','Missing startup record')
    require(sum(r.get('type')=='kernel_identity_start' for r in rows)==1,'Unique startup record')
    require(all(r.get('physical',physical) is physical for r in rows),'Wrong backend class')
    if physical:
        require(bindings is not None,'Physical evidence bindings required')
        for key,value in bindings.items():require(rows[0].get(key)==value,'Startup binding '+key)
        require(Path(rows[0]['provider_path']).resolve()==Path(contract['physical_provider']['path']).resolve(),'Fixed provider path')
        require(all(rows[0].get(k) is True for k in ('authorization_verified','root_reservation_verified','native_invocation_reserved')),'Native gate evidence')
    require(rows[0]['embedded_cipher_bytes']==rows[0]['declaration_size']==1808,'Fixed upload size')
    require(rows[0]['time_model']=='QPC_MONOTONIC_MINIMUM','Physical-compatible clock model')
    intents=[r for r in rows if r.get('type')=='api_intent'];returns=[r for r in rows if r.get('type')=='api_return']
    require(len(intents)==len(returns),'Incomplete API journal')
    require(len(rows)==2*len(returns)+2 and [r['type'] for r in rows[1:-1]]==['api_intent','api_return']*len(returns),'Exact API intent/return ordering; no unaccounted events')
    require([r['sequence'] for r in intents]==list(range(len(intents)))==[r['sequence'] for r in returns],'API sequence')
    for before,after in zip(intents,returns):
        require(before['function']==after['function'] and before['input']==after['input'],'API input/return mismatch')
        require(after['status']==0,'First nonzero API status at '+str(after['sequence'])+':'+after['function']+'='+str(after['status']))
        require(after['qpc_before']<=after['qpc_after'] and after['api_elapsed_ticks']==after['qpc_after']-after['qpc_before'],'API clock accounting')
        if 'esp_before' in after:require(after['esp_before']==after['esp_after'],'API stack integrity')
    tx=[r for r in returns if r['function']=='PassThruWriteMsgs']
    require(len(tx)==24,'Expected exactly24 protocol requests; observed '+str(len(tx)))
    replies=[]
    for stage,t in enumerate(tx):
        require(t['output']['count']==1 and t['input']['message']==t['output']['message'],'TX output mutation/count')
        sent=bytes.fromhex(t['input']['message']['data_hex'])
        if stage!=4:require(sent.hex()==contract['ordered_requests'][stage]['wire_hex'],'Request mismatch stage'+str(stage))
        end=min(r['sequence'] for r in returns if r['sequence']>t['sequence'] and r['function']!='PassThruReadMsgs')
        received=[r for r in returns if t['sequence']<r['sequence']<end and r['function']=='PassThruReadMsgs']
        require(received,'Reply must precede any following control action')
        require(received[-1]['qpc_after']-received[0]['qpc_before']<2*received[0]['qpc_frequency'],'Complete reply exceeds2000ms observation window')
        data=bytearray();indicators=0
        for r in received:
            m=r['output']['message'];part=bytes.fromhex(m['data_hex'])
            require(r['output']['count']==1 and m['protocol']==3 and m['tx_flags']==0 and m['data_size']==len(part) and m['extra_data_index'] in (0,len(part)),'RX metadata')
            if m['rx_status']:
                indicators+=1;require(not data and indicators<=4,'RX indicator boundary')
                require((m['rx_status'] in (2,8) and not part) or (m['rx_status'] in (1,9) and part==sent),'RX indicator/echo')
            else:require(bool(part),'Empty data record');data.extend(part)
        require(len(data)>=6 and sum(data[:-1])&255==data[-1],'Reply checksum stage'+str(stage))
        if stage==23:require(len(data)==20 and data[:4]==bytes.fromhex('beef000f'),'Exact identity frame length/marker')
        else:require(data[:3]==bytes.fromhex('80f010') and len(data)==data[3]+5,'SSM reply framing stage'+str(stage))
        if stage==0:require(data[3]==57 and data[4:13]==bytes.fromhex('ffa210112f12515306'),'BF identity/prefix')
        elif stage==3:require(len(data)==11 and data[4:6]==bytes.fromhex('6701'),'Seed response')
        else:require(data.hex()==contract['ordered_requests'][stage]['expected_reply_hex'],'Unexpected reply stage'+str(stage))
        replies.append(data.hex())
    seed=bytes.fromhex(replies[3])[6:10]
    require(tx[4]['input']['message']['data_hex']==wire(bytes.fromhex('2702')+seed_key(seed)),'Seed/key mismatch')
    # Exact non-read control schedule; only cleanup may follow the final response.
    def action(r):
        name,inp=r['function'],r['input']
        if name=='PassThruWriteMsgs':return (name,inp['message']['data_hex'])
        if name=='PassThruIoctl':return (name,inp['ioctl'],tuple((x['parameter'],x['value']) for x in inp.get('config',{}).get('owned_buffer_entries',[])))
        if name=='MonotonicMinimumWait':return (name,inp['requested_ms'],inp['reason'])
        return (name,)
    setup=[('PassThruOpen',),('PassThruReadVersion',),('PassThruConnect',)]
    setup += [('PassThruIoctl',2,((x['parameter'],x['value']),)) for x in contract['set_config_order']]
    setup += [('PassThruIoctl',1,tuple((x['parameter'],0xD15EA5ED) for x in contract['set_config_order'])),('PassThruStartMsgFilter',)]
    wanted=setup+[('PassThruWriteMsgs',t['input']['message']['data_hex']) for t in tx[:5]]
    wanted += [('MonotonicMinimumWait',200,'post_key_ack'),('PassThruWriteMsgs',tx[5]['input']['message']['data_hex']),
        ('MonotonicMinimumWait',100,'post_session_ack'),('PassThruIoctl',2,((1,15625),)),('PassThruIoctl',7,()),('PassThruIoctl',8,()),
        ('MonotonicMinimumWait',200,'pre_download_declaration')]
    wanted += [('PassThruWriteMsgs',t['input']['message']['data_hex']) for t in tx[6:23]]
    wanted += [('PassThruStopMsgFilter',),('PassThruIoctl',2,((1,62500),)),('PassThruStartMsgFilter',),('PassThruWriteMsgs',tx[23]['input']['message']['data_hex'])]
    wanted += [('PassThruStopMsgFilter',),('PassThruDisconnect',),('PassThruClose',)]
    require([action(r) for r in returns if r['function']!='PassThruReadMsgs']==wanted,'Exact control sequence')
    device=returns[0]['output']['device'];connection=next(r for r in returns if r['function']=='PassThruConnect');channel=connection['output']['channel']
    require(returns[0]['input']=={'name_present':False,'device_output_present':True},'Open arguments')
    require(connection['input']=={'device':device,'protocol':3,'flags':512,'baud':4800,'channel_output_present':True},'Connection arguments')
    for r in returns:
        inp=r['input'];out=r['output'];name=r['function']
        if 'channel' in inp:require(inp['channel']==channel,'Channel binding')
        if 'device' in inp:require(inp['device']==device,'Device binding')
        if 'canaries_intact' in out:require(out['canaries_intact'],'API output bounds')
        if name in ('PassThruWriteMsgs','PassThruReadMsgs'):
            require(inp['input_count']==inp['message_capacity']==1 and inp['count_pointer_present'] is True,'Message count/capacity arguments')
            require(1<=inp['timeout_ms']<=1000,'Read/write timeout bound')
        if name=='PassThruWriteMsgs':
            msg=inp['message'];require(inp['timeout_ms']==1000 and msg['protocol']==3 and msg['rx_status']==msg['tx_flags']==msg['timestamp']==msg['extra_data_index']==0,'TX metadata')
        if name=='PassThruIoctl':
            require(inp['output_present'] is False,'IOCTL output pointer')
            if inp['ioctl'] in (1,2):
                count=5 if inp['ioctl']==1 else 1
                require(inp['input_present'] is True,'Config input pointer')
                for obj in (inp['config'],out['config']):
                    require(obj['list_present'] and obj['pointer_matches_owned'] and obj['returned_num_params']==obj['owned_capacity']==count,'Config list integrity')
                expected=contract['set_config_order'] if inp['ioctl']==1 else inp['config']['owned_buffer_entries']
                require(out['config']['owned_buffer_entries']==expected,'Effective configuration output')
            else:require(inp['input_present'] is False,'Queue clear input pointer')
        if name=='PassThruReadVersion':require(inp=={'device':device,'firmware_capacity':80,'dll_capacity':80,'api_capacity':80},'Version argument bounds')
    gets=[r for r in returns if r['function']=='PassThruIoctl' and r['input']['ioctl']==1]
    require(len(gets)==1 and gets[0]['output']['config']['owned_buffer_entries']==contract['set_config_order'] and gets[0]['state']['effective_configuration_valid'],'Effective serial configuration')
    filters=[r for r in returns if r['function']=='PassThruStartMsgFilter']
    require(len(filters)==2 and all(f['state']['filter']['returned_objects_valid'] for f in filters),'Both filters validated')
    filt=filters[0];require(filt['input']['filter_type']==1 and all(filt['input'][x] is True for x in ('mask_present','pattern_present','flow_present','filter_output_present')),'Filter argument/pointer contract')
    for key in ('mask','pattern','flow'):
        msg=filt['input'][key]
        require(msg==filt['output'][key] and msg['protocol']==3 and msg['rx_status']==msg['tx_flags']==msg['timestamp']==msg['extra_data_index']==0 and msg['data_size']==4 and msg['data_hex']=='00000000','Exact broad filter objects')
    kernel_filter=filters[1];require(kernel_filter['input']['filter_type']==1 and kernel_filter['input']['flow_present'] is False and kernel_filter['input']['flow'] is None and kernel_filter['output']['flow'] is None,'Identity null flow filter')
    for key,value in [('mask','ffff'),('pattern','beef')]:
        msg=kernel_filter['input'][key];require(msg==kernel_filter['output'][key] and msg['protocol']==3 and msg['rx_status']==msg['tx_flags']==msg['timestamp']==msg['extra_data_index']==0 and msg['data_size']==2 and msg['data_hex']==value,'Fixed BEEF filter object')
    stops=[r for r in returns if r['function']=='PassThruStopMsgFilter'];require(len(stops)==2 and stops[0]['input']['filter_id']==filt['output']['filter_id'] and stops[1]['input']['filter_id']==kernel_filter['output']['filter_id'],'Owned filter identifiers')
    require(returns[-3]['input']['filter_id_present'] is True,'Cleanup filter argument')
    require(tx[22]['state']['acknowledged_chunks']==15 and tx[23]['state']['start_acknowledged'] and tx[23]['state']['kernel_filter'] and tx[23]['state']['requested_baud']==62500,'Start/identity state boundary')
    waits=[r for r in returns if r['function']=='MonotonicMinimumWait']
    require([r['input']['requested_ms'] for r in waits]==[200,100,200],'Three physical minimum waits')
    for r in waits:require(r['api_elapsed_ticks']*1000>=r['input']['requested_ms']*r['qpc_frequency'],'Minimum wait duration')
    require(tx[6]['state']['requested_baud']==15625 and tx[6]['state']['baud_set_accepted'] and tx[6]['state']['clear_mask']==3,'Baud/queue state')
    require([r['function'] for r in returns[-4:]]==['PassThruReadMsgs','PassThruStopMsgFilter','PassThruDisconnect','PassThruClose'],'Immediate final cleanup order')
    terminal=rows[-1]
    expected='PASS_KERNEL_START_IDENTITY_ONLY' if physical else 'PASS_OFFLINE_KERNEL_START_IDENTITY_ONLY'
    require(terminal['status']==expected and terminal['protocol_complete'] and terminal['cleanup_confirmed'] and not terminal['cleanup_error_mask'] and not terminal['log_failed'] and not terminal['failure'],'Terminal/cleanup result')
    require(terminal['state']['tx_attempts']==24 and terminal['state']['identity_validated'] and terminal['state']['acknowledged_chunks']==15,'Final TX counter')
    return {'BF_identity':'2F12515306','tx_count':24,'declarations':1,'transfers':15,'acknowledgements':15,
        'payload_bytes':1808,'responses':replies,'seed_hex':seed.hex(),'key_request':tx[4]['input']['message']['data_hex'],
        'waits_ms_actual':[r['api_elapsed_ticks']*1000/r['qpc_frequency'] for r in waits],
        'provider_version':next(r['output'] for r in returns if r['function']=='PassThruReadVersion'),
        'serial_readback':gets[0]['output'],'filter':filters[0]['input'],'identity_filter':filters[1]['input'],'API_returns':len(returns),
        'cleanup_confirmed':True,'kernel_start_requests':1,'identity_requests':1,'entry':'FFFF3004','identity_ascii':'A2WC511R-RK02\0','ROM_read_requests':0,'flash_operations':0}
def main():
    require(sys.argv[1:]==['--seal-completed-session'],'Explicit completed-session sealing command')
    execution=read(SESSION/'EXECUTION.json');require(execution['process_exited'],'Must confirm child exit')
    gates=read(GATES);require(gates['probe_invocation_count']==1 and gates['session_id']==SESSION_ID,'Single physical invocation')
    require(gates['commit_authorization']['reply']==TOKEN and gates['commit_authorization']['source']=='user','Authorization source')
    output=HERE/'physical_result';output.mkdir(exist_ok=False)
    copied=output/'evidence';copied.mkdir()
    evidence=[]
    for source in sorted(SESSION.iterdir()):
        if source.is_file():
            target=copied/source.name
            with target.open('xb') as f:f.write(source.read_bytes())
            require(digest(source)==digest(target),'Evidence copy integrity');evidence.append(pin(source))
    validation=None;failure=None
    try:
        require(execution['exit_code']==0 and execution['bookkeeping_error'] is None,'Process exit/bookkeeping failure')
        require(digest(HERE/'qualification/QUALIFICATION.json')==execution['qualification_sha256'],'Certificate binding')
        require(read(SESSION/'POSTEXIT_CLIENT_CHECK.json')['pass'],'Provider/client cleanup inspection')
        rows=[json.loads(x) for x in (SESSION/'native_api.jsonl').read_text().splitlines()]
        cert=read(HERE/'qualification/QUALIFICATION.json');contract=read(HERE/'PHYSICAL_IDENTITY_REVIEW_CONTRACT.json')
        require(cert['session_id']==execution['session_id']==SESSION_ID,'Certificate/execution session binding')
        require(cert['physical_executable']['sha256']==execution['executable_sha256']==digest(cert['physical_executable']['path']),'Executable binding')
        require(cert['review_contract']['sha256']==execution['contract_sha256']==digest(HERE/'PHYSICAL_IDENTITY_REVIEW_CONTRACT.json'),'Contract binding')
        validation=validate_rows(rows,contract,bindings={'session_id':SESSION_ID,'exe_sha256':execution['executable_sha256'],
            'contract_sha256':execution['contract_sha256'],'provider_sha256':contract['physical_provider']['sha256']})
    except Exception as exc:failure=str(exc)
    status='PASS' if validation else 'FAIL'
    result={'schema':1,'RK03_KERNEL_START_IDENTITY_PHYSICAL':status,'session_id':SESSION_ID,
        'utc':datetime.now(timezone.utc).isoformat(),'physical_invocations':1,'execution':execution,
        'validation':validation,'validation_failure':failure,'source_evidence':evidence,'validator':pin(Path(__file__)),
        'retry_allowed':False,'additional_kernel_start_allowed':False,'next_required_state':'IGNITION OFF'}
    write_new(output/'PHYSICAL_RESULT.json',result)
    write_new(output/'MANIFEST.json',{'status':'SEALED_PHYSICAL_KERNEL_START_IDENTITY_'+status,'files':[pin(p) for p in sorted(output.rglob('*')) if p.is_file()]})
    for p in list(SESSION.iterdir())+list(output.rglob('*')):
        if p.is_file():p.chmod(0o444)
    gates.update(identity_physical=status,status='PROBE_EXITED_IGNITION_OFF_REQUIRED',next_gate='IGNITION OFF',physical_result=pin(output/'PHYSICAL_RESULT.json'))
    GATES.write_text(json.dumps(gates,indent=2)+'\n')
    state=read(STATE);state.update(RK03_KERNEL_START_IDENTITY_PHYSICAL=status,identity_physical_result=str(output/'PHYSICAL_RESULT.json'),
        identity_physical_invocations=1,next_action='IGNITION OFF then NORMAL MODE ON and passive OEM return',human_required=['IGNITION OFF'],
        identity_kernel_started=True if validation else "UNCONFIRMED",identity_ROM_read=False,identity_flash_operation=False)
    STATE.write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps({'status':status,'validation_failure':failure,'result':pin(output/'PHYSICAL_RESULT.json')}))
if __name__=='__main__':main()
