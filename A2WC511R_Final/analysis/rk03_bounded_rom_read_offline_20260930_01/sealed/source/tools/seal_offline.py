"""Preserve the fixed-read offline result. No vehicle/native process or provider launch."""
from pathlib import Path
import datetime as dt,hashlib,json,stat,subprocess
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_rom_read_offline_20260930_01')
STATE=Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json')
EXPECTED='bf240d6c64257aca1952295c8a7bee03be714179124e002cdf45854d599aa0f6'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def require(ok,detail):
    if not ok:raise RuntimeError(detail)
def save(p,d):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()
def verify(obj):
    if isinstance(obj,dict):
        if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str):
            p=pin(obj['path']);require(p['sha256']==obj['sha256'],'Changed input '+obj['path'])
            if 'bytes' in obj:require(p['bytes']==obj['bytes'],'Changed size '+obj['path'])
        for v in obj.values():verify(v)
    elif isinstance(obj,list):
        for v in obj:verify(v)
def main():
    require(not git('status','--porcelain'),'Commit source before sealing')
    require(git('branch','--show-current')=='rk03/bounded-rom-read-offline','Wrong source branch')
    require(not (REPO/'physical_session').exists(),'Offline worktree must never have a physical session')
    require(not (A/'sealed').exists(),'Never overwrite sealed output')
    tests=read(A/'qualification_tests/TEST_REPORT.json');verify(tests)
    require(tests['status']=='PASS' and tests['tests']==tests['passed']==122 and tests['negative_fault_cases']==78,'Tests incomplete')
    reviews=[A/'instruction_review/INDEPENDENT_REVIEW.json',A/'root_instruction_review/ROOT_INSTRUCTION_REVIEW.json',A/'instruction_review/PACKAGING_REVIEW.json']
    for p in reviews:
        r=read(p);verify(r);require(r['status'].startswith('PASS'),'Review failure')
    instruction_ref=read(A/'instruction_review/INSTRUCTION_REVIEW.json');verify(instruction_ref)
    instruction=read(instruction_ref['replay']['path']);verify(instruction)
    require(instruction['status'].startswith('PASS') and instruction['new_read_requests']==1 and instruction['ROM_data_read_events']==512,'Instruction evidence incomplete')
    require(instruction['physical_operations']==instruction['provider_loads']==0,'Instruction scope violation')
    inputs=read(ROOT/'contract/SOURCE_PINS.json');verify(inputs)
    c=read(ROOT/'contract/CONTRACT.json')
    require(c['maximum_transmits']==25 and c['ROM_read_count']==1 and c['fixed_read']['address']=='00000000' and c['fixed_read']['length']==512,'Wrong bounded scope')
    require(c['frames'][-1]['tx']==instruction['request_hex'] and c['frames'][-1]['rx']==instruction['response_hex'],'Model/CPU contract differs')
    builds=[ROOT/('build_'+s) for s in ('a','b')]
    for b in builds:
        manifest=read(b/'BUILD_MANIFEST.json')
        for row in manifest['source']:
            p=pin(ROOT/'src'/row['name']);require(p['sha256']==row['sha256'] and p['bytes']==row['bytes'],'Build source drift')
        require(pin(b/'rk03_bounded_rom_read_offline.pyz')['sha256']==EXPECTED,'Build hash changed')
    require((builds[0]/'BUILD_MANIFEST.json').read_bytes()==(builds[1]/'BUILD_MANIFEST.json').read_bytes(),'Build manifests differ')
    require((builds[0]/'rk03_bounded_rom_read_offline.pyz').read_bytes()==(builds[1]/'rk03_bounded_rom_read_offline.pyz').read_bytes(),'Build bytes differ')
    source=[REPO/p for p in git('ls-files','bounded_rom_read').splitlines()]
    require(source and not any('draft_revision1' in str(p) for p in source),'Invalid source closure')
    sealed=A/'sealed';sealed.mkdir(exist_ok=False)
    copies=[]
    for p in source+[b/name for b in builds for name in ['rk03_bounded_rom_read_offline.pyz','BUILD_MANIFEST.json']]:
        target=sealed/'source'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(p.read_bytes())
        require(pin(target)['sha256']==pin(p)['sha256'],'Snapshot copy mismatch');copies.append(pin(target))
    image=Path(r'C:\Dev\A2WC511R_ReadKernel\build\rk02_01\kernel.bin')
    require(pin(image)['sha256']==c['image_sha256'],'Kernel changed')
    for p,name in [(image,'unchanged_kernel_image.bin'),(A/'EXPECTED_FIRST512_CURRENT.bin','expected_first512_current.bin')]:
        with (sealed/name).open('xb') as f:f.write(p.read_bytes())
        copies.append(pin(sealed/name))
    cert=dict(schema=1,status='PASS_OFFLINE_RK03_BOUNDED_ROM_READ',sealed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        source_branch=git('branch','--show-current'),source_commit=git('rev-parse','HEAD'),
        artifact_kind='DETERMINISTIC_PYTHON_ZIPAPP_STATIC_FAKE_MODEL',model_sha256=EXPECTED,
        canonical_build_manifest_sha256=pin(builds[0]/'BUILD_MANIFEST.json')['sha256'],
        test_count=122,tests_passed=122,negative_fault_cases=78,qualification_tests=pin(A/'qualification_tests/TEST_REPORT.json'),
        independent_reviews=[pin(p) for p in reviews],instruction_replay=instruction_ref['replay'],
        instruction_count=instruction['instruction_count'],new_instruction_read_requests=1,
        prior_upload_start_identity_instructions_reexecuted=0,maximum_transmits=25,
        uploaded_image_sha256=c['image_sha256'],uploaded_image_bytes=1808,start_count=1,identity_count=1,
        ROM_read_requests=1,address='00000000',length=512,pass_number=0,end_exclusive='00000200',
        request_hex=instruction['request_hex'],expected_reply_sha256=instruction['response_sha256'],
        expected_data_sha256=instruction['data_sha256'],current_ROM_sha256='bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2',
        second_read_allowed=False,arbitrary_address_or_payload=False,flash_operations=0,provider_loads=0,
        physical_operations_this_scope=0,physical_status='NOT_RUN_NOT_AUTHORIZED_IN_THIS_SCOPE',
        sealed_source_and_builds=copies,future_plan=pin(ROOT/'FUTURE_PHYSICAL_RELEASE_PLAN.md'),
        limits=['This qualification applies only to a static fake model and one SH-2E instruction continuation.',
          'No physical bounded ROM read occurred. The completed physical stage stopped after identity.',
          'The first512 bytes also match stock; this block cannot identify complete calibration or the entire current ROM.',
          'Recorded prefix is reused as data; prior transport/seed/image qualification is not rerun or added to the test count.',
          'Streaming receive fragmentation, native ABI/deadlines and physical recovery require a separately qualified future native release.',
          'Instruction/peripheral ticks are declared simulation assumptions, not silicon timing.'])
    save(sealed/'QUALIFICATION.json',cert);cert_pin=pin(sealed/'QUALIFICATION.json')
    paths=set(source+[A/'ROOT_FIXED_READ_CONTRACT.json',A/'EXPECTED_FIRST512_CURRENT.bin',Path(instruction_ref['replay']['path'])])
    for directory in [ROOT/'build_a',ROOT/'build_b',ROOT/'draft_revision1',A/'qualification_tests',A/'instruction_review',A/'root_instruction_review',A/'development_attempt_01',sealed]:
        paths.update(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.update(Path(p['path']) for p in inputs['inputs'])
    save(sealed/'PRESERVATION_MANIFEST.json',dict(status='SEALED_OFFLINE_FIXED_FIRST512_READ_PASS',qualification=cert_pin,files=[pin(p) for p in sorted(paths)]))
    verify(cert)
    for directory in [sealed,ROOT/'build_a',ROOT/'build_b',A/'qualification_tests',A/'instruction_review',A/'root_instruction_review']:
        for p in directory.rglob('*'):
            if p.is_file():p.chmod(stat.S_IREAD)
    now=cert['sealed_utc'];cp=A/'CHECKPOINT.json';checkpoint=read(cp)
    checkpoint.update(status='PASS_OFFLINE_RK03_BOUNDED_ROM_READ_SEALED',qualification=cert_pin,source_commit=cert['source_commit'],tests_passed=122,physical_operations=0,provider_loads=0,next_milestone='SEPARATELY_QUALIFY_RK03_BOUNDED_ROM_READ_PHYSICAL',updated_utc=now)
    cp.write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    state=read(STATE);save(A/'STATE_BEFORE_OFFLINE_SEAL.json',state)
    state.update(phase='RK03_IDENTITY_PHYSICAL_AND_OEM_RETURN_PASS_BOUNDED_READ_OFFLINE_PASS',
        RK03_BOUNDED_ROM_READ='PASS_OFFLINE',bounded_read_qualification=cert_pin,bounded_read_commit=cert['source_commit'],
        bounded_read_model_sha256=EXPECTED,bounded_read_tests=122,bounded_read_physical_operations=0,
        human_required=[],human_action_required=False,further_physical_activity_allowed=False,
        next_action='Report completed physical identity/OEM return and offline bounded read; future native bounded-read release requires separate qualification and authorization',updated_utc=now)
    STATE.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    require(not git('status','--porcelain'),'Unexpected source drift')
    print(json.dumps(dict(status=cert['status'],qualification=cert_pin,model_sha256=EXPECTED,source_commit=cert['source_commit'],tests_passed=122,physical_operations=0)))
if __name__=='__main__':main()
