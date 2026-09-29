"""Existing MerpMod patch reconstruction and independently checked hook mapping.

Read-only ROM/SQLite/source inputs; writes only merpmod_mapping reports. No active
feature execution. The one dynamic test runs the archived clear leaf in virtual
RAM with explicit bounds; unsupported kernel/MMIO/FPU paths stay unsupported.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sh2e import ROM,Memory,CPU,SimulationStop
import json,sqlite3,hashlib,datetime,re

P=Path('C:/Dev/Astra_A2WC511R')
OUT=P/'reports/local/diaphora/merpmod_mapping'
EXP=P/'work/diaphora/exports'
CMP=P/'work/diaphora/comparisons'
REF=P/'reports/local/diaphora/merpmod_reference'
CORE=Path(__file__).resolve().parents[1]/'sh2e.py'
CORE_SHA='b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff'

def sha(b):return hashlib.sha256(b).hexdigest()
def hx(n):return f'0x{n:08X}'
def ident(p):return {'path':str(p),'size':p.stat().st_size,'sha256':sha(p.read_bytes())}
def save(name,data):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def checkpoint(stage):save('CHECKPOINT.json',{'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script':ident(Path(__file__))})
def word(raw,a):return int.from_bytes(raw[a:a+2],'big')
def long(raw,a):return int.from_bytes(raw[a:a+4],'big')
def spans(values):
    out=[]
    for a in sorted(values):
        if not out or a!=out[-1][1]:out.append([a,a+1])
        else:out[-1][1]+=1
    return out
def ro(path):
    c=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    return c

class Image:
    def __init__(self,label):
        self.label=label;self.analysis_path=EXP/(label+'.analysis.json')
        self.db_path=EXP/(label+'.sqlite');self.analysis=json.loads(self.analysis_path.read_text())
        self.rom=ROM.load(self.analysis['rom'],self.analysis['rom_sha256']);self.raw=self.rom.data
        self.db=ro(self.db_path)
        self.functions={x['start']:x for x in self.analysis['functions']}
        self.rows={int(x['address']):dict(x) for x in self.db.execute('select id,address,name,size,instructions from functions')}
    def heads(self,a):
        assert a in self.rows,('native_function_missing',self.label,hx(a))
        return [dict(x) for x in self.db.execute('select address,mnemonic,disasm from instructions where func_id=? order by cast(address as integer)',(self.rows[a]['id'],))]
    def function(self,a):
        f=self.functions.get(a)
        if not f:return {'entry':hx(a),'status':'NO_EXACT_NATIVE_FUNCTION'}
        return {'entry':hx(a),'name':f['name'],'chunks':f['chunks'],'chunk_sha256':[sha(self.raw[lo:hi]) for lo,hi in f['chunks']],
                'native_instruction_count':len(self.heads(a)),'native_inbound':f['inbound'],
                'scope':'Native chunks/xrefs, not a complete arbitrary-entry/callee/ownership proof.'}
    def identity(self):return {'rom':self.rom.identity(),'analysis':ident(self.analysis_path),'sqlite':ident(self.db_path)}
    def caller_context(self,pc):
        owners=[{'entry':hx(f['start']),'name':f['name'],'chunks':f['chunks']} for f in self.functions.values() if any(lo<=pc<hi for lo,hi in f['chunks'])]
        return {'status':'NATIVE_CONTAINING_FUNCTION' if owners else 'NO_NATIVE_CONTAINING_FUNCTION_LOCAL_CALLSITE_ONLY','functions':owners}

def dependencies(im,a):
    result=[]
    for row in im.heads(a):
        pc=int(row['address']);w=word(im.raw,pc)
        if w>>12 in (9,13):
            size=4 if w>>12==13 else 2
            address=((pc+4)&~3)+(w&255)*4 if size==4 else pc+4+(w&255)*2
            result.append({'pc':hx(pc),'kind':'PC_relative_read','register':w>>8&15,'address':hx(address),'size':size,
                           'value':hx(int.from_bytes(im.raw[address:address+size],'big')),'bytes':im.raw[address:address+size].hex()})
        elif w&0xFF00==0xC700:
            address=((pc+4)&~3)+(w&255)*4
            result.append({'pc':hx(pc),'kind':'MOVA_address_not_bounded_read','address':hx(address),
                           'first32bytes_for_comparison_only':im.raw[address:address+32].hex(),
                           'limit':'Indexed/table extent and dynamic selector are not established by MOVA.'})
    return result

def structural_pair(src,a,dst,b):
    sf,df=src.functions[a],dst.functions[b]
    assert len(sf['chunks'])==len(df['chunks'])
    chunk_rows=[]
    for (lo,hi),(dl,dh) in zip(sf['chunks'],df['chunks']):
        assert hi-lo==dh-dl
        assert src.raw[lo:hi]==dst.raw[dl:dh],('chunk_bytes_differ',src.label,dst.label,hx(lo),hx(dl))
        chunk_rows.append({'source':[hx(lo),hx(hi)],'target':[hx(dl),hx(dh)],'size':hi-lo,'sha256':sha(src.raw[lo:hi])})
    sd,dd=dependencies(src,a),dependencies(dst,b);assert len(sd)==len(dd)
    diffs=[]
    for x,y in zip(sd,dd):
        assert x['kind']==y['kind']
        if x.get('value')!=y.get('value') or x.get('first32bytes_for_comparison_only')!=y.get('first32bytes_for_comparison_only'):
            diffs.append({'source':x,'target':y})
    return {'source_function':src.function(a),'target_function':dst.function(b),'chunks_equal':chunk_rows,
            'source_dependencies':sd,'target_dependencies':dd,'changed_external_dependencies':diffs,
            'identity_status':'HIGH_CONFIDENCE_STRUCTURAL_IDENTITY','behavioral_equivalence':'NOT_PROVEN',
            'boundary_scope':'Entry and reported native chunk bytes are established; called routines, indexed reads, all incoming contexts and ABI are not globally closed.'}

def result_rows(label):
    path=CMP/label/'results.diaphora';c=ro(path)
    return {'file':ident(path),'config':dict(c.execute('select * from config').fetchone()),
            'results':[dict(x) for x in c.execute('select * from results')],
            'unmatched':[dict(x) for x in c.execute('select * from unmatched')]}
def match(result,a=None,b=None):
    return [x for x in result['results'] if (a is None or int(x['address'],16)==a) and (b is None or int(x['address2'],16)==b)]

HOOKS=[('reset',0xD218,0xD21A,0xD324,0xF928,'d242420b0009'),
       ('maf_pull2D',0x79B4,0x79BE,0x7A04,0x209C,'d313445ad411f32df43c430bf422'),
       ('wgdc_main',0x120FA,0x120FC,0x122B4,0x14B20,'d36e430b0009'),
       ('rev_limit',0x125B6,0x125B8,0x127E8,0x317D8,'d38c430b0009')]

def verify_hook(raw,spec,target=None):
    name,load,call,pool,old,code=spec;target=old if target is None else target
    op=word(raw,load);reg=op>>8&15
    assert op>>12==13 and ((load+4)&~3)+(op&255)*4==pool,('wrong_literal_mapping',name)
    assert word(raw,call)==0x400B|(reg<<8),('wrong_jsr_register',name)
    assert raw[load:call+4].hex()==code,('changed_call_sequence',name)
    assert long(raw,pool)==target,('wrong_pointee',name)
    return {'name':name,'load':hx(load),'call':hx(call),'delay':hx(call+2),'return':hx(call+4),'literal':hx(pool),
            'pointee':hx(target),'sequence_hex':code,'before_hex':raw[pool:pool+4].hex(),'status':'PASS'}

def direct_pc_call(raw,load,call,target):
    w=word(raw,load);n=w>>8&15;assert w>>12==13
    p=((load+4)&~3)+(w&255)*4
    assert long(raw,p)==target and word(raw,call)==0x400B|(n<<8)
    assert call==load+2 and word(raw,call+2)==9
    return {'load':hx(load),'pool':hx(p),'call':hx(call),'target':hx(target),'bytes':raw[load:call+4].hex()}

def double_wrapper(raw,entry,pointer_field,target):
    assert word(raw,entry)==0x4F22
    w=word(raw,entry+2);assert w>>8==0xD1
    pool=((entry+6)&~3)+(w&255)*4
    assert long(raw,pool)==pointer_field and long(raw,pointer_field)==target
    assert raw[entry+4:entry+10].hex()=='6112410b0009'
    return {'entry':hx(entry),'outer_pool':hx(pool),'pointer_field':hx(pointer_field),'OEM_target':hx(target),
            'sequence_hex':raw[entry:entry+10].hex(),'status':'EXACT_TWO_LEVEL_CALL_BINDING'}

def continuation(raw,entry,callee):
    w=word(raw,entry);assert w>>8==0xD2
    pool=((entry+4)&~3)+(w&255)*4
    assert raw[entry+2:entry+6].hex()=='422b0009' and long(raw,pool)==callee
    return {'entry':hx(entry),'pool':hx(pool),'tail_target':hx(callee),'bytes':raw[entry:entry+6].hex()}

def archive_clear_regression(archive):
    b=archive.raw
    assert word(b,0xE1F1E)>>8==0xD2 and word(b,0xE1F20)>>8==0xD1
    pl=lambda pc:((pc+4)&~3)+(word(b,pc)&255)*4
    start,end=long(b,pl(0xE1F1E)),long(b,pl(0xE1F20))
    assert (start,end)==(0xFFFF73B0,0xFFFF7428)
    assert b[0xE1F22:0xE1F26].hex()=='64236513'
    call=direct_pc_call(b,0xE1F26,0xE1F28,0xE1F84)
    m=Memory(archive.rom);sp=0xFFFFBFA0
    m.initialize(start-4,b'\xA5'*(end-start+8));m.initialize(sp-32,b'\x69'*48)
    m.watch(start-4,end+4,'archived_project_RAM_sentinels');m.write_allowlist=[(start,end),(sp-16,sp)]
    cpu=CPU(m,[(0xE1F84,0xE1FDE)],(sp-16,sp));cpu.r[4]=start;cpu.r[5]=end;cpu.r[15]=sp
    cpu.pc=0xE1F84;cpu.pr=0xFFFFFFFC;cpu.call_context=['000E1F84'];cpu.track_control_sources=False
    for _ in range(1200):
        cpu.step()
        if cpu.returned:break
    else:raise AssertionError('clear_helper_timeout')
    assert cpu.pc==0xFFFFFFFC and cpu.r[15]==sp
    writes=[e for e in m.events if e['mode']=='w' and start<=int(e['address'],16)<end]
    assert [(int(e['address'],16),e['size'],e['value']) for e in writes]==[(a,4,'00000000') for a in range(start,end,4)]
    assert m.ram[start-4-0xFFFF0000:start-0xFFFF0000]==b'\xA5'*4
    assert m.ram[end-0xFFFF0000:end+4-0xFFFF0000]==b'\xA5'*4
    return {'status':'PASS','classification':'ARCHIVED_CLEAR_LEAF_VIRTUAL_RAM_ONLY','start':hx(start),'end_exclusive':hx(end),'bytes':end-start,
            'callsite':call,'longword_writes':len(writes),'instruction_count':len(cpu.trace),'sentinels_preserved':True,
            'trace':cpu.trace,'accesses':m.events,'no_other_archived_feature_executed':True}

def main():
    assert sha(CORE.read_bytes())==CORE_SHA;checkpoint('loading_pinned_final03_inputs')
    names=['A2WC510S_stock_02','A2WC511R_stock_03','A2WC522S_stock_02','A2WC522S_archive_02']
    im={n:Image(n) for n in names};s,t,o,a=(im[n] for n in names)
    source_contract=json.loads((REF/'A2WC510S_hook_manifest.json').read_text())
    assert s.rom.sha256==source_contract['stock_rom']['sha256']
    assert t.rom.sha256=='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
    comps={n:result_rows(n) for n in ('stock_511R_vs_510S_03','stock_522S_vs_archive_03','archive_522S_vs_511R_03')}
    report={'schema':1,'classification':'EXISTING_PATCH_RECONSTRUCTION_AND_STRUCTURAL_TRANSFER_ONLY','status':'IN_PROGRESS',
            'inputs':{n:x.identity() for n,x in im.items()},'source_reference':ident(REF/'A2WC510S_hook_manifest.json'),'source_contracts':source_contract['hooks'],
            'archive_manifest':ident(REF/'A2WC522S_archived_patch_manifest.json'),'script':ident(Path(__file__)),'core_sha256':CORE_SHA,
            'comparison_inputs':{n:{k:v for k,v in x.items() if k not in ('results','unmatched')} for n,x in comps.items()}}
    hooks=[]
    for spec in HOOKS:
        sr,tr=verify_hook(s.raw,spec),verify_hook(t.raw,spec)
        hooks.append({'name':spec[0],'source510S':sr,'target511R':tr,'source_caller_context':s.caller_context(spec[1]),'target_caller_context':t.caller_context(spec[1]),'status':'HIGH_CONFIDENCE_LITERAL_CALL_IDENTITY','enabled_by_this_audit':False})
    report['hooks']=hooks
    functions=[]
    for label,entry in [('Pull2D',0x209C),('Pull3D',0x2150),('MAF_caller',0x79A8),('reset',0xF928),('WGDC',0x14B20),('rev_limit',0x317D8)]:
        rows=match(comps['stock_511R_vs_510S_03'],entry,entry);assert len(rows)==1
        r=structural_pair(s,entry,t,entry);r.update(role=label,diaphora=rows[0]);functions.append(r)
    report['source510S_to_target511R_functions']=functions
    report['rev_limit_continuations']={'source510S':continuation(s.raw,0x3180E,0x28C20),'target511R':continuation(t.raw,0x3180E,0x28C20),
       'stock522S':continuation(o.raw,0x31912,0x28D24),'archive522S':continuation(a.raw,0x31912,0x28D24),
       'stock522S_to511R_independent_chunks':structural_pair(o,0x318DC,t,0x317D8),
       'rejected_Diaphora_proposal':match(comps['archive_522S_vs_511R_03'],0x31912),
       'reason':'31912 is the original522S six-byte tailcall after bypassed limiter head. Corresponding511R continuation is3180E, independently bound to28C20. The partial matcher proposal31814 is the next different function and is not accepted.'}
    report['CEL']={'configured_hook':hx(0x7AFDC),'configured_before':'fffff746','source510S_actual':s.raw[0x7AFDC:0x7AFE0].hex(),
       'target511R_actual':t.raw[0x7AFDC:0x7AFE0].hex(),'exact_patch_precondition':'FAIL',
       'trigger_source_address':hx(0x7AEC4),'candidate511R_address':hx(0x7AEC4),'raw_span_equal':s.raw[0x7AEC4:0x7AFE0]==t.raw[0x7AEC4:0x7AFE0],
       'native_source':s.function(0x7AEC4),'native_target':t.function(0x7AEC4),'identity_status':'CANDIDATE_ONLY_NOT_NATIVE_FUNCTION_MATCH',
       'note':'No correction or hook activation; separate signedwordF746 literal does not satisfy four-byte hook beforeword.'}
    save('MERPMOD_MAPPING.json',report);checkpoint('four_hooks_and_six_function_identities_saved')

    old_manifest=json.loads((REF/'A2WC522S_archived_patch_manifest.json').read_text())
    assert old_manifest['stock_rom']['sha256']==o.rom.sha256 and old_manifest['comparison_image']['sha256']==a.rom.sha256
    changed={i for i,(x,y) in enumerate(zip(o.raw,a.raw)) if x!=y}
    native_modified=[];all_code={}
    for address,f in o.rows.items():
        changed_heads=[]
        for row in o.heads(address):
            pc=int(row['address']);all_code[pc]=address
            if pc in changed or pc+1 in changed:changed_heads.append(hx(pc))
        if changed_heads:native_modified.append({'entry':hx(address),'name':f['name'],'changed_instruction_heads':changed_heads})
    assert not native_modified,('original_executable_bytes_modified',native_modified)
    new_functions=[x for x in a.functions if 0xE1000<=x<0xE20DD]
    codebytes=set();new_rows=[]
    for entry in new_functions:
        heads=a.heads(entry)
        for h in heads:codebytes.update((int(h['address']),int(h['address'])+1))
        low_matches=match(comps['stock_522S_vs_archive_03'],b=entry)+match(comps['archive_522S_vs_511R_03'],a=entry)
        new_rows.append({'native_function':a.function(entry),'dependencies':dependencies(a,entry),
                         'diaphora_proposals':low_matches,'proposal_disposition':'REJECTED_LOW_RATIO_NEW_CODE_IDENTITY' if low_matches else 'NO_MATCH_UNMATCHED_INSERTED_CODE'})
    payload=set(range(0xE1000,0xE20DD));unclassified=payload-codebytes
    wrappers={'reset':double_wrapper(a.raw,0xE1EFC,0xE20D4,0xF928),
              'WGDC':double_wrapper(a.raw,0xE20B8,0xE20D8,0x14B20),
              'MAF_calls_new_control':direct_pc_call(a.raw,0xE19B6,0xE19B8,0xE1BB0)}
    archived_hooks=[]
    for spec in HOOKS:
        original=0x318DC if spec[0]=='rev_limit' else spec[4]
        patched={'reset':0xE1EFC,'maf_pull2D':0xE1988,'wgdc_main':0xE20B8,'rev_limit':0x31912}[spec[0]]
        archived_hooks.append({'name':spec[0],'stock':verify_hook(o.raw,spec,original),'archive':verify_hook(a.raw,spec,patched),
                               'stock_caller_context':o.caller_context(spec[1]),'archive_caller_context':a.caller_context(spec[1]),
                               'existing_instruction_bytes_equal':o.raw[spec[1]:spec[2]+4]==a.raw[spec[1]:spec[2]+4]})
    clear=archive_clear_regression(a);save('archived_clear_leaf_regression.json',clear)
    report['archive_reconstruction']={'operations':old_manifest['operations'],'changed_byte_count':len(changed),
      'changed_ranges':[[hx(x),hx(y)] for x,y in spans(changed)],'modified_existing_executable_functions':native_modified,
      'all_existing_native_instruction_words_unchanged':True,'comparison_scope':'All instruction heads in pinned stock522S02 native export; not a whole-ROM executable classification theorem.',
      'four_changed_pointer_bindings':archived_hooks,'new_executable_functions':new_rows,
      'inserted_payload_span':[hx(0xE1000),hx(0xE20DD)],'inserted_payload_bytes':4317,
      'native_inserted_instruction_bytes':len(codebytes),'native_inserted_instruction_ranges':[[hx(x),hx(y)] for x,y in spans(codebytes)],
      'remaining_payload_bytes':len(unclassified),'remaining_payload_ranges':[[hx(x),hx(y)] for x,y in spans(unclassified)],
      'remaining_payload_classification':'Identifier/tables/literalpools/marker plus any undiscovered code; absence from native instructions is not proof every remaining byte is data.',
      'known_ASCII_runs':[{'start':hx(0xE1000+m.start()),'end_exclusive':hx(0xE1000+m.end()),'text':m.group().decode('ascii')}
                         for m in re.finditer(rb'[ -~]{16,}',a.raw[0xE1000:0xE1988])],
      'directly_loaded_RAM_constants':sorted({d['value'] for f in new_rows for d in f['dependencies'] if d.get('value','').startswith('0xFFFF')}),
      'known_wrapper_bindings':wrappers,'original_function_pointer_fields':{hx(p):hx(long(a.raw,p)) for p in (0xE20CC,0xE20D0,0xE20D4,0xE20D8)},
      'actual_binary_RAM_clear_span':{'start':clear['start'],'end_exclusive':clear['end_exclusive'],'bytes':clear['bytes'],'regression':str(OUT/'archived_clear_leaf_regression.json')},
      'RAM_ownership':'NOT_PROVEN','allocation_distinction':'Archived baseFFFF73B0/clear-endFFFF7428 is binary established; current510S source baseFFFF7400 differs. No persistent ownership or all-access end is inferred from clear span.',
      'cadence_distinction':'ArchivedMAF E1988 callsE1BB0 atE19B8 afterOEMsensorMAF. ArchivedWGDC wrapper onlycallsOEM. Currentsource RevLimHook architecture is different; no historicalsource or timing equivalence is claimed.',
      'unsupported_execution':'No FPU/control feature, OEM reset/MMIO, kernel or physical path executed. Only the standalone integer RAM clear leaf ran with virtualRAM.'}
    save('MERPMOD_MAPPING.json',report);checkpoint('archive_all_byte_changes_and_inserted_functions_saved')
    negatives=[]
    def negative(name,fn):
        try:fn()
        except (AssertionError,SimulationStop):negatives.append({'name':name,'detected':True})
        else:raise AssertionError(('negative_control_missed',name))
    for spec in HOOKS:
        negative(spec[0]+':wrong_target_mapping',lambda spec=spec:verify_hook(t.raw,spec,spec[4]+2))
        b=bytearray(t.raw);b[spec[2]:spec[2]+2]=b'\x00\x09'
        negative(spec[0]+':mutated_jsr',lambda spec=spec,b=bytes(b):verify_hook(b,spec))
        b=bytearray(t.raw);b[spec[3]+3]^=2
        negative(spec[0]+':mutated_literal',lambda spec=spec,b=bytes(b):verify_hook(b,spec))
        b=bytearray(t.raw);b[spec[2]+3]^=1
        negative(spec[0]+':mutated_delay_slot',lambda spec=spec,b=bytes(b):verify_hook(b,spec))
    for entry in (0x209C,0x2150):
        expected=s.raw[entry:entry+16]
        def interp_check(candidate,entry=entry,expected=expected):assert t.raw[candidate:candidate+16]==expected
        interp_check(entry);negative(hx(entry)+':wrong_interpolator_entry',lambda entry=entry:interp_check(entry+2))
    def cel_beforeword():assert t.raw[0x7AFDC:0x7AFE0]==bytes.fromhex('fffff746')
    negative('CEL_configured_beforeword_mismatch',cel_beforeword)
    negative('wrong_rev_continuation_31814',lambda:continuation(t.raw,0x31814,0x28C20))
    assert sha(CORE.read_bytes())==CORE_SHA
    report.update(status='PASS_STRUCTURAL_RECONSTRUCTION_WITH_EXPLICIT_REJECTIONS',regressions={'status':'PASS','four_hooks_each_positive_and_four_negative_controls':True,
      'six_source510S_function_chunk_identity_assertions':True,'stock522S_rev_relocated_chunk_identity_assertion':True,
      'interpolator_negative_entries':2,'negative_controls':negatives,'archived_clear_leaf':'PASS'},
      gates={'four_literal_hook_identities_and_OEM_interpolator_entries':'PASS','CEL_configured_patch_precondition':'FAIL',
             'complete_call_ABI_and_calibration_semantic_equivalence':'FAIL','exclusive_ROM_RAM_ownership':'FAIL',
             'kernel_MMIO_or_FPU_dynamic_validation':'NOT_PERFORMED_UNSUPPORTED','silicon_timing':'PHYSICAL/BENCH REQUIRED'},
      generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save('MERPMOD_MAPPING.json',report);checkpoint('complete')
    reviewed=[]
    for f in functions:
        m=f['diaphora'];reviewed.append({'comparison_prefix':'stock_511R_vs_510S_03','source_address':int(m['address'],16),'target_address':int(m['address2'],16),
          'confidence':'HIGH_CONFIDENCE_STRUCTURAL_IDENTITY','reason':f['role']+': native chunks match byte-for-byte and independent literal/call or original-function binding corroborates the entry. External dependencies retained; ABI/calibration/behavior equivalence is not established.',
          'evidence_path':str(OUT/'MERPMOD_MAPPING.json')})
    for prefix,sa,ta,why in [
      ('archive_522S_vs_511R_03',0x31912,0x31814,'Wrong continuation identity: exact six-byte OEM tailcall maps31912 to511R3180E, not next function31814. Partial rare-constant score is not authority.'),
      ('stock_522S_vs_archive_03',0x151DC,0xE1BB0,'Inserted archive routineE1BB0 is called from newMAF atE19B8. Low ratio0.2262198/rare constant does not identify OEM151DC; rejected.'),
      ('archive_522S_vs_511R_03',0xE1BB0,0x55CE4,'Inserted archive routineE1BB0 has no demonstrated identity with511R55CE4. Low ratio0.2766767/rare constant rejected.')]:
        assert len(match(comps[prefix],sa,ta))==1
        reviewed.append({'comparison_prefix':prefix,'source_address':sa,'target_address':ta,'confidence':'REJECTED','reason':why,'evidence_path':str(OUT/'MERPMOD_MAPPING.json')})
    save('REVIEWED_MATCHES.json',reviewed)
    print(json.dumps({'status':report['status'],'report':str(OUT/'MERPMOD_MAPPING.json'),'hooks':len(hooks),'function_pairs':len(functions),
                      'inserted_functions':len(new_rows),'inserted_instruction_bytes':len(codebytes),'negative_controls':len(negatives),
                      'RAM_clear_bytes':clear['bytes'],'report_sha256':sha((OUT/'MERPMOD_MAPPING.json').read_bytes())},indent=2))

if __name__=='__main__':main()
