"""Read existing sealed bytes and write a separate packaging review; no process launch."""
from pathlib import Path
import datetime,hashlib,json,zipfile
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_read_physical_20260930_01')
REPO=Path(r'C:\Dev\A2WC511R_RK03_BoundedReadPhysical');ROOT=REPO/'bounded_read_physical'
CERT=A/'qualification/QUALIFICATION.json';GATES=A/'BOUNDED_GATE_STATE.json';OUT=A/'independent_review/PACKAGING_REVIEW.json'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
certpin=pin(CERT);q=read(CERT)
check(certpin['sha256']=='15ba34b4d14c17e104fe28163faf7afe6b3c11b067ecf15a3bc97f8af8b253d1','exact certificate pin')
check(q['status']=='PASS_OFFLINE_QUALIFIED_PHYSICAL_BOUNDED_ROM_READ_ONLY','qualified scope')
check(q['commit']=='96f6c49030b2d1c694e388ba6a1925d62d83b56a' and q['branch']=='rk03/bounded-rom-read-physical','expected source commit and branch')
gitdir=Path((REPO/'.git').read_text().strip().split(': ',1)[1]);head=(gitdir/'HEAD').read_text().strip();common=(gitdir/(gitdir/'commondir').read_text().strip()).resolve()
check(head=='ref: refs/heads/'+q['branch'],'actual worktree HEAD branch')
check((common/head[5:]).read_text().strip()==q['commit'],'actual branch ref commit without git invocation')
check(len({r['path'] for r in q['files']})==len(q['files']),'unique certificate file paths')
for ref in q['files']:
 check(pin(ref['path'])==ref,'certificate file '+ref['path'])
for field in ['physical_executable','second_clean_executable','review_contract','source_snapshot','test_report','retained_offline_122_qualification']:
 check(pin(q[field]['path'])==q[field],'top-level artifact '+field)
check(q['physical_executable']['sha256']==q['second_clean_executable']['sha256']=='5a66a0848601c8564a6896ddabbc35af453179c68c79ec871bee6d73e120bfb9','both qualified clean builds')
builds=[read(ROOT/n/'BUILD.json') for n in ['build_a','build_b']]
for b in builds:
 check(b['status']=='PASS_BUILD_ONLY' and pin(b['exe_path'])['sha256']==b['exe_sha256'],'build status and executable')
 for ref in b['source_inputs']+[b[k] for k in ['compiler','linker','build_log','imports','headers']]:
  check(pin(ref['path'])['sha256']==ref['sha256'],'build pin '+ref['path'])
check(builds[0]['source_inputs']==builds[1]['source_inputs'],'same compiled source closure')
check((ROOT/'build_a/REPRODUCIBLE_MANIFEST.json').read_bytes()==(ROOT/'build_b/REPRODUCIBLE_MANIFEST.json').read_bytes(),'identical canonical build manifests')
known={str(Path(r['path']).resolve()):r for r in q['files']}
with zipfile.ZipFile(q['source_snapshot']['path']) as z:
 names=z.namelist();check(len(names)==len(set(names)),'unique snapshot members')
 for name in names:
  target=(REPO/name).resolve();check(target.is_relative_to(ROOT.resolve()),'snapshot bounded to new source')
  check(str(target) in known,'snapshot source included in certificate')
  check(z.read(name)==target.read_bytes(),'snapshot byte equality '+name)
 snapshot_count=len(names)
gates=read(GATES);gatepin=pin(GATES)
check(gates['session_id']==q['session_id']=='RK03_BOUNDED_ROM_READ_01' and gates['qualification_sha256']==certpin['sha256'],'gate session and certificate binding')
check(q['physical_authorization_received'] is False and q['maximum_physical_invocations']==1 and q['requires_exact_human_authorization']=='PROCEED RK03 BOUNDED ROM READ','certificate grants no physical authorization')
check(gates['probe_invocation_count']==0 and not gates['launch_reserved'] and not gates['physical_authorization_received'] and gates['commit_authorization'] is None,'unconsumed unauthorized gate state observed')
check(q['maximum_requests']==25 and q['maximum_ROM_requests']==1 and q['bounded_read']['address']==0 and q['bounded_read']['length']==512,'one fixed512 operation only')
check(not any(q[k] for k in ['arbitrary_read_allowed','repeated_read_allowed','flash_allowed','retry_allowed']),'forbidden scopes remain disabled')
check(q['tests_passed']==q['tests_total']==1116 and q['physical_operations_during_qualification']==q['provider_loads_during_qualification']==0,'qualification reused without execution')
mutable=[GATES,A/'CHECKPOINT.json',Path(r'C:\Dev\A2WC511R_Final\state\CURRENT.json')]
check(all(str(p.resolve()) not in known for p in mutable),'mutable state excluded from immutable certificate')
check(not (REPO/'physical_session').exists(),'no physical session or authorization artifacts at review time')
check(pin(CERT)==certpin,'certificate unchanged during read-only audit')
check(str(OUT.resolve()) not in known,'new packaging review outside existing certificate')
report=dict(schema=1,status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),certificate=certpin,source_commit=q['commit'],physical_executable=q['physical_executable'],verified_certificate_files=len(q['files']),verified_snapshot_members=snapshot_count,checks_passed=len(checks),summary=['All certificate files and top-level artifact pins match.','All compiled sources, toolchain and build evidence match both clean-build reports.','Canonical build manifests are identical; snapshot source bytes match current certified files.','New-session gates bind the exact certificate and remain unconsumed and unauthorized at observation.','Immutable certificate excludes mutable gates/checkpoint/current state.'],gate_observation=dict(path=str(GATES),sha256_at_observation=gatepin['sha256'],state=gates,note='Point-in-time mutable state; later actual human receipts may change this file.'),review_source=pin(Path(__file__)),physical_operations=0,provider_loads=0,native_executions=0,old_tests_rerun=0,blocking_findings=[],limits=['Read-only packaging audit; this report neither authorizes nor performs hardware activity.','Only the first512 bytes are compared; they equal current and stock and cannot attest a whole ROM.'])
with OUT.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(dict(status='PASS',report=pin(OUT),certificate_files=len(q['files']),snapshot_members=snapshot_count,checks=len(checks))))
