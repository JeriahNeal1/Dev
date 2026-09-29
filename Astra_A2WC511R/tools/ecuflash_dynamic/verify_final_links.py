"""Check current gate links and decisive evidence; no provider or GUI use."""
import sys
sys.dont_write_bytecode=True
import json
from finalize import ROOT,OUT,sha

def main():
    gates=json.loads((OUT/'ENGINEERING_GATES.json').read_text())
    summary=json.loads((OUT/'QUALIFICATION_SUMMARY.json').read_text())
    checkpoint=json.loads((ROOT/'state/CHECKPOINT.json').read_text())
    errors=[];checked=0
    for ref in [e for g in gates['gates'] for e in g.get('evidence',[])]+list(summary['evidence'].values()):
        try:
            if sha(ref['path'])!=ref['sha256']:errors.append({'hash_mismatch':ref['path']})
            checked+=1
        except OSError as e:errors.append({'missing':ref['path'],'error':str(e)})
    byid={g['id']:g for g in gates['gates']}
    assert len(byid)==len(gates['gates'])
    assert byid['ECUFLASH_EXACT_READ_COVERAGE']['status']=='FAIL'
    assert byid['ECUFLASH_INSTALLED_KERNEL_IDENTITY']['status']=='PASS'
    assert byid['SINGLE_ACQUISITION_CONNECTION']['status']=='FAIL'
    assert not gates['B_connection_qualified'] and not checkpoint['B_connection_qualified']
    assert checkpoint['engineering_gates']=='reports/local/ecuflash_dynamic/ENGINEERING_GATES.json'
    assert checkpoint['gate_summary']==gates['summary']
    assert summary['decision']=='NO_SINGLE_ACQUISITION_CONNECTION'
    assert summary['decisive_counterexample']['lost_bytes']==37
    assert not summary['physical_operations'] and not summary['real_provider_loaded']
    cleanup=json.loads((OUT/'SESSION_CLEANUP.json').read_text())
    assert all(x['status']=='PASS' for x in cleanup)
    preservation=json.loads((OUT/'FINAL_PRESERVATION.json').read_text())
    assert preservation['protected_artifacts_status']=='PASS' and preservation['real_provider_registry_status']=='PASS'
    assert preservation['real_ecuflash_settings_unchanged']
    assert not preservation['universal_preservation_claim']
    result={'schema':1,'status':'PASS' if not errors else 'FAIL','hash_links_checked':checked,'errors':errors,
        'closed_virtual_sessions':len(cleanup),'protected_files':preservation['verified_files'],
        'decision':summary['decision'],'physical':False}
    (OUT/'FINAL_LINK_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
