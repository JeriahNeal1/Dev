"""Read-only byte/encoding regression; no whole-firmware ownership assumption."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).parent
rom=Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin').read_bytes()
assert sha256(rom).hexdigest()=='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
checks=[]
def expect(name,condition):
    assert condition,name
    checks.append(dict(name=name,status='PASS'))

def inbound(blob,lo,hi):
    branches=[]; reads=[]; calls=[]
    for a in range(0,len(blob)-1,2):
        w=int.from_bytes(blob[a:a+2],'big')
        target=None
        if w>>12 in (10,11):
            d=w&4095;d=d-4096 if d&2048 else d
            target=a+4+2*d
        elif w&0xFF00 in (0x8900,0x8B00,0x8D00,0x8F00):
            d=w&255;d=d-256 if d&128 else d
            target=a+4+2*d
        if target is not None and lo<=target<hi and not lo<=a<hi:
            branches.append(a)
        if w>>12==13:ptr=((a+4)&~3)+4*(w&255);size=4
        elif w>>12==9:ptr=a+4+2*(w&255);size=2
        elif w&0xFF00==0xC700:ptr=((a+4)&~3)+4*(w&255);size=1
        else:ptr=None;size=0
        if ptr is not None and ptr<hi and lo<ptr+size and not lo<=a<hi:
            reads.append(a)
        is_call = w>>12==11 or w&0xF0FF in (0x400B,0x0003)
        if is_call and lo<=a+4<hi and not lo<=a<hi:
            calls.append(a)
    return dict(branches=branches,pc_reads=reads,external_call_returns=calls)

scans={}
for name,lo,hi in [('division',0x4260,0x430A),('range_enclosure',0x1466E,0x147AC),('range_changed',0x1473C,0x147AC)]:
    scans[name]=inbound(rom,lo,hi)
    expect(name+'_no_external_direct_branch',not scans[name]['branches'])
    if name!='range_enclosure':expect(name+'_no_external_PC_read',not scans[name]['pc_reads'])
    expect(name+'_no_external_call_return_created_inside',not scans[name]['external_call_returns'])

# Exact known call setup bytes include the original delay slot.
calls={0x1B250:'d33760ec430b6143',0x33E6C:'d21c2c01d01a420b6183',
       0x483BC:'d33a610c71fe430be003',0x6425C:'d32e611c430be005',0x11934:'d368430b0009'}
for a,h in calls.items():expect(f'call_{a:X}',rom[a:a+len(h)//2]==bytes.fromhex(h))
for a in [0x1B330,0x33EE0,0x484A8,0x64318]:expect(f'pool_{a:X}',rom[a:a+4]==bytes.fromhex('00004260'))
expect('range_pool_entry',rom[0x11AD8:0x11ADC]==bytes.fromhex('0001466e'))
expect('range_R6_dominator',rom[0x1466E:0x14670]==bytes.fromhex('e640'))
expect('range_mask_seed',rom[0x1473A:0x1473C]==bytes.fromhex('e00f'))
expect('odd_hit_spans_data_words',rom[0x8289C:0x828A4]==bytes.fromhex('00000043000823ea'))
expect('division_preserved_old_literals',rom[0x430A:0x4314]==bytes.fromhex('0009ffff130c0000044e'))

# External direct BRA into the candidate must become a detected frontier.
b=bytearray(rom);site=0x4240;dest=0x42A4;w=0xA000|(((dest-site-4)//2)&4095);b[site:site+2]=w.to_bytes(2,'big')
expect('negative_added_direct_entry_detected',site in inbound(b,0x4260,0x430A)['branches'])
# External PC-relative long load that overlaps a tail must become a detected reader.
b=bytearray(rom);site=0x4240;dest=0x42A4;w=0xD000|((dest-((site+4)&~3))//4);b[site:site+2]=w.to_bytes(2,'big')
expect('negative_added_PC_reader_detected',site in inbound(b,0x4260,0x430A)['pc_reads'])
# JSR just before an object would manufacture an interior return PC.
b=bytearray(rom);b[0x425E:0x4260]=bytes.fromhex('430b')
expect('negative_external_call_return_detected',0x425E in inbound(b,0x4260,0x430A)['external_call_returns'])

semantic=HERE.parent/'semantic'
manifest=json.loads((semantic/'candidate_manifest.json').read_text())
objects=manifest.get('candidates',manifest.get('objects',{}))
if not objects:
    objects={k:v for k,v in manifest.items() if isinstance(v,dict) and 'binary_sha256' in v}
for name,obj in objects.items():
    if not isinstance(obj,dict) or 'binary_sha256' not in obj:continue
    for key in ['source','binary','elf']:
        expect(name+'_'+key+'_unchanged',sha256(Path(obj[key]).read_bytes()).hexdigest()==obj[key+'_sha256'])
(HERE/'verification.json').write_text(json.dumps(dict(status='PASS',checks=checks,scans=scans,
    proof_scope='Finite raw encoding and exact known call/constant invariants. Does not constrain unknown register-computed transfers.',
    stock_sha256=sha256(rom).hexdigest()),indent=2)+'\n')
print('PASS',len(checks),'checks')
