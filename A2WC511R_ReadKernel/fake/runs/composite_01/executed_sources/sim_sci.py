"""Finite SCI2 register model. Virtual instruction ticks are not silicon cycles.

Renesas SH7058 Rev3: SCI2 FFFFF010..F016; SSR read-one/write-zero rules.
All initial values and scheduling are explicit simulation inputs. No ROM replies
or protocol framing are generated here: output is only from CPU TDR activity.
"""
from collections import deque,Counter
from dataclasses import dataclass
from hashlib import sha256
import struct
from .core import SimulationStop

BASE=0xFFFFF010
SMR,BRR,SCR,TDR,SSR,RDR,SDCR=range(BASE,BASE+7)
TDRE,RDRF,ORER,FER,PER,TEND=0x80,0x40,0x20,0x10,0x08,0x04

@dataclass(frozen=True)
class Schedule:
    # Explicit virtual scheduling. These values do not express measured baud.
    rx_gap_ticks:int=1
    tx_complete_ticks:int=1
    brr_settle_ticks:int=1

class SCI2:
    def __init__(self, schedule=Schedule(), *, initial=None):
        if min(schedule.rx_gap_ticks,schedule.tx_complete_ticks,schedule.brr_settle_ticks)<1:
            raise ValueError('SCI scheduling must have positive explicit delays')
        self.schedule=schedule
        self.reg={SMR:0,BRR:0xFF,SCR:0,TDR:0xFF,SSR:TDRE|TEND,RDR:0,SDCR:0xF2}
        if initial:
            for a,v in initial.items():
                if a not in self.reg or not 0<=v<=255:raise ValueError('Unknown SCI initial register')
                self.reg[a]=v
        self.rx=deque();self.tx=bytearray();self.tick=0
        self.ssr_observed=0;self.tdr_written=False;self.rdr_read=False
        self.tx_pending=None;self.tx_due=None;self.rx_due=0;self.brr_tick=None
        self.events=[];self.record_events=False;self.error_injections=[]
        self.event_counts=Counter();self.event_digest=sha256()

    def _event(self,kind,**values):
        self.event_counts[kind]+=1
        # Memory access hashing lives in KernelMemory. Hash internal scheduling
        # transitions here without retaining millions of polling dictionaries.
        if kind not in ('register_read','register_write'):
            self.event_digest.update(kind.encode()+b'\0'+struct.pack('>QII',self.tick,
                values.get('value',values.get('bits',0)),values.get('bytes',0)))
        if self.record_events:self.events.append({'tick':self.tick,'kind':kind,**values})

    def feed(self,payload):
        self.rx.extend(bytes(payload));self._event('host_rx_enqueued',bytes=len(payload))

    def advance(self):
        self.tick+=1
        if self.tx_pending is not None and self.tick>=self.tx_due:
            value=self.tx_pending;self.tx_pending=None;self.tx_due=None
            self.tx.append(value);self.reg[SSR]|=TDRE|TEND
            self._event('tx_character_complete',value=value)
        if self.rx and self.reg[SCR]&0x10 and not self.reg[SSR]&RDRF and self.tick>=self.rx_due:
            self.reg[RDR]=self.rx.popleft();self.reg[SSR]|=RDRF;self.rdr_read=False
            self._event('rx_character_ready',value=self.reg[RDR])

    def inject_error(self,bits):
        if not bits or bits&~(ORER|FER|PER):raise ValueError('Invalid SCI error bits')
        self.reg[SSR]|=bits;self.error_injections.append((self.tick,bits))
        self._event('explicit_error_injection',bits=bits)

    def read(self,address,size):
        if size!=1 or address not in self.reg:
            raise SimulationStop(f'Unsupported SCI2 read {address:08X}+{size}')
        value=self.reg[address]
        if address==SSR:self.ssr_observed|=value
        if address==RDR:self.rdr_read=True
        self._event('register_read',address=f'{address:08X}',value=value)
        return value

    def write(self,address,size,value):
        if size!=1 or address not in self.reg:
            raise SimulationStop(f'Unsupported SCI2 write {address:08X}+{size}')
        value&=255
        if address==RDR:raise SimulationStop('SCI2 RDR is read-only')
        if address==SSR:
            old=self.reg[SSR]
            clear=old&~value&(TDRE|RDRF|ORER|FER|PER)
            if clear&~self.ssr_observed:
                raise SimulationStop(f'SCI2 clear without prior read-one: {clear&~self.ssr_observed:02X}')
            if clear&TDRE:
                if not self.tdr_written:raise SimulationStop('SCI2 TDRE clear without preceding TDR write')
                if not self.reg[SCR]&0x20:raise SimulationStop('SCI2 transmit attempted with TE disabled')
                if self.tx_pending is not None:raise SimulationStop('SCI2 transmit overlap unsupported')
                self.tx_pending=self.reg[TDR];self.tx_due=self.tick+self.schedule.tx_complete_ticks
                self.tdr_written=False;self.reg[SSR]&=~TEND
                self._event('tx_character_start',value=self.tx_pending)
            if clear&RDRF:
                self.rx_due=self.tick+self.schedule.rx_gap_ticks
            self.reg[SSR]=(self.reg[SSR]&~clear&~1)|(value&1)
            # TEND and MPB are read-only; writing zeros to them cannot force state.
            self.ssr_observed&=~clear
        elif address==SCR:
            if value&0xCC:raise SimulationStop('SCI2 interrupts/clock-output mode not modeled')
            if value&3:raise SimulationStop('SCI2 external-clock mode not modeled')
            if value&0x30 and self.brr_tick is not None and self.tick-self.brr_tick<self.schedule.brr_settle_ticks:
                raise SimulationStop('SCI2 BRR settling interval not satisfied in declared virtual schedule')
            if not value&0x20:
                if self.tx_pending is not None:
                    # SH7058 15.5.4: TE0 initializes transmission regardless of
                    # current status. No partial character is invented as RX.
                    self._event('tx_aborted_by_TE0',value=self.tx_pending)
                    self.tx_pending=None;self.tx_due=None;self.tdr_written=False
                self.reg[SSR]|=TDRE|TEND
            self.reg[SCR]=value
        elif address in (SMR,BRR,SDCR):
            if self.reg[SCR]&0x30:raise SimulationStop('SCI2 configuration changed while TE/RE enabled')
            if (address==SMR and value!=0) or (address==SDCR and value!=0xF2):
                raise SimulationStop('SCI2 mode unsupported by this explicit 8N1 model')
            self.reg[address]=value
            if address==BRR:self.brr_tick=self.tick
        elif address==TDR:
            if self.tx_pending is not None or not self.reg[SSR]&TDRE:
                raise SimulationStop('SCI2 TDR write while not ready')
            self.reg[TDR]=value;self.tdr_written=True
        self._event('register_write',address=f'{address:08X}',value=value)

    @property
    def rx_empty(self):return not self.rx and not self.reg[SSR]&RDRF

    @property
    def tx_idle(self):return self.tx_pending is None
