"""Exact image, uninitialized private RAM, explicit SCI2/PFC/WDT/DMAOR surface."""
from collections import Counter
from hashlib import sha256
import struct
from .core import sh2e,SimulationStop
from .sci import SCI2,Schedule,BASE
from .self_echo import SelfEchoSCI2,EchoProfile

EMPTY=frozenset()

class PeripheralModel:
    """Instruction-stepped fixtures, never physical timing or background DMA."""
    def __init__(self, schedule=Schedule(), *, initial=None,receiver_self_echo=True,echo_profile=EchoProfile()):
        initial=dict(initial or {})
        if type(receiver_self_echo) is not bool:raise ValueError('Explicit boolean receiver loopback topology required')
        registers=initial.pop('sci2',None)
        self.sci=(SelfEchoSCI2(schedule,initial=registers,profile=echo_profile) if receiver_self_echo
            else SCI2(schedule,initial=registers))
        self.pccr=initial.pop('pccr',0)
        self.dmaor=initial.pop('dmaor',0)
        self.wdt_tcsr=initial.pop('wdt_tcsr',0x18)
        self.ramer=initial.pop('ramer',0)
        self.fmats=initial.pop('fmats',0)
        if initial:raise ValueError('Unknown peripheral fixture field')
        self.wdt_read=False;self.dma_read=False
        self.events=[]

    def read(self,address,size):
        if BASE<=address<=BASE+6:return self.sci.read(address,size)
        if (address,size)==(0xFFFFF73C,2):value=self.pccr
        elif (address,size)==(0xFFFFECB0,2):value=self.dmaor;self.dma_read=True
        elif (address,size)==(0xFFFFEC10,1):value=self.wdt_tcsr;self.wdt_read=True
        elif (address,size)==(0xFFFFEC26,2):value=self.ramer
        elif (address,size)==(0xFFFFE805,1):value=self.fmats
        else:raise SimulationStop(f'Unsupported peripheral read {address:08X}+{size}')
        self.events.append(('r',address,size,value));return value

    def write(self,address,size,value):
        if BASE<=address<=BASE+6:return self.sci.write(address,size,value)
        if (address,size)==(0xFFFFF73C,2):
            if value&~0x0155:raise SimulationStop('PCCR reserved bits written')
            self.pccr=value
        elif (address,size)==(0xFFFFECB0,2):
            if value!=0 or not self.dma_read:raise SimulationStop('Only read-then-disable DMAOR contract modeled')
            self.dmaor=0
        elif (address,size)==(0xFFFFEC10,2):
            if value!=0xA518 or not self.wdt_read:
                raise SimulationStop('Only read-then-keyed-disable WDT contract modeled')
            self.wdt_tcsr=0x18
        else:raise SimulationStop(f'Unsupported peripheral write {address:08X}+{size}')
        self.events.append(('w',address,size,value))


class KernelMemory(sh2e.Memory):
    def __init__(self,rom,kernel,load,executable,ram_spans,peripheral,*,detailed=False):
        super().__init__(rom)
        self.kernel=bytes(kernel);self.load=load
        self.executable=frozenset(executable);self.private=tuple(ram_spans)
        self.peripheral=peripheral;self.detailed=detailed
        self.initialize(load,kernel)
        self.protected=[(load,load+len(kernel))]
        self.write_allowlist=list(ram_spans)
        self.digest=sha256();self.access_counts=Counter();self.write_counts=Counter()
        self.read_bounds={};self.total_events=0

    def _event(self,mode,address,size,value,sources=(),address_sources=()):
        pc=self.pc if self.pc is not None else 0xFFFFFFFF
        value&=(1<<(8*size))-1
        self.digest.update(struct.pack('>cIBII',mode.encode(),address,size,value,pc))
        self.total_events+=1;self.access_counts[(mode,pc,size)]+=1
        if mode=='w':self.write_counts[(address,size,pc)]+=1
        else:
            lo,hi=self.read_bounds.get(pc,(address,address+size))
            self.read_bounds[pc]=(min(lo,address),max(hi,address+size))
        if self.detailed:
            self.events.append({'mode':mode,'address':f'{address:08X}','size':size,
                'value':f'{value:08X}','pc':f'{pc:08X}','delay_slot':self.in_delay_slot})

    def read(self,address,size,address_sources=(),fetch=False):
        self._check(address,size)
        if fetch:
            if size!=2 or address not in self.executable:
                raise SimulationStop(f'Execution outside compiled instruction whitelist: {address:08X}')
            offset=address-self.load
            if not 0<=offset<offset+2<=len(self.kernel):raise SimulationStop('Instruction outside exact uploaded object')
            return int.from_bytes(self.kernel[offset:offset+2],'big'),EMPTY
        if 0<=address<address+size<=sh2e.ROM_SIZE:
            value=int.from_bytes(self.rom.data[address:address+size],'big')
        elif self.load<=address<address+size<=self.load+len(self.kernel):
            offset=address-self.load;value=int.from_bytes(self.kernel[offset:offset+size],'big')
        elif any(a<=address<address+size<=b for a,b in self.private):
            offset=address-sh2e.RAM_START
            if not all(self.initialized[offset:offset+size]):
                raise SimulationStop(f'Uninitialized private RAM read {address:08X}+{size}')
            value=int.from_bytes(self.ram[offset:offset+size],'big')
        elif address>=0xFFFFC000:value=self.peripheral.read(address,size)
        else:raise SimulationStop(f'Undeclared memory read {address:08X}+{size}')
        self._event('r',address,size,value)
        return value,EMPTY

    def write(self,address,size,value,sources=(),address_sources=()):
        self._check(address,size)
        if 0<=address<sh2e.ROM_SIZE:raise SimulationStop(f'Read-only flash write {address:08X}')
        if self.load<=address<self.load+len(self.kernel):raise SimulationStop('Uploaded code/data write prohibited')
        value&=(1<<(8*size))-1
        if any(a<=address<address+size<=b for a,b in self.private):
            offset=address-sh2e.RAM_START
            self.ram[offset:offset+size]=value.to_bytes(size,'big')
            self.initialized[offset:offset+size]=b'\x01'*size
        elif address>=0xFFFFC000:self.peripheral.write(address,size,value)
        else:raise SimulationStop(f'Undeclared memory write {address:08X}+{size}')
        self._event('w',address,size,value)
