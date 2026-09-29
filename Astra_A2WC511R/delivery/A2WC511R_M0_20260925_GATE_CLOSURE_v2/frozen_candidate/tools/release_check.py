"""Check a candidate's identity, full-file diff allowlist and evidence hashes.
This is an evidence-envelope validator, NOT an ECU checksum implementation or safety certification.
Required review documents are hash-linked; their engineering conclusions still need review.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from project_core import ROM_SIZE,sha256

REQUIRED_REVIEWS=('baseline_provenance','calibration_compatibility','rom_allocation','ram_allocation',
 'hook_abi_and_timing','feature_closure','checksum_verification','reproducible_build','human_test_plan')

def under(root:Path, name:str)->Path:
 p=(root/name).resolve()
 if not p.is_relative_to(root.resolve()) or not p.is_file():raise ValueError('Missing/outside evidence file: '+name)
 return p

def number(v):return int(v,0) if isinstance(v,str) else int(v)

def check(manifest:dict,root:Path)->dict:
 errors=[];evidence=[]
 if manifest.get('target_calid')!='A2WC511R' or manifest.get('target_ecuid')!='2F12515306':errors.append('Incorrect target identity')
 if manifest.get('scope')!='diagnostic_only':errors.append('This first-run release contract only accepts diagnostic_only')
 def verified_file(desc):
  p=under(root,desc['path']);h=sha256(p)
  if h!=desc['sha256'].lower():raise ValueError('Hash mismatch: '+desc['path'])
  return p
 try:
  a=verified_file(manifest['baseline']);b=verified_file(manifest['candidate']);x=a.read_bytes();y=b.read_bytes()
  if len(x)!=ROM_SIZE or len(y)!=ROM_SIZE:raise ValueError('Both ROMs must be exactly 1,048,576 bytes')
  if x[0x2000:0x2008]!=b'A2WC511R' or x[0xCDAD8:0xCDADD]!=bytes.fromhex('2F12515306'):errors.append('Baseline ROM identity mismatch')
  identity=manifest.get('expected_output_identity',{})
  if y[0x2000:0x2008].decode('ascii',errors='replace')!=identity.get('calid'):errors.append('Output CALID mismatch')
  if y[0xCDAD8:0xCDADD].hex().upper()!=identity.get('ecuid','').upper():errors.append('Output ECU ID mismatch')
  allowed=bytearray(ROM_SIZE)
  ranges=manifest.get('allowed_changes',[])
  if not ranges:errors.append('No reviewed change ranges')
  for r in ranges:
   lo,hi=number(r['start']),number(r['end_exclusive'])
   if not 0<=lo<hi<=ROM_SIZE:raise ValueError('Invalid range')
   if not r.get('purpose') or not r.get('review_key'):raise ValueError('Missing range purpose/review linkage')
   if r['review_key'] not in REQUIRED_REVIEWS:raise ValueError('Invalid review key')
   if any(allowed[lo:hi]):raise ValueError('Overlapping allowlist ranges; consolidate explicitly')
   if hashlib.sha256(x[lo:hi]).hexdigest()!=r['baseline_range_sha256'].lower():raise ValueError('Original-byte range hash mismatch')
   allowed[lo:hi]=b'\x01'*(hi-lo)
  changed=[i for i,(old,new) in enumerate(zip(x,y)) if old!=new]
  if not changed:errors.append('Candidate is a no-op; not a completed source port')
  outside=[i for i in changed if not allowed[i]]
  if outside:errors.append('Changed bytes outside reviewed ranges: '+', '.join(hex(i) for i in outside[:20]))
  reviews=manifest.get('reviews',{})
  for name in REQUIRED_REVIEWS:
   if name not in reviews:errors.append('Missing review: '+name);continue
   p=verified_file(reviews[name])
   if p.stat().st_size<40:errors.append('Review is empty/placeholder: '+name)
   evidence.append({'key':name,'path':reviews[name]['path'],'sha256':reviews[name]['sha256']})
  result={'baseline_sha256':sha256(a),'candidate_sha256':sha256(b),'changed_bytes':len(changed),'outside_allowlist':len(outside)}
 except (KeyError,ValueError,OSError,TypeError) as e:
  errors.append(str(e));result={}
 return {'schema':1,'envelope_passed':not errors,'errors':errors,'evidence':evidence,**result,
         'status':'OFFLINE_ENVELOPE_CHECKS_PASSED_HUMAN_REVIEW_REQUIRED' if not errors else 'NOT_RELEASED',
         'not_checked_here':['Actual SH execution on ECU','Engineering truth of review conclusions','Runtime RAM/stack coexistence','Physical vehicle readiness'],
         'warning':'Passing this tool is not permission to flash and does not prove checksum correctness; it only hash-links the separate checksum review.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 r=check(json.loads(a.manifest.read_text(encoding='utf-8-sig')),a.root.resolve());a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2));raise SystemExit(0 if r['envelope_passed'] else 2)
if __name__=='__main__':main()
