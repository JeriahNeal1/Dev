"""Independent bounded inbound-use audit. Does not approve global ownership."""
import json
import struct
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).parent
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
rom=Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin').read_bytes()
assert sha256(rom).hexdigest()=='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
dbpath=ROOT/'reports/local/gate_closure/ida/defined_code_export.json'
db=json.loads(dbpath.read_text())
code={r['ea']:r for r in db['code']}
sx=lambda v,n:v-(1<<n) if v&(1<<(n-1)) else v
hx=lambda v:f'{v:08X}'
word=lambda a:int.from_bytes(rom[a:a+2],'big')
pc_refs={}
branches=[]
for a in range(0,len(rom)-2,2):
    w=word(a)
    if w>>12==13: target=((a+4)&~3)+4*(w&255); size=4; kind='MOV.L'
    elif w>>12==9: target=a+4+2*(w&255); size=2; kind='MOV.W'
    elif w&0xFF00==0xC700: target=((a+4)&~3)+4*(w&255); size=0; kind='MOVA'
    else: target=None
    if target is not None:
        pc_refs.setdefault(target,[]).append(dict(pc=a,size=size,kind=kind,defined=a in code))
    target=None
    if w>>12 in (10,11): target=a+4+2*sx(w&4095,12)
    elif w&0xFF00 in (0x8900,0x8B00,0x8D00,0x8F00):target=a+4+2*sx(w&255,8)
    if target is not None: branches.append(dict(pc=a,target=target,word=f'{w:04X}',defined=a in code))

def window(a,radius=8):
    return [dict(pc=hx(p),word=f'{word(p):04X}',text=code[p]['text'],function=hx(code[p]['function']) if code[p]['function'] is not None else None)
            for p in range(max(0,a-radius)&~1,min(len(rom),a+radius+2),2) if p in code]

objects={}
for name,entry,lo,hi,tail in [('division',0x4260,0x4260,0x430A,0x42A4),
                              ('range_tail',0x1466E,0x1473C,0x147AC,0x14770)]:
    full_lo=entry
    hits=[]
    for a in range(len(rom)-3):
        value=int.from_bytes(rom[a:a+4],'big')
        if not full_lo<=value<hi: continue
        if a%4==0:
            category='aligned_pointer_candidate'
        elif a in code and a+2 in code:
            category='overlaps_two_defined_instructions'
        elif a%4==2:
            category='straddles_aligned_words'
        else:
            category='byte_unaligned_unclassified'
        row=dict(address=hx(a),value=hx(value),alignment=a%4,category=category,
                 points_into_changed_span=value>=lo,points_into_tail=value>=tail,
                 direct_PC_accesses=pc_refs.get(a,[]),instruction_window=window(a,4))
        if a%4==2 and 2<=a<len(rom)-6:
            aligned=[a-2,a+2]
            row['adjacent_aligned_words']=[dict(address=hx(p),hex=rom[p:p+4].hex(),
                   float32=struct.unpack('>f',rom[p:p+4])[0],PC_accesses=pc_refs.get(p,[])) for p in aligned]
        hits.append(row)
    inbound=[b for b in branches if full_lo<=b['target']<hi and not full_lo<=b['pc']<hi]
    internal=[b for b in branches if full_lo<=b['target']<hi and full_lo<=b['pc']<hi]
    data_access=[dict(address=hx(a),references=refs) for a,refs in pc_refs.items()
                 if any(a<hi and a+max(r['size'],1)>lo and not full_lo<=r['pc']<hi for r in refs)]
    pools=[]
    for hit in hits:
        a=int(hit['address'],16)
        if a%4:continue
        loads=[]
        for ref in pc_refs.get(a,[]):
            p=ref['pc']
            loads.append(dict(**ref,window=window(p,12)))
        pools.append(dict(address=hit['address'],target=hit['value'],loads=loads))
    external_xrefs=[dict(source=hx(x['from']),target=hx(x['to']),type=x['type'],code=x['code'])
         for x in db['xrefs'] if full_lo<=x['to']<hi and not full_lo<=x['from']<hi]
    objects[name]=dict(entry=hx(entry),changed_span=[hx(lo),hx(hi)],tail=[hx(tail),hx(hi)],
        full_function_code=[dict(pc=hx(a),word=f'{word(a):04X}',text=code[a]['text']) for a in range(entry,hi,2) if a in code],
        pointers=hits,pointer_category_counts=dict(Counter(r['category'] for r in hits)),
        aligned_pools=pools,external_encoded_branches=inbound,internal_encoded_branches=internal,
        external_PC_accesses=data_access,external_exported_xrefs=external_xrefs,
        gate='FAIL_UNIVERSAL_OWNERSHIP_NOT_ESTABLISHED')
out=dict(rom_sha256=sha256(rom).hexdigest(),IDA_export_sha256=sha256(dbpath.read_bytes()).hexdigest(),objects=objects,
        note='Every raw encoded branch/PC-relative match is retained with defined-code classification. Matching encodings in data are not promoted to executed instructions.')
(HERE/'inbound_inventory.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
for name,obj in objects.items():
    print(name,json.dumps({k:obj[k] for k in ('entry','changed_span','tail','pointer_category_counts','aligned_pools','external_exported_xrefs')},indent=2))
