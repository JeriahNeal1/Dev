"""Architectural local-extension and finite peripheral-model negative controls."""
import unittest
from .core import sh2e,SimulationStop
from .cpu import KernelCPU
from .memory import KernelMemory,PeripheralModel
from .sci import SCI2,Schedule,SMR,BRR,SCR,TDR,SSR,RDR,SDCR,TDRE,RDRF,TEND

class LocalISA(unittest.TestCase):
    def cpu(self,op):
        rom=sh2e.ROM.synthetic(bytes(0x100000),'local opcode regression only')
        load=0xFFFF3000
        mem=KernelMemory(rom,op.to_bytes(2,'big'),load,[load],[(0xFFFF4000,0xFFFF4100)],PeripheralModel())
        c=KernelCPU(mem,[(load,load+2)],(0xFFFF4000,0xFFFF4100),0xFFFFBFA0)
        c.r[15]=0xFFFF4100;c.pc=load;c.call_context=['fixture']
        return c

    def test_exact_new_forms_preserve_T_and_delay_destination(self):
        checks=0
        for t in (0,1):
            for slot in (None,(0xFFFF3004,None)):
                for value in (0,1,255,256,0x80000000,0xFFFFFFFF):
                    for op in (0x0E2A,0x4E2A,0x402E,0x4419,0x4429,0xCABE):
                        c=self.cpu(op);c.pr=value;c.r[14]=value;c.r[0]=value;c.r[4]=value
                        c._set_system('sr',0x302|t,());c.pending=slot
                        c.step()
                        self.assertEqual(c.sr,0x302|t)
                        self.assertEqual(c.pc,0xFFFF3004 if slot else 0xFFFF3002)
                        if op==0x0E2A:self.assertEqual(c.r[14],value)
                        if op==0x4E2A:self.assertEqual(c.pr,value)
                        if op==0x402E:self.assertEqual(c.vbr,value)
                        if op==0x4419:self.assertEqual(c.r[4],value>>8)
                        if op==0x4429:self.assertEqual(c.r[4],value>>16)
                        if op==0xCABE:self.assertEqual(c.r[0],value^0xBE)
                        checks+=1
        self.assertEqual(checks,144)

    def test_unknown_opcode_and_address_fail(self):
        c=self.cpu(0xFFFF)
        with self.assertRaises(SimulationStop):c.step()
        c=self.cpu(0x0009);c.pc=0xFFFF3002
        with self.assertRaises(SimulationStop):c.step()
        c=self.cpu(0x0009)
        with self.assertRaises(SimulationStop):c.memory.write(0,1,0)
        with self.assertRaises(SimulationStop):c.memory.write(0xFFFF3000,1,0)
        with self.assertRaises(SimulationStop):c.memory.read(0xFFFF4000,1)
        with self.assertRaises(SimulationStop):c.memory.read(0xFFFFF000,1)

class SCIContracts(unittest.TestCase):
    def ready(self):
        s=SCI2(Schedule(tx_complete_ticks=3,brr_settle_ticks=2))
        s.write(SCR,1,0);s.write(SMR,1,0);s.write(SDCR,1,0xF2);s.write(BRR,1,9)
        s.advance();s.advance();s.write(SCR,1,0x30)
        return s

    def test_TX_is_only_actual_TDR_and_read_before_clear(self):
        s=self.ready();s.write(TDR,1,0xA5)
        with self.assertRaises(SimulationStop):s.write(SSR,1,4)
        ssr=s.read(SSR,1);s.write(SSR,1,ssr&0x7F)
        self.assertEqual(bytes(s.tx),b'');self.assertEqual(s.reg[SSR]&TEND,0)
        s.advance();s.advance();self.assertEqual(bytes(s.tx),b'')
        s.advance();self.assertEqual(bytes(s.tx),b'\xA5')
        self.assertEqual(s.reg[SSR]&(TDRE|TEND),TDRE|TEND)

    def test_RX_RDR_does_not_clear_flag(self):
        s=self.ready();s.feed(b'\xBE\xEF');s.advance()
        old=s.read(SSR,1);self.assertTrue(old&RDRF)
        self.assertEqual(s.read(RDR,1),0xBE);self.assertTrue(s.reg[SSR]&RDRF)
        s.write(SSR,1,old&~RDRF);s.advance()
        self.assertEqual(s.read(RDR,1),0xEF)

    def test_unknown_and_forbidden_peripherals_fail(self):
        s=SCI2(Schedule(brr_settle_ticks=2));s.write(BRR,1,9)
        with self.assertRaises(SimulationStop):s.write(SCR,1,0x30)
        with self.assertRaises(SimulationStop):s.write(SCR,1,0xC0)
        with self.assertRaises(SimulationStop):s.read(SSR,2)
        with self.assertRaises(SimulationStop):s.write(SDCR,1,0)
        p=PeripheralModel()
        for address in (0xFFFFE800,0xFFFFE803,0xFFFFE804,0xFFFFE805):
            with self.assertRaises(SimulationStop):p.write(address,1,0)
        with self.assertRaises(SimulationStop):p.read(0xFFFFF000,1)

    def test_errors_require_observed_one_and_never_set_by_zero_default(self):
        s=self.ready();s.inject_error(0x38)
        with self.assertRaises(SimulationStop):s.write(SSR,1,0x84)
        value=s.read(SSR,1);s.write(SSR,1,value&0xC7)
        self.assertEqual(s.read(SSR,1)&0x38,0)

if __name__=='__main__':unittest.main()
