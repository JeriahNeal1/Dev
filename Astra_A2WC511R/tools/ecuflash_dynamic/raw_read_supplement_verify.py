"""Independent offline reconstruction from client and fake-provider journals."""
import sys
sys.dont_write_bytecode=True
import argparse
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def verify(name):
    if not re.fullmatch('[A-Za-z0-9_-]+',name):raise ValueError('Simple session name required')
    folder=ROOT/'reports/local/ecuflash_dynamic/raw_read_supplement'/name
    report=json.loads((folder/'RESULT.json').read_text())
    provider=[json.loads(x) for x in (folder/'COMBINED_PROVIDER_TRACE.jsonl').read_text().splitlines()]
    records=[json.loads(x) for x in (folder/'SUPPLEMENT_RPC.jsonl').read_text().splitlines()]
    results=[x for x in records if x['phase']=='RESULT']
    intents=[x for x in records if x['phase']=='INTENT']
    tail=provider[report['original_trace']['events']:]
    assert len(results)==len(intents)==len(tail)==4104
    assert all(a['request']==b['request'] and a['response']==b['response'] for a,b in zip(results,tail))
    assert all(a['sequence']==b['sequence']==i and a['request']==b['request'] for i,(a,b) in enumerate(zip(intents,results)))
    raw=bytearray();reads=0;commands=[];last=None
    for event in results:
        request,response=event['request'],event['response']
        if request['function']=='PassThruWriteMsgs':
            last=bytes.fromhex(request['messages'][0]['data_hex']);commands.append(last[4])
        if request['function']=='PassThruReadMsgs' and last[4]==3:
            assert int.from_bytes(last[5:9],'big')==len(raw) and last[9:11]==b'\x02\x00'
            frame=bytes.fromhex(response['messages'][0]['data_hex'])
            assert len(frame)==518 and frame[:5]==bytes.fromhex('beef020183') and sum(frame[:-1])&255==frame[-1]
            raw.extend(frame[5:-1]);reads+=1
    assert reads==2048 and len(raw)==1048576 and bytes(raw)==(folder/'RAW_MODEL_RETURNED_BYTES.bin').read_bytes()
    assert commands==[1]+[3]*2048
    result={'schema':1,'status':'PASS','client_provider_event_crosslinks':4104,
            'independently_reconstructed_response_bytes':len(raw),'raw_read_replies':reads,
            'exact_transmit_command_sequence':'01 then03 repeated2048; noothercommand',
            'reconstructed_sha256':hashlib.sha256(raw).hexdigest(),
            'input_client_trace_sha256':hashlib.sha256((folder/'SUPPLEMENT_RPC.jsonl').read_bytes()).hexdigest(),
            'input_provider_trace_sha256':hashlib.sha256((folder/'COMBINED_PROVIDER_TRACE.jsonl').read_bytes()).hexdigest(),
            'physical':False}
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('session')
    verify(parser.parse_args().session)
