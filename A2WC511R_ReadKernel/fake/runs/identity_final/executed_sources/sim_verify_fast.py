"""Per-instruction differential of generated audit-light and frozen step code."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from .harness import KernelSession
from .sci import Schedule

def frame(body):
    data=b'\xBE\xEF'+len(body).to_bytes(2,'big')+body
    return data+bytes([sum(data)&255])

def architecture(s):
    c=s.cpu;p=s.peripheral;u=p.sci;m=s.memory
    return (tuple(c.r),c.pc,c.sr,c.pr,c.vbr,c.mach,c.macl,c.pending,
      tuple(c.call_context),c.returned,c.min_sp,c.private_sp_established,
      tuple(c.fpu_fixture),m.digest.digest(),c.execution_digest.digest(),
      u.event_digest.digest(),u.tick,tuple(sorted(u.reg.items())),
      tuple(u.rx),bytes(u.tx),u.tx_pending,u.tx_due,u.tx_buffer,u.tx_load_due,u.rx_due,u.brr_tick,
      u.ssr_observed,u.tdr_written,u.rdr_read,p.pccr,p.dmaor,p.wdt_tcsr,
      tuple((a,b,bytes(m.ram[a-0xFFFF0000:b-0xFFFF0000]),
        bytes(m.initialized[a-0xFFFF0000:b-0xFFFF0000])) for a,b in m.private))

def verify(manifest,rom,rom_hash):
    records=[];total=0
    scenarios=[('version_read_reject',Schedule(),{},
        [frame(b'\x01'),frame(b'\x03\x00'+bytes(4)+b'\x02\x00'),frame(b'\x01')]),
       ('delayed_RX_TX',Schedule(rx_gap_ticks=5,tx_complete_ticks=25),{},
        [frame(b'\x01'),frame(b'\x03\x00'+bytes(4)+b'\x02\x00')]),
       ('shadow_guard',Schedule(),{'ramer':8},[]),
       ('MAT_guard',Schedule(),{'fmats':0xAA},[]),
       ('stale_RX_error_clear',Schedule(),{'sci2':{0xFFFFF014:0xFC,0xFFFFF015:0xA5}},
        [frame(b'\x01')]),
       ('bad_checksum',Schedule(),{},[frame(b'\x01')[:-1]+b'\0'])]
    for name,schedule,initial,requests in scenarios:
        slow=KernelSession(manifest,rom,rom_hash,schedule=schedule,peripheral_initial=initial,optimized=False)
        fast=KernelSession(manifest,rom,rom_hash,schedule=schedule,peripheral_initial=initial,optimized=True)
        original=slow.cpu.step;steps=0
        def paired_step():
            nonlocal steps
            pc=slow.cpu.pc
            original();fast.cpu.step();steps+=1
            if architecture(slow)!=architecture(fast):
                raise AssertionError(f'{name}: architectural/event mismatch after {pc:08X}, step {steps}')
        slow.cpu.step=paired_step
        results=[slow.start().as_dict()]
        for request in requests:
            fast.peripheral.sci.feed(request)
            results.append(slow.exchange(request).as_dict())
        total+=steps
        records.append({'case':name,'status':'PASS','compared_instruction_steps':steps,
            'result_statuses':[r['status'] for r in results],
            'stop_reasons':[r['stop_reason'] for r in results],
            'execution_sha256':slow.cpu.execution_digest.hexdigest(),
            'memory_event_sha256':slow.memory.digest.hexdigest()})
    return {'schema':1,'status':'PASS','classification':'EXACT_PER_STEP_DIFFERENTIAL_WITH_FROZEN_ISA',
      'kernel_sha256':slow.identity['kernel_sha256'],'core_sha256':slow.identity['core_sha256'],
      'compared_instruction_steps':total,'scenarios':records,
      'compared':['all GPR','PC','SR','PR','VBR','MACH','MACL','pending delay branch','call context',
        'private RAM and initialization bits','every data event digest','every control edge digest',
        'every SCI schedule event digest','all SCI registers and queued/transmitted bytes',
        'stack state','DMAOR/WDT/PCCR model state'],
      'optimization':'Generated from the pinned frozen CPU.step AST; only decode lookup cache, optional taint and verbose trace allocations removed. Every instruction remains executed.',
      'source_sha256':{p.name:sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}}

def main():
    a=argparse.ArgumentParser();a.add_argument('--manifest',required=True);a.add_argument('--rom',required=True)
    a.add_argument('--rom-sha256',required=True);a.add_argument('--out',required=True);v=a.parse_args()
    result=verify(v.manifest,v.rom,v.rom_sha256);out=Path(v.out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'steps':result['compared_instruction_steps'],'out':str(out)}))

if __name__=='__main__':main()
