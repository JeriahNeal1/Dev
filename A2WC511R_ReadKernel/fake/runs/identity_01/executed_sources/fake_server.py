"""Private loopback server for the pinned native fake DLL; no device APIs.

Only the fixed read-kernel host's eight I/O APIs and one bounded data-rate IOCTL
are modeled. Every kernel reply is obtained from OwnedKernelECU CPU execution.
"""
import sys
sys.dont_write_bytecode = True
import json,os,socket,socketserver,struct,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import require,sha256
from fake.model import OwnedKernelECU

FAULTS=('none','identity','upload_begin','upload_middle','upload_final','entry','version',
        'read_begin','read_middle','read_final','read_disconnect','read_checksum','read_address',
        'read_duplicate','read_pass','read_truncate','read_extra')

def frame_receive(sock,authenticated):
    sock.settimeout(300 if authenticated else 5)
    first=sock.recv(1)
    if not first:raise EOFError()
    deadline=time.monotonic()+5
    def receive(n):
        result=bytearray()
        while len(result)<n:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('Whole RPC frame deadline')
            sock.settimeout(remaining);part=sock.recv(n-len(result))
            if not part:raise EOFError('Incomplete RPC frame')
            result.extend(part)
        return bytes(result)
    size=int.from_bytes(first+receive(3),'big')
    require(0<size<=65536,'RPC frame bound')
    return receive(size)

def decode_message(message):
    require(type(message) is dict and message.get('protocol')==3,'Only raw ISO9141')
    text=message.get('data_hex');require(type(text) is str and len(text)%2==0 and 2<=len(text)<=1046,'Complete bounded wire hex')
    raw=bytes.fromhex(text)
    require(message.get('tx_flags',0)==message.get('rx_status',0)==0,'No special TX/RX flags')
    return raw

