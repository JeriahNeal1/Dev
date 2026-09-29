"""Independent audit of fake-provider capture, never a physical proof."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,hashlib,collections
def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);a=p.parse_args();events=[json.loads(x) for x in a.trace.read_text().splitlines()]
    normalized=[];tx=[];issues=[];counts=collections.Counter()
    for i,e in enumerate(events):
        q=e['request'];r=e['response'];counts[q['function']]+=1
        for field in ('utc_filetime','monotonic_counter','monotonic_frequency','thread','pid'):
            if field not in q:issues.append(f'{i}: missing{field}')
        if e['sequence']!=i:issues.append(f'{i}: sequencegap')
        if 'status' not in r or not e.get('virtual_state_before') or not e.get('virtual_state_after'):issues.append(f'{i}: incompletestate')
        nq={k:v for k,v in q.items() if k not in ('utc_filetime','monotonic_counter','monotonic_frequency','thread','pid','input_pointer','output_pointer','name_pointer')}
        normalized.append({'request':nq,'response':r,'before':e['virtual_state_before'],'after':e['virtual_state_after']})
        if q['function']=='PassThruWriteMsgs':tx += [{'protocol':m['protocol'],'tx_flags':m['tx_flags'],'data_hex':m['data_hex']} for m in q['messages']]
    stable=json.dumps(normalized,sort_keys=True,separators=(',',':')).encode();transmitted=json.dumps(tx,sort_keys=True,separators=(',',':')).encode()
    report={'schema':1,'status':'PASS_LOG_SCHEMA' if not issues else 'FAIL','installed_Read_qualification':False,'calls':len(events),'function_counts':dict(counts),'raw_trace_sha256':hashlib.sha256(a.trace.read_bytes()).hexdigest(),'normalized_trace_sha256':hashlib.sha256(stable).hexdigest(),'transmitted_trace_sha256':hashlib.sha256(transmitted).hexdigest(),'normalization':'Only caller timestamp/thread/pid and process pointers omitted; no protocol message/return/state omitted','issues':issues}
    (a.trace.parent/'normalized_trace.json').write_bytes(stable+b'\n');(a.trace.parent/'transmitted_trace.json').write_bytes(transmitted+b'\n');(a.trace.parent/'TRACE_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
