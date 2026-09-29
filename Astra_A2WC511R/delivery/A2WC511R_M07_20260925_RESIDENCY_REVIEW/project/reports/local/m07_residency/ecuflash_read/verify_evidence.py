"""Offline evidence consistency/regression checks and final manifest."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).parent
ROOT=Path(r'C:\Dev\Astra_A2WC511R')
reports=json.loads((HERE/'historical_log_audit.json').read_text())['reports']

def contiguous(rows,start,end):
    cursor=start
    for row in rows:
        if row['address'] != cursor or row['size']<=0:
            return False
        cursor+=row['size']
    return cursor==end

checks=[]
for report in reports:
    uploads=report['uploads']
    assert contiguous(uploads,0xFFFF3000,0xFFFF4234)
    assert not contiguous(uploads[:-1],0xFFFF3000,0xFFFF4234)
    changed=[dict(r) for r in uploads]
    changed[1]['address']+=4
    assert not contiguous(changed,0xFFFF3000,0xFFFF4234)
    checks.append(report['path']+': upload geometry and two negative cases')
    if report['read_count']:
        assert report['read_count']==1200 and report['explicitly_logged_read_bytes']==614400
        assert not contiguous(report['reads'],0,0x100000)
        assert report['no_read_log_spans']==[['00086000','000C0000'],['000CF000','000FF000']]
        assert not report['flash_enable_logged'] and not report['flash_erase_logged'] and not report['flash_commit_logged']
        checks.append(report['path']+': incomplete full-ROM coverage correctly rejected')
    else:
        assert report['flash_enable_logged'] and report['flash_erase_logged'] and report['flash_commit_logged']

# Confirm this read-only branch did not change any manifest-pinned M0.6 inputs.
build=ROOT/'work/builds/m06_04'
frozen=json.loads((build/'manifest.json').read_text())
for name,digest in frozen['artifacts'].items():
    assert sha256((build/name).read_bytes()).hexdigest()==digest
for name,digest in frozen['sources'].items():
    assert sha256((ROOT/'work/M06'/name).read_bytes()).hexdigest()==digest
checks.append('All manifest-pinned frozen m06_04 artifacts and source hashes unchanged')

extraction=HERE/'static_extraction'
static_manifest=json.loads((extraction/'extraction_manifest.json').read_text())
for name,item in static_manifest['evidence'].items():
    assert sha256((extraction/name).read_bytes()).hexdigest()==item['sha256']
for name,digest in static_manifest['tools'].items():
    assert sha256(Path(name).read_bytes()).hexdigest()==digest
assert all(value=='FAIL' for value in static_manifest['gates'].values())
assert sha256(Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe').read_bytes()).hexdigest()=='5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115'
checks.append('Static extraction evidence/tool hashes match; installed executable unchanged; Read gates remain FAIL')

out=dict(status='PASS_EVIDENCE_REGRESSIONS',checks=checks,
         acquisition_approval='FAIL',physical_activity=False,
         command="& 'C:\\Program Files\\Python314\\python.exe' 'C:\\Dev\\Astra_A2WC511R\\reports\\local\\m07_residency\\ecuflash_read\\verify_evidence.py'")
(HERE/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
manifest=dict(schema=1,status='OFFLINE_AUDIT_COMPLETE_EXACT_ACQUISITION_UNAPPROVED',
    gates=dict(installed_target_inventory='PASS',historical_RAM_kernel_upload='PASS',
               protector_identification='PASS_BOUNDED',static_loader_recovery='PASS_BOUNDED_NOT_APPLICATION',
               exact_installed_kernel_identity='FAIL',complete_read_control_flow='FAIL',
               no_flash_side_effect_theorem='FAIL',exact_1MiB_coverage='FAIL',
               cleanup_and_reset_contract='FAIL',current_physical_ROM_attestation='FAIL'),
    frozen_M06='UNCHANGED_HASH_VERIFIED',
    reference_commits={'FastECU':'d7198f1c47791e67738576015789ebc2d740e55e',
        'FastECU-kernels':'d185a3e160a83e78425593c4c6450175bfa711e1',
        'subaru-ecu-flashing':'332a4858e2cc82f4d6131f4e94b633ced99a3a7b'},
    reference_sources_not_installed_implementation=True,
    static_extraction_manifest=dict(path=str(extraction/'extraction_manifest.json'),sha256=sha256((extraction/'extraction_manifest.json').read_bytes()).hexdigest()),
    files={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir())
           if p.is_file() and p.name!='manifest.json'})
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status=out['status'],checks=len(checks),gates=manifest['gates'],
    review_sha256=manifest['files']['ECUFLASH_READ_AUDIT.md'],
    manifest_sha256=sha256((HERE/'manifest.json').read_bytes()).hexdigest()),indent=2))
