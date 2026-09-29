"""Seal the completed review and check its final cross-linked identities."""
from pathlib import Path
from hashlib import sha256
import json,re,sqlite3
ROOT=Path('C:/Dev/Astra_A2WC511R');OUT=ROOT/'reports/local/diaphora';WORK=ROOT/'work/diaphora'
def h(p):return sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def main():
    target=OUT/'DELIVERABLE_MANIFEST.json';assert not target.exists()
    deterministic=read(OUT/'correspondence_final_01/DETERMINISM.json')
    for name,info in deterministic['files'].items():assert h(OUT/'correspondence_final_01'/name)==info['sha256']
    comparison=read(OUT/'comparison_audit/COMPARISON_SUMMARY.json')
    references={}
    for item in comparison['selected_comparisons']:
        p=Path(item['manifest']);assert h(p)==item['manifest_sha256'];references[str(p)]=h(p)
        p=Path(item['results']['path']);assert h(p)==item['results']['sha256'];references[str(p)]=h(p)
    for item in read(OUT/'EXPORT_INDEX.json')['exports'].values():
        for v in item.values():assert h(v['path'])==v['sha256'];references[v['path']]=v['sha256']
    decision=read(OUT/'ARCHITECTURAL_DECISION.json');gates=read(OUT/'ENGINEERING_GATES.json')
    assert decision['provably_owned_bytes']==gates['provably_owned_bytes']==0
    assert not decision['M08_payload_designed_or_built'] and not gates['ECU_physical_test_candidate']
    assert set(g['status'] for g in gates['gates'])<=set(['PASS','FAIL','PHYSICAL/BENCH REQUIRED'])
    for entry in gates['gates']:
        for item in entry.get('evidence',[]):assert h(item['path'])==item['sha256'],item
    damaged=read(OUT/'START_PRESERVATION.json')['authoritative_IDB'];assert h(damaged['path'])==damaged['sha256']
    candidate=WORK/'idbs/recovery_candidate_01.i64';assert h(candidate)=='55575c37d368665adcf89bd18cd81bcf6dd6cac7a615d17161514b4a0e4d1500'
    references[str(candidate)]=h(candidate)
    # Verify real relative document links in the primary user-facing handoff.
    broken=[]
    for name in ['DELIVERABLES.md','COMPARATIVE_ANALYSIS.md']:
        path=OUT/name
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if not link.startswith(('https:','http:')) and not (path.parent/link).exists():broken.append([name,link])
    assert not broken,broken
    files={}
    roots=[OUT,ROOT/'tools/diaphora',ROOT/'state',Path('C:/Dev/A2WC511R_Sim/diaphora_crossrom')]
    for root in roots:
        for p in sorted(root.rglob('*')):
            if p.is_file() and p!=target:files[str(p)]=h(p)
    result={'schema':1,'status':'PASS_SEALED_COMPARATIVE_REVIEW','architectural_decision':decision['decision'],
            'function_rows':deterministic['function_rows'],'correspondence_sha256':deterministic['files']['FUNCTION_CORRESPONDENCE.sqlite']['sha256'],
            'JSONL_sha256':deterministic['files']['FUNCTION_CORRESPONDENCE.jsonl']['sha256'],
            'files':files,'external_closed_artifacts':references,'no_authoritative_IDB_replacement':True,
            'M0_M06_M07_preservation':'PRESERVATION.json','no_new_physical_acquisition_or_active_control':True}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'files':len(files),'external_closed_artifacts':len(references),'manifest_sha256':h(target),'database_sha256':result['correspondence_sha256']}))
if __name__=='__main__':main()
