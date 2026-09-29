"""Pure virtual-ECU regressions; no application, provider or hardware launch."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib
import importlib.util
import json
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/'integrations/ecuflash_virtual/virtual_ecu.py'
spec=importlib.util.spec_from_file_location('a2wc_virtual_ecu_test_subject',MODULE)
model=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=model
spec.loader.exec_module(model)
ref=model._reference


class VirtualTests(unittest.TestCase):
    def tx(self, ecu, payload):
        event=ecu.handle_tx(3,ref.ssm(payload))
        return event,ecu.drain_replies()

    def authenticate(self, ecu):
        for payload in (b'\xBF',b'\x81',b'\x83\x00',b'\x27\x01',
                        b'\x27\x02'+ref.seed_key(ecu.seed),bytes.fromhex('108502')):
            event,replies=self.tx(ecu,payload)
            self.assertEqual(event['classification'],'HYPOTHETICAL_REPLY',event)
            self.assertEqual(len(replies),1)

    def upload(self, ecu, *, start=True):
        self.authenticate(ecu)
        declaration=b'\x34\xFF\x30\x00\x04'+ecu.expected_upload_length.to_bytes(3,'big')
        event,replies=self.tx(ecu,declaration)
        self.assertEqual(ecu.stage,'UPLOADING')
        plaintext=bytes((i*19+7)&255 for i in range(ecu.expected_upload_length))
        ciphertext=ref.encrypt_upload(plaintext)
        for offset in range(0,len(ciphertext),128):
            payload=b'\x36'+((model.UPLOAD_START+offset)&0xFFFFFF).to_bytes(3,'big')+ciphertext[offset:offset+128]
            event,replies=self.tx(ecu,payload)
            self.assertEqual(event['classification'],'HYPOTHETICAL_REPLY',event)
            self.assertEqual(len(replies),1)
        self.assertEqual(ecu.stage,'UPLOADED')
        self.assertEqual(ecu.uploaded_ciphertext,ciphertext)
        self.assertEqual(ecu.uploaded_plaintext,plaintext)
        if start:
            self.tx(ecu,bytes.fromhex('310101'))
            self.assertEqual(ecu.stage,'KERNEL')
        return plaintext,ciphertext

    def kernel(self, ecu, payload):
        event=ecu.handle_tx(3,ref.beef(payload))
        return event,ecu.drain_replies()

    def test_initial_kernel_timeout_until_explicit_complete_entry(self):
        ecu=model.VirtualECU()
        event,replies=self.kernel(ecu,b'\x01')
        self.assertEqual(event['classification'],'EXPECTED_TIMEOUT')
        self.assertEqual(replies,[])
        self.upload(ecu,start=False)
        event,replies=self.kernel(ecu,b'\x01')
        self.assertEqual(event['classification'],'EXPECTED_TIMEOUT')
        self.tx(ecu,bytes.fromhex('310101'))
        event,replies=self.kernel(ecu,b'\x01')
        self.assertEqual(replies[0].data,ref.kernel_reply(1,model.KERNEL_VERSION+b'\x00',response_mask=0x40))
        self.assertFalse(replies[0].provenance['kernel_executed'])

    def test_BF_actual_frame_and_queue_provenance(self):
        ecu=model.VirtualECU()
        event=ecu.handle_tx(3,ref.ssm(b'\xBF'),timestamp_us=123)
        self.assertEqual(event['timestamp_us'],123)
        self.assertEqual(ecu.pending_replies,1)
        reply=ecu.pop_reply()
        self.assertEqual(reply.data,model.BF_RESPONSE)
        self.assertEqual(len(reply.data),62)
        self.assertEqual(reply.data[8:13],bytes.fromhex('2F12515306'))
        self.assertTrue(reply.provenance['not_vehicle_telemetry'])
        self.assertIsNone(ecu.pop_reply())

    def test_key_and_session_cannot_be_skipped(self):
        ecu=model.VirtualECU()
        for payload in (bytes.fromhex('108502'),bytes.fromhex('310101'),bytes.fromhex('34ff300004001234')):
            event,replies=self.tx(ecu,payload)
            self.assertEqual(replies,[])
            self.assertEqual(ecu.stage,'OEM')
        self.tx(ecu,b'\xBF');self.tx(ecu,b'\x27\x01')
        event,replies=self.tx(ecu,b'\x27\x02'+b'\0'*4)
        self.assertEqual(event['classification'],'REJECTED_SECURITY')
        self.assertEqual(replies,[])
        self.assertEqual(ecu.stage,'SEED_SENT')

    def test_upload_geometry_duplicates_holes_and_complete_capture(self):
        ecu=model.VirtualECU()
        self.authenticate(ecu)
        declaration=bytes.fromhex('34ff300004001234')
        self.tx(ecu,declaration)
        chunk=b'\x36\xFF\x30\x00'+bytes(128)
        wrong=b'\x36\xFF\x30\x80'+bytes(128)
        for payload in (wrong,chunk[:-4]):
            event,replies=self.tx(ecu,payload)
            self.assertEqual(replies,[])
            self.assertEqual(ecu.uploaded_ciphertext,b'')
        self.tx(ecu,chunk)
        event,replies=self.tx(ecu,chunk)
        self.assertEqual(event['classification'],'UNSUPPORTED_RANGE')
        self.assertEqual(len(ecu.uploaded_ciphertext),128)
        self.assertEqual(len(ecu.captured_upload_frames),5)
        self.assertEqual(len(ecu.accepted_upload_frames),2)
        self.assertIsNone(ecu.uploaded_plaintext)
        event,replies=self.tx(ecu,bytes.fromhex('310101'))
        self.assertEqual(replies,[])

    def test_historical_full_upload_reconstructs37blocks(self):
        ecu=model.VirtualECU()
        self.upload(ecu)
        self.assertEqual(len(ecu.captured_upload_frames),38)  # declaration +37 blocks
        self.assertEqual(len(ref.parse_ssm(ecu.captured_upload_frames[-1]))-4,52)
        self.assertEqual(ecu.accepted_upload_frames,ecu.captured_upload_frames)

    def test_both_response_masks_sizes_read_and_CRC(self):
        for mask in (0x40,0x80):
            ecu=model.VirtualECU(response_mask=mask,expected_upload_length=4)
            self.upload(ecu)
            # Exact named-resource handler FFFF33D4 reports 0x208, not the
            # earlier public-reference guess of 512. Read handler allows514.
            for command,size in ((5,520),(6,4096)):
                event,replies=self.kernel(ecu,bytes((command,)))
                self.assertEqual(replies[0].data,ref.kernel_reply(command,size.to_bytes(4,'big'),response_mask=mask))
            address,length=0x86000,512
            event,replies=self.kernel(ecu,b'\x03'+address.to_bytes(4,'big')+length.to_bytes(2,'big'))
            self.assertEqual(replies[0].data[5:-1],ecu.flash[address:address+length])
            self.assertEqual(replies[0].provenance['flash_sha256'],ecu.flash_sha256)
            event,replies=self.kernel(ecu,b'\x02'+address.to_bytes(4,'big')+length.to_bytes(4,'big'))
            self.assertEqual(replies[0].data[5:-1],zlib.crc32(ecu.flash[address:address+length]).to_bytes(4,'big'))

    def test_read_boundaries_and_unknown_commands_no_ACK(self):
        ecu=model.VirtualECU(expected_upload_length=4)
        self.upload(ecu)
        original=ecu.flash_sha256
        for payload in (b'\x03'+(0xFFFF0).to_bytes(4,'big')+b'\x02\0',
                        b'\x03'+bytes(4)+b'\x02\x03',
                        b'\x03'+bytes(6),b'\x02'+bytes(8),b'\x04',b'\x99'):
            event,replies=self.kernel(ecu,payload)
            self.assertEqual(replies,[],event)
            self.assertTrue(event['classification'].startswith(('UNSUPPORTED','MALFORMED')))
        self.assertEqual(hashlib.sha256(ecu.flash).hexdigest(),original)

    def test_forbidden_commands_are_visible_never_acked(self):
        ecu=model.VirtualECU(expected_upload_length=4)
        for command in model.FORBIDDEN_SSM:
            event,replies=self.tx(ecu,bytes((command,)))
            self.assertEqual(event['classification'],'FORBIDDEN')
            self.assertEqual(replies,[])
        self.upload(ecu)
        for command in model.FORBIDDEN_KERNEL:
            event,replies=self.kernel(ecu,bytes((command,)))
            self.assertEqual(event['classification'],'FORBIDDEN')
            self.assertEqual(replies,[])

    def test_malformed_inputs_preserved_with_no_transition(self):
        ecu=model.VirtualECU()
        good=ref.ssm(bytes.fromhex('34ff300004001234'))
        corrupt=good[:-1]+bytes((good[-1]^1,))
        inputs=[(3,corrupt),(6,good),(3,good[:-1]),(3,b'\xBE\xEF\x00\x00\xAD'),
                (True,good),(3,bytearray(good)),(3,b'\x53\xff\x30\0')]
        for protocol,wire in inputs:
            event=ecu.handle_tx(protocol,wire)
            self.assertNotEqual(event['classification'],'HYPOTHETICAL_REPLY')
            self.assertEqual(ecu.drain_replies(),[])
            self.assertEqual(ecu.stage,'OEM')
            if type(wire) is bytes:self.assertEqual(event['wire_hex'],wire.hex())
        self.assertIn(corrupt,ecu.captured_upload_frames)

    def test_synthetic_variants_touch_only_historical_gaps(self):
        normal=model.make_synthetic_flash('baseline')
        blank=model.make_synthetic_flash('gaps_ff')
        marked=model.make_synthetic_flash('gap_sentinels')
        self.assertEqual(len(normal),0x100000)
        self.assertEqual(len({hashlib.sha256(x).hexdigest() for x in (normal,blank,marked)}),3)
        for a,b in model.HISTORICAL_GAPS:
            self.assertEqual(set(blank[a:b]),{255})
            for address in range(a,b,512):
                self.assertEqual(marked[address:address+8],b'GAP!'+address.to_bytes(4,'big'))
        for a,b in ((0,0x86000),(0xC0000,0xCF000),(0xFF000,0x100000)):
            self.assertEqual(normal[a:b],blank[a:b]);self.assertEqual(normal[a:b],marked[a:b])

    def test_complete_virtual_flash_read_no_synthesized_gaps(self):
        ecu=model.VirtualECU(sentinel_variant='gap_sentinels',expected_upload_length=4)
        self.upload(ecu)
        data=bytearray()
        for address in range(0,model.FLASH_SIZE,512):
            event,replies=self.kernel(ecu,b'\x03'+address.to_bytes(4,'big')+b'\x02\0')
            self.assertEqual(len(replies),1)
            data.extend(replies[0].data[5:-1])
        self.assertEqual(bytes(data),ecu.flash)
        self.assertEqual(hashlib.sha256(data).hexdigest(),ecu.flash_sha256)

    def test_deterministic_events_and_strict_configuration(self):
        first,second=model.VirtualECU(),model.VirtualECU()
        for ecu in (first,second):
            ecu.handle_tx(3,ref.beef(b'\x01'))
            self.authenticate(ecu)
        self.assertEqual(first.events,second.events)
        for kwargs in ({'response_mask':True},{'response_mask':0xC0},{'flash':bytes(16)},
                       {'flash':bytearray(model.FLASH_SIZE)},{'seed':bytearray(4)},
                       {'expected_upload_length':3},{'expected_upload_length':True}):
            with self.assertRaises(ValueError):model.VirtualECU(**kwargs)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(VirtualTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'status':'PASS_MODEL_ONLY' if result.wasSuccessful() else 'FAIL',
                      'groups':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                      'model_sha256':hashlib.sha256(MODULE.read_bytes()).hexdigest(),
                      'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'reference_sha256':model.REFERENCE_SHA256,'physical':False,
                      'installed_ECUFlash_acceptance':False,'kernel_executed':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
