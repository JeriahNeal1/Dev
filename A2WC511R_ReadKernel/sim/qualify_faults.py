"""Actual compiled negative paths, explicit peripheral faults and seeded fuzz.

Fault fixtures are deliberately separate from whole-ROM acquisition evidence.
No expected frame is ever fed into the SCI transmitter.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import random
import time
from .harness import KernelSession
from .core import SimulationStop
from .sci import Schedule,SSR,SCR,TDRE,TEND
from .verify_fast import frame

def read_body(address=0,pass_id=0,length=512):
    return b'\x03'+bytes([pass_id])+address.to_bytes(4,'big')+length.to_bytes(2,'big')

class Suite:
    def __init__(self,manifest,rom,rom_hash,out):
        self.manifest,self.rom,self.rom_hash=manifest,rom,rom_hash
        self.out=Path(out).resolve();self.out.mkdir(parents=True,exist_ok=False)
        self.records=[];self.counts=Counter();self.edges=Counter();self.writes=Counter()
        self.access=Counter();self.read_bounds={};self.max_stack=0;self.unsupported=[];self.mmio=set()
    def session(self,**kw):return KernelSession(self.manifest,self.rom,self.rom_hash,**kw)
    def record(self,name,s,result,expected,*,kind='COMPILED_NEGATIVE',injection=None,allow_tx=False):
        assert result.stop_reason==expected,(name,result.as_dict())
        if expected=='KERNEL_REJECT':
            assert result.status=='FAIL' and s.peripheral.sci.reg[SCR]==0
            if not allow_tx:assert not result.tx_bytes,(name,'unexpected output',result.tx_bytes.hex())
        if expected in ('RX_WAIT','COMPLETE'):assert result.status=='PASS'
        assert not result.stop_reason.startswith('SIMULATION_FAILURE'),(name,result.as_dict())
        cov=s.coverage();self.counts.update(s.cpu.pc_counts);self.edges.update(s.cpu.edge_counts)
        self.writes.update(s.memory.write_counts);self.access.update(s.memory.access_counts)
        self.max_stack=max(self.max_stack,cov['stack_max_bytes'])
        for pc,(a,b) in s.memory.read_bounds.items():
            old=self.read_bounds.get(pc,(a,b));self.read_bounds[pc]=(min(a,old[0]),max(b,old[1]))
            if a>=0xFFFFC000:self.mmio.add(('r',a,b-a,pc))
        for a,z,pc in s.memory.write_counts:
            if a>=0xFFFFC000:self.mmio.add(('w',a,z,pc))
        self.records.append({'case':name,'status':'PASS','classification':kind,
          'expected_kernel_outcome':expected,'observed_status':result.status,
          'observed_reason':result.stop_reason,'transmitted_bytes':len(result.tx_bytes),
          'transmitted_sha256':sha256(result.tx_bytes).hexdigest(),'instructions':s.cpu.trace.count,
          'memory_event_sha256':s.memory.digest.hexdigest(),
          'execution_sha256':s.cpu.execution_digest.hexdigest(),
          'stack_max_bytes':cov['stack_max_bytes'],'injection':injection,
          'result_evidence':result.evidence})
    def ready(self,**kw):
        s=self.session(**kw);r=s.start();assert r.status=='PASS' and not r.tx_bytes,r.as_dict()
        return s
    def identified(self,**kw):
        s=self.ready(**kw);r=s.exchange(frame(b'\1'))
        assert r.tx_bytes==frame(b'\x81A2WC511R-RK02\0') and r.status=='PASS',r.as_dict()
        return s
    def reject(self,name,payload,*,identified=True):
        s=self.identified() if identified else self.ready()
        r=s.exchange(payload);self.record(name,s,r,'KERNEL_REJECT')
    def run(self):
        began=time.monotonic()
        # Guards exercise actual compiled reads and both directions.
        for field,value in [('ramer',8),('fmats',0xAA)]:
            s=self.session(peripheral_initial={field:value});r=s.start()
            self.record(field+'_rejected',s,r,'KERNEL_REJECT',injection={field:value})
        for field,address,size,value in [('DMAOR',0xFFFFECB0,2,1),('WDT',0xFFFFEC10,1,0x38)]:
            s=self.session();original=s.peripheral.read
            def stuck(a,z,original=original,address=address,size=size,value=value):
                observed=original(a,z)
                return value if (a,z)==(address,size) else observed
            s.peripheral.read=stuck;r=s.start()
            self.record(field+'_disable_readback_stuck',s,r,'KERNEL_REJECT',
                injection={'kind':'explicit stuck peripheral readback','address':f'{address:08X}','value':value})
        s=self.ready(peripheral_initial={'sci2':{SSR:0xFC,0xFFFFF015:0xA5},'pccr':0xFFFF,'dmaor':7,'wdt_tcsr':0xF8})
        r=s.exchange(frame(b'\1'));assert r.tx_bytes==frame(b'\x81A2WC511R-RK02\0')
        self.record('stale_RX_errors_and_nonreset_peripherals',s,r,'RX_WAIT',kind='COMPILED_POSITIVE',
            injection=s.identity['peripheral_initial'],allow_tx=True)
        for symbol in ('guard_low','guard_high'):
            s=self.session();original=s.cpu.step;done=False
            def corrupt_guard(s=s,original=original,symbol=symbol):
                nonlocal done
                if not done and s.cpu.pc==s.symbols['check_guards']:
                    off=s.symbols[symbol]-0xFFFF0000;s.memory.ram[off:off+4]=b'\xA5'*4;done=True
                original()
            s.cpu.step=corrupt_guard;r=s.start()
            self.record(symbol+'_corruption',s,r,'KERNEL_REJECT',
                injection={'kind':'explicit RAM bit fault before guard check','address':f'{s.symbols[symbol]:08X}','value':'A5A5A5A5'})
        for bits in (8,16,32,56):
            s=self.ready();s.peripheral.sci.inject_error(bits);r=s.exchange(b'')
            self.record(f'SCI_error_{bits:02X}',s,r,'KERNEL_REJECT',injection={'SSR_error_bits':bits})
        for name,payload,identified in [
          ('bad_magic_first',b'\0\xEF\0\1\1\0',True),
          ('bad_magic_second',b'\xBE\0\0\1\1\0',True),
          ('length_high_nonzero',b'\xBE\xEF\1\1\1\0',True),
          ('length_zero',frame(b''),True),('length_two',frame(b'\1\0'),True),
          ('identity_wrong_shape',frame(b'\1'+bytes(7)),False),
          ('raw_wrong_shape',frame(b'\3'),True),
          ('raw_before_identity',frame(read_body()),False),
          ('repeated_identity',frame(b'\1'),True),
          ('bad_add8',frame(read_body())[:-1]+bytes([frame(read_body())[-1]^1]),True),
          ('unknown_20',frame(b'\x20'),True),('wrong_pass',frame(read_body(pass_id=1)),True),
          ('unaligned',frame(read_body(address=1)),True),('out_of_order',frame(read_body(address=512)),True),
          ('past_ROM',frame(read_body(address=0x100000)),True),('arbitrary_RAM',frame(read_body(address=0xFFFF3700)),True),
          ('length_high_wrong',frame(read_body(length=256)),True),('length_low_wrong',frame(read_body(length=513)),True)]:
            self.reject(name,payload,identified=identified)
        s=self.identified();r=s.exchange(frame(read_body()));assert r.status=='PASS'
        r=s.exchange(frame(read_body()));self.record('duplicate_block',s,r,'KERNEL_REJECT')
        # Partial frames are incomplete pending state, never a success response.
        packet=frame(read_body())
        for cut in range(len(packet)):
            s=self.identified();r=s.exchange(packet[:cut]);assert not r.tx_bytes
            self.record(f'partial_frame_{cut}',s,r,'RX_WAIT',kind='INCOMPLETE_REQUEST_NO_RESPONSE',
                injection={'prefix_bytes':cut,'host_deadline_required':True})
        # All invalid opcodes and deterministic mutations use the actual parser.
        for command in range(256):
            if command in (1,3):continue
            self.reject(f'command_{command:02X}',frame(bytes([command])))
        rng=random.Random(0x51170001)
        for n in range(128):
            address=rng.randrange(1,1<<32);length=rng.randrange(1<<16);pass_id=rng.randrange(256)
            self.reject(f'seeded_fields_{n}',frame(read_body(address,pass_id,length)))
        for n in range(len(packet)*8):
            data=bytearray(packet);data[n//8]^=1<<(n%8)
            self.reject(f'one_bit_wire_mutation_{n}',bytes(data))
        # Model delayed RX and real CPU TX polling, without a fake response.
        s=self.identified(schedule=Schedule(rx_gap_ticks=17,tx_complete_ticks=25))
        r=s.exchange(frame(read_body()));assert r.tx_bytes==frame(b'\x83\0'+bytes(4)+s.rom.data[:512])
        self.record('delayed_RX_TX_polling',s,r,'RX_WAIT',kind='COMPILED_POSITIVE',allow_tx=True)
        s=self.ready();s.peripheral.sci.reg[SSR]&=~TDRE
        r=s.exchange(frame(b'\1'))
        self.record('TDRE_stuck_zero_timeout',s,r,'KERNEL_REJECT',
            injection={'kind':'explicit peripheral fault','SSR.TDRE':0,'tx_pending':False})
        # A transmission that never completes is aborted by the documented TE0.
        s=self.ready(schedule=Schedule(tx_complete_ticks=10_000_000));r=s.exchange(frame(b'\1'))
        self.record('pending_TX_timeout_abort',s,r,'KERNEL_REJECT',
            injection={'tx_complete_ticks':10_000_000,'pending_character_aborted':True})
        assert s.peripheral.sci.event_counts['tx_aborted_by_TE0']==1 and not s.peripheral.sci.tx
        # Bounded terminal-state fixture. This is NOT a claim to have read prior
        # ROM blocks. Whole real passes are independently exercised by full_read.
        for fault in (False,True):
            s=self.identified();s.cpu._reg(8,0xFFE00,());s.cpu._reg(9,1,())
            if fault:
                original=s.cpu.step
                def stuck_tend(s=s,original=original):
                    if s.cpu.pc==s.symbols['tx_drain']:s.peripheral.sci.reg[SSR]&=~TEND
                    original()
                s.cpu.step=stuck_tend
            r=s.exchange(frame(read_body(0xFFE00,1)))
            expected='KERNEL_REJECT' if fault else 'COMPLETE'
            assert r.tx_bytes==frame(b'\x83\1'+(0xFFE00).to_bytes(4,'big')+s.rom.data[0xFFE00:])
            self.record('terminal_TEND_timeout' if fault else 'terminal_complete_fixture',s,r,expected,
              injection={'kind':'EXPLICIT_BOUNDED_STATE_FIXTURE_NOT_FULL_PASS','r8':'000FFE00','r9':1,
                 'stuck_TEND':fault},allow_tx=True)
        s=self.ready();r=s.inject_exception()
        assert r.stop_reason=='KERNEL_EXCEPTION' and not r.tx_bytes and s.peripheral.sci.reg[SCR]==0
        assert s.stack[1]-s.cpu.min_sp==8
        self.record('NMI_established_RX_boundary',s,r,'KERNEL_EXCEPTION',kind='EXPLICIT_HARDWARE_ENTRY_FIXTURE',
          injection=r.evidence['injection'])
        # API/closed-world negative controls reject without admitting a new path.
        controls=[]
        def rejected(name,operation):
            try:operation()
            except (SimulationStop,ValueError) as exc:controls.append({'case':name,'status':'PASS','expected_failure':str(exc)})
            else:raise AssertionError(name+' was admitted')
        s=self.session()
        rejected('exception_before_start',lambda:s.inject_exception())
        rejected('wrong_entry',lambda:s.start(0xFFFF3000))
        s=self.ready()
        rejected('SP_below_private',lambda:s.cpu._reg(15,s.stack[0]-4,()))
        rejected('SP_above_private',lambda:s.cpu._reg(15,s.stack[1]+4,()))
        rejected('SP_unaligned',lambda:s.cpu._reg(15,s.stack[1]-1,()))
        rejected('outside_compiled_code',lambda:s.memory.read(0xFFFF3000,2,fetch=True))
        rejected('unknown_MMIO',lambda:s.memory.read(0xFFFFF000,1))
        rejected('ROM_write',lambda:s.memory.write(0,1,0))
        rejected('kernel_code_write',lambda:s.memory.write(s.entry,2,9))
        rejected('flash_control_write',lambda:s.memory.write(0xFFFFE804,1,0x5A))
        rejected('outside_private_RAM',lambda:s.memory.write(s.stack[1]+8,1,0))
        rejected('upload_hash_mismatch',lambda:self.session(kernel_bytes=b'\0'*1808))
        s.cpu.pending=(s.cpu.pc+4,None)
        rejected('exception_delay_slot',lambda:s.inject_exception())
        s.cpu.pending=None;s.cpu.vbr=0
        rejected('exception_inherited_VBR',lambda:s.inject_exception())
        self.report(controls,time.monotonic()-began)
    def report(self,controls,seconds):
        m=json.loads(Path(self.manifest).read_text());ins=set(m['instruction_addresses'])
        branches=[]
        for i in m['instructions']:
            op=i['opcode'];pc=i['address']
            if op&0xFF00 not in (0x8900,0x8B00):continue
            disp=op&255;disp=disp-256 if disp&128 else disp
            targets=(pc+2,(pc+4+2*disp)&0xFFFFFFFF)
            branches.append({'pc':f'{pc:08X}','opcode':f'{op:04X}','successors':[
                {'pc':f'{a:08X}','count':self.edges[(pc,a)]} for a in targets]})
        cov={'schema':1,'kernel_sha256':m['kernel_sha256'],
          'instruction_counts':{f'{a:08X}':n for a,n in sorted(self.counts.items())},
          'unexecuted_instruction_addresses':[f'{a:08X}' for a in sorted(ins-self.counts.keys())],
          'edges':[{'from':f'{a:08X}','to':f'{b:08X}','count':n} for (a,b),n in sorted(self.edges.items())],
          'branches':branches,
          'writes':[{'address':f'{a:08X}','size':z,'pc':f'{pc:08X}','count':n} for (a,z,pc),n in sorted(self.writes.items())],
          'read_bounds_by_pc':{f'{p:08X}':[f'{a:08X}',f'{b:08X}'] for p,(a,b) in sorted(self.read_bounds.items())},
          'data_access_counts':[{'mode':mode,'pc':f'{pc:08X}','size':z,'count':n} for (mode,pc,z),n in sorted(self.access.items())],
          'MMIO_accesses':[{'mode':mode,'address':f'{a:08X}','size':z,'pc':f'{pc:08X}'} for mode,a,z,pc in sorted(self.mmio)],
          'stack_max_bytes':self.max_stack,'unsupported_instructions_or_MMIO_on_executed_paths':0}
        cp=self.out/'coverage.json';cp.write_text(json.dumps(cov,indent=2)+'\n')
        report={'schema':1,'status':'PASS','kernel_sha256':m['kernel_sha256'],'physical':False,
          'classification':'COMPILED_INSTRUCTION_NEGATIVE_AND_BOUNDED_FAULT_FIXTURES',
          'cases':self.records,'closed_world_negative_controls':controls,'seconds':seconds,
          'case_count':len(self.records),'negative_control_count':len(controls),
          'coverage':{'path':str(cp),'sha256':sha256(cp.read_bytes()).hexdigest()},
          'fuzz_seed':'51170001','unsupported_executed_paths':[],
          'model_sources':self.session().identity['model_sources'],
          'limitations':['NMI tested only at established non-delay RX boundary; hardware entry itself explicitly injected',
            'No prefix-before-private-SP/VBR or rapid repeated/nested NMI guarantee',
            'Virtual SCI instruction ticks are not silicon cycles, baud or electrical timing',
            'Terminal-state fixtures do not replace independent two-full-pass execution']}
        path=self.out/'FAULTS.json';path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'status':'PASS','cases':len(self.records),'controls':len(controls),
             'missing_instructions':cov['unexecuted_instruction_addresses'],'report':str(path)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--rom',required=True)
    p.add_argument('--rom-sha256',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    Suite(a.manifest,a.rom,a.rom_sha256,a.out).run()

