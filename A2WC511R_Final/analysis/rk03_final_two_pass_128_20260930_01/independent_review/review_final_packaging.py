"""Bounded packaging-only review. Never imports or executes the release sealer."""
from pathlib import Path
import ast,datetime,hashlib,json
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_final_two_pass_128_20260930_01')
H=Path(r'C:\Dev\A2WC511R_RK03_FinalTwoPass128\final_two_pass_128')
OUT=A/'independent_review';checks=[];pins=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def pin(p):
 p=Path(p);b=p.read_bytes();v={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};pins.append(v);return v
def read(p):pin(p);return json.loads(Path(p).read_text(encoding='utf-8-sig'))
sp=H/'tools/seal_final_release.py';source=sp.read_text();pin(sp);tree=ast.parse(source)
plan=(A/'FINAL_RUN_PLAN.md').read_text();pin(A/'FINAL_RUN_PLAN.md')
root=read(A/'root_review/REVIEW.json');check(pins[-1]['sha256']=='3433057aea42f085196f5f090cb02b7e950ba504dadb5beec1598122db9628eb','pinned independent root audit')
check(root['status']=='PASS' and root['checks_passed']==16759 and root['physical_operations']==root['prior_qualification_reruns']==0,'root audit status/role/no physical rerun')
for ref in root['files']:
 check(pin(ref['path'])['sha256']==ref['sha256'],'current root-reviewed source '+Path(ref['path']).name)
native=read(A/'independent_review/REVIEW.json');check(native['status']=='PASS','prior independent native/control review retained')
check(any(isinstance(n,ast.If) and 'sys.flags.optimize' in ast.unparse(n.test) and any(isinstance(x,ast.Raise) for b in n.body for x in ast.walk(b)) for n in ast.walk(tree)),'unconditional rejection when Python assertions disabled')
main_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');check(isinstance(main_node.body[0],ast.If) and 'sys.flags.optimize' in ast.unparse(main_node.body[0].test),'optimization rejection is first sealing operation')
check("git('branch','--show-current')=='rk03/final-two-pass-128'" in source and "not git('status','--porcelain')" in source,'clean final branch required')
check("not (R/'physical_session').exists()" in source,'no final physical session before sealing')
check("A/'independent_review/REVIEW.json',A/'root_review/REVIEW.json',A/'independent_review/PACKAGING_REVIEW.json'" in source and "for path in reviews:assert read(path)['status']=='PASS';verify(read(path))" in source,'all three reviews mandatory and recursively hash-verified')
check("tests['passed_cases']==tests['test_cases']==38" in source and "tests['physical_operations']==tests['real_provider_loads']==0" in source,'new38-case fake qualification required')
check("('FINAL_VALIDATOR_TESTS.json',65),('LAUNCHER_TESTS.json',36),('OEM_RETURN_CONTROL_TESTS.json',14)" in source,'65/36/14 control results mandatory')
check("RK03_BOUNDED_ROM_READ_128_PHYSICAL']=='PASS'" in source and "OEM_RETURN_AFTER_BOUNDED_ROM_READ_128']=='PASS'" in source,'physical128 and recovery prerequisites mandatory')
check("c['maximum_requests']==16408" in source and "c['maximum_ROM_requests']==16384" in source and "c['fixed_reads']['block_bytes']==128" in source and "c['fixed_reads']['passes']==2" in source,'fixed128 two-pass scope')
check("c['kernel_sha256']=='808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653'" in source and "c['entry']=='FFFF3004'" in source,'exact unchanged kernel/entry')
check("builds[0]['source_inputs']==builds[1]['source_inputs']" in source and "Path(builds[0]['exe_path']).read_bytes()==Path(builds[1]['exe_path']).read_bytes()" in source,'matching source closure and byte-identical PE builds')
check("git('ls-files','final_two_pass_128')" in source and "commit=git('rev-parse','HEAD')" in source and "SOURCE_SNAPSHOT.zip" in source,'commit will bind tracked exact source snapshot')
check("FIXED_READ_MANIFEST.json','FIXED_READ_SCHEDULE.bin','FINAL_RUN_PLAN.md'" in source,'schedule manifest, exact wires and future run plan included')
check("for case in tests['cases']" in source and "['journal','images','stdout','stderr']" in source,'case evidence pins verified including preserved gzip/raw images')
check("physical_authorization_received=False" in source and "probe_invocation_count=0,launch_reserved=False" in source and "completed_pre_probe_gates=[],completed_recovery_gates=[],commit_authorization=None" in source,'fresh gates contain no receipts, authorization or invocation')
check("status='QUALIFIED_FUTURE_RUN_NOT_AUTHORIZED'" in source and "physical_execution_allowed_in_current_run=False" in source and "final_full_physical_allowed_this_run=False" in source,'preparation cannot claim current physical authorization')
check("arbitrary_read_allowed=False,third_pass_allowed=False,flash_allowed=False,retry_allowed=False" in source,'certificate exclusions explicit')
check("pass_to_pass_identity_required=True,baseline_equality_required_for_transport=False" in source and "bytes_per_output=1048576,total_output_bytes=2097152" in source,'byte equality and separate baseline classification accurately bound')
check("save(q/'QUALIFICATION.json',certificate);cert=pin(q/'QUALIFICATION.json')" in source and source.index("save(q/'QUALIFICATION.json',certificate)")<source.index("save(A/'FINAL_GATE_STATE.json',gates)"),'certificate hash generated before future mutable gate binding')
check("paths=set(source+[cp]+reviews" in source and "A/'FINAL_GATE_STATE.json'" not in source[source.index('paths=set'):source.index('certificate=dict')],'mutable gate excluded from certificate files')
check("if p.resolve().is_relative_to(H.resolve()) or p.resolve().is_relative_to(A.resolve()):p.chmod(0o444)" in source,'read-only attributes limited to new package/analysis, not historical/provider/reference inputs')
calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
check('subprocess.Popen' not in calls and 'subprocess.run' not in calls and not any(x in source for x in ['ctypes','WinDLL','CDLL','LoadLibraryExW']),'sealer contains no vehicle/provider/process launch; only read-only git metadata')
check('NOT authorized for execution in its preparation run' in plan and 'PROCEED RK03 FINAL TWO PASS ACQUISITION' in plan,'future plan forbids this preparation run and requires exact new token')
check('Do not erase/reset a consumed marker' in plan and 'never relaunch' in plan and 'Regardless of acquisition PASS/FAIL' in plan,'no retry, consumed markers preserved, recovery regardless of result')
check('PROJECT_COMPLETE only after tag success' in plan and 'CURRENT_PHYSICAL_CAPTURE, not factory stock' in plan,'completion and image designation correct')
contract=read(A/'FINAL_TWO_PASS_REVIEW_CONTRACT.json');check(contract['maximum_requests']==16408 and contract['maximum_ROM_requests']==16384 and contract['fixed_reads']['passes']==2 and contract['fixed_reads']['block_bytes']==128,'actual contract matches packaging claims')
for name,count in [('FINAL_VALIDATOR_TESTS.json',65),('LAUNCHER_TESTS.json',36),('OEM_RETURN_CONTROL_TESTS.json',14)]:
 r=read(A/name);check(r['status']=='PASS' and r.get('passed_cases',r.get('checks_passed'))==count,'retained new result '+name)
