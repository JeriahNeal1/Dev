"""Read-only complete raw-literal/defined-code inventory for exact M0 RAM span.
Raw decodability and literal absence never certify unreferenced ownership.
"""
from pathlib import Path
import collections,hashlib,json,struct,subprocess
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
OUT=Path(__file__).resolve().parent
ROMFILE=Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin')
EXPORT=ROOT/'reports/local/gate_closure/ida/defined_code_export.json'
START,END=0xffff7400,0xffff7420
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 r=ROMFILE.read_bytes();assert sha(r)=='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
 d=json.loads(EXPORT.read_text());code={i['ea']:i for i in d['code']}
 assert all(i['word']==int.from_bytes(r[i['ea']:i['ea']+2],'big') for i in d['code'])
 literal_refs=[];immediate_words=[];pointers=collections.defaultdict(list)
 for ea in range(len(r)-3):
  val=int.from_bytes(r[ea:ea+4],'big')
  if 0xffff0000<=val<0xffffc000:pointers[val].append(ea)
 for ea in range(0,len(r)-2,2):
  w=int.from_bytes(r[ea:ea+2],'big')
  if w>>12==13:
   pool=((ea+4)&~3)+(w&255)*4
   if pool+4>len(r):continue
   val=int.from_bytes(r[pool:pool+4],'big')
   if val>=0xffff0000:
    literal_refs.append(dict(ea=ea,pool=pool,value=val,reg=(w>>8)&15,defined=ea in code,function=code.get(ea,{}).get('function')))
  elif w>>12==9:
   pool=ea+4+(w&255)*2
   if pool+2>len(r):continue
   v=int.from_bytes(r[pool:pool+2],'big');val=v|0xffff0000 if v&0x8000 else v
   if val>=0xffff8000 or 0x7000<=val<=0x8000:
    immediate_words.append(dict(ea=ea,pool=pool,value=val,reg=(w>>8)&15,defined=ea in code,function=code.get(ea,{}).get('function')))
 ranges={'candidate':(START,END),'nearby':(0xffff7000,0xffff8000),'dma':(0xffffecb0,0xffffed00),'ram_emulation':(0xffffec26,0xffffec28),'flash_download':(0xffffe800,0xffffe840)}
 groups={n:{'long_literal_loads':[x for x in literal_refs if a<=x['value']<b],'word_literal_loads':[x for x in immediate_words if a<=x['value']<b],
            'xrefs':[x for x in d['xrefs'] if a<=x['to']<b]} for n,(a,b) in ranges.items()}
 special=[x for x in d['code'] if 'gbr' in x['text'].lower() or 'vbr' in x['text'].lower() or (x['ops'] and x['ops'][-1]['text']=='r15')]
 functions={x['start']:x for x in d['functions']}
 report={'baseline_sha256':sha(r),'defined_export_sha256':sha(EXPORT.read_bytes()),'defined_code_heads':len(code),'defined_code_bytes':len(code)*2,
  'conservative_executable_envelope':[0,0x859bc],'defined_coverage_fraction':len([a for a in code if a<0x859bc])*2/0x859bc,
  'required_span':[START,END],'required_bytes':END-START,'literal_pointers_all_byte_alignments':{hex(k):v for k,v in sorted(pointers.items())},
  'groups':groups,'all_ram_or_mmio_literal32_loads':literal_refs,'all_peripheral_or_nearby_literal16_loads':immediate_words,
  'special_register_instructions':special,'referencing_functions':{hex(k):functions[k] for k in functions if any(x.get('function')==k for g in groups.values() for x in g['long_literal_loads']+g['word_literal_loads'])},
  'limitations':['defined IDA code excludes substantial executable intervals','raw scans include data-decoded phantom instructions','constant pointer loads do not exhaust indirect address arithmetic or aliases','all negative results are search observations, never sole ownership proof']}
 (OUT/'static_inventory.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'defined_code_heads':len(code),'coverage':report['defined_coverage_fraction'],'groups':{n:{k:len(v) for k,v in g.items()} for n,g in groups.items()},'functions':len(report['referencing_functions'])}))
if __name__=='__main__':main()
