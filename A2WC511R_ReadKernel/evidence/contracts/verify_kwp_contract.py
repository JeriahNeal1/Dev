"""Execute exact stock KWP validators and reply producers, offline only.

Explicit OEM RAM fixtures are boundary assumptions; this is not a serial driver,
reset-to-programming proof, or permission to issue physical commands.
"""
import sys
sys.dont_write_bytecode=True
import json,hashlib,gzip,struct,random
from pathlib import Path
import verify_oem_contracts as common
HERE=Path(__file__).resolve().parent
Base,sh,ext,extpath=common.build_cpu()

class CPU(Base):
    def step(self):
        op,_=self.memory.read(self.pc,2,fetch=True)
        if op&0xF0FF in (0x4015,0x4011):
            return ext.kernel.boot.BootCPU.extended_step(self,op)
        if op&0xF00F==0x6005:
            pc,slot,n,m=self.pc,self.pending,(op>>8)&15,(op>>4)&15
            assert any(a<=pc and pc+2<=b for a,b in self.execution_ranges)
            self._reg(15,self.r[15],self.sources[15])
            self.memory.pc,self.memory.in_delay_slot=pc,bool(slot)
            self.memory.call_context=list(self.call_context);self.memory.control_sources=set(self.control_sources)
            before=list(self.r);state={k:sh.hx(getattr(self,k)) for k in ('sr','mach','macl')}
            value,origins=self.memory.read(self.r[m],2,self.sources[m])
            self._reg(n,sh.sx(value,16),origins)
            if n!=m:self._reg(m,self.r[m]+2,self.sources[m])
            self.opcodes_seen.add('movw_postinc')
            self.trace.append({'pc':sh.hx(pc),'opcode':f'{op:04X}','instruction':'movw_postinc','delay_slot':bool(slot),
              'call_context':list(self.call_context),'registers':{f'r{i}':sh.hx(v) for i,v in enumerate(self.r) if v!=before[i]},
              't_before':self.t,'t_after':self.t,'system_before':state,'system_after':state,'pr_before':sh.hx(self.pr),'pr_after':sh.hx(self.pr)})
            self.pc,self.pending=pc+2,None
            if slot:
                self.pc,action=slot
                if action=='call':self.call_context.append(sh.hx(self.pc))
                elif action=='return':
                    assert self.call_context
                    self.call_context.pop();self.returned=not self.call_context
            return
        return super().step()

