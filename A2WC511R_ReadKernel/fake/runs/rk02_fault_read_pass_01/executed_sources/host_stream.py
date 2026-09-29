"""Independent bounded replay of native ISO9141 receive fragments/status events."""
import sys
sys.dont_write_bytecode=True
from .protocol import require

class ResponseAssembler:
    def __init__(self,request):
        self.request=request;self.data=bytearray();self.indicators=0;self.pieces=0;self.complete=False
    def consume(self,message):
        require(not self.complete,'No receive after complete response')
        self.pieces+=1;require(self.pieces<=527,'Bounded RX message count')
        require(message['protocol']==3 and message.get('tx_flags',0)==0,'Protocol/flags')
        raw=bytes.fromhex(message['data_hex']);status=message.get('rx_status',0)
        require(len(raw)<=523 and message.get('extra',len(raw)) in (0,len(raw)),'RX extra-data bounds')
        if status:
            self.indicators+=1;require(not self.data and self.indicators<=4,'Status only before response data')
            if status in (2,8):require(not raw,'Nonempty status indication unqualified')
            elif status in (1,9):require(raw==self.request,'Exact TX echo only')
            else:raise ValueError('Unknown/error RX status')
            return None
        require(raw and len(self.data)+len(raw)<=523,'Empty/oversized RX data')
        self.data.extend(raw)
        prefix=b'\xBE\xEF' if self.request[0]==0xBE else b'\x80\xF0\x10'
        count=min(len(prefix),len(self.data));require(self.data[:count]==prefix[:count],'RX prefix/direction')
        if len(self.data)<4:return None
        length=int.from_bytes(self.data[2:4],'big') if self.request[0]==0xBE else self.data[3]
        require(1<=length<=(518 if self.request[0]==0xBE else 255),'Declared response length')
        require(len(self.data)<=length+5,'Trailing/duplicate response bytes')
        self.complete=len(self.data)==length+5
        return bytes(self.data) if self.complete else None
