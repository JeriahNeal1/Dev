"""Straight-line constant construction search over all decoded words, including unlabelled code.

Join/branch/call boundaries discard state. Unknown opcodes discard all constants. This is
an additional positive-evidence search, explicitly not a complete abstract interpreter.
"""
import json, collections
from pathlib import Path
OUT=Path(__file__).parent
rom=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
raw={r['ea']:r for r in json.loads((OUT.parent/'ida/raw_decodable_code.json').read_text())}
reach=json.loads((OUT/'reachability.json').read_text());seen=set(reach['all_functions']['reached'])
targets=set(reach['all_functions']['roots'])
for x in reach['all_functions']['resolved_transfers']:targets.update(x['targets'])
def sx(x,n):return x-(1<<n) if x&(1<<(n-1)) else x
def hole(x):return 'provisional' if 0xCE754<=x<0xFFAF8 else 'alternative' if 0x859BC<=x<0xC0000 else None
for pc,row in raw.items():
    w=row['word']
    if w>>12 in (10,11):targets.add(pc+4+2*sx(w&4095,12))
    if w&0xff00 in (0x8900,0x8b00,0x8d00,0x8f00):targets.add(pc+4+2*sx(w&255,8))
regs=[None]*16;origins=[[] for _ in range(16)];derived=[];accesses=[];unknown=collections.Counter();previous=-4
def assign(n,value,origin):
    regs[n]=None if value is None else value&0xffffffff;origins[n]=origin
for pc,row in sorted(raw.items()):
    if pc!=previous+2 or pc in targets:regs=[None]*16;origins=[[] for _ in range(16)]
    previous=pc;w=row['word'];n=w>>8&15;m=w>>4&15;done=True
    if w>>12 in (9,13):
        a=pc+4+2*(w&255) if w>>12==9 else ((pc+4)&~3)+4*(w&255)
        v=sx(int.from_bytes(rom[a:a+2],'big'),16) if w>>12==9 else int.from_bytes(rom[a:a+4],'big')
        assign(n,v,[pc,a,pc])
    elif w>>12==14:assign(n,sx(w&255,8),[pc])
    elif w>>12==7:assign(n,regs[n]+sx(w&255,8) if regs[n] is not None else None,origins[n]+[pc])
    elif w&0xf00f==0x6003:assign(n,regs[m],origins[m]+[pc])
    elif w&0xf00f in (0x300c,0x3008,0x200b,0x2009,0x200a):
        a,b=regs[n],regs[m]
        f={0x300c:lambda:a+b,0x3008:lambda:a-b,0x200b:lambda:a|b,0x2009:lambda:a&b,0x200a:lambda:a^b}[w&0xf00f]
        assign(n,f() if a is not None and b is not None else None,origins[n]+origins[m]+[pc])
    elif w&0xf00f in (0x600c,0x600d,0x600e,0x600f):
        v=regs[m];kind=w&15
        assign(n, None if v is None else v&255 if kind==12 else v&65535 if kind==13 else sx(v&255,8) if kind==14 else sx(v&65535,16),origins[m]+[pc])
    elif w&0xf0ff in (0x4000,0x4001,0x4008,0x4009,0x4018,0x4019,0x4028,0x4029):
        low=w&255;bits={0:1,1:1,8:2,9:2,0x18:8,0x19:8,0x28:16,0x29:16}[low];v=regs[n]
        assign(n,None if v is None else v>>bits if low&1 else v<<bits,origins[n]+[pc])
    elif w&0xff00 in (0xc900,0xca00,0xcb00):
        v=regs[0];f={0xc900:lambda:v&(w&255),0xca00:lambda:v^(w&255),0xcb00:lambda:v|(w&255)}[w&0xff00]
        assign(0,None if v is None else f(),origins[0]+[pc])
    elif w&0xf00f in (0x6000,0x6001,0x6002,0x6004,0x6005,0x6006):
        if regs[m] is not None and hole(regs[m]):accesses.append({'pc':pc,'address':regs[m],'kind':'read','origins':origins[m],'reachable':pc in seen})
        if w&4:assign(m,None,[])
        assign(n,None,[])
    elif w&0xf00f in (0x2000,0x2001,0x2002):
        if regs[n] is not None and hole(regs[n]):accesses.append({'pc':pc,'address':regs[n],'kind':'write','origins':origins[n],'reachable':pc in seen})
    elif w==9 or w&0xf00f in (0x3000,0x3002,0x3003,0x3006,0x3007,0x2008) or w&0xff00==0xc800:pass
    else:
        if pc in seen:unknown[f'{w:04X}']+=1
        regs=[None]*16;origins=[[] for _ in range(16)];done=False
    if done:
        for reg,v in enumerate(regs):
            if v is not None and hole(v) and origins[reg] and origins[reg][-1]==pc:
                derived.append({'pc':pc,'reg':reg,'value':v,'origins':origins[reg],'reachable':pc in seen,'defined':row['defined']})
out={'derived_hole_values':derived,'concrete_hole_accesses':accesses,'unmodelled_reachable_opcodes':dict(unknown),
 'scope':__doc__}
(OUT/'immediate_propagation.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'derived_count':len(derived),'reachable_derived':[x for x in derived if x['reachable']],
 'reachable_accesses':[x for x in accesses if x['reachable']],'unmodelled_opcodes':len(unknown)},indent=2))
