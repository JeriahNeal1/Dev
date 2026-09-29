"""Loopback-only fake J2534 state and audit server. No physical transport."""
import sys
sys.dont_write_bytecode=True
import argparse,datetime,json,socketserver,struct,time,traceback,re,os
from pathlib import Path
from collections import deque
from virtual_ecu import VirtualECU, _reference
from faults import FaultPlan

def receive_rpc_frame(sock,*,authenticated=False,idle_timeout=300,frame_timeout=5):
    """Bound first authentication and each started frame; permit authenticated idle."""
    deadline=None if authenticated else time.monotonic()+frame_timeout
    sock.settimeout(idle_timeout if authenticated else frame_timeout)
    first=sock.recv(1)
    if not first:raise EOFError()
    if authenticated:deadline=time.monotonic()+frame_timeout
    def receive(n):
        result=b''
        while len(result)<n:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('RPC total frame deadline')
            sock.settimeout(remaining)
            part=sock.recv(n-len(result))
            if not part:raise ValueError('Truncated RPC frame')
            result+=part
        return result
    n=struct.unpack('!I',first+receive(3))[0]
    if not 0<n<=4*1024*1024:raise ValueError('RPC size')
    return receive(n)

def uint32(value,name):
    if type(value) is not int or not 0<=value<=0xFFFFFFFF:raise ValueError(name+' must be uint32')
    return value

def decode_message(msg,protocol):
    if type(msg) is not dict:raise ValueError('message must be an object')
    if uint32(msg['protocol'],'protocol')!=protocol:raise ValueError('message protocol mismatch')
    text=msg['data_hex']
    if type(text) is not str or not 2<=len(text)<=8256 or len(text)%2 or not re.fullmatch('[0-9a-fA-F]+',text):raise ValueError('invalid complete message hex')
    data=bytes.fromhex(text)
    for field in ('rx_status','tx_flags','timestamp','extra'):uint32(msg.get(field,0),field)
    if msg.get('extra',0)>len(data):raise ValueError('extra data index exceeds message')
    if msg.get('tx_flags',0):raise ValueError('TX flags are not modeled for raw ISO9141')
    return data

