"""Extract two separate research fragments, never flatten their ELF gap."""
from pathlib import Path
from hashlib import sha256
import subprocess,json
SRC=Path(__file__).parent;ROOT=Path('C:/Dev/Astra_A2WC511R')
OUT=ROOT/'reports/local/m07_residency/protocol/two_pages_01'
TOOLS=Path('C:/Program Files (x86)/Renesas/Hew/Tools/KPIT/GNUSH-ELF/v13.01/sh-elf/bin')
def main():
 assert not OUT.exists();OUT.mkdir(parents=True);commands=[]
 def run(label,args):
  args=[str(x) for x in args];p=subprocess.run(args,capture_output=True,text=True,timeout=60)
  (OUT/(label+'.log')).write_text(json.dumps(args)+'\n'+p.stdout+'\n'+p.stderr)
  commands.append({'argv':args,'exit':p.returncode});assert p.returncode==0,label
 run('assemble',[TOOLS/'sh-elf-as.exe','-big','-renesas','--isa=sh2e',SRC/'two_pages.s','-o',OUT/'payload.o'])
 run('link',[TOOLS/'sh-elf-ld.exe','-EB','-T',SRC/'two_pages.ld',OUT/'payload.o','-o',OUT/'payload.elf'])
 spans=[]
 for label,base in [('match',0x42A4),('main',0x14770)]:
  run('extract_'+label,[TOOLS/'sh-elf-objcopy.exe','-O','binary','-j','.m07_'+label,OUT/'payload.elf',OUT/(label+'.bin')])
  data=(OUT/(label+'.bin')).read_bytes();spans.append({'name':label,'start':base,'end_exclusive':base+len(data),'bytes':len(data),'sha256':sha256(data).hexdigest()})
 run('disassembly',[TOOLS/'sh-elf-objdump.exe','-d','-t','-h',OUT/'payload.elf'])
 m={'status':'RESEARCH_FRAGMENTS_NOT_OWNERSHIP_APPROVED','fragments':spans,'payload_bytes':sum(x['bytes'] for x in spans),
  'persistent_ram_bytes':0,'additional_adapter_stack_bytes':8,'uses_existing_A8_producer':True,'no_refill_hook':True,
  'pages':[{'page':0,'version':1,'request_without_checksum':'8010F00EBE10FF4C75FF4C8DFF4CA1FF4C50','response_opcode':0xFC,'data_bytes':4},
           {'page':1,'version':1,'request_without_checksum':'8010F008BE11FF4BC1FF4BC2','response_opcode':0xFD,'data_bytes':2}],
  'commands':commands,'sources':{p.name:sha256(p.read_bytes()).hexdigest() for p in SRC.iterdir() if p.is_file()},
  'artifacts':{p.name:sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()}}
 (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({k:m[k] for k in ('status','fragments','payload_bytes')}))
if __name__=='__main__':main()
