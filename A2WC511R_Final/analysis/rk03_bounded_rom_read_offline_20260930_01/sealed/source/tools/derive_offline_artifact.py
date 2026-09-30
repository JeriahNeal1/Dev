"""Derive one fixed offline read from named sealed sources. No vehicle access."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r'C:\Dev\A2WC511R_RK03_KernelIdentityOffline\kernel_identity')
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_rom_read_offline_20260930_01')
P=A.parent/'rk03_kernel_identity_physical_20260930_01'
K=Path(r'C:\Dev\A2WC511R_ReadKernel')
ROM=Path(r'C:\Dev\SubaruRoms\current.bin')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
def norm(x):
    if isinstance(x,list):return [norm(v) for v in x]
    if isinstance(x,dict):return {k:norm(v) for k,v in x.items() if k not in ('config_pointer','owned_buffer_pointer','timestamp')}
    return x
def frame(payload):
    raw=b'\xbe\xef'+len(payload).to_bytes(2,'big')+payload
    return (raw+bytes([sum(raw)&255])).hex()
def message(template,wire):
    m=copy.deepcopy(template);size=len(bytes.fromhex(wire))
    m.update(data_hex=wire,data_size=size,logged_bytes=size,extra_data_index=size if template['extra_data_index'] else 0,rx_status=0)
    return m
def main():
    expected={P/'physical_result/PHYSICAL_RESULT.json':'2f524a38ef883b189aeab55ac1c06127c6f8164eeccca835f81fd78d5f7fdcda',
      P/'oem_return_after_identity_01/OEM_RETURN_RESULT.json':'d2c181435ab346a400e30214f739c0363fec5ce13dc840c72dd2f66c82c0688b',
      P/'qualification/QUALIFICATION.json':'19dc92d085a5721d7af280fc8fabf32a22919a9a370ec19e8052c8d6f8cf9cf8',
      ROM:'bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2',
      K/'build/rk02_01/kernel.bin':'3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581',
      K/'build/rk02_01/manifest.json':'a35562a19f21d4a2815e88fb729d21dd2cc08bf702c0d866f88ffc9e3ddb659e',
      K/'src/kernel.S':'3d20c9227c209b6712a451ce867c032e8e8d21fd4d2776816d720e2a3fa72355',
      BASE/'src/identity_model.py':'8b2523cb4a20c75b0f5c53f9e5e663a6c78e7dd1a5dcbd52915f468160096b53',
      BASE/'contract/CONTRACT.json':'bed9a78f0bde41f092e5617d547eed520784a9354a099ea607e82e47c80afd31'}
    for p,h in expected.items():assert sha(p)==h,str(p)
    physical=json.loads((P/'physical_result/PHYSICAL_RESULT.json').read_text())
    assert physical['RK03_KERNEL_START_IDENTITY_PHYSICAL']=='PASS'
    raw_pin=next(p for p in physical['source_evidence'] if p['path'].endswith('native_api.jsonl'))
    raw=Path(raw_pin['path']);assert sha(raw)==raw_pin['sha256']
    ret=[r for r in map(json.loads,raw.read_text().splitlines()) if r.get('type')=='api_return']
    assert len(ret)==94 and all(r['status']==0 for r in ret)
    actions=[]
    for r in ret[:-3]:
        action={'function':r['function'],'input':norm(r['input']),'output':norm(r['output']),'source_sequence':r['sequence']}
        if r['function']=='MonotonicMinimumWait':action={'function':'VirtualWait','input':{'milliseconds':r['input']['milliseconds'],'reason':r['input']['reason']},'output':{},'source_sequence':r['sequence']}
        actions.append(action)
    cleanup=[{'function':r['function'],'input':norm(r['input']),'output':norm(r['output'])} for r in ret[-3:]]
    writes=[a for a in actions if a['function']=='PassThruWriteMsgs']
    reads=[a for a in actions if a['function']=='PassThruReadMsgs' and a['output']['message']['rx_status']==0]
    assert len(writes)==len(reads)==24 and len(actions)==91
    frames=[dict(tx=w['input']['message']['data_hex'],rx=r['output']['message']['data_hex']) for w,r in zip(writes,reads)]
    assert frames[-2:]==[{'tx':'8010f003310101b6','rx':'80f01003710101f6'},{'tx':'beef000101af','rx':'beef000f8141325743353131522d524b3032005f'}]
    rom=ROM.read_bytes();assert len(rom)==1048576
    data=rom[:512];data_sha=hashlib.sha256(data).hexdigest()
    request=frame(bytes.fromhex('0300000000000200'))
    response=frame(bytes.fromhex('830000000000')+data)
    assert request=='beef00080300000000000200ba' and len(bytes.fromhex(response))==523
    fixed={'address':'00000000','length':512,'end_exclusive':'00000200','pass':0,'request':request,
           'response':response,'expected_bytes_hex':data.hex(),'expected_bytes_sha256':data_sha,
           'request_frame_bytes':13,'response_frame_bytes':523,'response_body_bytes':518,
           'reason':'Unchanged RK02 image accepts only512-byte sequential blocks; the initial cursor is0. No smaller or CAL-ID-first request is valid.',
           'expected_next_cursor':'00000200','second_read_allowed':False}
    frame_row={'tx':request,'rx':response};frames.append(frame_row)
    w=copy.deepcopy(writes[-1]);w.pop('source_sequence');w['input']['message']=message(w['input']['message'],request);w['output']['message']=message(w['output']['message'],request);actions.append(w)
    marker=copy.deepcopy(actions[89]);marker.pop('source_sequence');actions.append(marker)
    r=copy.deepcopy(reads[-1]);r.pop('source_sequence');r['output']['message']=message(r['output']['message'],response);actions.append(r)
    old=json.loads((BASE/'contract/CONTRACT.json').read_text())
    contract=dict(schema=1,artifact='RK03_BOUNDED_ROM_READ',physical=False,kind='STATIC_FAKE_TRANSCRIPT_MODEL',
      entry='FFFF3004',image_bytes=1808,image_sha256=expected[K/'build/rk02_01/kernel.bin'],
      version_ascii='A2WC511R-RK02\0',frames=frames,actions=actions,cleanup=cleanup,
      prefix_transmits=24,prefix_actions=91,maximum_transmits=25,start_count=1,identity_count=1,
      ROM_read_count=1,fixed_read=fixed,full_upload_chunks=old['full_upload_chunks'],
      seed_behavior='FIXED_LATEST_PHYSICAL_SEED_KEY_TRANSCRIPT; general seed algorithm evidence reused, not rerun')
    canonical=json.dumps(contract,sort_keys=True,separators=(',',':'));contract_sha=hashlib.sha256(canonical.encode()).hexdigest()
    (ROOT/'src').mkdir(parents=True,exist_ok=True)
    with (ROOT/'src/fixed_data.py').open('x',encoding='utf-8',newline='\n') as f:
        f.write('# Generated pinned offline-only data.\nCONTRACT_SHA256 = '+repr(contract_sha)+'\nCONTRACT_JSON = '+repr(canonical)+'\n')
    save(ROOT/'contract/CONTRACT.json',contract)
    save(ROOT/'contract/SOURCE_PINS.json',dict(inputs=[pin(p) for p in expected]+[pin(raw)],
        normalizations=['Captured pointer addresses and provider timestamps removed from model actions; raw physical evidence remains sealed unchanged.',
                        'Physical minimum waits represented as virtual200/100/200ms; no silicon timing claim.',
                        'Only the25th exchange is synthetic, derived from the fixed kernel contract and current.bin bytes.'],
        physical_operations=0,prior_qualification_reused_not_recounted=True))
    save(A/'ROOT_FIXED_READ_CONTRACT.json',fixed)
    with (A/'EXPECTED_FIRST512_CURRENT.bin').open('xb') as f:f.write(data)
    source=(BASE/'src/identity_model.py').read_text()
    substitutions=[
      ("'wrong_rx_status','wrong_protocol','trailing_bytes','short_wait')","'wrong_rx_status','wrong_protocol','trailing_bytes','short_wait',\n        'wrong_read_pass','wrong_read_address','wrong_read_data','wrong_read_command')"),
      ("len(c['frames'])==24 and len(c['actions'])==91","len(c['frames'])==25 and len(c['actions'])==94"),
      ("    return c\n","    require(c['fixed_read']['address']=='00000000' and c['fixed_read']['length']==512 and c['fixed_read']['pass']==0,'Fixed first512-byte range')\n    require(c['frames'][24]['tx']=='beef00080300000000000200ba','Fixed read request')\n    require(c['fixed_read']['expected_bytes_sha256']=="+repr(data_sha)+",'Fixed expected ROM bytes')\n    return c\n"),
      ("    return status,output\n","    if fault in ('wrong_read_pass','wrong_read_address','wrong_read_data','wrong_read_command'):\n        m=output['message'];wire=bytearray.fromhex(m['data_hex'])\n        require(len(wire)==523,'Read mutation requires fixed523-byte reply')\n        index={'wrong_read_pass':5,'wrong_read_address':9,'wrong_read_data':10,'wrong_read_command':4}[fault]\n        wire[index]^=1;wire[-1]=sum(wire[:-1])&255;m['data_hex']=wire.hex()\n    return status,output\n"),
      ('fault_step<94','fault_step<97'),
      ('identity_done=False;virtual_ms=0','identity_done=False;read_done=False;virtual_ms=0'),
      ("require(not identity_done,'Only cleanup after identity')","require(not read_done,'Only cleanup after bounded read')"),
      ('not pending and tx<24','not pending and tx<25'),
      ('_frame(wire,tx==23,False)','_frame(wire,tx>=23,False)'),
      ("if tx==23: require(acks==23,'Start ACK before identity')","if tx==23: require(acks==23,'Start ACK before identity')\n                if tx==24: require(acks==24 and identity_done,'Identity ACK before one fixed read')"),
      ('pending and 1<=tx<=24','pending and 1<=tx<=25'),
      ('_frame(buffer,tx==24,True)','_frame(buffer,tx>=24,True)'),
      ("require(ordinal==90 and acks==24,'Identity is the final protocol action')\n                        identity_done=True","require(ordinal==90 and acks==24,'Fixed identity precedes read')\n                        identity_done=True\n                    if tx==25:\n                        require(ordinal==93 and acks==25 and identity_done,'One bounded read is the final protocol action')\n                        require(len(buffer)==523 and buffer[4:10]==bytes.fromhex('830000000000'),'Read command/pass/address/length')\n                        require(hashlib.sha256(buffer[10:-1]).hexdigest()==c['fixed_read']['expected_bytes_sha256'],'Exact expected ROM data')\n                        read_done=True"),
      ('identity_done and tx==acks==24','identity_done and read_done and tx==acks==25'),
      ('call(action,91+offset,True)','call(action,94+offset,True)'),
      ('and identity_done\n','and identity_done and read_done\n'),
      ('PASS_OFFLINE_KERNEL_START_IDENTITY_ONLY','PASS_OFFLINE_BOUNDED_ROM_READ'),
      ("'identity_validated':identity_done,","'identity_validated':identity_done,'bounded_read_validated':read_done,\n        'fixed_ROM_address':'00000000','fixed_ROM_length':512,'ROM_read_requests':max(0,tx-24),"),
    ]
    for old,new in substitutions:
        assert old in source,old
        source=source.replace(old,new,1)
    source=source.replace("            require(output==action['output'],'Exact captured/model output contract')\n",'',1)
    source=source.replace('            output=call(action,ordinal)\n',"            output=call(action,ordinal)\n            require(output==action['output'],'Exact captured/model output contract')\n",1)
    with (ROOT/'src/bounded_model.py').open('x',encoding='utf-8',newline='\n') as f:f.write(source)
    entry=(BASE/'src/__main__.py').read_text().replace('from identity_model import run','from bounded_model import run').replace('PASS_OFFLINE_KERNEL_START_IDENTITY_ONLY','PASS_OFFLINE_BOUNDED_ROM_READ')
    with (ROOT/'src/__main__.py').open('x',encoding='utf-8',newline='\n') as f:f.write(entry)
    build=(BASE/'tools/build.py').read_text().replace('identity_model.py','bounded_model.py').replace('rk03_kernel_start_identity_offline.pyz','rk03_bounded_rom_read_offline.pyz')
    with (ROOT/'tools/build.py').open('x',encoding='utf-8',newline='\n') as f:f.write(build)
    print(json.dumps(dict(status='OFFLINE_FIXED_READ_DERIVED',frames=len(frames),actions=len(actions),request=request,expected_bytes_sha256=data_sha,response_frame_sha256=hashlib.sha256(bytes.fromhex(response)).hexdigest(),physical_operations=0)))
if __name__=='__main__':main()
