"""Standalone experimental payload only; no ROM overlay or device tool."""
from pathlib import Path
from hashlib import sha256
import subprocess,json,sys
SRC=Path(__file__).parent
ROOT=Path('C:/Dev/Astra_A2WC511R')
OUT=ROOT/'reports/local/m07_residency/protocol/one_page_01'
TOOL=Path('C:/Program Files (x86)/Renesas/Hew/Tools/KPIT/GNUSH-ELF/v13.01/sh-elf/bin')
def main():
 assert not OUT.exists(),'Use a fresh output directory';OUT.mkdir(parents=True)
 commands=[]
 def run(name,args):
  argv=[str(x) for x in args];p=subprocess.run(argv,capture_output=True,text=True,timeout=60)
  (OUT/(name+'.log')).write_text(json.dumps(argv)+'\n'+p.stdout+'\n'+p.stderr)
  commands.append({'argv':argv,'exit':p.returncode});assert p.returncode==0,name
 run('assemble',[TOOL/'sh-elf-as.exe','-big','-renesas','--isa=sh2e',SRC/'one_page.s','-o',OUT/'payload.o'])
 run('link',[TOOL/'sh-elf-ld.exe','-EB','-T',SRC/'one_page.ld',OUT/'payload.o','-o',OUT/'payload.elf'])
 run('extract',[TOOL/'sh-elf-objcopy.exe','-O','binary','-j','.m07',OUT/'payload.elf',OUT/'payload.bin'])
 run('disassembly',[TOOL/'sh-elf-objdump.exe','-d','-t','-h',OUT/'payload.elf'])
 result={'status':'RESEARCH_PAYLOAD_NOT_OWNERSHIP_APPROVED','bytes':(OUT/'payload.bin').stat().st_size,'VMA':0x42A4,
  'no_persistent_ram':True,'added_stack_bytes':8,'no_refill_hook':True,
  'request_without_checksum_hex':'8010F014BE10FF4C75FF4C8DFF4CA1FF4C50FF4BC1FF4BC2',
  'response_opcode':0xFC,'version':1,'page':0,'raw_response_bytes':6,
  'control_flow_contract':'Only OEM default484B0, T=0, R13=request,R14=flags,R12=len,R11=response;R2/R3 dead until484BC/C0',
  'commands':commands,'sources':{p.name:sha256(p.read_bytes()).hexdigest() for p in SRC.iterdir() if p.is_file()},
  'artifacts':{p.name:sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()}}
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','bytes','added_stack_bytes','no_refill_hook')}))
if __name__=='__main__':main()
