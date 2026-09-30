"""Qualify only the new offline fixed-read model; never a physical executable."""
from pathlib import Path
import ast,copy,gzip,hashlib,inspect,json,subprocess,sys,zipfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_rom_read_offline_20260930_01\qualification_tests')
sys.path.insert(0,str(ROOT/'src'))
import bounded_model as model
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
def normalize(x):
    if isinstance(x,list):return [normalize(v) for v in x]
    if isinstance(x,dict):return {k:normalize(v) for k,v in x.items() if k not in ('config_pointer','owned_buffer_pointer','timestamp')}
    return x
def main():
    OUT.mkdir(exist_ok=False);checks=[]
    def record(name,ok,detail=None):
        checks.append(dict(case=name,pass_case=bool(ok),detail=detail))
        if not ok:raise AssertionError(name+': '+str(detail))
    c=json.loads((ROOT/'contract/CONTRACT.json').read_text());pins=json.loads((ROOT/'contract/SOURCE_PINS.json').read_text())
    for p in pins['inputs']:assert sha(Path(p['path']).read_bytes())==p['sha256'],p['path']
    good=model.run();journal=good['journal'];writes=[r for r in journal if r['function']=='PassThruWriteMsgs']
    wires=[r['input']['message']['data_hex'] for r in writes]
    record('success_one_bounded_read_then_cleanup',good['status']=='PASS_OFFLINE_BOUNDED_ROM_READ' and good['bounded_read_validated'] and good['identity_validated'] and good['cleanup_confirmed'] and good['ROM_read_requests']==1 and good['tx_attempts']==good['acknowledged_exchanges']==25,{'tx':good['tx_attempts'],'bytes':good['fixed_ROM_length']})
    raw_pin=next(p for p in pins['inputs'] if p['path'].endswith('native_api.jsonl'))
    ret=[r for r in map(json.loads,Path(raw_pin['path']).read_text().splitlines()) if r.get('type')=='api_return']
    projected=[]
    for r in ret[:-3]:
        a={'function':r['function'],'input':normalize(r['input']),'output':normalize(r['output']),'source_sequence':r['sequence']}
        if r['function']=='MonotonicMinimumWait':a={'function':'VirtualWait','input':{'milliseconds':r['input']['milliseconds'],'reason':r['input']['reason']},'output':{},'source_sequence':r['sequence']}
        projected.append(a)
    record('reuse_exact_latest_physical_identity_prefix',len(projected)==91 and c['actions'][:91]==projected,raw_pin)
    record('retained24TX_and_single_new_request',wires[:24]==[r['input']['message']['data_hex'] for r in ret if r['function']=='PassThruWriteMsgs'] and wires[24:]==['beef00080300000000000200ba'],wires[22:])
    frame=bytes.fromhex(wires[24]);body=frame[4:-1]
    record('fixed_request_address_length_pass_encoding',body==b'\x03\x00'+(0).to_bytes(4,'big')+(512).to_bytes(2,'big') and len(frame)==13 and int.from_bytes(frame[2:4],'big')==8,frame.hex())
    record('request_checksum',frame[-1]==sum(frame[:-1])%256,frame[-1])
    reply=bytes.fromhex(c['frames'][24]['rx'])
    record('fixed_response_framing_and_echo_fields',reply[:10]==bytes.fromhex('beef0206830000000000') and len(reply)==523 and int.from_bytes(reply[2:4],'big')==518,reply[:10].hex())
    record('response_checksum',reply[-1]==sum(reply[:-1])%256==0xe7,reply[-1])
    rom_pin=next(p for p in pins['inputs'] if p['path'].endswith('current.bin'))
    current=Path(rom_pin['path']).read_bytes()
    record('actual_current_ROM_first512_bytes',reply[10:-1]==current[:512] and len(reply[10:-1])==512 and sha(reply[10:-1])=='d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01',{'current_ROM_sha256':rom_pin['sha256'],'region_sha256':sha(reply[10:-1])})
    chunks=c['full_upload_chunks'];ok=True
    for i,row in enumerate(chunks):
        w=bytes.fromhex(wires[i+7]);ok &= (0xFF000000|int.from_bytes(w[5:8],'big'))==0xFFFF3000+i*128 and len(w[8:-1])==(128 if i<14 else 16) and sha(w[8:-1])==row['cipher_payload_sha256'] and sha(w)==row['wire_frame_sha256']
    record('all15_upload_chunks_unchanged',len(chunks)==15 and ok,c['image_sha256'])
    record('one_start_one_identity_before_one_read',wires[22:]==['8010f003310101b6','beef000101af','beef00080300000000000200ba'],wires[22:])
    record('stop_immediately_after_first_read_reply',journal[-4]['source_action']==93 and [r['function'] for r in journal[-3:]]==['PassThruStopMsgFilter','PassThruDisconnect','PassThruClose'],[r['function'] for r in journal[-4:]])
    record('fixed_signature_no_address_payload_backend',str(inspect.signature(model.run))=="(fault='none', fault_step=-1)",str(inspect.signature(model.run)))
    read_action=93
    cases=[]
    # New suffix and its immediate prerequisites; prior native qualification is
    # reused rather than rerun/recounted. All retained blockACK boundaries are
    # sampled to show none can reach the new read following a failure.
    for i in [*range(82,97)]:cases += [('api_failure',i),('output_mismatch',i)]
    for i in (88,89,90,91,92,93):cases.append(('count_zero',i))
    for i in (84,90,93):
        cases += [(f,i) for f in ('bad_checksum','wrong_ack','truncated','wrong_length','wrong_rx_status','wrong_protocol','trailing_bytes')]
    cases += [('wrong_identity',90),('wrong_version',90)]
    cases += [(f,93) for f in ('wrong_read_pass','wrong_read_address','wrong_read_data','wrong_read_command')]
    ack_indices=[i for i,a in enumerate(c['actions']) if a['function']=='PassThruReadMsgs' and a['output']['message']['data_hex']=='80f0100176f7']
    assert len(ack_indices)==15
    cases += [('api_failure',i) for i in ack_indices]
    packed=[]
    for fault,ordinal in cases:
        result=model.run(fault,ordinal);j=result['journal'];tx=[r['input']['message']['data_hex'] for r in j if r['function']=='PassThruWriteMsgs']
        hits=[r for r in j if r['source_action']==ordinal]
        later=[r for r in j if r['source_action']>ordinal and not r['cleanup']]
        cleanup=[r['function'] for r in j if r['cleanup']]
        ok=result['status']=='FAIL_TERMINAL' and tx==wires[:len(tx)] and len(hits)==1 and not later and len(tx)<=25 and len(set(cleanup))==len(cleanup) and result['retry_count']==0
        if ordinal<94:ok &= not result['bounded_read_validated']
        record('negative_'+fault+'_'+str(ordinal),ok,dict(tx=len(tx),failure=result['failure'],cleanup_errors=result['cleanup_errors'],cleanup_confirmed=result['cleanup_confirmed']))
        packed.append(dict(fault=fault,ordinal=ordinal,result=result))
    for args in [('none',0),('arbitrary',-1),('api_failure',-2),('api_failure',97),('api_failure',True)]:
        rejected=False
        try:model.run(*args)
        except model.ModelFailure:rejected=True
        record('reject_invalid_fault_arguments_'+repr(args),rejected)
    for key in ['address','payload','provider','backend','entry']:
        rejected=False
        try:model.run(**{key:0})
        except TypeError:rejected=True
        record('no_dynamic_parameter_'+key,rejected)
    changed=copy.deepcopy(c);changed['frames'][24]['tx']='beef00080300000002000200bc'
    original=model.CONTRACT_JSON
    try:
        model.CONTRACT_JSON=json.dumps(changed,sort_keys=True,separators=(',',':'))
        rejected=False
        try:model.run()
        except model.ModelFailure:rejected=True
        record('changed_address_contract_rejected_before_actions',rejected)
    finally:model.CONTRACT_JSON=original
    imports=[];forbidden=[]
    for name in ['__main__.py','fixed_data.py','bounded_model.py']:
        tree=ast.parse((ROOT/'src'/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(v.name for v in node.names)
            if isinstance(node,ast.ImportFrom):imports.append(node.module)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ['open','exec','eval','compile','__import__','input']:forbidden.append(node.func.id)
    record('closed_distributable_imports',set(imports)<={'hashlib','json','sys','fixed_data','bounded_model'},imports)
    record('no_physical_loader_filesystem_or_dynamic_execution_calls',not forbidden,forbidden)
    record('fixed_emit_alphabet_and_no_second_read',len(wires)==25 and [bytes.fromhex(w)[4] for w in wires]==[0xbf,0x81,0x83,0x27,0x27,0x10,0x34]+[0x36]*15+[0x31,1,3],{'transmits':len(wires),'read_requests':1,'flash_operations':0})
    for label in ('a','b'):
        artifact=ROOT/('build_'+label)/'rk03_bounded_rom_read_offline.pyz'
        with zipfile.ZipFile(artifact) as z:record('closed_archive_'+label,z.namelist()==['__main__.py','fixed_data.py','bounded_model.py'],z.namelist())
        cp=subprocess.run([sys.executable,'-I','-B',str(artifact)],capture_output=True,text=True)
        record('built_model_'+label,cp.returncode==0 and json.loads(cp.stdout)==good,{'returncode':cp.returncode})
        for option in ['--physical','--provider','--address','--length','--payload','--entry']:
            cp=subprocess.run([sys.executable,'-I','-B',str(artifact),option],capture_output=True,text=True)
            record('reject_CLI_'+label+option,cp.returncode==2 and cp.stdout=='',{'returncode':cp.returncode})
    record('two_clean_artifacts_identical',(ROOT/'build_a/rk03_bounded_rom_read_offline.pyz').read_bytes()==(ROOT/'build_b/rk03_bounded_rom_read_offline.pyz').read_bytes(),pin(ROOT/'build_a/rk03_bounded_rom_read_offline.pyz'))
    record('two_clean_manifests_identical',(ROOT/'build_a/BUILD_MANIFEST.json').read_bytes()==(ROOT/'build_b/BUILD_MANIFEST.json').read_bytes(),pin(ROOT/'build_a/BUILD_MANIFEST.json'))
    (OUT/'POSITIVE_RESULT.json').write_text(json.dumps(good,sort_keys=True,indent=2)+'\n')
    (OUT/'NEGATIVE_JOURNALS.json.gz').write_bytes(gzip.compress(json.dumps(packed,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    report=dict(status='PASS',scope='NEW_OFFLINE_FIXED_FIRST512_READ_MODEL_ONLY',tests=len(checks),passed=sum(x['pass_case'] for x in checks),negative_fault_cases=len(cases),physical_operations=0,provider_loads=0,prior_qualification_reused_not_recounted=True,checks=checks,source_inputs=[pin(p) for p in sorted((ROOT/'src').iterdir()) if p.is_file()],runner=pin(Path(__file__)),artifact=pin(ROOT/'build_a/rk03_bounded_rom_read_offline.pyz'),contract=pin(ROOT/'contract/CONTRACT.json'))
    (OUT/'TEST_REPORT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['checks','source_inputs']}))
if __name__=='__main__':main()
