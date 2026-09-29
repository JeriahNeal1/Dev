"""Conservative, read-only whole-hole search. Never equates absence of hits to ownership."""
import json, hashlib, re, collections, xml.etree.ElementTree as ET
from pathlib import Path
OUT=Path(__file__).parent
ROOT=OUT.parents[3]
ROM=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
DB=json.loads((OUT.parent/'ida/defined_code_export.json').read_text())
CODE={r['ea']:r for r in DB['code']}
REFS=collections.defaultdict(list)
for r in DB['xrefs']:REFS[r['to']].append(r['from'])
def word(a):return int.from_bytes(ROM[a:a+2],'big')
def long(a):return int.from_bytes(ROM[a:a+4],'big')
def sx(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
def inside(x,r):return r[0]<=x<r[1]
RUNS=[]
for m in re.finditer(b'\xff{1024,}',ROM):RUNS.append([m.start(),m.end()])
HOLES={'provisional':[0xCE754,0xFFAF8],'alternative':[0x859BC,0xC0000]}
def transfer(pc):
    w=word(pc);top=w>>12
    if top in (10,11):return ('bsr' if top==11 else 'bra',pc+4+2*sx(w&0xfff,12),True)
    if w&0xff00 in (0x8900,0x8b00,0x8d00,0x8f00):return ('conditional',pc+4+2*sx(w&255,8),bool(w&0x0400))
    if w&0xf0ff in (0x400b,0x402b,0x0003,0x0023):return ('indirect_call' if w&0xf0ff in (0x400b,0x0003) else 'indirect_jump',None,True)
    if w in (0x000b,0x002b):return ('return',None,True)
    if w&0xff00==0xc300:return ('trap',None,False)
    return None
def local_constant(pc,reg,limit=24):
    # Backward within straight-line path, no branch crossing. Only definitive forms accepted.
    delta=0
    for p in range(pc-2,max(-2,pc-2*limit-2),-2):
        w=word(p);n=(w>>8)&15;m=(w>>4)&15
        if transfer(p):return None
        if w>>12==13 and n==reg:
            at=((p+4)&~3)+4*(w&255)
            return ((long(at)+delta)&0xffffffff,at,p) if at+4<=len(ROM) else None
        if w>>12==14 and n==reg:return ((sx(w&255,8)+delta)&0xffffffff,None,p)
        if w>>12==7 and n==reg:delta+=sx(w&255,8);continue
        if w&0xf00f==0x6003 and n==reg:reg=m;continue
        row=CODE.get(p)
        # Any unrecognized destination write or unknown instruction loses provenance.
        if row and row['ops'] and row['ops'][-1]['text'].lower()==f'r{reg}':return None
        if not row:return None
    return None
out={'baseline_sha256':hashlib.sha256(ROM).hexdigest(),'ida_export_sha256':hashlib.sha256((OUT.parent/'ida/defined_code_export.json').read_bytes()).hexdigest(),
 'runs':RUNS,'holes':{},'vectors':{},'reachability':{},'family_maps':[]}
for name,span in HOLES.items():
    hits={'span':span,'size':span[1]-span[0],'sha256':hashlib.sha256(ROM[span[0]:span[1]]).hexdigest(),
          'boundary_before':ROM[span[0]-128:span[0]].hex(),'boundary_after':ROM[span[1]:span[1]+128].hex(),
          'defined_code':[a for a in CODE if inside(a,span)],'xrefs':[x for x in DB['xrefs'] if inside(x['to'],span)],
          'byte_unaligned_u32':[],'even_pc_relative':[],'direct_branches':[],'immediates':[]}
    for a in range(len(ROM)-3):
        v=long(a)
        if inside(v,span):hits['byte_unaligned_u32'].append({'ea':a,'value':v,'alignment':a%4,
             'referenced_from':REFS[a]})
    for pc in range(0,len(ROM)-2,2):
        w=word(pc);value=None;at=None;kind=None
        if w>>12==13:
            at=((pc+4)&~3)+4*(w&255);kind='mov.l_pc'
            if at+4<=len(ROM):value=long(at)
        elif w>>12==9:
            at=pc+4+2*(w&255);kind='mov.w_pc'
            if at+2<=len(ROM):value=sx(word(at),16)&0xffffffff
        elif w&0xff00==0xc700:at=((pc+4)&~3)+4*(w&255);value=at;kind='mova'
        if (value is not None and inside(value,span)) or (at is not None and inside(at,span)):
            hits['even_pc_relative'].append({'pc':pc,'kind':kind,'pool':at,'value':value,'defined':pc in CODE})
        t=transfer(pc)
        if t and t[1] is not None and inside(t[1],span):hits['direct_branches'].append({'pc':pc,'kind':t[0],'target':t[1],'defined':pc in CODE})
        if pc in CODE and any(o['type']==5 and inside(o['value']&0xffffffff,span) for o in CODE[pc]['ops']):hits['immediates'].append(CODE[pc])
    out['holes'][name]=hits
out['vectors']={'reset_words':[{'at':a,'value':long(a)} for a in range(0,0x400,4)],
 'vbr_words':[{'at':a,'value':long(a)} for a in range(0xFFC50,0x100000,4)],
 'vbr_instructions':[r for r in DB['code'] if 'vbr' in (r['text'] or '').lower()],
 'checksum_descriptors':[{'at':a,'start':long(a),'end':long(a+4),'correction':long(a+8)} for a in range(0xFFB80,0xFFC28,12)]}
# Root reachability follows existing defined code refs plus raw direct transfer edges and resolved straight-line calls.
# Unknown indirect edges remain an explicit blocker, never assumed empty.
roots={long(0),long(8),long(0xFFFF8)}
roots|={long(a) for a in range(0xFFC50,0xFFFF8,4) if long(a) in CODE}
def walk(seeds):
    pending=list(seeds);seen=set();ordinary_entries=set();unresolved=[];resolved=[];outside=[];hole=[]
    while pending:
        pc=pending.pop()
        if pc in ordinary_entries:continue
        ordinary_entries.add(pc)
        seen.add(pc)
        if any(inside(pc,span) for span in HOLES.values()):hole.append(pc);continue
        if pc not in CODE:outside.append(pc);continue
        t=transfer(pc)
        if not t:pending.append(pc+2);continue
        kind,target,delay=t
        if delay:seen.add(pc+2)
        if kind=='return':continue
        if kind=='trap':unresolved.append({'pc':pc,'kind':kind});continue
        if target is not None:pending.append(target)
        if kind.startswith('indirect'):
            c=local_constant(pc,(word(pc)>>8)&15)
            if c:
                target=c[0]
                if word(pc)&0xf0ff in (0x0003,0x0023):target=(pc+4+target)&0xffffffff
                resolved.append({'pc':pc,'target':target,'pool':c[1],'load':c[2]});pending.append(target)
            else:unresolved.append({'pc':pc,'kind':kind,'text':CODE[pc]['text']})
        if kind in ('bsr','conditional','indirect_call'):pending.append(pc+4 if delay else pc+2)
    return {'roots':sorted(seeds),'seen':sorted(seen),'seen_count':len(seen),'unresolved_indirect':unresolved,'resolved_indirect':resolved,'undefined_frontier':sorted(set(outside)),'hole_entries':hole}
out['reachability']['reset_and_vectors']=walk(roots)
out['reachability']['all_defined_functions']=walk({r['start'] for r in DB['functions']}|roots)
for p in Path('C:/Dev/MerpMod/MerpMod/Targets').glob('A2WC*.h'):
    txt=p.read_text(errors='replace')
    vals={k:v for k,v in re.findall(r'#define\s+(dRomHoleStart|pRamHoleStart|dEcuId|hMemoryReset|hMemoryResetLimit)\s+\(?([^\s)]+)',txt)}
    if vals:out['family_maps'].append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'symbols':vals})
(OUT/'static_audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'holes':{name:{k:len(v) if isinstance(v,list) and k not in ('span',) else v for k,v in r.items() if k not in ('boundary_before','boundary_after')} for name,r in out['holes'].items()},
 'reachability':{k:{'seen':r['seen_count'],'unresolved':len(r['unresolved_indirect']),'undefined':len(r['undefined_frontier']),'hole_entries':r['hole_entries']} for k,r in out['reachability'].items()}},indent=2))
