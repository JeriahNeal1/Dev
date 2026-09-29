"""Exact stock125C setup to polled loader, with named peripheral transcript."""
import sys
sys.dont_write_bytecode=True
import json,gzip
from pathlib import Path
from verify_boot_entry import CPU,sh,common
HERE=Path(__file__).resolve().parent

class SetupMemory(sh.Memory):
    def __init__(self,rom):
        super().__init__(rom);self.io={};self.mmio=[];self.counter=0
    def read(self,a,n,address_sources=(),fetch=False):
        if not fetch and ((0xFFFFF720<=a<0xFFFFF780 and n==2) or (a in (0xFFFFEC10,0xFFFFEC11,0xFFFFF012,0xFFFFF014,0xFFFFF819) and n==1)):
            if a==0xFFFFEC11:
                self.counter+=1;v=min(255,self.counter*50)
            elif a==0xFFFFF014:v=0x84
            elif a==0xFFFFF819:v=0x20
            elif a==0xFFFFEC10:v=0
            else:
                v=self.io.get(a,0)
                if a==0xFFFFF74E:v&=~0x40
                if a==0xFFFFF75E:v&=~0x04
            self.mmio.append({'pc':f'{self.pc:08X}','mode':'r','address':f'{a:08X}','size':n,'value':f'{v:0{n*2}X}'})
            return v,{'explicit_programming_connector_and_WDT_transcript'}
        return super().read(a,n,address_sources,fetch)
    def write(self,a,n,v,sources=(),address_sources=()):
        valid=(0xFFFFF720<=a<0xFFFFF780 and n==2) or (a in (0xFFFFEC10,0xFFFFEC12,0xFFFFF70A) and n==2) or (a in (0xFFFFF010,0xFFFFF011,0xFFFFF012,0xFFFFF014,0xFFFFF016,0xFFFFF818,0xFFFFF819) and n==1)
        if valid:
            v&=(1<<(n*8))-1;self.io[a]=v
            self.mmio.append({'pc':f'{self.pc:08X}','mode':'w','address':f'{a:08X}','size':n,'value':f'{v:0{n*2}X}'})
            return
        return super().write(a,n,v,sources,address_sources)

def main():
    rom=sh.ROM.load(common.STOCK,sh.STOCK_SHA256);m=SetupMemory(rom)
    m.initialize(0xFFFFBB80,bytes(0x420));m.initialize(0xFFFFBFE4,b'\x00')
    m.write_allowlist=[(0xFFFFBB80,0xFFFFC000)]
    c=CPU(m,[(0x1008,0x1150),(0x125C,0x1314),(0x14E6,0x1504),(0x1A5A,0x1AF4),(0x1B56,0x1BE8),(0x1C28,0x1C2E),(0x1C94,0x1CEE),(0x1DB6,0x1DE8)],(0xFFFFBB80,0xFFFFBFA0))
    c.pc=0x125C;c.r[15]=0xFFFFBFA0;c.pr=0xFFFFFFFC;c.call_context=['0000125C'];c._set_system('sr',0xF0,{'accepted_application_handoff'});c.track_control_sources=False
    for _ in range(3000):
        c.step()
        if c.pc==0x12F0 and not c.pending:break
    else:raise AssertionError('setup bound')
    assert c.pc==0x12F0 and c.sr&0xF0==0xF0 and c.vbr==0x1F44
    assert m.ram[0xBFBA]==1 and m.ram[0xBFC8]==1
    assert m.io[0xFFFFF70A]==0x3C00 and m.io[0xFFFFF011]==0x27
    assert not any(0xFFFFE800<=int(e['address'],16)<0xFFFFE807 for e in m.mmio)
    blob=gzip.compress(json.dumps({'instructions':c.trace,'memory':m.events,'mmio':m.mmio},sort_keys=True,separators=(',',':')).encode(),mtime=0)
    (HERE/'BOOT_SETUP_TRACE.json.gz').write_bytes(blob)
    report={'schema':1,'status':'PASS_SCOPED_STOCK_SETUP','inputs':[common.pin(common.STOCK),common.pin(Path(__file__)),common.pin(HERE/'verify_boot_entry.py')],
      'entry':'0000125C','end':'000012F0','instructions':len(c.trace),'SR_I':15,'VBR':'00001F44','SP':f'{c.r[15]:08X}',
      'programming_gate':'1008 observed F74Ebit6=0 and F75Ebit2=0 continuously across at least78 WDT counter ticks; setsBFBA1. ADC alternative not executed.',
      'register_transcript':'InitialGPIOwords0 unless initialized by executedboot; F74E inputbit6 andF75E inputbit2 forcedlow independentlyofoutputlatches; SCR initially0; SSR84 ready/TEND; EC10overflow0; EC11returns50,100,150,200 then255; F81920 holds ADC busy.',
      'MMIO':m.mmio,'flash_controller_store_count':0,
      'trace':common.pin(HERE/'BOOT_SETUP_TRACE.json.gz'),
      'limitations':['Pinned stock bytes, explicit peripheral values, no asynchronous interrupts/DMA/NMI.','The register transcript is not proof of physical connector, watchdog, ADC or oscillator behavior.','OEM changesGPIO direction/function/data andADC/WDT configuration; this is a temporary programming-session effect, not observational background execution.','No flash-controller access on this executed path; board-levelFWE wiring is not inferred fromGPIO values.'], 'physical_operations':0}
    (HERE/'BOOT_SETUP_CONTRACT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'instructions':len(c.trace),'mmio_writes':sum(x['mode']=='w' for x in m.mmio),'mask':c.sr&0xF0}))
if __name__=='__main__':main()
