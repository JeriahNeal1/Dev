"""Contract and negative controls for observed ECUFlash-only fake extensions."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import tempfile,json,unittest,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'integrations/ecuflash_virtual'))
from rpc_server import Provider
from virtual_ecu import VirtualECU,_reference
from faults import FaultPlan

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='a2wc-pure-')
        self.p=Provider(self.tmp.name,ecuflash_extensions=True)
        self.p.call({'function':'PassThruOpen'})
    def tearDown(self):self.p.log.close();self.p.intents.close();self.tmp.cleanup()
    def service(self,**kw):
        q=dict(function='PassThruIoctl',id=1,ioctl=0x70000,service_id=1,
               input_bytes=[1,0x12,0x34,0x56,0x78],output_capacity=255)
        q.update(kw);return self.p.call(q)
    def test_seed_key_observed_wire_vector(self):
        r=self.service();self.assertEqual(r['status'],0)
        self.assertEqual(bytes(r['output_bytes']).hex(),'e78f1f21')
        self.assertEqual(self.p.ecu.stage,'OEM')
    def test_vendor_unknown_or_malformed_rejected(self):
        for changes in ({'service_id':999},{'input_bytes':[2,18,52,86,120]},
                        {'input_bytes':[1,18,52,86]}, {'input_bytes':[1,18,52,86,256]},
                        {'output_capacity':3},{'id':99}):
            self.assertNotEqual(self.service(**changes)['status'],0)
    def test_extensions_require_explicit_mode(self):
        self.p.ecuflash_extensions=False
        self.assertNotEqual(self.service()['status'],0)
    def test_security_requires_key_and_complete_transaction(self):
        e=VirtualECU(response_mask=0x80)
        for payload in (b'\xbf',b'\x27\x01'):
            e.handle_tx(3,_reference.ssm(payload));e.drain_replies()
        bad=e.handle_tx(3,_reference.ssm(b'\x27\x02'+e.seed))
        self.assertEqual(bad['classification'],'REJECTED_SECURITY')
        self.assertEqual(e.pending_replies,0);self.assertEqual(e.stage,'SEED_SENT')
        e.handle_tx(3,_reference.ssm(b'\x27\x02'+_reference.seed_key(e.seed)))
        self.assertEqual(e.pop_reply().data.hex(),'80f0100367023420')
        self.assertEqual(e.stage,'AUTHENTICATED')
    def test_selected_host_double_download_contract(self):
        e=VirtualECU(response_mask=0x80)
        for payload in (b'\xbf',b'\x27\x01',b'\x27\x02'+_reference.seed_key(e.seed),bytes.fromhex('108502')):
            e.handle_tx(3,_reference.ssm(payload));e.drain_replies()
        declaration=bytes.fromhex('34ff300004001234')
        for _ in range(2):
            event=e.handle_tx(3,_reference.ssm(declaration))
            self.assertEqual(event['classification'],'HYPOTHETICAL_REPLY')
            self.assertEqual(e.pop_reply().data,_reference.ssm(b'\x74',response=True))
        self.assertEqual(e.handle_tx(3,_reference.ssm(declaration))['classification'],'UNSUPPORTED_SEQUENCE')
        self.assertEqual(e.pending_replies,0)
    def test_faults_only_fire_on_declared_boundary_once(self):
        p=FaultPlan('read_middle_timeout')
        self.assertIsNone(p.match(_reference.beef(b'\x03'+bytes(4)+b'\x02\x00')))
        wire=_reference.beef(bytes.fromhex('03000800000200'))
        self.assertEqual(p.match(wire)['action'],'timeout');self.assertIsNone(p.match(wire))
        with self.assertRaises(ValueError):FaultPlan('pretend_success')
        bad=FaultPlan('identity_timeout')
        self.assertIsNone(bad.match(bytes.fromhex('8010f001bf41')))
        self.assertFalse(bad.fired)
        self.assertIsNotNone(bad.match(bytes.fromhex('8010f001bf40')))
    def test_fault_reply_loss_is_distinct_from_ECU_rejection(self):
        self.p.fault=FaultPlan('identity_timeout')
        ch=self.p.call(dict(function='PassThruConnect',device=1,protocol=3,flags=0x200,baud=4800))['channel']
        msg=dict(protocol=3,data_hex='00',tx_flags=0)
        self.p.call(dict(function='PassThruStartMsgFilter',channel=ch,filter_type=1,mask=msg,pattern=msg,flow=None))
        msg=dict(protocol=3,data_hex='8010f001bf40',tx_flags=0)
        r=self.p.call(dict(function='PassThruWriteMsgs',channel=ch,count=1,timeout=100,messages=[msg]))
        self.assertEqual(r['status'],0);self.assertEqual(self.p.ecu.stage,'IDENTIFIED')
        self.assertEqual(r['delivery_events'][0]['kind'],'INJECTED_REPLY_DROP')
        r=self.p.call(dict(function='PassThruReadMsgs',channel=ch,count=1,timeout=0))
        self.assertEqual(r['messages'],[])

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    out=ROOT/'reports/local/ecuflash_dynamic/EXTENSION_TESTS.json'
    out.write_text(json.dumps(dict(status='PASS' if r.wasSuccessful() else 'FAIL',groups=r.testsRun,
        errors=[{'test':str(t),'detail':s} for t,s in r.failures+r.errors],physical=False,
        sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__),ROOT/'integrations/ecuflash_virtual/rpc_server.py',ROOT/'integrations/ecuflash_virtual/virtual_ecu.py',ROOT/'integrations/ecuflash_virtual/faults.py']}),indent=2)+'\n')
    raise SystemExit(0 if r.wasSuccessful() else 1)
