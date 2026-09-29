"""Offline installed-host TX/upload/read audit. No application or device APIs."""
import sys
sys.dont_write_bytecode=True
import argparse, hashlib, json, re, runpy, unittest, zlib
from collections import Counter, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUTROOT=ROOT/'reports/local/ecuflash_dynamic/read_audit'
CANDIDATES=ROOT/'reports/local/ecuflash_dynamic/kernel_candidate'
RESOURCE=CANDIDATES/'subarush7058dual_RESOURCE_CANDIDATE.bin'
PLAINTEXT=CANDIDATES/'subarush7058dual_DECRYPTED_CANDIDATE.bin'
RESOURCE_SHA='54378e8161c0029f3639c9761c197932e6d4300155a1dc26ff11e9c0eff9bfab'
PLAIN_SHA='b0989858ec59c7c281c1368d956a7187b353454683b248be5f1739c86835b082'
INSTALLED_SHA='5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115'
CRYPTO=ROOT/'work/M07_reference/subaru-ecu-flashing/encryption.py'
CRYPTO_SHA='bef8ea198f8c5064ad2747493d1e6e20a15ba0a5641629fe78f5feb586a8af01'
COMMAND04_EVIDENCE=CANDIDATES/'read_paths_CANDIDATE/CLEANUP_CANDIDATE.json'
COMMAND04_SHA='ed2679221cf639420e10e7900d7df97bfc417f2a55845e9eb81ee802efcd1447'
FLASH_SIZE=0x100000
LOAD=0xFFFF3000
CONTROL_NAMES={0x20:'FLASH_ENABLE',0x21:'FLASH_DISABLE',0x22:'FLASH_BUFFER_WRITE',
               0x23:'FLASH_BUFFER_VALIDATE_TEST_WRITE',0x24:'FLASH_COMMIT',0x25:'FLASH_ERASE'}
SSM_NAMES={0xBF:'OEM_IDENTITY',0x81:'COMMUNICATION_START',0x83:'TIMING_QUERY',
           0x27:'SECURITY',0x10:'SESSION',0x34:'RAM_DOWNLOAD_DECLARATION',
           0x36:'RAM_TRANSFER',0x31:'ROUTINE_ENTRY',0xA8:'OEM_MEMORY_READ'}
NIBBLES=(5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8)

