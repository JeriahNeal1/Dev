"""Focused pure fake-provider tests; never load a DLL or launch an application."""
import sys
sys.dont_write_bytecode=True
import importlib.util, json, hashlib, unittest, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'integrations/ecuflash_virtual/rpc_server.py'
OUT=ROOT/'reports/local/ecuflash_dynamic/provider_review'
sys.path.insert(0,str(SOURCE.parent))
spec=importlib.util.spec_from_file_location('reviewed_rpc_server',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from virtual_ecu import BF_RESPONSE
BF='8010f001bf40'

def message(data=BF,protocol=3):
    return {'protocol':protocol,'rx_status':0,'tx_flags':0,'timestamp':0,
            'extra':len(data)//2,'data_hex':data}

class Tests(unittest.TestCase):
    def setUp(self):
        self.folder=OUT/'runs'/uuid.uuid4().hex;self.folder.mkdir(parents=True)
        self.p=module.Provider(self.folder)
    def tearDown(self):self.p.log.close()
    def call(self,fn,**kw):return self.p.call({'function':fn,**kw})
    def channel(self):
        self.assertEqual(self.call('PassThruOpen')['status'],0)
        r=self.call('PassThruConnect',device=1,protocol=3,flags=0x1200,baud=4800)
        self.assertEqual(r['status'],0);return r['channel']
    def filter(self,ch,mask='00',pattern='00'):
        return self.call('PassThruStartMsgFilter',channel=ch,filter_type=1,
                         mask=message(mask),pattern=message(pattern),flow=None)
    def write(self,ch,*messages):
        return self.call('PassThruWriteMsgs',channel=ch,count=len(messages),timeout=100,messages=list(messages))
    def read(self,ch,count=1):return self.call('PassThruReadMsgs',channel=ch,count=count,timeout=0)

    def test_bf_provenance_and_complete_log(self):
        ch=self.channel();self.assertEqual(self.filter(ch)['status'],0)
        r=self.write(ch,message());self.assertEqual(r['count'],1)
        rx=self.read(ch);self.assertEqual(rx['status'],0)
        self.assertEqual(bytes.fromhex(rx['messages'][0]['data_hex']),BF_RESPONSE)
        self.assertTrue(rx['messages'][0]['provenance']['not_vehicle_telemetry'])
        log=[json.loads(x) for x in (self.folder/'j2534.jsonl').read_text().splitlines()]
        self.assertEqual(log[-2]['request']['messages'][0]['data_hex'],BF)
        self.assertFalse(log[-1]['physical'])

    def test_invalid_version_handle_rejected(self):
        self.assertNotEqual(self.call('PassThruReadVersion',device=1)['status'],0)
        self.channel()
        self.assertNotEqual(self.call('PassThruReadVersion',device=999)['status'],0)
        self.assertEqual(self.call('PassThruReadVersion',device=1)['status'],0)

    def test_later_invalid_protocol_cannot_hide_prior_TX(self):
        ch=self.channel();self.filter(ch)
        r=self.write(ch,message(),message(protocol=5))
        self.assertNotEqual(r['status'],0)
        self.assertEqual(r.get('count',0),0)
        self.assertEqual(self.p.ecu.stage,'OEM')
        self.assertEqual(self.p.ecu.events,[])
        self.assertEqual(self.read(ch)['messages'],[])

    def test_later_invalid_hex_cannot_hide_prior_TX(self):
        ch=self.channel();self.filter(ch)
        for bad in ('zz','0g','-1','80 10','1'):
            with self.subTest(bad=bad):
                r=self.write(ch,message(),message(bad))
                self.assertNotEqual(r['status'],0)
                self.assertEqual(self.p.ecu.stage,'OEM')
                self.assertEqual(self.p.ecu.events,[])

    def test_malformed_filter_rejected_before_TX(self):
        ch=self.channel()
        for mask,pattern in [('zz','00'),('00','0g'),('00','0000'),('0','0')]:
            with self.subTest(mask=mask,pattern=pattern):
                self.assertNotEqual(self.filter(ch,mask,pattern)['status'],0)
                self.assertEqual(self.p.channels[ch]['filters'],{})
        self.assertEqual(self.write(ch,message())['status'],0)
        self.assertEqual(self.p.ecu.stage,'IDENTIFIED')

    def test_filter_IDs_do_not_collide_after_deletion(self):
        ch=self.channel();one=self.filter(ch)['id'];two=self.filter(ch)['id']
        self.assertEqual(self.call('PassThruStopMsgFilter',channel=ch,id=one)['status'],0)
        three=self.filter(ch)['id'];self.assertNotEqual(two,three)
        self.assertEqual(set(self.p.channels[ch]['filters']),{two,three})

    def test_raw_invalid_frame_is_TX_accepted_without_ECU_ACK(self):
        ch=self.channel();self.filter(ch)
        r=self.write(ch,message('8010f001bf41'))
        self.assertEqual(r['status'],0);self.assertEqual(r['count'],1)
        self.assertEqual(r['virtual_events'][0]['classification'],'MALFORMED')
        self.assertEqual(self.read(ch)['messages'],[])

    def test_forbidden_command_visible_without_positive_reply(self):
        ch=self.channel();self.filter(ch)
        r=self.write(ch,message('beef000125d3'))
        self.assertEqual(r['status'],0)
        self.assertEqual(r['virtual_events'][0]['classification'],'FORBIDDEN')
        self.assertEqual(self.read(ch)['messages'],[])

    def test_unfiltered_response_decision_is_logged(self):
        ch=self.channel();r=self.write(ch,message())
        self.assertEqual(r['status'],0);self.assertEqual(self.read(ch)['messages'],[])
        self.assertTrue(r.get('delivery_events'))
        self.assertFalse(r['delivery_events'][0]['queued'])

    def test_configuration_invalid_values_rejected_atomically(self):
        ch=self.channel();before=dict(self.p.channels[ch]['config'])
        for items in ([{'parameter':3,'value':2}], [{'parameter':1,'value':0}],
                      [{'parameter':3,'value':1},{'parameter':999,'value':1}]):
            with self.subTest(items=items):
                self.assertNotEqual(self.call('PassThruIoctl',id=ch,ioctl=2,config=items)['status'],0)
                self.assertEqual(self.p.channels[ch]['config'],before)

    def test_loopback_explicitly_tagged_and_RX_clear(self):
        ch=self.channel();self.filter(ch)
        self.assertEqual(self.call('PassThruIoctl',id=ch,ioctl=2,config=[{'parameter':3,'value':1}])['status'],0)
        self.write(ch,message());rx=self.read(ch,2)['messages']
        self.assertEqual(len(rx),2);self.assertEqual(rx[0]['rx_status'],1)
        self.assertIn('provenance',rx[0]);self.assertEqual(rx[0]['data_hex'],BF)
        self.write(ch,message());self.assertEqual(self.call('PassThruIoctl',id=ch,ioctl=8)['status'],0)
        self.assertEqual(self.read(ch)['messages'],[])

    def test_invalid_counts_and_unknowns_have_no_success(self):
        ch=self.channel()
        for count in (-1,0,129,True,'1'):
            self.assertNotEqual(self.read(ch,count)['status'],0)
        self.assertNotEqual(self.call('NoSuchFunction',channel=ch)['status'],0)
        self.assertNotEqual(self.call('PassThruIoctl',id=ch,ioctl=0xDEAD)['status'],0)
        self.assertEqual(self.call('PassThruIoctl',id=0,ioctl=0x70004,input_pointer=0,output_pointer=1,
                                   output_contract='PINNED_ECUFLASH_1_44_4870_SINGLE_UTF16LE_NUL_PATH_MAX512_WCHAR')['status'],1)

    def test_invalid_envelope_returns_logged_failure(self):
        for bad in ({},[],None,{'function':42}):
            with self.subTest(bad=bad):
                r=self.p.call(bad);self.assertNotEqual(r['status'],0)
        rows=[json.loads(x) for x in (self.folder/'j2534.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows),4)

    def test_native_badarg_message_cannot_mutate_state(self):
        for function in ('PassThruOpen','PassThruClose','PassThruConnect','PassThruReadVersion','PassThruIoctl'):
            r=self.call(function,invalid_arguments='unreadable or unterminated native pointer')
            self.assertEqual(r['status'],4)
            self.assertFalse(self.p.open);self.assertEqual(self.p.channels,{})
            self.assertEqual(self.p.ecu.stage,'OEM')
        r=self.call('PassThruOpen',native_exception='native malformed reply')
        self.assertEqual(r['status'],7);self.assertFalse(self.p.open)

    def test_internal_failure_retains_completed_TX_events(self):
        ch=self.channel();original=self.p.ecu.handle_tx;calls=0
        def failing(protocol,data):
            nonlocal calls
            calls+=1
            if calls==2:raise RuntimeError('injected internal model failure')
            return original(protocol,data)
        self.p.ecu.handle_tx=failing
        r=self.write(ch,message(),message())
        self.assertNotEqual(r['status'],0);self.assertEqual(r['count'],1)
        self.assertEqual(len(r['virtual_events']),1)
        self.assertEqual(r['virtual_events'][0]['wire_hex'],BF)

    def test_message_limits_rejected_before_state_change(self):
        ch=self.channel()
        cases=[message('00'*4129),dict(message(),extra=99),dict(message(),tx_flags=0xFFFFFFFF)]
        for msg in cases:
            self.assertNotEqual(self.write(ch,msg)['status'],0)
            self.assertEqual(self.p.ecu.stage,'OEM')
        r=self.call('PassThruWriteMsgs',channel=ch,count=2,timeout=100,messages=[message()])
        self.assertNotEqual(r['status'],0);self.assertEqual(self.p.ecu.events,[])

    def test_raw_framing_flags_must_be_explicit(self):
        self.call('PassThruOpen')
        for flags in (0,0x1000,0xFFFFFFFF):
            self.assertEqual(self.call('PassThruConnect',device=1,protocol=3,flags=flags,baud=4800)['status'],6)
        self.assertEqual(self.p.channels,{})
        self.assertEqual(self.call('PassThruConnect',device=1,protocol=3,flags=0x200,baud=4800)['status'],0)

    def test_mask_pattern_rejects_wrong_response(self):
        ch=self.channel();self.assertEqual(self.filter(ch,'ff','81')['status'],0)
        r=self.write(ch,message());self.assertFalse(r['delivery_events'][0]['queued'])
        self.assertEqual(self.read(ch)['messages'],[])

    def test_disconnect_and_close_do_not_claim_ECU_reset(self):
        ch=self.channel();self.write(ch,message())
        self.assertEqual(self.call('PassThruDisconnect',channel=ch)['status'],0)
        self.assertEqual(self.p.ecu.stage,'IDENTIFIED')
        self.assertEqual(self.call('PassThruClose',device=1)['status'],0)
        self.assertEqual(self.p.ecu.stage,'IDENTIFIED')
        self.assertNotEqual(self.read(ch)['status'],0)

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    report={'status':'PASS_PURE_MODEL_ONLY' if result.wasSuccessful() else 'FAIL',
            'groups':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'details':[{'test':str(t),'traceback':text} for t,text in result.failures+result.errors],
            'rpc_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'provider_loaded':False,'app_launched':False,'physical':False}
    (OUT/'TEST_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='details'}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
