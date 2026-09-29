"""Adversarial finalizer replay checks using the completed native04 capture."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from host.protocol import sha256
from host.finalize import replay_native,record

def main(capture=None,output_dir=None):
    folder=Path(capture) if capture is not None else ROOT/'fake/runs/composite_native04'
    report=json.loads((folder/'RESULT.json').read_text())
    assert report['status']=='PASS_NATIVE_FAKE_COMPILED_KERNEL_TWO_FULL_READS'
    binding=report['binding'];kernel=Path(binding['kernel_path']).read_bytes()
    original=[json.loads(line) for line in (folder/'native_api.jsonl').read_text().splitlines()]
    host,proof=replay_native(original,kernel,binding['kernel_sha256'],False)
    assert host.images[0]==host.images[1]==(folder/'pass0.bin').read_bytes()
    checks=['complete native journal alone reproduces both exact raw files']
    def reject(name,events,expected=None):
        try:replay_native(events,kernel,binding['kernel_sha256'],False)
        except (ValueError,KeyError) as error:
            if expected is not None:assert expected in str(error),(name,str(error))
            checks.append(name);return
        raise AssertionError('Malformed capture accepted: '+name)
    for field,value in (('sequence',99),('status',1),('physical',True),('esp_after',0),
                        ('utc_filetime',0),('frequency',0),('counter',-1),('data_size',100)):
        events=original.copy();events[0]={**events[0],field:value}
        reject('mutated '+field,events)
    for field in ('protocol','rx_status','extra','timestamp','counter'):
        events=original.copy();events[0]=events[0].copy();del events[0][field]
        reject('missing native '+field,events,'Missing/invalid native metadata')
    events=original.copy();events[1]={**events[1],'frequency':events[1]['frequency']+1}
    reject('mixed monotonic clocks',events,'clock frequency')
    events=original.copy();events[1]={**events[1],'function':'PassThruSetProgrammingVoltage'}
    reject('forbidden extra API',events,'fixed API step')
    for field,value in (('count',1),('protocol',3),('rx_status',1),('tx_flags',1),('timestamp',1),('extra',1)):
        events=original.copy();events[0]={**events[0],field:value}
        reject('non-message API forged '+field,events,'exact zero message shape')
    tx=next(i for i,e in enumerate(original) if e['function']=='PassThruWriteMsgs')
    events=original.copy();changed=bytearray.fromhex(events[tx]['wire_hex']);changed[4]^=1;changed[-1]=sum(changed[:-1])&255
    events[tx]={**events[tx],'wire_hex':changed.hex()};reject('valid-checksum wrong TX opcode',events,'Actual TX outside')
    rx=next(i for i,e in enumerate(original) if e['function']=='PassThruReadMsgs' and e['rx_status']==0 and e['data_size']>10)
    events=original.copy();events[rx]={**events[rx],'extra':1};reject('unexplained extra-data index',events,'extra-data bounds')
    events=original.copy();events[rx]={**events[rx],'rx_status':4};reject('RX error status',events)
    events=original.copy();data=bytearray.fromhex(events[rx]['wire_hex']);data[-1]^=1;events[rx]={**events[rx],'wire_hex':data.hex()}
    reject('changed RX byte without matching checksum',events,'checksum')
    reject('missing terminal close',original[:-1],'fixed API step')
    extra={**original[-1],'sequence':len(original)}
    reject('trailing close/replay',original+[extra],'Trailing calls')
    result={'schema':1,'status':'PASS','input_capture':record(folder/'RESULT.json'),'native_journal':record(folder/'native_api.jsonl'),
            'checks':checks,'count':len(checks),'positive_proof':proof,'provider_loaded':False,'transport_calls':0,'physical':False,
            'source':record(Path(__file__)),'finalizer':record(ROOT/'host/finalize.py')}
    out=Path(output_dir) if output_dir is not None else ROOT/'host/tests';out.mkdir(parents=True,exist_ok=True)
    (out/'FINALIZER_TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)},indent=2))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--capture');parser.add_argument('--output-dir');args=parser.parse_args();main(args.capture,args.output_dir)
