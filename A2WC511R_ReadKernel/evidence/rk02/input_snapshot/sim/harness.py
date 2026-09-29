"""Persistent execution API consumed by the isolated project fake provider.

Responses are exclusively bytes shifted from executed SCI2 writes. No command
parser or ROM response implementation exists in this module.
"""
from collections import Counter
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
from pathlib import Path
from .core import CORE_PATH,CORE_SHA256,sh2e,SimulationStop
from .cpu import KernelCPU
from .memory import KernelMemory,PeripheralModel
from .sci import Schedule

# Capture model files when this module is imported, before a persistent fake
# provider begins an upload. A later edit on disk cannot relabel a live session.
MODEL_SOURCES={p.name:sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')
    if p.name in ('__init__.py','core.py','sci.py','self_echo.py','memory.py','cpu.py','fast_step.py','harness.py')}

def number(v):return int(v,0) if isinstance(v,str) else int(v)

@dataclass
class RunResult:
    status:str
    tx_bytes:bytes
    instruction_count:int
    stop_reason:str
    evidence:dict

    def as_dict(self):
        return {'status':self.status,'tx_hex':self.tx_bytes.hex(),
          'instruction_count':self.instruction_count,'stop_reason':self.stop_reason,
          'evidence':self.evidence}

class KernelSession:
    """One uploaded object and one immutable ROM fixture, persistent CPU/RAM."""
    def __init__(self,manifest_path,rom_path,rom_sha256,*,kernel_bytes=None,
                 trace_dir=None,schedule=Schedule(),peripheral_initial=None,detailed=False,
                 poison_seed=0xA5010000,optimized=True,receiver_self_echo=False):
        self.manifest_path=Path(manifest_path).resolve()
        self.manifest=json.loads(self.manifest_path.read_text())
        if 'sim' in self.manifest:sim=self.manifest['sim']
        else:
            m=self.manifest
            if m.get('artifact_class')!='TEMP_RAM_ACQUISITION_TOOL' or m.get('ECU_flash_image') is not False:
                raise SimulationStop('Not a project temporary-RAM kernel manifest')
            sim={'kernel':{'path':m['kernel_path'],'sha256':m['kernel_sha256']},
                 'load_address':m['load_address'],'entry':m['entry'],
                 'instruction_addresses':m['instruction_addresses'],'writable_ram':m['private_ram_ranges'],
                 'stack':[m['stack_low'],m['stack_high']],'inherited_sp':m['inherited_sp'],'symbols':m['symbols']}
        artifact=sim['kernel']
        path=Path(artifact['path'])
        if not path.is_absolute():path=self.manifest_path.parent/path
        compiled=path.read_bytes()
        if sha256(compiled).hexdigest()!=artifact['sha256']:
            raise SimulationStop('Compiled kernel identity mismatch')
        if kernel_bytes is not None and bytes(kernel_bytes)!=compiled:
            raise SimulationStop('Uploaded bytes differ from pinned compiled kernel')
        self.load=number(sim['load_address']);self.entry=number(sim['entry'])
        if self.load!=0xFFFF3000 or self.entry!=0xFFFF3004:
            raise SimulationStop('Only fixed project RAM upload/entry supported')
        self.executable=frozenset(number(a) for a in sim['instruction_addresses'])
        if not self.executable or self.entry not in self.executable:
            raise SimulationStop('Missing compiled instruction whitelist')
        self.ram_spans=tuple((number(a),number(b)) for a,b in sim['writable_ram'])
        self.stack=tuple(number(v) for v in sim['stack'])
        for a,b in self.ram_spans:
            if not sh2e.RAM_START<=a<b<=sh2e.RAM_END:
                raise SimulationStop('Invalid private RAM interval')
            if a<self.load+len(compiled) and b>self.load:
                raise SimulationStop('Writable RAM overlaps uploaded immutable object')
        if not any(a<=self.stack[0]<self.stack[1]<=b for a,b in self.ram_spans):
            raise SimulationStop('Private stack not in writable RAM')
        self.symbols={k:number(v) for k,v in sim['symbols'].items()}
        for k in ('rx_poll','halt_fail','halt_complete','halt_exception'):
            if self.symbols[k] not in self.executable:raise SimulationStop(f'Invalid stop symbol {k}')
        self.rom=sh2e.ROM.load(rom_path,rom_sha256)
        self.peripheral=PeripheralModel(schedule,initial=peripheral_initial,receiver_self_echo=receiver_self_echo)
        self.memory=KernelMemory(self.rom,compiled,self.load,self.executable,self.ram_spans,
            self.peripheral,detailed=detailed)
        self.peripheral.sci.record_events=detailed
        inherited=number(sim.get('inherited_sp',0xFFFFBFA0))
        self.cpu=KernelCPU(self.memory,[(min(self.executable),max(self.executable)+2)],self.stack,inherited,detailed=detailed,optimized=optimized)
        for n in range(16):self.cpu._reg(n,inherited if n==15 else (poison_seed+n*0x10203)&0xFFFFFFFF,())
        self.cpu._set_system('sr',0x302,());self.cpu.mach=0x89ABCDEF;self.cpu.macl=0x01234567
        self.cpu.pr=0xFFFFEEEE;self.cpu.call_context=[f'{self.entry:08X}']
        self.cpu.pc=self.entry
        self.started=False;self.terminal=None;self.results=[];self._sequence=0;self.pending_injection=None
        self.trace_dir=Path(trace_dir).resolve() if trace_dir else None
        if self.trace_dir:self.trace_dir.mkdir(parents=True,exist_ok=True)
        self.identity={'kernel_sha256':sha256(compiled).hexdigest(),'kernel_bytes':len(compiled),
          'rom':self.rom.identity(),'core_path':str(CORE_PATH),'core_sha256':CORE_SHA256,
          'manifest_sha256':sha256(self.manifest_path.read_bytes()).hexdigest(),
          'model_sources':MODEL_SOURCES,
          'peripheral_initial':{'sci2':{f'{a:08X}':v for a,v in self.peripheral.sci.reg.items()},
             'pccr':self.peripheral.pccr,'dmaor':self.peripheral.dmaor,'wdt_tcsr':self.peripheral.wdt_tcsr,
             'ramer':self.peripheral.ramer,'fmats':self.peripheral.fmats},
          'schedule':asdict(schedule),'optimized':optimized,
          'receiver_self_echo':receiver_self_echo,
          'model':'DECLARED_INSTRUCTION_TICK_SCI2_NOT_PHYSICAL_TIMING'}

    def _run(self,budget):
        before=self.cpu.trace.count;tx_start=len(self.peripheral.sci.tx);seen_empty=False;seen_terminal=None
        reason='INSTRUCTION_BUDGET_EXCEEDED';status='FAIL'
        try:
            for _ in range(budget):
                pc=self.cpu.pc
                if not self.cpu.pending:
                    terminals={self.symbols['halt_fail']:'KERNEL_REJECT',
                       self.symbols['halt_exception']:'KERNEL_EXCEPTION',
                       self.symbols['halt_complete']:'COMPLETE'}
                    if pc in terminals:
                        if seen_terminal==pc:
                            reason=terminals[pc];status='PASS' if reason=='COMPLETE' else 'FAIL'
                            self.terminal=reason;break
                        seen_terminal=pc
                    if pc==self.symbols['rx_poll'] and self.peripheral.sci.rx_empty and self.peripheral.sci.tx_idle:
                        if seen_empty:reason='RX_WAIT';status='PASS';break
                        seen_empty=True
                    elif not self.peripheral.sci.rx_empty or not self.peripheral.sci.tx_idle:seen_empty=False
                self.cpu.step()
            else:self.terminal=reason
        except SimulationStop as exc:
            reason='SIMULATION_FAILURE: '+str(exc);self.terminal=reason
        tx=bytes(self.peripheral.sci.tx[tx_start:])
        evidence={'sequence':self._sequence,'terminal_pc':f'{self.cpu.pc:08X}',
          'terminal_sp':f'{self.cpu.r[15]:08X}','min_sp':f'{self.cpu.min_sp:08X}',
          'memory_event_sha256':self.memory.digest.hexdigest(),
          'execution_sha256':self.cpu.execution_digest.hexdigest(),
          'SCI_schedule_sha256':self.peripheral.sci.event_digest.hexdigest(),
          'physical':False}
        if self.pending_injection:
            evidence['injection']=self.pending_injection;self.pending_injection=None
        result=RunResult(status,tx,self.cpu.trace.count-before,reason,evidence)
        if self.trace_dir:
            target=self.trace_dir/f'exchange_{self._sequence:05d}.json'
            if target.exists():raise SimulationStop('Evidence file already exists; use a new run directory')
            target.write_text(json.dumps(result.as_dict(),indent=2)+'\n')
            evidence['path']=str(target)
            evidence['sha256']=sha256(target.read_bytes()).hexdigest()
        self.results.append({'sequence':self._sequence,'status':status,'tx_bytes':len(tx),
          'tx_sha256':sha256(tx).hexdigest(),'instruction_count':result.instruction_count,'stop_reason':reason})
        self._sequence+=1
        return result

    def start(self,entry=0xFFFF3004,*,instruction_budget=200000):
        if self.started or entry!=self.entry:raise SimulationStop('Invalid/repeated kernel start')
        self.started=True
        return self._run(instruction_budget)

    def exchange(self,request:bytes,*,instruction_budget=500000):
        if not self.started:raise SimulationStop('Kernel not started')
        if self.terminal:raise SimulationStop('Kernel already terminal: '+self.terminal)
        if not self.peripheral.sci.rx_empty:raise SimulationStop('Previous receive bytes still pending')
        self.peripheral.sci.feed(bytes(request))
        return self._run(instruction_budget)

    def inject_exception(self,*,kind='NMI',instruction_budget=1000):
        """Explicit virtual hardware entry, restricted to an established RX wait.

        No claim covers pre-VBR/SP entry or rapid repeated/nested exceptions.
        The actual initialized vector and actual handler instructions are used.
        """
        if not self.started or self.terminal:raise SimulationStop('Exception outside active kernel')
        if kind!='NMI':raise SimulationStop('Only documented NMI injection contract admitted')
        if self.cpu.pending or self.cpu.pc!=self.symbols['rx_poll']:
            raise SimulationStop('Exception injection requires established non-delay RX boundary')
        if self.cpu.vbr!=number(self.manifest.get('vector_base',self.symbols.get('vector_table',0))):
            raise SimulationStop('Private vector base not established')
        c=self.cpu;m=self.memory
        saved_pc,saved_sr=c.pc,c.sr
        m.pc=c.pc;m.in_delay_slot=False
        c._reg(15,c.r[15]-4,());m.write(c.r[15],4,saved_sr)
        c._reg(15,c.r[15]-4,());m.write(c.r[15],4,saved_pc)
        target,_=m.read(c.vbr+0x2C,4)
        if target not in self.executable:raise SimulationStop('Exception vector outside compiled code')
        c._set_system('sr',c.sr|0xF0,());c.pc=target
        self.pending_injection={'kind':'EXPLICIT_VIRTUAL_NMI','saved_pc':f'{saved_pc:08X}',
            'saved_sr':f'{saved_sr:08X}','frame_bytes':8,'vector':f'{target:08X}'}
        return self._run(instruction_budget)

    def coverage(self):
        return {'schema':1,'identity':self.identity,'physical':False,
          'instruction_counts':{f'{a:08X}':n for a,n in sorted(self.cpu.pc_counts.items())},
          'edges':[{'from':f'{a:08X}','to':f'{b:08X}','count':n} for (a,b),n in sorted(self.cpu.edge_counts.items())],
          'unexecuted_instruction_addresses':[f'{a:08X}' for a in sorted(self.executable-self.cpu.pc_counts.keys())],
          'writes':[{'address':f'{a:08X}','size':s,'pc':f'{p:08X}','count':n}
                    for (a,s,p),n in sorted(self.memory.write_counts.items())],
          'read_bounds_by_pc':{f'{p:08X}':[f'{a:08X}',f'{b:08X}'] for p,(a,b) in sorted(self.memory.read_bounds.items())},
          'stack_max_bytes':self.stack[1]-self.cpu.min_sp,'terminal':self.terminal,
          'registers':{f'r{i}':f'{v:08X}' for i,v in enumerate(self.cpu.r)},
          'system':{'SR':f'{self.cpu.sr:08X}','PR':f'{self.cpu.pr:08X}','VBR':f'{self.cpu.vbr:08X}',
             'MACH':f'{self.cpu.mach:08X}','MACL':f'{self.cpu.macl:08X}'},
          'memory_event_sha256':self.memory.digest.hexdigest(),'execution_sha256':self.cpu.execution_digest.hexdigest(),
          'SCI_event_counts':dict(self.peripheral.sci.event_counts),'exchanges':self.results}
