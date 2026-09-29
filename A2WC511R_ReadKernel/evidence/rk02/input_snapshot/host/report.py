"""Regenerate hash-linked host qualification from retained actual executions."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import require,sha256
from host.run import validate_fault_prefix,record

CASE_RUNS={
 'identity':'identity_final','upload_begin':'upload_begin_final','upload_middle':'upload_middle_final',
 'upload_final':'upload_final_final','entry':'entry_final','version':'version_final',
 'read_begin':'read_begin_final','read_middle':'read_middle_01','read_final':'read_final_01',
 'read_disconnect':'read_disconnect_final','read_checksum':'read_checksum_native04',
 'read_address':'read_address_final','read_duplicate':'read_duplicate_final','read_pass':'read_pass_final',
 'read_truncate':'read_truncate_final','read_extra':'read_extra_final','read_opcode':'read_opcode_native04',
 'rx_status':'rx_status_final','rx_extra':'rx_extra_final','rx_echo':'rx_echo_native04','rx_empty':'rx_empty_final',
 'host_termination':'host_termination_native04'}

def main():
    cases={};failures=[]
    for case,label in CASE_RUNS.items():
        folder=ROOT/'fake/runs'/label;result_path=folder/'RESULT.json';result=json.loads(result_path.read_text())
        try:
            require(result['status']=='PASS_EXPECTED_TERMINAL_FAULT' and result['fault']==case,'Named native fault qualification')
            proof=validate_fault_prefix(folder,result['binding'],case=='host_termination')
            require(proof['status']=='PASS_FIXED_TX_PREFIX','Every actual transmitted frame must match fixed plan')
            target=folder/'FIXED_TX_PREFIX_REPLAY.json'
            data=(json.dumps(proof,indent=2)+'\n').encode()
            if target.exists():require(target.read_bytes()==data,'Existing independent prefix replay differs')
            else:target.write_bytes(data)
            cases[case]={'status':'PASS','result':record(result_path),'fixed_TX_prefix_replay':record(target),
                         'host_sha256':result['binding']['client_sha256'],'kernel_sha256':result['binding']['kernel_sha256'],
                         'terminal':True,'native_calls':result['native_requests'],'physical':False}
        except Exception as error:
            failures.append({'case':case,'error':type(error).__name__+': '+str(error)});cases[case]={'status':'FAIL','result':record(result_path)}
    faults={'schema':1,'status':'PASS' if not failures else 'FAIL','cases':cases,'failures':failures,
            'all_TX_prefixes_replayed':not failures,'physical_provider_loaded':False,
            'native03_to_04_applicability':record(ROOT/'host/build/native_04/SOURCE_TRANSITION.json'),
            'scope':'Native03 fault wire/ABI path unchanged in04;04 repeated checksum/echo/termination/opcode faults with full metadata. Kernel malformed-request/unknown-opcode execution is in separate sim qualification.'}
    fault_path=ROOT/'host/HOST_FAULTS.json';fault_path.write_text(json.dumps(faults,indent=2)+'\n')
    complete=ROOT/'fake/runs/composite_native04/RESULT.json'
    if not complete.exists():
        print(json.dumps({'fault_status':faults['status'],'cases':len(cases),'final_host':'still executing'},indent=2));return
    final=json.loads(complete.read_text());require(final['status']=='PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS','Final exact host complete execution')
    finalization=ROOT/'fake/runs/composite_native04/finalized/FINALIZATION.json'
    require(finalization.exists(),'Read-only finalizer must pass against actual final host output')
    finalizer_tests=ROOT/'host/tests/FINALIZER_TESTS.json';require(json.loads(finalizer_tests.read_text())['status']=='PASS','Finalizer adversarial tests')
    qualification={'schema':1,'status':'PASS' if not failures else 'FAIL','kernel_sha256':final['binding']['kernel_sha256'],
      'final_fake_host_sha256':final['binding']['client_sha256'],'fixed_only':True,'all_TX_prefixes_replayed':not failures,
      'physical_provider_loaded':False,'final_native_full_run':record(complete),'faults':record(fault_path),
      'full_fixtures':[record(ROOT/'fake/runs'/name/'RESULT.json') for name in ('composite_01','random_01','composite_native04')],
      'native_journal_only_finalization':record(finalization),'finalizer_adversarial_tests':record(finalizer_tests),
      'pure_host_contract_tests':record(ROOT/'host/tests/CONTRACT_TESTS.json'),'pure_stream_tests':record(ROOT/'host/tests/STREAM_TESTS.json'),
      'final_build':record(ROOT/'host/build/native_04/BUILD_MANIFEST.json'),
      'OEM_scope':'Actual scoped OEM KWP producer/validator and decrypt checks recorded separately; full physical UART/session/reset not asserted',
      'helper_boundary':'Python HostState/protocol are internal pure offline oracles without transport; only supported uploader executable embeds fixed kernel and exposes no arbitrary command/address/provider parameters',
      'no_CRC_substitution':True,'two_full_reads':True,'close_is_ECU_reset':False,
      'source_files':[record(ROOT/'host'/name) for name in ('native.cpp','protocol.py','state.py','stream.py','run.py','finalize.py','report.py')]}
    path=ROOT/'host/HOST_QUALIFICATION.json';path.write_text(json.dumps(qualification,indent=2)+'\n')
    print(json.dumps({'host':record(path),'faults':record(fault_path),'status':qualification['status']},indent=2))

if __name__=='__main__':main()
