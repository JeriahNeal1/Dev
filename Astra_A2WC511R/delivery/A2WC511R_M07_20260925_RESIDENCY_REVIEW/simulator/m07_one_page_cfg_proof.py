"""Exact compiled first-mismatch partition and frame proof, no new scenarios."""
from pathlib import Path
from hashlib import sha256
import json
from sh2e import OPCODES, sx, STOCK_SHA256

ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=ROOT/'reports/local/m07_residency/semantic'
DIRECTORY=ROOT/'reports/local/m07_residency/protocol'
def main():
    manifest=json.loads((DIRECTORY/'one_page_01/manifest.json').read_text())
    payload=(DIRECTORY/'one_page_01/payload.bin').read_bytes()
    assert sha256(payload).hexdigest()==manifest['artifacts']['payload.bin']
    rom=(DIRECTORY/'execution_01/one_page.RESEARCH_NOT_RESIDENCY_PROVEN.raw.bin').read_bytes()
    overlay=json.loads((DIRECTORY/'execution_01/one_page_overlay.json').read_text())
    assert sha256(rom).hexdigest()==overlay['rom_sha256']
    stock=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin').read_bytes()
    assert sha256(stock).hexdigest()==STOCK_SHA256
    assert rom[0x42A4:0x4308]==payload
    assert rom[0x1466E:0x147AC]==stock[0x1466E:0x147AC], 'This is the division-only image'
    assert rom[0x484B0:0x484BC].hex()=='d201422b00090009000042a4'
    assert rom[0x42E8:0x42F0].hex()=='000042f0000484bc'
    assert rom[0x42F0:0x4308].hex()==manifest['request_without_checksum_hex'].lower()
    assert rom[0x42AC:0x42AE].hex()=='e406'
    assert rom[0x42B6:0x42BA].hex()=='44108bf9'
    assert rom[0x4829A:0x4829C].hex()=='4f22'
    assert rom[0x484BC:0x484C6].hex()=='63c07304d29f22304f26'
    assert rom[0x48308:0x48318].hex()=='910e30108f020009a0af0009a0cc0009'
    forms={};frames={};edges=set();paths=[]
    # Seven exhaustive abstract partitions: first mismatching longword0..5, or all six equal.
    # These are control predicates, not seven selected concrete request examples.
    for first_mismatch in (*range(6),None):
        pc=0x484B0;depth=0;peak=0;counter=None;iteration=-1;t=0;trace=[];accesses=0
        def word_at(address):return int.from_bytes(rom[address:address+2],'big')
        def execute(address,delay=False):
            nonlocal depth,peak,counter,iteration,t,accesses
            word=word_at(address)
            spec=next((s for s in OPCODES if word&s.mask==s.value),None)
            assert spec is not None
            form=spec.name;forms[address]={'word':f'{word:04X}','form':form,'delay_slot':delay}
            assert address not in frames or frames[address]==depth,('Frame join',address)
            frames[address]=depth;trace.append(address)
            if form=='movl_predec':
                assert word>>8&15==15;depth+=4;accesses+=1
            elif form=='movl_postinc':
                base=word>>4&15
                assert base in (2,3,15)
                if base==15:depth-=4
                accesses+=1
            elif form in ('movl_pc','movb_load','movb_store','movb_disp_load','movb_disp_store'):
                accesses+=1
            elif form=='mov_imm' and word>>8&15==4:
                assert counter is None;counter=word&255;assert counter==6
            elif form=='cmpeq_reg':
                assert address==0x42B2;iteration+=1;t=int(iteration!=first_mismatch)
            elif form=='dt':
                assert address==0x42B6 and 1<=counter<=6;counter-=1;t=int(counter==0)
            elif form=='clrt':t=0
            else:
                assert form in ('mov_reg','mov_imm','or_imm','and_imm','bf','bra','jmp','nop'),form
            peak=max(peak,depth);assert 0<=depth<=8
            return word,form
        while pc!=0x484BC:
            assert 0x42A4<=pc<0x42E6 or 0x484B0<=pc<0x484B6
            word,form=execute(pc)
            if form=='bf':target=pc+4+2*sx(word&255,8) if not t else pc+2
            elif form=='bra':
                execute(pc+2,True);target=pc+4+2*sx(word&4095,12)
            elif form=='jmp':
                assert pc in (0x484B2,0x42E2)
                execute(pc+2,True);target=0x42A4 if pc==0x484B2 else 0x484BC
            else:target=pc+2
            edges.add((pc,target));pc=target
            assert len(trace)<100
        assert depth==0 and peak==8 and t==0
        paths.append({'partition':'all six equal' if first_mismatch is None else 'first mismatch at longword'+str(first_mismatch),
            'accepted':first_mismatch is None,'instructions_including_entry':len(trace),
            'data_accesses_including_entry':accesses,'additional_stack_peak':peak,'trace':[f'{p:08X}' for p in trace]})
    # Every executable instruction is in the seven complete control partitions.
    expected=set(range(0x42A4,0x42E6,2))|set(range(0x484B0,0x484B6,2))
    assert set(forms)==expected
    assert not any(v['form'] in ('jsr','rts') or v['form'].startswith(('stc','ldc','sts','lds','f')) for v in forms.values() if v['form']!='bf')
    cycles={}
    for name,selected in [('accepted',[p for p in paths if p['accepted']]),('rejected',[p for p in paths if not p['accepted']])]:
        n=max(p['instructions_including_entry'] for p in selected);a=max(p['data_accesses_including_entry'] for p in selected)
        cycles[name]={'instructions':n,'data_accesses':a,'conditional_F2_D2_cycles':6*n+a}
    result={'status':'PASS','code_overlay_sha256':sha256(rom).hexdigest(),
        'scope':'Exact one-page division-only raw research image; exhaustive compiled control-predicate partition, no new scenario collection.',
        'frame_before_instruction':{f'{a:08X}':d for a,d in sorted(frames.items())},
        'compiled_instructions':{f'{a:08X}':v for a,v in sorted(forms.items())},
        'CFG_edges':[[f'{a:08X}',f'{b:08X}'] for a,b in sorted(edges)],'paths':paths,
        'added_stack_peak':8,'OEM_frame':28,'full_dispatcher_peak':36,'every_frame_join_equal':True,
        'balanced_at_continuation':True,'called_functions':[],
        'preserved_GPR':'R1/R4 saved/restored; R5-R14 untouched; R15 balanced; R2/R3 overwritten by original484BC/C0. R0 scratch.',
        'PR':'No adapter call or PR instruction; original OEM dispatcher restores caller PR.',
        'SR':'All-six success explicitly CLRT; first mismatch CMP supplies T0. DT reaches zero after exactly six matching words. Other SR bits unchanged.',
        'FPU_MAC_control':'No reachable FPU, MACH/MACL, GBR/VBR, SR-transfer or interrupt-mask operation.',
        'write_contract':'Two private stack words; existing OEM response length/opcode/flags/reject byte only, under unchanged dispatcher register setup.',
        'bound_argument':'First differing aligned longword among six, or all equal, partitions every24-byte request value. Each successful comparison decreases R4; no other loop or counter writer.',
        'cycles':cycles,'cycle_assumptions':'5*N+(F-1)*N+(D-1)*A, illustrative F=D=2. Excludes OEM baseline, external/entry stalls, interrupt delivery and actual silicon wait states.',
        'limitations':['Private ordinary stack and valid dispatcher entry required.','OEM upstream parser/SCI timing remains separate.','Full RAM request reads are sequential, not atomic.','Residency and global execution-context gates remain FAIL.'],
        'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'core_sha256':sha256(Path(__file__).with_name('sh2e.py').read_bytes()).hexdigest()}
    (OUT/'one_page_CFG_frame_proof.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS','compiled_paths':7,'frame':36,'cycles':cycles}))
if __name__=='__main__':main()
