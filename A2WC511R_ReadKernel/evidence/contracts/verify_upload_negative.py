"""Negative controls for exact stock loader; no physical transport."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from verify_upload_wire import Memory,CPU,sh,common,protocol,HERE,KERNEL

def main():
    rom=sh.ROM.load(common.STOCK,sh.STOCK_SHA256);rows=[]
    def fixture():
        m=Memory(rom);m.initialize(0xFFFFBB80,bytes(0x480));m.initialize(0xFFFFBFBA,b'\x01')
        m.write_allowlist=[(0xFFFFBB80,0xFFFFC000),(0xFFFF3000,0xFFFF5000)]
        return m
    def send(m,frame):
        before=len(m.tx);steps=0
        for b in frame:
            m.byte=b;c=CPU(m,[(0x13F6,0x1F40)],(0xFFFFBB80,0xFFFFBFA0));c.pc=0x1440;c.pr=0xFFFFFFFC;c.r[15]=0xFFFFBFA0;c.call_context=['00001440'];c.track_control_sources=False;c._set_system('sr',0xF0,{'fixture'})
            for _ in range(12000):
                c.step();steps+=1
                assert c.pc!=0xFFFF3004,'Negative control entered upload'
                if c.returned:assert c.pc==0xFFFFFFFC;break
            else:raise AssertionError('parser negative bound')
        return bytes(m.tx[before:]),steps
    declaration=protocol.declaration(8)
    cases=[('bad_declaration_checksum',declaration[:-1]+bytes([declaration[-1]^1]),b''),
           ('bad_declaration_mode',protocol.ssm(bytes.fromhex('34ff300005000008')),bytes.fromhex('7f3410')),
           ('below_RAM_floor',protocol.ssm(bytes.fromhex('34ff2ffc04000008')),bytes.fromhex('7f3422')),
           ('beyond_RAM_ceiling',protocol.ssm(bytes.fromhex('34ff4ffc04000008')),bytes.fromhex('7f3422'))]
    for name,frame,want in cases:
        m=fixture();reply,steps=send(m,frame)
        assert reply==(protocol.ssm(want,response=True) if want else b''),(name,reply.hex())
        assert not any(e['mode']=='w' and int(e['address'],16)<0xFFFFBB80 for e in m.events)
        rows.append({'case':name,'request':frame.hex(),'reply':reply.hex(),'steps':steps,'upload_stores':0})
    for name,payload,corrupt,want in [('wrong_entry_subcommand',bytes.fromhex('310102'),False,bytes.fromhex('7f3110')),('bad_upload_low16_sum',bytes.fromhex('310101'),True,bytes.fromhex('7f3122'))]:
        m=fixture();data=bytearray(KERNEL.read_bytes());data[-1]^=int(corrupt)
        m.initialize(0xFFFF3000,bytes(data));m.initialize(0xFFFFBFA0,(0xFFFF3000).to_bytes(4,'big')+(0xFFFF3000+len(data)-1).to_bytes(4,'big'));m.initialize(0xFFFFBFBA,b'\x02')
        reply,steps=send(m,protocol.ssm(payload));assert reply==protocol.ssm(want,response=True),(name,reply.hex())
        rows.append({'case':name,'reply':reply.hex(),'steps':steps,'entered':False})
    m=fixture();reply,_=send(m,declaration);assert reply==protocol.ssm(bytes.fromhex('7484'),response=True)
    block=protocol.ssm(bytes.fromhex('36ff3000')+protocol.encrypt_upload(bytes.fromhex('12345678')))
    reply,steps=send(m,block[:-1]+bytes([block[-1]^1]));assert reply==b''
    stores=[e for e in m.events if e['mode']=='w' and e['pc']=='00001646']
    assert len(stores)==1 and bytes(m.ram[0x3000:0x3004])==bytes.fromhex('12345678')
    rows.append({'case':'bad36checksum_after_stream_store','reply':'','steps':steps,'upload_stores':1,'warning':'Actual OEM commits decrypted RAM words before validating trailing frame checksum; ACK failure must terminate acquisition. This is not a flash write.'})
    out={'schema':1,'status':'PASS_NEGATIVE_CONTROLS','inputs':[common.pin(common.STOCK),common.pin(Path(__file__)),common.pin(HERE/'verify_upload_wire.py'),common.pin(KERNEL)],'cases':rows,'physical_operations':0}
    (HERE/'UPLOAD_NEGATIVE_CONTROLS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'cases':len(rows)}))
if __name__=='__main__':main()