for name in ['build_a','build_b']:
 b=read(H/name/'BUILD.json');check(b['status']=='PASS_BUILD_ONLY' and b['exe_sha256']=='991492809897e3333fdc1422e70d70690906f59d722e1e99088fb55bd56432ce','final build manifest '+name)
 check(pin(b['exe_path'])['sha256']==b['exe_sha256'],'current PE '+name)
pin(A/'FIXED_READ_MANIFEST.json');pin(A/'FIXED_READ_SCHEDULE.bin');pin(Path(__file__))
report={'schema':1,'status':'PASS','scope':'FINAL_TWO_PASS128_PACKAGING_ONLY_STATIC_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'passive_review','checks_passed':len(checks),'checks':checks,'blocking_findings':[],
 'reviewed_files':pins,'conclusions':['The sealer binds the new fixed128 two-pass scope, samePE matching builds,38-case fake report,65/36/14 control checks and all three independent reviews.','Prior physical128 success and OEM return are exact pinned prerequisites. The unchanged128 kernel and all16384 request wires are bound through reviewed source/manifest/evidence.','Source snapshot and clean commit are sealed without touching prior evidence. Certificate creation precedes separate mutable gate/state files; no authorization, receipt or invocation is invented.','The run plan requires a separately authorized future run, exact fresh token, single child ownership, cleanup/recovery, independently reconstructed raw images and offline integrity/tag completion.'],
 'resolved_findings':[{'issue':'Python assert-based sealing checks can be disabled by optimization.','resolution':'An unconditional sys.flags.optimize rejection is now required and verified before sealing work.'}],
 'limitations':['No sealer, test suite, native executable, provider, client scanner or hardware was invoked by this packaging review.','The generated certificate hash is intentionally absent from this review to avoid self-reference. Final source commit is read and bound by the sealer after commit.','Root independent audit is reused by its sealed hash; no prior full qualification audit is repeated.','Physical two-pass acquisition remains unexecuted and requires a separate future request and human gates.'],
 'physical_operations':0,'provider_loads':0,'native_executions':0,'qualification_reruns':0}
with (OUT/'PACKAGING_REVIEW.json').open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks),'report':pin(OUT/'PACKAGING_REVIEW.json')}))
