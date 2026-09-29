"""Concrete installed RomRaider model extents, ECUFlash inheritance and family map evidence."""
import json, hashlib, re, xml.etree.ElementTree as ET
from pathlib import Path
OUT=Path(__file__).parent
snapshot=Path('C:/Dev/Astra_A2WC511R/reports/local/interfaces/native_snapshot.json')
ss=json.loads(snapshot.read_text());rows=[];overlaps=[]
holes=[(0x859BC,0xC0000),(0xCE754,0xFFAF8)]
for t in ss['tables']:
    width={0:0,1:1,2:2,4:4,99:4}.get(t['storage_type'])
    assert width is not None,t['storage_type']
    if not width or t.get('static'):continue
    count=max([int(c['storage_index'])+1 for row in t.get('cells',[]) for c in row]+[t['rows']*t['columns']])
    # Switch preset byte spans may exceed cell count (checksum table).
    count=max([int(p.get('offset',0))+len(p.get('data',[])) for p in t.get('presets',[])]+[count])
    start=t['storage_address'];end=start+width*count
    row={'name':t['name'],'start':start,'end':end,'width':width,'count':count}
    rows.append(row)
    if any(start<b and end>a for a,b in holes):overlaps.append(row)
base=Path('C:/Dev/SubaruDefs/ECUFlash/subaru standard')
chain=[];roms={}
for p in base.rglob('*.xml'):
    root=ET.parse(p).getroot();rid=root.findtext('./romid/xmlid')
    if rid:roms[rid]=(p,root)
def visit(rid):
    p,root=roms[rid];chain.append({'id':rid,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'address_entries':[{'name':t.get('name'),'address':t.get('address'),'elements':t.get('elements')} for t in root.iter('table') if t.get('address')]})
    for node in root.findall('include'):visit(node.text.strip())
visit('A2WC511R')
family=[]
for p in Path('C:/Dev/MerpMod/MerpMod/Targets').glob('A2WC*.map'):
    relevant=[]
    for line in p.read_text(errors='replace').splitlines():
        if re.search('HoleStart|dEcuId|hMemoryReset|sMemoryReset',line):relevant.append(line.strip())
    family.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'entries':relevant})
result={'native_snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'table_extents':rows,
 'hole_overlaps':overlaps,'ecuflash_inheritance':chain,'family_maps':family,
 'limitations':'Native model reports all loaded definitions, not every undocumented OEM table; family hole labels are MerpMod annotations, not manufacturer ownership evidence.'}
(OUT/'definition_overlap.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'native_rom_backed_extents':len(rows),'hole_overlaps':overlaps,'ecuflash_chain':[c['id'] for c in chain],'family_maps':len(family)},indent=2))
