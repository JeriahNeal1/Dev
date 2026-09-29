"""Verify protected artifacts and compare real registry without exposing values."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,winreg,datetime
from start_session import ROOT,BACK,OUT,tree,sha

def main():
    before=json.loads((OUT/'START_PRESERVATION.json').read_text())
    files={**before['sealed_files'],**before['protected_external']}
    files[before['previous_seal']['path']]=before['previous_seal']['sha256']
    # Damaged evidence IDB is separately retained under its old exact filename.
    files[r'C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER.bin.i64']='46f442e93535b20cc9f360403c69724d55c72900c7e9716af81bda7fd5c3357f'
    seals=[];historical_state=[]
    for path,base in (
        (ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2/SHA256SUMS.json',ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2'),
        (ROOT/'reports/local/m07_residency/M06_FROZEN_MANIFEST.json',ROOT),
        (ROOT/'delivery/A2WC511R_M07_20260925_RESIDENCY_REVIEW/SHA256SUMS.json',ROOT/'delivery/A2WC511R_M07_20260925_RESIDENCY_REVIEW'),
        (ROOT/'reports/local/diaphora/DELIVERABLE_MANIFEST.json',ROOT)):
        seal=json.loads(path.read_text());entries={**seal['files'],**seal.get('external_closed_artifacts',{})}
        for p,h in entries.items():
            target=Path(p) if Path(p).is_absolute() else base/p
            if target.parent==ROOT/'state':
                # A historical delivery seals that checkpoint's state, not every
                # later checkpoint. Verify the exact pre-existing backup rather
                # than overwriting the current run's preservation expectation.
                candidates=[ROOT/'backups/prehardware_20260926/state'/target.name,
                            BACK/'state'/target.name]
                preserved=next((q for q in candidates if q.exists() and sha(q)==h),None)
                historical_state.append({'manifest':str(path),'logical_path':str(target),
                    'expected_sha256':h,'preserved_path':str(preserved) if preserved else None})
                if preserved is not None:
                    files[str(preserved)]=h
                    continue
                raise ValueError(f'Historical state version not preserved: {target} {h}')
            files[str(target)]=h
        seals.append({'path':str(path),'sha256':sha(path),'entries':len(entries)})
    bad=[];updated_state=[]
    for p,h in files.items():
        path=Path(p)
        if path.parent==ROOT/'state':
            preserved=BACK/'state'/path.name
            updated_state.append({'current_path':p,'current_sha256':sha(path),
                'preserved_prior_path':str(preserved),'expected_prior_sha256':h,
                'scope':'AUTHORIZED_CURRENT_STATE_UPDATE; ORIGINAL_VERIFIED_IN_PREWRITE_BACKUP'})
            actual=sha(preserved) if preserved.exists() else None
        else:actual=sha(p) if Path(p).exists() else None
        if actual!=h:bad.append({'path':p,'expected':h,'actual':actual})
    reg={}
    for name,view in [('x86',winreg.KEY_WOW64_32KEY),('x64',winreg.KEY_WOW64_64KEY)]:
        for path in (r'SOFTWARE\PassThruSupport.04.04',r'SOFTWARE\PassThruSupport.05.00'):
            reg['HKLM/'+name+'/'+path]=tree(winreg.HKEY_LOCAL_MACHINE,path,view)
    reg['HKCU/Software/OpenECU/EcuFlash']=tree(winreg.HKEY_CURRENT_USER,r'Software\OpenECU\EcuFlash')
    original=json.loads((BACK/'REGISTRY_BEFORE_PRIVATE.json').read_text())
    changed=[key for key in original if original[key]!=reg.get(key)]
    # Private snapshots can contain existing adapter identity/license settings.
    # Never echo them or embed their values in a public report.
    private=BACK/'REGISTRY_AFTER_PRIVATE.json';private.write_text(json.dumps(reg,indent=2)+'\n')
    report=dict(schema=1,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protected_artifacts_status='PASS' if not bad else 'FAIL',verified_files=len(files),mismatches=bad,updated_state=updated_state,seals=seals,historical_state=historical_state,
        real_provider_registry_status='PASS' if not any(k.startswith('HKLM/') for k in changed) else 'FAIL',
        real_ecuflash_settings_unchanged=not changed,changed_registry_keys=changed,
        private_registry_snapshot_sha256=sha(private),
        historical_log_preservation='FAIL_INITIAL_APPDATA_ROTATION_7_FILES; 3_EXACT_RECOVERIES; 4_UNRECOVERED',
        incident_evidence='backups/ecuflash_dynamic_20260926/recovered_logs/RECOVERY_REPORT.json',
        universal_preservation_claim=False,physical_operations=False)
    (OUT/'FINAL_PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('updated_state','seals','historical_state')}))
    return 0 if not bad and not any(k.startswith('HKLM/') for k in changed) else 1
if __name__=='__main__':raise SystemExit(main())
