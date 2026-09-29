"""Integrated research overlays + actual OEM SSM software-event replay.

Overlay creation is not a ROM ownership assertion. No physical transport.
"""
from pathlib import Path
from hashlib import sha256
import json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=Path(__file__).parent/'execution_01'
sys.path[:0]=[str(ROOT/'integrations/m07'),'C:/Dev/A2WC511R_Sim']
from generate_stock_fixture import EventMemory
from sh2e import ROM,FunctionHarness,RAM_START
STOCK=ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin','22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218')
ADDRESSES=(0xFFFF4C75,0xFFFF4C8D,0xFFFF4CA1,0xFFFF4C50,0xFFFF4BC1,0xFFFF4BC2)
def full(prefix):
 b=bytes.fromhex(prefix);return b+bytes((sum(b)&255,))
def overlay(profile):
 sm=json.loads((OUT.parent.parent/'semantic/candidate_manifest.json').read_text())
 pm=json.loads((OUT.parent/(profile+'_01')/'manifest.json').read_text())
 fragments=[]
 for name in (['division'] if profile=='one_page' else ['division','range_tail']):
  c=sm['candidates'][name];data=Path(c['binary']).read_bytes()
  assert sha256(data).hexdigest()==c['binary_sha256']
  fragments.append((c['start'],data,'experimental replacement '+name))
 if profile=='one_page':
  fragments.append((0x42A4,(OUT.parent/'one_page_01/payload.bin').read_bytes(),'raw six adapter'))
  target=0x42A4
 else:
  for f in pm['fragments']:
   data=(OUT.parent/'two_pages_01'/(f['name']+'.bin')).read_bytes();assert sha256(data).hexdigest()==f['sha256']
   fragments.append((f['start'],data,'two-page '+f['name']))
  target=0x14770
 assert STOCK.data[0x484B0:0x484BC].hex()=='84e1cb0180e160e0c97f2e00'
 fragments.append((0x484B0,struct.pack('>HHHHI',0xD201,0x422B,9,9,target),'project default adapter'))
 result=STOCK;used=set();manifest=[]
 for a,b,label in fragments:
  span=set(range(a,a+len(b)));assert not span&used;used|=span
  manifest.append({'address':a,'before_hex':STOCK.data[a:a+len(b)].hex(),'after_hex':b.hex(),'label':label})
  result=result.with_overlay(a,b,label)
 restored=bytearray(result.data)
 for f in manifest:restored[f['address']:f['address']+len(bytes.fromhex(f['before_hex']))]=bytes.fromhex(f['before_hex'])
 assert restored==STOCK.data
 assert result.data[0x4F310:0x4F950]==STOCK.data[0x4F310:0x4F950]
 assert result.data[0x11AD8:0x11AE0]==STOCK.data[0x11AD8:0x11AE0]
 assert result.data[0xE1000:0xE1364]==STOCK.data[0xE1000:0xE1364]
 (OUT/(profile+'.RESEARCH_NOT_RESIDENCY_PROVEN.raw.bin')).write_bytes(result.data)
 (OUT/(profile+'_overlay.json')).write_text(json.dumps({'classification':'UNAPPROVED_RESEARCH_OVERLAY','rom_sha256':result.sha256,'stock_sha256':STOCK.sha256,'fragments':manifest,'inverse_exact':True,'ROM_ownership':'FAIL_PENDING_ENTRY_TAIL_CLOSURE'},indent=2))
 return result,pm
def receive(m,value,error=0):
 m.rdr=value;m.status_reads=[0xC0|error,0x80|error,0x80|error]
 h=FunctionHarness(m,[(0x47000,0x48B90),(0x2500,0x2590),(0x4200,0x4400),(0x14770,0x147AC)])
 h.cpu.track_control_sources=False
 try:r=h.run(0x47E24,allowed_writes=[(0xFFFF63E0,0xFFFF64BC)],max_steps=12000)
 except Exception:
  (OUT/'failure_trace.json').write_text(json.dumps({'pc':hex(h.cpu.pc),'trace':h.cpu.trace[-60:],'events':m.events[-60:]},indent=2));raise
 assert not m.status_reads;m.rdr=None
 return r
