"""Bounded static fake transcript model. No transport, filesystem, or loader API.

Inputs to run are fault-test labels and a bounded action ordinal only. The
distributable entry point accepts no arguments. All output is simulated data.
"""
import hashlib
import json
from fixed_data import CONTRACT_JSON, CONTRACT_SHA256

FAULTS=('none','api_failure','output_mismatch','count_zero','bad_checksum',
        'wrong_identity','wrong_version','wrong_ack','truncated','wrong_length',
        'wrong_rx_status','wrong_protocol','trailing_bytes','short_wait')

class ModelFailure(Exception): pass

def require(ok,reason):
    if not ok: raise ModelFailure(reason)

def _copy(value): return json.loads(json.dumps(value))

def _fixed_contract():
    require(hashlib.sha256(CONTRACT_JSON.encode()).hexdigest()==CONTRACT_SHA256,'Pinned contract digest')
    c=json.loads(CONTRACT_JSON)
    require(len(c['frames'])==24 and len(c['actions'])==91 and len(c['cleanup'])==3,'Fixed model dimensions')
    require(c['entry']=='FFFF3004' and c['image_bytes']==1808,'Fixed entry and image size')
    require(c['image_sha256']=='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581','Fixed image')
    require(c['frames'][22]=={'tx':'8010f003310101b6','rx':'80f01003710101f6'},'Fixed start')
    require(c['frames'][23]=={'tx':'beef000101af','rx':'beef000f8141325743353131522d524b3032005f'},'Fixed identity')
    return c

def _frame(wire,beef,reply):
    require(len(wire)>=6,'Frame minimum length')
    if beef:
        require(wire[:2]==b'\xbe\xef','Identity framing')
        size=int.from_bytes(wire[2:4],'big')
    else:
        require(wire[:3]==(b'\x80\xf0\x10' if reply else b'\x80\x10\xf0'),'SSM framing')
        size=wire[3]
    require(len(wire)==size+5,'Exact frame length')
    require((sum(wire[:-1])&255)==wire[-1],'Frame checksum')
    return wire[4:-1]

def _fake(action,fault):
    """Return a copied constant fixture, optionally one fixed negative-test fault."""
    output=_copy(action['output']);status=16 if fault=='api_failure' else 0
    if fault=='output_mismatch': output['injected_mismatch']=True
    if fault=='count_zero': output['count']=0
    if fault=='short_wait': output['elapsed_ms']=0
    if fault in ('bad_checksum','wrong_identity','wrong_version','wrong_ack','truncated','wrong_length',
                 'wrong_rx_status','wrong_protocol','trailing_bytes'):
        require('message' in output,'RX fault requires a message fixture')
        m=output['message'];wire=bytearray.fromhex(m['data_hex'])
        if fault=='wrong_rx_status': m['rx_status']=4
        elif fault=='wrong_protocol': m['protocol']=99
        else:
            require(len(wire)>=6,'Wire fault requires a complete fixture')
            if fault=='bad_checksum': wire[-1]^=1
            elif fault=='truncated': wire=wire[:-1]
            elif fault=='trailing_bytes': wire+=b'\x00'
            elif fault=='wrong_length': wire[3]^=1;wire[-1]=sum(wire[:-1])&255
            else:
                where=5 if fault=='wrong_identity' else (17 if fault=='wrong_version' else 4)
                require(where<len(wire)-1,'Mutation inside fixed response')
                wire[where]^=1;wire[-1]=sum(wire[:-1])&255
            m['data_hex']=wire.hex();m['data_size']=len(wire);m['logged_bytes']=len(wire)
    return status,output

