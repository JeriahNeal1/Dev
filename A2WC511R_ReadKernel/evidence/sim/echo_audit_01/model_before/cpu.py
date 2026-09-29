"""Project subclass: frozen ISA semantics, strict stack and aggregate coverage."""
from collections import Counter
from hashlib import sha256
import struct
from .core import sh2e,SimulationStop
from .fast_step import frozen_step_without_verbose_audit

class TraceSink:
    def __init__(self, detailed=False):self.rows=[];self.count=0;self.detailed=detailed
    def append(self,row):
        self.count+=1
        if self.detailed:self.rows.append(row)
    def __len__(self):return self.count
    def __bool__(self):return bool(self.count)

class KernelCPU(sh2e.CPU):
    def __init__(self,memory,execution_ranges,stack_bounds,inherited_sp,*,detailed=False,optimized=False):
        self.inherited_sp=inherited_sp;self.private_sp_established=False
        self.min_sp=stack_bounds[1];self.vbr=0;self.fpu_fixture=tuple(0x7FC10000+i for i in range(16))
        super().__init__(memory,execution_ranges,stack_bounds)
        self.trace=TraceSink(detailed);self.pc_counts=Counter();self.edge_counts=Counter()
        self.execution_digest=sha256();self.track_control_sources=False
        self.optimized=optimized
        self._decode_cache={}
        for pc in memory.executable:
            op,_=memory.read(pc,2,fetch=True)
            self._decode_cache[op]=next((x for x in sh2e.OPCODES if op&x.mask==x.value),None)

    def _reg(self,number,value,sources):
        value&=sh2e.MASK32
        if number==15:
            lo,hi=self.stack_bounds
            if value%4:raise SimulationStop(f'Unaligned SP {value:08X}')
            if not lo<=value<=hi:
                if self.private_sp_established or value!=self.inherited_sp:
                    raise SimulationStop(f'SP outside private stack {value:08X}')
            else:
                self.private_sp_established=True;self.min_sp=min(self.min_sp,value)
        self.r[number]=value;self.sources[number]=set()

    def _t(self,value,sources):self.t=int(bool(value));self.t_sources=set()

    def _set_system(self,name,value,sources):
        # The project does not rely on the original optional source-taint data.
        return super()._set_system(name,value,())

    def step(self):
        pc=self.pc
        op,_=self.memory.read(pc,2,fetch=True)
        if op&0xF0FF in (0x002A,0x402A,0x402E,0x4019,0x4029) or op&0xFF00==0xCA00:
            self._local_step(op)
        elif self.optimized:frozen_step_without_verbose_audit(self)
        else:super().step()
        self.pc_counts[pc]+=1;self.edge_counts[(pc,self.pc)]+=1
        self.execution_digest.update(struct.pack('>II',pc,self.pc))
        self.memory.peripheral.sci.advance()

    def _local_step(self,op):
        pc=self.pc;slot=self.pending;n=(op>>8)&15;form=op&0xF0FF
        self._reg(15,self.r[15],())
        self.memory.pc=pc;self.memory.in_delay_slot=bool(slot)
        before_pr=self.pr
        if form==0x002A:name='sts_pr_reg';self._reg(n,self.pr,())
        elif form==0x402A:name='lds_pr_reg';self.pr=self.r[n]
        elif form==0x402E:name='ldc_vbr_reg';self.vbr=self.r[n]
        elif form in (0x4019,0x4029):
            name='shlr8' if form==0x4019 else 'shlr16'
            self._reg(n,self.r[n]>>(8 if form==0x4019 else 16),())
        elif op&0xFF00==0xCA00:name='xor_imm';self._reg(0,self.r[0]^(op&255),())
        else:raise AssertionError('not a local form')
        self.opcodes_seen.add(name)
        self.trace.append({'pc':f'{pc:08X}','opcode':f'{op:04X}','instruction':name,
          'delay_slot':bool(slot),'pr_before':f'{before_pr:08X}','pr_after':f'{self.pr:08X}',
          'vbr':f'{self.vbr:08X}','sr':f'{self.sr:08X}'})
        self.pc=pc+2;self.pending=None
        if slot:
            self.pc,action=slot
            if action=='call':self.call_context.append(f'{self.pc:08X}')
            elif action=='return':
                if not self.call_context:raise SimulationStop('Return without call context')
                self.call_context.pop();self.returned=not self.call_context
