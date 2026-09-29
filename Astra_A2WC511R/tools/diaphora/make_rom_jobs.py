"""Create immutable, hash-pinned, consistently seeded native ROM analysis jobs."""
from pathlib import Path
import json,hashlib
ROOT=Path('C:/Dev/Astra_A2WC511R'); WORK=ROOT/'work/diaphora'
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    stock=Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin'); raw=stock.read_bytes()
    prior=ROOT/'reports/local/gate_closure/ida/defined_code_export.json'
    functions=json.loads(prior.read_text())['functions']
    public=json.loads((ROOT/'reports/local/diaphora/rom_inventory/public_rom_manifest.json').read_text())['roms']
    targets=[('A2WC511R_stock_01',stock),('A2WC511R_stock_02',stock)]
    targets += [(r['calid_at_2000']+'_stock_01',Path(r['path'])) for r in public if r['calid_at_2000']!='A2WC511R']
    targets += [('M07_one_page_01',ROOT/'reports/local/m07_residency/protocol/execution_01/one_page.RESEARCH_NOT_RESIDENCY_PROVEN.raw.bin'),
                ('M07_two_page_01',ROOT/'reports/local/m07_residency/protocol/execution_01/two_pages.RESEARCH_NOT_RESIDENCY_PROVEN.raw.bin'),
                ('A2WC522S_archive_01',ROOT/'reports/local/diaphora/merpmod_reference/A2WC522S_ARCHIVED_PATCH_RECONSTRUCTED_NOT_FOR_FLASH.bin')]
    out=WORK/'scripts/rom_jobs';out.mkdir(parents=True,exist_ok=True)
    jobs=[]
    for label,path in targets:
        data=path.read_bytes();assert len(data)==0x100000
        same=label.startswith(('A2WC511R','M07_'))
        seeds={}
        def seed(ea,why):
            if 0<=ea<0x100000 and ea%2==0 and data[ea:ea+2]!=b'\xff\xff':seeds.setdefault(ea,[]).append(why)
        for f in functions:
            if same:seed(f['start'],{'kind':'existing_A2WC511R_function_start','source':f['start']})
            else:
                # Never copy addresses or ends blindly to a sibling calibration.
                if len(f['chunks'])!=1 or f['end']-f['start']<24:continue
                fragment=raw[f['start']:min(f['start']+48,f['end'])]
                at=data.find(fragment)
                if at>=0 and data.find(fragment,at+1)<0:
                    seed(at,{'kind':'unique_exact_executable_prefix','source':f['start'],'length':len(fragment),'prefix_sha256':digest(fragment)})
        for offset in [0,8,0xffff8]+list(range(0xffc50,0xffff8,4)):
            ea=int.from_bytes(data[offset:offset+4],'big')
            seed(ea,{'kind':'candidate_reset_or_exception_vector','vector_offset':offset,'qualification':'entry candidate; vector interpretation not universal ownership proof'})
        if label.startswith('M07_'):seed(0x42a4,{'kind':'declared_research_payload_entry'})
        if label.startswith('M07_two'):seed(0x14770,{'kind':'declared_research_payload_fragment'})
        if label.startswith('A2WC522S_archive'):
            # Actual archived hook targets, discovered from patched pointer values.
            for offset in (0xd324,0x7a04,0x122b4,0x127e8):seed(int.from_bytes(data[offset:offset+4],'big'),{'kind':'archived_patch_hook_pointer','offset':offset})
        job={'schema':1,'label':label,'rom':str(path.resolve()),'rom_sha256':digest(data),'rom_size':len(data),
             'processor':'sh4b','hardware':'SH-2E / SH7058; sh4b is IDA implementation only','endianness':'big','rom_base':0,
             'ram_segment':[0xffff0000,0xffffc000],'analysis_profile':'native_default_autoanalysis_with_explicit_evidenced_roots_v1',
             'seed_source':str(prior),'seed_source_sha256':digest(prior.read_bytes()),'function_seeds':[{'address':ea,'evidence':why} for ea,why in sorted(seeds.items())],
             'coverage_claim':'seeded static discovery, not complete firmware reachability or executable ownership',
             'idb':str(WORK/'idbs'/f'{label}.i64'),'export':str(WORK/'exports'/f'{label}.sqlite')}
        target=out/f'{label}.json'
        if target.exists():assert json.loads(target.read_text())==job,'Existing config differs'
        else:target.write_text(json.dumps(job,indent=2)+'\n',encoding='utf-8')
        jobs.append({'label':label,'config':str(target),'seeds':len(seeds)})
    (out/'INDEX.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8');print(json.dumps(jobs,indent=2))
if __name__=='__main__':main()
