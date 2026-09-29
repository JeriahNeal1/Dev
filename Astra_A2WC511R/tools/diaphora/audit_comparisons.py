"""Audit existing completed comparisons and exports without rerunning IDA/matcher."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import json,sqlite3,re
ROOT=Path('C:/Dev/Astra_A2WC511R');WORK=ROOT/'work/diaphora';OUT=ROOT/'reports/local/diaphora/comparison_audit'
def h(p):return sha256(Path(p).read_bytes()).hexdigest()
def ro(p):return sqlite3.connect(Path(p).resolve().as_uri()+'?mode=ro',uri=True)
def read(p):return json.loads(Path(p).read_text())
def intervals(values):
    result=[]
    for v in sorted(values):
        if result and result[-1][1]==v:result[-1][1]=v+1
        else:result.append([v,v+1])
    return result
def main():
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'COMPARISON_SUMMARY.json').exists();selected={}
    for manifest in sorted((WORK/'comparisons').glob('*/comparison.json')):
        label=manifest.parent.name
        if not label.startswith(('stock_','archive_')):continue
        v=int(label.rsplit('_',1)[1]);key=re.sub(r'_\d+$','',label)
        d=read(manifest)
        if v<3 or d['status']!='PASS':continue
        if key not in selected or v>selected[key][0]:selected[key]=(v,manifest,d)
    summaries=[];export_ids={};coverage=[]
    for key,(_,manifest,d) in sorted(selected.items()):
        sets=[]
        for side in ['left','right']:
            export=Path(d[side+'_export']['path']);assert h(export)==d[side+'_export']['sha256']
            identity=read(export.with_suffix('.identity.json'))
            for name,item in identity.items():assert h(item['path'])==item['sha256'],(export,name)
            export_ids[str(export)]=identity
            with ro(export) as c:sets.append({int(r[0]) for r in c.execute('select address from functions')})
        result=Path(d['results']['path']);assert h(result)==d['results']['sha256']
        with ro(result) as c:
            assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
            rows=c.execute('select type,address,address2 from results').fetchall();unmatched=c.execute('select type,address from unmatched').fetchall()
        matches=[{int(r[i+1],16) for r in rows} for i in range(2)]
        missing=[{int(ea,16) for label,ea in unmatched if label==side} for side in ['primary','secondary']]
        for i in range(2):
            assert not matches[i]&missing[i],(key,'matched/unmatched overlap',i)
            assert matches[i]|missing[i]==sets[i],(key,'incomplete/wrong-side result coverage',i)
        assert len(rows)==d['results']['match_rows']
        counts=Counter(t for t,a,b in rows)
        assert all(counts[k]==v for k,v in d['results']['counts'].items() if not k.startswith('unmatched'))
        summaries.append({'comparison':manifest.parent.name,'manifest':str(manifest),'manifest_sha256':h(manifest),
                          'results':d['results'],'left_export':d['left_export']['path'],'right_export':d['right_export']['path'],
                          'unique_matched_primary':len(matches[0]),'unique_matched_secondary':len(matches[1]),
                          'exact_partition_of_both_function_sets':True,'profile':d['typed_options']})
    a=selected['stock_511R_vs_510S'][2];b=selected['stock_511R_vs_510S_repeat'][2]
    assert a['results']['canonical_result_sha256_excluding_lines_dates_paths']==b['results']['canonical_result_sha256_excluding_lines_dates_paths']
    assert a['driver']['sha256']==b['driver']['sha256']
    fixed=selected['stock_511R_vs_412D'][2];fixed_repeat=selected['stock_511R_vs_412D_repeat'][2]
    assert fixed['results']['canonical_result_sha256_excluding_lines_dates_paths']==fixed_repeat['results']['canonical_result_sha256_excluding_lines_dates_paths']
    assert fixed['driver']['sha256']==fixed_repeat['driver']['sha256']
    deterministic=selected['stock_determinism'][2]
    assert deterministic['left_export']['functions_semantic_sha256_excluding_export_time']==deterministic['right_export']['functions_semantic_sha256_excluding_export_time']
    patch_checks=[]
    for key,allowed in [('stock_vs_M07_one',[(0x4260,0x430a),(0x484b0,0x484bc)]),('stock_vs_M07_two',[(0x4260,0x430a),(0x1473c,0x147ac),(0x484b0,0x484bc)])]:
        d=selected[key][2];raw1=Path(d['left_rom']['path']).read_bytes();raw2=Path(d['right_rom']['path']).read_bytes()
        changed={i for i,(x,y) in enumerate(zip(raw1,raw2)) if x!=y}
        assert all(any(a<=x<b for a,b in allowed) for x in changed)
        functions=[]
        for side in ['left','right']:
            export=Path(d[side+'_export']['path']);analysis=read(export.with_suffix('.analysis.json'))
            with ro(export) as c:
                ins={}
                for row in c.execute('select f.address,i.address from functions f join instructions i on i.func_id=f.id'):
                    ins.setdefault(int(row[0]),set()).add(int(row[1]))
            affected=[{'entry':f['start'],'chunks':f['chunks'],'changed_instruction_starts':[x for x in sorted(ins.get(f['start'],[])) if x in changed or x+1 in changed],
                       'changed_chunk_bytes':sum(a<=x<b for a,b in f['chunks'] for x in changed)} for f in analysis['functions'] if any(a<=x<b for a,b in f['chunks'] for x in changed)]
            functions.append(affected)
        patch_checks.append({'comparison':d['results']['path'],'changed_bytes':len(changed),'changed_intervals':intervals(changed),'allowed_existing_research_spans':allowed,'all_changes_inside_known_patch':True,
                             'affected_stock_native_functions':functions[0],'affected_research_native_functions':functions[1],
                             'note':'Unmatched entries are matcher omissions/ambiguities until raw bytes and function boundaries are checked; they are not automatically changed functions.'})
    output={'status':'PASS','selected_comparisons':summaries,'closed_export_identities':export_ids,
            'acceptance':{'A_tiny_native_export':'reused durable_smoke_03_final, no repeat','B_self_compare':'reused durable_smoke_03_final, no repeat',
                          'C_independent_stock_analyses_same_function_rows':True,'D_stock_M07_changes_confined_to_known_patch':patch_checks,
                          'E_clean_matcher_process_canonical_hash':a['results']['canonical_result_sha256_excluding_lines_dates_paths'],
                          'E_comparisons':[str(selected['stock_511R_vs_510S'][1]),str(selected['stock_511R_vs_510S_repeat'][1])],
                          'repaired_partition_clean_process_canonical_hash':fixed['results']['canonical_result_sha256_excluding_lines_dates_paths']},
            'all_result_rows_partition_source_and_target_sets':True,'upstream_unmatched_side_fix_commit':'24e02a891e7af468882b919a52f75787fa3692cd',
            'no_new_environment_probe_install_or_stock_self_comparison':True,'no_authoritative_IDB_mutation':True}
    (OUT/'COMPARISON_SUMMARY.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','comparisons':len(summaries),'exports':len(export_ids),'clean_match_hash':output['acceptance']['E_clean_matcher_process_canonical_hash']}))
if __name__=='__main__':main()
