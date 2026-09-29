"""Independent fragmentation/status adversarial tests; no transport execution."""
import sys
sys.dont_write_bytecode=True
import json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import read_request,beef,read_response
from host.stream import ResponseAssembler

def main():
    request=read_request(1,0xFFE00)
    payload=b'\x83\x01'+(0xFFE00).to_bytes(4,'big')+random.Random(37058).randbytes(512)
    wire=beef(payload);checks=[]
    def msg(raw,status=0,extra=None):return {'protocol':3,'rx_status':status,'tx_flags':0,'extra':len(raw) if extra is None else extra,'data_hex':raw.hex()}
    for seed in range(32):
        rng=random.Random(seed);assembler=ResponseAssembler(request)
        assert assembler.consume(msg(b'',2,0)) is None
        assert assembler.consume(msg(request,9,0)) is None
        cursor=0
        while cursor<len(wire):
            chunk=wire[cursor:cursor+rng.randint(1,31)];cursor+=len(chunk)
            result=assembler.consume(msg(chunk,extra=0 if rng.randint(0,1) else len(chunk)))
            assert (result is not None)==(cursor==len(wire))
        assert result==wire and read_response(result,1,0xFFE00)==payload[6:]
    checks.append('32 deterministic arbitrary fragment boundaries and allowed status indications')
    negatives=[msg(wire,4),msg(wire,0,1),msg(b'',0),msg(b'not exact TX',1),msg(b'header',2),
               {**msg(wire),'protocol':4},{**msg(wire),'tx_flags':1},msg(wire+wire)]
    for index,bad in enumerate(negatives):
        assembler=ResponseAssembler(request)
        try:assembler.consume(bad)
        except ValueError:checks.append('metadata/replay negative '+str(index))
        else:raise AssertionError(index)
    assembler=ResponseAssembler(request);assert assembler.consume(msg(wire[:20])) is None
    try:assembler.consume(msg(b'',2,0))
    except ValueError:checks.append('new-start after partial data rejected')
    else:raise AssertionError('status accepted midframe')
    assembler=ResponseAssembler(request)
    for _ in range(4):assembler.consume(msg(b'',8,0))
    try:assembler.consume(msg(b'',8,0))
    except ValueError:checks.append('status-only flood bounded')
    else:raise AssertionError('unboundedstatus')
    result={'schema':1,'status':'PASS','checks':checks,'fragmented_positive_cases':32,'DLLs_loaded':0,'RPC_calls':0,'physical':False}
    out=ROOT/'host/tests';out.mkdir(exist_ok=True)
    (out/'STREAM_TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
