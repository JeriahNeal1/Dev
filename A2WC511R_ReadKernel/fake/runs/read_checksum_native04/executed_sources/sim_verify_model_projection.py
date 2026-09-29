"""Prove the saved full-run scheduling profile projects to the final SCI model.

All old files are read-only. The proof is restricted to tx_load=tx_complete=1,
not arbitrary deferred or physical UART schedules.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import types
from .harness import KernelSession
from .verify_fast import frame

def state(s):
    c=s.cpu;m=s.memory;u=s.peripheral.sci
    return (tuple(c.r),c.pc,c.sr,c.pr,c.vbr,c.mach,c.macl,c.pending,tuple(c.call_context),
      c.returned,c.min_sp,m.digest.digest(),c.execution_digest.digest(),
      u.tick,tuple(sorted(u.reg.items())),tuple(u.rx),bytes(u.tx),u.tx_pending,u.tx_due,
      u.rx_due,u.brr_tick,u.ssr_observed,u.tdr_written,u.rdr_read,
      tuple((bytes(m.ram[a-0xFFFF0000:b-0xFFFF0000]),bytes(m.initialized[a-0xFFFF0000:b-0xFFFF0000]))
         for a,b in m.private))

def verify(manifest,rom,rom_hash,saved_paths,out):
    records=[]
    for n,path in enumerate(saved_paths):
        path=Path(path).resolve();name=f'sim._saved_projection_{n}';module=types.ModuleType(name)
        module.__package__='sim';sys.modules[name]=module
        exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
        for scenario in ('ordinary_then_reject','terminal_complete'):
            old=KernelSession(manifest,rom,rom_hash);new=KernelSession(manifest,rom,rom_hash)
            old.peripheral.sci=module.SCI2(module.Schedule());original=old.cpu.step;steps=0
            def pair():
                nonlocal steps
                pc=old.cpu.pc;original();new.cpu.step();steps+=1
                assert state(old)==state(new),(str(path),scenario,steps,f'{pc:08X}')
                assert new.peripheral.sci.tx_buffer is None and new.peripheral.sci.tx_pending is None
            old.cpu.step=pair
            r=old.start();assert r.status=='PASS'
            def exchange(body):
                request=frame(body);new.peripheral.sci.feed(request);return old.exchange(request)
            r=exchange(b'\1');assert r.status=='PASS'
            if scenario=='ordinary_then_reject':
                for address in (0,512):
                    r=exchange(b'\3\0'+address.to_bytes(4,'big')+b'\2\0');assert r.status=='PASS'
                r=exchange(b'\1');assert r.stop_reason=='KERNEL_REJECT'
            else:
                for s in (old,new):s.cpu._reg(8,0xFFE00,());s.cpu._reg(9,1,())
                r=exchange(b'\3\1'+(0xFFE00).to_bytes(4,'big')+b'\2\0');assert r.stop_reason=='COMPLETE'
            records.append({'status':'PASS','saved_SCI_source':str(path),'saved_SCI_sha256':sha256(path.read_bytes()).hexdigest(),
                'scenario':scenario,'instruction_steps_compared':steps,
                'memory_event_sha256':old.memory.digest.hexdigest(),'execution_sha256':old.cpu.execution_digest.hexdigest(),
                'transmitted_sha256':sha256(old.peripheral.sci.tx).hexdigest()})
    result={'schema':1,'status':'PASS','classification':'SCOPED_OBSERVATIONAL_REFINEMENT_OF_SAVED_FULL_RUN_MODELS',
      'kernel_sha256':old.identity['kernel_sha256'],'final_model_sources':old.identity['model_sources'],
      'assumptions':['tx_load_ticks=tx_complete_ticks=rx_gap_ticks=1, as in saved full-run profiles',
        'CPU executes one instruction then one peripheral tick; no asynchronous fault injected into a half instruction',
        'Kernel has at most one MMIO transaction per instruction; TX actions happen only through actual TDR/SSR stores',
        'No source mutation relabeling: original full runs retain their saved source hashes'],
      'inductive_argument':[
        'At an instruction boundary both TX stages are empty under the collapsed one-tick profile.',
        'A TDR store changes the same TDR byte and tdr_written flag in both versions.',
        'A qualified SSR.TDRE-clear changes the same visible SSR bits; the old model holds a pending character and the new model holds a submitted buffer byte.',
        'The immediately following peripheral tick completes that byte in both versions. The new model performs TDR-to-TSR load and completion in that one declared abstract tick.',
        'Both append the same byte, set TDRE/TEND, and are empty again before the next instruction. Non-TX transitions and RX scheduling are unchanged.',
        'Therefore every CPU-visible value, memory event, control edge and transmitted byte is identical by induction for arbitrary request/ROM bytes under this profile.',
        'The new internal shift-register-loaded event is intentionally additional evidence; its internal scheduling digest is not asserted equal.',
        'Old-model TE0-while-pending unsupported path is unreachable at instruction boundaries in this collapsed profile. Explicit delayed-pipeline abort tests use the new model.'
      ],'concrete_per_step_crosschecks':records,
      'not_claimed':['Cycle/baud/electrical timing','Equivalence for arbitrary delayed schedules',
        'That saved full runs used the newer model','That the terminal-state fixture exercised preceding ROM blocks']}
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS','compared_steps':sum(x['instruction_steps_compared'] for x in records),'out':str(p)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--rom',required=True)
    p.add_argument('--rom-sha256',required=True);p.add_argument('--saved-sci',action='append',required=True)
    p.add_argument('--out',required=True);a=p.parse_args()
    verify(a.manifest,a.rom,a.rom_sha256,a.saved_sci,a.out)
