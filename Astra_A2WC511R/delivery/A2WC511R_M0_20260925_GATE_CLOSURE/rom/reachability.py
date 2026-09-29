"""Conservative raw-decode CFG frontier, with all unresolved control transfers retained."""
import json, collections
from pathlib import Path
OUT=Path(__file__).parent
rom=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
raw={r['ea']:r for r in json.loads((OUT.parent/'ida/raw_decodable_code.json').read_text())}
db=json.loads((OUT.parent/'ida/defined_code_export.json').read_text())
crefs=collections.defaultdict(set)
for x in db['xrefs']:
    if x['code'] and x['type']!=21:crefs[x['from']].add(x['to'])
def sx(v,b):return v-(1<<b) if v&(1<<(b-1)) else v
def u16(a):return int.from_bytes(rom[a:a+2],'big')
def u32(a):return int.from_bytes(rom[a:a+4],'big')
def transfer(pc):
    w=u16(pc)
    if w>>12 in (10,11):return ('call' if w>>12==11 else 'jump',pc+4+2*sx(w&4095,12),True)
    if w&0xff00 in (0x8900,0x8b00,0x8d00,0x8f00):return ('conditional',pc+4+2*sx(w&255,8),bool(w&0x400))
    if w&0xf0ff in (0x400b,0x402b,0x0003,0x0023):return ('icall' if w&0xf0ff in (0x400b,0x0003) else 'ijump',None,True)
    if w in (0x000b,0x002b):return ('return',None,True)
    if w&0xff00==0xc300:return ('trap',None,False)
joins={f['start'] for f in db['functions']}
for pc in raw:
    t=transfer(pc)
    if t and t[1] is not None:joins.add(t[1])
for refs in crefs.values():joins.update(refs)
def constant(pc,reg):
    delta=0
    for p in range(pc-2,max(-2,pc-130),-2):
        if p+2 in joins:return None
        if p not in raw or transfer(p):return None
        w=u16(p);n=(w>>8)&15;m=(w>>4)&15
        if (w&0xf00f in (0x6004,0x6005,0x6006) and m==reg) or (w&0xf00f in (0x2004,0x2005,0x2006) and n==reg):return None
        if w>>12==13 and n==reg:return ((u32(((p+4)&~3)+4*(w&255))+delta)&0xffffffff,p)
        if w>>12==9 and n==reg:return ((sx(u16(p+4+2*(w&255)),16)+delta)&0xffffffff,p)
        if w>>12==14 and n==reg:return ((sx(w&255,8)+delta)&0xffffffff,p)
        if w>>12==7 and n==reg:delta+=sx(w&255,8);continue
        if w&0xf00f==0x6003 and n==reg:reg=m;continue
        ops=raw[p]['ops']
        if ops and ops[-1]['type']==1 and ops[-1]['reg']==reg:return None
def walk(roots):
    seen=set();ordinary_entries=set();pending=list(roots);frontier=[];unknown=[];resolved=[];hole=[]
    while pending:
        pc=pending.pop()
        if pc in ordinary_entries:continue
        ordinary_entries.add(pc)
        seen.add(pc)
        if 0xCE754<=pc<0xFFAF8 or 0x859BC<=pc<0xC0000:hole.append(pc);continue
        if pc not in raw:frontier.append(pc);continue
        t=transfer(pc)
        pending.extend(crefs[pc])
        if not t:pending.append(pc+2);continue
        k,target,delay=t
        if delay:seen.add(pc+2)
        if k in ('return','trap'):
            if k=='trap':unknown.append({'pc':pc,'kind':k})
            continue
        if target is not None:pending.append(target)
        if k in ('icall','ijump'):
            c=constant(pc,(u16(pc)>>8)&15)
            targets=set(crefs[pc])
            if c:
                a=c[0]
                if u16(pc)&0xf0ff in (0x0003,0x0023):a=(pc+4+a)&0xffffffff
                targets.add(a)
            if targets:resolved.append({'pc':pc,'targets':sorted(targets),'local_constant':c});pending.extend(targets)
            else:unknown.append({'pc':pc,'kind':k,'word':u16(pc)})
        if k in ('call','icall','conditional'):pending.append(pc+4 if delay else pc+2)
    return {'roots':sorted(roots),'words_reached':len(seen),'defined_words_reached':sum(raw[p]['defined'] for p in seen if p in raw),
      'unresolved_transfers':unknown,'resolved_transfers':resolved,'undecodable_frontier':sorted(set(frontier)),
      'hole_entries':sorted(set(hole)),'reached':sorted(seen)}
roots={u32(0),u32(8),u32(0xFFFF8)}|{u32(a) for a in range(0xFFC50,0xFFFF8,4) if u32(a) in raw}
funroots=roots|{r['start'] for r in db['functions']}
# All direct PC-relative loaded executable pointers, regardless whether load is code, are an overapproximation.
proots={u32(((p+4)&~3)+4*(r['word']&255)) for p,r in raw.items() if r['word']>>12==13}
proots={a for a in proots if a in raw and a%2==0}
result={'scope':'Exploratory raw-decode CFG with extra potential roots, not a sound whole-program overapproximation. Join boundaries and implicit postincrement/predecrement invalidate local constants. Unresolved indirect targets and data accesses prevent an ownership theorem.',
 'reset_vectors':walk(roots),'all_functions':walk(funroots),'potential_pointer_roots':walk(funroots|proots)}
(OUT/'reachability.json').write_text(json.dumps(result),encoding='utf-8')
print(json.dumps({k:{'roots':len(v['roots']),'words':v['words_reached'],'unresolved':len(v['unresolved_transfers']),'frontier':len(v['undecodable_frontier']),'hole_entries':v['hole_entries']} for k,v in result.items() if isinstance(v,dict)},indent=2))
