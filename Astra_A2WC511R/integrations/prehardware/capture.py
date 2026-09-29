"""Common M07 snapshot caller for replay, native virtual, fake and physical reads."""
import argparse
import json
from pathlib import Path
import time
from transport import create_transport, SnapshotClient, utc_now

def capture(output, backend, count=8, interval_ms=100, authorize_physical_read_only=False):
    if type(count) is not int or not 1<=count<=300:
        raise ValueError('Count must be 1..300')
    if backend in ('replay','native-virtual') and count>8:
        raise ValueError('Finite virtual fixture has only eight samples')
    if type(interval_ms) is not int or not 0<=interval_ms<=60000:
        raise ValueError('Interval must be 0..60000')
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    transport=client=None
    error=cleanup_error=None
    completed=0
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        def emit(row):
            stream.write(json.dumps(row,separators=(',',':'))+'\n');stream.flush()
        emit({'type':'capture_start','backend':backend,'host_utc':utc_now(),
              'ecu_patch':False,'current_ROM_attestation':False,'samples_requested':count})
        try:
            transport=create_transport(backend,output,authorize_physical_read_only=authorize_physical_read_only)
            client=SnapshotClient(transport,timeout_ms=5000)
            if getattr(transport,'identity',None):
                emit(transport.identity)
            for index in range(count):
                if index and interval_ms:
                    time.sleep(interval_ms/1000)
                emit(client.capture());completed+=1
        except BaseException as failure:
            error={'type':type(failure).__name__,'message':str(failure)}
            emit({'type':'capture_failure','host_utc':utc_now(),'error':error})
        finally:
            try:
                if client is not None:client.close()
                elif transport is not None:transport.close()
            except BaseException as failure:
                cleanup_error={'type':type(failure).__name__,'message':str(failure)}
            result={'type':'capture_end','status':'PASS_CAPTURE_ONLY' if error is None and cleanup_error is None else 'FAIL',
                    'backend':backend,'samples_written':completed,'error':error,'cleanup_error':cleanup_error,
                    'host_utc':utc_now(),'retry':False,'current_ROM_attestation':False}
            emit(result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend',required=True,choices=['replay','native-virtual','fake-j2534','physical-j2534'])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--count',type=int,default=8)
    p.add_argument('--interval-ms',type=int,default=100)
    p.add_argument('--authorize-physical-read-only',action='store_true')
    a=p.parse_args()
    r=capture(a.output,a.backend,a.count,a.interval_ms,a.authorize_physical_read_only)
    print(json.dumps(r));raise SystemExit(0 if r['status']=='PASS_CAPTURE_ONLY' else 1)