class Provider:
    def __init__(self,folder,binding,fixture,fault='none'):
        require(fault in FAULTS,'Fixed fault name')
        self.folder=Path(folder);self.fault=fault;self.failed=False;self.open=False;self.channel=False
        self.baud=4800;self.filter=None;self.queue=None;self.call_index=0;self.upload_index=0;self.read_index=0;self.previous_read=None
        kernel=Path(binding['kernel_path']).read_bytes()
        require(sha256(kernel)==binding['kernel_sha256'],'Exact compiled kernel')
        require(sha256(Path(binding['manifest_path']).read_bytes())==binding['manifest_sha256'],'Build manifest pin')
        require(sha256(Path(fixture['path']).read_bytes())==fixture['sha256'],'Fixture identity')
        self.ecu=OwnedKernelECU(binding['manifest_path'],fixture['path'],fixture['sha256'],kernel,binding['kernel_sha256'],self.folder/'execution')
        self.log=(self.folder/'provider.jsonl').open('x',encoding='utf8',buffering=1)
        self.intent=(self.folder/'provider_intents.jsonl').open('x',encoding='utf8',buffering=1)

    def _write(self,stream,event):
        stream.write(json.dumps(event,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())

    def snapshot(self):
        (self.folder/'model_events.json').write_text(json.dumps(self.ecu.events,indent=2)+'\n')
        if self.ecu.cpu:
            (self.folder/'execution_coverage.json').write_text(json.dumps(self.ecu.cpu.coverage(),indent=2)+'\n')
        (self.folder/'provider_state.json').write_text(json.dumps({'physical':False,'calls':self.call_index,
            'failed':self.failed,'open':self.open,'channel':self.channel,'baud':self.baud,
            'state':self.ecu.state,'read_blocks':self.read_index,'upload_blocks':self.upload_index,
            'kernel_executed':self.ecu.cpu is not None,'provider_close_is_ECU_reset':False},indent=2)+'\n')

    def call(self,request):
        require(not self.failed,'Provider terminal after fault/rejection')
        q={key:value for key,value in request.items() if key!='token'}
        self._write(self.intent,{'sequence':self.call_index,'phase':'BEFORE_DISPATCH','request':q,'physical':False})
        try:
            reply=self.dispatch(q)
        except Exception as error:
            self.failed=True;reply={'status':7,'error':type(error).__name__+': '+str(error)}
        if reply['status']:
            self.failed=True
        self._write(self.log,{'sequence':self.call_index,'request':q,'response':reply,'state':self.ecu.state,'physical':False})
        self.call_index+=1
        return reply

    def dispatch(self,q):
        fn=q.get('function')
        require('invalid_arguments' not in q and 'native_exception' not in q,'Native ABI exception')
        if fn=='PassThruOpen':
            require(not self.open and q.get('name_hex','')=='','One nameless fake open');self.open=True
            return {'status':0,'device':1}
        require(self.open,'Open fake required')
        if fn=='PassThruClose':
            require(q.get('device')==1 and not self.channel,'Close only after disconnect');self.open=False
            return {'status':0}
        if fn=='PassThruConnect':
            require(not self.channel and q.get('device')==1 and q.get('protocol')==3 and q.get('flags')==0x200 and q.get('baud')==4800,'Exact initial fake connection')
            self.channel=True;return {'status':0,'channel':100}
        require(self.channel,'Connected fake channel required')
        if fn=='PassThruIoctl':
            require(q.get('id')==100 and q.get('ioctl')==2,'Only SET_CONFIG on fixed channel')
            newbaud=15625 if self.baud==4800 else 62500 if self.baud==15625 else None
            state='DECLARE' if self.baud==4800 else 'KERNEL'
            require(newbaud is not None and self.ecu.state==state and q.get('config')==[{'parameter':1,'value':newbaud}],'Only exact expected baud transition')
            self.baud=newbaud;return {'status':0}
        require(q.get('channel')==100,'Fixed channel identifier')
        if fn=='PassThruDisconnect':
            require(self.filter is None and self.queue is None,'Filter/queue must be empty at disconnect');self.channel=False
            return {'status':0,'meaning':'HOST_TRANSPORT_CLOSE_NOT_ECU_RESET'}
        if fn=='PassThruStartMsgFilter':
            mask=decode_message(q.get('mask'));pattern=decode_message(q.get('pattern'))
            require(q.get('filter_type')==1 and q.get('flow') is None and self.filter is None,'Single pass filter')
            expected=(b'\xFF\xFF\xFF',b'\x80\xF0\x10') if self.baud!=62500 else (b'\xFF\xFF',b'\xBE\xEF')
            require((mask,pattern)==expected,'Exact protocol filter');self.filter=1
            return {'status':0,'id':1}
        if fn=='PassThruStopMsgFilter':
            require(self.filter==1 and q.get('id')==1 and self.queue is None,'Exact filter close');self.filter=None
            return {'status':0}
        if fn=='PassThruWriteMsgs':
            require(self.filter==1 and self.queue is None and q.get('count')==1 and q.get('timeout')==1000,'Single synchronous request; no pending reply')
            require(type(q.get('messages')) is list and len(q['messages'])==1,'Exactly one TX')
            wire=decode_message(q['messages'][0]);state=self.ecu.state
            # Faults are injected at the transport/response boundary and recorded;
            # they never fabricate a successful kernel execution result.
            block=self.upload_index
            upload_count=(len(self.ecu.kernel)+127)//128
            drop=(state=='UPLOAD' and ((self.fault=='upload_begin' and block==0) or (self.fault=='upload_middle' and block==upload_count//2) or (self.fault=='upload_final' and block==upload_count-1)))
            drop=drop or (state=='ENTRY' and self.fault=='entry')
            isread=state=='KERNEL' and len(wire)>4 and wire[4]==3
            if isread:
                drop=drop or (self.fault=='read_begin' and self.read_index==0) or (self.fault=='read_middle' and self.read_index==2048) or (self.fault=='read_final' and self.read_index==4095)
                if self.fault=='read_disconnect' and self.read_index==16:
                    self.channel=False;return {'status':2,'count':0,'fault':'injected_disconnect'}
            if drop:
                self.queue=None;self.dropped=True
                return {'status':0,'count':1,'fault':'dropped_before_ECU_processing'}
            reply=self.ecu.exchange(wire,self.baud)
            if state=='IDENTITY' and self.fault=='identity':
                reply=bytearray(reply);reply[8]^=1;reply[-1]=sum(reply[:-1])&255;reply=bytes(reply)
            if state=='UPLOAD':self.upload_index+=1
            if state=='KERNEL' and wire[4]==1 and self.fault=='version':
                reply=bytearray(reply);reply[5]^=1;reply[-1]=sum(reply[:-1])&255;reply=bytes(reply)
            if isread:
                if self.read_index==16:
                    changed=bytearray(reply)
                    if self.fault=='read_checksum':changed[-1]^=1
                    if self.fault=='read_address':changed[9]^=2;changed[-1]=sum(changed[:-1])&255
                    if self.fault=='read_pass':changed[5]^=1;changed[-1]=sum(changed[:-1])&255
                    if self.fault=='read_truncate':changed=changed[:-1]
                    if self.fault=='read_extra':changed.append(0)
                    reply=bytes(changed)
                    if self.fault=='read_duplicate':reply=self.previous_read
                self.previous_read=reply;self.read_index+=1
            self.queue=reply
            return {'status':0,'count':1}
        if fn=='PassThruReadMsgs':
            require(q.get('count')==1 and q.get('timeout')==1000,'Single bounded RX')
            if self.queue is None:return {'status':9,'messages':[],'error':'No response; terminal no-retry fault'}
            raw=self.queue;self.queue=None
            return {'status':0,'messages':[{'protocol':3,'rx_status':0,'tx_flags':0,'timestamp':self.call_index,'extra':len(raw),'data_hex':raw.hex()}]}
        raise ValueError('API outside acquisition allowlist: '+str(fn))

def main():
    require(len(sys.argv)==2,'One private session specification required')
    spec=json.loads(Path(sys.argv[1]).read_text());folder=Path(spec['folder']).resolve()
    require(folder.parent==ROOT/'fake/runs','Fixed new-project session root')
    provider=Provider(folder,spec['binding'],spec['fixture'],spec.get('fault','none'))
    token=spec['token'];require(type(token) is str and len(token)==64,'Private random token')
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            authenticated=False
            self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
            try:
                while True:
                    q=json.loads(frame_receive(self.request,authenticated))
                    require(type(q) is dict and q.get('token')==token,'Private RPC token')
                    authenticated=True
                    reply=json.dumps(provider.call(q),sort_keys=True).encode()
                    self.request.sendall(struct.pack('!I',len(reply))+reply)
            except EOFError:pass
            except Exception:
                with (folder/'server_errors.log').open('a') as out:out.write(traceback.format_exc())
            finally:
                provider.snapshot()
    with socketserver.TCPServer(('127.0.0.1',0),Handler) as server:
        (folder/'ready.json').write_text(json.dumps({'port':server.server_address[1],'physical':False}))
        server.serve_forever(poll_interval=.05)

if __name__=='__main__':main()
