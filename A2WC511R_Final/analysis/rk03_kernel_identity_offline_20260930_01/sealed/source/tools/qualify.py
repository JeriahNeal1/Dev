"""Offline-only qualification of the new bounded model, not prior native stages."""
from pathlib import Path
import ast,gzip,hashlib,json,subprocess,sys,zipfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_kernel_identity_offline_20260930_01\qualification_tests')
sys.path.insert(0,str(ROOT/'src'))
import identity_model as model

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    OUT.mkdir(exist_ok=False)
    rows=[]
    c=json.loads((ROOT/'contract/CONTRACT.json').read_text())
    def record(name,ok,detail):
        row={'case':name,'pass':bool(ok),'detail':detail};rows.append(row)
        if not ok:raise AssertionError(name+': '+str(detail))
    good=model.run()
    (OUT/'POSITIVE_RESULT.json').write_text(json.dumps(good,indent=2,sort_keys=True)+'\n')
    record('positive_complete_cleanup',good['status']=='PASS_OFFLINE_KERNEL_START_IDENTITY_ONLY' and good['cleanup_confirmed'],{'tx':good['tx_attempts'],'acks':good['acknowledged_exchanges']})
    writes=[r for r in good['journal'] if r['function']=='PassThruWriteMsgs']
    wires=[r['input']['message']['data_hex'] for r in writes]
    source_pin=next(p for p in json.loads((ROOT/'contract/SOURCE_PINS.json').read_text())['inputs'] if p['path'].endswith('native_api.jsonl'))
    source=Path(source_pin['path']);assert sha(source.read_bytes())==source_pin['sha256']
    old=[json.loads(l) for l in source.read_text().splitlines()]
    oldwrites=[r['input']['message']['data_hex'] for r in old if r['type']=='api_return' and r['function']=='PassThruWriteMsgs']
    record('exact_physical_upload_prefix',len(oldwrites)==22 and wires[:22]==oldwrites,{'physical_log_sha256':source_pin['sha256']})
    record('exact_start_and_identity_only_suffix',wires[22:]==['8010f003310101b6','beef000101af'],wires[22:])
    acknowledgements=[r['output']['message']['data_hex'] for r in good['journal'] if r['function']=='PassThruReadMsgs' and r['output']['message']['rx_status']==0]
    record('exact_fixed_replies',acknowledgements[7:22]==['80f0100176f7']*15 and acknowledgements[22:]==['80f01003710101f6','beef000f8141325743353131522d524b3032005f'],acknowledgements[22:])
    record('stop_after_identity',good['journal'][-4]['source_action']==90 and [r['function'] for r in good['journal'][-3:]]==['PassThruStopMsgFilter','PassThruDisconnect','PassThruClose'],{'final_protocol_action':90})
    for n,ch in enumerate(c['full_upload_chunks']):
        w=bytes.fromhex(wires[n+7]);address=0xFF000000|int.from_bytes(w[5:8],'big');cipher=w[8:-1]
        record('fixed_chunk_'+str(n+1),address==0xFFFF3000+n*128 and len(cipher)==(128 if n<14 else 16) and sha(cipher)==ch['cipher_payload_sha256'] and sha(w)==ch['wire_frame_sha256'],{'address':f'{address:08X}','length':len(cipher),'sha256':sha(cipher)})
    for n,w in enumerate(wires+acknowledgements):
        b=bytes.fromhex(w);length=int.from_bytes(b[2:4],'big') if b[:2]==b'\xbe\xef' else b[3]
        record('frame_checksum_length_'+str(n),sum(b[:-1])&255==b[-1] and len(b)==length+5,{'bytes':len(b)})
    setup=c['actions'][:10]
    actual=[a['input']['config']['owned_buffer_entries'] for a in setup if a['function']=='PassThruIoctl' and a['input']['ioctl']==2]
    serial=[[{'parameter':p,'value':v}] for p,v in [(22,0),(7,1),(10,0),(12,0),(3,0)]]
    record('retained_five_serial_sets',actual==serial,actual)
    record('retained_effective_readback',setup[8]['output']['config']['owned_buffer_entries']==[x[0] for x in serial],setup[8]['output']['config'])
    record('retained_broad_filter',all(setup[9]['input'][k]['data_hex']=='00000000' for k in ('mask','pattern','flow')),setup[9]['input'])
    waits=[(i,a['input']['milliseconds']) for i,a in enumerate(c['actions']) if a['function']=='VirtualWait']
    record('virtual_wait_contract',[v for _,v in waits]==[200,100,200] and good['virtual_ms']==500,waits)
    baud=[a['input']['config']['owned_buffer_entries'] for a in c['actions'] if a['function']=='PassThruIoctl' and a['input'].get('ioctl')==2][-2:]
    record('baud_transition_contract',baud==[[{'parameter':1,'value':15625}],[{'parameter':1,'value':62500}]],baud)
    record('fixed_start_identity_transition',[(a['function'],a['input'].get('ioctl')) for a in c['actions'][85:88]]==[('PassThruStopMsgFilter',None),('PassThruIoctl',2),('PassThruStartMsgFilter',None)],c['actions'][85:88])
    record('fixed_BEEF_filter',c['actions'][87]['input']['mask']['data_hex']=='ffff' and c['actions'][87]['input']['pattern']['data_hex']=='beef' and c['actions'][87]['input']['flow'] is None,c['actions'][87]['input'])
    # Injection matrix operates on the new artifact only. Previous287native tests
    # remain reused evidence; their count is not added to this new result.
    cases=[]
    for i in range(94): cases += [('api_failure',i),('output_mismatch',i)]
    for i,a in enumerate(c['actions']):
        if a['function'] in ('PassThruWriteMsgs','PassThruReadMsgs'):cases.append(('count_zero',i))
        if a['function']=='PassThruReadMsgs' and a['output']['message']['rx_status']==0:
            cases += [(f,i) for f in ('bad_checksum','wrong_ack','truncated','wrong_length','wrong_rx_status','wrong_protocol','trailing_bytes')]
        if a['function']=='VirtualWait':cases.append(('short_wait',i))
    cases += [('wrong_identity',90),('wrong_version',90)]
    packed=[]
    for mode,idx in cases:
        r=model.run(mode,idx);j=r['journal'];attempts=[v for v in j if v['function']=='PassThruWriteMsgs']
        attempted_wires=[v['input']['message']['data_hex'] for v in attempts]
        require_prefix=attempted_wires==wires[:len(attempted_wires)]
        hits=[v for v in j if v['source_action']==idx]
        after=[v for v in j if v['source_action']>idx and not v['cleanup']]
        releases=[v['function'] for v in j if v['cleanup']]
        record(mode+'_'+str(idx),r['status']=='FAIL_TERMINAL' and require_prefix and len(hits)==1 and not after and len(attempted_wires)<=24 and len(releases)==len(set(releases)) and r['retry_count']==0,
            {'fault_action':idx,'tx':len(attempted_wires),'cleanup_confirmed':r['cleanup_confirmed'],'failure':r['failure'],'cleanup_errors':r['cleanup_errors'],'result_sha256':sha(json.dumps(r,sort_keys=True,separators=(',',':')).encode())})
        packed.append({'mode':mode,'action':idx,'result':r})
    (OUT/'NEGATIVE_JOURNALS.json.gz').write_bytes(gzip.compress(json.dumps(packed,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    # Inspect only the exact three-file distributable closure.
    imports=[];forbidden=[]
    for name in ('identity_model.py','fixed_data.py','__main__.py'):
        tree=ast.parse((ROOT/'src'/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports += [n.name for n in node.names]
            if isinstance(node,ast.ImportFrom):imports.append(node.module)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('open','exec','eval','compile','__import__','input'):forbidden.append(node.func.id)
    record('structural_closed_imports',set(imports)<={'hashlib','json','sys','fixed_data','identity_model'},imports)
    record('structural_no_external_IO_or_execution',not forbidden,forbidden)
    # No command dispatch beyond the fixed frame whitelist; these are the only
    # modeled emissions, not strings passed to any callable external API.
    commands=[bytes.fromhex(w)[4] for w in wires[:23]]
    record('structural_fixed_emit_alphabet',commands==[0xbf,0x81,0x83,0x27,0x27,0x10,0x34]+[0x36]*15+[0x31],commands)
    record('structural_no_read_or_flash_command',wires[23]=='beef000101af' and len(wires)==24,{'kernel_command':1,'kernel_command3_absent':True})
    for label in ('a','b'):
        artifact=ROOT/('build_'+label)/'rk03_kernel_start_identity_offline.pyz'
        with zipfile.ZipFile(artifact) as z:record('closed_build_'+label,z.namelist()==['__main__.py','fixed_data.py','identity_model.py'],z.namelist())
        executed=subprocess.run([sys.executable,'-I','-B',str(artifact)],capture_output=True,text=True,check=False)
        record('built_model_execution_'+label,executed.returncode==0 and json.loads(executed.stdout)==good,{'returncode':executed.returncode,'stderr':executed.stderr})
        for option in ('--physical','--entry','--payload','--provider'):
            rejected=subprocess.run([sys.executable,'-I','-B',str(artifact),option],capture_output=True,text=True,check=False)
            record('reject_cli_'+label+option,rejected.returncode==2 and rejected.stdout=='',{'returncode':rejected.returncode})
    a=ROOT/'build_a';b=ROOT/'build_b'
    record('two_clean_artifacts_identical',(a/'rk03_kernel_start_identity_offline.pyz').read_bytes()==(b/'rk03_kernel_start_identity_offline.pyz').read_bytes(),{'sha256':sha((a/'rk03_kernel_start_identity_offline.pyz').read_bytes())})
    record('two_clean_manifests_identical',(a/'BUILD_MANIFEST.json').read_bytes()==(b/'BUILD_MANIFEST.json').read_bytes(),{'sha256':sha((a/'BUILD_MANIFEST.json').read_bytes())})
    report={'status':'PASS','scope':'NEW_OFFLINE_IDENTITY_MODEL_ONLY','physical_operations':0,'test_count':len(rows),'passed':sum(r['pass'] for r in rows),'negative_cases':len(cases),'tests':rows,'prior287qualification_reused_not_recounted':True}
    (OUT/'TEST_REPORT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tests'}))
if __name__=='__main__':main()
