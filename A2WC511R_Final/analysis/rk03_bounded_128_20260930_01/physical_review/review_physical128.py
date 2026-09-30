"""Read-only audit of one preserved physical run; never invokes native/provider tools."""
from pathlib import Path
import datetime
import hashlib
import json

A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_128_20260930_01')
R=Path(r'C:\Dev\A2WC511R_RK03_Bounded128Physical')
S=R/'physical_session/RK03_BOUNDED_ROM_READ_128_01'
OUT=A/'physical_review'
pins={}; checks=0
def check(value,label):
 global checks
 if not value: raise AssertionError(label)
 checks+=1
def pin(path):
 path=Path(path); data=path.read_bytes()
 p={'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 pins[str(path)]=p
 return p
def load(path):
 pin(path); return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def verify(p):
 actual=pin(p['path']);check(actual['sha256']==p['sha256'],'hash '+p['path'])
 if 'bytes' in p:check(actual['bytes']==p['bytes'],'size '+p['path'])
def transform(data,keys):
 table=[5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8];out=bytearray()
 for n in range(0,len(data),4):
  l,r=int.from_bytes(data[n:n+2],'big'),int.from_bytes(data[n+2:n+4],'big')
  for k in keys:
   e=(r^k)*0x10001;v=sum(table[(e>>s)&31]<<s for s in [0,4,8,12]);l,r=r,l^(((v>>3)|(v<<13))&65535)
  out+=r.to_bytes(2,'big')+l.to_bytes(2,'big')
 return bytes(out)
def checksum(wire):return len(wire)>1 and sum(wire[:-1])%256==wire[-1]

result=load(A/'physical_result/PHYSICAL_RESULT.json')
check(pin(A/'physical_result/PHYSICAL_RESULT.json')['sha256']=='84b6a7cd1540540ade99aa2582723c91ac1c6efebf95ba04e37a3e6383fac754','result pin')
for p in result['source_evidence']:verify(p)
verify(result['validator'])
qual=load(A/'qualification/QUALIFICATION.json')
check(pin(A/'qualification/QUALIFICATION.json')['sha256']==result['execution']['qualification_sha256']=='a9080dae4b33766f7de2771ae5dbac575c5d8201096a52a3bf5611dcb926e26c','certificate binding')
for k in ['physical_executable','review_contract','fixed_upload_manifest']:verify(qual[k])
contract=load(qual['review_contract']['path']); upload=load(qual['fixed_upload_manifest']['path'])
verify(upload['kernel']); kernel=Path(upload['kernel']['path']).read_bytes()
check(hashlib.sha256(kernel).hexdigest()==contract['kernel_sha256']==qual['kernel_sha256']=='808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653','new kernel bound')
verify(contract['bounded_read']['current_rom']);rom=Path(contract['bounded_read']['current_rom']['path']).read_bytes()
expected=bytes.fromhex('beef0086830000000000')+rom[:128];expected+=bytes([sum(expected)%256])
check(len(expected)==139 and expected.hex()==contract['bounded_read']['response'],'independent current128 reply derivation')
execution=load(S/'EXECUTION.json');check(execution==result['execution'],'execution record matches result')
check(execution['exit_code']==0 and execution['process_exited'] and execution['pid']==26152 and not execution['retry_allowed'],'single completed child')
for name in ['PRELAUNCH_CLIENT_CHECK.json','POSTEXIT_CLIENT_CHECK.json']:
 client=load(S/name);check(client['pass'] and not client['known_conflicting_clients'] and not client['provider_module_users'] and not client['module_inspection_failures'] and not client['real_provider_loaded_by_check'],'preserved client check '+name)
auth=(S/'AUTHORIZATION.txt').read_bytes();reserve=(S/'launch.reserved').read_bytes()
sid=contract['session_id'];exe=execution['executable_sha256'];ch=execution['contract_sha256']
check(auth==f'PROCEED RK03 128 BYTE ROM READ\nSESSION_ID={sid}\nEXE_SHA256={exe}\nCONTRACT_SHA256={ch}\n'.encode(),'authorization exact bytes')
check(reserve==(S/'invocation.once').read_bytes()==f'{sid}\n{exe}\n{ch}\n'.encode(),'root/native one-shot binding')
rows=[json.loads(line) for line in (S/'native_api.jsonl').read_text().splitlines()]
start=rows[0]; terminal=rows[-1]
check(start['type']=='bounded_read_start' and start['physical'] and start['session_id']==sid,'physical startup/session')
check(start['exe_sha256']==exe==qual['physical_executable']['sha256'] and start['contract_sha256']==ch==qual['review_contract']['sha256'],'release bindings')
provider=contract['physical_provider'];verify(provider)
check(start['provider_sha256']==provider['sha256'] and Path(start['provider_path'])==Path(provider['path']),'provider binding')
check(all(start[k] for k in ['authorization_verified','root_reservation_verified','native_invocation_reserved']),'native authorization checks')
check(start['embedded_cipher_bytes']==start['declaration_size']==1808,'kernel upload size')
api=[r for r in rows if r['type'] in ['api_intent','api_return']]
check(len(api)==194,'97 complete API pairs')
returns=[]
for n in range(97):
 intent,ret=api[n*2:n*2+2]
 check(intent['type']=='api_intent' and ret['type']=='api_return' and intent['sequence']==ret['sequence']==n,'paired chronological call '+str(n))
 check(intent['function']==ret['function'] and intent['input']==ret['input'] and intent['physical'] and ret['physical'],'paired arguments '+str(n))
 check(ret['status']==0 and ret['qpc_before']<=ret['qpc_after'] and ret['qpc_frequency']>0 and ret['api_elapsed_ticks']==ret['qpc_after']-ret['qpc_before'],'return/timing '+str(n))
 if n:check(returns[-1]['qpc_after']<=ret['qpc_before'],'monotonic API '+str(n))
 if 'canaries_intact' in ret['output']:check(ret['output']['canaries_intact'],'canaries '+str(n))
 returns.append(ret)
tx=[r for r in returns if r['function']=='PassThruWriteMsgs']
check(len(tx)==25 and len(contract['ordered_requests'])==25,'exact25TX')
responses=[]; exchanges=[]
for stage,t in enumerate(tx):
 m=t['input']['message']; wire=bytes.fromhex(m['data_hex']); seq=t['sequence']
 check(t['input']['input_count']==t['output']['count']==1 and t['output']['message']==m,'unmutated TX '+str(stage))
 check(m['protocol']==3 and m['rx_status']==m['tx_flags']==0 and m['data_size']==m['logged_bytes']==len(wire) and not m['data_truncated'] and checksum(wire),'TX frame metadata/checksum '+str(stage))
 if stage!=4:check(wire.hex()==contract['ordered_requests'][stage]['wire_hex'],'fixed TX '+str(stage))
 # Exactly two reads (SOM/data) must precede every next control API/TX.
 som,data=returns[seq+1:seq+3]
 check(som['function']==data['function']=='PassThruReadMsgs','complete reply before next API '+str(stage))
 for rr in [som,data]:check(rr['output']['count']==1 and rr['input']['input_count']==1 and rr['input']['timeout_ms']==1000,'read count/timeout '+str(stage))
 sm=som['output']['message']; dm=data['output']['message']; reply=bytes.fromhex(dm['data_hex'])
 check(sm['rx_status']==2 and sm['protocol']==3 and sm['tx_flags']==0 and sm['data_size']==sm['extra_data_index']==sm['logged_bytes']==0 and sm['data_hex']=='','exact SOM '+str(stage))
 check(dm['protocol']==3 and dm['rx_status']==dm['tx_flags']==0 and dm['data_size']==dm['extra_data_index']==dm['logged_bytes']==len(reply) and not dm['data_truncated'] and checksum(reply),'complete RX metadata/checksum '+str(stage))
 duration=(data['qpc_after']-som['qpc_before'])*1000/data['qpc_frequency'];check(0<=duration<2000,'whole response deadline '+str(stage))
 if stage!=3:check(reply.hex()==contract['ordered_requests'][stage]['expected_reply_hex'],'exact expected ACK/reply '+str(stage))
 responses.append(reply);exchanges.append({'stage':stage,'TX_sequence':seq,'RX_sequences':[som['sequence'],data['sequence']],'response_bytes':len(reply),'receive_window_ms':duration})
seed_reply=responses[3];check(len(seed_reply)==11 and seed_reply[:6]==bytes.fromhex('80f010066701'),'valid seed format')
seed=seed_reply[6:10];key=transform(seed,[0x88F0,0x6E74,0x6B70,0x3563,0x9D34,0xDBA3,0x503D,0xAFB8,0x3608,0x834F,0x3382,0x7CA3,0x437D,0x72EB,0x33BC,0x53DA])
keywire=bytes.fromhex('8010f0062702')+key;keywire+=bytes([sum(keywire)%256])
check(tx[4]['input']['message']['data_hex']==keywire.hex(),'independent seed/key transform')
cipher=bytearray()
for n,chunk in enumerate(upload['chunks']):
 wire=bytes.fromhex(tx[7+n]['input']['message']['data_hex']);piece=wire[8:-1];plain=kernel[n*128:n*128+128]
 check(wire.hex()==chunk['request_hex'] and responses[n+7].hex()==chunk['reply_hex']=='80f0100176f7','new chunk wire and ACK '+str(n))
 check(len(piece)==chunk['length'] and hashlib.sha256(piece).hexdigest()==chunk['cipher_sha256'] and hashlib.sha256(plain).hexdigest()==chunk['payload_sha256'],'chunk plaintext/cipher pins '+str(n))
 check(int.from_bytes(wire[5:8],'big')==0xff3000+n*128,'contiguous upload address '+str(n));cipher.extend(piece)
check(len(cipher)==1808 and transform(cipher,[0x6E86,0xF513,0xCE22,0x7856])==kernel,'captured complete ciphertext decodes to exact new kernel')
check([len(bytes.fromhex(t['input']['message']['data_hex']))-9 for t in tx[7:22]]==[128]*14+[16],'15 upload chunks only')
check(responses[-1]==expected and len(responses[-1][10:-1])==128 and responses[-1][10:-1]==rom[:128],'physical exact139 response/current128')
events=[r for r in rows if r['type']=='bounded_read_result'];check(len(events)==1,'one bounded result')
event=events[0];check(event['address']==0 and event['length']==128 and event['checksum_pass'] and event['mismatch_count']==0 and event['mismatches']==[] and event['response_hex']==expected.hex() and event['payload_hex']==rom[:128].hex(),'bounded result raw evidence agrees')
io=[r for r in returns if r['function']=='PassThruIoctl'];initial=[{'parameter':p,'value':v} for p,v in [(22,0),(7,1),(10,0),(12,0),(3,0)]]
check([(r['input']['ioctl'],r['sequence']) for r in io[:6]]==[(2,3),(2,4),(2,5),(2,6),(2,7),(1,8)],'initial five SET immediate GET')
for n,r in enumerate(io[:5]):check(r['input']['config']['owned_buffer_entries']==r['output']['config']['owned_buffer_entries']==[initial[n]],'SET exact '+str(n))
check(io[5]['output']['config']['owned_buffer_entries']==initial and io[5]['output']['config']['pointer_matches_owned'],'provider returned GET values')
check([r['input']['ioctl'] for r in io[6:]]==[2,7,8,2],'baud15625 TX/RX clear then62500 ordering')
check([io[n]['output']['config']['owned_buffer_entries'] for n in [6,9]]==[[{'parameter':1,'value':15625}],[{'parameter':1,'value':62500}]],'accepted baud values without claiming GET verification')
filters=[r for r in returns if r['function']=='PassThruStartMsgFilter'];check(len(filters)==2 and filters[0]['sequence']==9 and filters[1]['sequence']==87,'two filters/order')
for f,mask,pattern,flow in [(filters[0],'00000000','00000000','00000000'),(filters[1],'ffff','beef',None)]:
 x=f['input'];check(x['filter_type']==1 and x['mask']['data_hex']==mask and x['pattern']['data_hex']==pattern and ((x['flow']['data_hex'] if x['flow'] is not None else None)==flow),'exact filter and flow pointer')
check(returns[85]['function']=='PassThruStopMsgFilter' and returns[85]['input']['filter_id']==filters[0]['output']['filter_id'],'OEM filter stopped after start ACK')
waits=[r for r in returns if r['function']=='MonotonicMinimumWait'];check([r['input']['requested_ms'] for r in waits]==[200,100,200],'exact waits')
for r in waits:check(r['output']['minimum_satisfied'] and r['output']['elapsed_qpc_ticks']>=r['output']['minimum_qpc_ticks'],'actual wait minimum')
cleanup=returns[-3:];check([r['function'] for r in cleanup]==['PassThruStopMsgFilter','PassThruDisconnect','PassThruClose'] and all(r.get('cleanup') for r in cleanup),'cleanup only following bounded read')
check(cleanup[0]['input']['filter_id']==filters[1]['output']['filter_id'],'active BEEF filter cleanup')
check(terminal['status']=='PASS_BOUNDED_ROM_READ_128_ONLY' and terminal['protocol_complete'] and terminal['cleanup_confirmed'] and terminal['cleanup_error_mask']==0 and not terminal['log_failed'] and not terminal['failure'],'terminal PASS cleanup')
state=terminal['state'];check(state['tx_attempts']==25 and state['acknowledged_chunks']==15 and all(state[k] for k in ['start_acknowledged','identity_validated','bounded_validated']) and not state['opened'] and not state['connected'] and not state['filter']['active'],'terminal counters/resources')
check(result['physical_invocations']==1 and result['validation']['bounded_reply_hex']==expected.hex() and result['validation']['responses']==[b.hex() for b in responses],'root result matches independently parsed raw evidence')
for p in list(pins.values()):verify(p)
pin(Path(__file__))
report={'schema':1,'status':'PASS','scope':'INDEPENDENT_READ_ONLY_REVIEW_OF_COMPLETED_PHYSICAL_BOUNDED128_RUN','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'passive_review','checks_passed':checks,'blocking_findings':[],
 'result':pin(A/'physical_result/PHYSICAL_RESULT.json'),'journal':pin(S/'native_api.jsonl'),'session_id':sid,'execution':execution,
 'counts':{'physical_invocations_recorded':1,'TX':25,'API_pairs':97,'ROM_requests':1,'upload_chunks':15,'upload_ACKs':15,'uploaded_bytes':1808,'start_requests':1,'identity_requests':1,'cleanup_calls':3,'retries':0},
 'bounded_read':{'address':0,'length':128,'request':tx[-1]['input']['message']['data_hex'],'response':expected.hex(),'response_bytes':139,'response_sha256':hashlib.sha256(expected).hexdigest(),'payload_sha256':hashlib.sha256(rom[:128]).hexdigest(),'mismatch_locations':[],'exchange':exchanges[-1]},
 'seed':seed.hex(),'derived_key':key.hex(),'kernel_sha256':hashlib.sha256(kernel).hexdigest(),'captured_cipher_sha256':hashlib.sha256(cipher).hexdigest(),'waits_ms_actual':[r['output']['elapsed_qpc_ticks']*1000/r['output']['qpc_frequency'] for r in waits],
 'conclusions':['All nine result-pinned raw files retain their sealed hashes; recorded authorization, certificate, executable and provider match the new release.','Exactly 15 contiguous uploaded ciphertext chunks independently decode to the new128 kernel and each has its exact positive ACK before subsequent control operations.','One start and one identity precede the sole128-byte ROM request; exact139-byte frame, body length, address/pass, checksum and all128 bytes match current.bin.','The journal contains no additional TX, retry or flash command; all three cleanup calls return0 and the child exited0 with a clean recorded post-exit client/module scan.'],
 'limitations':['This is review of preserved physical API evidence, not a second physical operation or a rerun of the qualified sealer.','Only128 bytes at address0 were validated; they cannot attest the whole current calibration and are also known to match stock.','No raw waveform or ECU RAM readback was captured; upload ACKs and release-bound ciphertext support the image association.','This successful shorter response does not establish the cause of the preceding failed512-byte response.','OEM-return/recovery is managed separately by root and was pending when this review was requested. Full two-pass acquisition is neither executed nor authorized by this review.'],
 'reviewed_files':list(pins.values()),'physical_operations_by_reviewer':0,'provider_loads_by_reviewer':0,'native_executions_by_reviewer':0}
with (OUT/'REVIEW.json').open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':'PASS','checks':checks,'report':pin(OUT/'REVIEW.json'),'bounded_receive_ms':exchanges[-1]['receive_window_ms']}))
