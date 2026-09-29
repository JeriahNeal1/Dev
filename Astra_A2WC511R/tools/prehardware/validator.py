"""Fail-closed, read-only prehardware image validation. No device or flash API.

Exit codes: 0 PASS, 2 CONDITIONAL, 3 FAIL. PASS is an offline evidence result,
never permission to flash. Only the hash-pinned project registry is trusted.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import argparse, hashlib, json, struct, subprocess
from bisect import bisect_left
from pathlib import Path

HERE=Path(__file__).resolve().parent
REGISTRY_SHA256='e715887f064e605371f3d413beba55876a62fe0290c4da6aefee9e85e0a7a861'
SIZE=0x100000
def digest(b):return hashlib.sha256(b).hexdigest()
def hx(a):return f'0x{a:08X}'
def read(path):return Path(path).read_bytes()
def status(checks):return 'FAIL' if any(c['status']=='FAIL' for c in checks) else 'CONDITIONAL' if any(c['status']=='CONDITIONAL' for c in checks) else 'PASS'
def load_registry(path=None):
    p=Path(path) if path else HERE/'validator_registry.json'
    raw=p.read_bytes()
    if digest(raw)!=REGISTRY_SHA256:raise ValueError('Project registry hash mismatch; caller assertions cannot supply approval')
    d=json.loads(raw)
    if d.get('schema')!=1:raise ValueError('Unsupported project registry schema')
    return d
def check_files(items,reader=read):
    bad=[]
    for p,h in items.items():
        try:
            actual=digest(reader(p))
            if actual!=h:bad.append({'path':p,'expected':h,'actual':actual})
        except OSError as e:bad.append({'path':p,'error':str(e)})
    return bad
def checksum_rows(data):
    rows=[]
    for p in range(0xFFB80,0xFFC28,12):
        start,end,stored=struct.unpack_from('>III',data,p)
        if start%4 or start>end or end>SIZE:raise ValueError(f'Malformed descriptor at {p:X}')
        effective=start+((end-start+3)//4)*4
        if effective>SIZE or (start<=p+8<end):raise ValueError(f'Invalid region at {p:X}')
        summed=sum(struct.unpack_from('>I',data,i)[0] for i in range(start,end,4))&0xFFFFFFFF
        expected=(0x5AA5A55A-summed)&0xFFFFFFFF
        rows.append(dict(offset=p,start=start,end_parameter=end,effective_end_exclusive=effective,stored=stored,expected=expected,valid=stored==expected))
    return rows
def direct_branch(w,pc):
    if w>>12 in (10,11):
        v=w&4095;return pc+4+2*(v-4096 if v&2048 else v)
    if w&0xFF00 in (0x8900,0x8B00,0x8D00,0x8F00):
        v=w&255;return pc+4+2*(v-256 if v&128 else v)
    return None
def delayed(w):return w>>12 in (10,11) or w&0xFF00 in (0x8D00,0x8F00) or w&0xF0FF in (0x400B,0x402B) or w in (0x000B,0x002B)
def transfer(w):return delayed(w) or w&0xFF00 in (0x8900,0x8B00)

def evaluate(data,registry,artifact_name=None,reader=read):
    """Pure image/evidence checks; artifact_name selects requirements, not trust."""
    checks=[]
    def add(cid,ok,detail,scope=None):
        checks.append(dict(id=cid,status=ok if isinstance(ok,str) else 'PASS' if ok else 'FAIL',detail=detail,**({'scope':scope} if scope else {})))
    common=registry['common'];image_hash=digest(data)
    matches=[k for k,v in registry['artifacts'].items() if v['image']['sha256']==image_hash]
    if artifact_name is None:artifact_name=matches[0] if len(matches)==1 else 'stock'
    record=registry['artifacts'][artifact_name]
    associated=matches==[artifact_name]
    add('INPUT_ARTIFACT_ASSOCIATION',associated,dict(selected_requirements=artifact_name,recognized_artifacts=matches,expected_sha256=record['image']['sha256'],actual_sha256=image_hash))
    add('LENGTH',len(data)==SIZE,dict(expected=SIZE,actual=len(data)))
    if len(data)!=SIZE:return {'schema':1,'status':'FAIL','image':{'sha256':image_hash,'size':len(data)},'artifact':artifact_name if associated else None,'checked_against':artifact_name,'checks':checks,'flash_authorized':False}
    ident=common['identity']
    for cid,key in [('CALID','calid'),('ECUID','ecuid')]:
        expected=bytes.fromhex(ident[key+'_hex']);p=ident[key+'_offset'];actual=data[p:p+len(expected)]
        add(cid,actual==expected,dict(offset=hx(p),expected_hex=expected.hex(),actual_hex=actual.hex()))
    reset=[int.from_bytes(data[p:p+4],'big') for p in range(0,16,4)]
    add('BIG_ENDIAN_RESET_VECTORS',reset==common['reset_words'] and reset[0]%2==0 and reset[2]%2==0,dict(actual=[hx(x) for x in reset],expected=[hx(x) for x in common['reset_words']]))
    add('INITIAL_SP',reset[1]==reset[3]==0xFFFFBFA0 and reset[1]%4==0 and 0xFFFF0000<reset[1]<0xFFFFC000,dict(power_on_SP=hx(reset[1]),manual_reset_SP=hx(reset[3])))
    try:
        rows=checksum_rows(data);geom=[{k:r[k] for k in ('offset','start','end_parameter')} for r in rows]
        add('CHECKSUM_GEOMETRY',geom==common['checksum_descriptors'] and rows[0]['start']!=rows[0]['end_parameter'],geom)
        add('CHECKSUM_VALIDITY',all(r['valid'] for r in rows),rows)
    except (ValueError,struct.error) as e:
        add('CHECKSUM_GEOMETRY',False,str(e));add('CHECKSUM_VALIDITY',False,'Not calculated for malformed geometry')
    evidence=dict(registry['evidence_files']);evidence[common['baseline']['path']]=common['baseline']['sha256']
    for x in record.get('repro_artifacts',[]):evidence[x['path']]=x['sha256']
    for k in ('residency_evidence','active_control_evidence','protocol_manifest'):
        if k in record:evidence[record[k]['path']]=record[k]['sha256']
    bad=check_files(evidence,reader);add('EVIDENCE_INTEGRITY',not bad,dict(files_checked=len(evidence),mismatches=bad))
    try:stock=reader(common['baseline']['path'])
    except OSError:stock=b''
    if len(stock)!=SIZE or digest(stock)!=common['baseline']['sha256']:
        add('BASELINE_INTEGRITY',False,'Pinned stock unavailable or changed; dependent checks fail closed')
        return {'schema':1,'status':'FAIL','image':{'sha256':image_hash,'size':len(data)},'artifact':artifact_name if associated else None,'checked_against':artifact_name,'checks':checks,'flash_authorized':False}
    changed=[i for i,(a,b) in enumerate(zip(stock,data)) if a!=b]
    allowed=set();fragments=record['fragments'];fragment_errors=[];reconstructed=bytearray(stock);inverse=bytearray(data);rom_spans=[]
    for f in fragments:
        p=f['address'];before=bytes.fromhex(f['before_hex']);after=bytes.fromhex(f['after_hex']);end=p+len(after)
        valid=0<=p<end<=SIZE and len(before)==len(after) and not any(p<b and end>a for a,b in rom_spans)
        if not valid:fragment_errors.append({'address':p,'reason':'invalid/overlapping fragment'});continue
        rom_spans.append((p,end));allowed.update(range(p,end))
        if stock[p:end]!=before:fragment_errors.append({'address':p,'reason':'original bytes mismatch'})
        if data[p:end]!=after:fragment_errors.append({'address':p,'reason':'candidate bytes mismatch'})
        reconstructed[p:end]=after;inverse[p:end]=before
    outside=[i for i in changed if i not in allowed]
    add('CHANGED_BYTE_ALLOWLIST',not outside,dict(changed_byte_count=len(changed),outside_count=len(outside),first_outside=[hx(a) for a in outside[:32]],declared_spans=rom_spans))
    add('PATCH_INVERSE_ROUNDTRIP',not fragment_errors and bytes(reconstructed)==data and bytes(inverse)==stock,
        dict(fragment_errors=fragment_errors,reconstructed_sha256=digest(reconstructed),restored_sha256=digest(inverse),baseline_sha256=digest(stock)), 'Both directions checked in memory; no reconstructed image is written')
    hook_errors=[]
    for p,v in common['preserved_hook_words'].items():
        p=int(p)
        if int.from_bytes(data[p:p+4],'big')!=v:hook_errors.append(dict(address=hx(p),expected=hx(v),actual=hx(int.from_bytes(data[p:p+4],'big'))))
    diagnostic_fragment=[f for f in fragments if f['address']==0x484B0]
    expected_hook=bytes.fromhex(diagnostic_fragment[0]['after_hex']) if diagnostic_fragment else stock[0x484B0:0x484BC]
    if data[0x484B0:0x484BC]!=expected_hook:hook_errors.append({'address':'0x000484B0','reason':'Unexpected diagnostic hook/continuation bytes'})
    add('ORIGINAL_HOOK_BYTES',not hook_errors and not any(e['reason']=='original bytes mismatch' for e in fragment_errors),hook_errors)
    protected=common['forbidden_spans']+common['preserved_special_spans']
    violations=[dict(start=hx(a),end=hx(b)) for a,b in protected if data[a:b]!=stock[a:b]]
    add('FORBIDDEN_BOOT_VECTOR_REGIONS',not violations,dict(forbidden_spans=protected,violations=violations))
    checksum_words={p for r in common['checksum_descriptors'] for p in range(r['offset']+8,r['offset']+12)}
    calchanges=[]
    for t in common['calibration_extents']:
        lo,hi=bisect_left(changed,t['start']),bisect_left(changed,t['end'])
        hits=[i for i in changed[lo:hi] if i not in checksum_words]
        if hits:calchanges.append(dict(name=t['name'],start=hx(t['start']),end=hx(t['end']),first_changes=[hx(a) for a in hits[:8]]))
    add('CALIBRATION_PRESERVATION',not calchanges,dict(native_extents_checked=len(common['calibration_extents']),changed_tables=calchanges,
        exception='Only pinned checksum correction words; undocumented bytes are additionally protected by exact changed-byte allowlist'))
    words={int(k,16):int(v['word'],16) for k,v in record['code_words'].items()};word_mismatch=[];delay_errors=[];branch_errors=[];targets=[]
    for pc,w in words.items():
        actual=int.from_bytes(data[pc:pc+2],'big')
        if actual!=w:word_mismatch.append(dict(pc=hx(pc),expected=f'{w:04X}',actual=f'{actual:04X}'))
        if pc%2:delay_errors.append(dict(pc=hx(pc),reason='unaligned instruction'))
        if delayed(actual):
            dw=int.from_bytes(data[pc+2:pc+4],'big')
            if pc+2 not in words or transfer(dw):delay_errors.append(dict(pc=hx(pc),delay_pc=hx(pc+2),delay_word=f'{dw:04X}',reason='Missing or transfer instruction in delay slot'))
        target=direct_branch(actual,pc)
        if target is None and actual&0xF0FF in (0x400B,0x402B):
            reg=(actual>>8)&15;prev=int.from_bytes(data[pc-2:pc],'big')
            if prev>>12==13 and (prev>>8)&15==reg:
                pool=((pc+2)&~3)+(prev&255)*4;target=int.from_bytes(data[pool:pool+4],'big')
            else:branch_errors.append(dict(pc=hx(pc),reason='Indirect transfer lacks reviewed adjacent literal load'))
        if target is not None:
            targets.append(dict(pc=hx(pc),target=hx(target)))
            if target%2 or (target not in words and target!=0x484BC):branch_errors.append(dict(pc=hx(pc),target=hx(target),reason='Target outside declared compiled code/continuation'))
    add('COMPILED_INSTRUCTION_IDENTITY',not word_mismatch and (associated or bool(words)),dict(words_checked=len(words),mismatches=word_mismatch), 'Registered changed-code instructions only; whole-image unknowns stay in boot frontier')
    add('DELAY_SLOT_ALIGNMENT',not delay_errors and (associated or bool(words)),delay_errors)
    add('BRANCH_TARGETS',not branch_errors and (associated or bool(words)),dict(targets=targets,errors=branch_errors,return_contract='RTS uses preserved caller PR; complete external entry/consumer ownership is a separate gate'))
    declarations=record['rom_declarations'];actual_decl=[[f['address'],f['address']+len(bytes.fromhex(f['after_hex']))] for f in fragments if f['label']!='checksum correction word']
    declared_ok=declarations==actual_decl and record['persistent_ram_declarations']==[] and all(0<=a<b<=SIZE and a%2==b%2==0 for a,b in declarations)
    add('ROM_RAM_DECLARATIONS',declared_ok,dict(rom_spans=declarations,persistent_RAM=record['persistent_ram_declarations'],adapter_stack_bytes=record.get('adapter_stack_bytes',0),division_stack_bytes=record.get('division_stack_bytes',0),exclusive_ROM_ownership_separately_required=record['residency_required']))
    active_ok=associated and not hook_errors and not outside and not fragment_errors
    if record.get('active_control_evidence'):
        try:
            eg=json.loads(reader(record['active_control_evidence']['path']));active_ok=active_ok and next(g for g in eg['gates'] if g['id']=='NO_ACTIVE_CONTROL_FEATURES')['status']=='PASS'
        except (OSError,ValueError,StopIteration,KeyError):active_ok=False
    add('ACTIVE_FEATURE_CLOSURE',active_ok,dict(no_project_timing_fuel_WGDC_MAF_DBW_revlimit_launch_ALS_transmission_torque=True if active_ok else 'NOT_ESTABLISHED',basis='Exact registered image, pinned diagnostic-only source/build/review association, preserved OEM control hooks and change set'))
    reprobad=check_files({x['path']:x['sha256'] for x in record.get('repro_artifacts',[])},reader)
    add('REPRO_BUILD_ASSOCIATION',associated and not reprobad and not bad,dict(classification=record['reproducible_build'],mismatches=reprobad,rerun_compiler=False))
    if record['residency_required']:
        add('RESIDENCY_OWNERSHIP',False,dict(proven_owned_bytes=0,policy='Frozen M07 tails explicitly unapproved; registry or caller JSON cannot promote them',evidence=record['residency_evidence']))
    else:add('RESIDENCY_OWNERSHIP',True,'No injected code or new resource; unchanged registered OEM stock')
    add('CURRENT_ROM_IDENTITY','CONDITIONAL','A local image hash does not identify the currently flashed ECU. Physical acquisition deferred.')
    add('SILICON_TIMING','CONDITIONAL','No verified silicon timing, electrical behavior, complete ISR/context or physical stack margin result is supplied.')
    return {'schema':1,'status':status(checks),'image':{'sha256':image_hash,'size':len(data)},'artifact':artifact_name if associated else None,'checked_against':artifact_name,'checks':checks,'flash_authorized':False,
            'ownership_claim':False,'physical_actions':False,'registry_sha256':REGISTRY_SHA256}

def integrate_boot(report,result,expected_hash,expected_stock_hash=None,dependencies=None):
    """Validate harness association; an optimistic caller-supplied PASS is insufficient."""
    checks=report['checks']
    def add(cid,s,d):checks.append({'id':cid,'status':s,'detail':d})
    if 'candidate' in result:
        candidate=result['candidate'];stock=result.get('stock',{})
        paired=(result.get('classification')=='RESET_PREFIX_DIFFERENTIAL_NOT_COMPLETE_BOOT_EQUIVALENCE'
                and stock.get('image',{}).get('sha256')==expected_stock_hash and result.get('explicit_allowlist')==[]
                and result.get('equal_frontier') is True and result.get('terminal_state_equal') is True and result.get('differences')==[] and result.get('status')!='FAIL')
        add('STOCK_VS_CANDIDATE_BOOT_PREFIX','PASS' if paired else 'FAIL',
            dict(equal_frontier=result.get('equal_frontier'),terminal_state_equal=result.get('terminal_state_equal'),differences=result.get('differences'),scope='Exact observed prefix writes/control and terminal integer/system state; not complete boot equivalence'))
        if not paired:report['status']='FAIL'
    else:candidate=result
    dependency_bad=[]
    if dependencies is not None:
        for side in ([result['stock'],candidate] if 'candidate' in result else [candidate]):
            claimed={x.get('path'):x.get('sha256') for x in side.get('dependencies',[])}
            if claimed!=dependencies:dependency_bad.append(claimed)
        add('BOOT_MODEL_DEPENDENCIES','FAIL' if dependency_bad else 'PASS',dict(expected=dependencies,mismatches=dependency_bad))
    if candidate.get('image',{}).get('sha256')!=expected_hash or result.get('schema')!=1 or dependency_bad:
        add('BOOT_PATH','FAIL','Boot result image/schema mismatch');add('SSM_STARTUP_READINESS','FAIL','Untrusted boot evidence');add('UNSUPPORTED_BEHAVIOR','FAIL','Untrusted boot evidence')
    else:
        s=candidate.get('status');valid=s in ('PASS','CONDITIONAL','FAIL')
        add('BOOT_PATH',s if valid else 'FAIL',dict(stop=candidate.get('stop'),milestones=candidate.get('milestones'),scenario=candidate.get('scenario'),semantic_sha256=candidate.get('semantic_sha256'),assumptions=candidate.get('assumptions')))
        ready=candidate.get('ssm_readiness',{})
        unsupported=candidate.get('unsupported',candidate.get('unsupported_frontier',candidate.get('frontier')))
        add('SSM_STARTUP_READINESS','PASS' if ready.get('status')=='PASS' and ready.get('boot_proven') is True and not unsupported else 'CONDITIONAL' if valid and s!='FAIL' else 'FAIL',ready)
        add('UNSUPPORTED_BEHAVIOR','FAIL' if not valid or s=='FAIL' else 'CONDITIONAL' if unsupported else 'PASS',unsupported)
    report['status']=status(checks)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--artifact',choices=['stock','one_page','two_pages'])
    args=p.parse_args(argv);out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    try:
        registry=load_registry();raw=args.image.resolve().read_bytes();report=evaluate(raw,registry,args.artifact);report['image']['path']=str(args.image.resolve())
        harness=registry.get('boot_harness')
        if harness:
            bad=check_files(harness['files'])
            if bad:raise ValueError('Boot harness source integrity mismatch: '+json.dumps(bad))
            result_path=out/'boot_result.json'
            command=[sys.executable,'-B',harness['entry'],'--image',str(args.image.resolve()),'--expected-sha256',digest(raw),'--stock',registry['common']['baseline']['path'],
                     '--expected-stock-sha256',registry['common']['baseline']['sha256'],'--output',str(result_path)]
            done=subprocess.run(command,capture_output=True,text=True,timeout=60)
            (out/'boot.log').write_text(done.stdout+'\n'+done.stderr)
            if not result_path.is_file():raise ValueError('Boot harness produced no machine result')
            result=json.loads(result_path.read_text());integrate_boot(report,result,digest(raw),registry['common']['baseline']['sha256'],harness['files'])
            for side in (result.get('stock',{}),result.get('candidate',{})):
                evidence_bad=check_files({r['path']:r['sha256'] for r in side.get('evidence',[])})
                if evidence_bad:raise ValueError('Generated boot trace integrity mismatch: '+json.dumps(evidence_bad))
            if done.returncode!=(2 if result.get('status')=='FAIL' else 0):raise ValueError(f'Unexpected boot process exit/status {done.returncode}/{result.get("status")}')
            report['boot_command']=command;report['boot_exit_code']=done.returncode
            report['boot_result_sha256']=digest(result_path.read_bytes())
            report['boot_summary']={k:{f:result[k].get(f) for f in ('trace_hashes','stop','scenario','milestones','terminal_state')} for k in ('stock','candidate') if k in result}
        else:
            for cid in ('BOOT_PATH','UNSUPPORTED_BEHAVIOR','SSM_STARTUP_READINESS'):report['checks'].append(dict(id=cid,status='CONDITIONAL',detail='No pinned end-to-end boot/readiness harness evidence registered'))
            report['status']=status(report['checks'])
        if digest(args.image.resolve().read_bytes())!=digest(raw):raise ValueError('Input changed during validation')
        report['input_unchanged']=True
    except Exception as e:
        if 'report' not in locals():report={'schema':1,'status':'FAIL','flash_authorized':False,'checks':[]}
        report['checks'].append({'id':'VALIDATOR_EXECUTION','status':'FAIL','detail':f'{type(e).__name__}: {e}'})
        report['status']='FAIL'
    report['validator_sha256']=digest(Path(__file__).read_bytes())
    semantic={'image_sha256':report.get('image',{}).get('sha256'),'artifact':report.get('artifact'),'status':report['status'],
              'checks':[(c['id'],c['status']) for c in report['checks']],'registry_sha256':REGISTRY_SHA256,'validator_sha256':report['validator_sha256'],
              'boot_summary':report.get('boot_summary')}
    report['deterministic_verdict_sha256']=digest(json.dumps(semantic,sort_keys=True).encode())
    # No clock data enters canonical evidence: same pinned inputs yield same result.
    payload=json.dumps(report,indent=2,sort_keys=True)+'\n';(out/'VALIDATION.json').write_text(payload)
    print(json.dumps({'status':report['status'],'report':str(out/'VALIDATION.json'),'sha256':digest(payload.encode()),'flash_authorized':False}))
    return {'PASS':0,'CONDITIONAL':2,'FAIL':3}[report['status']]
if __name__=='__main__':raise SystemExit(main())
