"""Read-only stock loader anchors and actual SH-2E decrypt execution.

Writes only new ReadKernel evidence; never invokes IDA, a provider or hardware.
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
OLD = Path('C:/Dev/Astra_A2WC511R')
SIM = Path('C:/Dev/A2WC511R_Sim/sh2e.py')
STOCK = Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')
REF = OLD/'reports/local/ecuflash_dynamic/protocol_reference/protocol_reference.py'

def pin(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m
    spec.loader.exec_module(m)
    return m

def build_cpu():
    sh=module('sh2e',SIM)
    # Reuse the pinned already-tested integer extensions. Frozen CPU files are
    # read-only; no new instruction semantics are introduced here.
    extpath=OLD/'reports/local/ecuflash_dynamic/kernel_candidate/read_paths_CANDIDATE/cleanup_CANDIDATE.py'
    ext=module('readkernel_contract_extensions',extpath)
    class ContractCPU(ext.PathCPU):
        def step(self):
            op,_=self.memory.read(self.pc,2,fetch=True)
            if op & 0xFF00 == 0x8500:
                # SH-2E MOV.W @(disp,Rm),R0: unsigned disp*2, signed data.
                pc,slot,m=self.pc,self.pending,(op>>4)&15
                if not any(a<=pc and pc+2<=b for a,b in self.execution_ranges):
                    raise sh.SimulationStop('MOV.W displacement outside execution range')
                self._reg(15,self.r[15],self.sources[15])
                self.memory.pc,self.memory.in_delay_slot=pc,bool(slot)
                self.memory.call_context=list(self.call_context)
                self.memory.control_sources=set(self.control_sources)
                value,origins=self.memory.read((self.r[m]+2*(op&15))&0xFFFFFFFF,2,self.sources[m])
                state={k:sh.hx(getattr(self,k)) for k in ('sr','mach','macl')}
                self._reg(0,sh.sx(value,16),origins)
                self.opcodes_seen.add('movw_disp_load')
                self.trace.append({'pc':sh.hx(pc),'opcode':f'{op:04X}',
                  'instruction':'movw_disp_load','delay_slot':bool(slot),
                  'call_context':list(self.call_context),'registers':{'r0':sh.hx(self.r[0])},
                  't_before':self.t,'t_after':self.t,'system_before':state,'system_after':state,
                  'pr_before':sh.hx(self.pr),'pr_after':sh.hx(self.pr)})
                self.pc,self.pending=pc+2,None
                if slot:
                    self.pc,action=slot
                    if action=='call':self.call_context.append(sh.hx(self.pc))
                    elif action=='return':
                        if not self.call_context:raise sh.SimulationStop('Return without context')
                        self.call_context.pop();self.returned=not self.call_context
                return
            if op & 0xF0FF == 0x4029 or op & 0xFF00 == 0x8100:
                return ext.kernel.boot.BootCPU.extended_step(self,op)
            return super().step()
    return ContractCPU,sh,ext,extpath

def main():
    ContractCPU,sh,ext,extpath=build_cpu()
    ref=module('readkernel_contract_crypto',REF)
    rom=sh.ROM.load(STOCK,sh.STOCK_SHA256)
    raw=rom.data
    opcode_cases=0
    for disp in (0,1,4,15):
        for word in (0,0x7FFF,0x8000,0xFFFF):
            for delayed in (False,True):
                program=(b'\x00\x0b'+bytes((0x85,0x40|disp))) if delayed else (bytes((0x85,0x40|disp))+b'\x00\x0b\x00\x09')
                r=rom.with_overlay(0x200,program,'synthetic isolated MOV.W displacement contract')
                m=sh.Memory(r);m.initialize(0xFFFF6000+2*disp,word.to_bytes(2,'big'))
                h=sh.FunctionHarness(m,[(0x200,0x206)])
                h.cpu=ContractCPU(m,h.cpu.execution_ranges,h.stack)
                h.run(0x200,registers={4:0xFFFF6000},preserve_system=('sr','mach','macl'))
                assert h.cpu.r[0]==sh.sx(word,16)&0xFFFFFFFF
                opcode_cases+=1
    assert raw[0x1C34:0x1C54] == bytes(ref.TABLE)
    assert raw[0x1C54:0x1C5C] == bytes.fromhex('7856CE22F5136E86')
    anchors={0x18CE:0x3E12,0x18DC:0x3026,0x18E2:0x60E3,
             0x18E8:0x3E00,0x18F2:0x8804,0x163C:0x410B,
             0x1646:0x2302,0x197C:0x6346,0x1982:0x363C,
             0x1986:0x666D,0x1988:0x3630,0x199E:0x432B,
             0x1C28:0xDF01,0x1C2A:0x442B}
    for a,v in anchors.items():assert int.from_bytes(raw[a:a+2],'big')==v
    rng=random.Random(70583136)
    words=[0,0xFFFFFFFF,0x2178B10A,0x00090009,0x80000000,0x00008000]
    words += [rng.getrandbits(32) for _ in range(58)]
    rows=[]
    for w in words:
        mem=sh.Memory(rom)
        h=sh.FunctionHarness(mem,[(0x1E3C,0x1E82),(0x1E94,0x1F40)])
        h.cpu=ContractCPU(mem,h.cpu.execution_ranges,h.stack)
        h.cpu.track_control_sources=False
        result=h.run(0x1E3C,registers={4:w},max_steps=2000)
        expected=int.from_bytes(ref.decrypt_upload(w.to_bytes(4,'big')),'big')
        assert h.cpu.r[0]==expected
        assert all(e['mode']!='w' or h.stack[0]<=int(e['address'],16)<h.stack[1]
                   for e in mem.events)
        rows.append({'ciphertext':f'{w:08X}','plaintext':f'{expected:08X}',
                     'instructions':result['steps'],'trace_sha256':result['trace_sha256'],
                     'stack_low':min([h.stack[1]]+[int(e['address'],16) for e in mem.events if e['mode']=='w'])})
    # Same four rounds and branch pattern for all input values: the only branch
    # depends on the literal four-round loop count, not ciphertext bits.
    assert len({r['instructions'] for r in rows})==1
    report={'schema':1,'status':'PASS_SCOPED_STOCK_DECRYPT_AND_LITERAL_CONTRACT',
      'inputs':[pin(STOCK),pin(SIM),pin(REF),pin(Path(__file__)),pin(extpath),
                pin(Path(ext.kernel.__file__)),pin(Path(ext.kernel.boot.__file__))],
      'table_address':'00001C34','encrypt_keys':['7856','CE22','F513','6E86'],
      'decrypt_keys':['6E86','F513','CE22','7856'],
      'entry':'00001E3C','callees':['00001F1A','00001E94'],
      'anchors':{f'{a:08X}':f'{v:04X}' for a,v in anchors.items()},
      'executed_vectors':rows,'preserved_registers':'R8..R15, PR, MACH, MACL',
      'new_harness_instruction':'MOV.W @(disp,Rm),R0 only; signedword/displacement0,1,4,15 and ordinary/RTS-delay-slot regressions',
      'new_harness_instruction_cases':opcode_cases,
      'write_scope':'Only declared stack; no MMIO, flash or upload-store execution.',
      'limits':['No full OEM serial/parser/session execution.',
                'Positive handoff ACK and physical boot acceptance are not modeled.',
                'Regression examples supplement the fixed-round instruction/constant derivation; they do not prove arbitrary loader input safety.'],
      'physical_operations':0}
    (HERE/'OEM_LOADER_REGRESSION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'vectors':len(rows),'instructions_per_word':rows[0]['instructions'],'stack_depth':h.stack[1]-rows[0]['stack_low']}))

if __name__=='__main__':main()
