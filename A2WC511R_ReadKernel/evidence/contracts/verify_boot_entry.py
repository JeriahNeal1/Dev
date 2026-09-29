"""Bounded exact-stock IRQ mask, GPIO and boot-entry contracts; no hardware."""
import sys
sys.dont_write_bytecode=True
import json,gzip,hashlib
from pathlib import Path
from verify_kwp_contract import CPU as BaseCPU,sh,common,ext
HERE=Path(__file__).resolve().parent

class CPU(BaseCPU):
    def step(self):
        op,_=self.memory.read(self.pc,2,fetch=True)
        if op&0xF0FF==0x402E:return ext.kernel.boot.BootCPU.extended_step(self,op)
        return super().step()

class GPIO(sh.Memory):
    def __init__(self,rom):super().__init__(rom);self.io={};self.mmio=[]
    def write(self,address,size,value,sources=(),address_sources=()):
        if 0xFFFFF720<=address<0xFFFFF780 and size==2:
            self.io[address]=value&65535
            self.mmio.append({'pc':f'{self.pc:08X}','address':f'{address:08X}','size':size,'value':f'{value&65535:04X}'})
            return
        return super().write(address,size,value,sources,address_sources)

def main():
    rom=sh.ROM.load(common.STOCK,sh.STOCK_SHA256);traces=[];rows=[]
    def run(entry,ranges,registers=None,sr=0x301,initialize=(),allowed=(),memory=None):
        m=memory or sh.Memory(rom)
        for a,b in initialize:m.initialize(a,b)
        h=sh.FunctionHarness(m,ranges);h.cpu=CPU(m,ranges,h.stack)
        h.cpu.track_control_sources=False
        r=h.run(entry,registers=registers,system_registers={'sr':sr},allowed_writes=allowed,max_steps=500)
        traces.append({'entry':f'{entry:08X}','sr_input':f'{sr:08X}','instructions':h.cpu.trace,'memory':m.events})
        return h,r
    for mask in range(1,16):
        sr=0x301|(mask<<4)
        h,r=run(0x2088,[(0x2088,0x209C)],{4:0xFFFF6000,5:0xE0},sr,allowed=[(0xFFFF6000,0xFFFF6004)])
        assert int.from_bytes(h.memory.ram[0x6000:0x6004],'big')==mask<<4
        assert h.cpu.sr&0xF0==max(mask<<4,0xE0)
        h2,r2=run(0x2098,[(0x2088,0x209C)],{4:mask<<4},h.cpu.sr)
        assert h2.cpu.sr==mask<<4
        h3,r3=run(0x3AF4,[(0x3AF4,0x3B02),(0x3B04,0x3B08)],{4:0x10},h2.cpu.sr)
        assert h3.cpu.r[0]==mask<<4
        h4,r4=run(0x3B08,[(0x3B08,0x3B20)],{4:h3.cpu.r[0]},h3.cpu.sr)
        assert h4.cpu.sr==mask<<4
        assert len(h4.cpu.trace)==4
        assert not any(e['mode']=='r' for e in h4.memory.events)
        rows.append({'accepted_irq_level':mask,'saved_mask':f'{mask<<4:02X}','3B08_steps':r4['steps'],'scheduler_or_descriptor_access':False})
    # Deliberately do not initialize the scheduler descriptor: a mask0 call is
    # outside the IRQ contract and must visibly fail on that external read.
    negative=None
    try:run(0x3B08,[(0x3B08,0x3B20)],{4:0},0)
    except sh.SimulationStop as e:
        negative=str(e)
        assert 'FFFF12C8' in negative.upper(),negative
    assert negative
    # Actual prologue restores the interrupt SR before any device handler.
    prologue=[]
    for mask in range(1,16):
        m=sh.Memory(rom);m.initialize(0xFFFF12B0,bytes(0x20))
        m.initialize(0xFFFF12C0,(0xF0).to_bytes(4,'big'))
        h=sh.FunctionHarness(m,[(0x340C,0x341E)])
        c=CPU(m,h.cpu.execution_ranges,h.stack);c.pc=0x340C;c.r[15]=h.stack[1]
        c._set_system('sr',0x301|(mask<<4),{'accepted_interrupt_fixture'})
        for _ in range(9):c.step()
        assert c.pc==0x341E and c.sr==0x301|(mask<<4)
        traces.append({'entry':'0000340C','instructions':c.trace,'memory':m.events})
        prologue.append({'level':mask,'restored_sr':f'{c.sr:08X}','instructions':len(c.trace)})
    g=GPIO(rom);h,r=run(0x1B56,[(0x1B56,0x1BE8)],sr=0xF0,memory=g)
    assert g.io[0xFFFFF746]==0x3CFF and not(g.io[0xFFFFF746]&0x0100)
    assert len(g.mmio)==31,len(g.mmio)
    fragments=[]
    for name,start,end,ranges,initial in [
        ('application_to_boot',0x471AE,0x125C,[(0x471AE,0x471C2),(0x40,0x50)],{}),
        ('loader_mask_and_vbr',0x12A8,0x12B6,[(0x12A8,0x12B6)],{}),
        ('post_ACK_uploaded_entry',0x1992,0xFFFF3004,[(0x1992,0x19A2),(0x1C28,0x1C2E)],{})]:
        m=sh.Memory(rom);m.initialize(0xFFFFBFA0,bytes(8));m.initialize(0xFFFFBFC7,b'\x00')
        c=CPU(m,ranges,(0xFFFFBBA0,0xFFFFBFB0));c.pc=start;c.r[15]=0xFFFFBFA0
        c.call_context=[name];c._set_system('sr',0x301,{'fragment_fixture'})
        for _ in range(50):
            c.step()
            if c.pc==end and not c.pending:break
        assert c.pc==end and not c.pending
        if name=='loader_mask_and_vbr':assert c.vbr==0x1F44
        elif name=='application_to_boot':assert c.r[15]==0xFFFFBFA0
        else:assert c.r[15]==0xFFFFBFA0 and c.sr==0x301
        if name!='post_ACK_uploaded_entry':assert c.sr&0xF0==0xF0
        fragments.append({'name':name,'start':f'{start:08X}','end':f'{end:08X}','instructions':len(c.trace),'sr':f'{c.sr:08X}','sp':f'{c.r[15]:08X}','vbr':f'{getattr(c,'vbr',0):08X}'})
        traces.append({'entry':f'{start:08X}','instructions':c.trace,'memory':m.events})
    assert int.from_bytes(rom.data[0xFFF94:0xFFF98],'big')==0x31FC
    assert int.from_bytes(rom.data[0xF6D0:0xF6D4],'big')==0xFFC50
    packed=gzip.compress(json.dumps(traces,sort_keys=True,separators=(',',':')).encode(),mtime=0)
    (HERE/'BOOT_ENTRY_TRACE.json.gz').write_bytes(packed)
    report={'schema':1,'status':'PASS_SCOPED_IRQ_AND_BOOT_ENTRY','inputs':[common.pin(common.STOCK),common.pin(Path(__file__)),common.pin(HERE/'verify_kwp_contract.py'),common.pin(HERE/'verify_oem_contracts.py')],
      'admitted_caller':'SCI2 RXI vector209 accepted with SR.I1..15; VBRFFC50 + vector offset344 = FFF94 ->31FC',
      'mask_contract_cases':rows,'interrupt_prologue_cases':prologue,'mask0_negative':negative,'boot_gpio_writes':g.mmio,'boot_gpio_instructions':r['steps'],'fragments':fragments,
      'trace':common.pin(HERE/'BOOT_ENTRY_TRACE.json.gz'),
      'limits':['Separate exact instruction fragments; not a reset-to-entry execution.','No UART waveform, physical clock, asynchronous nested interrupt or board GPIO semantics modeled.','No scheduler domain claimed for an artificial mask0 call.','No ROM other than the pinned stock identity admitted.'], 'physical_operations':0}
    (HERE/'BOOT_ENTRY_REGRESSIONS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'mask_cases':len(rows),'prologue_cases':len(prologue),'gpio_stores':len(g.mmio),'fragments':len(fragments)}))
if __name__=='__main__':main()
