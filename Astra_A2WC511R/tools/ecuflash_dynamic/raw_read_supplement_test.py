"""Adversarial offline tests; no sockets, DLL loading, provider, or vehicle calls."""
import sys
sys.dont_write_bytecode=True
import copy
import io
import json
import struct
import unittest
import raw_read_supplement as target


def reply(data, command=3):
    frame=target._packet(bytes([command+0x80])+data)
    msg=target._message(frame)
    msg.update(extra=len(frame), provenance={'not_vehicle_telemetry':True,'kernel_executed':False})
    return {'status':0,'messages':[msg]}


class Checks(unittest.TestCase):
    def test_asymmetric_bytes_returned_exactly(self):
        data=bytes((i*31+7)&255 for i in range(512))
        self.assertEqual(target._reply(reply(data),3,512),data)
        self.assertEqual(target._reply(reply(target.VERSION,1),1,len(target.VERSION)),target.VERSION)

    def test_malformed_reply_matrix(self):
        valid=reply(bytes(512))
        mutations=[]
        for field,value in [('status',1),('status',False),('messages',[]),('messages',valid['messages']*2)]:
            item=copy.deepcopy(valid);item[field]=value;mutations.append((field+str(value)[:5],item))
        for field,value in [('protocol',4),('rx_status',1),('rx_status',False),('tx_flags',1),('extra',1),('data_hex','0'),('data_hex','gg')]:
            item=copy.deepcopy(valid);item['messages'][0][field]=value;mutations.append((field,item))
        for index in [0,2,3,4,-1]:
            item=copy.deepcopy(valid);raw=bytearray.fromhex(item['messages'][0]['data_hex']);raw[index]^=1
            if index!=-1:raw[-1]=sum(raw[:-1])&255
            item['messages'][0]['data_hex']=raw.hex();mutations.append(('wire'+str(index),item))
        for value in [{},{'not_vehicle_telemetry':True,'kernel_executed':True}]:
            item=copy.deepcopy(valid);item['messages'][0]['provenance']=value;mutations.append(('provenance',item))
        mutations.append(('truncated_data',reply(bytes(511))))
        mutations.append(('extra_data',reply(bytes(513))))
        for name,item in mutations:
            with self.subTest(name=name),self.assertRaises(ValueError):target._reply(item,3,512)

    def test_outbound_rejects_other_opcodes_ranges_configuration(self):
        policy=target._OutboundPolicy();policy.phase='tx_data';policy.channel=100
        def request(payload):
            return dict(function='PassThruWriteMsgs',channel=100,count=1,timeout=2000,
                        messages=[target._message(target._packet(payload))],physical=False)
        good=b'\x03'+bytes(4)+b'\x02\x00'
        policy.check(request(good))
        bad=[bytes([code])+good[1:] for code in [0,1,2,4,5,6,0x20,0x21,0x22,0x23,0x24,0x25,0x31,0x36]]
        bad += [b'\x03'+(512).to_bytes(4,'big')+b'\x02\x00',b'\x03'+(0x100000).to_bytes(4,'big')+b'\x02\x00',
                b'\x03'+bytes(4)+b'\x00\x01',b'\x03'+bytes(4)+b'\x02\x02']
        for payload in bad:
            with self.subTest(payload=payload.hex()),self.assertRaises(ValueError):policy.check(request(payload))
        for mutation in [dict(function='PassThruIoctl'),dict(device=1),dict(physical=True),dict(token='orphan'),dict(channel=101),dict(count=2)]:
            item=request(good);item.update(mutation)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):policy.check(item)

    def test_exact_version_and_progression(self):
        p=target._OutboundPolicy();p.phase='rx_version'
        with self.assertRaises(ValueError):p.accept(reply(target.VERSION.replace(b'1.07',b'1.08'),1))
        p.accept(reply(target.VERSION,1));self.assertEqual(p.phase,'tx_data')
        p.phase='rx_data';p.next_address=target.SIZE-target.CHUNK
        p.accept(reply(bytes(512)));self.assertEqual(p.phase,'stop_filter')
        with self.assertRaises(ValueError):p.check({'function':'PassThruWriteMsgs','physical':False})

    def test_network_failure_latches_terminal_before_more_send(self):
        class Socket:
            def __init__(self):
                raw=json.dumps({'status':1}).encode();self.response=struct.pack('!I',len(raw))+raw;self.sent=0;self.closed=False
            def sendall(self,raw):self.sent+=1
            def recv(self,n):out,self.response=self.response[:n],self.response[n:];return out
            def settimeout(self,n):pass
            def close(self):self.closed=True
        c=object.__new__(target._LoopbackClient);c.sock=Socket();c.token='x'*32;c.journal=io.StringIO();c.policy=target._OutboundPolicy();c.sequence=0;c.failed=False
        with self.assertRaises(ValueError):c._call(function='PassThruOpen')
        self.assertTrue(c.failed);self.assertTrue(c.sock.closed)
        with self.assertRaises(ValueError):c._call(function='PassThruOpen')
        self.assertEqual(c.sock.sent,1)

    def test_terminal_and_unknown_rpc_fail_closed(self):
        p=target._OutboundPolicy();p.phase='done'
        for fn in ['PassThruOpen','PassThruSetProgrammingVoltage','PassThruIoctl','PassThruStartPeriodicMsg']:
            with self.subTest(fn=fn),self.assertRaises(ValueError):p.check(dict(function=fn,physical=False))

    def test_original_trace_mutation_or_truncation_revokes_pass(self):
        original=b'{"sequence":0}\n'
        for after in [original[:-1],b'X'+original[1:],b'']:
            report={'status':'PASS_VIRTUAL_RAW_READ_ONLY'}
            self.assertFalse(target._require_trace_prefix(report,original,after))
            self.assertEqual(report['status'],'FAIL')
        report={'status':'PASS_VIRTUAL_RAW_READ_ONLY'}
        self.assertTrue(target._require_trace_prefix(report,original,original+b'{"sequence":1}\n'))
        self.assertEqual(report['status'],'PASS_VIRTUAL_RAW_READ_ONLY')


if __name__=='__main__':unittest.main(verbosity=2)
