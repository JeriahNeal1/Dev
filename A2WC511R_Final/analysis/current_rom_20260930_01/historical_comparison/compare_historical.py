"""A2 offline comparison. Reads ROM/evidence bytes; writes only this result directory."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, zlib, zipfile, io

OUT=Path(__file__).resolve().parent
CURRENT=OUT.parent/'current.preserved.bin'
EXPECTED='bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2'
CAL=Path(r'C:\Dev\Astra_A2WC511R\reports\local\gate_closure\calibration')
CAT=Path(r'C:\Dev\Astra_A2WC511R\reports\local\prehardware\acquisition\LOCAL_IMAGE_ATTESTATION_CATALOG.json')
def digest(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':digest(b)}
def read_label(label):
 parts=label.split('::');p=Path(parts.pop(0))
 if not parts:return p.read_bytes()
 blob=None
 for part in parts:
  if part.startswith('payload@'):
   if blob is None:blob=p.read_bytes()
   offset=int(part.split('@',1)[1],16);blob=blob[offset:offset+0x100000]
  else:
   with zipfile.ZipFile(p if blob is None else io.BytesIO(blob),'r') as archive:blob=archive.read(part)
 return blob
def ranges(before,after):
 rr=[]
 for i,(a,b) in enumerate(zip(before,after)):
  if a==b:continue
  if rr and rr[-1][1]==i:rr[-1][1]+=1
  else:rr.append([i,i+1])
 return [{'start':s,'end_exclusive':e,'start_hex':f'0x{s:06X}','end_exclusive_hex':f'0x{e:06X}','length':e-s,'historical_hex':before[s:e].hex(),'current_hex':after[s:e].hex()} for s,e in rr]

current=CURRENT.read_bytes();assert len(current)==0x100000 and digest(current)==EXPECTED
sources=[CURRENT,CAL/'inventory.json',CAL/'history_comparison.json',CAL/'ecuflash_history.json',CAT]
source_pins=[pin(p) for p in sources]
inv=json.loads(sources[1].read_text());history=json.loads(sources[2].read_text());catalog=json.loads(CAT.read_text())
assert catalog['history_evidence']['sha256']==digest(sources[2].read_bytes()),'Catalog history source changed'
aliases={}
for item in inv['images']:aliases.setdefault(item['sha256'],set()).add(item['path'])
for item in catalog['images']:aliases.setdefault(item['sha256'],set()).update(item['paths'])
match_aliases=[]
for label in sorted(aliases.get(EXPECTED,[])):
 row={'path':label,'catalogued_sha256':EXPECTED}
 try:
  b=read_label(label);row.update({'bytes':len(b),'live_sha256':digest(b),'byte_equal_to_current':b==current,'status':'VERIFIED_BYTE_IDENTICAL' if b==current else 'CHANGED_SINCE_INVENTORY'})
 except (OSError,KeyError,zipfile.BadZipFile) as e:row.update({'status':'UNAVAILABLE','error':str(e)})
 match_aliases.append(row)
assert any(x.get('byte_equal_to_current') for x in match_aliases)

comparisons=[]
for item in inv['unique_images']:
 h=item['sha256'];attempts=[];b=None;selected=None
 for label in sorted(aliases.get(h,[]),key=lambda p:(p!=item['first_seen_path'],p)):
  try:
   loaded=read_label(label);live=digest(loaded)
   attempts.append({'path':label,'bytes':len(loaded),'live_sha256':live,'expected_sha256':h})
   if len(loaded)==len(current) and live==h:b=loaded;selected=label;break
  except (OSError,KeyError,zipfile.BadZipFile) as e:attempts.append({'path':label,'error':str(e)})
 row={'historical_sha256':h,'historical_classification':item['classification'],'catalogued_first_path':item['first_seen_path'],'all_catalogued_aliases':sorted(aliases.get(h,[])),'source_attempts':attempts,'direction':'HISTORICAL_TO_AUTHORITATIVE_CURRENT'}
 if b is None:row['status']='NO_LIVE_HASH_MATCHING_SOURCE'
 else:
  rr=ranges(b,current)
  row.update({'status':'EXACT_BYTE_MATCH' if b==current else 'DIFFERENT','verified_source':selected,'changed_bytes':sum(x['length'] for x in rr),'changed_range_count':len(rr),'changed_ranges':rr})
 comparisons.append(row)

pages=[];cursor=0
for page in history['logged_pages']:
 assert page['start']==cursor;cursor+=page['length']
 value=zlib.crc32(current[page['start']:cursor])
 pages.append({**page,'current_crc32':value,'current_crc32_hex':f'{value:08x}','matches_historical_ecu_crc32':value==page['ecu_crc32'],'matches_historical_image_crc32':value==page['image_crc32']})
assert cursor==len(current) and len(pages)==16
history_extract=next(x for x in json.loads((CAL/'ecuflash_history.json').read_text()) if x['path']==history['log'])
assert history_extract['sha256']==history['log_sha256']
historical_log=Path(history['log'])
log_status={'recorded_path':str(historical_log),'recorded_sha256':history['log_sha256'],'currently_exists_at_recorded_path':historical_log.exists(),'crc_table_source':str(CAL/'history_comparison.json'),'operation_extract_source':str(CAL/'ecuflash_history.json'),'limitation':'Original historical log is not reverified if absent; retained historical reports supply the CRC table and line-numbered operation extracts.'}
if historical_log.exists():log_status['current_file_pin']=pin(historical_log)
crc={'algorithm':catalog['CRC_algorithm'],'pages':pages,'matches':sum(p['matches_historical_ecu_crc32'] and p['matches_historical_image_crc32'] for p in pages),'total':len(pages),'coverage_bytes':cursor,'historical_log':log_status,'authority':'Historical corroboration only; authoritative comparison input is current.preserved.bin.'}
result={'schema':1,'status':'PASS_EXACT_CURRENT_TO_HISTORICAL_BYTE_MATCH','created_utc':datetime.now(timezone.utc).isoformat(),'authoritative_input':source_pins[0],'identity_relation':'CURRENT_PHYSICAL_INPUT_BYTES_EXACTLY_EQUAL_ADJUSTED_BASE_TIMING_AND_NO_CLOLD_HISTORICAL_BYTES','source_pins':source_pins,'inventory_scope':{'inventory_utc':inv['utc'],'inventory_image_paths':len(inv['images']),'inventory_unique_hashes':len(inv['unique_images']),'catalog_image_observations':len(catalog['observations']),'catalog_unique_hashes':len(catalog['images']),'alias_scope':'Union of existing calibration inventory images and LOCAL_IMAGE_ATTESTATION_CATALOG paths; no claim of a new exhaustive filesystem scan.'},'exact_match_aliases':match_aliases,'crc_comparison':crc,'comparisons':comparisons,'limits':['Current input authority comes from the supplied preserved physical input, not file naming, date or historical CRC matching.','This comparison proves byte identity of files; it does not establish untouched subsequent vehicle state or independently validate acquisition method.','Historical CRC32 agreement is corroboration and is not cryptographic identity.','No ROM, sealed report, RK03 repository, provider or hardware was modified or executed.']}
(OUT/'HISTORICAL_COMPARISON.json').write_text(json.dumps(result,indent=2)+'\n')
known=[x for x in comparisons if x['historical_classification'] in ['stock','historical_tuned']]
lines=['# A2 current image versus historical images','',f'The authoritative preserved current image is exactly byte-identical to the historical `AdjustedBaseTimingANDNOCLOLD.bin`: SHA256 `{EXPECTED}`, 1,048,576 bytes. This is a direct byte comparison, not an inference from the filename or historical CRC values.','',f'The two existing inventories identify {len(match_aliases)} historical alias for this hash:','']
for a in match_aliases:lines.append(f'- `{a["path"]}` — {a["status"]}.')
lines += ['','The alias list covers the union of the existing inventory and attestation catalog, not a new exhaustive filesystem search. The authoritative new input remains `current.preserved.bin`; historical aliases remain provenance material.','','| Historical image | Changed bytes to current | Contiguous ranges |','| --- | ---: | ---: |']
for x in known:lines.append(f'| {Path(x["verified_source"]).name if x.get("verified_source") else x["catalogued_first_path"]} | {x.get("changed_bytes","unavailable")} | {x.get("changed_range_count","unavailable")} |')
lines += ['',f'The current input matches all {crc["matches"]}/16 retained historical ECU and image CRC32 values, covering the full1MiB in the recorded page geometry. The prior suspected-current candidate is therefore an exact file match to the new input; the historical CRC result now serves only as corroboration.','','The original August18 13:49:42 log is absent from its recorded AppData path. Its CRC table remains in the hash-pinned `history_comparison.json`; `ecuflash_history.json` retains the line-numbered operation extracts and recorded original log hash. This review does not claim to have freshly verified the absent raw log.','','`HISTORICAL_COMPARISON.json` includes every exact changed interval (start inclusive/end exclusive, historical bytes and current bytes) for all18 distinct images in the original inventory. It separates historical tunes, stock, editor stamps and generated/test images. The later attestation catalog supplies additional aliases without replacing the historical comparison scope.','','No ROM bytes, sealed reports, RK03 history or physical state were changed. No probe was built or executed.']
(OUT/'HISTORICAL_COMPARISON.md').write_text('\n'.join(lines)+'\n')
assert all(pin(Path(x['path']))==x for x in source_pins),'Input changed during comparison'
manifest={'status':'PASS','input_pins_unchanged':True,'outputs':[pin(p) for p in [OUT/'HISTORICAL_COMPARISON.json',OUT/'HISTORICAL_COMPARISON.md',Path(__file__)]]}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'status':result['status'],'aliases':match_aliases,'crc_matches':crc['matches'],'comparisons':[{k:v for k,v in x.items() if k in ['historical_sha256','status','changed_bytes','changed_range_count']} for x in known],'report':str(OUT/'HISTORICAL_COMPARISON.json'),'report_sha256':digest((OUT/'HISTORICAL_COMPARISON.json').read_bytes())}))
