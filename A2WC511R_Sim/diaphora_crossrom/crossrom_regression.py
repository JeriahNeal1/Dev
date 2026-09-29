"""Pinned cross-ROM function correspondence; no ownership or physical inference.

Only this new subtree is written. Imports do not update the frozen core cache.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sh2e import ROM, Memory, CPU, SimulationStop, OPCODES, RAM_START, sx
from hashlib import sha256
import datetime
import json
import random

HERE=Path(__file__).resolve().parent
INV=Path('C:/Dev/Astra_A2WC511R/reports/local/diaphora/rom_inventory/public_rom_manifest.json')
BASE=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')
BASE_SHA='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
CORE_SHA='b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff'
SP,RET=0xFFFFBFA0,0xFFFFFFFC
ROLES={'source':0xFFFF4C8C,'flags':0xFFFF4BA4,'output':0xFFFF4BC0}

def digest(b):return sha256(b).hexdigest()
def hx(a):return f'0x{a:08X}'
def word(raw,a):return int.from_bytes(raw[a:a+2],'big')
def decode(w):
    s=next((s for s in OPCODES if w&s.mask==s.value),None)
    if s is None:raise AssertionError(('unknown_instruction',f'{w:04X}'))
    return s.name
def runs(values):
    out=[]
    for a in sorted(values):
        if not out or a!=out[-1][1]:out.append([a,a+1])
        else:out[-1][1]+=1
    return out

def cfg(raw,entry,limit=512):
    """Exact supported leaf CFG: both branch outcomes, explicit delay words.

    Separate ordinary entries and visited words; no delay-slot pruning bug.
    Calls/indirect transfers/opaque instructions fail, never imply exclusion.
    """
    code={};entered=set();todo=[entry]; edges=[]
    def add(pc,delay=False):
        assert entry<=pc<entry+limit and pc%2==0, ('CFG_escape',hx(pc))
        w=word(raw,pc); name=decode(w)
        assert not delay or name not in ('rts','bra','bf','bt','bf_s','bt_s','jmp','jsr','bsr'), 'branch_in_delay'
        code[pc]={'pc':pc,'word':w,'name':name}
        return w,name
    while todo:
        pc=todo.pop()
        if pc in entered:continue
        entered.add(pc); w,name=add(pc)
        if name=='rts':add(pc+2,True);edges.append([pc,'return']);continue
        if name=='bra':
            target=pc+4+2*sx(w&4095,12); add(pc+2,True);todo.append(target);edges.append([pc,target]);continue
        if name in ('bt','bf','bt_s','bf_s'):
            target=pc+4+2*sx(w&255,8);fall=pc+(4 if name.endswith('_s') else 2)
            if name.endswith('_s'):add(pc+2,True)
            todo.extend([target,fall]);edges.extend([[pc,target],[pc,fall]]);continue
        assert name not in ('jmp','jsr','bsr'), ('not_a_closed_leaf',hx(pc),name)
        todo.append(pc+2);edges.append([pc,pc+2])
    literals=[]
    for pc,row in sorted(code.items()):
        w=row['word'];name=row['name']
        if name in ('movl_pc','movw_pc'):
            size=4 if name=='movl_pc' else 2
            a=((pc+4)&~3)+(w&255)*4 if size==4 else pc+4+(w&255)*2
            literals.append({'pc':pc,'register':w>>8&15,'address':a,'size':size,'value':int.from_bytes(raw[a:a+size],'big')})
    return {'entry':entry,'code':code,'edges':edges,'literals':literals}

def find_range(raw):
    candidates=[]
    patterns=[[(0xFFFF,0xE640),(0xFF00,0xD400),(0xFF00,0xD300),(0xFFFF,0x6730),(0xFFFF,0x657C),(0xFFFF,0x6253),(0xFFFF,0x2268)],
              [(0xFF00,0xD300),(0xFFFF,0xE640),(0xFF00,0xD400),(0xFFFF,0x6730),(0xFFFF,0x657C),(0xFFFF,0x6253),(0xFFFF,0x2268)]]
    for a in range(0,len(raw)-14,2):
        first=word(raw,a)
        if first!=0xE640 and first&0xFF00!=0xD300:continue
        for pattern in patterns:
            if all(word(raw,a+i*2)&mask==value for i,(mask,value) in enumerate(pattern)):
                candidates.append(a)
    assert len(candidates)==1, ('range_candidate_not_unique',candidates)
    graph=cfg(raw,candidates[0])
    longs=[x for x in graph['literals'] if x['size']==4]
    flags=[x for x in longs if x['register']==4]
    r3=[x for x in longs if x['register']==3]
    const=[x for x in graph['literals'] if x['size']==2]
    assert len(longs)==3 and len(flags)==1 and len(r3)==2 and len(const)==1
    assert const[0]['value']==128 and const[0]['register']==7
    roles={'source':r3[0]['value'],'flags':flags[0]['value'],'output':r3[1]['value']}
    assert len(set(roles.values()))==3 and all(RAM_START<=a<0xFFFFC000 for a in roles.values())
    graph['roles']=roles
    return graph

def signature(graph):
    pcs=sorted(graph['code']); ix={p:i for i,p in enumerate(pcs)}
    literal={x['pc']:x for x in graph['literals']}
    rolevalues={v:k for k,v in graph.get('roles',{}).items()}
    out=[]
    for pc in pcs:
        w=graph['code'][pc]['word'];name=graph['code'][pc]['name']
        if pc in literal:
            x=literal[pc];out.append([name,x['register'],rolevalues.get(x['value'],x['value'])])
        elif name=='bra':out.append([name,ix[pc+4+sx(w&4095,12)*2]])
        elif name in ('bf','bt','bf_s','bt_s'):out.append([name,ix[pc+4+sx(w&255,8)*2]])
        else:out.append([name,w])
    # Only permitted scheduling change is the independent first3 constant loads
    # into distinct R3/R4/R6. They cannot fault in the declared immutable ROM map,
    # do not read prior destination values and do not modify SR.
    assert sorted(out[:3],key=str)==sorted([['mov_imm',0xE640],['movl_pc',4,'flags'],['movl_pc',3,'source']],key=str)
    out[:3]=sorted(out[:3],key=str)
    return out

def fixture(rom,graph,regs,sr,ram):
    m=Memory(rom)
    m.initialize(SP-32,bytes((0xA5+i)&255 for i in range(48)))
    for a,v in ram.items():m.initialize(a,v)
    m.watch(SP-32,SP+16,'stack_sentinels')
    for name,a in graph.get('roles',{}).items():m.watch(a,a+1,name)
    m.write_allowlist=[(SP-8,SP),(0xFFFF130C,0xFFFF1310)]+[(a,a+1) for k,a in graph.get('roles',{}).items() if k!='source']
    cpu=CPU(m,[(graph['entry'],max(graph['code'])+2)],(SP-16,SP))
    cpu.r=list(regs);cpu.r[15]=SP;cpu.pc=graph['entry'];cpu.pr=RET
    cpu.mach=0x89ABCDEF;cpu.macl=0x13579BDF;cpu._set_system('sr',sr,{'fixture:SR'})
    cpu.call_context=[f'{graph["entry"]:08X}'];cpu.track_control_sources=False
    for _ in range(180):
        assert cpu.pc in graph['code'], ('dynamic_outside_CFG',hx(cpu.pc))
        cpu.step()
        if cpu.returned:
            assert cpu.pc==RET and cpu.pending is None and cpu.r[15]==SP
            return cpu
    raise AssertionError('function_budget_exceeded')

def normalized(cpu,roles=None):
    roles=roles or {};translate={a:ROLES[k] for k,a in roles.items()}
    regs=list(cpu.r)
    if roles:
        assert regs[3]==roles['output']
        regs[3]=ROLES['output']
    ram=bytearray(cpu.memory.ram);init=bytearray(cpu.memory.initialized)
    values={k:ram[a-RAM_START] for k,a in roles.items()}
    known={k:init[a-RAM_START] for k,a in roles.items()}
    for a in roles.values():ram[a-RAM_START]=0;init[a-RAM_START]=0
    for k in roles:ram[ROLES[k]-RAM_START]=values[k];init[ROLES[k]-RAM_START]=known[k]
    accesses=[(e['mode'],translate.get(int(e['address'],16),int(e['address'],16)),e['size'],e['value'])
              for e in cpu.memory.events if int(e['address'],16)>=RAM_START]
    calls=[e for e in cpu.trace if e['instruction'] in ('jsr','bsr','jmp')]
    return {'r':regs,'sr':cpu.sr,'pr':cpu.pr,'sp':cpu.r[15],'pc':cpu.pc,'mach':cpu.mach,'macl':cpu.macl,
            'RAM_SHA256':digest(ram),'initialized_RAM_SHA256':digest(init),'RAM_MMIO_accesses':accesses,'calls':calls}

def compare(a,b,roles_a=None,roles_b=None):
    av,bv=normalized(a,roles_a),normalized(b,roles_b)
    assert av==bv, ('architectural_or_memory_trace_mismatch',[(k,av[k],bv[k]) for k in av if av[k]!=bv[k]])
    return av

def small_candidates(base,roms):
    path=Path('C:/Dev/Astra_A2WC511R/reports/local/gate_closure/ida/defined_code_export.json')
    db=json.loads(path.read_text()); wanted={0x147AC,0x15A02,0x4B04,0x18012,0x18026,0x23B12}
    results=[]
    for f in db['functions']:
        if f['start'] not in wanted:continue
        a,b=f['start'],f['end'];prefix=base.data[a:min(a+8,b)]
        row={'baseline_entry':hx(a),'baseline_end':hx(b),'baseline_IDA_name':f['name'],'prefix_hex':prefix.hex(),'roms':[]}
        for ident,rom in roms:
            hits=[];pos=0
            while (pos:=rom.data.find(prefix,pos))>=0:
                if pos%2==0:hits.append({'entry':hx(pos),'full_span_equal':rom.data[pos:pos+b-a]==base.data[a:b]})
                pos+=1
            row['roms'].append({'calid':ident,'prefix_candidates':hits})
        results.append(row)
    return {'classification':'RAW_PREFIX_PROPOSALS_NOT_VALIDATED_FUNCTIONS_OR_OWNERSHIP','IDA_export':str(path),'IDA_export_sha256':digest(path.read_bytes()),'candidates':results,
            'limitations':'The8-byte prefix can be nonunique or data; full span equality can omit external pools. No compression replacement or ownership claim is made.'}

def native_evidence(calid,rom,entry):
    root=Path('C:/Dev/Astra_A2WC511R/work/diaphora/exports')
    paths=sorted(root.glob(calid+'_stock_*.analysis.json'))
    if not paths:return {'status':'UNAVAILABLE'}
    path=paths[-1];data=json.loads(path.read_text())
    assert data['rom_sha256']==rom.sha256
    fs=[f for f in data['functions'] if f['start']==entry]
    return {'status':'EXACT_START' if len(fs)==1 else 'NO_EXACT_NATIVE_START','path':str(path),
            'sha256':digest(path.read_bytes()),'function':fs[0] if len(fs)==1 else None,
            'scope':'Disposable native export only; xrefs are observed analysis evidence, not complete inbound closure.'}

def main():
    core=HERE.parent/'sh2e.py';assert digest(core.read_bytes())==CORE_SHA
    manifest=json.loads(INV.read_text());base=ROM.load(BASE,BASE_SHA)
    roms=[(x['calid_at_2000'],ROM.load(x['path'],x['sha256'])) for x in manifest['roms']]
    graph=cfg(base.data,0x4260,170);reference_range=find_range(base.data);sig=signature(reference_range)
    mappings=[]
    for name,rom in roms:
        assert rom.data[0x4260:0x430A]==base.data[0x4260:0x430A]
        for lit in graph['literals']:
            assert int.from_bytes(rom.data[lit['address']:lit['address']+lit['size']],'big')==lit['value'],('division_external_literal_mismatch',name,lit)
        rg=find_range(rom.data);assert signature(rg)==sig,('structural_range_mismatch',name)
        mappings.append((name,rom,rg))
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    out=HERE/'runs'/stamp;out.mkdir(parents=True)
    summary={'classification':'SCOPED_CROSS_ROM_FUNCTION_CORRESPONDENCE_NOT_OWNERSHIP','status':'RUNNING','core_sha256':CORE_SHA,
             'baseline':base.identity(),'inventory_path':str(INV),'inventory_sha256':digest(INV.read_bytes()),
             'normalization':'Range only: explicit3 RAM roles and finalR3 output pointer; immutable ROM literal access order may differ for first3 independent loads. All other GPRs/system state and full canonical RAM/init bytes plus ordered RAM/MMIO accesses compared exactly. Division compares actual addresses without normalization.',
             'ROM_mapping':[],'negative_controls':[],'source_sha256':digest(Path(__file__).read_bytes())}
    for name,rom,rg in mappings:
        summary['ROM_mapping'].append({'calid':name,'rom':rom.identity(),'division_entry':hx(0x4260),'division_full_object_equal':True,
          'division_external_literals_verified':graph['literals'],'division_reachable_instruction_bytes':len(graph['code'])*2,
          'division_native':native_evidence(name,rom,0x4260),
          'range_entry':hx(rg['entry']),'range_last_instruction':hx(max(rg['code'])),'range_roles':{k:hx(v) for k,v in rg['roles'].items()},
          'range_structural_signature_sha256':digest(json.dumps(sig).encode()),'reachable_instruction_count':len(rg['code']),
          'range_instruction_bytes':len(rg['code'])*2,'range_entry_through_return_span':max(rg['code'])+2-rg['entry'],
          'range_unexecuted_bytes_inside_span':max(rg['code'])+2-rg['entry']-len(rg['code'])*2,
          'range_native':native_evidence(name,rom,rg['entry']),
          'first3_reordered':rg['code'][rg['entry']]['word']!=0xE640,'literal_dependencies':rg['literals']})
    (out/'mapping.json').write_text(json.dumps(summary,indent=2)+'\n')
    rng=random.Random(0xD1A4260);values=[0,1,-1,2,-2,3,-3,0x7FFFFFFF,-0x80000000,65535,-65535]
    pairs=[(a,b) for a in values for b in values]+[(a,3) for a in range(-2,254)]+[(rng.randrange(-0x80000000,0x80000000),rng.randrange(-0x80000000,0x80000000)) for _ in range(256)]
    regseed=lambda:[rng.getrandbits(32) for _ in range(16)]
    coverage={name:{'division':set(),'range':set()} for name,_ in roms};h=sha256();counts={'division_per_rom':0,'range_per_rom':0};samples=[]
    for dividend,divisor in pairs:
        regs=regseed();regs[0]=divisor&0xFFFFFFFF;regs[1]=dividend&0xFFFFFFFF;sr=rng.getrandbits(32)&0x0FFF0FFF
        old=fixture(base,graph,regs,sr,{0xFFFF130C:bytes.fromhex('a55aa55a')})
        for name,rom,_ in mappings:
            new=fixture(rom,graph,regs,sr,{0xFFFF130C:bytes.fromhex('a55aa55a')});v=compare(old,new)
            coverage[name]['division'].update(int(e['pc'],16) for e in new.trace);h.update(json.dumps([name,dividend,divisor,v],sort_keys=True).encode())
        counts['division_per_rom']+=1
    print('Division comparisons complete:',counts['division_per_rom'],'per ROM',flush=True)
    for raw in range(256):
        for prior in (0,1,0x1F,0x20,0x55,0x80,0xA5,0xFF):
            regs=regseed();sr=rng.getrandbits(32)&0x0FFF0FFF
            ram=lambda roles:{roles['source']:bytes([raw]),roles['flags']:bytes([prior]),roles['output']:b'\xA5'}
            old=fixture(base,reference_range,regs,sr,ram(reference_range['roles']))
            for name,rom,rg in mappings:
                new=fixture(rom,rg,regs,sr,ram(rg['roles']));v=compare(old,new,reference_range['roles'],rg['roles'])
                coverage[name]['range'].update(int(e['pc'],16) for e in new.trace);h.update(json.dumps([name,raw,prior,v],sort_keys=True).encode())
                if raw==0xF3 and prior==0xA5:samples.append({'calid':name,'raw':raw,'prior':prior,'normalized_final':v,'trace':new.trace,'accesses':new.memory.events})
            counts['range_per_rom']+=1
        if raw%64==63:print('Range raw-byte partitions complete:',raw+1,flush=True)
    # Negative controls demonstrate byte/mapping gates and actual behavior checks.
    mutated=base.with_overlay(0x14786,b'\xE4\x02','negative:range1 result changed to2')
    try:assert signature(find_range(mutated.data))==sig
    except AssertionError:summary['negative_controls'].append({'name':'reachable_opcode_mutation','detected_by':'structural_signature'})
    else:raise AssertionError('opcode mutation escaped')
    mutgraph=find_range(mutated.data);regs=[i*0x1020304 for i in range(16)];ram={ROLES['source']:b'\x01',ROLES['flags']:b'\x55',ROLES['output']:b'\xA5'}
    old=fixture(base,reference_range,regs,0x301,ram);new=fixture(mutated,mutgraph,regs,0x301,ram)
    try:compare(old,new,ROLES,ROLES)
    except AssertionError:summary['negative_controls'].append({'name':'reachable_opcode_mutation','detected_by':'actual_register_and_RAM_behavior'})
    else:raise AssertionError('behavior mutation escaped')
    _,different,rg=next(x for x in mappings if x[0]=='A2WC521R')
    # Deliberately initialize candidate RAM at the baseline role addresses only.
    try:fixture(different,rg,regs,0x301,ram)
    except SimulationStop as e:
        assert 'Uninitialized RAM read' in str(e)
        summary['negative_controls'].append({'name':'wrong_cross_ROM_input_mapping','detected_by':'strict_uninitialized_RAM','error':str(e)})
    else:raise AssertionError('incorrect RAM mapping escaped')
    try:ROM.load(BASE,'0'*64)
    except SimulationStop:summary['negative_controls'].append({'name':'incorrect_ROM_hash','detected_by':'immutable_input_identity'})
    else:raise AssertionError('identity mismatch escaped')
    bad=base.with_overlay(0x4260,b'\xFF\xFF','negative:unsupported opcode')
    try:cfg(bad.data,0x4260,170)
    except AssertionError:summary['negative_controls'].append({'name':'unsupported_instruction','detected_by':'fail_closed_CFG_decoder'})
    else:raise AssertionError('opaque instruction escaped')
    for name,_,rg in mappings:
        assert coverage[name]['division']==set(graph['code']),('division_instruction_coverage',name)
        assert coverage[name]['range']==set(rg['code']),('range_instruction_coverage',name)
    summary.update(status='PASS',counts={**counts,'ROMs':len(roms),'division_comparisons':counts['division_per_rom']*len(roms),'range_comparisons':counts['range_per_rom']*len(roms)},
                   deterministic_output_digest=h.hexdigest(),all_reachable_instructions_executed=True,
                   FPU='No reachable instruction in either function uses FPU; core has no floating execution/state model, so this is static instruction exclusion, not simulated FPU validation.',
                   peripheral_policy='No MMIO mapping provided; any peripheral access fails. Both tested leaf functions make zero calls.',
                   gates={'declared_input_function_correspondence':'PASS','exclusive_ROM_or_RAM_ownership':'FAIL','complete_firmware_correspondence':'FAIL','silicon_timing_and_interrupt_behavior':'PHYSICAL/BENCH REQUIRED'},
                   limitations=['Declared-entry only; arbitrary interior entries and other firmware consumers remain unproved.','Division scenarios are finite. Range enumerates all256 input bytes with8 prior flag seeds, not every architectural machine state.','Static CFG decoder rejects calls/indirect control/opaque instructions; it is not a whole-ROM reachability theorem.','RAM role mapping is a software correspondence, not a transmission physical-state/freshness claim.'])
    summary['instruction_coverage']={name:{k:len(v) for k,v in rows.items()} for name,rows in coverage.items()}
    assert digest(core.read_bytes())==CORE_SHA
    (out/'crossrom_regression.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'representative_traces.json').write_text(json.dumps(samples,indent=2)+'\n')
    (out/'small_wrapper_prefix_candidates.json').write_text(json.dumps(small_candidates(base,roms),indent=2)+'\n')
    (HERE/'LATEST.json').write_text(json.dumps({'run':str(out),'report':str(out/'crossrom_regression.json'),'sha256':digest((out/'crossrom_regression.json').read_bytes())},indent=2)+'\n')
    print(json.dumps({'status':'PASS','run':str(out),'counts':summary['counts'],'output_digest':summary['deterministic_output_digest']},indent=2),flush=True)

if __name__=='__main__':main()
