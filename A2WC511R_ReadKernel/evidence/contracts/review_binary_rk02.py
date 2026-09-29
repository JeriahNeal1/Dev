"""Independent fixed-object structural/store review; no execution or providers.

This review fails on a changed instruction/object. Its domain annotations are
proved by the documented straight-line definitions and loop inductions, not by
a no-literal-reference search or sampled peripheral execution.
"""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,re,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=0xFFFF3000
EXPECTED='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'

def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def sx(v,n):return v-(1<<n) if v&(1<<(n-1)) else v

def review(build):
    manifest=json.loads((build/'manifest.json').read_text())
    raw=(build/'kernel.bin').read_bytes()
    elf=(build/'kernel.elf').read_bytes()
    assert elf[:7]==b'\x7fELF\x01\x02\x01' and int.from_bytes(elf[18:20],'big')==42
    assert int.from_bytes(elf[36:40],'big')==11
    digest=hashlib.sha256(raw).hexdigest()
    # The review below is address-specific and must not silently approve a new build.
    assert digest==manifest['kernel_sha256']==EXPECTED
    symbols={}
    for line in (build/'kernel.symbols.txt').read_text().splitlines():
        if m:=re.fullmatch(r'([0-9a-fA-F]+)\s+\S\s+(.+)',line):symbols[m[2]]=int(m[1],16)
    assert (symbols['kernel_entry'],symbols['code_end'],symbols['const_pool_start'],symbols['upload_end'],symbols['work_end'])==(0xFFFF3004,0xFFFF32A2,0xFFFF32A4,0xFFFF3710,0xFFFF3730)
    dis={}
    for line in (build/'kernel.disassembly.txt').read_text().splitlines():
        if m:=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{2}) ([0-9a-f]{2})\s+(.+)',line):
            pc=int(m[1],16)
            if symbols['kernel_entry']<=pc<symbols['code_end']:
                op=int(m[2]+m[3],16);assert raw[pc-BASE:pc-BASE+2]==op.to_bytes(2,'big')
                dis[pc]=(op,m[4].strip())
    assert list(dis)==list(range(symbols['kernel_entry'],symbols['code_end'],2))
    def code(a):return a in dis
    stores=[];loads=[];edges=[];calls=[];literal=[];writes={str(n):[] for n in range(16)}
    allowed={'mov','mov.b','mov.w','mov.l','extu.b','ldc','tst','bt','bf','bra','bsr','nop','cmp/eq','and','or','dt','add','xor','shll8','rts','sts','lds','shlr8','shlr16'}
    for pc,(op,assembly) in dis.items():
        mnemonic=assembly.split()[0];assert mnemonic in allowed,(hex(pc),assembly)
        n,m=(op>>8)&15,(op>>4)&15
        isstore=(op&0xF00F in (0x2000,0x2001,0x2002)) or op&0xFF00==0x8000
        if isstore:stores.append(pc)
        if op&0xF00F in (0x6000,0x6001,0x6002,0x6004) or op&0xFF00==0x8400:loads.append(pc)
        if op>>12==0xD:
            address=((pc+4)&~3)+(op&255)*4
            assert symbols['const_pool_start']<=address<symbols['vector_table']
            literal.append({'pc':f'{pc:08X}','address':f'{address:08X}','value':f'{int.from_bytes(raw[address-BASE:address-BASE+4],"big"):08X}'})
        if op>>12 in (0xA,0xB):
            target=(pc+4+2*sx(op&4095,12))&0xFFFFFFFF
            assert code(target) and code(pc+2)
            assert dis[pc+2][0]==0x0009,(hex(pc),'Non-NOP direct branch delay slot requires explicit review')
            edges.append((pc,target,'call' if op>>12==0xB else 'branch'))
            if op>>12==0xB:calls.append((pc,target))
        elif op&0xFF00 in (0x8900,0x8B00):
            target=pc+4+2*sx(op&255,8)
            assert code(target) and code(pc+2);edges.extend(((pc,target,'conditional'),(pc,pc+2,'fallthrough')))
        elif op==0x000B:
            assert code(pc+2)
        elif pc not in {p+2 for p,(o,_) in dis.items() if o>>12 in (0xA,0xB) or o==0xB}:
            assert code(pc+2),(hex(pc),'Code falls into constants')
        # Exclude all computed branch forms and all memory forms absent our review.
        assert op&0xF0FF not in (0x400B,0x402B,0x0003,0x0023)
        assert not (op>>12 in (1,0xF) or op&0xF00F in (0x2004,0x2005,0x2006,0x0004,0x0005,0x0006))
        dest=[]
        if op>>12 in (0xD,0xE,0x7):dest=[n]
        elif op>>12==6:
            dest=[n]
            if op&15==4 and m!=n:dest.append(m)
        elif op&0xF00F in (0x300C,0x2009,0x200B):dest=[n]
        elif op&0xF0FF in (0x4010,0x4018,0x4019,0x4029,0x002A):dest=[n]
        elif op&0xFF00 in (0xC900,0xCA00,0xCB00,0x8400):dest=[0]
        for d in dest:writes[str(d)].append(f'{pc:08X}')
    exact_stores={
      0xFFFF3016:(2,0xFFFFECB0,0xFFFFECB2,'DMAOR constant0'),
      0xFFFF3028:(2,0xFFFFEC10,0xFFFFEC12,'WDT constantA518'),
      0xFFFF3052:(4,0xFFFF3710,0xFFFF3730,'R1 starts3710, stride4, equalend3730 exit: exactly8 aligned writes'),
      0xFFFF305E:(4,0xFFFF3718,0xFFFF371C,'constant low guard'),
      0xFFFF3062:(4,0xFFFF372C,0xFFFF3730,'constant high guard'),
      0xFFFF3070:(1,0xFFFFF012,0xFFFFF013,'SCR0'),
      0xFFFF3072:(1,0xFFFFF010,0xFFFFF011,'SMR0'),
      0xFFFF3076:(1,0xFFFFF016,0xFFFFF017,'SDCRF2'),
      0xFFFF307A:(1,0xFFFFF011,0xFFFFF012,'BRR9'),
      0xFFFF3086:(2,0xFFFFF73C,0xFFFFF73E,'PCCR(read&0155)|0050'),
      0xFFFF3092:(1,0xFFFFF014,0xFFFFF015,'SSR observed&C7'),
      0xFFFF30A0:(1,0xFFFFF014,0xFFFFF015,'SSR observed&BF'),
      0xFFFF30A4:(1,0xFFFFF012,0xFFFFF013,'SCR10'),
      0xFFFF30F8:(1,0xFFFF3710,0xFFFF3718,'R5 fixedRXstart, R6 only1/8 afterlength guard, stride1; calleerx preservesR4..R14'),
      0xFFFF3196:(1,0xFFFFF012,0xFFFFF013,'SCR0 afterTEND'),
      0xFFFF31A0:(1,0xFFFFF012,0xFFFFF013,'SCR0 on failure'),
      0xFFFF31D2:(1,0xFFFFF014,0xFFFFF015,'SSR snapshot&BF'),
      0xFFFF31EC:(1,0xFFFFF013,0xFFFFF014,'TDR low byte R4'),
      0xFFFF31F2:(1,0xFFFFF014,0xFFFFF015,'SSR observed&7F'),
      0xFFFF3202:(1,0xFFFFF012,0xFFFFF013,'SCR20 disables receiver before response; residualSSR78 checked beforefirstTDR'),
      0xFFFF3278:(1,0xFFFFF012,0xFFFFF013,'SCR10 only after every-frame TEND drain returns'),
      0xFFFF329C:(1,0xFFFFF012,0xFFFFF013,'SCR0 on exception')}
    assert set(stores)==set(exact_stores)
    # Exact definitions close the persistent register-domain induction.
    assert writes['8']==['FFFF3064','FFFF3174','FFFF3180']
    assert writes['9']==['FFFF3066','FFFF3182']
    assert writes['10']==['FFFF3068','FFFF3128']
    assert writes['11']==['FFFF306A','FFFF312A','FFFF316C']
    assert writes['14']==['FFFF31FC']
    assert writes['15']==['FFFF3004','FFFF3296']
    assert all(t in (symbols['check_guards'],symbols['rx_byte'],symbols['tx_byte'],symbols['tx_frame'],symbols['drain_tx']) for _,t in calls)
    assert raw[symbols['vector_table']-BASE:symbols['upload_checksum_word']-BASE]==symbols['exception_handler'].to_bytes(4,'big')*256
    assert len(raw)==1808 and sum(struct.unpack('>452I',raw))&65535==0x5AA5
    assert len(dis)==335
    # Exact half-duplex transition and status guards; delay slots are explicit.
    echo_anchors={0xFFFF3200:0xE020,0xFFFF3202:0x8012,0xFFFF3204:0x8414,
                  0xFFFF3206:0xC878,0xFFFF3208:0x8901,0xFFFF3276:0xE010,
                  0xFFFF3278:0x8012,0xFFFF3284:0x8414,0xFFFF3286:0xC804,
                  0xFFFF3288:0x8B03,0xFFFF328A:0x4310,0xFFFF328C:0x8BFA,
                  0xFFFF3292:0x000B,0xFFFF3294:0x0009}
    for pc,op in echo_anchors.items():assert dis[pc][0]==op
    assert (0xFFFF3270,symbols['drain_tx']) in calls
    assert not any(0xFFFF3274<=t<0xFFFF3280 and k!='fallthrough' for _,t,k in edges)
    assert raw[symbols['identity_body']-BASE:symbols['identity_body']-BASE+15]==b'\x81A2WC511R-RK02\x00'
    domains=[{'pc':f'{pc:08X}','instruction':dis[pc][1],'width':v[0],
              'destination_range':[f'{v[1]:08X}',f'{v[2]:08X}'],'argument':v[3]} for pc,v in exact_stores.items()]
    report={'schema':1,'status':'PASS_FIXED_BINARY_STRUCTURAL_STORE_AND_CONTROL_CONTRACT',
      'inputs':[pin(build/n) for n in ('manifest.json','kernel.bin','kernel.elf','kernel.disassembly.txt','kernel.symbols.txt')]+[pin(Path(__file__))],
      'kernel_sha256':digest,'instruction_count':len(dis),'store_count':len(stores),'store_domains':domains,
      'target':{'ISA':'SH-2E','ELF_class':32,'endian':'big','e_machine':42,'e_flags':11},
      'RAM_store_sites':4,'MMIO_store_sites':18,
      'literal_loads':literal,'all_GPR_definition_sites':writes,
      'direct_calls':[{'pc':f'{p:08X}','target':f'{t:08X}'} for p,t in calls],
      'all_direct_edges':[{'pc':f'{p:08X}','target':f'{t:08X}','kind':k} for p,t,k in edges],
      'nonliteral_load_sites':[{'pc':f'{p:08X}','instruction':dis[p][1]} for p in loads],
      'ROM_read_induction':{'load_site':'FFFF3260','pointer_setup':'FFFF325C R5=R8;FFFF325E R6=512',
        'R8_initial':0,'R8_increment':512,'R8_increment_site':'FFFF3174',
        'R8_postincrement_limit':'FFFF3178 compares00100000, branches before next request',
        'R8_reset_site':'FFFF3180','admitted_bases':'00000000,00000200,...,000FFE00',
        'R9_passes':[0,1],'R9_2_means_terminal':True,
        'request_cannot_set_R8':'AddressdecodeR2 mustequalR8 at315C; no assignment fromhostR2 intoR8',
        'R5_byte_load_range':[0,1048576],
        'alternative_identity_load':'Same3260 site reads exactly15 immutable bytes[FFFF32FC,FFFF330B),selectedonlyr11=0.'},
      'RAM_read_contract':'Only zeroed privateRX/guard words and immutable literal/identity bytes; no inheritedFFFF5444. Firmware does not read its exception stack.',
      'call_graph':{'main':['check_guards','rx_byte','tx_frame'],'tx_frame':['tx_byte','drain_tx'],'check_guards':[],'rx_byte':[],'tx_byte':[],'drain_tx':[],'exception_handler':[]},
      'return_proof':'Leaves do not alterPR; tx_frame savesPR once inR14, nestedtx_byte preservesR14, LDSR14PR beforeRTS; abnormaledgeshalt insteadofreturn.',
      'software_stack_bytes':0,'single_hardware_exception_stack_bytes':8,
      'private_stack':['FFFF371C','FFFF372C'],
      'stack_limit':'Exceptionhandler resetsSP beforequiet; arbitrary successiveNMI beforethatinstruction notbounded. PreprivateSP/VBRtransition outsideclaim.',
      'MMIO_writes':['FFFFECB0 word0','FFFFEC10 wordA518','FFFFF010 byte0','FFFFF011 byte9','FFFFF012 byte0/10/20','FFFFF013 byteTX','FFFFF014 byteflags','FFFFF016 byteF2','FFFFF73C wordmask0155/set0050'],
      'flash_stores':0,'prohibited_accesses':0,'computed_executable_calls':0,'external_OEM_calls':0,
      'RX_wait':'Unbounded polling, read-only afterinitialization; hostdeadline/powerreset boundary. No sessionwallclockupperbound.',
      'TX_wait':'65536 polling iterations maximum at31DC; every-frame TEND drain3284 same budget; each timeout writesSCR0 thenhalts.',
      'half_duplex_contract':{'TX_receiver_disable':'SCR20 at3202 occurs before any tx_byte call.',
        'residual_input':'AfterRE0, readSSR3204 andtestmask78 at3206; anyRDRF/ORER/FER/PER reachesfatal beforefirstTDR. NoRDRdrain hides extra bytes.',
        'frame_drain':'Finalchecksum tx_byte returns to3270, which callsdrain_tx3280. OnlyobservedTEND1 returns; timeout goesfatal.',
        'RX_restore':'SCR10 at3278 is reachable onlyafterdrain_tx returns; TE0/RE1 selects receive-only. No direct branch enters3274..327E.',
        'PR':'tx_frame saves incomingPR inR14. tx_byte anddrain_tx never writeR14; LDSR14PR at327A precedesRTS.',
        'remaining':'RE0 initializes an in-progress receive; software cannot attest absence of a physical byte that has not completed. Host is strictly sequential; real line turnaround remains a physical gate.'},
      'conditions':['Intact exact pinned code/constants/vectors and no asynchronous corruption.',
        'Entry/peripheral assumptions in ENTRY_PERIPHERAL_CONTRACT.json.',
        'This is static fixed-object review; actual execution coverage and UART event tests are separate simulator evidence.'],
      'physical_operations':0}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('build',type=Path);a=p.parse_args()
    report=review(a.build.resolve())
    out=HERE/'BINARY_REVIEW_rk02_01.json'
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'instructions':report['instruction_count'],'stores':report['store_count'],'kernel_sha256':report['kernel_sha256']}))