def sha(data):return hashlib.sha256(data).hexdigest()
def stable(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def strict_hex(text):
    if type(text) is not str or len(text)%2 or not text or not re.fullmatch('[0-9A-Fa-f]+',text):raise ValueError('noncanonical complete hex')
    return bytes.fromhex(text)

def parse_wire(raw,response=False):
    if raw[:2]==b'\xBE\xEF':
        if len(raw)<6 or len(raw)!=int.from_bytes(raw[2:4],'big')+5:raise ValueError('BEEF length')
        payload=raw[4:-1];kind='BEEF'
    elif raw[:1]==b'\x80':
        header=b'\x80\xF0\x10' if response else b'\x80\x10\xF0'
        if len(raw)<6 or raw[:3]!=header or len(raw)!=raw[3]+5:raise ValueError('SSM direction/length')
        payload=raw[4:-1];kind='SSM'
    else:raise ValueError('unknown raw framing')
    if not payload or sum(raw[:-1])&255!=raw[-1]:raise ValueError('wire checksum/payload')
    return kind,payload

def transform(raw,keys):
    if len(raw)%4:raise ValueError('ciphertext is not 32-bit aligned')
    result=bytearray()
    for offset in range(0,len(raw),4):
        high=int.from_bytes(raw[offset:offset+2],'big');low=int.from_bytes(raw[offset+2:offset+4],'big')
        for key in keys:
            expanded=(low^key)*0x10001
            substituted=0
            for shift in (0,4,8,12):substituted|=NIBBLES[(expanded>>shift)&31]<<shift
            rotated=((substituted>>3)|(substituted<<13))&65535
            high,low=low,high^rotated
        result.extend(low.to_bytes(2,'big')+high.to_bytes(2,'big'))
    return bytes(result)

def decrypt(raw):return transform(raw,(0x6E86,0xF513,0xCE22,0x7856))
def encrypt(raw):return transform(raw,(0x7856,0xCE22,0xF513,0x6E86))

def ranges(mask,value=1):
    out=[];start=None
    for i,item in enumerate(mask):
        if item==value and start is None:start=i
        elif item!=value and start is not None:out.append([start,i]);start=None
    if start is not None:out.append([start,len(mask)])
    return out

def checked_inputs():
    pins=((RESOURCE,RESOURCE_SHA),(PLAINTEXT,PLAIN_SHA),(CRYPTO,CRYPTO_SHA),(COMMAND04_EVIDENCE,COMMAND04_SHA))
    for path,digest in pins:
        if sha(path.read_bytes())!=digest:raise ValueError('Pinned analytical input changed: '+str(path))
    raw=RESOURCE.read_bytes();plain=PLAINTEXT.read_bytes()
    command04=json.loads(COMMAND04_EVIDENCE.read_text())
    if command04['plaintext_sha256']!=PLAIN_SHA or command04['command04_exact_payload']!='840258' or command04['command04_exit_reset']!='DISPROVEN_HANDLER_ONLY_RETURNS_CONSTANT':raise ValueError('Command04 evidence contract mismatch')
    foreign=runpy.run_path(str(CRYPTO))
    independent=bytes(foreign['decrypt_0x36'](list(raw)))
    if decrypt(raw)!=plain or independent!=plain or encrypt(plain)!=raw:raise ValueError('Independent crypto/resource disagreement')
    table={}
    for p in range(0x1150,len(plain)-7,8):
        record=plain[p:p+8];command=record[0]
        if not command:break
        table[command]={'record_address':LOAD+p,'record_hex':record.hex(),'required_length':record[1],
                        'handler':int.from_bytes(record[4:8],'big')}
    contracts={}
    for service,name in ((5,'READ_VERSION_CONTRACT.json'),(1,'SEED_KEY_CONTRACT.json')):
        path=ROOT/'reports/local/ecuflash_dynamic/api_boundary'/name
        if path.exists():
            document=json.loads(path.read_text())
            valid=document.get('image_sha256')=='1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18'
            valid=valid and (document.get('app_service',{}).get('input_header_hex')=='02000000050000000100' if service==5 else document.get('minimal_well_formed_success',{}).get('output_length')==4)
            if valid:contracts[service]={'path':str(path),'sha256':sha(path.read_bytes())}
    return {'resource':raw,'plain':plain,'foreign':foreign,'command_table':table,'provider_contracts':contracts,
            'pins':{str(path):digest for path,digest in pins}}

def provider_service(q,r,inputs):
    """These calls request host-provider services, not ECU wire frames."""
    service=q.get('service_id');data=q.get('input_bytes');contract=inputs['provider_contracts'].get(service)
    row={'classification':'ADDITIONAL_TRANSPORT_COMMAND_REQUIRES_REVIEW','request':q,'response_status':r.get('status')}
    if q.get('function')!='PassThruIoctl' or q.get('ioctl')!=0x70000 or q.get('id')!=1 or contract is None:return row
    if type(data) is not list or any(type(v) is not int or not 0<=v<=255 for v in data):return row
    valid_shape=data==[1,0] if service==5 else len(data)==5 and data[0]==1
    if not valid_shape:return row
    row.update({'classification':'HOST_PROVIDER_DEVICE_LABEL' if service==5 else 'HOST_PROVIDER_SEED_KEY',
                'is_ECU_wire_TX':False,'contract':contract,'response_provenance':r.get('provenance')})
    if r.get('status')==0:
        output=r.get('output_bytes')
        valid=type(output) is list and all(type(v) is int and 0<=v<=255 for v in output)
        valid=valid and len(output)<=q.get('output_capacity',0)
        if service==1:
            expected=bytes(inputs['foreign']['generate_0x27_auth_key'](list(data[1:])))
            valid=valid and bytes(output)==expected
            row['independent_expected_key_hex']=expected.hex()
        else:valid=valid and 0<len(output)<=256
        row['response_contract_match']=valid
        if not valid:row['classification']='HOST_PROVIDER_SERVICE_RESPONSE_MISMATCH'
    else:row['response_contract_match']=False;row['rejected_service_visible']=True
    return row

def installed_provenance(run,events):
    result={'status':'UNQUALIFIED','reason':'No installed-host metadata','physical':False}
    try:
        session=json.loads((run/'session_private.json').read_text())
        attach=json.loads((run/'API_ATTACH.json').read_text())
        target=Path(session['target']);digest=sha(target.read_bytes())
        pids={e['request'].get('pid') for e in events if e.get('request',{}).get('function')=='PassThruWriteMsgs'}
        valid=(not session.get('probe',True) and digest==INSTALLED_SHA and attach.get('status')=='PASS_INSTRUMENTATION_INSTALLED'
               and session.get('pid')==attach.get('pid') and pids=={session.get('pid')})
        result={'status':'PINNED_INSTALLED_HOST_CAPTURE' if valid else 'UNQUALIFIED','target':str(target),
                'target_sha256':digest,'pid':session.get('pid'),'TX_pids':sorted(pids,key=str),
                'session_metadata_sha256':sha((run/'session_private.json').read_bytes()),
                'api_attach_sha256':sha((run/'API_ATTACH.json').read_bytes()),
                'scope':'Local guarded-host metadata association, not a signed attestation or physical execution proof','physical':False}
    except (OSError,ValueError,KeyError,TypeError) as e:result['reason']=str(e)
    return result

def audit(events,inputs,expected=None,saved=None):
    """Analyze in-memory evidence. Returns report plus complete decoded upload, if any."""
    if expected is not None and len(expected)!=FLASH_SIZE:raise ValueError('Expected flash must be exactly1MiB')
    if saved is not None and len(saved)!=FLASH_SIZE:raise ValueError('Saved raw flash must be exactly1MiB; no SRF extraction or padding')
    issues=[];tx=[];norm=[];accepted_norm=[];reads=[];crc=[];control=[];unknown=[];upload=[];starts=[]
    requested=bytearray(FLASH_SIZE);received=bytearray(FLASH_SIZE);received_data=bytearray(FLASH_SIZE)
    pending=deque();crc_pending=deque();crc_replies=[];rx_records=[];rx_echoes=0;checksum_failures=[];non_write=[]
    for position,event in enumerate(events):
        if event.get('sequence')!=position:issues.append({'sequence':position,'issue':'Noncontiguous/duplicate trace sequence'})
        if event.get('physical') is not False:issues.append({'sequence':position,'issue':'Trace lacks explicit virtual provenance'})
        q=event.get('request',{});r=event.get('response',{});fn=q.get('function')
        if fn=='PassThruWriteMsgs':
            messages=q.get('messages',[]);count=r.get('count',0)
            if type(count) is not int or not 0<=count<=len(messages):issues.append({'sequence':position,'issue':'Invalid accepted count'});count=0
            for index,msg in enumerate(messages):
                wire=msg.get('data_hex');record={'tx_index':len(tx),'sequence':position,'message_index':index,
                    'protocol':msg.get('protocol'),'tx_flags':msg.get('tx_flags'),'wire_hex':wire,
                    'provider_accepted':index<count,'provider_status':r.get('status'),'classification':'MALFORMED'}
                normalized={k:record[k] for k in ('protocol','tx_flags','wire_hex')};norm.append(normalized)
                if record['provider_accepted']:accepted_norm.append(normalized)
                tx.append(record)
                try:
                    raw=strict_hex(wire)
                    normalized['wire_hex']=raw.hex()
                    # Do not hide attempted flash control behind a bad checksum.
                    apparent=raw[4] if len(raw)>4 and raw[:2]==b'\xBE\xEF' else None
                    if apparent in CONTROL_NAMES:control.append({'tx_index':record['tx_index'],'command':apparent,'name':CONTROL_NAMES[apparent],
                        'candidate_object':inputs['command_table'].get(apparent),'payload_hex':raw[4:-1].hex(),'provider_accepted':record['provider_accepted']})
                    kind,payload=parse_wire(raw)
                    if msg.get('protocol')!=3:raise ValueError('unsupported protocol')
                    command=payload[0];record.update({'framing':kind,'command':command,'payload_hex':payload.hex(),'wire_checksum_valid':True})
                    if kind=='SSM':
                        record['classification']=SSM_NAMES.get(command,'UNKNOWN_SSM')
                        shapes={0xBF:payload==b'\xBF',0x81:payload==b'\x81',0x83:payload==b'\x83\x00',
                                0x27:payload==b'\x27\x01' or len(payload)==6 and payload[:2]==b'\x27\x02',
                                0x10:payload==bytes.fromhex('108502'),0x31:payload==bytes.fromhex('310101'),
                                0xA8:5<=len(payload)<=251 and payload[1]==0 and (len(payload)-2)%3==0}
                        if command in shapes and not shapes[command]:record['classification']='UNKNOWN_SSM'
                        if command in (0x34,0x36):upload.append(record)
                        if command==0x31:starts.append(record)
                        if command in (0xB0,0xB8,0x11,0x2F,0x30):record['classification']='FORBIDDEN_OEM_WRITE_OR_CONTROL';control.append(record.copy())
                        if record['classification']=='UNKNOWN_SSM':unknown.append(record['tx_index'])
                    else:
                        record['candidate_object']=inputs['command_table'].get(command)
                        record['classification']=CONTROL_NAMES.get(command,{1:'KERNEL_VERSION',2:'ROM_CRC',3:'ROM_READ',4:'CONSTANT_0258_QUERY_NOT_RESET',5:'COMM_CAPACITY',6:'FLASH_BUFFER_CAPACITY'}.get(command,'UNKNOWN_BEEF'))
                        if record['classification'] in ('UNKNOWN_BEEF','UNQUALIFIED_QUERY'):unknown.append(record['tx_index'])
                        if command in (1,4,5,6) and len(payload)!=1:raise ValueError('Query has unexpected arguments')
                        if command==4:record['semantic_evidence']={'path':str(COMMAND04_EVIDENCE),'sha256':COMMAND04_SHA,'expected_payload':'840258','does_reset_or_exit':False}
                        if command in (2,3):
                            required=9 if command==2 else 7
                            if len(payload)!=required:raise ValueError('read/CRC payload length')
                            address=int.from_bytes(payload[1:5],'big');length=int.from_bytes(payload[5:],'big')
                            if not 0<length<=FLASH_SIZE or address+length>FLASH_SIZE:raise ValueError('read/CRC outside1MiB')
                            if command==3 and length>514:raise ValueError('read exceeds named candidate handler maximum514')
                            record.update({'address':address,'length':length})
                            if command==2:
                                crc.append(record.copy())
                                if record['provider_accepted']:
                                    if crc_pending:
                                        issues.append({'sequence':position,'issue':'More than one outstanding CRC; address association ambiguous'})
                                        for earlier in crc_pending:earlier['association_ambiguous']=True
                                        record['association_ambiguous']=True
                                    crc_pending.append(record)
                            else:
                                reads.append(record.copy())
                                if record['provider_accepted']:
                                    requested[address:address+length]=b'\1'*length
                                    if pending:
                                        issues.append({'sequence':position,'issue':'More than one outstanding read; response address association ambiguous'})
                                        for earlier in pending:earlier['association_ambiguous']=True
                                        record['association_ambiguous']=True
                                    pending.append(record)
                except (ValueError,TypeError,KeyError) as e:
                    record['parse_error']=str(e);record['classification']='MALFORMED'
                    checksum_failures.append(record['tx_index']);unknown.append(record['tx_index'])
        elif fn=='PassThruReadMsgs':
            for index,msg in enumerate(r.get('messages',[])):
                if msg.get('rx_status',0)&1:rx_echoes+=1;continue
                try:
                    raw=strict_hex(msg['data_hex']);kind,payload=parse_wire(raw,response=True)
                    if kind!='BEEF' or payload[0] not in (0x42,0x82,0x43,0x83):continue
                    if payload[0] in (0x42,0x82):
                        if len(payload)!=5 or not crc_pending:raise ValueError('Malformed or unsolicited CRC response')
                        query=crc_pending.popleft()
                        if query.get('association_ambiguous'):raise ValueError('Ambiguous CRC response address')
                        if msg.get('protocol')!=3 or r.get('status') not in (0,9):raise ValueError('CRC response transport contract')
                        address=query['address'];length=query['length'];value=int.from_bytes(payload[1:],'big')
                        ff=zlib.crc32(b'\xFF'*length);zero=zlib.crc32(bytes(length))
                        item={'sequence':position,'request_tx_index':query['tx_index'],'wire_hex':raw.hex(),
                              'address':address,'length':length,'crc32':f'{value:08x}',
                              'equals_all_ff_crc32':value==ff,'equals_all_00_crc32':value==zero,
                              'provenance':msg.get('provenance'),'response_proves_bytes':False}
                        if expected is not None:
                            part=expected[address:address+length]
                            item.update({'expected_crc32_match':zlib.crc32(part)==value,'expected_all_ff':part==b'\xFF'*length,
                                         'expected_all_00':part==bytes(length)})
                            if zlib.crc32(part)!=value:issues.append({'sequence':position,'issue':'CRC reply differs from supplied expected backing bytes'})
                        item['qualified_association']=payload[0]==0x82 and bool(msg.get('provenance',{}).get('not_vehicle_telemetry'))
                        if payload[0]!=0x82:issues.append({'sequence':position,'issue':'CRC response differs from candidate opcode82'})
                        if not msg.get('provenance',{}).get('not_vehicle_telemetry'):issues.append({'sequence':position,'issue':'Missing synthetic CRC provenance'})
                        crc_replies.append(item);continue
                    rx={'sequence':position,'message_index':index,'wire_hex':raw.hex(),'provenance':msg.get('provenance'),
                        'provider_status':r.get('status'),'response_opcode':payload[0]};rx_records.append(rx)
                    if msg.get('protocol')!=3:raise ValueError('RX protocol mismatch')
                    if r.get('status') not in (0,9):raise ValueError('RX bytes accompany unexpected provider failure status')
                    if not pending:raise ValueError('Unsolicited read reply')
                    request=pending.popleft();rx['request_tx_index']=request['tx_index']
                    if request.get('association_ambiguous'):raise ValueError('Ambiguous outstanding read; no qualified address association')
                    data=payload[1:];address=request['address'];length=request['length']
                    if len(data)!=length:raise ValueError('Read response length does not match requested bytes')
                    if payload[0]!=0x83:raise ValueError('Response opcode differs from named DUAL1.07 candidate83')
                    if not msg.get('provenance',{}).get('not_vehicle_telemetry'):raise ValueError('Missing synthetic response provenance')
                    for i,b in enumerate(data,address):
                        if received[i] and received_data[i]!=b:issues.append({'sequence':position,'issue':'Conflicting returned byte','address':i})
                        received[i]=1;received_data[i]=b
                    rx.update({'address':address,'length':length,'data_sha256':sha(data),'expected_match':None if expected is None else data==expected[address:address+length]})
                except (ValueError,TypeError,KeyError) as e:issues.append({'sequence':position,'issue':'RX: '+str(e)})
        elif fn in ('PassThruStartPeriodicMsg','PassThruIoctl') and any(k in q for k in ('message','init_message','input_bytes')):
            non_write.append({'sequence':position,**provider_service(q,r,inputs)})

    kernel={'status':'INCOMPLETE_NO_KERNEL_EMITTED','captured_transfer_frames':len(upload),'start_commands':starts,
            'frame_records':upload,'resource_ciphertext_sha256':RESOURCE_SHA,'candidate_plaintext_sha256':PLAIN_SHA}
    plain=None
    try:
        if not upload:raise ValueError('No34/36 upload captured')
        if not all(x['provider_accepted'] for x in upload):raise ValueError('Upload contains unaccepted frame')
        declarations=sum(x['command']==0x34 for x in upload)
        if upload[0]['command']!=0x34 or declarations not in (1,2):raise ValueError('Missing/third download declaration')
        if declarations==2 and (len(upload)<2 or upload[1]['command']!=0x34 or upload[1]['payload_hex']!=upload[0]['payload_hex']):raise ValueError('Differing or late repeated declaration')
        kernel['declaration_count']=declarations
        kernel['declaration_contract']='Installed caller RVA9C154/9C164 intentionally repeats the identical34 before any36. Both raw frames retained; third/differing/late declarations rejected.'
        declaration=bytes.fromhex(upload[0]['payload_hex'])
        if len(declaration)!=8 or declaration[4]!=4:raise ValueError('Unsupported34 declaration layout')
        address=0xFF000000|int.from_bytes(declaration[1:4],'big');length=int.from_bytes(declaration[5:8],'big')
        kernel.update({'declared_address':address,'declared_length':length})
        if address!=LOAD or length!=len(inputs['resource']):raise ValueError('Declaration differs from named resource span')
        ciphertext=bytearray();blocks=[]
        for record in upload[declarations:]:
            payload=bytes.fromhex(record['payload_hex']);cursor=address+len(ciphertext)
            if payload[0]!=0x36 or len(payload)<8:raise ValueError('Unsupported36 transfer shape')
            actual=0xFF000000|int.from_bytes(payload[1:4],'big');data=payload[4:]
            if actual!=cursor or len(data)%4 or len(ciphertext)+len(data)>length:raise ValueError('Upload gap/duplicate/overlap/alignment/overflow')
            blocks.append({'tx_index':record['tx_index'],'address':actual,'length':len(data),'ciphertext_sha256':sha(data)})
            ciphertext.extend(data)
        kernel['blocks']=blocks;kernel['captured_ciphertext_bytes']=len(ciphertext)
        if len(ciphertext)!=length:raise ValueError('Incomplete declared upload')
        independent=bytes(inputs['foreign']['decrypt_0x36'](list(ciphertext)))
        decoded=decrypt(ciphertext)
        if independent!=decoded or encrypt(decoded)!=ciphertext:raise ValueError('Independent decryption/roundtrip mismatch')
        kernel.update({'ciphertext_sha256':sha(ciphertext),'plaintext_sha256':sha(decoded),
                       'independent_crypto_match':True,'resource_ciphertext_exact_match':bytes(ciphertext)==inputs['resource'],
                       'candidate_plaintext_exact_match':decoded==inputs['plain'],
                       'wire_checksum_validation':'ALL_TRANSFER_FRAMES_PASS_ADD8',
                       'internal_transfer_checksum':'UNQUALIFIED; not inferred from wire add8 or roundtrip',
                       'sum_be16_mod65536':sum(int.from_bytes(decoded[i:i+2],'big') for i in range(0,len(decoded),2))&65535,
                       'crc32_plaintext':f'{zlib.crc32(decoded):08x}',
                       'captured_start_after_upload':any(s['provider_accepted'] and s['payload_hex']=='310101' and s['tx_index']>upload[-1]['tx_index'] for s in starts)})
        if ciphertext!=inputs['resource'] or decoded!=inputs['plain']:raise ValueError('Captured upload does not match named Subaru DUAL resource')
        kernel['status']='COMPLETE_CAPTURE_MATCHES_NAMED_RESOURCE';plain=decoded
    except (ValueError,TypeError,KeyError) as e:kernel['reason']=str(e)

    expected_mismatch=bytearray(FLASH_SIZE);saved_mismatch=bytearray(FLASH_SIZE);saved_unreturned=bytearray(FLASH_SIZE);saved_expected_mismatch=bytearray(FLASH_SIZE)
    crc_fill=bytearray(FLASH_SIZE);collision_ranges=[]
    for item in crc_replies:
        if not item['qualified_association'] or not item.get('expected_crc32_match',True):continue
        address=item['address'];length=item['length']
        fill=1 if item['equals_all_ff_crc32'] else 2 if item['equals_all_00_crc32'] else 0
        if fill:crc_fill[address:address+length]=bytes((fill,))*length
        if expected is not None and (fill==1 and not item['expected_all_ff'] or fill==2 and not item['expected_all_00']):
            collision_ranges.append({'start':address,'end':address+length,'CRC_matches_fill':'FF' if fill==1 else '00',
                                     'expected_differs_from_fill':True,'request_tx_index':item['request_tx_index']})
    saved_provenance=[]
    for i in range(FLASH_SIZE):
        if expected is not None and received[i] and received_data[i]!=expected[i]:expected_mismatch[i]=1
        if saved is not None:
            if received[i] and saved[i]!=received_data[i]:saved_mismatch[i]=1
            if not received[i]:saved_unreturned[i]=1
            if expected is not None and saved[i]!=expected[i]:saved_expected_mismatch[i]=1
            label=('DIFFERS_FROM_RETURNED_SYNTHETIC_BYTES' if saved_mismatch[i] else 'MATCHES_RETURNED_SYNTHETIC_BYTES') if received[i] else 'REQUESTED_WITHOUT_QUALIFIED_REPLY' if requested[i] else 'NEVER_REQUESTED'
            if not received[i] and not requested[i] and (crc_fill[i]==1 and saved[i]==255 or crc_fill[i]==2 and saved[i]==0):
                label='CRC_MATCH_ONLY_'+('FF' if crc_fill[i]==1 else '00')+'_NO_READ_PAYLOAD'
            if saved_provenance and saved_provenance[-1]['classification']==label:saved_provenance[-1]['end']=i+1
            else:saved_provenance.append({'start':i,'end':i+1,'classification':label})
    coverage={'requested_bytes':sum(requested),'returned_bytes':sum(received),'requested_ranges':ranges(requested),
              'returned_ranges':ranges(received),'no_requested_read_ranges':ranges(requested,0),'no_returned_bytes_ranges':ranges(received,0),
              'read_requests':reads,'CRC_requests':crc,'CRC_replies':crc_replies,'CRC_proves_returned_bytes':False,
              'CRC_fill_collision_ranges':collision_ranges,'unanswered_CRC_requests':[x['tx_index'] for x in crc_pending],'RX_read_replies':rx_records,
              'RX_echoes_excluded':rx_echoes,'unanswered_read_requests':[x['tx_index'] for x in pending],
              'expected_image_sha256':None if expected is None else sha(expected),
              'returned_vs_expected_mismatch_bytes':sum(expected_mismatch),'returned_vs_expected_mismatch_ranges':ranges(expected_mismatch),
              'saved_image_sha256':None if saved is None else sha(saved),'saved_vs_returned_mismatch_bytes':sum(saved_mismatch),
              'saved_vs_returned_mismatch_ranges':ranges(saved_mismatch),'saved_without_returned_provenance_ranges':ranges(saved_unreturned) if saved is not None else None,
              'saved_equals_expected':None if saved is None or expected is None else saved==expected,
              'saved_vs_expected_mismatch_bytes':None if saved is None or expected is None else sum(saved_expected_mismatch),
              'saved_vs_expected_mismatch_ranges':None if saved is None or expected is None else ranges(saved_expected_mismatch),
              'saved_byte_provenance_ranges':saved_provenance if saved is not None else None,
              'full_saved_bytes_from_received_payloads':saved is not None and sum(received)==FLASH_SIZE and not any(saved_mismatch)}
    gates={'COMPLETE_CAPTURED_UPLOAD':kernel['status']=='COMPLETE_CAPTURE_MATCHES_NAMED_RESOURCE',
           'EXPLICIT_KERNEL_START_CAPTURED':kernel.get('captured_start_after_upload',False),
           'NO_CAPTURED_FLASH_CONTROL':not control,'NO_UNKNOWN_OR_MALFORMED_TX':not unknown and all(x['classification'].startswith('HOST_PROVIDER_') and x['classification']!='HOST_PROVIDER_SERVICE_RESPONSE_MISMATCH' for x in non_write),
           'FULL_1MIB_RESPONSE_BYTES':sum(received)==FLASH_SIZE and not pending,
           'SAVED_IMAGE_MATCHES_RECEIVED_BYTES':coverage['full_saved_bytes_from_received_payloads'],
           'EXPECTED_IMAGE_MATCHES_RECEIVED_BYTES':expected is not None and sum(received)==FLASH_SIZE and not any(expected_mismatch),
           'TRACE_ASSOCIATION':not issues}
    return {'schema':1,'classification':'OFFLINE_GUARDED_HOST_CAPTURE_AUDIT_NOT_PHYSICAL_PROOF',
            'status':'PASS_CAPTURE_AND_SAVED_COVERAGE' if all(gates.values()) else 'INCOMPLETE_OR_FAIL',
            'calls':len(events),'TX_count':len(tx),'normalized_TX_sha256':sha(stable(norm)),
            'normalized_accepted_TX_sha256':sha(stable(accepted_norm)),
            'normalization':'Ordered protocol,TX flags,exactwirehex only. Excludes clocks,PID,thread,pointers and uninitialized TX timestamp/RxStatus/ExtraDataIndex.',
            'gates':gates,'issues':issues,'TX_classification':tx,'forbidden_control_TX':control,'unknown_TX_indices':unknown,
            'additional_transport_commands':non_write,'kernel':kernel,'coverage':coverage,
            'physical':False,'kernel_execution_proven':False,'OEM_restoration_proven':False,
            'universal_exact_acquisition_proven':False},plain

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path);parser.add_argument('--out',type=Path)
    parser.add_argument('--expected',type=Path);parser.add_argument('--saved',type=Path)
    parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    inputs=checked_inputs()
    if args.self_test:return selftest(inputs)
    if args.run is None:parser.error('--run is required unless --self-test')
    run=args.run.resolve();output=(args.out or OUTROOT/run.name).resolve()
    if not output.is_relative_to(OUTROOT.resolve()):raise ValueError('Output must remain under read_audit')
    path=run/'j2534.jsonl';raw=path.read_bytes()
    if not raw.endswith(b'\n'):raise ValueError('Incomplete final JSONL record; audit a complete trace snapshot')
    events=[json.loads(line) for line in raw.splitlines()]
    expected=None if args.expected is None else args.expected.read_bytes()
    saved=None if args.saved is None else args.saved.read_bytes()
    report,plain=audit(events,inputs,expected,saved)
    report['inputs']={'trace':{'path':str(path),'sha256':sha(raw),'bytes':len(raw)},'analysis_pins':inputs['pins'],'provider_contracts':inputs['provider_contracts']}
    model_inputs=run/'MODEL_INPUTS.json'
    if model_inputs.exists():report['inputs']['MODEL_INPUTS']={'path':str(model_inputs),'sha256':sha(model_inputs.read_bytes())}
    for name,path in (('expected',args.expected),('saved',args.saved)):
        if path is not None:report['inputs'][name]={'path':str(path.resolve()),'sha256':sha(path.read_bytes())}
    provenance=installed_provenance(run,events);report['installed_host_provenance']=provenance
    report['gates']['PINNED_INSTALLED_HOST_CAPTURE']=provenance['status']=='PINNED_INSTALLED_HOST_CAPTURE'
    report['status']='PASS_CAPTURE_AND_SAVED_COVERAGE' if all(report['gates'].values()) else 'INCOMPLETE_OR_FAIL'
    report['kernel']['extracted_artifact']=None
    output.mkdir(parents=True,exist_ok=True)
    if plain is not None and provenance['status']=='PINNED_INSTALLED_HOST_CAPTURE' and report['gates']['TRACE_ASSOCIATION']:
        artifact=output/'DUAL1.07_EXTRACTED_FROM_INSTALLED_ECUFLASH.bin'
        if artifact.exists():
            if artifact.read_bytes()!=plain:raise ValueError('Refuse to replace differing extracted kernel')
        else:
            with artifact.open('xb') as stream:stream.write(plain)
        report['kernel']['extracted_artifact']={'path':str(artifact),'sha256':sha(artifact.read_bytes()),'bytes':len(plain)}
    (output/'READ_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    normalized=[]
    for x in report['TX_classification']:
        item={k:x[k] for k in ('protocol','tx_flags','wire_hex')}
        try:item['wire_hex']=strict_hex(item['wire_hex']).hex()
        except (ValueError,TypeError):pass
        normalized.append(item)
    canonical=stable(normalized)
    if sha(canonical)!=report['normalized_TX_sha256']:raise AssertionError('Normalized artifact/hash disagreement')
    (output/'NORMALIZED_TX.json').write_bytes(canonical)
    print(json.dumps({'report':str(output/'READ_AUDIT.json'),'status':report['status'],'TX':report['TX_count'],
                      'kernel':report['kernel']['status'],'extracted':report['kernel']['extracted_artifact'],
                      'returned_bytes':report['coverage']['returned_bytes'],'gates':report['gates']}))

def selftest(inputs):
    """Synthetic fixtures test the auditor, never qualify a captured kernel."""
    def packet(payload,ssm=False,response=False):
        h=bytes((0x80,0xF0,0x10,len(payload))) if response and ssm else bytes((0x80,0x10,0xF0,len(payload))) if ssm else b'\xBE\xEF'+len(payload).to_bytes(2,'big')
        raw=h+payload;return raw+bytes((sum(raw)&255,))
    def tx(raw):return {'request':{'function':'PassThruWriteMsgs','messages':[{'protocol':3,'tx_flags':0,'data_hex':raw.hex()}]},'response':{'status':0,'count':1},'physical':False}
    def rx(data):return {'request':{'function':'PassThruReadMsgs'},'response':{'status':0,'messages':[{'protocol':3,'rx_status':0,'data_hex':packet(b'\x83'+data).hex(),'provenance':{'not_vehicle_telemetry':True}}]},'physical':False}
    def upload():
        rows=[tx(packet(bytes.fromhex('34ff300004001234'),True))]
        for offset in range(0,len(inputs['resource']),128):rows.append(tx(packet(b'\x36'+((LOAD+offset)&0xFFFFFF).to_bytes(3,'big')+inputs['resource'][offset:offset+128],True)))
        rows.append(tx(packet(bytes.fromhex('310101'),True)));return rows
    def run(rows,**kw):
        for i,e in enumerate(rows):e['sequence']=i
        return audit(rows,inputs,**kw)
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    rows=upload();report,plain=run(rows)
    check('complete37block_capture_and_independent_crypto',plain==inputs['plain'] and report['kernel']['captured_start_after_upload'])
    check('incomplete_upload_not_emitted',run(rows[:-2])[1] is None)
    twice=upload();twice.insert(1,json.loads(json.dumps(twice[0])))
    check('installed_identical_double34_before_data_accepted',run(twice)[1]==inputs['plain'])
    third=upload();third.insert(1,json.loads(json.dumps(third[0])));third.insert(1,json.loads(json.dumps(third[0])))
    check('third_declaration_rejected',run(third)[1] is None)
    late=upload();late.insert(3,json.loads(json.dumps(late[0])))
    check('late_declaration_rejected',run(late)[1] is None)
    check('duplicate_block_rejected',run(rows[:3]+[rows[2]]+rows[3:])[1] is None)
    check('gap_rejected',run(rows[:2]+rows[3:])[1] is None)
    damaged=upload();wire=bytearray.fromhex(damaged[2]['request']['messages'][0]['data_hex']);wire[10]^=1;wire[-1]=sum(wire[:-1])&255;damaged[2]['request']['messages'][0]['data_hex']=wire.hex()
    check('wrong_ciphertext_not_promoted',run(damaged)[1] is None)
    bad=upload();bad[2]['request']['messages'][0]['data_hex']=bad[2]['request']['messages'][0]['data_hex'][:-2]+'00'
    check('wire_checksum_failure_rejected',run(bad)[1] is None)
    forbidden=[tx(packet(bytes((c,)))) for c in range(0x20,0x26)]
    check('all6flash_controlcommands_visible',len(run(forbidden)[0]['forbidden_control_TX'])==6)
    damaged_control=tx(bytes.fromhex('beef00012500'))
    check('malformed_flash_attempt_not_hidden',len(run([damaged_control])[0]['forbidden_control_TX'])==1)
    crcreport,_=run([tx(packet(b'\x02'+bytes(4)+FLASH_SIZE.to_bytes(4,'big')))])
    check('CRC_only_is_zero_returned_bytes',crcreport['coverage']['returned_bytes']==0)
    def crc_fixture(fill):
        page=bytes((fill,))*4096
        query=tx(packet(b'\x02'+bytes(4)+(4096).to_bytes(4,'big')))
        response=rx(b'')
        response['response']['messages'][0]['data_hex']=packet(b'\x82'+zlib.crc32(page).to_bytes(4,'big')).hex()
        return page,query,response
    for fill in (255,0):
        page,query,response=crc_fixture(fill);backing=page+bytes(FLASH_SIZE-4096)
        fill_report,_=run([query,response],expected=backing,saved=backing)
        label='CRC_MATCH_ONLY_'+('FF' if fill==255 else '00')+'_NO_READ_PAYLOAD'
        check('CRC_'+str(fill)+'_fill_is_assumption_not_returned_bytes',fill_report['coverage']['returned_bytes']==0 and fill_report['coverage']['saved_byte_provenance_ranges'][0]=={'start':0,'end':4096,'classification':label})
    # Solve an independent 32-bit CRC influence system for the last four bytes.
    # The collision must differ from fill while preserving its real CRC32.
    page,query,response=crc_fixture(255);collision=bytearray(page);collision[17]^=1
    base=zlib.crc32(collision);basis={}
    for bit in range(32):
        variant=bytearray(collision);variant[-4+bit//8]^=1<<(bit%8)
        value=zlib.crc32(variant)^base;choice=1<<bit
        while value:
            pivot=value.bit_length()-1
            if pivot in basis:value^=basis[pivot][0];choice^=basis[pivot][1]
            else:basis[pivot]=(value,choice);break
    remainder=base^zlib.crc32(page);solution=0
    while remainder:
        pivot=remainder.bit_length()-1
        if pivot not in basis:raise AssertionError('CRC influence matrix lacks full rank')
        remainder^=basis[pivot][0];solution^=basis[pivot][1]
    for bit in range(32):
        if solution>>bit&1:collision[-4+bit//8]^=1<<(bit%8)
    check('CRC_collision_negative_control_is_real',bytes(collision)!=page and zlib.crc32(collision)==zlib.crc32(page))
    collision_report,_=run([query,response],expected=bytes(collision)+bytes(FLASH_SIZE-4096),saved=page+bytes(FLASH_SIZE-4096))
    check('CRC_collision_synthetic_saved_corruption_detected',collision_report['coverage']['CRC_fill_collision_ranges']==[{'start':0,'end':4096,'CRC_matches_fill':'FF','expected_differs_from_fill':True,'request_tx_index':0}] and collision_report['coverage']['saved_vs_expected_mismatch_bytes']>0 and not collision_report['universal_exact_acquisition_proven'])
    unknown_report,_=run([tx(packet(b'\x19'))]);check('unknown_command19_visible',unknown_report['unknown_TX_indices']==[0])
    constant_query,_=run([tx(packet(b'\x04'))]);check('command04_constant_query_never_reset',constant_query['TX_classification'][0]['classification']=='CONSTANT_0258_QUERY_NOT_RESET' and not constant_query['TX_classification'][0]['semantic_evidence']['does_reset_or_exit'])
    no_start,_=run(upload()[:-1]);check('complete_upload_without_entry_not_full_session',not no_start['gates']['EXPLICIT_KERNEL_START_CAPTURED'])
    if 1 in inputs['provider_contracts']:
        q={'function':'PassThruIoctl','ioctl':0x70000,'id':1,'service_id':1,'input_bytes':[1,18,52,86,120],'output_capacity':255}
        good=provider_service(q,{'status':0,'output_bytes':list(bytes.fromhex('e78f1f21'))},inputs)
        bad=provider_service(q,{'status':0,'output_bytes':[1,2,3,4]},inputs)
        check('host_seed_service_distinct_from_TX_and_crypto_checked',not good['is_ECU_wire_TX'] and good['response_contract_match'] and bad['classification']=='HOST_PROVIDER_SERVICE_RESPONSE_MISMATCH')
    image=bytes((i*17+3)&255 for i in range(FLASH_SIZE))
    read=tx(packet(b'\x03'+bytes(4)+(512).to_bytes(2,'big')))
    partial,_=run([read,rx(image[:512])],expected=image,saved=image)
    check('equal_saved_image_without_coverage_rejected',partial['coverage']['saved_equals_expected'] and not partial['coverage']['full_saved_bytes_from_received_payloads'])
    wrong=bytearray(image[:512]);wrong[7]^=1
    mismatch,_=run([read,rx(bytes(wrong))],expected=image,saved=image)
    check('actual_received_saved_mismatch_detected',mismatch['coverage']['saved_vs_returned_mismatch_ranges']==[[7,8]])
    unexpected,_=run([rx(image[:512])]);check('unsolicited_response_rejected',unexpected['coverage']['returned_bytes']==0 and bool(unexpected['issues']))
    wrong_opcode=rx(image[:512]);wrong_opcode['response']['messages'][0]['data_hex']=packet(b'\x43'+image[:512]).hex()
    check('wrong_candidate_reply_opcode_not_counted',run([read,wrong_opcode])[0]['coverage']['returned_bytes']==0)
    malformed_query,_=run([tx(packet(b'\x01\x00'))]);check('query_with_unexpected_argument_not_known_success',malformed_query['unknown_TX_indices']==[0])
    ambiguous,_=run([read,json.loads(json.dumps(read)),rx(image[:512]),rx(image[:512])]);check('ambiguous_response_addresses_do_not_count',ambiguous['coverage']['returned_bytes']==0)
    complete=upload()
    for address in range(0,FLASH_SIZE,512):complete.extend([tx(packet(b'\x03'+address.to_bytes(4,'big')+(512).to_bytes(2,'big'))),rx(image[address:address+512])])
    full,_=run(complete,expected=image,saved=image)
    check('complete2048readblocks_full_saved_comparison',full['status']=='PASS_CAPTURE_AND_SAVED_COVERAGE')
    normal=full['normalized_TX_sha256']
    for event in complete:
        event['server_utc']='different';event['request']['pid']=54321
        for msg in event['request'].get('messages',[]):msg['timestamp']=987654;msg['rx_status']=0xFFFFFFFF
    check('TX_hash_ignores_clock_uninitialized_RX_fields',run(complete,expected=image,saved=image)[0]['normalized_TX_sha256']==normal)
    output=OUTROOT/'selftest';output.mkdir(parents=True,exist_ok=True)
    result={'status':'PASS_AUDITOR_NEGATIVE_CONTROLS_ONLY','checks':checks,'count':len(checks),
            'script_sha256':sha(Path(__file__).read_bytes()),'analysis_pins':inputs['pins'],
            'physical':False,'actual_upload_claimed':False,'kernel_artifact_emitted':False}
    (output/'SELFTEST.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