class Provider:
    def __init__(self,folder,mask=0x40,ecuflash_extensions=False,variant='baseline',fault=None):
        self.ecuflash_extensions=ecuflash_extensions
        self.folder=Path(folder);self.ecu=VirtualECU(response_mask=mask,sentinel_variant=variant);self.fault=FaultPlan(fault);self.open=False;self.channels={};self.next_channel=100;self.last_error='No error';self.counter=0
        (self.folder/'synthetic_flash.bin').write_bytes(self.ecu.flash)
        self.log=(self.folder/'j2534.jsonl').open('x',encoding='utf8',buffering=1)
        self.intents=(self.folder/'rpc_intents.jsonl').open('x',encoding='utf8',buffering=1)
        self.audit_failed=False
    def call(self,q):
        if self.audit_failed:raise RuntimeError('Audit journal failed; provider stopped before further dispatch')
        before=self.ecu.stage
        request={k:v for k,v in q.items() if k!='token'} if type(q) is dict else {'malformed_rpc_type':type(q).__name__}
        intent={'sequence':self.counter,'server_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'server_monotonic_ns':time.monotonic_ns(),'request':request,'virtual_state_before':before,
                'phase':'BEFORE_DISPATCH','physical':False}
        try:
            self.intents.write(json.dumps(intent,sort_keys=True)+'\n');self.intents.flush();os.fsync(self.intents.fileno())
        except Exception:
            self.audit_failed=True;raise
        try:
            if type(q) is not dict or type(q.get('function')) is not str:raise ValueError('RPC function object required')
            r=self.dispatch(q)
        except Exception as e:r={'status':7,'error':type(e).__name__+': '+str(e),'traceback':traceback.format_exc()}
        if r['status']:self.last_error=r.get('error','J2534 status '+str(r['status']))
        event={'sequence':self.counter,'server_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'server_monotonic_ns':time.monotonic_ns(),'request':request,'response':r,'virtual_state_before':before,'virtual_state_after':self.ecu.stage,'physical':False}
        try:
            self.log.write(json.dumps(event,sort_keys=True)+'\n');self.log.flush();os.fsync(self.log.fileno())
        except Exception:
            self.audit_failed=True;raise
        self.counter+=1
        try:(self.folder/'live_state.json').write_text(json.dumps({'calls':self.counter,'stage':self.ecu.stage,'last_function':request.get('function'),'last_status':r['status'],'last_error':self.last_error}))
        except OSError:
            # The complete response is already durable. A status-display failure
            # must not turn an executed call into an ambiguous failed RPC.
            self.last_status_display_error=traceback.format_exc()
            try:
                with (self.folder/'rpc_errors.log').open('a') as out:out.write('NONCRITICAL_LIVE_STATE_WRITE_FAILED\n'+self.last_status_display_error)
            except OSError:pass  # The primary intent/result journals remain authoritative.
        return r
    def dispatch(self,q):
        fn=q['function']
        if 'invalid_arguments' in q:return {'status':4,'error':str(q['invalid_arguments']),'provenance':'NATIVE_ABI_ARGUMENT_REJECTION_NO_STATE_CHANGE'}
        if 'native_exception' in q:return {'status':7,'error':str(q['native_exception']),'provenance':'NATIVE_PROVIDER_EXCEPTION'}
        if fn=='PassThruOpen':
            if self.open:return {'status':14,'error':'already open'}
            self.open=True;return {'status':0,'device':1,'provenance':'VIRTUAL_DEVICE_ONLY'}
        if fn=='PassThruClose':
            if not self.open or q['device']!=1:return {'status':26}
            self.open=False;self.channels.clear();return {'status':0}
        if fn=='PassThruGetLastError':return {'status':0,'error':q.get('native_error',self.last_error)}
        if fn=='PassThruReadVersion':
            if not self.open or q.get('device')!=1:return {'status':26,'error':'invalid or unopened device'}
            return {'status':0,'firmware':'A2WC VIRTUAL ECU 0.1','dll':'A2WC isolated fake 0.1','api':'04.04'}
        if fn=='PassThruConnect':
            if not self.open or q['device']!=1:return {'status':26}
            if q['protocol']!=3:return {'status':3,'error':'Only reviewed ISO9141 modeled'}
            flags=uint32(q['flags'],'flags');baud=uint32(q['baud'],'baud')
            if flags&~0x1200 or not flags&0x200:return {'status':6,'error':'Only explicit raw ISO9141_NO_CHECKSUM framing modeled'}
            if not baud:return {'status':25,'error':'zero baud rate'}
            ch=self.next_channel;self.next_channel+=1
            self.channels[ch]={'protocol':q['protocol'],'baud':baud,'flags':flags,'queue':deque(),'config':{1:baud,3:0},'filters':{},'next_filter':1}
            return {'status':0,'channel':ch}
        if fn=='PassThruIoctl':
            op=q['ioctl'];ch=self.channels.get(q['id'])
            if self.ecuflash_extensions and op==0x70001 and q['id']==0 and q.get('unqualified_debug_argument')==0:
                return {'status':0,'provenance':'OBSERVED_INSTALLED_READ_DLL_DEBUG_FLAGS_ZERO; VENDOR_HEADER_DEBUG_OFF; FAKE_HOST_ONLY'}
            if self.ecuflash_extensions and op==0x70000 and q['id']==1 and self.open and q.get('service_id')==5 and q.get('input_bytes')==[1,0]:
                data=list(b'A2WC-VIRTUAL-ONLY')
                if q.get('output_capacity',0)<len(data):return {'status':18,'error':'serial output capacity'}
                return {'status':0,'output_bytes':data,'provenance':'VENDOR_SAMPLE_INFO5_SERIAL1; EXPLICIT_SYNTHETIC_SERIAL_NOT_HARDWARE_IDENTITY'}
            if self.ecuflash_extensions and op==0x70000 and q['id']==1 and self.open and q.get('service_id')==1:
                payload=q.get('input_bytes')
                if type(payload) is not list or len(payload)!=5 or payload[0]!=1 or any(type(x) is not int or not 0<=x<=255 for x in payload):
                    return {'status':1,'error':'Unmodeled Subaru APP_SERVICE1 request'}
                data=list(_reference.seed_key(bytes(payload[1:])))
                if q.get('output_capacity',0)<len(data):return {'status':18,'error':'key output capacity'}
                return {'status':0,'output_bytes':data,'provenance':'OBSERVED_READ004_TX_AND_RVA9B7E0_OUTPUT4; PUBLIC_REFERENCE_SEED_KEY; NO_HARDWARE_OR_LICENSE_IDENTITY'}
            if self.ecuflash_extensions and op==0x70004 and q['id']==0:
                if q.get('input_pointer') or not q.get('output_pointer') or q.get('output_contract')!='PINNED_ECUFLASH_1_44_4870_SINGLE_UTF16LE_NUL_PATH_MAX512_WCHAR':return {'status':4,'error':'70004 pinned ABI mismatch'}
                return {'status':0,'device_instance':'A2WC511R-VIRTUAL-ONLY','provenance':'PINNED_CALLER_RVA96270_UTF16_PATH; SYNTHETIC_DEVICE_NOT_OPENPORT'}
            if op==3 and q['id']==1 and self.open:return {'status':0,'value':12500,'provenance':'SYNTHETIC_12_5V_NOT_MEASURED'}
            if op==0x70001 and self.open and q['id']==1:return {'status':0,'provenance':'FAKE_DLL_DEBUG_FLAGS_NO_DEVICE_EFFECT'}
            if op in (1,2) and ch:
                items=q.get('config',[])
                if type(items) is not list or not 1<=len(items)<=128:return {'status':5,'error':'Invalid configuration list'}
                for x in items:
                    uint32(x['parameter'],'parameter')
                    if op==2:uint32(x['value'],'value')
                if op==2:
                    known={1,3,7,10,12,14,15,16,17,18,19,20,21,22,25,32}
                    if any(x['parameter'] not in known for x in items):return {'status':1,'error':'Unknown SET_CONFIG parameter; rejected'}
                    if any(x['parameter']==3 and x['value'] not in (0,1) or x['parameter']==1 and x['value']==0 for x in items):return {'status':5,'error':'Invalid loopback or baud value'}
                    # Timing values are retained, not applied to electrical timing.
                    for x in items:ch['config'][x['parameter']]=x['value']
                    return {'status':0,'provenance':'FAKE_PROVIDER_CONFIGURATION_STORED_ONLY_NO_PHYSICAL_TIMING'}
                if any(x['parameter'] not in ch['config'] for x in items):return {'status':1,'error':'unknown GET_CONFIG parameter'}
                return {'status':0,'config':[{'parameter':x['parameter'],'value':ch['config'][x['parameter']]} for x in items]}
            if op in (7,8,9,10) and ch:
                if op==8:ch['queue'].clear()
                if op==10:ch['filters'].clear()
                return {'status':0,'provenance':'FAKE_QUEUE_OR_FILTER_CLEANUP'}
            return {'status':1,'error':f'Unsupported IOCTL 0x{op:X}; no success fabricated'}
        if fn=='PassThruSetProgrammingVoltage':
            if self.ecuflash_extensions and self.open and q.get('device')==1 and q.get('pin')==9 and q.get('voltage')==0xFFFFFFFF:
                return {'status':0,'virtual_pin9':'OFF','provenance':'OBSERVED_INSTALLED_READ_PIN9_VOLTAGE_OFF; VENDOR_HEADER_FFFFFFFF; NO_ELECTRICAL_EFFECT'}
            return {'status':1,'error':'Voltage operation not yet modeled; no hardware access'}
        ch=self.channels.get(q.get('channel'))
        if not ch:return {'status':2,'error':'unknown channel'}
        if fn=='PassThruDisconnect':del self.channels[q['channel']];return {'status':0,'provenance':'HOST_CHANNEL_CLOSE_NOT_ECU_RESET'}
        if fn=='PassThruStartMsgFilter':
            if q['filter_type']!=1:return {'status':1,'error':'Only PASS_FILTER supported'}
            if q.get('flow') is not None:
                flow=q['flow']
                observed_unused=self.ecuflash_extensions and flow.get('protocol')==3 and flow.get('data_hex')=='00000000' and flow.get('tx_flags',0)==0
                if not observed_unused:return {'status':6,'error':'Unmodeled PASS_FILTER flow argument'}
            mask,pattern=q.get('mask'),q.get('pattern')
            try:mask_bytes=decode_message(mask,ch['protocol']);pattern_bytes=decode_message(pattern,ch['protocol'])
            except (KeyError,TypeError,ValueError) as e:return {'status':10,'error':str(e)}
            if len(mask_bytes)!=len(pattern_bytes):return {'status':10,'error':'Invalid mask/pattern lengths'}
            identity=ch['next_filter'];ch['next_filter']+=1
            ch['filters'][identity]={'mask':mask_bytes,'pattern':pattern_bytes};return {'status':0,'id':identity}
        if fn=='PassThruStopMsgFilter':
            if q['id'] not in ch['filters']:return {'status':22}
            del ch['filters'][q['id']];return {'status':0}
        if fn=='PassThruWriteMsgs':
            messages=q.get('messages');count=q.get('count')
            if type(messages) is not list or type(count) is not int or not 1<=count<=128 or count!=len(messages):return {'status':10,'count':0,'error':'Invalid TX batch count'}
            try:
                uint32(q['timeout'],'timeout')
                decoded=[decode_message(msg,ch['protocol']) for msg in messages]
            except (KeyError,TypeError,ValueError) as e:return {'status':10,'count':0,'error':str(e)}
            events=[];delivery=[]
            for msg,data in zip(messages,decoded):
                fault=self.fault.match(data)
                if fault and fault['action']=='disconnect':
                    del self.channels[q['channel']]
                    return {'status':8,'count':len(events),'virtual_events':events,'delivery_events':delivery,'fault':fault,'error':'Injected fake device disconnect before TX delivery'}
                try:events.append(self.ecu.handle_tx(msg['protocol'],data))
                except Exception as e:
                    return {'status':7,'count':len(events),'virtual_events':events,'delivery_events':delivery,'error':'Model failure: '+repr(e),'traceback':traceback.format_exc()}
                if ch['config'].get(3):
                    ch['queue'].append(dict(msg,rx_status=1,tx_flags=0,timestamp=0,extra=len(data),provenance={'classification':'VIRTUAL_TX_ECHO','timestamp_origin':'SYNTHETIC_ZERO_UNTIMED','not_vehicle_telemetry':True}))
                    delivery.append({'kind':'TX_ECHO','queued':True,'wire_hex':data.hex()})
                replies=self.ecu.drain_replies()
                if fault:events[-1]['injected_fault']=fault
                for reply in replies:
                    if fault and fault['action']=='timeout':
                        delivery.append({'kind':'INJECTED_REPLY_DROP','queued':False,'wire_hex':reply.data.hex(),'fault':fault});continue
                    if fault:
                        from dataclasses import replace
                        raw=reply.data
                        if fault['action']=='checksum':raw=raw[:-1]+bytes((raw[-1]^1,))
                        elif fault['action']=='malformed':raw=raw[:2]+b'\x00\x01'+raw[4:]
                        else:raise ValueError('Unimplemented reply fault action')
                        reply=replace(reply,data=raw,provenance=dict(reply.provenance,injected_fault=fault))
                    accepted=False
                    for f in ch['filters'].values():
                        mask=f['mask'];pattern=f['pattern']
                        if len(reply.data)>=len(mask) and all((v&m)==(p&m) for v,m,p in zip(reply.data,mask,pattern)):accepted=True
                    delivery.append({'kind':'ECU_MODEL_REPLY','queued':accepted,'reason':'PASS_FILTER_MATCH' if accepted else 'NO_PASS_FILTER_MATCH','wire_hex':reply.data.hex(),'provenance':reply.provenance})
                    if accepted:ch['queue'].append({'protocol':reply.protocol_id,'rx_status':0,'tx_flags':0,'timestamp':0,'extra':len(reply.data),'data_hex':reply.data.hex(),'provenance':dict(reply.provenance,timestamp_origin='SYNTHETIC_ZERO_UNTIMED')})
            return {'status':0,'count':len(messages),'virtual_events':events,'delivery_events':delivery,'provenance':'TX_ACCEPTANCE_IS_NOT_ECU_ACKNOWLEDGEMENT'}
        if fn=='PassThruReadMsgs':
            if type(q['count']) is not int or not 1<=q['count']<=128:return {'status':10,'messages':[],'error':'Invalid RX count'}
            uint32(q['timeout'],'timeout')
            messages=[]
            while ch['queue'] and len(messages)<q['count']:messages.append(ch['queue'].popleft())
            if not messages and q['timeout']:time.sleep(min(q['timeout']/1000,.05))
            return {'status':0 if messages else (9 if q['timeout'] else 16),'messages':messages,'provenance':'FAKE_IMMEDIATE_QUEUE_READ_TIMEOUT_CAPPED_AT_50MS_NOT_NATIVE_TIMING'}
        return {'status':1,'error':fn+' is not implemented; no success fabricated'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('session',type=Path);args=parser.parse_args()
    spec=json.loads(args.session.read_text());folder=Path(spec['directory']);token=spec['environment']['A2WC_RPC_TOKEN'];provider=Provider(folder,mask=spec.get('response_mask',0x40),ecuflash_extensions=spec.get('ecuflash_extensions',False),variant=spec.get('variant','baseline'),fault=spec.get('fault'))
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            import socket
            self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
            try:
                authenticated=False
                while True:
                    q=json.loads(receive_rpc_frame(self.request,authenticated=authenticated))
                    if type(q) is not dict or q.get('token')!=token:raise ValueError('RPC envelope/token mismatch')
                    authenticated=True
                    self.request.settimeout(5)
                    response=json.dumps(provider.call(q),sort_keys=True).encode();self.request.sendall(struct.pack('!I',len(response))+response)
            except EOFError:pass
            except Exception:
                with (folder/'rpc_errors.log').open('a') as out:out.write(traceback.format_exc())
    with socketserver.TCPServer(('127.0.0.1',0),Handler) as server:
        (folder/'rpc_ready.json').write_text(json.dumps({'port':server.server_address[1],'physical':False}))
        server.serve_forever(poll_interval=.1)
if __name__=='__main__':main()
