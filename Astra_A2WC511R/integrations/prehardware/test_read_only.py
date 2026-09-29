"""Offline negative controls and ABI-boundary tests. Never selects physical mode."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import time
from unittest.mock import patch

from transport import (HERE, REQUEST, IDENTITY_REQUEST, ReadOnlyJ2534Transport,
    SnapshotClient, ProtocolError, validate_request, validate_operation, parse_identity)
from capture import capture

BROKER=HERE/'build/broker.exe'
RESULTS={}

def run_worker(data, fault=None):
    env=dict(os.environ)
    env.pop('A2WC_FAKE_FAULT',None)
    if fault:env['A2WC_FAKE_FAULT']=fault
    run=subprocess.run([str(BROKER),'--fake'],input=data,capture_output=True,env=env,timeout=6)
    assert b'FORBIDDEN_' not in run.stderr, run.stderr
    frames=[line.removeprefix(b'FAKE WIRE ').decode() for line in run.stderr.splitlines() if line.startswith(b'FAKE WIRE ')]
    assert set(frames)<= {REQUEST.hex(),IDENTITY_REQUEST.hex()}
    return run,frames

class AllowlistTests(unittest.TestCase):
    def test_exhaustive_frame_mutations(self):
        rejected=0
        for i in range(len(REQUEST)):
            for value in range(256):
                if value==REQUEST[i]:continue
                changed=bytearray(REQUEST);changed[i]=value
                with self.assertRaises(ProtocolError):validate_request(bytes(changed))
                rejected+=1
                if i<len(REQUEST)-1:
                    changed[-1]=sum(changed[:-1])&255
                    with self.assertRaises(ProtocolError):validate_request(bytes(changed))
                    rejected+=1
        for i in range(len(REQUEST)+1):
            for value in range(256):
                with self.assertRaises(ProtocolError):validate_request(REQUEST[:i]+bytes([value])+REQUEST[i:])
                rejected+=1
        for i in range(len(REQUEST)):
            with self.assertRaises(ProtocolError):validate_request(REQUEST[:i]+REQUEST[i+1:])
            rejected+=1
        for value in (None,True,False,123,'SNAPSHOT',bytearray(REQUEST),memoryview(REQUEST),[int(b) for b in REQUEST],IDENTITY_REQUEST):
            with self.assertRaises(ProtocolError):validate_request(value)
        RESULTS['frame_mutations_rejected']=rejected

    def test_all_opcode_values(self):
        allowed=[]
        for opcode in range(256):
            q=bytearray(REQUEST);q[4]=opcode;q[-1]=sum(q[:-1])&255
            try:validate_request(bytes(q));allowed.append(opcode)
            except ProtocolError:pass
        self.assertEqual(allowed,[0xa8]);RESULTS['fixed_frame_accepted_opcodes']=allowed

    def test_worker_parser_native_selftest(self):
        r=subprocess.run([str(BROKER),'--policy-selftest'],capture_output=True,text=True,check=True,timeout=5)
        RESULTS['native_token_selftest']=json.loads(r.stdout)

    def test_malformed_worker_calls_never_load(self):
        cases=[b'', b'SNAPSHOT\n', b'identity\n', b'IDENTITY\r\n',b'IDENTITY\0\n',
            b'IDENTITY',b'IDENTITY {}\n',b'{"op":"write","data":"b0"}\n',
            b'CLOSE\nIDENTITY\n',b'X'*10000+b'\n',b'B0\n',b'B8\n',b'A0\n',
            b'RESET\n',b'KERNEL\n',b'FLASH\n',b'ACTUATE\n']
        cases += [bytes([i])+b'\n' for i in range(256)]
        for data in cases:
            run,frames=run_worker(data)
            self.assertEqual(frames,[])
            self.assertNotIn(b'FAKE Open',run.stderr)
        RESULTS['process_boundary_malformed_cases']=len(cases)

    def test_terminal_error_prevents_later_valid_command(self):
        for op in (b'B0',b'B8',b'WRITE',b'RESET',b'SNAPSHOT extra',b'IDENTITY'):
            run,frames=run_worker(b'IDENTITY\n'+op+b'\nSNAPSHOT\n')
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(frames,[IDENTITY_REQUEST.hex()])
            self.assertIn(b'FAKE Close',run.stderr)

    def test_provider_faults_abort(self):
        faults=['bad_checksum','wrong_opcode','wrong_identity','missing_echo','echo_mismatch',
                'timeout','rx_status','wrong_protocol','extra_bytes','oversized','short_tx']
        for fault in faults:
            run,frames=run_worker(b'IDENTITY\nSNAPSHOT\nCLOSE\n',fault)
            self.assertNotEqual(run.returncode,0,fault)
            self.assertEqual(frames,[IDENTITY_REQUEST.hex()],fault)
            self.assertIn(b'FAKE StopFilter',run.stderr,fault)
            self.assertIn(b'FAKE Disconnect',run.stderr,fault)
            self.assertIn(b'FAKE Close',run.stderr,fault)
        RESULTS['provider_faults_terminal']=faults

    def test_normal_and_fragmented_response(self):
        for fault in (None,'split'):
            run,frames=run_worker(b'IDENTITY\nSNAPSHOT\nCLOSE\n',fault)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(frames,[IDENTITY_REQUEST.hex(),REQUEST.hex()])
            rows=[json.loads(s) for s in run.stdout.splitlines()]
            self.assertEqual(parse_identity(bytes.fromhex(rows[1]['wire_hex']))['ecu_id'],'2F12515306')
            self.assertEqual(rows[-1],{'type':'closed'})

    def test_cleanup_failure_is_latched(self):
        for fault in ('stop_failure','disconnect_failure','close_failure'):
            run,frames=run_worker(b'IDENTITY\nCLOSE\n',fault)
            self.assertNotEqual(run.returncode,0)
            rows=[json.loads(s) for s in run.stdout.splitlines()]
            self.assertEqual(rows[-1],{'type':'terminal_failure','cleanup_ok':False})
            self.assertEqual(frames,[IDENTITY_REQUEST.hex()])
            for operation in (b'StopFilter',b'Disconnect',b'Close'):
                self.assertIn(b'FAKE '+operation,run.stderr)
        RESULTS['cleanup_failure_latching']='PASS_ALL_THREE_OPERATIONS'

    def test_startup_failure_cleans_owned_resources(self):
        for fault,expected in [('open_failure',[]),('connect_failure',[b'Close']),
                              ('config_failure',[b'Disconnect',b'Close']),('filter_failure',[b'Disconnect',b'Close'])]:
            run,frames=run_worker(b'IDENTITY\nSNAPSHOT\n',fault)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(frames,[])
            for operation in expected:self.assertIn(b'FAKE '+operation,run.stderr)

    def test_host_faults_attempt_graceful_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='a2wc-readonly-') as temp:
            for fault in ('timeout','parse','outer_client_timeout'):
                log=Path(temp)/(fault+'.log')
                t=ReadOnlyJ2534Transport(log,fake=True)
                receive=t._receive
                def broken():
                    row=receive()
                    if fault=='timeout':raise TimeoutError('Injected host deadline')
                    if fault=='parse':row['wire_hex']='00'
                    if fault=='outer_client_timeout':time.sleep(0.1)
                    return row
                t._receive=broken
                try:
                    if fault=='outer_client_timeout':
                        with self.assertRaises(TimeoutError):SnapshotClient(t,timeout_ms=1).capture()
                    else:
                        with self.assertRaises((TimeoutError,ProtocolError)):t.exchange(REQUEST)
                finally:t.close()
                self.assertEqual(t.cleanup_status,'CONFIRMED')
                for operation in ('StopFilter','Disconnect','Close'):
                    self.assertIn('FAKE '+operation,log.read_text())
        RESULTS['host_abort_cleanup_regressions']='PASS_TIMEOUT_PARSE_OUTER_CLIENT_TIMEOUT'

    def test_unexpected_worker_death_reports_cleanup_unknown(self):
        with tempfile.TemporaryDirectory(prefix='a2wc-readonly-') as temp:
            t=ReadOnlyJ2534Transport(Path(temp)/'dead.log',fake=True)
            t._process.kill();t._process.wait(timeout=3)
            with self.assertRaisesRegex(RuntimeError,'cleanup not confirmed'):t.close()

    def test_hung_fake_provider_reports_forced_cleanup_unknown(self):
        original=subprocess.Popen
        def fake_hang(*args,**kwargs):
            self.assertIn('--fake',args[0])
            kwargs['env']['A2WC_FAKE_FAULT']='hang_snapshot'
            return original(*args,**kwargs)
        with tempfile.TemporaryDirectory(prefix='a2wc-readonly-') as temp:
            with patch('subprocess.Popen',fake_hang):
                t=ReadOnlyJ2534Transport(Path(temp)/'hang.log',fake=True)
            client=SnapshotClient(t,timeout_ms=100)
            started=time.monotonic()
            with self.assertRaises(TimeoutError):client.capture()
            self.assertLess(time.monotonic()-started,3)
            with self.assertRaisesRegex(RuntimeError,'cleanup not confirmed'):client.close()
            self.assertEqual(t.cleanup_status,'FORCED_TERMINATION_CLEANUP_UNCONFIRMED')
        RESULTS['hard_hang']='BOUNDED_KILL_CLEANUP_EXPLICITLY_UNCONFIRMED'

    def test_bytes_subclass_cannot_override_validation(self):
        class LyingBytes(bytes):
            def __ne__(self,other):return False
        with self.assertRaises(ProtocolError):validate_request(LyingBytes(b'B0'))

    def test_same_snapshot_caller_and_offline_backends(self):
        with tempfile.TemporaryDirectory(prefix='a2wc-readonly-') as temp:
            for backend in ('replay','native-virtual','fake-j2534'):
                p=Path(temp)/(backend+'.jsonl')
                result=capture(p,backend,8,0)
                self.assertEqual(result['status'],'PASS_CAPTURE_ONLY',result)
                rows=[json.loads(s) for s in p.read_text().splitlines()]
                samples=[r for r in rows if r['type']=='sample']
                self.assertEqual(len(samples),8)
                self.assertTrue(all(len(r['raw_by_address'])==6 and r['reason_mask']&0x80 for r in samples))
                self.assertTrue(all(r['host_response_monotonic_ns']>=r['host_request_monotonic_ns'] for r in samples))
        RESULTS['common_caller_backends']=['replay','native-virtual','fake-j2534']

    def test_no_implicit_physical_selection(self):
        with self.assertRaises(ValueError):ReadOnlyJ2534Transport('unused.log')
        with self.assertRaises(ValueError):ReadOnlyJ2534Transport('unused.log',fake=1)
        for op in ('B0','B8','A0','write',None,True,{},b'IDENTITY'):
            with self.assertRaises(ProtocolError):validate_operation(op)

    def test_bad_api_request_cannot_reach_provider(self):
        with tempfile.TemporaryDirectory(prefix='a2wc-readonly-') as temp:
            log=Path(temp)/'provider.log'
            t=ReadOnlyJ2534Transport(log,fake=True)
            try:
                for opcode in range(256):
                    if opcode==0xa8:continue
                    q=bytearray(REQUEST);q[4]=opcode;q[-1]=sum(q[:-1])&255
                    with self.assertRaises(ProtocolError):t.exchange(bytes(q))
            finally:t.close()
            writes=[s for s in log.read_text().splitlines() if s.startswith('FAKE WIRE')]
            self.assertEqual(writes,['FAKE WIRE '+IDENTITY_REQUEST.hex()])

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(AllowlistTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    RESULTS.update({'status':'PASS' if result.wasSuccessful() else 'FAIL','test_groups':result.testsRun,
                    'failures':len(result.failures),'errors':len(result.errors),'real_provider_loaded':False,
                    'scope':'All public grammar branches; all opcode values; exhaustive single-byte edit domains. Exact enum-to-constant construction is the universal allowlist argument, not finite fuzzing.',
                    'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'host_dependency_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                        [HERE/'transport.py',HERE/'capture.py',HERE.parent/'m07/protocol.py',HERE.parent/'m07/backends.py']},
                    'build_manifest_sha256':hashlib.sha256((HERE/'build/BUILD_MANIFEST.json').read_bytes()).hexdigest()})
    out=HERE.parents[1]/'reports/local/prehardware/READ_ONLY_BACKEND_TESTS.json'
    out.write_text(json.dumps(RESULTS,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
