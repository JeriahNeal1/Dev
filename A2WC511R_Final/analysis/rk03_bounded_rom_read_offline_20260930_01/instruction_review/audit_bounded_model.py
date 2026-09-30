"""Read-only independent audit of root's completed static-model qualification."""
from pathlib import Path
import ast, collections, datetime as dt, gzip, hashlib, json, zipfile
ROOT=Path(r'C:\Dev\A2WC511R_RK03_BoundedRomReadOffline\bounded_rom_read')
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_rom_read_offline_20260930_01')
OUT=A/'instruction_review'
checks=[];pins={}
def check(ok,detail):
    if not ok:raise AssertionError(detail)
    checks.append(detail)
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def bind(p,expected=None):
    q=pin(p)
    if expected:
        check(q['sha256']==expected['sha256'],'Hash '+q['path'])
        if 'bytes' in expected:check(q['bytes']==expected['bytes'],'Size '+q['path'])
    pins[q['path']]=q;return q
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def norm(v):
    if isinstance(v,list):return [norm(x) for x in v]
    if isinstance(v,dict):return {k:norm(x) for k,x in v.items() if k not in {'config_pointer','owned_buffer_pointer','timestamp'}}
    return v
def main():
    reportpath=A/'qualification_tests/TEST_REPORT.json';bind(reportpath,{'sha256':'133f89d03a49dc28e4640b67c11ee9af60217c1180d9633f0103f799afd6afcb'})
    report=read(reportpath)
    check(report['status']=='PASS' and report['tests']==report['passed']==122 and report['negative_fault_cases']==78,'Final122 checks/78 faults PASS')
    check(report['physical_operations']==report['provider_loads']==0 and report['prior_qualification_reused_not_recounted'],'New offline scope only')
    for p in report['source_inputs']+[report['runner'],report['artifact'],report['contract']]:bind(p['path'],p)
    for n in ['tools/derive_offline_artifact.py','tools/build.py','contract/SOURCE_PINS.json']:bind(ROOT/n)
    sourcepins=read(ROOT/'contract/SOURCE_PINS.json')
    for p in sourcepins['inputs']:bind(p['path'],p)
    names=['__main__.py','fixed_data.py','bounded_model.py'];imports=set();constants={}
    for name in names:
        p=ROOT/'src'/name;tree=ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.update(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):imports.add(node.module)
            elif isinstance(node,ast.Call):
                check(not isinstance(node.func,ast.Name) or node.func.id not in {'open','input','eval','exec','compile','__import__'},'No file/dynamic dispatch call '+name)
                check(not isinstance(node.func,ast.Attribute) or node.func.attr not in {'read_bytes','write_bytes','read_text','write_text','open','Popen','run','CDLL','WinDLL','LoadLibrary','system'},'No provider/process/filesystem attribute call '+name)
        if name=='fixed_data.py':
            check(all(isinstance(x,ast.Assign) for x in tree.body),'Fixed data contains assignments only')
            constants={x.targets[0].id:ast.literal_eval(x.value) for x in tree.body}
    check(imports=={'hashlib','json','sys','fixed_data','bounded_model'},'Closed three-source import set')
    check(hashlib.sha256(constants['CONTRACT_JSON'].encode()).hexdigest()==constants['CONTRACT_SHA256'],'Embedded contract digest')
    c=read(ROOT/'contract/CONTRACT.json');check(json.loads(constants['CONTRACT_JSON'])==c,'Embedded contract equals readable contract')
    check(len(c['frames'])==25 and len(c['actions'])==94 and len(c['cleanup'])==3 and c['physical'] is False,'Fixed dimensions and offline scope')
    fixed=read(OUT/'FIXED_READ_CONTRACT.json');bind(OUT/'FIXED_READ_CONTRACT.json')
    rootfixed=read(A/'ROOT_FIXED_READ_CONTRACT.json');bind(A/'ROOT_FIXED_READ_CONTRACT.json')
    check(c['frames'][24]=={'tx':fixed['request_hex'],'rx':fixed['reply_hex']},'Root model matches independently recovered wire contract')
    check(rootfixed['request']==fixed['request_hex'] and rootfixed['response']==fixed['reply_hex'] and rootfixed['expected_bytes_sha256']==fixed['data_sha256'],'Independent contract derivations agree')
    rawpin=next(p for p in sourcepins['inputs'] if p['path'].endswith('native_api.jsonl'))
    raw=[json.loads(s) for s in Path(rawpin['path']).read_text().splitlines()]
    ret=[r for r in raw if r.get('type')=='api_return'];check(len(ret)==94 and all(r['status']==0 for r in ret),'Pinned successful physical prefix')
    projected=[]
    for r in ret[:-3]:
        projected.append({'function':r['function'],'input':norm(r['input']),'output':norm(r['output']),'source_sequence':r['sequence']})
        if r['function']=='MonotonicMinimumWait':projected[-1]={'function':'VirtualWait','input':{'milliseconds':r['input']['milliseconds'],'reason':r['input']['reason']},'output':{},'source_sequence':r['sequence']}
    check(c['actions'][:91]==projected,'All91 prefix actions match declared normalization of physical evidence')
    physicalwires=[r['input']['message']['data_hex'] for r in ret if r['function']=='PassThruWriteMsgs']
    check([f['tx'] for f in c['frames'][:24]]==physicalwires,'All24 prior physical TX unchanged including captured seed/key')
    check(c['frames'][4]['tx']=='8010f0062702349c6319fb' and c['frames'][3]['rx']=='80f010066701b8808513be','Captured seed/key provenance explicit')
    check(c['cleanup']==[{'function':r['function'],'input':norm(r['input']),'output':norm(r['output'])} for r in ret[-3:]],'Cleanup contract unchanged from physical suffix')
    expected=bytes.fromhex(fixed['data_hex']);bind(A/'EXPECTED_FIRST512_CURRENT.bin')
    check((A/'EXPECTED_FIRST512_CURRENT.bin').read_bytes()==expected and len(expected)==512,'Fixed expected512-byte artifact')
    for stage,f in enumerate(c['frames']):
        for kind in ['tx','rx']:
            b=bytes.fromhex(f[kind]);check(b[-1]==sum(b[:-1])%256,'Checksum '+str(stage)+kind)
            length=int.from_bytes(b[2:4],'big') if stage>=23 else b[3]
            check(len(b)==length+5,'Length '+str(stage)+kind)
    check([bytes.fromhex(f['tx'])[4] for f in c['frames']]==[0xbf,0x81,0x83,0x27,0x27,0x10,0x34]+[0x36]*15+[0x31,1,3],'Exact emit alphabet with one read and no flash')
    text=(ROOT/'src/bounded_model.py').read_text();call=text.index('output=call(action,ordinal)');gate=text.index("require(output==action['output'],'Exact captured/model output contract')")
    check(call<gate<text.index("if function=='PassThruReadMsgs':",call),'Corrected exact-output acceptance precedes all reply flag changes')
    check('len(sys.argv)!=1' in (ROOT/'src/__main__.py').read_text(),'Distributable CLI rejects all arguments')
    artifacts=[];manifests=[]
    for label in ('a','b'):
        path=ROOT/('build_'+label)/'rk03_bounded_rom_read_offline.pyz';bpath=path.with_name('BUILD_MANIFEST.json')
        artifacts.append(bind(path,{'sha256':'bf240d6c64257aca1952295c8a7bee03be714179124e002cdf45854d599aa0f6'}));manifests.append(bind(bpath))
        manifest=read(bpath);check(manifest['format']=='PYTHON_ZIPAPP_STATIC_OFFLINE_MODEL' and manifest['physical'] is False,'Build mode '+label)
        check(manifest['output']['sha256']==artifacts[-1]['sha256'] and manifest['build_script_sha256']==pin(ROOT/'tools/build.py')['sha256'],'Build output/script pins '+label)
        with zipfile.ZipFile(path) as z:
            check(z.namelist()==names,'Exactly three archive members '+label)
            for name in names:
                info=z.getinfo(name);data=z.read(name)
                check(data==(ROOT/'src'/name).read_bytes(),'Archive/source byte identity '+label+name)
                check(info.date_time==(1980,1,1,0,0,0) and info.compress_type==zipfile.ZIP_STORED and info.create_system==3 and info.external_attr==0o100644<<16,'Deterministic ZIP metadata '+label+name)
                row=next(x for x in manifest['source'] if x['name']==name);check(row['sha256']==hashlib.sha256(data).hexdigest() and row['bytes']==len(data),'Manifest source pin '+label+name)
    check(artifacts[0]['sha256']==artifacts[1]['sha256'] and manifests[0]['sha256']==manifests[1]['sha256'],'Both clean artifacts/manifests match')
    positivepath=A/'qualification_tests/POSITIVE_RESULT.json';negativepath=A/'qualification_tests/NEGATIVE_JOURNALS.json.gz'
    bind(positivepath);bind(negativepath);good=read(positivepath);neg=json.loads(gzip.decompress(negativepath.read_bytes()))
    check(good['status']=='PASS_OFFLINE_BOUNDED_ROM_READ' and good['identity_validated'] and good['bounded_read_validated'] and good['cleanup_confirmed'],'Recorded positive accepts read and closes resources')
    check(good['tx_attempts']==good['acknowledged_exchanges']==25 and good['ROM_read_requests']==1 and not any(good['remaining_resources'].values()),'Positive exact terminal counters')
    check(len(good['journal'])==97 and good['virtual_ms']==500,'Positive exact97 actions and virtual waits500ms')
    for n,j in enumerate(good['journal']):
        a=(c['actions']+c['cleanup'])[n]
        check(j['function']==a['function'] and j['input']==a['input'] and j['output']==a['output'] and j['status']==0 and j['source_action']==n and j['physical'] is False and j['cleanup']==(n>=94),'Positive exact recorded action '+str(n))
    expected_faults={(f,n) for n in range(82,97) for f in ['api_failure','output_mismatch']}
    expected_faults.update(('count_zero',n) for n in range(88,94))
    expected_faults.update((f,n) for n in [84,90,93] for f in ['bad_checksum','wrong_ack','truncated','wrong_length','wrong_rx_status','wrong_protocol','trailing_bytes'])
    expected_faults.update((f,90) for f in ['wrong_identity','wrong_version'])
    expected_faults.update((f,93) for f in ['wrong_read_pass','wrong_read_address','wrong_read_data','wrong_read_command'])
    ack_indices=[n for n,a in enumerate(c['actions']) if a['function']=='PassThruReadMsgs' and a['output']['message']['data_hex']=='80f0100176f7']
    check(len(ack_indices)==15,'All15 prerequisite ACK indices included')
    expected_faults.update(('api_failure',n) for n in ack_indices)
    check(len(neg)==len(expected_faults)==78 and {(x['fault'],x['ordinal']) for x in neg}==expected_faults,'Exact78 independent negative matrix')
    faultcounts=collections.Counter()
    for x in neg:
        f,n,r=x['fault'],x['ordinal'],x['result'];j=r['journal'];faultcounts[f]+=1
        check(r['status']=='FAIL_TERMINAL' and r['retry_count']==0 and r['physical'] is False,'Negative terminal '+f+str(n))
        tx=[y['input']['message']['data_hex'] for y in j if y['function']=='PassThruWriteMsgs']
        check(tx==[z['tx'] for z in c['frames'][:len(tx)]] and len(tx)<=25 and r['tx_attempts']==len(tx),'Negative fixed TX prefix '+f+str(n))
        hit=[y for y in j if y['source_action']==n];check(len(hit)==1,'Fault action reached once '+f+str(n))
        check(not any(y['source_action']>n and not y['cleanup'] for y in j),'Only cleanup after failure '+f+str(n))
        check(hit[0]['status']==16 if f=='api_failure' else hit[0]['output']!=(c['actions']+c['cleanup'])[n]['output'],'Fault actually injected '+f+str(n))
        cleanup=[y['function'] for y in j if y['cleanup']];check(len(cleanup)==len(set(cleanup)),'Cleanup targets attempted at most once '+f+str(n))
        if n<94:check(not r['bounded_read_validated'],'No premature read success flag '+f+str(n))
    pointer=read(OUT/'INSTRUCTION_REVIEW.json');bind(OUT/'INSTRUCTION_REVIEW.json');bind(pointer['replay']['path'],pointer['replay'])
    cpu=read(pointer['replay']['path'])
    check(cpu['status']=='PASS_ONE_FIXED_READ_FROM_RETAINED_IDENTITY_CHECKPOINT' and cpu['new_read_requests']==1 and cpu['instruction_count']==10327 and cpu['ROM_data_read_events']==512,'Completed narrow instruction replay')
    check(cpu['request_hex']==fixed['request_hex'] and cpu['response_hex']==fixed['reply_hex'] and cpu['response_sha256']==hashlib.sha256(bytes.fromhex(c['frames'][24]['rx'])).hexdigest(),'Actual CPU reply equals model reply')
    for p in cpu['inputs']+cpu['artifacts']:bind(p['path'],p)
    bind(OUT/'replay_one_fixed_read.py');bind(__file__)
    for p in list(pins.values()):check(pin(p['path'])==p,'Inspected input remained unchanged '+p['path'])
    summary={'schema':1,'status':'PASS_INDEPENDENT_OFFLINE_BOUNDED_READ_MODEL_REVIEW','utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'reviewer':'passive_review','roles':{'static_model_deriver_builder_and_tests':'root','independent_static_model_and_recorded_tests_reviewer':'passive_review','instruction_replay_author_and_executor':'passive_review','independent_instruction_replay_reviewer':'root'},
      'blocking_findings':[],'checks_passed':len(checks),'checks':checks,'inspected_pins':list(pins.values()),
      'qualification_summary':{'checks':122,'negative_cases':78,'fault_counts':dict(faultcounts),'new_stage_only':True,'prior_qualifications_reused':True},
      'artifact_sha256':artifacts[0]['sha256'],'contract_sha256':pin(ROOT/'contract/CONTRACT.json')['sha256'],
      'fixed_request_hex':fixed['request_hex'],'fixed_response_sha256':fixed['reply_sha256'],'fixed_data_sha256':fixed['data_sha256'],
      'first_supported_address':'00000000','bytes':512,'cursor_after':'00000200','pass':0,'stock_range_equal':True,
      'CPU_replay_instructions':10327,'CPU_ROM_byte_reads':512,'CPU_upload_start_identity_instructions_reexecuted':0,
      'new_model_protocol_TX':25,'physical_operations':0,'provider_loads':0,'model_or_native_invocations_by_review_audit':0,
      'findings':['The unchanged kernel enforces512-byte sequential reads. The first legal block follows identity at address0/pass0;16-byte or direct CAL-ID requests are invalid.',
        'All91 captured physical prefix actions and24 transmissions are retained with explicit pointer/timestamp normalization and virtual-wait substitution. Only the25th exchange is synthetic.',
        'Exactly one fixed read is reachable in the closed three-source zipapp. It has no provider/backend/path/address/payload interface; API names are data strings.',
        'Independent instruction execution emits the exact523-byte reply from512 one-byte ROM loads, advances the cursor once and stops at RX_WAIT; no flash write or kernel mutation occurs.',
        'All78 recorded fault cases genuinely inject a fault, stop protocol continuation, use only the fixed TX prefix and attempt cleanup without retry. Final corrected source validates exact output before any ACK/identity/read flag advancement.',
        'Two clean final archives and manifests match; archive members equal the reviewed source bytes. Initial reporting-order defect was isolated to preserved draft evidence.'],
      'limits':['This qualifies a static fake transcript model, not a native ABI/parser/fragmentation/deadline implementation or a physical ROM-read release.',
        'The fixed captured seed/key is reused; this model does not newly qualify a general seed algorithm.',
        'CPU continuation uses a reconstructed retained register/private-RAM/peripheral checkpoint. Its explicit instruction-tick, SCI and self-echo assumptions are model evidence, not physical timing.',
        'The first512 bytes equal both authoritative current.bin and preserved stock; they cannot distinguish the complete current calibration image.',
        'Only one block is modeled/executed. No second read, full acquisition, image classification, calibration change, flash, provider load or vehicle operation was performed.',
        'This reviewer authored the instruction replay but independently reviewed root-authored model/tests. Root separately reviews the instruction replay; roles are not conflated.']}
    p=OUT/'INDEPENDENT_REVIEW.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(summary,f,indent=2);f.write('\n')
    print(json.dumps({'status':summary['status'],'checks_passed':len(checks),'pins':len(pins),'report':pin(p)}))
if __name__=='__main__':main()
