"""Independent byte/layout/reproducibility checks for the temporary RAM object."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
PIN='3d70abfb8617b87e1b9c52724fd27ed4066ba231818994e780c8ba3006de273f'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':Path(p).stat().st_size}

def verify(manifest,repro):
    m=json.loads(Path(manifest).read_text());r=json.loads(Path(repro).read_text())
    p=Path(m['kernel_path']);b=p.read_bytes();s=m['symbols'];errors=[]
    def check(name,condition):
        if not condition:errors.append(name)
    check('hash_pin',sha(p)==m['kernel_sha256']==r['kernel_sha256']==PIN)
    check('class',m['artifact_class']=='TEMP_RAM_ACQUISITION_TOOL' and m['ECU_flash_image'] is False)
    check('target',m['target']=={'cpu':'SH-2E','mcu':'SH7058','endian':'big','ELF_flags':11})
    check('upload_size',len(b)==1776 and m['kernel_bytes']==1776)
    check('entry',m['load_address']==0xffff3000 and m['entry']==0xffff3004)
    check('loader_checksum',sum(struct.unpack('>444I',b))&0xffff==0x5aa5)
    check('header',b[:4]==bytes.fromhex('00090009'))
    check('repro_binary',b==Path(r['kernel_path']).read_bytes())
    elf=p.with_suffix('.elf');re=p.parent.parent/Path(r['kernel_path']).parent.name/'kernel.elf'
    check('repro_ELF',elf.read_bytes()==re.read_bytes())
    eb=elf.read_bytes()
    check('ELF_architecture',eb[:6]==b'\x7fELF\x01\x02' and struct.unpack_from('>H',eb,18)[0]==42
          and struct.unpack_from('>I',eb,24)[0]==0xffff3004 and struct.unpack_from('>I',eb,36)[0]==11)
    for name,h in m['sources'].items():check('source:'+name,sha(ROOT/name)==h==r['sources'].get(name))
    for name,t in m['toolchain'].items():check('tool:'+name,sha(t['path'])==t['sha256']==r['toolchain'][name]['sha256'])
    expected=list(range(0xffff3004,s['code_end'],2))
    check('complete_instruction_map',len(expected)==319 and expected==m['instruction_addresses']==[x['address'] for x in m['instructions']])
    for ins in m['instructions']:
        a=ins['address']-0xffff3000
        check('opcode:'+hex(ins['address']),struct.unpack_from('>H',b,a)[0]==ins['opcode'])
    check('complete_vectors',b[s['vector_table']-0xffff3000:s['vector_table']-0xffff3000+1024]==struct.pack('>I',s['exception_handler'])*256)
    check('identity',b[s['identity_body']-0xffff3000:s['identity_body']-0xffff3000+15]==b'\x81A2WC511R-RK01\0')
    spans=[('skipped_header',0xffff3000,0xffff3004,False),('instructions',0xffff3004,s['code_end'],False),
      ('instruction_alignment',s['code_end'],s['const_pool_start'],False),
      ('constants',s['const_pool_start'],s['identity_body'],False),
      ('identity',s['identity_body'],s['identity_body']+15,False),
      ('data_alignment',s['identity_body']+15,s['vector_table'],False),
      ('private_vectors',s['vector_table'],s['upload_checksum_word'],False),
      ('loader_integrity_word',s['upload_checksum_word'],s['upload_end'],False),
      ('RX_buffer',s['work_start'],s['guard_low'],True),('low_guard',s['guard_low'],s['stack_low'],True),
      ('exception_stack',s['stack_low'],s['stack_top'],True),('high_guard',s['guard_high'],s['work_end'],True)]
    check('contiguous_layout',all(a<b and (i==0 or a==spans[i-1][2]) for i,(_,a,b,_) in enumerate(spans)))
    check('RAM_bounds',spans[0][1]==0xffff3000 and spans[-1][2]==0xffff3710 and spans[-1][2]<=0xffff5000)
    check('working_RAM',m['private_ram_ranges']==[[0xffff36f0,0xffff3710]] and m['stack_low']==0xffff36fc and m['stack_high']==0xffff370c)
    check('protocol',m['protocol']['commands']==[1,3] and m['protocol']['passes']==2 and m['protocol']['block_bytes']==512
          and m['protocol']['ROM_range']==[0,0x100000] and m['protocol']['CRC_substitution'] is False and m['protocol']['strict_sequential'] is True)
    return {'schema':1,'status':'PASS' if not errors else 'FAIL','artifact_class':'TEMP_RAM_ACQUISITION_TOOL',
      'kernel_sha256':sha(p),'errors':errors,'inputs':[ref(Path(manifest)),ref(Path(repro)),ref(p),ref(elf),ref(Path(__file__))],
      'uploaded_bytes':1776,'takeover_bytes':1808,'private_work_bytes':32,'software_stack_bytes':0,
      'single_exception_stack_bytes':8,'reserved_stack_bytes':16,
      'ranges':[{'role':n,'start':f'{a:08X}','end_exclusive':f'{e:08X}','bytes':e-a,'writable_after_entry':w} for n,a,e,w in spans],
      'no_unaccounted_bytes':True,'byte_reproducibility':True,'ELF_reproducibility':True,
      'physical_operations':False,'limitations':['Layout ownership is a temporary OEM RAM takeover; it is not concurrent OEM residency.',
      'No claim that repeated NMI arrivals before the handler first instruction fit the bounded exception contract.',
      'Exact compiled hash and an additive loader checksum do not establish intact physical RAM after transfer.']}

if __name__=='__main__':
    out=ROOT/'evidence/build';out.mkdir(parents=True,exist_ok=True)
    result=verify(ROOT/'build/attempt_03/manifest.json',ROOT/'build/reproducibility_01/manifest.json')
    (out/'ARTIFACT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'errors':result['errors'],'report':str(out/'ARTIFACT_REVIEW.json')}))
    raise SystemExit(bool(result['errors']))