def main():
    rom=sh.ROM.load(common.STOCK,sh.STOCK_SHA256)
    opcode_controls=0
    for value in (0,0x7FFF,0x8000,0xFFFF):
        for overlap in (False,True):
            for delay in (False,True):
                instruction=bytes((0x64 if overlap else 0x65,0x45))
                program=b'\x00\x0b'+instruction if delay else instruction+b'\x00\x0b\x00\x09'
                memory=sh.Memory(rom.with_overlay(0x200,program,'isolated MOV.W postincrement regression'))
                memory.initialize(0xFFFF6000,value.to_bytes(2,'big'))
                h=sh.FunctionHarness(memory,[(0x200,0x206)]);h.cpu=CPU(memory,h.cpu.execution_ranges,h.stack)
                h.run(0x200,registers={4:0xFFFF6000},preserve_system=('sr','mach','macl'))
                assert h.cpu.r[4 if overlap else 5]==sh.sx(value,16)&0xFFFFFFFF
                if not overlap:assert h.cpu.r[4]==0xFFFF6002
                opcode_controls+=1
    rows=[]
    def run(name,entry,req=b'',session=0,unlocked=0,cooldown=0,cursor=5,key=0,registers=None,expected=None):
        mem=sh.Memory(rom);mem.initialize(0xFFFF63E0,bytes(0xC0))
        frame=bytes.fromhex('8010F0')+bytes([len(req)])+req
        mem.initialize(0xFFFF6408,frame)
        mem.initialize(0xFFFF63E1,bytes([session]));mem.initialize(0xFFFF649C,bytes([unlocked]))
        mem.initialize(0xFFFF6498,cooldown.to_bytes(2,'big'))
        mem.initialize(0xFFFF63FA,bytes([cursor]));mem.initialize(0xFFFF63EC,key.to_bytes(4,'big'))
        h=sh.FunctionHarness(mem,[(0x47108,0x47AFA)])
        h.cpu=CPU(mem,h.cpu.execution_ranges,h.stack);h.cpu.track_control_sources=False
        r=h.run(entry,allowed_writes=[(0xFFFF63E0,0xFFFF64A0)],registers=registers,max_steps=3000)
        def b(a,n=1):return bytes(mem.ram[a-sh.RAM_START:a-sh.RAM_START+n])
        row={'name':name,'entry':f'{entry:08X}','request':req.hex(),
             'fixtures':{'session_63E1':session,'unlocked_649C':unlocked,'cooldown_6498':cooldown,'cursor_63FA':cursor,'key_63EC':f'{key:08X}'},
             'return':h.cpu.r[0],'response_opcode':b(0xFFFF6401).hex(),'response_length':b(0xFFFF6405)[0],
             'reason':b(0xFFFF63E3).hex(),'body_buffer':b(0xFFFF6492,8).hex(),
             'session_after':b(0xFFFF63E1)[0],'unlocked_after':b(0xFFFF649C)[0],
             'instructions':r['steps'],'trace_sha256':r['trace_sha256'],
             'writes':[[e['address'],e['size'],e.get('value')] for e in mem.events if e['mode']=='w']}
        if expected:
            for k,v in expected.items():assert row[k]==v,(name,k,row[k],v)
        trace=json.dumps({'instructions':h.cpu.trace,'memory':mem.events},sort_keys=True,separators=(',',':')).encode()
        (HERE/(name+'.trace.json.gz')).write_bytes(gzip.compress(trace,mtime=0))
        rows.append(row)
        return row
    run('kwp_81_valid',0x476E0,b'\x81',expected={'return':0,'response_opcode':'c1','response_length':3})
    run('kwp_81_bad_length',0x476E0,b'\x81\x00',expected={'return':0,'response_opcode':'7f','response_length':3,'reason':'10'})
    run('kwp_83_valid',0x476E0,b'\x83\x00',session=0x20,expected={'response_opcode':'c3','response_length':7})
    run('kwp_83_without_session',0x476E0,b'\x83\x00',expected={'response_opcode':'7f','reason':'10'})
    run('kwp_83_bad_sub',0x476E0,b'\x83\x01',session=0x20,expected={'response_opcode':'7f','reason':'10'})
    run('kwp_27_seed_valid',0x476E0,b'\x27\x01',session=0x20,expected={'response_opcode':'67','response_length':6})
    run('kwp_27_cooldown',0x476E0,b'\x27\x01',session=0x20,cooldown=1,expected={'response_opcode':'7f','reason':'37'})
    run('kwp_27_key_valid',0x476E0,bytes.fromhex('270212345678'),session=0x60,key=0x12345678,expected={'response_opcode':'67','response_length':3,'unlocked_after':1})
    run('kwp_27_key_wrong',0x476E0,bytes.fromhex('270212345679'),session=0x60,key=0x12345678,expected={'response_opcode':'7f','reason':'35','unlocked_after':0})
    run('kwp_10_valid',0x476E0,bytes.fromhex('108502'),session=0x20,unlocked=1,expected={'response_opcode':'50','response_length':2})
    run('kwp_10_locked',0x476E0,bytes.fromhex('108502'),session=0x20,expected={'response_opcode':'7f','reason':'22'})
    run('kwp_10_wrong_rate',0x476E0,bytes.fromhex('108503'),session=0x20,unlocked=1,expected={'response_opcode':'7f','reason':'10'})
    run('kwp_81_body',0x477DE,expected={'body_buffer':'ef8f000000000000','session_after':0x20})
    run('kwp_83_body_first',0x477FC,cursor=5,expected={'body_buffer':'0000ff0000000000'})
    run('kwp_83_body_last',0x477FC,cursor=9,expected={'body_buffer':'ff00000000000000'})
    run('kwp_27_key_body',0x4782A,session=0x60,unlocked=1,expected={'body_buffer':'0234000000000000','session_after':0x20})
    run('kwp_10_body',0x47910,expected={'body_buffer':'8500000000000000'})
    # Execute the actual seed producer with one explicit peripheral input.
    ref=common.module('readkernel_seed_reference',common.REF)
    assert rom.data[0x4EAAC:0x4EACC]==struct.pack('>16H',*ref.SEED_KEYS)
    assert rom.data[0x4EAEC:0x4EB0C]==bytes(ref.TABLE)
    class TimerMemory(sh.Memory):
        def __init__(self,rom,timer):super().__init__(rom);self.timer=timer;self.timer_reads=[]
        def read(self,address,size,address_sources=(),fetch=False):
            if address==0xFFFFF430 and size==4 and not fetch:
                self.timer_reads.append({'pc':f'{self.pc:08X}','address':'FFFFF430','width':4,'value':f'{self.timer:08X}'})
                return self.timer,{'fixture:ATU_TCNT0_value'}
            return super().read(address,size,address_sources,fetch)
    rng=random.Random(0x511027)
    seeds=[]
    for timer in [0,0xFFFFFFFF,0x12345678,0xE78F1F21]+[rng.getrandbits(32) for _ in range(12)]:
        m=TimerMemory(rom,timer);m.initialize(0xFFFF63E0,bytes(0xC0));m.initialize(0xFFFF63E1,b'\x20')
        h=sh.FunctionHarness(m,[(0x479A0,0x47A16),(0x47A4C,0x47AF8)])
        h.cpu=CPU(m,h.cpu.execution_ranges,h.stack);h.cpu.track_control_sources=False
        result=h.run(0x479A0,allowed_writes=[(0xFFFF63EC,0xFFFF63F0)],max_steps=3000)
        seed=h.cpu.r[0].to_bytes(4,'big')
        assert seed==ref.transform_words(timer.to_bytes(4,'big'),ref.SEED_KEYS)
        assert ref.seed_key(seed)==timer.to_bytes(4,'big')
        assert bytes(m.ram[0x63EC:0x63F0])==timer.to_bytes(4,'big')
        assert len(m.timer_reads)==1
        seeds.append({'timer_and_stored_expected_key':f'{timer:08X}','wire_seed':seed.hex(),'steps':result['steps'],'trace_sha256':result['trace_sha256'],'timer_reads':m.timer_reads})
    report={'schema':1,'status':'PASS_SCOPED_KWP_VALIDATOR_AND_PRODUCER_EXECUTION',
      'inputs':[common.pin(common.STOCK),common.pin(common.SIM),common.pin(Path(common.__file__)),common.pin(Path(__file__)),common.pin(extpath),common.pin(Path(ext.kernel.__file__)),common.pin(Path(ext.kernel.boot.__file__))],
      'cases':rows,'seed_cases':seeds,'new_instruction_controls':{'instruction':'MOV.W @Rm+,Rn','cases':opcode_controls,'scope':'Signed boundary values; same/different source/destination; ordinary and RTS delay slot; SR preserved.'},'positive_payloads':{'81':'c1ef8f','8300':'c30000ff00ff00','2701':'6701 + four generated seed bytes','2702_valid_key':'670234','108502':'5085'},
      'seed_contract':{'entry':'000479A0','timer_read':'FFFFF430 long','expected_key_store':'FFFF63EC long','rounds':16,'keys':'0004EAAC..0004EACC','substitution_table':'0004EAEC..0004EB0C','round_function':'00047AD2 -> 00047A4C','host_inverse':'Same Feistel permutation with reversed keys; exact stock constants match host reference.'},
      'limits':['Explicit RAM boundary fixtures; no receive-checksum/UART timing execution.','Boot transition is a separate follow-up contract.','No physical protocol acceptance or current-ROM identity claim.'],
      'physical_operations':0}
    (HERE/'KWP_PRODUCER_REGRESSIONS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'cases':len(rows),'seed_cases':len(seeds),'positive_payloads':report['positive_payloads']}))

if __name__=='__main__':main()
