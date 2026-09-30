"""Seal this completed offline model only, with no physical executable invocation."""
from pathlib import Path
import datetime,hashlib,json,shutil,stat,subprocess

HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Dev\A2WC511R_RK03_KernelIdentityOffline')
SOURCE=REPO/'kernel_identity'
KERNEL=Path(r'C:\Dev\A2WC511R_ReadKernel\build\rk02_01\kernel.bin')
MODEL_SHA='04d8332493c98e90fa3c537c8ea0bc12926b5a85e37ea8ea9c826ec8e03c34fe'
IMAGE_SHA='3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,value):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def verify_nested_pins(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            assert digest(value['path'])==value['sha256'],value['path']
        for item in value.values():verify_nested_pins(item)
    elif isinstance(value,list):
        for item in value:verify_nested_pins(item)

def main():
    tests=read(HERE/'qualification_tests/TEST_REPORT.json')
    independent=read(HERE/'instruction_review/INDEPENDENT_REVIEW.json')
    instruction_index=read(HERE/'instruction_review/INSTRUCTION_REVIEW.json')
    replay=read(instruction_index['replay']['path'])
    assert tests['status']=='PASS' and tests['test_count']==tests['passed']==526
    assert independent['status'].startswith('PASS') and not independent.get('blocking_findings',[])
    verify_nested_pins(independent)
    assert replay['status']=='PASS_OFFLINE_OEM_START_AND_SINGLE_KERNEL_IDENTITY'
    assert digest(instruction_index['replay']['path'])==instruction_index['replay']['sha256']
    for p in replay['inputs']:assert digest(p['path'])==p['sha256'],p['path']
    for p in read(SOURCE/'contract/SOURCE_PINS.json')['inputs']:assert digest(p['path'])==p['sha256'],p['path']
    assert not git('status','--porcelain')
    branch=git('branch','--show-current');commit=git('rev-parse','HEAD')
    assert branch=='rk03/kernel-start-identity-offline'
    for label in ('a','b'):assert digest(SOURCE/('build_'+label)/'rk03_kernel_start_identity_offline.pyz')==MODEL_SHA
    assert (SOURCE/'build_a/BUILD_MANIFEST.json').read_bytes()==(SOURCE/'build_b/BUILD_MANIFEST.json').read_bytes()
    assert digest(KERNEL)==IMAGE_SHA and KERNEL.stat().st_size==1808
    sealed=HERE/'sealed';sealed.mkdir(exist_ok=False)
    tracked=git('ls-files','kernel_identity').splitlines();copied=[]
    for name in tracked:
        src=REPO/name;target=sealed/'source'/Path(name).relative_to('kernel_identity')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
        assert digest(src)==digest(target);copied.append(pin(target))
    shutil.copyfile(KERNEL,sealed/'unchanged_kernel_image.bin')
    limits=[
        'Offline deterministic model qualification only; this zipapp has no physical provider boundary.',
        'Captured22-transmit prefix and fixed seed/key are replayed as data; earlier native287test qualification is reused, not rerun or recounted.',
        'Instruction replay executes the fixed start/identity path under declared peripheral fixtures. It does not establish silicon timing or physical kernel execution.',
        'The unchanged kernel image contains its preexisting acquisition command. This artifact and replay expose only fixed identity01; no acquisition path is exercised.',
        'Native ABI, receive fragmentation, real deadlines, opaque provider handles and physical recovery require the future separately qualified physical release.'
    ]
    certificate={'schema':1,'status':'PASS_OFFLINE_RK03_KERNEL_START_IDENTITY_ONLY','sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'artifact_kind':'DETERMINISTIC_PYTHON_ZIPAPP_STATIC_FAKE_MODEL','source_branch':branch,'source_commit':commit,
        'model_sha256':MODEL_SHA,'canonical_build_manifest_sha256':digest(SOURCE/'build_a/BUILD_MANIFEST.json'),
        'uploaded_image_sha256':IMAGE_SHA,'uploaded_image_bytes':1808,'entry':'FFFF3004',
        'start_frame':'8010f003310101b6','start_ack':'80f01003710101f6',
        'identity_request':'beef000101af','identity_reply':'beef000f8141325743353131522d524b3032005f',
        'identity_ascii':'A2WC511R-RK02\u0000','maximum_transmits':24,'fixed_upload_chunks':15,'start_count':1,'identity_request_count':1,
        'test_count':526,'tests_passed':526,'negative_tests':433,
        'qualification_tests':pin(HERE/'qualification_tests/TEST_REPORT.json'),
        'independent_review':pin(HERE/'instruction_review/INDEPENDENT_REVIEW.json'),
        'instruction_review':pin(HERE/'instruction_review/INSTRUCTION_REVIEW.json'),'instruction_replay':instruction_index['replay'],
        'physical_operations_this_scope':0,'provider_loads':0,'ROM_acquisition_requests':0,'flash_operations':0,
        'physical_status':'NOT_RUN_NOT_AUTHORIZED_IN_THIS_SCOPE','future_plan':pin(SOURCE/'FUTURE_PHYSICAL_RELEASE_PLAN.md'),
        'sealed_source_and_builds':copied,'sealed_image':pin(sealed/'unchanged_kernel_image.bin'),'limits':limits}
    save(sealed/'QUALIFICATION.json',certificate)
    result={'RK03_KERNEL_START_IDENTITY_ONLY':'PASS_OFFLINE','physical_operations':0,'branch':branch,'commit':commit,
        'model_sha256':MODEL_SHA,'qualification':pin(sealed/'QUALIFICATION.json'),'test_count':526,'negative_cases':433,
        'independent_review':'PASS','next_milestone':'SEPARATELY_QUALIFY_RK03_KERNEL_START_IDENTITY_ONLY_PHYSICAL',
        'physical_authorization_required_later':'PROCEED RK03 KERNEL START IDENTITY'}
    save(HERE/'RESULT.json',result)
    report=f'''# RK03_KERNEL_START_IDENTITY_ONLY — OFFLINE PASS

The static-fake model passed **526/526 checks**, including **433 negative cases**. Independent review passed. No physical operation or provider load occurred in this scope. Completed transition, first-chunk, full-upload and OEM-return physical PASS evidence remains unchanged.

Source branch: `{branch}`. Commit: `{commit}`.

Both clean builds produced the same 81,146-byte Python zipapp. This is an executable model, not a native physical release:

`{MODEL_SHA}`

Canonical build manifest SHA256: `{certificate['canonical_build_manifest_sha256']}`.

Qualification certificate SHA256: `{result['qualification']['sha256']}`.

## Fixed boundary

The reviewed transport/session setup and all 15 fixed upload chunks are retained. All 15 exact `76` acknowledgements are required before one start. The modeled sequence contains 24 transmissions total and stops after one exact identity response, followed only by cleanup.

| Contract | Value |
|---|---|
| Unchanged uploaded image | 1,808 bytes, SHA256 `{IMAGE_SHA}` |
| Entry | `FFFF3004` |
| Start at 15625 baud | `8010f003310101b6` |
| Start ACK | `80f01003710101f6` |
| After ACK | stop OEM filter, set 62500 baud, install fixed BEEF pass filter |
| Identity request | `beef000101af` |
| Identity reply | `beef000f8141325743353131522d524b3032005f` |
| Actual identity | `A2WC511R-RK02` followed by NUL |

SSM uses an 8-bit payload length; BEEF uses a 16-bit big-endian length. Both append the sum of preceding frame bytes modulo 256. The identity body is 15 bytes and the complete reply is 20 bytes. RK03 names the host workflow; the pinned kernel identity remains RK02.

## Evidence and exclusions

The first 22 frames match the successful physical full-upload log. Address, length, cipher hash and frame checks retain all 15 chunks, including repeated payload hashes at different addresses. The previously verified complete RAM image is reused unchanged.

The instruction review resumes retained post-upload state and verifies that the exact OEM start path reaches `FFFF3004`; it then executes the unchanged kernel's identity path. Both poisoned-register and actual OEM-register cases pass. Its detailed report records peripheral assumptions and coverage. No kernel ROM-data read or flash write occurs in that path. Simulation does not establish silicon timing or a physical kernel-start PASS.

The distributable contains only three Python modules and standard-library JSON, hash and console support. It has no external file input, provider loading, OpenPort interface, dynamic backend, entry/payload/address selector, ROM-read command, flash operation, second start or retry. The fixed identity request is the only custom-kernel command. The underlying unchanged kernel's older read capability is not exposed by this artifact.

Negative cases cover every modeled call failure, output mismatch, each exchange's malformed/checksum/length/status replies, wrong identity and version, short virtual waits, and cleanup failure. Cleanup after failures is verified without a later protocol transmission. The existing 287 native qualification cases were reused, not counted again.

## Next milestone

Separately qualify **RK03_KERNEL_START_IDENTITY_ONLY_PHYSICAL** using the future plan. Native boundary integration, ABI/stream handling, real deadlines and timing, filter/baud transition and launch-once controls remain release work. No vehicle run is authorized by this package. A later qualified release must use only IGNITION OFF, TEST MODE ON, NORMAL MODE ON and require exactly `PROCEED RK03 KERNEL START IDENTITY` before its single invocation.

The future stage ends after identity and cleanup, then ignition OFF, normal mode, and passive OEM return. It must not read ROM.
'''
    with (HERE/'RK03_KERNEL_START_IDENTITY_ONLY_RESULT.md').open('x',encoding='utf-8') as f:f.write(report)
    checkpoint=read(HERE/'CHECKPOINT.json');checkpoint.update(status='SEALED_OFFLINE_PASS',qualification=result['qualification'],next_milestone=result['next_milestone'])
    (HERE/'CHECKPOINT.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
    # Only this newly created analysis tree is enumerated and sealed.
    files=[p for p in HERE.rglob('*') if p.is_file()]
    save(sealed/'PRESERVATION_MANIFEST.json',{'scope':'NEW_OFFLINE_IDENTITY_ANALYSIS_ONLY','files':[pin(p) for p in sorted(files)]})
    for p in files+[sealed/'PRESERVATION_MANIFEST.json']:p.chmod(stat.S_IREAD)
    state=Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json');s=read(state)
    s.update(phase='RK03_KERNEL_START_IDENTITY_OFFLINE_SEALED_PASS',full_upload_physical_status='PASS',
        RK03_KERNEL_START_IDENTITY_ONLY='PASS_OFFLINE',kernel_identity_physical_operations=0,kernel_identity_tests='526/526',
        kernel_identity_branch=branch,kernel_identity_commit=commit,kernel_identity_model_sha256=MODEL_SHA,
        kernel_identity_qualification=result['qualification'],kernel_identity_result=str(HERE/'RESULT.json'),
        completion_claimed=True,completion_scope='RK03_KERNEL_START_IDENTITY_ONLY offline model qualification only',
        completion_report=str(HERE/'RESULT.json'),completion_manifest=str(sealed/'PRESERVATION_MANIFEST.json'),
        completion_manifest_sha256=digest(sealed/'PRESERVATION_MANIFEST.json'),
        future_physical_release_plan=str(SOURCE/'FUTURE_PHYSICAL_RELEASE_PLAN.md'),
        kernel_identity_physical_status='NOT_RUN_NOT_AUTHORIZED_IN_THIS_SCOPE',human_required=[],
        further_physical_activity_allowed=False,human_action_required=False,next_action=result['next_milestone'],
        updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    state.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':main()
