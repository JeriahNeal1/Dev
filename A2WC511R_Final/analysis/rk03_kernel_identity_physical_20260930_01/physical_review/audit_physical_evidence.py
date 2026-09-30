"""Independent completed-evidence audit. Reads files only; never dispatches a client."""
from pathlib import Path
import collections, datetime as dt, hashlib, json

A = Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_kernel_identity_physical_20260930_01')
OUT = A / 'physical_review'
RESULT = A / 'physical_result/PHYSICAL_RESULT.json'
checks = []
pins = {}
def check(ok, detail):
    if not ok: raise AssertionError(detail)
    checks.append(detail)
def pin(path):
    path = Path(path); data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
def bind(path, expected=None):
    p = pin(path)
    if expected:
        check(p['sha256'] == expected['sha256'], 'SHA256: ' + p['path'])
        if 'bytes' in expected: check(p['bytes'] == expected['bytes'], 'Size: ' + p['path'])
    pins[p['path']] = p
    return p
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path, obj):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2); f.write('\n')
def key(seed):
    # Independent Python arithmetic translation of the preserved reviewed algorithm.
    table = [5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8]
    rounds = [0x88F0,0x6E74,0x6B70,0x3563,0x9D34,0xDBA3,0x503D,0xAFB8,0x3608,0x834F,0x3382,0x7CA3,0x437D,0x72EB,0x33BC,0x53DA]
    left, right = int.from_bytes(seed[:2], 'big'), int.from_bytes(seed[2:], 'big')
    for k in rounds:
        expanded = (right ^ k) * 0x10001
        v = sum(table[(expanded >> s) & 31] << s for s in (0,4,8,12))
        v = ((v >> 3) | (v << 13)) & 0xffff
        left, right = right, left ^ v
    return right.to_bytes(2,'big') + left.to_bytes(2,'big')
def config(r, values, ioctl=2):
    i, o = r['input'], r['output']
    check(i['ioctl']==ioctl and i['input_present'] and not i['output_present'], 'Config API shape '+str(r['sequence']))
    check(o['canaries_intact'], 'Config canaries '+str(r['sequence']))
    for c in [i['config'],o['config']]:
        check(c['list_present'] and c['returned_num_params']==len(values) and c['owned_capacity']==len(values)
              and c['pointer_matches_owned'] and c['config_pointer']==c['owned_buffer_pointer'], 'Config list bounds '+str(r['sequence']))
    check(o['config']['owned_buffer_entries']==values, 'Provider-returned configuration '+str(r['sequence']))
    if ioctl==2: check(i['config']==o['config'], 'Unmutated SET_CONFIG '+str(r['sequence']))
def message(m):
    b=bytes.fromhex(m['data_hex'])
    check(m['protocol']==3 and m['tx_flags']==0 and m['data_size']==m['logged_bytes']==len(b)
          and m['buffer_capacity']==4128 and not m['data_truncated'], 'Bounded protocol-3 message')
    return b

