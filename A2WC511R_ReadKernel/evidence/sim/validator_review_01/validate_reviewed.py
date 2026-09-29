"""Read-only, hash-linked acquisition TOOL validator. Never loads a provider.

The release index is explicit: missing evidence fails rather than being replaced
by the newest similarly named file. Physical claims are separate from software.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from artifact_review import verify as artifact_review,PIN

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
    sealed={str((ROOT/x['path']).resolve() if not Path(x['path']).is_absolute() else Path(x['path']).resolve()) for x in index.get('files',[])}
    def read(rel):
        p=(ROOT/rel).resolve()
        if str(p) not in sealed:raise ValueError('Unsealed referenced evidence: '+str(p))
        if str(p) not in cache:cache[str(p)]=json.loads(p.read_text())
        return cache[str(p)]
    try:
        result=artifact_review(ROOT/index['build_manifest'],ROOT/index['repro_manifest'])
        record('PINNED_TOOLCHAIN_SOURCE_REPRODUCIBILITY_LAYOUT',result['status']=='PASS',result['errors'])
    except (OSError,ValueError,KeyError,AssertionError) as e:record('PINNED_TOOLCHAIN_SOURCE_REPRODUCIBILITY_LAYOUT',False,str(e))
    for gate in index.get('software_gates',[]):
        try:
            doc=read(gate['report'])
            mismatches=[]
            for assertion in gate['assertions']:
                actual=pointer(doc,assertion['path'])
                if actual!=assertion['equals']:mismatches.append({'path':assertion['path'],'actual':actual,'expected':assertion['equals']})
            record(gate['id'],bool(gate['assertions']) and not mismatches,mismatches)
        except (OSError,ValueError,KeyError,IndexError,TypeError) as e:record(gate['id'],False,str(e))
    required={'STATIC_NO_FLASH_WRITE_PATH','SIMULATOR_EXECUTION_COVERAGE','LOSSLESS_FULL_IMAGE_FIXTURES',
              'HOST_FIXED_ALLOWLIST','FAKE_PROVIDER_ACTUAL_KERNEL_EXECUTION','FAULT_INJECTION',
              'OEM_UPLOAD_ENTRY_CONTRACT','EVIDENCE_PRESERVATION'}
    record('REQUIRED_SOFTWARE_GATES',required<={x.get('id') for x in index.get('software_gates',[])})
    # Independently check every compiled instruction and conditional direction,
    # instead of accepting a report's percentage or PASS label.
    try:
        m=read(index['build_manifest']);c=read(index['aggregate_coverage'])
        observed={int(a,16) for a,n in c['instruction_counts'].items() if n>0}
        executable=set(m['instruction_addresses'])
        classified={int(x['address'],16) for x in c.get('unreachable_instructions',[]) if x.get('proof')}
        record('ALL_EMITTED_INSTRUCTIONS',not (executable-observed-classified) and observed<=executable,
               {'executed':len(observed),'total':len(executable),'missing':sorted(executable-observed-classified)})
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
        record('EVERY_OBSERVED_STORE_DECLARED',not invalid,invalid)
    except (OSError,ValueError,KeyError,IndexError,TypeError) as e:record('COMPILED_COVERAGE_CROSSCHECK',False,str(e))
    # Compare retained bytes directly, never just a success flag or CRC.
    fixture_results=[]
    try:
        for f in index['fixtures']:
            p=(ROOT/f['fixture']).resolve();outputs=[(ROOT/x).resolve() for x in f['outputs']]
            if str(p) not in sealed or any(str(q) not in sealed for q in outputs):raise ValueError('Unsealed fixture/image')
            original=p.read_bytes();ok=len(original)==0x100000 and len(outputs)==2 and outputs[0]!=outputs[1]
            ok=ok and all(q.read_bytes()==original for q in outputs)
            fixture_results.append({'fixture':f['id'],'pass':ok,'sha256':sha(p)})
        names={f['id'] for f in index['fixtures']}
        record('BYTE_FOR_BYTE_TWO_FULL_READS',{'stock','composite','random'}<=names and all(f['pass'] for f in fixture_results),fixture_results)
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
