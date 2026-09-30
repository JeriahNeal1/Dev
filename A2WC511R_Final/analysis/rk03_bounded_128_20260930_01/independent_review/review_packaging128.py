"""Read-only final packaging review; no test, compiler, provider, or hardware invocation."""
from pathlib import Path
import hashlib,json,datetime,ast,re
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_128_20260930_01')
REPO=Path(r'C:\Dev\A2WC511R_RK03_Bounded128Physical');ROOT=REPO/'bounded_128_physical'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def verify(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):check(pin(v['path'])['sha256']==v['sha256'],'unchanged pin '+v['path'])
  for x in v.values():verify(x)
 elif isinstance(v,list):
  for x in v:verify(x)
sealer=ROOT/'tools/seal_bounded_release.py';reviewer=ROOT/'tools/root_review.py';doc=ROOT/'README.md';interp=A/'CONTRACT_INTERPRETATION.json'
seal=sealer.read_text();root_source=reviewer.read_text();interpretation=read(interp);contract=read(A/'PHYSICAL_BOUNDED_128_REVIEW_CONTRACT.json')
ast.parse(seal);ast.parse(root_source)
check("rk03/bounded-128-physical" in seal and "rk03_bounded_128_20260930_01" in seal,'new branch and analysis target')
check("PHYSICAL_BOUNDED_128_REVIEW_CONTRACT.json" in seal and "'beef0008030000000000008038'" in seal and "['length']==128" in seal,'fixed128 contract validated by sealer')
check("808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653" in seal,'new kernel pin required')
check("kernel_review/LATEST_KERNEL_TESTS.json" in seal and "kt['passed_cases']==kt['test_cases']==17" in seal,'new17 instruction cases mandatory')
check("OUT/'independent_review/PACKAGING_REVIEW.json'" in seal,'final packaging review mandatory')
check("OUT/'independent_review/REVIEW.json'" in seal and "OUT/'root_review/REVIEW.json'" in seal and "assert r['status']=='PASS';verify(r)" in seal,'independent native and kernel reviews mandatory with pins')
check("'bounded_128_physical','kernel128'" in seal and "REPO/'kernel128/build'" in seal,'source snapshot and certificate include both new native and kernel tree')
check("retained_512_reference_qualification=" in seal and "kernel_instruction_tests=ktref['report']" in seal and "fixed_upload_manifest=pin(OUT/'FIXED_UPLOAD_128_MANIFEST.json')" in seal,'historical512 evidence explicitly distinguished from newkernel and upload proof')
check("contract_interpretation=pin(OUT/'CONTRACT_INTERPRETATION.json')" in seal,'provenance interpretation bound into certificate')
check("PASS_OFFLINE_QUALIFIED_PHYSICAL_BOUNDED_ROM_READ_128_ONLY" in seal and "maximum_ROM_requests=1" in seal and "maximum_requests=25" in seal,'correct limited128 certificate status')
check("physical_authorization_received=False" in seal and "status='WAITING_IGNITION_OFF'" in seal and "probe_invocation_count=0" in seal and "BOUNDED_128_GATE_STATE.json" in seal,'unconsumed new gate state without authorization')
check("requires_exact_human_authorization=c['requires_exact_human_authorization']" in seal and contract['requires_exact_human_authorization']=='PROCEED RK03 128 BYTE ROM READ','exact fresh128 token binding')
check("git('status','--porcelain')" in seal and "assert not (REPO/'physical_session').exists()" in seal,'clean source and absent physical session required before sealing')
check("arbitrary_read_allowed=False,repeated_read_allowed=False,flash_allowed=False,retry_allowed=False" in seal,'no arbitrary or repeated operations')
check("OFFLINE_QUALIFY_RK03_FINAL_TWO_PASS_128_DO_NOT_EXECUTE" in seal,'next scope conditional offline qualification only')
check("for p in paths|set(q.iterdir())" in seal and "p.resolve().is_relative_to((REPO/'kernel128').resolve())" in seal,'read-only attribute changes confined to new release-owned trees')
check(interpretation['current_scope']=='FIXED_ONE128_BYTE_READ' and interpretation['response_bytes']==139 and interpretation['current_kernel_sha256']==contract['kernel_sha256'],'interpretation current scope correct')
check(any('retained old512 evidence' in s for s in interpretation['notes']) and any('No inherited actions array is executed' in s for s in interpretation['notes']),'inherited512 fields clearly limited to references')
native_review=read(A/'independent_review/REVIEW.json');check(native_review['status']=='PASS','frozen independent native review PASS');verify(native_review['reviewed_files'])
root_review=read(A/'root_review/REVIEW.json');check(root_review['status']=='PASS' and root_review['checks_passed']==1827,'1827 root review checks passed');verify(root_review)
check(any(p['path']==str(reviewer) and p['sha256']==pin(reviewer)['sha256'] for p in root_review['files']),'root review binds exact current script')
ktref=read(A/'kernel_review/LATEST_KERNEL_TESTS.json');verify(ktref);kt=read(ktref['report']['path']);check(kt['status']=='PASS' and kt['passed_cases']==kt['test_cases']==17,'kernel17 report current');verify(kt['inputs'])
manifest=read(A/'FIXED_UPLOAD_128_MANIFEST.json');verify(manifest['kernel']);kernel=Path(manifest['kernel']['path']).read_bytes();check(len(kernel)==manifest['kernel_bytes']==1808,'new upload length1808')
check(manifest['kernel']['sha256']==contract['kernel_sha256'],'upload manifest references current kernel')
owned=(ROOT/'src/owned_artifact.h').read_text();cipher=bytes(int(v,16) for v in re.findall(r'0x([0-9a-f]{2})',owned))
for n,chunk in enumerate(manifest['chunks']):
 start=n*128;raw=kernel[start:start+128];encoded=cipher[start:start+128]
 check(chunk['index']==n+1 and chunk['address']==f'{0xffff3000+start:08X}' and chunk['length']==len(raw),'chunk index address length')
 check(chunk['payload_sha256']==hashlib.sha256(raw).hexdigest() and chunk['cipher_sha256']==hashlib.sha256(encoded).hexdigest(),'chunk plaintext ciphertext hashes')
 check(chunk['request_hex']==contract['ordered_requests'][n+7]['wire_hex'] and chunk['reply_hex']=='80f0100176f7','chunk request exact ACK contract')