def run(fault='none',fault_step=-1):
    require(fault in FAULTS,'Only fixed fake fault labels')
    require(type(fault_step) is int and -1<=fault_step<94,'Bounded fake fault ordinal')
    require((fault=='none')==(fault_step==-1),'Fault label/ordinal pairing')
    c=_fixed_contract();journal=[];owned={'device':False,'channel':False,'filter':False}
    tx=0;acks=0;pending=False;buffer=b'';identity_done=False;virtual_ms=0;failure=None
    attempted_release=set()

    def call(action,ordinal,cleanup=False):
        nonlocal virtual_ms
        function=action['function'];before=virtual_ms
        status,output=_fake(action,fault if ordinal==fault_step else 'none')
        if function=='VirtualWait' and status==0 and 'elapsed_ms' not in output:
            virtual_ms+=action['input']['milliseconds']
        journal.append({'sequence':len(journal),'source_action':ordinal,'function':function,
            'input':_copy(action['input']),'output':output,'status':status,'cleanup':cleanup,
            'clock':'VIRTUAL_NOT_SILICON','before_ms':before,'after_ms':virtual_ms,'physical':False})
        if function=='PassThruStopMsgFilter': attempted_release.add('filter')
        if function=='PassThruDisconnect': attempted_release.add('channel')
        if function=='PassThruClose': attempted_release.add('device')
        if status==0:
            if function=='PassThruOpen': owned['device']=True
            elif function=='PassThruConnect': owned['channel']=True
            elif function=='PassThruStartMsgFilter': owned['filter']=True;attempted_release.discard('filter')
            elif function=='PassThruStopMsgFilter': owned['filter']=False
            elif function=='PassThruDisconnect': owned['channel']=False;owned['filter']=False
            elif function=='PassThruClose': owned['device']=False
        require(status==0,'Fake status '+str(status)+' at '+function)
        return output

    try:
        for ordinal,action in enumerate(c['actions']):
            require(not identity_done,'Only cleanup after identity')
            function=action['function']
            if function=='PassThruWriteMsgs':
                require(not pending and tx<24,'One ordered fixed transmit per exchange')
                wire=bytes.fromhex(action['input']['message']['data_hex'])
                require(wire.hex()==c['frames'][tx]['tx'],'Transmit whitelist')
                _frame(wire,tx==23,False)
                if tx==22: require(acks==22,'All fifteen chunk ACKs before one start')
                if tx==23: require(acks==23,'Start ACK before identity')
                tx+=1;pending=True;buffer=b''
            output=call(action,ordinal)
            if function=='PassThruReadMsgs':
                require(pending and 1<=tx<=24,'Read only for a pending fixed exchange')
                require(output.get('count')==1,'One receive record')
                m=output['message'];require(m['protocol']==3 and m['tx_flags']==0,'Receive protocol/flags')
                wire=bytes.fromhex(m['data_hex'])
                require(m['data_size']==len(wire)==m['logged_bytes'] and not m['data_truncated'],'Receive byte bounds')
                if m['rx_status']==2: require(not wire and not buffer,'Empty start-of-message only')
                else:
                    require(m['rx_status']==0,'Unexpected receive status')
                    buffer+=wire
                    require(len(buffer)<=len(bytes.fromhex(c['frames'][tx-1]['rx'])),'Bounded fixed reply')
                    _frame(buffer,tx==24,True)
                    require(buffer.hex()==c['frames'][tx-1]['rx'],'Exact expected reply')
                    acks+=1;pending=False
                    if tx==24:
                        require(ordinal==90 and acks==24,'Identity is the final protocol action')
                        identity_done=True
            require(output==action['output'],'Exact captured/model output contract')
        require(identity_done and tx==acks==24 and not pending,'Complete bounded model sequence')
    except ModelFailure as exc: failure=str(exc)
    cleanup_errors=[]
    for offset,action in enumerate(c['cleanup']):
        resource=('filter','channel','device')[offset]
        if owned[resource] and resource not in attempted_release:
            try:
                output=call(action,91+offset,True)
                require(output==action['output'],'Cleanup output contract')
            except ModelFailure as exc: cleanup_errors.append(str(exc))
    passed=failure is None and not cleanup_errors and not any(owned.values()) and identity_done
    return {'status':'PASS_OFFLINE_KERNEL_START_IDENTITY_ONLY' if passed else 'FAIL_TERMINAL',
        'physical':False,'backend':'STATIC_FAKE_ONLY','contract_sha256':CONTRACT_SHA256,
        'tx_attempts':tx,'acknowledged_exchanges':acks,'identity_validated':identity_done,
        'failure':failure,'cleanup_errors':cleanup_errors,'cleanup_confirmed':not any(owned.values()),
        'remaining_resources':owned,'virtual_ms':virtual_ms,'retry_count':0,'journal':journal}
