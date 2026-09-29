"""Adversarial pure host/boot contract checks. No DLL or CPU replies synthesized."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import *
from host.state import HostState
from fake.model import OwnedKernelECU,BF_PAYLOAD

def main(output_dir=None):
    checks=[]
    def reject(name,call):
        try:call()
        except (ValueError,TypeError):checks.append(name);return
        raise AssertionError('Accepted adversarial case: '+name)
    assert seed_key(bytes.fromhex('12345678')).hex()=='e78f1f21'
    assert seed_key(bytes(4)).hex()=='2a52f963'
    assert encrypt_upload(bytes.fromhex('00090009')).hex()=='2178b10a'
    assert decrypt_upload(bytes.fromhex('2178b10a')).hex()=='00090009';checks.append('independent known crypto vectors')
    kernel=b'\x00\x09\x00\x09'+b'\x00\x00\x5A\x9C';digest=sha256(kernel)
    assert stock_entry_checksum(kernel)==0x5AA5
    reject('changed kernel hash',lambda:HostState(kernel,'0'*64))
    reject('bad entry checksum',lambda:HostState(bytes(8),sha256(bytes(8))))
    for size in (0,4,7,8193,8196,0x100000):reject('upload length '+str(size),lambda size=size:declaration(size))
    assert declaration(8192)[4:-1]==bytes.fromhex('34ff300004002000');checks.append('maximum8192 exact fixed span')
    for bad in (b'',b'\x80',ssm(b'\xBF')[:-1],ssm(b'\xBF')[:-1]+b'\x00',ssm(b'\xBF',True)):
        reject('malformed SSM '+bad.hex(),lambda bad=bad:parse_ssm(bad))
    for pair in ((-1,0),(2,0),(0,-512),(0,1),(0,0x100000)):
        reject('invalid fixed read '+str(pair),lambda pair=pair:read_request(*pair))
    correct=beef(b'\x83\x00'+bytes(4)+bytes(range(256))*2)
    assert len(read_response(correct,0,0))==512;checks.append('full raw reply baseline')
    for prefix in (b'\x83\x01'+bytes(4),b'\x83\x00'+(512).to_bytes(4,'big'),b'\x82\x00'+bytes(4)):
        reject('wrong read discriminant '+prefix.hex(),lambda prefix=prefix:read_response(beef(prefix+bytes(512)),0,0))
    for bad in (correct[:-1],correct+b'\x00',correct[:-1]+bytes((correct[-1]^1,))):reject('malformed raw reply',lambda bad=bad:read_response(bad,0,0))
    h=HostState(kernel,digest);bad=bytearray(BF_PAYLOAD);bad[4]^=1
    reject('wrong identity terminal',lambda:h.accept(ssm(bytes(bad),True)));assert h.status=='FAIL' and h.pending is None
    reject('no recovery after failed identity',lambda:h.accept(ssm(BF_PAYLOAD,True)))
    # Boot model tests stop before entry. Actual kernel execution is exclusively
    # tested in the simulator/native integration suite against the real build.
    ecu=OwnedKernelECU(ROOT/'unused_manifest.json',ROOT/'unused_rom.bin','0'*64,kernel,digest,ROOT/'fake/not_created_by_test')
    h=HostState(kernel,digest)
    for _ in range(8):
        step=h.pending;h.accept(ecu.exchange(step.wire,step.baud))
        if ecu.state=='UPLOAD':break
    assert ecu.state=='UPLOAD'
    reject('duplicate34 rejected before any byte',lambda:ecu.exchange(declaration(len(kernel)),15625));assert ecu.state=='FAIL'
    checks.append('exact modeled bootstrap reaches upload with matched ACKs')
    def version_ready():
        machine=HostState(kernel,digest)
        positives={'identity':BF_PAYLOAD,'communication':bytes.fromhex('C1EF8F'),'timings':bytes.fromhex('C30000FF00FF00'),
                   'seed':bytes.fromhex('670112345678'),'key':bytes.fromhex('670234'),'session':bytes.fromhex('5085'),
                   'declaration':bytes.fromhex('7484'),'upload':bytes.fromhex('76'),'entry':bytes.fromhex('710101')}
        while machine.pending.kind!='version':machine.accept(ssm(positives[machine.pending.kind],True))
        return machine
    h=version_ready();reject('RK01 identity rejected by RK02 host',lambda:h.accept(beef(b'\x81A2WC511R-RK01\0')))
    assert h.status=='FAIL' and h.pending is None
    h=version_ready();h.accept(beef(b'\x81A2WC511R-RK02\0'));assert h.pending.kind=='read'
    checks.append('RK02 exact identity permits first fixed raw request')
    out=Path(output_dir) if output_dir is not None else ROOT/'host/tests';out.mkdir(parents=True,exist_ok=True)
    report={'schema':1,'status':'PASS','checks':checks,'count':len(checks),'scope':'PURE_HOST_POLICY_AND_MODELED_BOOT_ONLY','kernel_executed':False,'DLLs_loaded':0,'RPC_calls':0,'physical':False}
    (out/'CONTRACT_TESTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir');args=parser.parse_args();main(args.output_dir)
