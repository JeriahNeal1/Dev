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
CORE_PATH=Path(r'C:\Dev\A2WC511R_Sim\sh2e.py')
CORE_SHA='b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff'
MODEL_NAMES={'__init__.py','core.py','cpu.py','fast_step.py','harness.py','memory.py','sci.py','self_echo.py'}
HOST_SHA='4b681bcdb3c178b89382b37b207b4a7679f0a1e87ab13c7051e8cf8019c094ec'
PHYSICAL_IDS={'ACTUAL_OPENPORT_ELECTRICAL_UART','ACTUAL_CURRENT_ECU_LOADER_ACCEPTANCE',
 'CLOCK_RAM_UPLOAD_AND_ENTRY','EXTERNAL_WATCHDOG_AND_NMI','POWER_DOWN_OEM_RESTART','PHYSICAL_CAPTURE_CURRENT_ROM_ASSOCIATION'}
FIXTURES={
 'stock':'22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218',
 'composite':'b91ad3e88637bfae6a15871761c288f914fe10fe74c78cbc53e963c4fe80e545',
 'random':'988a6d620df4396bd5b6d72572ecaba99006b891110dba6a8ad9b32ba1444b9b'}
# Mandatory gate semantics belong to this reviewed checker, not caller-supplied
# assertions in the evidence index. Additional assertions can only tighten it.
FIXED_GATES={
 'STATIC_NO_FLASH_WRITE_PATH':('evidence/contracts/BINARY_REVIEW_rk02_01.json',{
   'status':'PASS_FIXED_BINARY_STRUCTURAL_STORE_AND_CONTROL_CONTRACT','kernel_sha256':PIN,
   'instruction_count':335,'store_count':22,'flash_stores':0,'prohibited_accesses':0,'computed_executable_calls':0,'external_OEM_calls':0}),
 'SIMULATOR_EXECUTION_COVERAGE':('evidence/rk02/sim/QUALIFICATION.json',{
   'status':'PASS','kernel_sha256':PIN,'instruction_covered':335,'instruction_total':335,
   'instruction_missing':[],'branches_total':40,'branch_directions_covered':80,'stack_max_bytes':8,
   'unsupported_executed_instruction_count':0,'unsupported_executed_MMIO_count':0}),
 'LOSSLESS_FULL_IMAGE_FIXTURES':('evidence/rk02/LOSSLESS_FIXTURES.json',{'status':'PASS','kernel_sha256':PIN,'failures':[]}),
 'HOST_FIXED_ALLOWLIST':('evidence/rk02/host/HOST_QUALIFICATION.json',{'status':'PASS','kernel_sha256':PIN,'fixed_only':True,
   'all_TX_prefixes_replayed':True,'physical_provider_loaded':False}),
 'FAKE_PROVIDER_ACTUAL_KERNEL_EXECUTION':('fake/runs/rk02_composite_01/RESULT.json',{
   'status':'PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS','CPU_kernel_executed':True,
   'kernel_terminal':'COMPLETE','kernel_exchanges':4098,'full_bytes_per_pass':1048576,'physical':False}),
 'FAULT_INJECTION':('evidence/rk02/host/HOST_FAULTS.json',{'status':'PASS','failures':[]}),
 'OEM_UPLOAD_ENTRY_CONTRACT':('evidence/contracts/OEM_ACQUISITION_CONTRACT_RK02.json',{
   'status':'PASS','kernel_sha256':PIN,'complete_fixed_protocol':True,'security_preserved':True,
   'flash_controller_stores_on_admitted_path':0}),
 'EVIDENCE_PRESERVATION':('evidence/rk02/FINAL_PRESERVATION.json',{
   'status':'PASS','failures':[],'real_registry_unchanged':True,'physical_provider_loaded':False}),
 'RK01_PERMANENTLY_SUPERSEDED':('evidence/RK01_SUPERSEDED.json',{
   'status':'SUPERSEDED_NOT_FOR_HARDWARE','permanent':True,'no_requalification_of_RK01_permitted':True}),
 'HALF_DUPLEX_SELF_ECHO':('evidence/rk02/sim/SELF_ECHO_QUALIFICATION.json',{
   'status':'PASS','kernel_sha256':PIN})}

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
    errors=[];checks=[];cache={};binding={}
    def record(name,ok,details=None):
        item={'gate':name,'status':'PASS' if ok else 'FAIL'}
        if details is not None:item['details']=details
        checks.append(item)
        if not ok:errors.append(name)
    record('ARTIFACT_CLASS',index.get('artifact_class')=='TEMP_RAM_ACQUISITION_TOOL')
    record('EXACT_KERNEL_PIN',index.get('kernel_sha256')==PIN)
    record('SUPPORTED_RELEASE_STAGE',index.get('stage') in ('SOFTWARE_QUALIFICATION','FINAL_RK02_ACQUISITION_STACK'))
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
        p=(ROOT/Path(p)).resolve()
        if str(p) not in sealed:raise ValueError('Unsealed referenced evidence: '+str(p))
        raw=p.read_bytes();reference=sealed[str(p)]
        if hashlib.sha256(raw).hexdigest()!=reference['sha256'] or len(raw)!=reference['bytes']:
            raise ValueError('Used evidence bytes differ from sealed hash: '+str(p))
        return raw
    def read(rel):
        p=(ROOT/rel).resolve()
        if str(p) not in cache:cache[str(p)]=json.loads(read_bytes(p))
        return cache[str(p)]
    def model_pins(d):
        if set(d)!=MODEL_NAMES:raise ValueError('Incomplete model source association')
        for name,digest in d.items():
            if hashlib.sha256(read_bytes(ROOT/'sim'/name)).hexdigest()!=digest:
                raise ValueError('Executed simulator source changed: '+name)
        if hashlib.sha256(read_bytes(CORE_PATH)).hexdigest()!=CORE_SHA:raise ValueError('Frozen CPU core changed')
    def execution_identity(d):
        if d['kernel_sha256']!=PIN or d['kernel_bytes']!=1808:raise ValueError('Executed object changed')
        if Path(d['core_path']).resolve()!=CORE_PATH or d['core_sha256']!=CORE_SHA:raise ValueError('Frozen CPU association absent')
        if d['manifest_sha256']!=hashlib.sha256(read_bytes(ROOT/'build/rk02_01/manifest.json')).hexdigest():
            raise ValueError('Executed build manifest mismatch')
        model_pins(d['model_sources'])
    try:
        required_sources=[ROOT/'tools'/n for n in ('validate.py','artifact_review.py','build.py','build_checked.py')]
        required_sources += [ROOT/'src/kernel.S',ROOT/'linker/kernel.ld']
        required_sources += [ROOT/'evidence/contracts/review_physical_derivation_rk02.py']
        required_sources += [ROOT/'build'/folder/name for folder in ('rk02_01','rk02_repro_01')
          for name in ('manifest.json','kernel.bin','kernel.elf')]
        for p in required_sources:read_bytes(p)
        record('REQUIRED_REVIEWED_SOURCE_SEAL',True)
    except (OSError,ValueError,KeyError,TypeError) as e:record('REQUIRED_REVIEWED_SOURCE_SEAL',False,str(e))
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
    ids=[x.get('id') for x in index.get('software_gates',[])]
    record('REQUIRED_SOFTWARE_GATES',required<=set(ids) and len(ids)==len(set(ids)))
    try:
        binding=read('host/build/native_05/binding.json')
        host=read('evidence/rk02/host/HOST_QUALIFICATION.json')
        ok=binding['kernel_sha256']==PIN and binding['kernel_bytes']==1808
        ok=ok and binding['version_hex']==b'A2WC511R-RK02\0'.hex()
        ok=ok and binding['load_address']=='FFFF3000' and binding['entry_address']=='FFFF3004'
        ok=ok and binding['physical'] is False and binding['physical_provider_supported'] is False
        exe=read_bytes(binding['client_path'])
        ok=ok and Path(binding['client_path']).resolve()==ROOT/'host/build/native_05/owned_read32.exe'
        ok=ok and hashlib.sha256(exe).hexdigest()==binding['client_sha256']==host['final_fake_host_sha256']==HOST_SHA
        build=read('host/build/native_05/BUILD_MANIFEST.json')
        expected_host_files={ROOT/p for p in ('host/native.cpp','host/build.py','host/protocol.py',
          'host/vendor/j2534_tactrix.h','fake/native/a2wc_readkernel_fake32.dll')}
        expected_host_files|={ROOT/'host/build/native_05'/n for n in ('owned_artifact.h','owned_read32.exe','build.cmd','selftest.log','build.log','binding.json')}
        ok=ok and build['binding']==binding and len(build['files'])==len(expected_host_files)
        ok=ok and {Path(x['path']).resolve() for x in build['files']}==expected_host_files
        for item in build['files']:
            if hashlib.sha256(read_bytes(item['path'])).hexdigest()!=item['sha256']:ok=False
        record('EXACT_TESTED_NATIVE_HOST_AND_SOURCE_ASSOCIATION',ok)
    except (OSError,ValueError,KeyError,TypeError) as e:record('EXACT_TESTED_NATIVE_HOST_AND_SOURCE_ASSOCIATION',False,str(e))
    try:
        t=read('evidence/rk02/host/NATIVE_TOOLCHAIN.json')
        ok=t['status']=='PASS_COMPILE_ONLY_TOOLCHAIN_IDENTIFICATION' and t['provider_loaded'] is False
        for name in ('compiler','linker','vcvars32','native05_command','compiler_version_output','linker_version_output'):
            item=t[name]
            ok=ok and hashlib.sha256(read_bytes(item['path'])).hexdigest()==item['sha256']
        record('NATIVE_TOOLCHAIN_ASSOCIATION',ok)
    except (OSError,ValueError,KeyError,TypeError) as e:record('NATIVE_TOOLCHAIN_ASSOCIATION',False,str(e))
    try:
        host=read('evidence/rk02/host/HOST_QUALIFICATION.json');ok=True
        for name in ('final_native_full_run','faults','native_journal_only_finalization','finalizer_adversarial_tests',
                     'pure_host_contract_tests','pure_stream_tests','final_build','native_toolchain','source_transition'):
            item=host[name]
            ok=ok and hashlib.sha256(read_bytes(item['path'])).hexdigest()==item['sha256']
        expected_sources={ROOT/p for p in ('host/native.cpp','host/protocol.py','host/state.py','host/stream.py',
          'host/run.py','host/finalize.py','host/report_rk02.py','fake/model.py','fake/server.py')}
        ok=ok and len(host['source_files'])==len(expected_sources)
        ok=ok and {Path(x['path']).resolve() for x in host['source_files']}==expected_sources
        for item in host['source_files']:
            ok=ok and hashlib.sha256(read_bytes(item['path'])).hexdigest()==item['sha256']
        ok=ok and len(host['full_fixtures'])==2
        ok=ok and {Path(x['result']['path']).resolve() for x in host['full_fixtures']}=={
          ROOT/'fake/runs/rk02_composite_01/RESULT.json',ROOT/'fake/runs/rk02_random_01/RESULT.json'}
        for fixture in host['full_fixtures']:
            for name in ('result','execution_coverage'):
                item=fixture[name]
                ok=ok and hashlib.sha256(read_bytes(item['path'])).hexdigest()==item['sha256']
            model_pins(fixture['model_sources'])
            ok=ok and fixture['receiver_self_echo'] is True and fixture['kernel_terminal']=='COMPLETE'
            ok=ok and fixture['kernel_exchanges']==4098 and fixture['completed_TX_characters']==2142228
            ok=ok and fixture['self_echo_characters_ignored_RE0']==2142228
        finalizer=read(host['native_journal_only_finalization']['path'])
        ok=ok and finalizer['status']=='PASS_RAW_CAPTURE_INTEGRITY' and finalizer['kernel_sha256']==PIN
        ok=ok and finalizer['client_sha256']==HOST_SHA and finalizer['current_ROM_identified'] is False
        tests=[('finalizer_adversarial_tests','count',28),('pure_host_contract_tests','count',33),('pure_stream_tests','fragmented_positive_cases',32)]
        for name,field,count in tests:
            d=read(host[name]['path']);ok=ok and d['status']=='PASS' and d[field]==count
        record('HOST_FINALIZER_AND_TERMINAL_TEST_ASSOCIATION',ok)
    except (OSError,ValueError,KeyError,TypeError) as e:record('HOST_FINALIZER_AND_TERMINAL_TEST_ASSOCIATION',False,str(e))
    try:
        echo=read('evidence/rk02/sim/SELF_ECHO_QUALIFICATION.json');model_pins(echo['model_sources'])
        positives={'no_echo','every_byte_echo','delayed_completion_after_RX_restore','only_final_bytes_echo',
          'fragmented_requests_every_byte_echo','entry_stale_RDRF_and_error_flags_cleared'}
        negatives={'pre_TX_residual_SSR_'+x for x in ('40','20','10','08','78')}|{'new_post_RX_noise_start_rejected','genuinely_late_echo_start_rejected'}
        ok=echo['case_count']==len(echo['cases'])==13 and {x['case'] for x in echo['cases']}==positives|negatives
        for case in echo['cases']:
            execution_identity(case['identity'])
            ok=ok and case['expected_outcome']==('RX_WAIT' if case['case'] in positives else 'KERNEL_REJECT')
            for transition in case['SCR_writes']:
                if transition['value']==0x10:
                    ok=ok and transition['SSR_before']&4!=0 and transition['pending_before'] is None and transition['buffer_before'] is None
        old=echo['RK01_negative_control']
        ok=ok and old['kernel_sha256']=='3d70abfb8617b87e1b9c52724fd27ed4066ba231818994e780c8ba3006de273f'
        ok=ok and old['observed_outcome']=='KERNEL_REJECT' and old['included_in_RK02_coverage'] is False
        ok=ok and old['SCI_event_counts']['ECU_self_echo_overrun']>0
        ok=ok and hashlib.sha256(read_bytes(echo['coverage']['path'])).hexdigest()==echo['coverage']['sha256']
        record('HALF_DUPLEX_CASES_AND_MODEL_ASSOCIATION',ok)
    except (OSError,ValueError,KeyError,TypeError) as e:record('HALF_DUPLEX_CASES_AND_MODEL_ASSOCIATION',False,str(e))
    try:
        faults=read('evidence/rk02/host/HOST_FAULTS.json')
        required_faults={'identity','upload_begin','upload_middle','upload_final','entry','version',
          'read_begin','read_middle','read_final','read_disconnect','read_checksum','read_address',
          'read_duplicate','read_pass','read_truncate','read_extra','read_opcode','host_termination',
          'rx_status','rx_extra','rx_echo','rx_empty'}
        missing=required_faults-set(faults['cases']);bad=[]
        for name,case in faults['cases'].items():
            if case['status']!='PASS' or case['kernel_sha256']!=PIN or case['physical'] is not False:bad.append(name)
            if case['host_sha256']!=binding['client_sha256']:bad.append(name+':host')
            for key in ('result','fixed_TX_prefix_replay'):
                reference=case[key];doc=read(reference['path'])
                if sha(reference['path'])!=reference['sha256']:bad.append(name+':hash')
                expected='PASS_EXPECTED_TERMINAL_FAULT' if key=='result' else 'PASS_FIXED_TX_PREFIX'
                if doc['status']!=expected:bad.append(name+':'+key)
                if key=='fixed_TX_prefix_replay' and doc['host_summary']['kernel_sha256']!=PIN:bad.append(name+':kernel')
        record('REQUIRED_NATIVE_FAULTS_AND_CLOSED_TX_PREFIXES',not missing and not bad,
               {'missing':sorted(missing),'invalid':bad,'cases':len(faults['cases'])})
    except (OSError,ValueError,KeyError,IndexError,TypeError) as e:record('REQUIRED_NATIVE_FAULTS_AND_CLOSED_TX_PREFIXES',False,str(e))
    # Independently check every compiled instruction and conditional direction,
    # instead of accepting a report's percentage or PASS label.
    try:
        m=read(index['build_manifest']);c=read(index['aggregate_coverage'])
        record('COVERAGE_BINARY_IDENTITY',c['kernel_sha256']==m['kernel_sha256']==PIN)
        recomputed_counts=Counter();recomputed_edges=Counter();recomputed_writes=Counter();stack=[]
        expected_coverage={ROOT/'evidence/rk02/sim'/p for p in ('stock_full_01/coverage.json','faults_01/coverage.json','echo_cases_01/coverage.json')}
        record('FIXED_RK02_COVERAGE_INPUTS',{Path(x['path']).resolve() for x in c['inputs']}==expected_coverage)
        fault_provenance=read('evidence/rk02/sim/faults_01/FAULTS.json');model_pins(fault_provenance['model_sources'])
        if fault_provenance['coverage']['sha256']!=hashlib.sha256(read_bytes(ROOT/'evidence/rk02/sim/faults_01/coverage.json')).hexdigest():
            raise ValueError('Fault execution coverage association')
        if fault_provenance['status']!='PASS' or fault_provenance['kernel_sha256']!=PIN:raise ValueError('Fault execution mismatch')
        for item in c['inputs']:
            d=read(item['path'])
            if sha(item['path'])!=item['sha256']:raise ValueError('Coverage input hash mismatch')
            if d.get('kernel_sha256',d.get('identity',{}).get('kernel_sha256'))!=PIN:raise ValueError('Coverage input binary mismatch')
            if 'identity' in d:execution_identity(d['identity'])
            recomputed_counts.update(d['instruction_counts'])
            recomputed_edges.update({(e['from'],e['to']):e['count'] for e in d['edges']})
            recomputed_writes.update({(w['address'],w['size'],w['pc']):w['count'] for w in d['writes']})
            stack.append(d['stack_max_bytes'])
        record('COVERAGE_AGGREGATE_RECONCILIATION',len(c['inputs'])>=2 and bool(recomputed_writes)
          and len({x['path'] for x in c['inputs']})==len(c['inputs'])
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
        static=read('evidence/contracts/BINARY_REVIEW_rk02_01.json')
        store_domains={int(x['pc'],16):x for x in static['store_domains']}
        decoded_stores={i['address'] for i in m['instructions']
            if (i['opcode']&0xf00f in (0x2000,0x2001,0x2002)) or i['opcode']&0xff00==0x8000}
        record('COMPLETE_UNIQUE_STATIC_STORE_DOMAINS',len(static['store_domains'])==len(store_domains)==22
              and set(store_domains)==decoded_stores)
        for w in c['writes']:
            address=int(w['address'],16);size=w['size'];pc=int(w['pc'],16)
            ram=0xffff3710<=address and address+size<=0xffff3730
            if not (ram or (address,size) in legal_mmio) or pc not in executable:invalid.append(w)
            # An exception frame is explicit hardware entry, not a CPU store.
            hardware=(pc==m['rx_poll'] and size==4 and address in (m['stack_high']-4,m['stack_high']-8))
            if not hardware:
                domain=store_domains.get(pc)
                if domain is None or domain['width']!=size:invalid.append(w)
                elif not int(domain['destination_range'][0],16)<=address<address+size<=int(domain['destination_range'][1],16):invalid.append(w)
        record('EVERY_OBSERVED_STORE_DECLARED',bool(c['writes']) and not invalid,invalid)
        record('ALL_STATIC_STORE_SITES_EXECUTED',set(store_domains)<={int(x['pc'],16) for x in c['writes']})
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
            ok=ok and execution['identity']['receiver_self_echo'] is True
            ok=ok and len(execution['exchanges'])==4098 and all(e['status']=='PASS' for e in execution['exchanges'])
            ok=ok and execution['instruction_counts']['FFFF3260']==2*1048576+15
            events=execution['SCI_event_counts'];wire_bytes=4096*523+20
            ok=ok and events.get('tx_character_complete')==wire_bytes
            ok=ok and events.get('ECU_self_echo_ignored_RE0')==wire_bytes
            ok=ok and events.get('ECU_self_echo_start_RE0')==wire_bytes
            ok=ok and events.get('ECU_self_echo_received',0)==events.get('ECU_self_echo_overrun',0)==0
            execution_identity(execution['identity'])
            fixture_results.append({'fixture':f['id'],'pass':ok,'sha256':original_sha})
        names={f['id'] for f in index['fixtures']}
        record('BYTE_FOR_BYTE_TWO_FULL_READS',set(FIXTURES)==names and len(index['fixtures'])==3
               and len({f['sha256'] for f in fixture_results})==3 and all(f['pass'] for f in fixture_results),fixture_results)
    except (OSError,ValueError,KeyError,TypeError) as e:record('BYTE_FOR_BYTE_TWO_FULL_READS',False,str(e))
    physical=index.get('physical_gates',[])
    record('PHYSICAL_CLAIMS_SEPARATE',len(physical)==len(PHYSICAL_IDS)
      and {x.get('id') for x in physical}==PHYSICAL_IDS and all(x['status']=='PHYSICAL_REQUIRED' for x in physical))
    try:
        superseded=read('evidence/RK01_SUPERSEDED.json')
        if hashlib.sha256(read_bytes(ROOT/'evidence/RK01_SUPERSEDED.json')).hexdigest()!='45fe930a4bd97cd34cf1e4c81d0e27926a2871fda7d9a8ea6f7c8486aff5f85b':
            raise ValueError('Fixed permanent RK01 supersession seal changed')
        for item in superseded['preserved_directory_files']:
            if hashlib.sha256(read_bytes(item['path'])).hexdigest()!=item['sha256']:
                raise ValueError('RK01 preserved directory changed')
        record('RK01_PRESERVED_BYTES',True)
    except (OSError,ValueError,KeyError,TypeError) as e:record('RK01_PRESERVED_BYTES',False,str(e))
    # A prior preservation PASS is not a substitute for checking current files
    # and registry values before a future human acquisition invocation.
    try:
        from verify_preservation import verify_all
        handoff=index.get('handoff_manifest')
        if handoff:read(handoff)
        current=verify_all(ROOT/handoff if handoff else None)
        record('LIVE_PRESERVATION_PREREQUISITE',current['status']=='PASS',current['failures'])
    except (OSError,ValueError,KeyError,TypeError) as e:record('LIVE_PRESERVATION_PREREQUISITE',False,str(e))
    if index.get('stage')=='FINAL_RK02_ACQUISITION_STACK':
        try:
            d=read(index['physical_build_manifest']);cert=read('OFFLINE_SOFTWARE_CERTIFICATE.json')
            ok=d['status']=='COMPILED_NEVER_EXECUTED_PHYSICAL_REQUIRED' and d['executed'] is False
            ok=ok and d['provider_loaded_during_build'] is False and d['never_executed_not_even_selftest'] is True
            ok=ok and d['source_roundtrip_to_tested_fake_exact'] is True and d['protocol_payload_and_ciphertext_unchanged'] is True
            ok=ok and cert['kernel_sha256']==PIN and cert['fake_host_sha256']==binding['client_sha256'] and cert['eligible'] is True
            ok=ok and hashlib.sha256(read_bytes(d['native_binary']['path'])).hexdigest()==d['native_binary']['sha256']
            ok=ok and hashlib.sha256(read_bytes('OFFLINE_SOFTWARE_CERTIFICATE.json')).hexdigest()==d['certificate']['sha256']
            physical_root=ROOT/'host/physical_build/rk02_physical_01'
            expected_physical_files={ROOT/'host/build_physical.py'}|{physical_root/n for n in (
                'native_physical.cpp','owned_artifact.h','compile_only.cmd','compile_only.log',
                'resolved_linker.txt','owned_physical_read32.exe','SOURCE_DIFF.patch')}
            ok=ok and len(d['files'])==len(expected_physical_files) and {Path(x['path']).resolve() for x in d['files']}==expected_physical_files
            ok=ok and Path(d['native_binary']['path']).resolve()==physical_root/'owned_physical_read32.exe'
            ok=ok and d['tested_fake_binding']==binding
            for key in ('tested_build_manifest','native_toolchain','provider_binding_evidence'):
                item=d[key];ok=ok and hashlib.sha256(read_bytes(item['path'])).hexdigest()==item['sha256']
            ok=ok and Path(d['tested_build_manifest']['path']).resolve()==ROOT/'host/build/native_05/BUILD_MANIFEST.json'
            for item in cert['evidence']:
                ok=ok and hashlib.sha256(read_bytes(item['path'])).hexdigest()==item['sha256']
            for item in d['files']:
                if hashlib.sha256(read_bytes(item['path'])).hexdigest()!=item['sha256']:ok=False
            record('COMPILE_ONLY_PHYSICAL_HOST_DERIVATION',ok)
            checker=ROOT/'evidence/contracts/review_physical_derivation_rk02.py'
            namespace={'__file__':str(checker),'__name__':'rk02_independent_physical_derivation'}
            exec(compile(read_bytes(checker),str(checker),'exec'),namespace)
            independent=namespace['verify'](ROOT,d,read_bytes)
            record('INDEPENDENT_PHYSICAL_SOURCE_HEADER_DERIVATION',independent['status']=='PASS',independent['errors'])
        except (OSError,ValueError,KeyError,TypeError) as e:record('COMPILE_ONLY_PHYSICAL_HOST_DERIVATION',False,str(e))
    status='FAIL' if errors else ('CONDITIONAL' if physical else 'PASS')
    return {'schema':1,'artifact_class':'TEMP_RAM_ACQUISITION_TOOL','kernel_sha256':PIN,
      'status':status,'software_status':'FAIL' if errors else 'PASS','failed_checks':errors,
      'checks':checks,'physical_gates':physical,'provider_loaded':False,'physical_operations':False,
      'ECU_ROM_release':False,'current_ROM_identified':False,
      'installed_ECUFlash_universal_exactness':'PERMANENTLY_REJECTED',
      'next_acquisition_connection_software_eligible':not errors,
      'stage':index.get('stage'),
      'limitations':['This validator verifies pinned prior execution evidence; it does not execute a provider or vehicle.',
       'CONDITIONAL means software checks passed with explicit physical assumptions; it is not hardware acceptance.',
       'A temporary RAM object is never an ECU flash image or a pre-flash release.']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path)
    parser.add_argument('--index',type=Path,default=ROOT/'QUALIFICATION_INPUTS.json')
    args=parser.parse_args();p=args.index.resolve()
    try:
        raw=p.read_bytes();index=json.loads(raw);result=validate(index)
        result['input_index_sha256']=hashlib.sha256(raw).hexdigest()
        if p.read_bytes()!=raw:raise ValueError('Qualification index changed during validation')
        if index.get('stage')=='FINAL_RK02_ACQUISITION_STACK':
            release_path=ROOT/'RELEASE_CERTIFICATE.json';release_raw=release_path.read_bytes();release=json.loads(release_raw)
            if release.get('status')!='RK02_OFFLINE_QUALIFIED_PHYSICAL_REQUIRED' or release.get('kernel_sha256')!=PIN:
                raise ValueError('Missing or mismatched final release certificate')
            for item in release['files']:
                if sha(item['path'])!=item['sha256'] or Path(item['path']).stat().st_size!=item['bytes']:
                    raise ValueError('Final release certificate input changed: '+item['path'])
            if release['qualification_index']['path']!=str(p) or release['qualification_index']['sha256']!=result['input_index_sha256']:
                raise ValueError('Final certificate does not bind this exact index')
            if release['validator_sha256']!=sha(Path(__file__)):raise ValueError('Final validator changed')
            physical=json.loads((ROOT/index['physical_build_manifest']).read_text())
            if release['physical_host_sha256']!=physical['native_binary']['sha256']:
                raise ValueError('Final certificate physical host mismatch')
            if release_path.read_bytes()!=release_raw:raise ValueError('Final certificate changed during validation')
            result['release_certificate_sha256']=hashlib.sha256(release_raw).hexdigest()
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
