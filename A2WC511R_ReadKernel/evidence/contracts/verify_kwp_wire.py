"""Actual stock parser/serializer with explicit SCI register transcripts.

No UART waveform, elapsed time, interrupt scheduling, provider or hardware is
simulated. Replies come exclusively from executed TDR writes.
"""
import sys
sys.dont_write_bytecode=True
import json,gzip,hashlib
from pathlib import Path
from verify_kwp_contract import CPU,sh,common,ext
HERE=Path(__file__).resolve().parent

class TranscriptMemory(sh.Memory):
    def __init__(self,rom):
        super().__init__(rom);self.sci={0xFFFFF012:0x10,0xFFFFF014:0x84};self.tx=[];self.mmio=[]
    def read(self,address,size,address_sources=(),fetch=False):
        if not fetch and ((address in self.sci and size==1) or (address==0xFFFFF430 and size==4)):
            v=0xE78F1F21 if address==0xFFFFF430 else self.sci[address]
            self.mmio.append({'mode':'read','address':f'{address:08X}','size':size,'value':v,'pc':f'{self.pc:08X}'})
            return v,{'explicit_SCI_or_ATU_boundary_transcript'}
        return super().read(address,size,address_sources,fetch)
    def write(self,address,size,value,sources=(),address_sources=()):
        if size==1 and address in (0xFFFFF012,0xFFFFF013,0xFFFFF014):
            self.mmio.append({'mode':'write','address':f'{address:08X}','size':size,'value':value&255,'pc':f'{self.pc:08X}'})
            if address==0xFFFFF013:self.tx.append(value&255)
            elif address==0xFFFFF012:self.sci[address]=value&255
            # SSR reads are an explicit always-ready transcript, not a UART.
            return
        return super().write(address,size,value,sources,address_sources)

def main():
    rom=sh.ROM.load(common.STOCK,sh.STOCK_SHA256)
    ref=common.module('readkernel_wire_reference',common.REF)
    mem=TranscriptMemory(rom);mem.initialize(0xFFFF63E0,bytes(0xC0))
    traces=[]
    def call(entry):
        class WireCPU(CPU):
            def step(self):
                if self.pc==0x4717E and mem.ram[0x63E0]&0x10:
                    raise sh.SimulationStop('DECLARED_OEM_QUIESCENCE_BOUNDARY')
                return super().step()
        h=sh.FunctionHarness(mem,[(0x47108,0x47192),(0x471C2,0x47AFA),(0x47F20,0x48070),(0x4808C,0x4823A),(0x484F4,0x4857E),(0x2534,0x2550)])
        h.cpu=WireCPU(mem,h.cpu.execution_ranges,h.stack);h.cpu.track_control_sources=False
        try:result=h.run(entry,allowed_writes=[(0xFFFF63E0,0xFFFF64A0)],max_steps=3500)
        except sh.SimulationStop as e:
            if str(e)!='DECLARED_OEM_QUIESCENCE_BOUNDARY':raise
            assert entry==0x4808C and h.cpu.pc==0x4717E and not h.cpu.pending
            result={'boundary':'4717E before OEM quiescence','steps':len(h.cpu.trace)}
        traces.extend(h.cpu.trace)
        return result
    def transaction(payload,expected,bad_checksum=False):
        frame=ref.ssm(payload)
        if bad_checksum:frame=frame[:-1]+bytes([frame[-1]^1])
        offset=len(mem.tx)
        for b in frame:
            mem.initialize(0xFFFF63F8,bytes([b]));call(0x47F20)
        if bad_checksum:
            assert mem.ram[0x6401]==0 and not mem.tx
            return {'request':frame.hex(),'result':'bad checksum rejected; no reply selected or TDR write'}
        expected_frame=ref.ssm(expected,response=True)
        # The OEM periodic starter, after its counter reaches3, emits the first
        # byte at47DF4. Execute that exact bounded fragment; scheduler cadence is
        # an explicit boundary here, not a claimed simulated timer.
        c=CPU(mem,[(0x47DEE,0x47E02)],(0xFFFFBBA0,0xFFFFBFA0))
        c.pc=0x47DEE;c.r[15]=0xFFFFBFA0;c.call_context=['00047DEE']
        for _ in range(20):
            c.step()
            if c.pc==0x47E06 and not c.pending:break
        assert c.pc==0x47E06 and not c.pending
        traces.extend(c.trace)
        mem.pc=None
        # Stop after all reply bytes are actually written, before the next TX
        # service can trigger the separate OEM programming quiescence path.
        for _ in range(30):
            call(0x4808C)
            if len(mem.tx)-offset==len(expected_frame):break
        actual=bytes(mem.tx[offset:])
        assert actual==expected_frame,(payload.hex(),actual.hex(),expected_frame.hex())
        # For non-session replies, one final service closes the TX RAM state.
        if payload[0]!=0x10:call(0x4808C)
        return {'request':frame.hex(),'executed_TDR_reply':actual.hex(),'source':'stock instructions; explicit ready/TEND register input','physical_completion':False}
    rows=[]
    rows.append(transaction(b'\x81',b'',bad_checksum=True))
    rows.append(transaction(b'\x81',bytes.fromhex('c1ef8f')))
    rows.append(transaction(bytes.fromhex('8300'),bytes.fromhex('c30000ff00ff00')))
    rows.append(transaction(bytes.fromhex('2701'),bytes.fromhex('670112345678')))
    rows.append(transaction(bytes.fromhex('2702e78f1f21'),bytes.fromhex('670234')))
    rows.append(transaction(bytes.fromhex('108502'),bytes.fromhex('5085')))
    trace={'instructions':traces,'memory':mem.events,'mmio':mem.mmio}
    packed=gzip.compress(json.dumps(trace,sort_keys=True,separators=(',',':')).encode(),mtime=0)
    (HERE/'KWP_WIRE_TRACE.json.gz').write_bytes(packed)
    report={'schema':1,'status':'PASS_ACTUAL_STOCK_PARSER_SERIALIZER_WITH_REGISTER_TRANSCRIPTS','inputs':[common.pin(common.STOCK),common.pin(Path(__file__)),common.pin(HERE/'verify_kwp_contract.py'),common.pin(HERE/'verify_oem_contracts.py')],
      'transactions':rows,'executed_instructions':len(traces),'trace_sha256':hashlib.sha256(packed).hexdigest(),
      'post_session':{'session_63E1':mem.ram[0x63E1],'unlocked_649C':mem.ram[0x649C],'response_kind_63E0':mem.ram[0x63E0]},
      'limitations':['SCI status84 supplied as ready/TEND transcript; not cycle-accurate hardware.','RX bytes injected into actual parser input63F8, not actual SCI ISR/electrical timing.','Stops before OEM quiescence47AFC and boot jump; no ROM/MMIO effects inferred across that boundary.'],
      'physical_operations':0}
    (HERE/'KWP_WIRE_CONTRACT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'transactions':len(rows),'instructions':len(traces)}))

if __name__=='__main__':main()