def exchange(rom,request,raw=bytes.fromhex('111128820101')):
 m=EventMemory(rom);m.initialize(0xFFFF63E0,bytes(0xDC))
 for a,v in zip(ADDRESSES,raw):m.initialize(a,bytes((v,)));m.watch(a,a+1,'raw','r')
 calls=[receive(m,v) for v in request];accepted=bool(m.ram[0x649A]&0x20)
 if accepted:
  m.tx.append(m.ram[0x6492])
  for _ in range(270):
   prior=bytes(m.ram[0x6408:0x6492]);calls.append(receive(m,m.tx[-1]));assert bytes(m.ram[0x6408:0x6492])==prior
   if not m.ram[0x649A]&0x20:break
  else:raise AssertionError('No one-shot completion')
 events=[e for e in m.events if not 0xFFFFBBA0<=int(e['address'],16)<0xFFFFBFA0]
 response=bytes(m.tx)
 if response:assert response[-1]==sum(response[:-1])&255
 reads=[e for e in events if e['watchpoints']]
 return {'rom_sha256':rom.sha256,'request_hex':request.hex(),'response_hex':response.hex(),'accepted':accepted,
  'raw':raw.hex(),'raw_read_addresses':[e['address'] for e in reads],
  'events':events,'events_sha256':sha256(json.dumps(events,sort_keys=True).encode()).hexdigest(),
  'calls':calls,'steps':sum(c['steps'] for c in calls),'final_SSM_hex':m.ram[0x63E0:0x64BC].hex()}
def main():
 assert not OUT.exists();OUT.mkdir(parents=True)
 profiles={};records=[];negatives=[]
 for profile in ('one_page','two_pages'):
  rom,pm=overlay(profile);profiles[profile]=rom
  pages=[{'page':0,'request_without_checksum':pm['request_without_checksum_hex'],'response_opcode':0xFC,'data_bytes':6}] if profile=='one_page' else pm['pages']
  for page in pages:
   req=full(page['request_without_checksum']);a=exchange(STOCK,req);b=exchange(rom,req)
   assert not a['accepted'] and not a['raw_read_addresses']
   raw=bytes.fromhex(b['raw']);expected=raw if profile=='one_page' else (raw[:4] if page['page']==0 else raw[4:])
   response=bytes.fromhex(b['response_hex']);assert response[4]==page['response_opcode'] and response[5:-1]==expected
   expected_addresses=ADDRESSES if profile=='one_page' else (ADDRESSES[:4] if page['page']==0 else ADDRESSES[4:])
   assert b['raw_read_addresses']==[f'{a:08X}' for a in expected_addresses],'Discarded callback resampled source'
   records.append({'profile':profile,'page':page['page'],'stock':a,'m07':b})
   for label,index,delta in [('checksum',len(req)-1,1),('version',5,0x20),('page',5,1),('address',8,1),('destination',1,2)]:
    bad=bytearray(req);bad[index]^=delta
    if label!='checksum':bad[-1]=sum(bad[:-1])&255
    a=exchange(STOCK,bytes(bad));b=exchange(rom,bytes(bad))
    assert not b['accepted'] and not b['raw_read_addresses'] and a['final_SSM_hex']==b['final_SSM_hex']
    negatives.append({'profile':profile,'page':page['page'],'case':label,'request_hex':bytes(bad).hex(),'status':'PASS_REJECTED'})
 native=full('8010F014A800FF4C75FF4C8DFF4CA1FF4C50FF4BC1FF4BC2')
 stock=exchange(STOCK,native);native_pairs=[]
 for profile,rom in profiles.items():
  candidate=exchange(rom,native);assert candidate['response_hex']==stock['response_hex'];assert candidate['final_SSM_hex']==stock['final_SSM_hex']
  writes=lambda r:[(e['address'],e['size'],e['value']) for e in r['events'] if e['mode']=='w']
  assert writes(stock)==writes(candidate)
  native_pairs.append({'profile':profile,'stock':stock,'m07':candidate})
 report={'status':'PASS_SCOPED_SOFTWARE_TRANSPORT','physical':False,'ROM_ownership_approved':False,
  'scope':'Actual OEM RX/echo/parser/dispatcher/A8 reader/TX, supplied SCIstatus; first byte fixture-released; no timer/silicon/interrupt model',
  'records':records,'negative_ingress':negatives,'native_A8_pairs':native_pairs,
  'source_prefetch':'No discarded resampling: OEM6403 counter stops after requested byte count',
  'sources':{str(p):sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('C:/Dev/A2WC511R_Sim/sh2e.py')]}}
 (OUT/'compiled_protocol_fixtures.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'valid_profiles_pages':len(records),'negative_ingress':len(negatives),'native_pairs':len(native_pairs),'raw_hashes':{n:r.sha256 for n,r in profiles.items()}}))
if __name__=='__main__':main()
