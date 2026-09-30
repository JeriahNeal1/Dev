"""Seal offline qualification only; leaves the first human gate pending."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical')
ROOT=REPO/'first_chunk'
OUT=HERE/'qualification'
def require(ok,why):
    if not ok:raise RuntimeError(why)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(Path(p)),bytes=Path(p).stat().st_size,sha256=sha(p))
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
files={}
def add(p,expected=None):
    row=pin(p)
    require(expected is None or row['sha256']==expected.lower(),'Pin changed: '+str(p))
    prior=files.get(row['path'])
    require(prior is None or prior['sha256']==row['sha256'],'Conflicting input pin')
    files[row['path']]=row
    return row
def walk(obj):
    if isinstance(obj,dict):
        if 'path' in obj and 'sha256' in obj:add(obj['path'],obj['sha256'])
        for v in obj.values():walk(v)
    elif isinstance(obj,list):
        for v in obj:walk(v)
def new_json(path,obj):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')

require(git('branch','--show-current')=='rk03/first-chunk-physical','Isolated branch')
commit=git('rev-parse','HEAD')
require(commit=='76f8bc16495529645f10fab6dd5f5b522cbe190b','Reviewed commit')
require(git('rev-parse','HEAD^')=='2a8eeee2a7ff251346314c54d6dd028f6df93766','Preserved parent')
require(not git('status','--porcelain','--untracked-files=no'),'Dirty tracked source')
preserved_branches={}
for branch,expected in [('rk03/post-transition-offline','2a8eeee2a7ff251346314c54d6dd028f6df93766'),
 ('rk03/transition-probe','6d2a076cc8cf90f023211c1e71ad5571e7b0ee8d'),
 ('rk03/explicit-serial-init','00664cbe83c35eee0faffd4161c76fc70888984f')]:
    actual=git('rev-parse',branch);require(actual==expected,'Historical branch changed');preserved_branches[branch]=actual
exe=add(ROOT/'build_a/rk03_first_chunk_probe32.exe','3a6abe4e11fc6a85682c33018e67b533897860a932962f2840976fbd35ed1c02')
replica=add(ROOT/'build_b/rk03_first_chunk_probe32.exe',exe['sha256'])
require(Path(exe['path']).read_bytes()==Path(replica['path']).read_bytes(),'Nonidentical clean builds')
contract=add(HERE/'FIRST_CHUNK_REVIEW_CONTRACT.json','a7482b0eba224c9642745b830c71b3fff14f987988a58cdc1376e45dc0aa839c')
pointer=read(ROOT/'reports/LATEST_QUALIFICATION.json');report_path=Path(pointer['report']['path'])
test=read(report_path)
require(test['status']=='PASS' and test['passed_cases']==test['test_cases']==156,'All offline cases required')
require(test['physical_operations']==test['real_provider_loads']==0,'No physical qualification run')
require(all(v is None for v in test['physical_controls_after'].values()),'Physical session already used')
walk(test);add(report_path,pointer['report']['sha256'])
reviews={}
for key,relative in [('native','native_review/NATIVE_REVIEW.json'),('root','root_review/ROOT_REVIEW.json'),
                     ('launcher','native_review/LAUNCHER_REVIEW.json'),('recovery','native_review/RECOVERY_REVIEW.json')]:
    path=HERE/relative;doc=read(path)
    require(doc['status'].startswith('PASS'),'Review not passing: '+key)
    require(doc.get('unresolved_findings',[])==[],'Review has unresolved findings: '+key)
    walk(doc);reviews[key]=add(path)
require(read(reviews['native']['path'])['physical_executable']['sha256']==exe['sha256'],'Independent review must bind final executable')
for relative,count in [('LAUNCHER_TESTS_V2.json',36),('LAUNCHER_TESTS_V2_OPTIMIZED.json',36),('OEM_RETURN_CONTROL_TESTS_V2.json',14)]:
    doc=read(HERE/relative);require(doc['status']=='PASS' and doc['checks_passed']==count,'Control test gate');walk(doc);add(HERE/relative)
for p in [ROOT/'README.md',ROOT/'INPUT_PINS.json',ROOT/'.gitignore',REPO/'.gitignore',
          HERE/'launch_first_chunk_once.py',HERE/'check_clients.ps1',HERE/'launch_oem_return_once.py',
          HERE/'SUPERSESSION_STATUS.json',HERE/'SUPERSESSION_STATUS.md',HERE/'PRESERVED_CHECKPOINT_VERIFICATION.json',Path(__file__)]:add(p)
for p in (ROOT/'tools').iterdir():
    if p.is_file():add(p)
for name in ['NATIVE_REVIEW.md','NATIVE_REVIEW_MANIFEST.json']:
    add(HERE/'native_review'/name)
prior=read(HERE/'PRESERVED_CHECKPOINT_VERIFICATION.json')
require(prior['status']=='PASS' and prior['files_checked']==846 and not prior['failures'],'Original evidence preservation')
add(prior['source_manifest']['path'],prior['source_manifest']['sha256'])
rom=add(Path(r'C:\Dev\SubaruRoms\current.bin'),'bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2')
gates=read(HERE/'FIRST_CHUNK_GATE_STATE.json')
require(gates['probe_invocation_count']==0 and gates['commit_authorization'] is None and not gates['launch_reserved'],'New human authorization absent')
require(not gates['completed_pre_probe_gates'],'Fresh ignition gates must follow qualification')
session=REPO/'physical_session/RK03_FIRST_CHUNK_01'
require(not session.exists(),'Physical session must not exist before human gates')
stamp=datetime.now(timezone.utc).isoformat()
cert=dict(schema=1,created_utc=stamp,status='PASS_OFFLINE_QUALIFIED_FIRST_CHUNK_ONLY',session_id='RK03_FIRST_CHUNK_01',
    branch=git('branch','--show-current'),commit=commit,preserved_branches=preserved_branches,
    physical_executable=exe,reproducible_build_executable=replica,review_contract=contract,
    native_test_report=pin(report_path),native_cases_passed=156,
    case_groups={'prior_model_reused_and_replayed':127,'exact_successful_physical_transition_added':1,'real_clock_fake':4,'bootstrap_fake':24},
    independent_reviews=reviews,launcher_checks=36,launcher_optimized_checks=36,recovery_control_checks=14,
    fixed_transfer=read(contract['path'])['fixed_transfer'],expected_ecu_id='2F12515306',
    physical_authorization_received=False,physical_probe_invocations=0,maximum_physical_invocations=1,
    requires_exact_human_authorization='PROCEED RK03 FIRST CHUNK PROBE',
    full_acquisition_allowed=False,retry_allowed=False,kernel_start_allowed=False,flash_operations_allowed=False,
    human_state_policy='IGNITION OFF -> TEST MODE ON -> exact software authorization -> one probe -> IGNITION OFF -> NORMAL MODE ON -> passive OEM return',
    current_physical_rom=rom,current_executable_identical_to_stock=True,
    current_rom_classification_basis='Reused sealed current-ROM report; no new ROM ingestion or comparison.',
    next_stage_after_physical_pass='Prepare and qualify FULL_KERNEL_UPLOAD_NO_START offline only; do not execute it.',
    limits=['Offline qualification does not establish physical first-chunk success.',
            'The declaration retains1808 bytes but the executable embeds and can send only first128 bytes.',
            'Real-clock fake waits prove host minimum waits, not electrical K-line timing.',
            'Baud15625 SET/output integrity checked; no effective baud GET or waveform claim.',
            'A failed36 may already have changed RAM; recovery is required after an attempt.',
            'No second36, full kernel, custom kernel execution, ROM read or flash path exists in this executable.',
            'Initial Git whitespace check treats CRLF as whitespace; after CR handling only unchanged vendor-header whitespace remains, preserved to retain the exact SDK hash.'],
    files=list(sorted(files.values(),key=lambda r:r['path'])))
OUT.mkdir(exist_ok=False)
new_json(OUT/'QUALIFICATION.json',cert)
cert_pin=pin(OUT/'QUALIFICATION.json')
md=f'''# First-chunk probe qualification

OFFLINE QUALIFICATION = PASS (156/156 cases)
RK03_FIRST_CHUNK_PHYSICAL = NOT_RUN

The supersession note records the earlier transition and OEM-return physical PASS results without changing historical reports. The new first-chunk executable is qualified separately and has not contacted the vehicle.

- Branch: `{cert['branch']}`
- Commit: `{commit}`
- Executable SHA256: `{exe['sha256']}`
- Qualification SHA256: `{cert_pin['sha256']}`
- Two clean builds are byte-identical.
- Independent native, runner/evidence, launcher and recovery reviews passed.
- All16 seed vectors and the exact successful BF/81/83 transcript passed; all12 real-clock waits meet the requested minima.
- The physical path can send one fixed128-byte36 at FFFF3000 after one34, then requires exact76 and closes transport.
- Original846 checkpoint files and current.bin remain hash-identical.

The next required human state is IGNITION OFF, followed by TEST MODE ON and the exact new authorization PROCEED RK03 FIRST CHUNK PROBE. No physical authorization is recorded. There will be no automatic retry.

After the attempt, recovery requires IGNITION OFF then NORMAL MODE ON, followed by the unchanged passive BF/A8 OEM-return observer. Full-kernel-upload-no-start preparation is conditional on physical PASS and remains offline only.
'''
with (OUT/'QUALIFICATION.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
new_json(OUT/'MANIFEST.json',dict(status='SEALED_FIRST_CHUNK_OFFLINE_QUALIFICATION',files=[pin(p) for p in OUT.iterdir() if p.is_file()]))
for p in OUT.iterdir():p.chmod(0o444)
for sub in ['build_a','build_b','reports']:
    for p in (ROOT/sub).rglob('*'):
        if p.is_file():p.chmod(0o444)
for p in [HERE/'SUPERSESSION_STATUS.json',HERE/'SUPERSESSION_STATUS.md',HERE/'FIRST_CHUNK_REVIEW_CONTRACT.json']:p.chmod(0o444)
gates.update(status='QUALIFIED_WAITING_IGNITION_OFF',qualification_sha256=cert_pin['sha256'],qualification_path=cert_pin['path'],
    physical_executable_sha256=exe['sha256'],next_gate='IGNITION OFF',updated_utc=stamp)
(HERE/'FIRST_CHUNK_GATE_STATE.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
statepath=Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json');state=read(statepath)
state.update(phase='RK03_FIRST_CHUNK_QUALIFIED_WAITING_IGNITION_OFF',first_chunk_qualification=cert_pin['path'],
    first_chunk_qualification_sha256=cert_pin['sha256'],first_chunk_executable_sha256=exe['sha256'],
    first_chunk_commit=commit,first_chunk_offline_cases_passed=156,first_chunk_physical_invocations=0,
    first_chunk_physical_authorization_received=False,first_chunk_physical_status='NOT_RUN',
    human_required=['IGNITION OFF'],next_action='Fresh IGNITION OFF, then TEST MODE ON, then exact PROCEED RK03 FIRST CHUNK PROBE; one attempt only',updated_utc=stamp)
statepath.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':cert['status'],'qualification':cert_pin,'files_pinned':len(files),'next_gate':'IGNITION OFF'}))
