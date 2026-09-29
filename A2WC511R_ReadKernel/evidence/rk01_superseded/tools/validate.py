"""Read-only, hash-linked acquisition TOOL validator. Never loads a provider.

The release index is explicit: missing evidence fails rather than being replaced
by the newest similarly named file. Physical claims are separate from software.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,json
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from artifact_review import verify as artifact_review,PIN
FIXTURES={
 'stock':'22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218',
 'composite':'b91ad3e88637bfae6a15871761c288f914fe10fe74c78cbc53e963c4fe80e545',
 'random':'988a6d620df4396bd5b6d72572ecaba99006b891110dba6a8ad9b32ba1444b9b'}
# Mandatory gate semantics belong to this reviewed checker, not caller-supplied
# assertions in the evidence index. Additional assertions can only tighten it.
FIXED_GATES={
 'STATIC_NO_FLASH_WRITE_PATH':('evidence/contracts/BINARY_REVIEW_attempt_03.json',{
   'status':'PASS_FIXED_BINARY_STRUCTURAL_STORE_AND_CONTROL_CONTRACT','kernel_sha256':PIN,
   'instruction_count':319,'flash_stores':0,'prohibited_accesses':0,'computed_executable_calls':0,'external_OEM_calls':0}),
 'SIMULATOR_EXECUTION_COVERAGE':('evidence/sim/QUALIFICATION.json',{
   'status':'PASS','kernel_sha256':PIN,'instruction_covered':319,'instruction_total':319,
   'instruction_missing':[],'branches_total':39,'branch_directions_covered':78,'stack_max_bytes':8,
   'unsupported_executed_instruction_count':0,'unsupported_executed_MMIO_count':0}),
 'LOSSLESS_FULL_IMAGE_FIXTURES':('evidence/LOSSLESS_FIXTURES.json',{'status':'PASS','kernel_sha256':PIN,'failures':[]}),
 'HOST_FIXED_ALLOWLIST':('host/HOST_QUALIFICATION.json',{'status':'PASS','kernel_sha256':PIN,'fixed_only':True,
   'all_TX_prefixes_replayed':True,'physical_provider_loaded':False}),
 'FAKE_PROVIDER_ACTUAL_KERNEL_EXECUTION':('fake/runs/composite_native04/RESULT.json',{
   'status':'PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS','CPU_kernel_executed':True,
   'kernel_terminal':'COMPLETE','kernel_exchanges':4098,'full_bytes_per_pass':1048576,'physical':False}),
 'FAULT_INJECTION':('host/HOST_FAULTS.json',{'status':'PASS','failures':[]}),
 'OEM_UPLOAD_ENTRY_CONTRACT':('evidence/contracts/OEM_ACQUISITION_CONTRACT.json',{
   'status':'PASS','kernel_sha256':PIN,'complete_fixed_protocol':True,'security_preserved':True,
   'flash_controller_stores_on_admitted_path':0}),
 'EVIDENCE_PRESERVATION':('evidence/FINAL_PRESERVATION.json',{
   'status':'PASS','failures':[],'real_registry_unchanged':True,'physical_provider_loaded':False})}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def pointer(obj,path):
    for key in path:
        obj=obj[key]
    return obj

def validate(index):
    errors=[];checks=[];cache={}
    def record(name,ok,details=None):
        item={'gate':name,'status':'PASS' if ok else 'FAIL'}
        if details is not None:item['details']=details
        checks.append(item)
        if not ok:errors.append(name)
    record('ARTIFACT_CLASS',index.get('artifact_class')=='TEMP_RAM_ACQUISITION_TOOL')
    record('EXACT_KERNEL_PIN',index.get('kernel_sha256')==PIN)
    for f in index.get('files',[]):
        p=Path(f['path'])
        if not p.is_absolute():p=ROOT/p
        try:ok=p.is_file() and sha(p)==f['sha256'] and p.stat().st_size==f['bytes']
        except OSError:ok=False
        record('HASH:'+f['path'],ok)
    record('NONEMPTY_EVIDENCE_SEAL',len(index.get('files',[]))>=10)
    sealed={str((ROOT/x['path']).resolve() if not Path(x['path']).is_absolute() else Path(x['path']).resolve()):x for x in index.get('files',[])}
    record('UNIQUE_EVIDENCE_PATHS',len(sealed)==len(index.get('files',[])))
    def read_bytes(p):
        p=Path(p).resolve()
        if str(p) not in sealed:raise ValueError('Unsealed referenced evidence: '+str(p))
        raw=p.read_bytes();reference=sealed[str(p)]
        if hashlib.sha256(raw).hexdigest()!=reference['sha256'] or len(raw)!=reference['bytes']:
            raise ValueError('Used evidence bytes differ from sealed hash: '+str(p))
        return raw
    def read(rel):
        p=(ROOT/rel).resolve()
        if str(p) not in cache:cache[str(p)]=json.loads(read_bytes(p))
        return cache[str(p)]
    try:
        result=artifact_review(ROOT/index['build_manifest'],ROOT/index['repro_manifest'])
        record('PINNED_TOOLCHAIN_SOURCE_REPRODUCIBILITY_LAYOUT',result['status']=='PASS',result['errors'])
    except (OSError,ValueError,KeyError,AssertionError) as e:record('PINNED_TOOLCHAIN_SOURCE_REPRODUCIBILITY_LAYOUT',False,str(e))
    for gate in index.get('software_gates',[]):
        try:
            doc=read(gate['report'])
            mismatches=[]
            if gate['id'] in FIXED_GATES:
                expected_report,requirements=FIXED_GATES[gate['id']]
                if (ROOT/gate['report']).resolve()!=(ROOT/expected_report).resolve():
                    mismatches.append({'error':'Mandatory report path mismatch'})
                for key,value in requirements.items():
                    if doc.get(key)!=value:mismatches.append({'path':[key],'actual':doc.get(key),'expected':value})
            for assertion in gate['assertions']:
                actual=pointer(doc,assertion['path'])
                if actual!=assertion['equals']:mismatches.append({'path':assertion['path'],'actual':actual,'expected':assertion['equals']})
            record(gate['id'],bool(gate['assertions'] or gate['id'] in FIXED_GATES) and not mismatches,mismatches)
        except (OSError,ValueError,KeyError,IndexError,TypeError) as e:record(gate['id'],False,str(e))
    required=set(FIXED_GATES)
    record('REQUIRED_SOFTWARE_GATES',required<={x.get('id') for x in index.get('software_gates',[])})
    try:
        faults=read('host/HOST_FAULTS.json')
        required_faults={'identity','upload_begin','upload_middle','upload_final','entry','version',
          'read_begin','read_middle','read_final','read_disconnect','read_checksum','read_address',
          'read_duplicate','read_pass','read_truncate','read_extra','read_opcode','host_termination'}
        missing=required_faults-set(faults['cases']);bad=[]
        for name,case in faults['cases'].items():
            if case['status']!='PASS' or case['kernel_sha256']!=PIN or case['physical'] is not False:bad.append(name)
            for key in ('result','fixed_TX_prefix_replay'):
                reference=case[key];doc=read(reference['path'])
                if sha(reference['path'])!=reference['sha256']:bad.append(name+':hash')
                expected='PASS_EXPECTED_TERMINAL_FAULT' if key=='result' else 'PASS_FIXED_TX_PREFIX'
                if doc['status']!=expected:bad.append(name+':'+key)
        record('REQUIRED_NATIVE_FAULTS_AND_CLOSED_TX_PREFIXES',not missing and not bad,
               {'missing':sorted(missing),'invalid':bad,'cases':len(faults['cases'])})
    except (OSError,ValueError,KeyError,IndexError,TypeError) as e:record('REQUIRED_NATIVE_FAULTS_AND_CLOSED_TX_PREFIXES',False,str(e))
    # Independently check every compiled instruction and conditional direction,
    # instead of accepting a report's percentage or PASS label.
    try:
        m=read(index['build_manifest']);c=read(index['aggregate_coverage'])
        record('COVERAGE_BINARY_IDENTITY',c['kernel_sha256']==m['kernel_sha256']==PIN)
        recomputed_counts=Counter();recomputed_edges=Counter();recomputed_writes=Counter();stack=[]
        for item in c['inputs']:
            d=read(item['path'])
            if sha(item['path'])!=item['sha256']:raise ValueError('Coverage input hash mismatch')
            if d.get('kernel_sha256',d.get('identity',{}).get('kernel_sha256'))!=PIN:raise ValueError('Coverage input binary mismatch')
            recomputed_counts.update(d['instruction_counts'])
            recomputed_edges.update({(e['from'],e['to']):e['count'] for e in d['edges']})
            recomputed_writes.update({(w['address'],w['size'],w['pc']):w['count'] for w in d['writes']})
            stack.append(d['stack_max_bytes'])
        record('COVERAGE_AGGREGATE_RECONCILIATION',len(c['inputs'])==2 and bool(recomputed_writes)
          and dict(recomputed_counts)==c['instruction_counts']
          and dict(recomputed_edges)=={(e['from'],e['to']):e['count'] for e in c['edges']}
          and dict(recomputed_writes)=={(w['address'],w['size'],w['pc']):w['count'] for w in c['writes']}
          and max(stack)==c['stack_max_bytes'])
        observed={int(a,16) for a,n in c['instruction_counts'].items() if n>0}
        executable=set(m['instruction_addresses'])
        record('ALL_EMITTED_INSTRUCTIONS',observed==executable and not c.get('unreachable_instructions'),
               {'executed':len(observed),'total':len(executable),'missing':sorted(executable-observed)})
        observed_edges={(int(e['from'],16),int(e['to'],16)) for e in c['edges'] if e['count']>0}
        missing=[]
        for ins in m['instructions']:
            op=ins['opcode'];a=ins['address']
            if op&0xff00 in (0x8900,0x8b00):
                offset=op&255;offset=offset-256 if offset&128 else offset
                for target in (a+2,(a+4+2*offset)&0xffffffff):
                    if (a,target) not in observed_edges:missing.append([a,target])
            elif op&0xff00 in (0x8d00,0x8f00):
                raise ValueError('New delayed conditional needs an explicitly reviewed edge checker')
        record('ALL_CONDITIONAL_DIRECTIONS',not missing,missing)
        record('EXACT_STACK_BOUND',c['stack_max_bytes']==8 and c['software_stack_bytes']==0 and m['stack_high']-m['stack_low']==16)
        legal_mmio={(0xffffecb0,2),(0xffffec10,2),(0xfffff010,1),(0xfffff011,1),(0xfffff012,1),
                    (0xfffff013,1),(0xfffff014,1),(0xfffff016,1),(0xfffff73c,2)}
        invalid=[]
        for w in c['writes']:
            address=int(w['address'],16);size=w['size'];pc=int(w['pc'],16)
            ram=0xffff36f0<=address and address+size<=0xffff3710
            if not (ram or (address,size) in legal_mmio) or pc not in executable:invalid.append(w)
        record('EVERY_OBSERVED_STORE_DECLARED',bool(c['writes']) and not invalid,invalid)
    except (OSError,ValueError,KeyError,IndexError,TypeError) as e:record('COMPILED_COVERAGE_CROSSCHECK',False,str(e))
    # Compare retained bytes directly, never just a success flag or CRC.
    fixture_results=[]
    try:
        for f in index['fixtures']:
            p=(ROOT/f['fixture']).resolve();outputs=[(ROOT/x).resolve() for x in f['outputs']]
            if str(p) not in sealed or any(str(q) not in sealed for q in outputs):raise ValueError('Unsealed fixture/image')
            original=read_bytes(p);original_sha=hashlib.sha256(original).hexdigest()
            ok=len(original)==0x100000 and len(outputs)==2 and outputs[0]!=outputs[1]
            ok=ok and original_sha==FIXTURES[f['id']] and all(read_bytes(q)==original for q in outputs)
            execution=read(f['coverage'])
            ok=ok and execution['identity']['kernel_sha256']==PIN and execution['terminal']=='COMPLETE'
            ok=ok and len(execution['exchanges'])==4098 and all(e['status']=='PASS' for e in execution['exchanges'])
            ok=ok and execution['instruction_counts']['FFFF3260']==2*1048576+15
            fixture_results.append({'fixture':f['id'],'pass':ok,'sha256':original_sha})
        names={f['id'] for f in index['fixtures']}
        record('BYTE_FOR_BYTE_TWO_FULL_READS',set(FIXTURES)==names and len(index['fixtures'])==3
               and len({f['sha256'] for f in fixture_results})==3 and all(f['pass'] for f in fixture_results),fixture_results)
    except (OSError,ValueError,KeyError,TypeError) as e:record('BYTE_FOR_BYTE_TWO_FULL_READS',False,str(e))
    physical=index.get('physical_gates',[])
    record('PHYSICAL_CLAIMS_SEPARATE',len(physical)>=5 and all(x['status']=='PHYSICAL_REQUIRED' for x in physical))
    status='FAIL' if errors else ('CONDITIONAL' if physical else 'PASS')
    return {'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','kernel_sha256':PIN,
      'status':status,'software_status':'FAIL' if errors else 'PASS','failed_checks':errors,
      'checks':checks,'physical_gates':physical,'provider_loaded':False,'physical_operations':False,
      'ECU_ROM_release':False,'current_ROM_identified':False,
      'installed_ECUFlash_universal_exactness':'PERMANENTLY_REJECTED',
      'next_acquisition_connection_software_eligible':not errors,
      'limitations':['This validator verifies pinned prior execution evidence; it does not execute a provider or vehicle.',
       'CONDITIONAL means software checks passed with explicit physical assumptions; it is not hardware acceptance.',
       'A temporary RAM object is never an ECU flash image or a pre-flash release.']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path);args=parser.parse_args()
    p=ROOT/'QUALIFICATION_INPUTS.json'
    try:
        index=json.loads(p.read_text());result=validate(index);result['input_index_sha256']=sha(p)
    except (OSError,ValueError,KeyError,TypeError) as e:
        result={'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','status':'FAIL','software_status':'FAIL',
                'failed_checks':['MISSING_OR_INVALID_QUALIFICATION_INDEX'],'details':str(e),'provider_loaded':False}
    result['validator_sha256']=sha(Path(__file__))
    text=json.dumps(result,indent=2)+'\n'
    if args.report:
        with args.report.open('x',encoding='utf-8') as f:f.write(text)
        print(json.dumps({'status':result['status'],'software_status':result['software_status'],'report':str(args.report.resolve()),'sha256':sha(args.report)}))
    else:print(text,end='')
    return 1 if result['status']=='FAIL' else 0

if __name__=='__main__':raise SystemExit(main())
