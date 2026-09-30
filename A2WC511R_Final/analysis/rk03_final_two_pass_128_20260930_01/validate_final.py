"""Streaming independent final-acquisition evidence validation; no device access."""
import json,hashlib,gzip
from pathlib import Path
N=1048576;BLOCK=128;PER=8192;READS=16384
def require(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(path):
 opener=gzip.open if str(path).endswith('.gz') else open
 with opener(path,'rt',encoding='utf-8') as f:
  for line in f:yield json.loads(line)
def frame(index):
 b=b'\xbe\xef\x00\x08'+bytes([3,index//PER])+(index%PER*BLOCK).to_bytes(4,'big')+b'\x00\x80';return b+bytes([sum(b)%256])
def comparison(a,b):
 ranges=[];count=0;i=0
 while i<N:
  if a[i]==b[i]:i+=1;continue
  start=i
  while i<N and a[i]!=b[i]:i+=1;count+=1
  ranges.append(dict(start=start,end_exclusive=i))
 return dict(identical=count==0,differing_bytes=count,differing_ranges=ranges)
def seed_key(seed):
 table=(5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8)
 keys=(0x88F0,0x6E74,0x6B70,0x3563,0x9D34,0xDBA3,0x503D,0xAFB8,0x3608,0x834F,0x3382,0x7CA3,0x437D,0x72EB,0x33BC,0x53DA)
 left,right=int.from_bytes(seed[:2],'big'),int.from_bytes(seed[2:],'big')
 for key in keys:
  expanded=(right^key)*0x10001;sub=sum(table[(expanded>>n)&31]<<n for n in (0,4,8,12));left,right=right,left^(((sub>>3)|(sub<<13))&65535)
 return right.to_bytes(2,'big')+left.to_bytes(2,'big')
def validate(stream,contract,reference,physical=True,bindings=None):
 require(len(reference)==N and sha(reference)==contract['current_reference']['sha256'],'Comparison reference pin')
 startup=None;pending=None;active=None;last=None;terminal=None;full=None;sequence=0;txcount=0;blocks=0;controls=[];images=[bytearray(),bytearray()];seed=None
 device=None;channel=None;filters=[];stops=[];prefix=[];requests_hash=hashlib.sha256();responses_hash=hashlib.sha256()
 for r in stream:
  typ=r.get('type');require(terminal is None,'Data after terminal')
  if typ=='full_read_start':
   require(startup is None and sequence==0,'Unique startup');startup=r;require(r['physical'] is physical,'Backend class')
   require(r['embedded_cipher_bytes']==r['declaration_size']==1808 and r['contract_sha256']==contract['_sha256'],'Startup image/contract binding')
   if physical:
    require(bindings is not None,'Physical binding required')
    for k,v in bindings.items():require(r.get(k)==v,'Startup '+k)
    require(Path(r['provider_path']).resolve()==Path(contract['physical_provider']['path']).resolve(),'Provider path')
    require(all(r.get(k) is True for k in ['authorization_verified','root_reservation_verified','native_invocation_reserved']),'Native gate proof')
    require(r['time_model']=='QPC_MONOTONIC_MINIMUM','Physical clock')
   continue
  require(startup is not None,'Missing startup')
  if typ=='api_intent':
   require(pending is None and last is None,'API order or missing block event');require(r['sequence']==sequence and r['physical'] is physical,'API sequence/backend');pending=r;continue
  if typ=='api_return':
   require(pending is not None and r['sequence']==sequence and r['function']==pending['function'] and r['input']==pending['input'],'API pair')
   require(r['physical'] is physical and r['status']==0,'Terminal API failure');require(r['qpc_after']>=r['qpc_before'] and r['api_elapsed_ticks']==r['qpc_after']-r['qpc_before'] and r['qpc_frequency']>0,'API clock')
   if 'esp_before' in r:require(r['esp_before']==r['esp_after'],'Stack integrity')
   pending=None;sequence+=1;name=r['function'];inp=r['input'];out=r['output']
   if 'canaries_intact' in out:require(out['canaries_intact'] is True,'API canaries')
   if 'channel' in inp:require(inp['channel']==channel,'Channel binding')
   if 'device' in inp:require(inp['device']==device,'Device binding')
   if name in ('PassThruReadMsgs','PassThruWriteMsgs'):
    require(full is None,'Protocol operation after final result');require(inp['input_count']==inp['message_capacity']==out['count']==1 and inp['count_pointer_present'],'API message counts');require(1<=inp['timeout_ms']<=1000,'Timeout bounds')
   if name=='PassThruWriteMsgs':
    require(active is None and txcount<16408,'No retry/extra write');m=inp['message'];sent=bytes.fromhex(m['data_hex']);require(m==out['message'],'Write mutation')
    require(inp['timeout_ms']==1000 and m['protocol']==3 and m['rx_status']==m['tx_flags']==m['timestamp']==m['extra_data_index']==0 and m['data_size']==len(sent),'TX metadata')
    if txcount<24:
     if txcount==4:
      require(seed is not None,'Seed before key');body=b'\x27\x02'+seed_key(seed);b=b'\x80\x10\xf0'+bytes([len(body)])+body;expected=b+bytes([sum(b)%256])
     else:expected=bytes.fromhex(contract['ordered_prefix_requests'][txcount]['wire_hex'])
    else:expected=frame(txcount-24)
    require(sent==expected,'Exact fixed request schedule at '+str(txcount));active=dict(stage=txcount,sent=sent,data=bytearray(),indicators=0,pieces=0,start=None);txcount+=1;requests_hash.update(sent);continue
   if name=='PassThruReadMsgs':
    require(active is not None,'Read without one outstanding request');stage=active['stage'];m=out['message'];part=bytes.fromhex(m['data_hex']);limit=139 if stage>=24 else (20 if stage==23 else 523)
    require(m['protocol']==3 and m['tx_flags']==0 and m['data_size']==len(part)<=limit and m['extra_data_index'] in (0,len(part)),'RX metadata')
    active['pieces']+=1;require(active['pieces']<=limit+4,'Fragment count')
    if active['start'] is None:active['start']=r['qpc_before']
    require(r['qpc_after']-active['start']<2*r['qpc_frequency'],'Whole frame deadline')
    if m['rx_status']:
     active['indicators']+=1;require(not active['data'] and active['indicators']<=4,'Indicator bounds')
     require((m['rx_status'] in (2,8) and not part) or (m['rx_status'] in (1,9) and part==active['sent']),'Indicator/echo');continue
    require(part and len(active['data'])+len(part)<=limit,'Response byte bounds');active['data'].extend(part);data=active['data']
    expected_size=139 if stage>=24 else (20 if stage==23 else (data[3]+5 if len(data)>=4 else None))
    if expected_size is None or len(data)<expected_size:continue
    require(len(data)==expected_size and sum(data[:-1])%256==data[-1],'Response length/checksum')
    if stage>=24:
     i=stage-24;header=b'\xbe\xef\x00\x86\x83'+bytes([i//PER])+(i%PER*128).to_bytes(4,'big');require(data[:10]==header,'Returned pass/address/length');last=(i,bytes(data),active['sent'])
    elif stage==0:require(len(data)==62 and data[:13]==bytes.fromhex('80f01039ffa210112f12515306'),'BF identity')
    elif stage==3:require(len(data)==11 and data[:6]==bytes.fromhex('80f010066701'),'Seed framing');seed=bytes(data[6:10])
    else:require(data.hex()==contract['ordered_prefix_requests'][stage]['expected_reply_hex'],'Fixed prefix reply '+str(stage))
    if stage<24:prefix.append(data.hex())
    responses_hash.update(data);active=None;continue
   require(active is None and last is None,'Control before complete reply')
   detail=None
   if name=='PassThruOpen':require(inp=={'name_present':False,'device_output_present':True},'Open args');device=out['device']
   elif name=='PassThruReadVersion':require(inp==dict(device=device,firmware_capacity=80,dll_capacity=80,api_capacity=80),'Version args')
   elif name=='PassThruConnect':require(inp==dict(device=device,protocol=3,flags=512,baud=4800,channel_output_present=True),'Connect args');channel=out['channel']
   elif name=='PassThruIoctl':
    require(inp['output_present'] is False,'IOCTL output pointer');code=inp['ioctl'];detail=[code]
    if code in (1,2):
     count=5 if code==1 else 1;require(inp['input_present'],'Config input')
     for obj in [inp['config'],out['config']]:require(obj['list_present'] and obj['pointer_matches_owned'] and obj['returned_num_params']==obj['owned_capacity']==count,'Config integrity')
     wanted=contract['set_config_order'] if code==1 else inp['config']['owned_buffer_entries'];require(out['config']['owned_buffer_entries']==wanted,'Effective config')
     detail.append([[x['parameter'],x['value']] for x in inp['config']['owned_buffer_entries']])
    else:require(code in (7,8) and inp['input_present'] is False,'Only queue clears')
   elif name=='PassThruStartMsgFilter':
    k=len(filters);require(k<2 and inp['filter_type']==1 and inp['mask_present'] and inp['pattern_present'] and inp['filter_output_present'],'Filter pointers')
    for field,hexdata in [('mask','ffff' if k else '00000000'),('pattern','beef' if k else '00000000')]+([] if k else [('flow','00000000')]):
     msg=inp[field];require(msg==out[field] and msg['protocol']==3 and msg['rx_status']==msg['tx_flags']==msg['timestamp']==msg['extra_data_index']==0 and msg['data_hex']==hexdata and msg['data_size']==len(bytes.fromhex(hexdata)),'Filter objects')
    require(inp['flow_present'] is (k==0),'Filter flow presence')
    if k:require(inp['flow'] is None and out['flow'] is None,'Kernel null flow')
    filters.append(out['filter_id'])
   elif name=='PassThruStopMsgFilter':require(len(stops)<len(filters) and inp['filter_id']==filters[len(stops)],'Filter ownership');stops.append(inp['filter_id'])
   elif name in ('MonotonicMinimumWait','OfflineClockAdvance'):
    require(not physical or name=='MonotonicMinimumWait','Physical minimum wait');detail=[inp['requested_ms'],inp['reason']]
    if name=='MonotonicMinimumWait':require(r['api_elapsed_ticks']*1000>=inp['requested_ms']*r['qpc_frequency'],'Minimum delay')
    else:require(out['virtual_after']>=inp['virtual_before']+inp['requested_ms'],'Virtual minimum delay')
    name='WAIT'
   elif name not in ('PassThruDisconnect','PassThruClose'):raise ValueError('Unlisted API '+name)
   controls.append([name,txcount,detail]);continue
  if typ=='rom_block':
   require(pending is None and last is not None and full is None,'Block event ordering');i,data,sent=last;require(i==blocks and i<READS,'Block ordering');p=i//PER;a=i%PER*128
   require(r==dict(type='rom_block',read_index=i,**{'pass':p},block=i%PER,address=a,length=128,request_hex=sent.hex(),response_hex=data.hex(),pass0_match=True,mismatches=[]),'Exact block event and immediate match')
   if p:require(images[0][a:a+128]==data[10:-1],'Immediate second-pass identity')
   require(len(images[p])==a,'Output coverage');images[p].extend(data[10:-1]);blocks+=1;last=None;continue
  if typ=='full_read_result':
   require(pending is None and active is None and last is None and full is None and blocks==READS and txcount==16408,'Full-result boundary')
   require(len(images[0])==len(images[1])==N and images[0]==images[1],'Full byte equality')
   full=dict(type='full_read_result',passes=2,blocks_per_pass=8192,block_bytes=128,ROM_start=0,ROM_end_exclusive=N,pass0_bytes=N,pass1_bytes=N,pass0_sha256=sha(images[0]),pass1_sha256=sha(images[1]),pass_to_pass_identical=True,current_reference_sha256=sha(reference),pass0_vs_current=comparison(images[0],reference),pass1_vs_current=comparison(images[1],reference),baseline_equality_required_for_transport=False)
   require(r==full,'Independent final comparison');continue
  if typ=='probe_terminal':
   require(pending is None and active is None and last is None and full is not None,'Terminal after complete results')
   require(r['physical'] is physical and r['status']==('PASS_FULL_ROM_TWO_PASS_128' if physical else 'PASS_OFFLINE_FULL_ROM_TWO_PASS_128'),'Terminal pass')
   require(r['protocol_complete'] and r['cleanup_confirmed'] and r['cleanup_error_mask']==0 and not r['log_failed'] and not r['failure'],'Terminal cleanup')
   require(r['state']['tx_attempts']==16408 and r['state']['acquisition_validated'] and r['state']['identity_validated'] and r['state']['acknowledged_chunks']==15,'Terminal bounds');terminal=r;continue
  raise ValueError('Unaccounted event '+str(typ))
 require(terminal is not None,'Missing terminal')
 wanted=[['PassThruOpen',0,None],['PassThruReadVersion',0,None],['PassThruConnect',0,None]]
 wanted += [['PassThruIoctl',0,[2,[[x['parameter'],x['value']]]]] for x in contract['set_config_order']]
 wanted += [['PassThruIoctl',0,[1,[[x['parameter'],0xD15EA5ED] for x in contract['set_config_order']]]],['PassThruStartMsgFilter',0,None],['WAIT',5,[200,'post_key_ack']],['WAIT',6,[100,'post_session_ack']],['PassThruIoctl',6,[2,[[1,15625]]]],['PassThruIoctl',6,[7]],['PassThruIoctl',6,[8]],['WAIT',6,[200,'pre_download_declaration']],['PassThruStopMsgFilter',23,None],['PassThruIoctl',23,[2,[[1,62500]]]],['PassThruStartMsgFilter',23,None],['PassThruStopMsgFilter',16408,None],['PassThruDisconnect',16408,None],['PassThruClose',16408,None]]
 require(controls==wanted,'Exact control schedule')
 return dict(status='PASS',BF_identity='2F12515306',tx_count=txcount,ROM_requests=blocks,API_returns=sequence,prefix_replies=prefix,requests_sha256=requests_hash.hexdigest(),responses_sha256=responses_hash.hexdigest(),cleanup_confirmed=True,result=full),tuple(bytes(x) for x in images)