check(len(manifest['chunks'])==15,'new15-frame upload manifest')
builds=[read(ROOT/n/'BUILD.json') for n in ['build_a','build_b']]
for b in builds:check(pin(b['exe_path'])['sha256']==b['exe_sha256'],'current native build executable');verify(b['source_inputs'])
check(builds[0]['exe_sha256']==builds[1]['exe_sha256']=='1e98524252b28b634129bc3622b37e739b18d99ea5955209c9857a8f4ce02c45','same reviewed native pair')
check('Previous512 authorization is not reusable.' in doc.read_text() and 'PROCEED RK03 128 BYTE ROM READ' in doc.read_text(),'README requires fresh authorization')
check(not (REPO/'physical_session').exists(),'no physical session exists at review time')
gitdir=Path((REPO/'.git').read_text().strip().split(': ',1)[1]);head=(gitdir/'HEAD').read_text().strip();common=(gitdir/(gitdir/'commondir').read_text().strip()).resolve();commit=(common/head[5:]).read_text().strip()
paths=[sealer,reviewer,doc,interp,A/'root_review/REVIEW.json',A/'independent_review/REVIEW.json',A/'FIXED_UPLOAD_128_MANIFEST.json',A/'PHYSICAL_BOUNDED_128_REVIEW_CONTRACT.json',A/'kernel_review/LATEST_KERNEL_TESTS.json',Path(ktref['report']['path']),Path(__file__)]
result=dict(schema=1,status='PASS',scope='FINAL128_PACKAGING_ONLY_NO_HARDWARE_AUTHORIZATION',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=commit,reviewer='passive_review',checks_passed=len(checks),reviewed_files=[pin(p) for p in paths],summary=['Current certificate scope explicitly requires one128-byte request, the new kernel hash,17 new instruction cases and349 native test evidence.','New upload manifest was independently checked against kernel plaintext, embedded ciphertext, exact15 requests and ACKs.','Historical512 qualification/contract/action fields are explicitly identified as references and cannot substitute for new128 proof.','Three mandatory reviews include this final packaging report; certificate sealing initializes unconsumed BOUNDED_128_GATE_STATE with exact new token.','Mutable gate/current/checkpoint data remains outside immutable certificate files; only new owned paths are frozen.'],blocking_findings=[],physical_operations=0,provider_loads=0,native_or_model_test_runs=0,builds_run=0,limits=['This review does not execute the sealer or grant physical authorization.','Same identity text is retained; kernel808a5523 and native1e985242 image hashes distinguish the new variant.','A physical128 pass and successful OEM return are still required before the conditional final two-pass qualification.'])
with (A/'independent_review/PACKAGING_REVIEW.json').open('x',encoding='utf8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(status='PASS',checks=len(checks),commit=commit,report=pin(A/'independent_review/PACKAGING_REVIEW.json'))))
