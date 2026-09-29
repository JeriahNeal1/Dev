"""Classify actual reference encodings without assuming global pointer completeness."""
import json
import math
import struct
import xml.etree.ElementTree as ET
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).parent
ROM_PATH = Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin')
rom = ROM_PATH.read_bytes()
inventory = json.loads((HERE/'inbound_inventory.json').read_text())
assert sha256(rom).hexdigest() == inventory['rom_sha256']
metadata = Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\rommetadata\subaru')
xml_paths = [metadata/'Bases/32BITBASE.xml', metadata/'Legacy GT/A2WC510C.xml',
             metadata/'Outback XT/A2WC511R.xml']
base, parent, target = [ET.parse(p).getroot() for p in xml_paths]
assert target.findtext('include') == 'A2WC510C'
assert parent.findtext('include') == '32BITBASE'
scaling = {x.get('name'):x.attrib for x in base.findall('scaling')}
tables = {x.get('name'):x for x in base.findall('table')}
spans = []
for table in parent.findall('table'):
    model = tables.get(table.get('name'))
    if model is None:
        continue
    rows = [(table, model)]
    children = {x.get('name'):x for x in model.findall('table')}
    rows += [(x, children[x.get('name')]) for x in table.findall('table') if x.get('name') in children]
    for item, spec in rows:
        if not item.get('address'):
            continue
        count = int(spec.get('elements', '1'))
        if item is table:
            count = math.prod(int(x.get('elements', '1')) for x in model.findall('table'))
        scale = scaling.get(spec.get('scaling'), {})
        size = {'float':4, 'uint32':4, 'uint16':2, 'uint8':1}.get(scale.get('storagetype'))
        if size:
            start = int(item.get('address'), 16)
            spans.append(dict(start=start, end=start+count*size, storage=scale['storagetype'],
                name=table.get('name')+'/'+item.get('name'), count=count))

def word(a):
    return int.from_bytes(rom[a:a+2], 'big')

def mova_float_read(pc):
    """Bounded straight-line audit: whitelist only non-R0-writing instructions."""
    for a in range(pc+2, pc+34, 2):
        w = word(a)
        if w & 0xF0FF == 0xF008:
            return dict(mova=f'{pc:08X}', fmov=f'{a:08X}', bytes=rom[pc:a+2].hex())
        # FMOV/arithmetic register instructions; no integer-register effect.
        fp_register = w >> 12 == 15 and ((w & 15) <= 5 or (w & 15) in (8, 12) or (w & 0xFF) in (0x8D, 0x9D))
        push = w & 0xFF0F == 0x2F06 or w & 0xFF0F == 0xFF0B
        move_not_r0 = w & 0xF00F == 0x6003 and ((w >> 8)&15) != 0
        pcload_not_r0 = w >> 12 in (9, 13) and ((w >> 8)&15) != 0
        if not (fp_register or push or move_not_r0 or pcload_not_r0 or w == 0x4F22):
            return None
    return None

classified = []
for hit in inventory['objects']['division']['pointers']:
    row = dict(address=hit['address'], value=hit['value'], alignment=hit['alignment'])
    if hit['alignment'] == 0:
        row['classification'] = 'ALIGNED_ENTRY_LITERAL'
    elif hit['alignment'] == 2:
        reads = []
        defs = []
        for aligned in hit['adjacent_aligned_words']:
            a = int(aligned['address'],16)
            reads.append([r for x in aligned['PC_accesses'] if x['kind']=='MOVA' and (r:=mova_float_read(x['pc']))])
            defs.append([s for s in spans if s['storage']=='float' and s['start']<=a and a+4<=s['end'] and (a-s['start'])%4==0])
        row['known_reads'] = reads
        row['definition_spans'] = defs
        if all(reads):
            row['classification'] = 'TWO_SEPARATELY_READ_FLOAT_LITERALS'
        elif all(defs):
            row['classification'] = 'TWO_DEFINITION_TYPED_FLOAT_ELEMENTS'
        else:
            row['classification'] = 'ALIGNED_WORD_CROSSING_NO_PROVEN_CONSUMER'
        row['aligned_words'] = [{k:v for k,v in a.items() if k!='PC_accesses'} for a in hit['adjacent_aligned_words']]
    else:
        a = int(hit['address'],16)
        row['classification'] = 'BYTE_CROSSING_NO_PROVEN_CONSUMER'
        row['surrounding_aligned_words'] = [dict(address=f'{p:08X}', value=f'{int.from_bytes(rom[p:p+4],"big"):08X}') for p in (a&~3,(a&~3)+4)]
    classified.append(row)

calls = [(0x1B250,0x1B254,0x1B330,3), (0x33E6C,0x33E72,0x33EE0,2),
         (0x483BC,0x483C2,0x484A8,3), (0x6425C,0x64260,0x64318,3),
         (0x11934,0x11936,0x11AD8,3)]
call_records=[]
for load,call,pool,reg in calls:
    assert word(load)>>12==13 and ((word(load)>>8)&15)==reg
    assert ((load+4)&~3)+4*(word(load)&255)==pool
    assert word(call)==0x400B+reg*256
    call_records.append(dict(load=f'{load:08X}',call=f'{call:08X}',pool=f'{pool:08X}',
        target=f'{int.from_bytes(rom[pool:pool+4],"big"):08X}',register=reg,
        through_delay_slot=rom[load:call+4].hex()))

out = dict(rom_sha256=sha256(rom).hexdigest(), counts=dict(Counter(r['classification'] for r in classified)),
    calls=call_records, hits=classified, definitions=[dict(path=str(p),sha256=sha256(p.read_bytes()).hexdigest()) for p in xml_paths],
    scope='Typed definitions and exact MOVA/FMOV fragments explain particular ordinary data uses. They do not exclude arbitrary bytewise reconstruction or unknown calculated control.',
    ownership='FAIL_UNRESOLVED_CALCULATED_ENTRY_AND_INTERNAL_READ_CONSUMERS')
(HERE/'classified_uses.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out['counts'],indent=2))
