"""ECU-side receive-loopback controls; unrelated to host J2534 TX flags."""
import unittest
from .self_echo import SelfEchoSCI2,EchoProfile
from .sci import Schedule,SSR,SCR,TDR,RDR,RDRF,ORER,TEND

class ReceiverLoopback(unittest.TestCase):
    def transmit(self,u,value):
        status=u.read(SSR,1);u.write(TDR,1,value);u.write(SSR,1,status&0x7F);u.advance()
    def test_RE_off_discards_all_256_byte_values(self):
        u=SelfEchoSCI2();u.reg[SCR]=0x20
        for value in range(256):self.transmit(u,value)
        self.assertEqual(bytes(u.tx),bytes(range(256)))
        self.assertFalse(u.reg[SSR]&(RDRF|ORER))
        self.assertEqual(u.event_counts['ECU_self_echo_ignored_RE0'],256)
    def test_RE_on_retains_first_byte_and_ORER_disables_later_receiving(self):
        u=SelfEchoSCI2();u.reg[SCR]=0x30
        for value in (0x12,0x34,0x56):self.transmit(u,value)
        self.assertEqual(u.reg[RDR],0x12);self.assertEqual(u.reg[SSR]&(RDRF|ORER),RDRF|ORER)
        self.assertEqual(u.event_counts['ECU_self_echo_received'],1)
        self.assertEqual(u.event_counts['ECU_self_echo_overrun'],1)
        self.assertEqual(u.event_counts['ECU_self_echo_receiver_error_disabled'],1)
        old=u.read(SSR,1);u.read(RDR,1);u.write(SSR,1,old&~RDRF)
        u.feed(b'\x78');u.advance();self.assertEqual(u.reg[RDR],0x12)
        self.assertEqual(len(u.rx),1)
        old=u.read(SSR,1);u.write(SSR,1,old&~ORER);u.advance()
        self.assertEqual(u.reg[RDR],0x78)
    def test_receive_restore_before_TEND_admits_echo(self):
        u=SelfEchoSCI2(Schedule(tx_complete_ticks=5));u.reg[SCR]=0x20
        self.transmit(u,0xA5);self.assertFalse(u.reg[SSR]&TEND)
        self.transmit(u,0x5A)
        u.write(SCR,1,0x30)
        for _ in range(7):u.advance()
        self.assertEqual(u.reg[RDR],0x5A);self.assertTrue(u.reg[SSR]&RDRF)
    def test_wait_TEND_then_receive_restore_keeps_RDR_empty(self):
        u=SelfEchoSCI2(Schedule(tx_complete_ticks=5));u.reg[SCR]=0x20
        self.transmit(u,0xA5)
        for _ in range(4):u.advance()
        self.assertTrue(u.reg[SSR]&TEND);u.write(SCR,1,0x10)
        self.assertFalse(u.reg[SSR]&(RDRF|ORER))

    def test_start_while_RE0_cannot_become_a_byte_on_later_RE1(self):
        u=SelfEchoSCI2(Schedule(tx_complete_ticks=9),profile=EchoProfile(3));u.reg[SCR]=0x20
        self.transmit(u,0xA5)
        for _ in range(8):u.advance()
        self.assertTrue(u.reg[SSR]&TEND);u.write(SCR,1,0x10)
        for _ in range(3):u.advance()
        self.assertFalse(u.reg[SSR]&(RDRF|ORER))
        self.assertEqual(u.event_counts['ECU_self_echo_RE0_start_completed_after_RX_restore'],1)

    def test_genuinely_late_start_after_RE1_is_admitted(self):
        u=SelfEchoSCI2(Schedule(tx_complete_ticks=9),profile=EchoProfile(20));u.reg[SCR]=0x20
        self.transmit(u,0xA5)
        for _ in range(8):u.advance()
        u.write(SCR,1,0x10)
        for _ in range(20):u.advance()
        self.assertEqual(u.reg[RDR],0xA5);self.assertTrue(u.reg[SSR]&RDRF)

    def test_abort_cancels_incomplete_echo_character(self):
        u=SelfEchoSCI2(Schedule(tx_complete_ticks=25),profile=EchoProfile(5));u.reg[SCR]=0x20
        self.transmit(u,0xA5);u.write(SCR,1,0)
        for _ in range(40):u.advance()
        self.assertFalse(u.tx);self.assertTrue(u.line_idle)
        self.assertFalse(u.reg[SSR]&(RDRF|ORER))

if __name__=='__main__':unittest.main()
