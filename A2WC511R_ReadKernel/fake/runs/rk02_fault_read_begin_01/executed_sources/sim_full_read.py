"""Run the actual compiled kernel through two complete immutable-ROM passes."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import time
from .harness import KernelSession
from .verify_fast import frame

def run(manifest,rom,rom_hash,out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    s=KernelSession(manifest,rom,rom_hash,optimized=True)
    results=[];began=time.monotonic()
    r=s.start();assert r.status=='PASS' and r.stop_reason=='RX_WAIT' and not r.tx_bytes,r.as_dict()
    r=s.exchange(frame(b'\x01'));assert r.status=='PASS' and r.tx_bytes==frame(b'\x81A2WC511R-RK02\0'),r.as_dict()
    for pass_id in range(2):
        path=out/f'pass_{pass_id}.bin'
        with path.open('xb') as f:
            for address in range(0,0x100000,512):
                body=b'\x03'+bytes([pass_id])+address.to_bytes(4,'big')+b'\x02\x00'
                r=s.exchange(frame(body))
                expected=frame(b'\x83'+bytes([pass_id])+address.to_bytes(4,'big')+s.rom.data[address:address+512])
                assert r.status=='PASS' and r.tx_bytes==expected,(pass_id,address,r.as_dict())
                reason='COMPLETE' if pass_id==1 and address==0xFFE00 else 'RX_WAIT'
                assert r.stop_reason==reason,(pass_id,address,r.stop_reason)
                f.write(r.tx_bytes[10:-1])
                if address%0x20000==0:
                    print(json.dumps({'pass':pass_id,'address':f'{address:06X}','instructions':s.cpu.trace.count,
                         'seconds':round(time.monotonic()-began,2)}),flush=True)
        digest=sha256(path.read_bytes()).hexdigest()
        assert path.stat().st_size==0x100000 and digest==rom_hash
        results.append({'pass':pass_id,'bytes':path.stat().st_size,'path':str(path),'sha256':digest})
    assert s.peripheral.sci.reg[0xFFFFF012]==0 and s.peripheral.sci.tx_idle
    coverage=s.coverage();coverage_path=out/'coverage.json';coverage_path.write_text(json.dumps(coverage,indent=2)+'\n')
    report={'schema':1,'status':'PASS','classification':'ACTUAL_COMPILED_KERNEL_TWO_FULL_VIRTUAL_ROM_READS',
      'identity':s.identity,'passes':results,'blocks':4096,'version_responses':1,
      'instructions_executed':s.cpu.trace.count,'seconds':time.monotonic()-began,
      'coverage':{'path':str(coverage_path),'sha256':sha256(coverage_path.read_bytes()).hexdigest()},
      'terminal':s.terminal,'SCI2_SCR':s.peripheral.sci.reg[0xFFFFF012],
      'unsupported_instruction_or_MMIO':0,'physical':False,
      'limitations':['Declared finite SCI instruction-tick model, not silicon timing','No physical upload or reset/power restoration performed']}
    (out/'FULL_READ.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','report':str(out/'FULL_READ.json'),'seconds':report['seconds']}),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--rom',required=True)
    p.add_argument('--rom-sha256',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    run(a.manifest,a.rom,a.rom_sha256,a.out)
