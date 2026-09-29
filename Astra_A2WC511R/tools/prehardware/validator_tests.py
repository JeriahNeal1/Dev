"""Adversarial validator regressions; mutated images stay in memory only."""
import sys
sys.dont_write_bytecode=True
import argparse, copy, json, tempfile
from pathlib import Path
import validator as v

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    registry=v.load_registry();stock=v.read(registry['common']['baseline']['path']);one=v.read(registry['artifacts']['one_page']['image']['path']);two=v.read(registry['artifacts']['two_pages']['image']['path'])
    results=[]
    def ck(name,report,cid):
        found=next(x for x in report['checks'] if x['id']==cid)
        assert found['status']=='FAIL',(name,cid,found)
        assert report['status']=='FAIL',(name,report['status'])
        results.append({'test':name,'detected_by':cid,'status':'PASS_NEGATIVE_REJECTION'})
    def mutant(data,address,replacement):return data[:address]+bytes(replacement)+data[address+len(replacement):]
    def test(name,data,cid,artifact='stock',r=None,reader=v.read):ck(name,v.evaluate(data,r or registry,artifact,reader),cid)
    test('truncated_image',stock[:-1],'LENGTH')
    test('wrong_CALID',mutant(stock,0x2000,b'B'),'CALID')
    test('wrong_ECUID',mutant(stock,0xCDAD8,b'\x30'),'ECUID')
    test('little_endian_reset_PC',mutant(stock,0,stock[:4][::-1]),'BIG_ENDIAN_RESET_VECTORS')
    test('unaligned_reset_PC',mutant(stock,3,b'\xAD'),'BIG_ENDIAN_RESET_VECTORS')
    test('SP_outside_RAM',mutant(stock,4,bytes.fromhex('ffffc000')),'INITIAL_SP')
    test('unaligned_SP',mutant(stock,7,b'\xA1'),'INITIAL_SP')
    test('checksum_disabled_first_descriptor',mutant(stock,0xFFB80,bytes(8)),'CHECKSUM_GEOMETRY')
    test('checksum_region_overflow',mutant(stock,0xFFB84,bytes.fromhex('00100001')),'CHECKSUM_GEOMETRY')
    test('checksum_wrong_correction',mutant(stock,0xFFB88,bytes([stock[0xFFB88]^1])),'CHECKSUM_VALIDITY')
    test('original_control_hook_changed',mutant(stock,0x7A07,b'\x9D'),'ORIGINAL_HOOK_BYTES')
    test('original_diagnostic_hook_changed',mutant(one,0x484B0,b'\x00\x09'),'ORIGINAL_HOOK_BYTES','one_page')
    test('branch_in_delay_slot',mutant(one,0x484B4,bytes.fromhex('000b')),'DELAY_SLOT_ALIGNMENT','one_page')
    test('odd_indirect_branch_target',mutant(one,0x484BB,b'\xA5'),'BRANCH_TARGETS','one_page')
    test('direct_branch_into_literal_data',mutant(one,0x42CC,bytes.fromhex('a00e')),'BRANCH_TARGETS','one_page')
    test('unrecognized_changed_opcode',mutant(one,0x42A4,bytes.fromhex('ffff')),'COMPILED_INSTRUCTION_IDENTITY','one_page')
    test('orphan_FF_hole_change',mutant(stock,0xE1000,b'\x00'),'CHANGED_BYTE_ALLOWLIST')
    test('bootloader_change',mutant(stock,0xA00,bytes([stock[0xA00]^1])),'FORBIDDEN_BOOT_VECTOR_REGIONS')
    test('exception_vector_change',mutant(stock,0xFFFF0,bytes([stock[0xFFFF0]^1])),'FORBIDDEN_BOOT_VECTOR_REGIONS')
    table=next(t for t in registry['common']['calibration_extents'] if 0xC0000<=t['start']<0xCDAD8)
    at=table['start'];test('calibration_table_change',mutant(stock,at,bytes([stock[at]^1])),'CALIBRATION_PRESERVATION')
    test('WGDC_hook_activation',mutant(one,0x122B7,bytes([one[0x122B7]^2])),'ACTIVE_FEATURE_CLOSURE','one_page')
    bad=copy.deepcopy(registry);bad['artifacts']['one_page']['persistent_ram_declarations']=[[0xFFFF7400,0xFFFF7420]]
    test('unapproved_persistent_RAM_declaration',one,'ROM_RAM_DECLARATIONS','one_page',bad)
    bad=copy.deepcopy(registry);bad['artifacts']['one_page']['rom_declarations'][0][0]+=1
    test('misaligned_ROM_declaration',one,'ROM_RAM_DECLARATIONS','one_page',bad)
    test('inside_allowlist_payload_corruption',mutant(one,0x42AC,bytes.fromhex('e407')),'PATCH_INVERSE_ROUNDTRIP','one_page')
    source=registry['artifacts']['one_page']['repro_artifacts'][0]['path']
    def changed_source(path):
        data=v.read(path);return data+b'\x00' if str(path)==source else data
    test('rebuild_artifact_orphan',one,'REPRO_BUILD_ASSOCIATION','one_page',reader=changed_source)
    evidence=next(iter(registry['evidence_files']))
    def absent_evidence(path):
        if str(path)==evidence:raise FileNotFoundError('synthetic missing immutable evidence')
        return v.read(path)
    test('missing_required_evidence',one,'EVIDENCE_INTEGRITY','one_page',reader=absent_evidence)
    test('unassociated_valid_identity_image',mutant(stock,0xE1000,b'\x00'),'INPUT_ARTIFACT_ASSOCIATION')
    test('wrong_registered_protocol_profile',one,'INPUT_ARTIFACT_ASSOCIATION','two_pages')
    def wrong_baseline(path):
        data=v.read(path)
        return mutant(data,0x2000,b'B') if str(path)==registry['common']['baseline']['path'] else data
    test('baseline_reference_drift',one,'BASELINE_INTEGRITY','one_page',reader=wrong_baseline)
    raw_one=v.read(Path(registry['artifacts']['one_page']['image']['path']).parents[1]/'protocol/execution_01/one_page.RESEARCH_NOT_RESIDENCY_PROVEN.raw.bin')
    test('unfixed_research_image_checksum',raw_one,'CHECKSUM_VALIDITY','one_page')
    # A caller's JSON cannot promote ownership or authorize a previously unknown hash.
    bad=copy.deepcopy(registry);bad['artifacts']['one_page']['residency_evidence']['status']='PASS';bad['artifacts']['one_page']['image']['sha256']='0'*64
    with tempfile.TemporaryDirectory(prefix='A2WC validator registry negative ') as td:
        fp=Path(td)/'forged_registry.json';fp.write_text(json.dumps(bad))
        try:v.load_registry(fp)
        except ValueError:results.append({'test':'forged_registry_ownership_PASS','detected_by':'PINNED_REGISTRY_HASH','status':'PASS_NEGATIVE_REJECTION'})
        else:raise AssertionError('Forged registry accepted')
    ck('frozen_one_page_unapproved_residency',v.evaluate(one,registry),'RESIDENCY_OWNERSHIP')
    ck('frozen_two_page_unapproved_residency',v.evaluate(two,registry),'RESIDENCY_OWNERSHIP')
    stock_result=v.evaluate(stock,registry);assert stock_result['status']=='CONDITIONAL'
    again=v.evaluate(stock,registry);assert stock_result==again
    results.append({'test':'stock_repeat_determinism','status':'PASS','canonical_sha256':v.digest(json.dumps(stock_result,sort_keys=True).encode())})
    wrong={'schema':1,'status':'PASS','image':{'sha256':'0'*64},'ssm_readiness':{'status':'PASS','boot_proven':True}}
    r=copy.deepcopy(stock_result);v.integrate_boot(r,wrong,v.digest(stock));ck('boot_result_wrong_image',r,'BOOT_PATH')
    failed={'schema':1,'status':'FAIL','image':{'sha256':v.digest(stock)},'unsupported_frontier':{'kind':'unsupported_instruction','pc':'0xAAC'}}
    r=copy.deepcopy(stock_result);v.integrate_boot(r,failed,v.digest(stock));ck('boot_unsupported_opcode',r,'UNSUPPORTED_BEHAVIOR')
    pending={'schema':1,'status':'CONDITIONAL','image':{'sha256':v.digest(stock)},'unsupported_frontier':{'kind':'unmodeled_MMIO'},'ssm_readiness':{'status':'CONDITIONAL','boot_proven':False}}
    r=copy.deepcopy(stock_result);v.integrate_boot(r,pending,v.digest(stock));assert r['status']=='CONDITIONAL' and next(x for x in r['checks'] if x['id']=='SSM_STARTUP_READINESS')['status']=='CONDITIONAL'
    results.append({'test':'partial_boot_cannot_claim_SSM_ready','status':'PASS'})
    paired={'schema':1,'status':'CONDITIONAL','classification':'RESET_PREFIX_DIFFERENTIAL_NOT_COMPLETE_BOOT_EQUIVALENCE',
            'stock':copy.deepcopy(pending),'candidate':copy.deepcopy(pending),'equal_frontier':True,'terminal_state_equal':True,'explicit_allowlist':[],'differences':[]}
    paired['stock']['image']['sha256']='f'*64
    r=copy.deepcopy(stock_result);v.integrate_boot(r,paired,v.digest(stock),v.digest(stock));ck('comparison_wrong_stock_image',r,'STOCK_VS_CANDIDATE_BOOT_PREFIX')
    paired['stock']['image']['sha256']=v.digest(stock);paired['differences']=[{'kind':'observable_trace','index':0,'allowed':False}]
    r=copy.deepcopy(stock_result);v.integrate_boot(r,paired,v.digest(stock),v.digest(stock));ck('unapproved_boot_write_difference',r,'STOCK_VS_CANDIDATE_BOOT_PREFIX')
    paired['differences']=[];paired['explicit_allowlist']=[{'stock':None,'candidate':{'mode':'w','address':'FFFF7400'}}]
    r=copy.deepcopy(stock_result);v.integrate_boot(r,paired,v.digest(stock),v.digest(stock));ck('caller_added_boot_allowlist',r,'STOCK_VS_CANDIDATE_BOOT_PREFIX')
    paired['explicit_allowlist']=[];paired['terminal_state_equal']=False
    r=copy.deepcopy(stock_result);v.integrate_boot(r,paired,v.digest(stock),v.digest(stock));ck('unreported_terminal_register_difference',r,'STOCK_VS_CANDIDATE_BOOT_PREFIX')
    r=copy.deepcopy(stock_result);v.integrate_boot(r,pending,v.digest(stock),dependencies={'boot.py':'a'*64});ck('boot_model_orphan_result',r,'BOOT_MODEL_DEPENDENCIES')
    out={'schema':1,'status':'PASS','groups':len(results),'tests':results,'mutated_images_written':False,'physical_or_provider_access':False,
         'validator_sha256':v.digest(Path(v.__file__).read_bytes()),'registry_sha256':v.REGISTRY_SHA256}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(results),'report':str(args.output)}))
if __name__=='__main__':main()
