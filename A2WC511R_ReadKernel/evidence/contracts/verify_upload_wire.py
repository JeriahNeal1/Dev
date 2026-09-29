"""Execute actual stock RAM-upload parser, decrypt, checksum, ACK and handoff.

Peripheral values are explicit ready/TEND transcripts, not hardware simulation.
The boot programming-admission byte is an explicitly stated entry assumption.
"""
import sys
sys.dont_write_bytecode=True
import json,gzip,hashlib
from pathlib import Path
from verify_boot_entry import CPU,sh,common
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
KERNEL=ROOT/'build/attempt_03/kernel.bin'
protocol=common.module('readkernel_upload_protocol',ROOT/'host/protocol.py')

class Memory(sh.Memory):
    def __init__(self,rom):
        super().__init__(rom);self.byte=None;self.tx=[];self.mmio=[];self.scr=0x10
    def read(self,a,n,address_sources=(),fetch=False):
        if not fetch and n==1 and a in (0xFFFFF012,0xFFFFF014,0xFFFFF015,0xFFFFEC10):
            v={0xFFFFF012:self.scr,0xFFFFF014:0x84,0xFFFFF015:self.byte,0xFFFFEC10:0}[a]
            assert v is not None
            self.mmio.append({'pc':f'{self.pc:08X}','mode':'r','address':f'{a:08X}','size':n,'value':v})
            return v,{'explicit_ready_TEND_RDR_WDT_transcript'}
        return super().read(a,n,address_sources,fetch)
    def write(self,a,n,v,sources=(),address_sources=()):
        if n==1 and a in (0xFFFFF012,0xFFFFF013,0xFFFFF014):
            self.mmio.append({'pc':f'{self.pc:08X}','mode':'w','address':f'{a:08X}','size':n,'value':v&255})
            if a==0xFFFFF013:self.tx.append(v&255)
            if a==0xFFFFF012:self.scr=v&255
            return
        return super().write(a,n,v,sources,address_sources)

def main():
    rom=sh.ROM.load(common.STOCK,sh.STOCK_SHA256);kernel=KERNEL.read_bytes()
    assert hashlib.sha256(kernel).hexdigest()=='3d70abfb8617b87e1b9c52724fd27ed4066ba231818994e780c8ba3006de273f'
    m=Memory(rom);m.initialize(0xFFFFBFA0,bytes(0x60));m.initialize(0xFFFFBFBA,b'\x01');m.initialize(0xFFFFBFC8,b'\x01')
    m.initialize(0xFFFFBB80,bytes(0x420))
    m.write_allowlist=[(0xFFFFBB80,0xFFFFC000),(0xFFFF3000,0xFFFF3000+len(kernel))]
    trace=[];rows=[];entered=False
    def call(byte):
        nonlocal entered
        m.byte=byte;c=CPU(m,[(0x13F6,0x1F40)],(0xFFFFBB80,0xFFFFBFA0));c.pc=0x1440;c.pr=0xFFFFFFFC;c.r[15]=0xFFFFBFA0
        c.call_context=['00001440'];c._set_system('sr',0xF0,{'boot_loop_mask15'});c.track_control_sources=False
        for _ in range(15000):
            c.step()
            if c.pc==0xFFFF3004 and not c.pending:
                entered=True;assert c.r[15]==0xFFFFBFA0 and c.sr&0xF0==0xF0
                break
            if c.returned:
                assert c.pc==0xFFFFFFFC and c.r[15]==0xFFFFBFA0 and not c.pending
                break
        else:raise AssertionError('bounded parser instruction budget')
        trace.extend(c.trace)
    frames=[protocol.declaration(len(kernel)),*protocol.upload_frames(kernel),protocol.ssm(bytes.fromhex('310101'))]
    for i,frame in enumerate(frames):
        start=len(m.tx);before=len(trace)
        for byte in frame:call(byte)
        reply=bytes(m.tx[start:]);wanted=bytes.fromhex('7484') if i==0 else bytes.fromhex('710101') if i==len(frames)-1 else b'\x76'
        assert reply==protocol.ssm(wanted,response=True),(i,reply.hex(),wanted.hex())
        rows.append({'frame_index':i,'request':frame.hex(),'reply_from_executed_TDR':reply.hex(),'instructions':len(trace)-before})
    actual=bytes(m.ram[0x3000:0x3000+len(kernel)])
    assert actual==kernel and entered
    stores=[e for e in m.events if e['mode']=='w' and 0xFFFF3000<=int(e['address'],16)<0xFFFF3000+len(kernel)]
    assert len(stores)==len(kernel)//4 and all(e['size']==4 and e['pc']=='00001646' for e in stores)
    assert [int(e['address'],16) for e in stores]==list(range(0xFFFF3000,0xFFFF3000+len(kernel),4))
    packed=gzip.compress(json.dumps({'instructions':trace,'memory':m.events,'mmio':m.mmio},sort_keys=True,separators=(',',':')).encode(),mtime=0)
    (HERE/'UPLOAD_WIRE_TRACE.json.gz').write_bytes(packed)
    report={'schema':1,'status':'PASS_ACTUAL_STOCK_UPLOAD_PARSER_AND_HANDOFF','inputs':[common.pin(common.STOCK),common.pin(KERNEL),common.pin(ROOT/'host/protocol.py'),common.pin(Path(__file__)),common.pin(HERE/'verify_boot_entry.py'),common.pin(HERE/'verify_kwp_contract.py'),common.pin(HERE/'verify_oem_contracts.py')],
      'frames':rows,'instructions':len(trace),'actual_upload_sha256':hashlib.sha256(actual).hexdigest(),'upload_store_count':len(stores),'upload_store_pc':'00001646','upload_range':['FFFF3000',f'{0xFFFF3000+len(kernel):08X}'],
      'handoff':{'pc':'FFFF3004','sp':'FFFFBFA0','SR_I':15,'VBR':'inherited1F44; not rewritten by these parser functions'},
      'MMIO_store_addresses':sorted({x['address'] for x in m.mmio if x['mode']=='w'}),'flash_controller_stores':0,'trace':common.pin(HERE/'UPLOAD_WIRE_TRACE.json.gz'),
      'assumptions':['Successful OEM1008 programming condition established BFBA1; boot loop BFC81 and initialized parser RAM.','Input injected at actual RDR read; ready/TEND84 and nonexpired WDT are explicit transcript values.','No asynchronous DMA, interrupt, NMI, power event or byte corruption; pinned stock bytes.'],
      'limits':['No UART waveform, physical clock or elapsed-time simulation.','No full reset-to-upload uninterrupted execution; earlier KWP/IRQ/initialization contracts are independently linked.','This byte-exact upload execution supplements address/length/domain derivation, not a universal malformed-request theorem.'], 'physical_operations':0}
    (HERE/'UPLOAD_WIRE_CONTRACT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'frames':len(rows),'instructions':len(trace),'upload_store_count':len(stores),'entry':entered}))
if __name__=='__main__':main()
