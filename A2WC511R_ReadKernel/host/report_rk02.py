"""Hash-linked RK02 host qualification; never writes an earlier qualification."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import require,sha256,VERSION
from host.run import validate_fault_prefix,record,load_binding

OUT=ROOT/'evidence/rk02/host'
CASES=('identity','upload_begin','upload_middle','upload_final','entry','version',
       'read_begin','read_middle','read_final','read_disconnect','read_checksum','read_address',
       'read_duplicate','read_pass','read_truncate','read_extra','read_opcode',
       'rx_status','rx_extra','rx_echo','rx_empty','host_termination')
KERNEL='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
CLIENT='4b681bcdb3c178b89382b37b207b4a7679f0a1e87ab13c7051e8cf8019c094ec'

def check_coverage(folder):
    path=folder/'execution_coverage.json'
    if not path.exists():return {'kernel_execution':'NOT_REACHED_BEFORE_TERMINAL_HOST_FAULT'}
    coverage=json.loads(path.read_text());identity=coverage['identity']
    require(identity['kernel_sha256']==KERNEL and identity['receiver_self_echo'] is True,'Exact RK02 with explicit ECU receiver self echo')
    for name,digest in identity['model_sources'].items():
        require(sha256((ROOT/'sim'/name).read_bytes())==digest,'Final runtime model changed: '+name)
    events=coverage['SCI_event_counts']
    completed=events.get('tx_character_complete',0)
    require(events.get('ECU_self_echo_start_RE0',0)==completed and events.get('ECU_self_echo_ignored_RE0',0)==completed,'Every completed TX character exercised the RE0 self-echo path')
    require(not events.get('ECU_self_echo_received',0) and not events.get('ECU_self_echo_overrun',0),'Unexpected ECU RX self echo during fixed host sequence')
    return {'execution_coverage':record(path),'receiver_self_echo':True,'model_sources':identity['model_sources'],
            'kernel_terminal':coverage['terminal'],'kernel_exchanges':len(coverage['exchanges']),
            'completed_TX_characters':completed,'self_echo_characters_ignored_RE0':events.get('ECU_self_echo_ignored_RE0',0)}

def publish(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/name;data=(json.dumps(value,indent=2)+'\n').encode()
    if target.exists():require(target.read_bytes()==data,'Existing RK02 qualification differs; preserve it: '+str(target))
    else:target.write_bytes(data)
    return record(target)

def main():
    binding=load_binding('native_05')
    require(binding['kernel_sha256']==KERNEL and binding['client_sha256']==CLIENT and VERSION==b'A2WC511R-RK02\0','Pinned RK02 host release')
    cases={};failures=[]
    for case in CASES:
        suffix='_02' if case=='read_extra' else '_01'
        folder=ROOT/'fake/runs'/('rk02_fault_'+case+suffix);path=folder/'RESULT.json'
        try:
            result=json.loads(path.read_text())
            require(result['status']=='PASS_EXPECTED_TERMINAL_FAULT' and result['fault']==case,'Actual named fault passed')
            require(result['binding']==binding,'Every fault ran final native05 and RK02')
            proof=validate_fault_prefix(folder,binding,case=='host_termination')
            target=folder/'FIXED_TX_PREFIX_REPLAY.json';data=(json.dumps(proof,indent=2)+'\n').encode()
            if target.exists():require(target.read_bytes()==data,'Fault replay changed')
            else:target.write_bytes(data)
            cases[case]={'status':'PASS','result':record(path),'fixed_TX_prefix_replay':record(target),
                         'host_sha256':CLIENT,'kernel_sha256':KERNEL,'terminal':True,'physical':False,**check_coverage(folder)}
        except Exception as error:
            cases[case]={'status':'FAIL','error':type(error).__name__+': '+str(error)};failures.append(case)
    require(not failures,'RK02 fault cases incomplete/failed: '+','.join(failures))
    faults=publish('HOST_FAULTS.json',{'schema':1,'status':'PASS','kernel_sha256':KERNEL,'host_sha256':CLIENT,
        'cases':cases,'failures':[],'all_TX_prefixes_replayed':True,'physical_provider_loaded':False,
        'retained_harness_expectation_mismatch':{'result':record(ROOT/'fake/runs/rk02_fault_read_extra_01/RESULT.json'),
          'reason':'Fragmented oversized reply was correctly rejected as aggregate oversize; the old runner expected per-message oversize text. Repeated with complete-message profile at _02; native code unchanged.'},
        'all_cases_executed_on_exact_final_native05':True,'prior_version_applicability_used':False})
    fixtures=[]
    for label in ('rk02_composite_01','rk02_random_01'):
        folder=ROOT/'fake/runs'/label;path=folder/'RESULT.json';result=json.loads(path.read_text())
        require(result['status']=='PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS' and result['binding']==binding,'Full exact RK02/native05 fixture')
        require(result['receiver_self_echo'] is True,'Full native fixture self echo required')
        fixtures.append({'result':record(path),**check_coverage(folder)})
    finalization=ROOT/'fake/runs/rk02_composite_01/finalized/FINALIZATION.json'
    parsed=json.loads(finalization.read_text())
    require(parsed['status']=='PASS_RAW_CAPTURE_INTEGRITY' and parsed['kernel_sha256']==KERNEL and parsed['client_sha256']==CLIENT,'Finalizer exact release')
    tests={}
    for name in ('CONTRACT_TESTS','STREAM_TESTS','FINALIZER_TESTS'):
        path=OUT/'tests'/(name+'.json');require(json.loads(path.read_text())['status']=='PASS','RK02 pure tests');tests[name]=record(path)
    qualification={'schema':1,'status':'PASS','kernel_sha256':KERNEL,'final_fake_host_sha256':CLIENT,
      'fixed_only':True,'all_TX_prefixes_replayed':True,'physical_provider_loaded':False,'receiver_self_echo':True,
      'final_native_full_run':fixtures[0]['result'],'faults':faults,'full_fixtures':fixtures,
      'native_journal_only_finalization':record(finalization),'tests':tests,
      'finalizer_adversarial_tests':tests['FINALIZER_TESTS'],'pure_host_contract_tests':tests['CONTRACT_TESTS'],'pure_stream_tests':tests['STREAM_TESTS'],
      'final_build':record(ROOT/'host/build/native_05/BUILD_MANIFEST.json'),
      'native_toolchain':record(OUT/'NATIVE_TOOLCHAIN.json'),'source_transition':record(OUT/'SOURCE_TRANSITION.json'),
      'all_faults_executed_on_exact_final_binary':True,'prior_version_applicability_used':False,
      'OEM_scope':'Explicit boot model independently constrained by actual stock parser/serializer/loader contracts; physical UART/session/reset not asserted',
      'no_CRC_substitution':True,'two_full_reads':True,'close_is_ECU_reset':False,
      'source_files':[record(ROOT/part) for part in ('host/native.cpp','host/protocol.py','host/state.py','host/stream.py','host/run.py','host/finalize.py','host/report_rk02.py','fake/model.py','fake/server.py')]}
    result=publish('HOST_QUALIFICATION.json',qualification)
    print(json.dumps({'status':'PASS','host':result,'faults':faults},indent=2))

if __name__=='__main__':main()