def main():
    bind(RESULT, {'sha256':'2f524a38ef883b189aeab55ac1c06127c6f8164eeccca835f81fd78d5f7fdcda'})
    result=read(RESULT); ex=result['execution']
    check(result['RK03_KERNEL_START_IDENTITY_PHYSICAL']=='PASS' and result['physical_invocations']==1, 'Root result records one PASS')
    for p in result['source_evidence']: bind(p['path'], p)
    bind(result['validator']['path'], result['validator'])
    session=Path(ex['command_argv'][3])
    certpath=A/'qualification/QUALIFICATION.json'; bind(certpath, {'sha256':ex['qualification_sha256']}); cert=read(certpath)
    bind(cert['physical_executable']['path'], cert['physical_executable'])
    bind(cert['review_contract']['path'], cert['review_contract']); contract=read(cert['review_contract']['path'])
    bind(cert['fixed_upload_manifest']['path'], cert['fixed_upload_manifest']); manifest=read(cert['fixed_upload_manifest']['path'])
    bind(contract['physical_provider']['path'], contract['physical_provider'])
    bind(manifest['expected_uploaded_ram']['path'], manifest['expected_uploaded_ram'])
    protocol=session.parents[1]/'kernel_identity_physical/src/protocol.hpp'
    protocol_pin=next(p for p in cert['files'] if Path(p['path'])==protocol); bind(protocol, protocol_pin)
    bind(__file__)
    check(cert['session_id']==contract['session_id']==ex['session_id']==result['session_id']=='RK03_KERNEL_START_IDENTITY_01', 'Session binding')
    check(cert['physical_executable']['sha256']==ex['executable_sha256']=='623dc766ca69a97b16f7beabc9acb909a1225eabb8a21c40fe8379b4f72b593f', 'Qualified executable binding')
    check(cert['review_contract']['sha256']==ex['contract_sha256']=='5f2b1e263d98bc1a4a957770ea8e3c214a6ffb5a6798caf7aba79bcc5ecfe167', 'Qualified contract binding')
    check(ex==read(session/'EXECUTION.json'), 'Execution summary equals preserved record')
    begin=read(session/'EXECUTION_BEGIN.json'); check(all(ex[k]==v for k,v in begin.items()), 'Begin/end execution records agree')
    check(ex['exit_code']==0 and ex['process_exited'] and ex['bookkeeping_error'] is None and not ex['retry_allowed'], 'Recorded exit0 without bookkeeping failure or retry')
    check(ex['command_argv']==[cert['physical_executable']['path'],'--physical-kernel-start-identity','--session',str(session),'--authorization-file',str(session/'AUTHORIZATION.txt')], 'Exact physical command recorded')
    auth=(contract['requires_exact_human_authorization']+'\nSESSION_ID='+ex['session_id']+'\nEXE_SHA256='+ex['executable_sha256']+'\nCONTRACT_SHA256='+ex['contract_sha256']+'\n').encode()
    marker=(ex['session_id']+'\n'+ex['executable_sha256']+'\n'+ex['contract_sha256']+'\n').encode()
    check((session/'AUTHORIZATION.txt').read_bytes()==auth, 'Exact authorization bytes')
    check((session/'invocation.once').read_bytes()==(session/'launch.reserved').read_bytes()==marker, 'Exact matching one-shot markers')
    gate=read(A/'IDENTITY_GATE_STATE.json')
    receipt={'observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'origin':str(A/'IDENTITY_GATE_STATE.json'),
             'session_id':gate['session_id'],'qualification_sha256':gate['qualification_sha256'],
             'completed_pre_probe_gates':gate['completed_pre_probe_gates'],'commit_authorization':gate['commit_authorization']}
    receipts=receipt['completed_pre_probe_gates']+[receipt['commit_authorization']]
    check([x['reply'] for x in receipts]==['IGNITION OFF','TEST MODE ON','PROCEED RK03 KERNEL START IDENTITY'], 'Fresh gate and commit receipt order')
    check(all(x['source']=='user' and x['session_id']==ex['session_id'] and x['qualification_sha256']==ex['qualification_sha256'] for x in receipts), 'Receipt source and certificate binding')
    times=[dt.datetime.fromisoformat(x['received_utc']) for x in receipts]+[dt.datetime.fromisoformat(ex['started_utc']),dt.datetime.fromisoformat(ex['exited_utc'])]
    check(times==sorted(times) and len(set(times))==len(times), 'Fresh receipts precede recorded launch and exit')
    for name,before in [('PRELAUNCH_CLIENT_CHECK.json',True),('POSTEXIT_CLIENT_CHECK.json',False)]:
        scan=read(session/name)
        check(scan['pass'] and not scan['known_conflicting_clients'] and not scan['provider_module_users'] and not scan['module_inspection_failures'] and not scan['real_provider_loaded_by_check'], 'Recorded empty client/module scan '+name)
        stamp=dt.datetime.fromisoformat(scan['utc'].replace('Z','+00:00'))
        check(stamp<times[-2] if before else stamp>times[-1], 'Recorded scan timing '+name)
    rows=[json.loads(s) for s in (session/'native_api.jsonl').read_text().splitlines()]
    start, terminal=rows[0], rows[-1]
    check(start['type']=='kernel_identity_start' and start['physical'] is True, 'Physical startup envelope')
    for k,v in [('session_id',ex['session_id']),('exe_sha256',ex['executable_sha256']),('contract_sha256',ex['contract_sha256']),('provider_path',contract['physical_provider']['path']),('provider_sha256',contract['physical_provider']['sha256']),('time_model','QPC_MONOTONIC_MINIMUM'),('embedded_cipher_bytes',1808),('declaration_size',1808)]: check(start[k]==v, 'Startup '+k)
    check(all(start[k] is True for k in ['authorization_verified','root_reservation_verified','native_invocation_reserved']), 'Native authorization and reservation verification flags')
    intents=rows[1:-1:2]; returns=rows[2:-1:2]
    check(len(rows)==190 and len(intents)==len(returns)==94, 'Exactly 94 complete call pairs plus startup/terminal')
    for n,(i,r) in enumerate(zip(intents,returns)):
        check(i['type']=='api_intent' and r['type']=='api_return' and i['sequence']==r['sequence']==n and i['function']==r['function'] and i['input']==r['input'], 'Exact paired call '+str(n))
        check(i['physical'] is True and r['physical'] is True and r['status']==0, 'Physical successful API '+str(n))
        check(r['qpc_before']<=r['qpc_after'] and r['api_elapsed_ticks']==r['qpc_after']-r['qpc_before'] and r['qpc_frequency']==10000000, 'Clock integrity '+str(n))
        if n<91: check(r['esp_before']==r['esp_after'], 'Recorded stack integrity '+str(n))
        else: check('esp_before' not in r and 'esp_after' not in r, 'Cleanup schema has no stack-pointer fields '+str(n))
        if n: check(returns[n-1]['qpc_after']<=r['qpc_before'] and returns[n-1]['utc_filetime']<=r['utc_filetime'], 'Monotonic complete API order '+str(n))
        if 'canaries_intact' in r['output']: check(r['output']['canaries_intact'], 'Guard canaries '+str(n))
        if 'channel' in r['input']: check(r['input']['channel']==3, 'Bound channel '+str(n))
        if 'device' in r['input']: check(r['input']['device']==1, 'Bound device '+str(n))
    check(returns[0]['input']=={'name_present':False,'device_output_present':True} and returns[0]['output']=={'device':1}, 'Open null name and returned device')
    check({k:returns[2]['input'][k] for k in ['protocol','flags','baud']}==contract['connect'] and returns[2]['output']=={'channel':3}, 'Exact connection arguments and channel')
    for n,v in enumerate(contract['set_config_order'],3): config(returns[n],[v])
    config(returns[8],contract['set_config_order'],1)
    check(all(x['value']==0xd15ea5ed for x in returns[8]['input']['config']['owned_buffer_entries']), 'GET values were sentinel initialized')
    def filt(n, kernel):
        r=returns[n]; i,o=r['input'],r['output']; want=contract['kernel_filter' if kernel else 'filter']
        check(i['filter_type']==1 and i['mask_present'] and i['pattern_present'] and i['filter_output_present'] and i['flow_present']==want['flow_pointer_nonnull'], 'Filter pointer/type contract '+str(n))
        for k,h in [('mask',want['mask_hex']),('pattern',want['pattern_hex']),('flow',want['flow_control_hex'])]:
            check(i[k]==o[k], 'Unmutated filter argument '+str(n)+k)
            if h is None: check(i[k] is None, 'Null BEEF flow')
            else:
                b=message(i[k]);check(b.hex()==h and i[k]['rx_status']==i[k]['timestamp']==i[k]['extra_data_index']==0, 'Fixed filter bytes '+str(n)+k)
        check(o['filter_id']==(1 if kernel else 0), 'Observed filter ID '+str(n))
    filt(9,False); filt(87,True)
    expected=['PassThruOpen','PassThruReadVersion','PassThruConnect']+['PassThruIoctl']*6+['PassThruStartMsgFilter']
    for stage in range(24):
        if stage==5: expected+=['MonotonicMinimumWait']
        if stage==6: expected+=['MonotonicMinimumWait']+['PassThruIoctl']*3+['MonotonicMinimumWait']
        if stage==23: expected+=['PassThruStopMsgFilter','PassThruIoctl','PassThruStartMsgFilter']
        expected+=['PassThruWriteMsgs','PassThruReadMsgs','PassThruReadMsgs']
    expected+=['PassThruStopMsgFilter','PassThruDisconnect','PassThruClose']
    check([r['function'] for r in returns]==expected, 'Complete exact call schedule; no extra operations or retries')
    tx=[r for r in returns if r['function']=='PassThruWriteMsgs']; rx=[]; exchanges=[]
    for stage,w in enumerate(tx):
        b=message(w['input']['message']);check(w['output']['message']==w['input']['message'] and w['output']['count']==w['input']['input_count']==w['input']['message_capacity']==1 and w['input']['count_pointer_present'] and w['input']['timeout_ms']==1000, 'Write count, arguments and preserved message '+str(stage))
        check(w['input']['message']['rx_status']==w['input']['message']['timestamp']==w['input']['message']['extra_data_index']==0 and b[-1]==sum(b[:-1])%256, 'Write framing/checksum '+str(stage))
        if stage!=4: check(b.hex()==contract['ordered_requests'][stage]['wire_hex'], 'Exact fixed request '+str(stage))
        reads=returns[w['sequence']+1:w['sequence']+3]
        for rr in reads:
            m=rr['output']['message']; rb=message(m)
            check(rr['output']['count']==rr['input']['input_count']==rr['input']['message_capacity']==1 and rr['input']['timeout_ms']==1000 and rr['input']['count_pointer_present'], 'Receive API bounds '+str(rr['sequence']))
            check(rr['input']['message']['data_size']==0 and rr['input']['message']['protocol']==0, 'Zeroed receive record '+str(rr['sequence']))
        som,reply=reads[0]['output']['message'],reads[1]['output']['message']; rb=bytes.fromhex(reply['data_hex'])
        check(som['rx_status']==2 and som['data_size']==som['extra_data_index']==0 and reply['rx_status']==0 and reply['extra_data_index']==len(rb), 'Exact empty SOM then full data '+str(stage))
        check(som['timestamp']<=reply['timestamp'] and rb[-1]==sum(rb[:-1])%256, 'Provider timestamp and RX checksum '+str(stage))
        if stage==23: check(rb[:4]==bytes.fromhex('beef000f') and len(rb)==20, 'BEEF length/header20')
        else: check(rb[:3]==bytes.fromhex('80f010') and len(rb)==rb[3]+5, 'OEM reply framing '+str(stage))
        if stage!=3: check(reply['data_hex']==contract['ordered_requests'][stage]['expected_reply_hex'], 'Exact response '+str(stage))
        else: check(rb[:6]==bytes.fromhex('80f010066701') and len(rb)==11, 'Fresh four-byte seed shape')
        elapsed=(reads[-1]['qpc_after']-reads[0]['qpc_before'])*1000/reads[0]['qpc_frequency']
        check(elapsed<2000, 'Complete receive window within deadline '+str(stage))
        rx.append(reply['data_hex']);exchanges.append({'stage':stage,'write_sequence':w['sequence'],'request_hex':b.hex(),'reply_hex':reply['data_hex'],'receive_window_ms':elapsed,'provider_records':[x['output']['message'] for x in reads]})
    seed=bytes.fromhex(rx[3])[6:10]; derived=key(seed); kw=bytes.fromhex(tx[4]['input']['message']['data_hex'])
    check(kw[6:10]==derived and kw[:6]==bytes.fromhex('8010f0062702') and len(kw)==11, 'Independently recomputed key equals actual request')
    cipher=b'';chunks=[]
    for n,c in enumerate(manifest['chunks']):
        w=bytes.fromhex(tx[n+7]['input']['message']['data_hex']); payload=w[8:-1];address=0xff000000|int.from_bytes(w[5:8],'big')
        check(w.hex()==c['wire_hex'] and len(w)==c['wire_bytes'] and hashlib.sha256(w).hexdigest()==c['wire_frame_sha256'], 'Manifest full frame '+str(n+1))
        check(len(payload)==c['payload_bytes'] and hashlib.sha256(payload).hexdigest()==c['cipher_payload_sha256'] and address==int(c['target_address'],16), 'Payload address/size/hash '+str(n+1))
        check(address==0xffff3000+len(cipher) and rx[n+7]=='80f0100176f7', 'Contiguous chunk and exact ACK '+str(n+1))
        cipher+=payload;chunks.append(c)
    check(len(chunks)==15 and len(cipher)==1808 and hashlib.sha256(cipher).hexdigest()==contract['cipher_sha256']==manifest['cipher_sha256'], 'Complete fixed cipher1808 and hash')
    check(manifest['expected_uploaded_ram_sha256']==contract['kernel_sha256']==cert['kernel_image_sha256']=='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581', 'Reused cipher-to-kernel evidence binding; no RAM readback claim')
    waits=[r for r in returns if r['function']=='MonotonicMinimumWait']; actual=[]
    for r,ms,reason in zip(waits,[200,100,200],['post_key_ack','post_session_ack','pre_download_declaration']):
        check(r['input']['milliseconds']==r['input']['requested_ms']==r['output']['requested_ms']==ms and r['input']['reason']==reason and r['output']['minimum_satisfied'], 'Wait contract '+str(ms)+reason)
        elapsed=r['api_elapsed_ticks']*1000/r['qpc_frequency'];check(elapsed>=ms,'Actual minimum wait '+str(ms));actual.append(elapsed)
    config(returns[30],[{'parameter':1,'value':15625}]);config(returns[86],[{'parameter':1,'value':62500}])
    for n,ioctl in [(31,7),(32,8)]: check(returns[n]['input']=={'channel':3,'ioctl':ioctl,'input_present':False,'output_present':False} and returns[n]['output']=={}, 'Exact queue clear '+str(ioctl))
    check(returns[85]['input']=={'channel':3,'filter_id':0} and returns[85]['state']['start_acknowledged'], 'OEM filter stopped once only after start ACK')
    check(tx[22]['state']['acknowledged_chunks']==15 and tx[23]['state']['start_acknowledged'] and tx[23]['state']['kernel_filter'] and tx[23]['state']['requested_baud']==62500, 'Start/identity admission state')
    check(returns[91]['input']['filter_id']==1 and returns[92]['input']['channel']==3 and returns[93]['input']['device']==1, 'Cleanup targets owned identities')
    st=terminal['state']
    check(terminal['type']=='probe_terminal' and terminal['physical'] is True and terminal['status']=='PASS_KERNEL_START_IDENTITY_ONLY' and terminal['protocol_complete'] and terminal['cleanup_confirmed'] and terminal['cleanup_error_mask']==0 and not terminal['log_failed'] and terminal['failure']=='', 'Complete terminal PASS')
    check(not st['opened'] and not st['connected'] and not st['filter']['active'] and st['tx_attempts']==24 and st['acknowledged_chunks']==15 and st['start_acknowledged'] and st['identity_validated'], 'Terminal ownership closed and exact counters')
    check(rx==result['validation']['responses'] and actual==result['validation']['waits_ms_actual'] and seed.hex()==result['validation']['seed_hex'] and kw.hex()==result['validation']['key_request'], 'Independent derivations agree with sealed root result')
    check(bytes.fromhex(rx[-1])[5:-1]==b'A2WC511R-RK02\x00', 'Exact ASCII identity and terminal NUL')
    for p in list(pins.values()): check(pin(p['path'])==p, 'Inputs unchanged after audit '+p['path'])
    save(OUT/'GATE_RECEIPTS_OBSERVED.json',receipt);bind(OUT/'GATE_RECEIPTS_OBSERVED.json')
    report={'schema':1,'status':'PASS_INDEPENDENT_PHYSICAL_KERNEL_START_IDENTITY_REVIEW','reviewer':'passive_review','utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope':'Independent read-only audit of the one completed physical session. No native executable, provider, client scanner or qualification suite invoked by reviewer.',
        'session_id':ex['session_id'],'source_pins':list(pins.values()),'checks_passed':len(checks),'checks':checks,'blocking_findings':[],
        'recorded_execution':ex,'physical_invocations_recorded':1,'journal_rows':len(rows),'paired_call_records':94,'j2534_calls':91,'host_wait_calls':3,
        'tx_count':24,'rx_records':48,'fixed_upload_chunks':15,'fixed_cipher_bytes':1808,'cipher_sha256':hashlib.sha256(cipher).hexdigest(),
        'uploaded_plaintext_sha256_bound_by_reused_qualification':contract['kernel_sha256'],'seed_hex':seed.hex(),'independently_derived_key_hex':derived.hex(),
        'start_frame':exchanges[22]['request_hex'],'start_ack':rx[22],'contract_entry':'FFFF3004','identity_request':exchanges[23]['request_hex'],
        'identity_reply':rx[23],'identity_ascii':'A2WC511R-RK02\u0000','identity_receive_window_ms':exchanges[23]['receive_window_ms'],
        'start_receive_window_ms':exchanges[22]['receive_window_ms'],'actual_wait_ms':actual,'cleanup_statuses':[r['status'] for r in returns[-3:]],
        'provider_version':returns[1]['output'],'provider_resource_ids':{'device':1,'channel':3,'oem_filter':0,'kernel_filter':1},'exchanges':exchanges,
        'ROM_read_requests':0,'flash_requests':0,'second_start_requests':0,'programming_retry_requests':0,
        'reviewer_physical_operations':0,'reviewer_provider_loads':0,'reviewer_native_invocations':0,
        'limitations':['Evidence is the hash-bound provider API journal, native status and launcher/process-scan records, not an independent electrical bus or ECU instruction trace.',
          'The fixed upload frames/ACKs and exact kernel identity are observed. Complete plaintext RAM was not read back during this session; cipher-to-image mapping and intended FFFF3004 entry reuse the sealed qualification and instruction evidence.',
          'Baud SET success and returned argument integrity are observed; effective electrical baud was not independently measured.',
          'Exact complete identity ended reception. The journal does not prove absence of separately queued records after that response.',
          'The recorded one-shot session is verified; this audit does not claim to discover unrecorded external actions. Cleanup records contain status/timing/state but no stack-pointer fields; stack equality is verified only for the 91 preceding call records.',
          'Human prelaunch receipts are preserved as an observed snapshot; the mutable operational gate file is deliberately not a stable report dependency.',
          'OEM-return recovery is outside this report and was pending when review was assigned. No bounded ROM work has been started by this reviewer.']}
    save(OUT/'INDEPENDENT_PHYSICAL_REVIEW.json',report)
    print(json.dumps({'status':report['status'],'checks_passed':len(checks),'report':pin(OUT/'INDEPENDENT_PHYSICAL_REVIEW.json')}))
if __name__=='__main__': main()
