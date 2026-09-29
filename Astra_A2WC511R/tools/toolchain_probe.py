"""Compile/link/disassemble a NON-FIRMWARE SH-2E smoke object with installed GNUSH.
Only generated diagnostic files under --out are touched. No HEW phases or vehicle I/O.
"""
from __future__ import annotations
import argparse,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
from audit_dev import elf_header,file_meta

def probe(cc:Path,out:Path):
 cc=cc.resolve();out=out.resolve();out.mkdir(parents=True,exist_ok=True)
 if not cc.is_file():raise ValueError('GNUSH compiler not found')
 suffix='.exe' if cc.suffix.lower()=='.exe' else ''
 ld=cc.with_name('sh-elf-ld'+suffix);objdump=cc.with_name('sh-elf-objdump'+suffix)
 if not ld.is_file() or not objdump.is_file():raise ValueError('Need matching sh-elf-ld and sh-elf-objdump next to compiler')
 source=out/'smoke_not_firmware.c';obj=out/'smoke_not_firmware.o';linked=out/'smoke_linked_not_firmware.o'
 source.write_text('volatile float smoke_value;\nfloat smoke(float x, float y) { smoke_value = x*y+1.0f; return smoke_value; }\n',encoding='ascii')
 for p in (obj,linked):
  if p.exists():p.unlink() # Only our two regenerable smoke artifacts.
 commands=[[str(cc),'--version'],[str(cc),'-m2e','-mrenesas','-mieee','-ffreestanding','-fno-builtin','-nostdinc','-O1','-c',str(source),'-o',str(obj)],
           [str(ld),'-r',str(obj),'-o',str(linked)],[str(objdump),'-dr',str(linked)]]
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'toolchain_ready':False,'commands':[],
         'warning':'This smoke object is NOT an ECU firmware image and proves neither target hooks nor memory allocation.'}
 for i,cmd in enumerate(commands):
  p=subprocess.run(cmd,cwd=out,capture_output=True,text=True,errors='replace',timeout=90)
  log=out/f'command_{i:02d}.txt';log.write_text('ARGV: '+json.dumps(cmd)+'\nEXIT: '+str(p.returncode)+'\n'+p.stdout+'\nSTDERR:\n'+p.stderr,encoding='utf-8')
  report['commands'].append({'argv':cmd,'returncode':p.returncode,'log':str(log)})
  if p.returncode:report['error']='Tool command failed; see '+str(log);break
 else:
  h=elf_header(linked);report['elf']=h
  report['toolchain_ready']=h.get('class_bits')==32 and h.get('byte_order')=='big' and h.get('machine')==42 and h.get('sh_machine_nibble')==11
  if not report['toolchain_ready']:report['error']='Expected ELF32 big endian EM_SH SH2E object'
 report['compiler']=file_meta(cc,cc.parent)
 (out/'toolchain_probe.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cc',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 r=probe(a.cc,a.out);print(json.dumps(r,indent=2));raise SystemExit(0 if r['toolchain_ready'] else 2)
if __name__=='__main__':main()
