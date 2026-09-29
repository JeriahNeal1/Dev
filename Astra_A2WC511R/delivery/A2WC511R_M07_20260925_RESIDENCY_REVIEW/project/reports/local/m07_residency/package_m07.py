"""Create a fresh review bundle. Never flash or overwrite an existing package."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse, json, shutil
ROOT=Path('C:/Dev/Astra_A2WC511R'); REPORT=ROOT/'reports/local/m07_residency'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'delivery/A2WC511R_M07_20260925_RESIDENCY_REVIEW')
    args=parser.parse_args();out=args.out.resolve()
    assert out.parent==ROOT/'delivery','Review packages stay in project delivery directory'
    assert not out.exists(),'Fresh output required'
    gates=json.loads((REPORT/'ENGINEERING_GATES.json').read_text())
    assert gates['release_allowed'] is False and gates['provably_owned_bytes']==0
    preserved=[]
    for base,manifest in [(ROOT,REPORT/'M06_FROZEN_MANIFEST.json'),
         (ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2',ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2/SHA256SUMS.json')]:
        expected=json.loads(manifest.read_text())['files']
        for rel,h in expected.items():assert sha(base/rel)==h,('Frozen content changed',rel)
        if base==ROOT:
            roots=['work/M06','work/builds/m06_04','work/builds/m06_repeat_05','reports/local/m06_architecture','integrations/m06']
            actual={p.relative_to(base).as_posix() for r in roots for p in (base/r).rglob('*') if p.is_file()}
            assert actual==set(expected),'Frozen M06 file set changed'
        preserved.append({'manifest':str(manifest),'sha256':sha(manifest),'verified_files':len(expected)})
    core=Path('C:/Dev/A2WC511R_Sim/sh2e.py')
    assert sha(core)=='b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff'
    assert sha(Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin'))=='22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
    out.mkdir()
    def copy(source,dest):
        target=out/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    def tree(source,dest):
        for p in sorted(source.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
                copy(p,Path(dest)/p.relative_to(source))
    for rel in ('work/M07','integrations/m07','reports/local/m07_residency'):
        tree(ROOT/rel,Path('project')/rel)
    for rel in ('AGENTS.md','reports/local/interfaces/checksum_audit.py',
        'reports/local/gate_closure/ida/defined_code_export.json',
        'reports/local/gate_closure/calibration/CURRENT_CALIBRATION_REVIEW.md',
        'reports/local/m06_architecture/protocol/ACQUISITION_COVERAGE_ADVISORY.md',
        'reports/local/m06_architecture/rom_reclamation/ROM_RECLAMATION_REVIEW.md',
        'reports/local/m06_architecture/rom_reclamation/reclamation_audit.json',
        'reports/local/m06_architecture/rom_reclamation/lookup_overlay_manifest.json',
        'reports/local/m06_architecture/build_audit/build_audit.json',
        'integrations/romraider/dist/romraider-bridge.jar',
        'work/romraider_acceptance/NativeChecksumCheck.java'):
        copy(ROOT/rel,Path('project')/rel)
    tree(ROOT/'work/romraider_acceptance/classes',Path('project/work/romraider_acceptance/classes'))
    sim=Path('C:/Dev/A2WC511R_Sim')
    for p in sorted(sim.glob('*.py')):copy(p,Path('simulator')/p.name)
    copy(sim/'README.md',Path('simulator/README.md'))
    tree(sim/'tests',Path('simulator/tests'))
    tree(sim/'backups/m07_start_75form_20260925',Path('simulator/backups/m07_start_75form_20260925'))
    for p in sorted((ROOT/'work/tools/m07_aplib').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            copy(p,Path('analysis_dependencies/m07_aplib')/p.relative_to(ROOT/'work/tools/m07_aplib'))
    for source,destination in [
        (Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin'),'inputs/A2WC511R.stock.bin'),
        (Path('C:/Dev/SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin.i64'),'inputs/current_metadata_only_IDB.i64'),
        (ROOT/'work/builds/m06_04/A2WC511R_M06.EXPERIMENTAL_NOT_FLASH_READY.raw.bin','comparison/M06.EXPERIMENTAL.raw.bin'),
        (ROOT/'work/builds/m06_04/A2WC511R_M06.EXPERIMENTAL.elf','comparison/M06.EXPERIMENTAL.elf'),
        (ROOT/'delivery/A2WC511R_M0_20260925_GATE_CLOSURE_v2/SHA256SUMS.json','comparison/M0_FROZEN_MANIFEST.json'),
        (REPORT/'M06_FROZEN_MANIFEST.json','comparison/M06_FROZEN_MANIFEST.json'),
        (REPORT/'ENGINEERING_GATES.json','ENGINEERING_GATES.json')]:
        copy(source,Path(destination))
    # Use the report's original relative paths from the front-page link.
    (out/'README.md').write_text('''# A2WC511R M0.7 review bundle

**ECU residency FAIL. No image is approved for flashing or physical testing.**
The supported deliverable is the offline stock-A8 host observation tool. ECU
research payloads are 100/148 bytes; 162 bytes of conditional executable savings
remain 0 proven owned bytes. No active-control feature is enabled.

Start with [the complete review](project/reports/local/m07_residency/M07_REVIEW.md),
[engineering gates](ENGINEERING_GATES.json), [exact fragment ownership](project/reports/local/m07_residency/OWNERSHIP_FRAGMENTS.json)
and [host tool usage](project/integrations/m07/README.md).

This is a source/evidence review snapshot of the existing C:\\Dev workspace, not
a portable installer or a flashing procedure. Scripts intentionally retain
their reviewed workspace and installed-tool paths. Licensed GNUSH/RomRaider,
official IDA, Python/Java and local analysis-tool inputs are identified in logs,
profiles and manifests; installed proprietary tools are not redistributed here.
The simulator source/test snapshot is in simulator/. Use its README for scoped
semantic/ownership checks. Do not regenerate outputs into frozen original trees.

Current M0.6 comparison binaries and both old manifests are included. The full
M0 and 211-file M0.6 sets remain in their original verified workspace locations;
this package does not claim to duplicate every historical file. Frozen files
were verified before packaging. The current IDB copy contains comments only;
its mapped bytes retain the original four-byte-stamp variant, distinct from the
stock build input. All images are offline research artifacts.

The A0 exact-image acquisition procedure is withdrawn. ECUFlash Read/kernel
coverage, flash-exclusion and cleanup are unresolved; the audit offers only
conditional future ordering. No physical action is requested by this bundle.

SHA256SUMS.json covers every other file, including this notice. Verification is
read-only with verify_package.py; its manifest is integrity evidence, not an
ownership or physical-safety certificate.
''',encoding='utf-8')
    (out/'PRESERVATION.json').write_text(json.dumps({'status':'PASS','frozen':preserved,
        'core_sha256':sha(core),'M06_file_set_unchanged':True},indent=2)+'\n',encoding='utf-8')
    (out/'verify_package.py').write_text('''from pathlib import Path
from hashlib import sha256
import json
root=Path(__file__).resolve().parent
manifest=root/'SHA256SUMS.json'
expected=json.loads(manifest.read_text())['files']
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=manifest}
assert actual==set(expected),'Package file set differs'
for rel,value in expected.items():
    assert sha256((root/rel).read_bytes()).hexdigest()==value,rel
print(json.dumps({'status':'PASS','files':len(expected),'manifest_sha256':sha256(manifest.read_bytes()).hexdigest()}))
''',encoding='utf-8')
    files={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    manifest=out/'SHA256SUMS.json'
    manifest.write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),
        'classification':'OFFLINE_REVIEW_BUNDLE_NOT_APPROVED_ECU_RESIDENCY','files':files},indent=2)+'\n',encoding='utf-8')
    for rel,h in files.items():assert sha(out/rel)==h,rel
    print(json.dumps({'status':'PASS','path':str(out),'files':len(files),
        'manifest_sha256':sha(manifest),'bytes':sum((out/p).stat().st_size for p in files),'ECU_release_allowed':False}))
if __name__=='__main__':main()
