"""Read-only audit of the user's C:\\Dev tree. Never imports or executes project code.
Only git metadata commands are run. Reports are written under --out, not the inputs.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, struct, subprocess
from datetime import datetime, timezone
from pathlib import Path
import project_core

PINNED = {
 'MerpMod':'8720d209df107a81fd171131cfba96d8cae1f118',
 'SharpTune':'ecabea89615132dac2de37c05f72adae16d966d1',
 'SubaruDefs':'9b2992eba8133fe5338b89aa77b22c1bb14d6507',
}
BASELINE='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'

def file_meta(path: Path, root: Path) -> dict:
 return {'path':path.relative_to(root).as_posix(), 'size':path.stat().st_size,
         'sha256':project_core.sha256(path)}

def macros(path: Path) -> dict:
 if not path.is_file(): return {}
 out={}
 for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
  m=re.match(r'\s*#define\s+(\w+)\s+(.+)',line)
  if m:out[m[1]]=m[2].strip()
 return out

def elf_header(path: Path) -> dict:
 data=path.read_bytes()
 if len(data)<52 or data[:4]!=b'\x7fELF':return {'elf':False}
 cls,enc=data[4],data[5]
 if cls!=1 or enc not in (1,2):return {'elf':True,'class':cls,'encoding':enc,'supported_parser':False}
 e='>' if enc==2 else '<'
 typ,mach,ver,entry,pho,sho,flags,hs,phes,phn,shes,shn,shstr=struct.unpack_from(e+'HHIIIIIHHHHHH',data,16)
 return {'elf':True,'class_bits':32,'byte_order':'big' if enc==2 else 'little',
         'type':typ,'machine':mach,'entry':hex(entry),'flags':hex(flags),
         'sh_machine_nibble':flags&0x1f,'program_headers':phn,'section_headers':shn,
         'warning':'Architecture metadata only. Metadata/simulator sections are not a 1MiB flash image.'}

def git_info(repo: Path) -> dict:
 if not (repo/'.git').exists():return {'present':repo.exists(),'git_metadata':False}
 if not shutil.which('git'):return {'present':True,'error':'git not on PATH'}
 def run(*args):
  p=subprocess.run(['git','-c','core.autocrlf=true','-C',str(repo),*args],capture_output=True,text=True,errors='replace',timeout=90)
  return {'rc':p.returncode,'text':p.stdout.strip(),'stderr':p.stderr.strip()}
 return {'present':True,'head':run('rev-parse','HEAD'), 'describe':run('describe','--tags','--long','--always'),
         'semantic_diff_names':run('diff','--ignore-space-at-eol','--name-only'),
         'semantic_diff_stat':run('diff','--ignore-space-at-eol','--stat'),
         'untracked':run('ls-files','--others','--exclude-standard'),
         'note':'core.autocrlf override avoids treating the Windows CRLF checkout as a wholesale code rewrite. No git reset/clean is used.'}

def audit(root: Path) -> dict:
 root=root.resolve()
 if not root.is_dir():raise ValueError('Dev directory not found: '+str(root))
 report={'schema':1,'generated_at':datetime.now(timezone.utc).isoformat(),'root':str(root),
         'vehicle':'2005 USDM Outback XT 5EAT','calid':'A2WC511R','ecu_id':'2F12515306',
         'repositories':{},'roms':[],'executables':[],'idb_files':[],'generated_build':{},'findings':[]}
 for name,pin in PINNED.items():
  r=git_info(root/name);r['upload_expected_head']=pin
  r['matches_upload_head']=r.get('head',{}).get('text')==pin
  report['repositories'][name]=r
 romdir=root/'SubaruRoms'
 if romdir.is_dir():
  for p in sorted(romdir.rglob('*')):
   if not p.is_file():continue
   if p.suffix.lower()=='.bin' and p.stat().st_size==project_core.ROM_SIZE:
    r=project_core.rom_audit(p);r['file']=p.relative_to(root).as_posix();report['roms'].append(r)
   elif p.suffix.lower() in ('.i64','.idb','.id0','.id1','.nam','.til'):
    report['idb_files'].append(file_meta(p,root))
 for rel in ('MerpMod/SharpTune.exe','SharpTune/SharpTune.exe'):
  p=root/rel
  if p.is_file():report['executables'].append(file_meta(p,root))
 m=root/'MerpMod'/'MerpMod';gb=report['generated_build']
 for fname in ('TargetHeader.h','TargetConfig.h','GitVersion.h'):
  p=m/fname;gb[fname]=macros(p)
  if p.is_file():gb[fname+'_file']=file_meta(p,root)
 for rel in ('Gratis_Debug/EcuHacks.gcc','Gratis_Debug/EcuHacks.gas','Gratis_Debug/MerpMod.gld','LinkerScript.txt'):
  p=m/rel
  if p.is_file():gb[rel]=p.read_text(encoding='utf-8',errors='replace')
 for rel in ('Gratis_Debug/MerpMod.x','Gratis_Debug/EcuHacks.o'):
  p=m/rel
  if p.is_file():gb[rel]={'file':file_meta(p,root),'header':elf_header(p)}
 gb['A2WC511R_target_files']=[p.relative_to(root).as_posix() for p in sorted((m/'Targets').glob('*A2WC511R*'))] if (m/'Targets').is_dir() else []
 for name in ('Gratis.h','Flash.h','Switch.h'):
  for p in m.rglob(name):
   if '.git' not in p.parts:gb[name]=macros(p);break
 target=gb.get('TargetHeader.h',{}).get('ECU_CALIBRATION_ID')
 auto=gb.get('TargetConfig.h',{}).get('AUTO_TRANS')
 if target!='A2WC511R':report['findings'].append({'id':'WRONG_TARGET','severity':'build_blocker','actual':target,'required':'A2WC511R'})
 if auto!='1':report['findings'].append({'id':'AUTO_TRANS_NOT_SET','severity':'build_blocker','actual':auto,'required':'verify 5EAT config then set AUTO_TRANS=1 in port configuration'})
 if not gb['A2WC511R_target_files']:report['findings'].append({'id':'MISSING_TARGET_FILES','severity':'port_work','detail':'No A2WC511R target header/map/linker/config in uploaded MerpMod/Targets.'})
 a=root/'SubaruRoms/OEM/A2WC511R.bin';b=root/'SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin'
 if a.is_file() and b.is_file():
  d=project_core.binary_diff(a,b);d['a']=a.relative_to(root).as_posix();d['b']=b.relative_to(root).as_posix()
  report['named_stock_comparison']=d
 report['baseline_hash_seen']=any(x['sha256']==BASELINE for x in report['roms'])
 report['findings'].extend([
  {'id':'RAM_HOLE_UNPROVEN','severity':'integration_blocker','detail':'FFFF7400 is a prior candidate, not an allocation. No absence-of-xref proof accepted.'},
  {'id':'CURRENT_FLASH_UNKNOWN','severity':'vehicle_test_blocker','detail':'The uploaded baseline identity does not identify the current modified calibration in the car.'},
  {'id':'FRESHNESS_UNPROVEN','severity':'active_control_blocker','detail':'4CA1 and 4C50:02 have not been proven to exclude stale gear data under communication failure.'},
 ])
 return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dev',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=True);r=audit(a.dev)
 (a.out/'dev_audit.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 rows=['# Read-only Dev audit','',f"CALID: {r['calid']}; ECU ID: {r['ecu_id']}",'',
       '## Findings','']
 rows += [f"- **{x['id']}** ({x['severity']}): {x.get('detail',str(x.get('actual')))}" for x in r['findings']]
 rows += ['','## ROM identities','']+[f"- `{x['file']}`: `{x['sha256']}`" for x in r['roms']]
 rows += ['','## Repository revisions','']+[f"- {n}: `{x.get('head',{}).get('text','unavailable')}`" for n,x in r['repositories'].items()]
 rows+=['','This report does not modify a ROM, certify unused memory, identify the currently flashed tune, or authorize flashing.','']
 (a.out/'dev_audit.md').write_text('\n'.join(rows),encoding='utf-8')
 print(json.dumps({'out':str(a.out),'roms':len(r['roms']),'findings':[x['id'] for x in r['findings']]},indent=2))
if __name__=='__main__':main()
