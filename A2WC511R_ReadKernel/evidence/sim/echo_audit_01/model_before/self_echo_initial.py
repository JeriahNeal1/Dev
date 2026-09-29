"""Explicit ECU-side serial loopback profile, distinct from J2534 TX echoes.

Every completed SCI transmit character is also present on the physical receive
line in this declared topology. RE0 ignores it. RE1 receives into empty RDR;
another character with RDRF1 raises ORER and does not replace the unread byte.
This is a finite byte-completion model, not a bit waveform or electrical claim.
"""
from .sci import SCI2,SCR,SSR,RDR,RDRF,ORER

class SelfEchoSCI2(SCI2):
    def _complete_tx(self):
        value=self.tx_pending
        super()._complete_tx()
        if not self.reg[SCR]&0x10:
            self._event('ECU_self_echo_ignored_RE0',value=value)
        elif self.reg[SSR]&RDRF:
            self.reg[SSR]|=ORER
            self._event('ECU_self_echo_overrun',value=value)
        else:
            self.reg[RDR]=value;self.reg[SSR]|=RDRF;self.rdr_read=False
            self._event('ECU_self_echo_received',value=value)
