"""Derive fixed offline data only from individually named, already sealed evidence."""
from pathlib import Path
import copy, hashlib, json

ROOT=Path(__file__).resolve().parents[1]
ANALYSIS=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_kernel_identity_offline_20260930_01')
P=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_full_upload_physical_20260930_01')
F=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_full_upload_no_start_20260930_01')
K=Path(r'C:\Dev\A2WC511R_ReadKernel')
RAW=Path(r'C:\Dev\A2WC511R_RK03_FullUploadPhysical\physical_session\RK03_FULL_UPLOAD_NO_START_01\native_api.jsonl')

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p): return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
def normalized(x):
    if isinstance(x,list): return [normalized(v) for v in x]
    if isinstance(x,dict):
        return {k:normalized(v) for k,v in x.items() if k not in ('config_pointer','owned_buffer_pointer','timestamp')}
    return x
def message(template,wire,status=0):
    m=copy.deepcopy(template);m.update(data_hex=wire,data_size=len(bytes.fromhex(wire)),logged_bytes=len(bytes.fromhex(wire)),rx_status=status)
    return m

def main():
    expected={K/'build/rk02_01/kernel.bin':'3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581',
        K/'build/rk02_01/manifest.json':'a35562a19f21d4a2815e88fb729d21dd2cc08bf702c0d866f88ffc9e3ddb659e',
        K/'evidence/contracts/UPLOAD_WIRE_CONTRACT_RK02.json':'b1c5431141f9b249b16dd15938c290f20b99593e7ab8512caebcde1906c37f50',
        P/'physical_result/PHYSICAL_RESULT.json':'41d0b333b1fd01c43ae6f11154e33e10a1740f8d9735694d3895bb0e47b4d1a0',
        P/'physical_review/PHYSICAL_REVIEW.json':'bb7a189788c17fe4492c385c739d226065bc37a424c8bb4812cd8cc458406673',
        P/'oem_return_after_full_upload_01/OEM_RETURN_RESULT.json':'b1fe217fed67fcbe2de4e56f7d0f0b643939d7361534faaf5d7534c212d1ee4a'}
    for p,h in expected.items(): assert digest(p)==h,str(p)
    review=json.loads((P/'physical_review/PHYSICAL_REVIEW.json').read_text())
    raw_pin=next(v for v in review['source_evidence'] if v['path']==str(RAW))
    assert digest(RAW)==raw_pin['sha256']
    rows=[json.loads(line) for line in RAW.read_text().splitlines()]
    returns=[r for r in rows if r['type']=='api_return']
    assert len(returns)==85 and all(r['status']==0 for r in returns)
    actions=[]
    for r in returns[:-3]:
        a={'function':r['function'],'input':normalized(r['input']),'output':normalized(r['output']),'source_sequence':r['sequence']}
        if r['function']=='MonotonicMinimumWait':
            a={'function':'VirtualWait','input':{'milliseconds':r['input']['milliseconds'],'reason':r['input']['reason']},'output':{},'source_sequence':r['sequence']}
        actions.append(a)
    cleanup=[{'function':r['function'],'input':normalized(r['input']),'output':normalized(r['output'])} for r in returns[-3:]]
    writes=[a for a in actions if a['function']=='PassThruWriteMsgs']
    rx=[a for a in actions if a['function']=='PassThruReadMsgs' and a['output']['message']['rx_status']==0]
    assert len(writes)==len(rx)==22
    frames=[{'tx':a['input']['message']['data_hex'],'rx':b['output']['message']['data_hex']} for a,b in zip(writes,rx)]
    chunks=json.loads((F/'FIXED_UPLOAD_MANIFEST.json').read_text())
    assert [f['tx'] for f in frames[7:]]==[c['wire_hex'] for c in chunks['chunks']]
    wire_contract=json.loads((K/'evidence/contracts/UPLOAD_WIRE_CONTRACT_RK02.json').read_text())
    assert frames[6:]==[{'tx':r['request'],'rx':r['reply_from_executed_TDR']} for r in wire_contract['frames'][:16]]
    start=wire_contract['frames'][16]
    manifest=json.loads((K/'build/rk02_01/manifest.json').read_text())
    def beef(payload):
        wire=b'\xbe\xef'+len(payload).to_bytes(2,'big')+payload
        return (wire+bytes([sum(wire)&255])).hex()
    identity={'tx':beef(b'\x01'),'rx':beef(b'\x81'+bytes.fromhex(manifest['protocol']['identity_hex']))}
    assert identity=={'tx':'beef000101af','rx':'beef000f8141325743353131522d524b3032005f'}
    frames += [{'tx':start['request'],'rx':start['reply_from_executed_TDR']},identity]
    def exchange(frame):
        w=copy.deepcopy(writes[-1]);w.pop('source_sequence');w['input']['message']=message(w['input']['message'],frame['tx']);w['output']['message']=message(w['output']['message'],frame['tx']);actions.append(w)
        s=copy.deepcopy(next(a for a in actions if a['function']=='PassThruReadMsgs' and a['output']['message']['rx_status']==2));s.pop('source_sequence',None);actions.append(s)
        r=copy.deepcopy(rx[-1]);r.pop('source_sequence');r['output']['message']=message(r['output']['message'],frame['rx']);actions.append(r)
    exchange(frames[22])
    # Retained reviewed host: after exact start ACK, stop OEM filter, set62500,
    # install fixed BEEF pass filter, then exactly one identity request.
    actions.append(copy.deepcopy(cleanup[0]))
    baud=copy.deepcopy(next(a for a in actions if a['function']=='PassThruIoctl' and a['input'].get('ioctl')==2 and a['input']['config']['owned_buffer_entries']==[{'parameter':1,'value':15625}]))
    baud.pop('source_sequence');baud['input']['config']['owned_buffer_entries'][0]['value']=62500;baud['output']['config']['owned_buffer_entries'][0]['value']=62500;actions.append(baud)
    filt=copy.deepcopy(next(a for a in actions if a['function']=='PassThruStartMsgFilter'));filt.pop('source_sequence');filt['input']['flow_present']=False;filt['input']['flow']=None;filt['output']['flow']=None
    for side in ('input','output'):
        filt[side]['mask']=message(filt[side]['mask'],'ffff');filt[side]['pattern']=message(filt[side]['pattern'],'beef')
    actions.append(filt)
    exchange(frames[23])
    contract={'schema':1,'artifact':'RK03_KERNEL_START_IDENTITY_ONLY','physical':False,'kind':'STATIC_FAKE_TRANSCRIPT_MODEL',
        'entry':'FFFF3004','image_sha256':manifest['kernel_sha256'],'image_bytes':1808,
        'version_ascii':manifest['protocol']['identity_ascii'],'start_frame':frames[22]['tx'],'start_ack':frames[22]['rx'],
        'identity_request':identity['tx'],'identity_reply':identity['rx'],'actions':actions,'cleanup':cleanup,'frames':frames,
        'prefix_actions':82,'prefix_transmits':22,'maximum_transmits':24,'start_count':1,'identity_count':1,
        'seed_behavior':'FIXED_CAPTURED_SEED_AND_KEY_TRANSCRIPT; arbitrary-seed algorithm qualification reused, not rerun',
        'full_upload_chunks':chunks['chunks']}
    canonical=json.dumps(contract,sort_keys=True,separators=(',',':'))
    ROOT.joinpath('src').mkdir(parents=True,exist_ok=True)
    with (ROOT/'src/fixed_data.py').open('x',encoding='utf-8',newline='\n') as f:
        f.write('# Generated fixed offline data. No external input or provider.\nCONTRACT_SHA256 = '+repr(hashlib.sha256(canonical.encode()).hexdigest())+'\nCONTRACT_JSON = '+repr(canonical)+'\n')
    save(ROOT/'contract/CONTRACT.json',contract)
    save(ROOT/'contract/SOURCE_PINS.json',{'inputs':[pin(p) for p in expected]+[pin(RAW),pin(F/'FIXED_UPLOAD_MANIFEST.json'),pin(K/'host/physical_build/rk02_physical_01/native_physical.cpp')],
        'normalizations':['remove captured process pointer addresses and provider timestamps','represent reviewed200/100/200ms waits as virtual minimums','new start/identity replies are pinned model expectations, not physical evidence'],
        'reused_offline_qualification':'287/287; unchanged history not rerun','physical_invocations_this_scope':0})
    save(ANALYSIS/'CHECKPOINT.json',{'status':'CONTRACT_RECOVERED_OFFLINE_IMPLEMENTATION_IN_PROGRESS','physical_operations':0,'contract':pin(ROOT/'contract/CONTRACT.json')})
    note='''# Current status and supersession\n\nThe full-upload/no-start physical stage and subsequent passive OEM return passed. Earlier NOT RUN or QUALIFIED_NOT_AUTHORIZED_NOT_RUN labels describe historical checkpoints and are superseded; sealed historical files remain unchanged.\n\nThis scope is OFFLINE ONLY RK03_KERNEL_START_IDENTITY_ONLY. No provider access, physical authorization or new vehicle operation is included. The pinned kernel still identifies as A2WC511R-RK02 with a trailing NUL. This stage does not change that image.\n\nThe static model reproduces captured full-upload API semantics and extends them with the retained fixed start/identity contract. It is a deterministic engineering model, not a native physical executable or a replacement qualification of the prior transport host.\n'''
    with (ANALYSIS/'STATUS_SUPERSESSION.md').open('x',encoding='utf-8') as f:f.write(note)
    print(json.dumps({'status':'CONTRACT_RECOVERED','actions':len(actions),'frames':len(frames),'contract_sha256':hashlib.sha256(canonical.encode()).hexdigest()}))
if __name__=='__main__': main()
