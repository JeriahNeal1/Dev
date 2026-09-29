"""Maintainer-only registry preparation; not part of image acceptance or flashing.

Copies declarations from pinned, already reviewed frozen evidence. A changed
registry must have its hash reviewed and pinned in validator.py before use.
"""
import sys
sys.dont_write_bytecode = True
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
M07=ROOT/'reports/local/m07_residency'
STOCK=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')
STOCK_SHA='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
def digest(b):return hashlib.sha256(b).hexdigest()
def artifact(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':digest(p.read_bytes())}
def leaf_words(data,start,end):
    # Exact bounded leaf decode follows both conditional arms and delay words.
    # No general indirect control transfer is accepted by this extractor.
    sys.path.insert(0,'C:/Dev/A2WC511R_Sim')
    from sh2e import OPCODES
    assert digest(Path('C:/Dev/A2WC511R_Sim/sh2e.py').read_bytes())=='b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff'
    out={};todo=[start];seen=set()
    def add(a,delay=False):
        assert start<=a<end and a%2==0
        w=int.from_bytes(data[a:a+2],'big');o=next((o for o in OPCODES if w&o.mask==o.value),None);assert o
        assert not delay or not o.branch
        out[f'{a:08X}']={'word':f'{w:04X}','form':o.name,'delay_slot':delay};return w,o.name
    while todo:
        a=todo.pop()
        if a in seen:continue
        seen.add(a);w,n=add(a)
        if n=='rts':add(a+2,True);continue
        if n=='bra':
            v=w&4095;todo.append(a+4+2*(v-4096 if v&2048 else v));add(a+2,True);continue
        if n in ('bt','bf','bt_s','bf_s'):
            v=w&255;todo.extend([a+4+2*(v-256 if v&128 else v),a+(4 if n.endswith('_s') else 2)])
            if n.endswith('_s'):add(a+2,True)
            continue
        assert n not in ('jmp','jsr','bsr')
        todo.append(a+2)
    return out
def main():
    stock=STOCK.read_bytes();assert digest(stock)==STOCK_SHA
    evidence={}
    def read(p):
        p=Path(p);evidence[str(p.resolve())]=digest(p.read_bytes());return json.loads(p.read_text())
    frozen=read(ROOT/'reports/local/diaphora/START_PRESERVATION.json')['frozen_m07_files']
    build=read(M07/'build_audit_02/BUILD_AUDIT.json')
    assert digest((M07/'build_audit_02/BUILD_AUDIT.json').read_bytes())=='afc1ed229e957d6f3abcfe445f42ee55e19f1212d25c720995aee6ff1f28760b'
    checksum_source=ROOT/'reports/local/interfaces/checksum_audit.py'
    evidence[str(checksum_source.resolve())]=digest(checksum_source.read_bytes())
    defs=read(ROOT/'reports/local/gate_closure/rom/definition_overlap.json')
    own=read(M07/'OWNERSHIP_FRAGMENTS.json');assert own['status']=='FAIL' and own['provably_owned_bytes']==0
    gates=read(M07/'ENGINEERING_GATES.json')
    assert next(g for g in gates['gates'] if g['id']=='NO_ACTIVE_CONTROL_FEATURES')['status']=='PASS'
    read(M07/'semantic/semantic_structural_proof.json')
    read(M07/'semantic/TARGET_DOMAIN_CLOSURE.json')
    read(M07/'protocol/execution_01/compiled_protocol_fixtures.json')
    hook_words={0x7A04:0x209C,0x122B4:0x14B20,0x127E8:0x317D8,0xD324:0xF928,0xFFF8:0xFFFFBFFB,0x114E0:0x35B96,
                0x1281C:0x2E2E8,0x35C3C:0x2150,0x35C40:0x84944,0x2E538:0x2150,0x2E544:0x842E4}
    assert all(int.from_bytes(stock[a:a+4],'big')==v for a,v in hook_words.items())
    common={'baseline':artifact(STOCK),'identity':{'size':0x100000,'calid_offset':0x2000,'calid_hex':b'A2WC511R'.hex(),'ecuid_offset':0xCDAD8,'ecuid_hex':'2f12515306'},
            'reset_words':[int.from_bytes(stock[p:p+4],'big') for p in range(0,16,4)],
            'checksum_descriptors':[{'offset':p,'start':int.from_bytes(stock[p:p+4],'big'),'end_parameter':int.from_bytes(stock[p+4:p+8],'big')} for p in range(0xFFB80,0xFFC28,12)],
            'forbidden_spans':[[0,0x2000],[0xFFF00,0x100000]],
            'preserved_hook_words':{str(a):v for a,v in hook_words.items()},
            'preserved_special_spans':[[0x11AD8,0x11AE0],[0x4F310,0x4F950],[0xE1000,0xE1364],[0xFFC4C,0xFFC50]],
            'calibration_extents':defs['table_extents']}
    records={'stock':{'image':artifact(STOCK),'kind':'unchanged_stock','fragments':[],'rom_declarations':[],'persistent_ram_declarations':[],
                      'code_words':{},'cfg_edges':[],'reproducible_build':'OEM_REFERENCE_NO_PROJECT_BUILD','residency_required':False}}
    for profile in ('one_page','two_pages'):
        overlay=read(M07/f'protocol/execution_01/{profile}_overlay.json')
        image=M07/f'build_audit_02/{profile}.RESEARCH_NOT_RESIDENCY_PROVEN.checksum_corrected.bin'
        candidate=image.read_bytes();assert digest(candidate)==build['profiles'][profile]['corrected_sha256']
        native_checksum=read(M07/f'build_audit_02/{profile}.native_checksum.json')
        assert native_checksum['status']=='PASS' and any(r['sha256']==digest(candidate) and r['native_validation']==0 for r in native_checksum['inputs'])
        f=[dict(x) for x in overlay['fragments']]
        for row in build['profiles'][profile]['checksum_rows']:
            p=row['descriptor_offset']+8
            if candidate[p:p+4]!=stock[p:p+4]:f.append({'address':p,'before_hex':stock[p:p+4].hex(),'after_hex':candidate[p:p+4].hex(),'label':'checksum correction word'})
        cfg=read(M07/('semantic/one_page_CFG_frame_proof.json' if profile=='one_page' else 'semantic/two_page_dispatch_abi.json'))
        if profile=='two_pages':cfg=cfg['compiled_CFG']
        words=cfg.get('compiled_instructions',cfg.get('instruction_addresses'))
        words.update(leaf_words(candidate,0x4260,0x42A4))
        if profile=='two_pages':words.update(leaf_words(candidate,0x1473C,0x14770))
        pm=read(M07/('protocol/one_page_01/manifest.json' if profile=='one_page' else 'protocol/two_pages_01/manifest.json'))
        assert pm.get('no_persistent_ram') is True if profile=='one_page' else pm['persistent_ram_bytes']==0
        assert pm.get('added_stack_bytes',pm.get('additional_adapter_stack_bytes'))==8
        artifacts=[]
        names=['division',profile]+(['range_tail'] if profile=='two_pages' else [])
        for n in names:
            for filename,detail in build['repeat_artifacts'][n].items():
                if filename.endswith('.bin'):
                    p=M07/'build_audit_02'/n/filename;assert digest(p.read_bytes())==detail['repeat_sha256']==detail['original_sha256']
                    artifacts.append(artifact(p))
            sourcefolder='semantic' if n in ('division','range_tail') else 'protocol'
            for suffix in ('.s','.ld'):
                p=ROOT/'work/M07'/sourcefolder/(n+suffix)
                assert digest(p.read_bytes())==frozen[p.relative_to(ROOT).as_posix()], ('Frozen source drift',p)
                artifacts.append(artifact(p))
        records[profile]={'image':artifact(image),'kind':'FROZEN_UNAPPROVED_M07_RESEARCH','fragments':f,
            'rom_declarations':[[x['address'],x['address']+len(bytes.fromhex(x['after_hex']))] for x in overlay['fragments']],
            'persistent_ram_declarations':[],'adapter_stack_bytes':8,'division_stack_bytes':12,
            'code_words':words,'cfg_edges':cfg['CFG_edges'],'reproducible_build':'PINNED_PREVIOUS_BYTE_IDENTICAL_RAW_SECTIONS',
            'repro_artifacts':artifacts,'residency_required':True,'residency_evidence':artifact(M07/'OWNERSHIP_FRAGMENTS.json'),
            'active_control_evidence':artifact(M07/'ENGINEERING_GATES.json'),'protocol_manifest':artifact(M07/('protocol/one_page_01/manifest.json' if profile=='one_page' else 'protocol/two_pages_01/manifest.json'))}
    model_path=HERE/'validator_boot_model.json'
    model=read(model_path) if model_path.exists() else None
    if model:
        for p,h in model['files'].items():assert digest(Path(p).read_bytes())==h, ('Boot model drift',p)
        contract=model['contract'];assert digest(Path(contract['path']).read_bytes())==contract['sha256']
        evidence[contract['path']]=contract['sha256']
    result={'schema':1,'trust':'Maintainer reviewed project registry; hash pinned in validator.py. Not an external signature or caller-supplied approval.',
            'common':common,'artifacts':records,'evidence_files':evidence,'boot_harness':model}
    out=HERE/'validator_registry.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(digest(out.read_bytes()))
if __name__=='__main__':main()
