"""Explicit ECU-side serial loopback profile, distinct from J2534 TX echoes.

Every completed SCI transmit character is also present on the physical receive
line in this declared topology. RE0 ignores it. RE1 receives into empty RDR;
another character with RDRF1 raises ORER and does not replace the unread byte.
This is a finite byte-completion model, not a bit waveform or electrical claim.
"""
from dataclasses import dataclass
import heapq
from .sci import SCI2,SCR,SSR,RDR,RDRF,ORER

@dataclass(frozen=True)
class EchoProfile:
    # This delay shifts BOTH receive-start and receive-completion. It is not
    # permission to deliver a character whose start was ignored with RE0.
    start_delay_ticks:int=0
    ordinals:tuple|None=None

class SelfEchoSCI2(SCI2):
    def __init__(self,schedule=None,*,initial=None,profile=EchoProfile()):
        from .sci import Schedule
        super().__init__(Schedule() if schedule is None else schedule,initial=initial)
        if type(profile.start_delay_ticks) is not int or profile.start_delay_ticks<0:
            raise ValueError('Nonnegative explicit echo start delay required')
        if profile.ordinals is not None and (type(profile.ordinals) is not tuple or
          any(type(x) is not int or x<1 for x in profile.ordinals)):
            raise ValueError('Positive explicit echo character ordinals required')
        self.profile=profile;self.echo_ordinal=0;self.receive_epoch=0
        self.echo_queue=[];self.echo_started={};self.current_echo=None

    def _event(self,kind,**values):
        super()._event(kind,**values)
        if kind=='tx_shift_register_loaded':
            self.echo_ordinal+=1;ordinal=self.echo_ordinal
            if self.profile.ordinals is not None and ordinal not in self.profile.ordinals:return
            value=values['value'];delay=self.profile.start_delay_ticks
            if delay==0:self.current_echo=self._receive_start(value,ordinal)
            else:
                heapq.heappush(self.echo_queue,(self.tick+delay,0,ordinal,value))
                heapq.heappush(self.echo_queue,(self.tx_due+delay,1,ordinal,value))

    def _receive_start(self,value,ordinal):
        enabled=bool(self.reg[SCR]&0x10);error=bool(self.reg[SSR]&ORER)
        token=(ordinal,value,self.receive_epoch,enabled and not error,enabled)
        SCI2._event(self,'ECU_self_echo_start_RE0' if not enabled else
            ('ECU_self_echo_start_receiver_error_disabled' if error else 'ECU_self_echo_start_admitted'),value=value)
        return token

    def _receive_complete(self,token):
        ordinal,value,epoch,admitted,enabled=token
        if not admitted:
            self._event('ECU_self_echo_ignored_RE0' if not enabled else 'ECU_self_echo_receiver_error_disabled',value=value)
            if not enabled and self.reg[SCR]&0x10:
                self._event('ECU_self_echo_RE0_start_completed_after_RX_restore',value=value)
        elif epoch!=self.receive_epoch or not self.reg[SCR]&0x10:
            self._event('ECU_self_echo_cancelled_by_RE0',value=value)
        elif self.reg[SSR]&ORER:
            self._event('ECU_self_echo_receiver_error_disabled',value=value)
        elif self.reg[SSR]&RDRF:
            self.reg[SSR]|=ORER
            self._event('ECU_self_echo_overrun',value=value)
        else:
            self.reg[RDR]=value;self.reg[SSR]|=RDRF;self.rdr_read=False
            self._event('ECU_self_echo_received',value=value)

    def _complete_tx(self):
        token=self.current_echo;self.current_echo=None
        super()._complete_tx()
        if token is not None:self._receive_complete(token)

    def advance(self):
        super().advance()
        while self.echo_queue and self.echo_queue[0][0]<=self.tick:
            due,phase,ordinal,value=heapq.heappop(self.echo_queue)
            if phase==0:self.echo_started[ordinal]=self._receive_start(value,ordinal)
            else:self._receive_complete(self.echo_started.pop(ordinal))

    def write(self,address,size,value):
        aborted_ordinal=self.echo_ordinal if address==SCR and not value&0x20 and self.tx_pending is not None else None
        super().write(address,size,value)
        if aborted_ordinal is not None:
            self.echo_queue=[e for e in self.echo_queue if e[2]!=aborted_ordinal];heapq.heapify(self.echo_queue)
            self.echo_started.pop(aborted_ordinal,None);self.current_echo=None
            self._event('ECU_self_echo_aborted_transmit_character',value=aborted_ordinal)
        if address==SCR and not value&0x10:self.receive_epoch+=1

    @property
    def line_idle(self):return not self.echo_queue and not self.echo_started

    def echo_state(self):
        return (self.echo_ordinal,self.receive_epoch,tuple(self.echo_queue),
           tuple(sorted(self.echo_started.items())),self.current_echo)
