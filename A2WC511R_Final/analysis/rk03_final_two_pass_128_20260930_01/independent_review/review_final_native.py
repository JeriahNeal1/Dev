"""Read-only root-authored native/control review; does not execute those modules."""
from pathlib import Path
import datetime,hashlib,json
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_final_two_pass_128_20260930_01')
R=Path(r'C:\Dev\A2WC511R_RK03_FinalTwoPass128\final_two_pass_128')
OLD=Path(r'C:\Dev\A2WC511R_RK03_Bounded128Physical\bounded_128_physical')
OUT=A/'independent_review';pins={};checks=[]
def pin(p):
 p=Path(p);b=p.read_bytes();v={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};pins[str(p)]=v;return v
def read(p):pin(p);return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def text(p):pin(p);return Path(p).read_text()
def check(ok,name):
 if not ok:raise AssertionError(name)
 checks.append(name)
def verify(v):
 p=pin(v['path']);check(p['sha256']==v['sha256'],'pinned '+v['path'])
 if 'bytes' in v:check(p['bytes']==v['bytes'],'size '+v['path'])
def section(s,a,b):return s[s.index(a):s.index(b,s.index(a))].rstrip()

c=read(A/'FINAL_TWO_PASS_REVIEW_CONTRACT.json');check(c['maximum_requests']==16408 and c['maximum_ROM_requests']==16384 and len(c['ordered_prefix_requests'])==24,'24 prerequisite plus16384 read bound')
check(c['kernel_sha256']=='808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653' and c['entry']=='FFFF3004','unchanged physically proven128 kernel and entry')
for k in ['kernel_image','kernel_manifest','current_reference','physical_provider','retained_bounded_qualification','physical128_result','physical128_review','OEM_return_after128','physical128_journal','fixed_upload_manifest']:verify(c[k])
check(read(c['physical128_result']['path'])['RK03_BOUNDED_ROM_READ_128_PHYSICAL']=='PASS','bounded physical prerequisite PASS')
check(read(c['OEM_return_after128']['path'])['OEM_RETURN_AFTER_BOUNDED_ROM_READ_128']=='PASS','OEM return prerequisite PASS')
fixed=text(R/'src/fixed_reads.hpp');core=text(R/'src/probe_core.hpp');oldcore=text(OLD/'src/probe_core.hpp');raw=text(R/'src/raw_images.hpp');main=text(R/'src/main.cpp');boot=text(R/'src/bootstrap.hpp');pinned=text(R/'src/pins.hpp')
for name in ['common.hpp','protocol.hpp','identity_response.hpp','owned_artifact.h','fixtures.hpp','bounded_response.hpp','bootstrap.hpp','bootstrap_tests.hpp','j2534_tactrix.h','real_clock.hpp']:
 check((R/'src'/name).read_bytes()==(OLD/'src'/name).read_bytes(),'byte-identical retained '+name);pin(R/'src'/name);pin(OLD/'src'/name)
for a,b in [(' void setup()', ' Bytes exchange('),(' template<class F> long cleanup_call',' int run()'),('try{setup();','identity_validated=true;')]:
 check(section(core,a,b)==section(oldcore,a,b),'unchanged normalized source section '+a)
check(section(core,'if(stage==22)',' std::string state()')==section(oldcore,'if(stage==22)',' std::string state()'),'all prefix request construction retained')
check('COUNT=16384,PREFIX=24,MAX_TX=16408' in fixed and 'BLOCK=128,PER_PASS=8192,PASSES=2' in fixed,'compile-time complete coverage')
schedule=bytearray()
for index in range(16384):
 b=bytes.fromhex('beef000803')+bytes([index//8192])+((index%8192)*128).to_bytes(4,'big')+bytes.fromhex('0080');schedule.extend(b+bytes([sum(b)%256]))
manifest=read(A/'FIXED_READ_MANIFEST.json');verify(manifest['fixed_schedule']);check(Path(manifest['fixed_schedule']['path']).read_bytes()==schedule,'all16384 manifest wires independently derived gap-free')
check('require(index<COUNT' in fixed and 'index/PER_PASS' in fixed and '(index%PER_PASS)*BLOCK' in fixed and 'm.DataSize<=139' in fixed and 'bytes.size()+data.size()<=139' in fixed and '++pieces<=143' in fixed,'fixed read bounds and strict139-byte parser')
check('Fixed framing length command pass address' in fixed and 'Fixed response checksum' in fixed and '++indicators<=4' in fixed and 'data==tx' in fixed,'strict header/checksum/indication/echo acceptance')
check('stage==next_tx&&next_tx<FixedReads::MAX_TX' in core and 'Bytes(tx.value.Data,tx.value.Data+tx.value.DataSize)==request(stage)' in core,'transmit guard and no arbitrary request input')
check('for(unsigned index=0;index<FixedReads::COUNT;index++)' in core and 'exchange(FixedReads::PREFIX+index)' in core,'only two ordered passes')
check('GetTickCount64()<deadline' in core and 'Whole frame deadline after API return' in core and 'status==0' in core,'unchanged fatal API status and whole2s deadline')
check(core.index('images.accept(index,reply)')<core.index('event(images.finish());acquisition_validated=true;protocol_complete=true'),'image validation precedes protocol success')
check('require(index==accepted&&index<FixedReads::COUNT' in raw and 'require(counts[p]==a' in raw,'no output gap duplicate or overlap')
check(raw.index('require(matches_pass0(index,frame)')<raw.index('WriteFile(files[p].value'),'immediate pass1 comparison before writing mismatching block')
check('CREATE_NEW' in raw and 'counts[0]==1048576&&counts[1]==1048576' in raw and 'FlushFileBuffers(files[0].value)&&FlushFileBuffers(files[1].value)' in raw,'exclusive exact-size flushed outputs')
check('a==pass0&&a==b' in raw and 'ah==bh' in raw and 'sha256(baseline.value)==REFERENCE_SHA' in raw,'complete byte and SHA comparisons against captured pass0 and pinned independent baseline')
check(r'baseline_equality_required_for_transport\":false' in raw and 'differing_ranges' in raw,'baseline differences classified separately')
check(main.index('return probe.run();')<main.index('const Bindings b=physical_bindings()')<main.index('outputs.prepare(b.session,false,0)')<main.index('LoadLibraryExW('),'offline branch precedes gated physical boundary; outputs prepared before provider')
check('argc==6' in main and '--physical-final-two-pass-128' in main and 'gate.prepare(b,argv[3],argv[5])' in main,'fixed physical CLI and gate')
check(c['requires_exact_human_authorization'] in pinned and c['session_id'] in pinned and pin(A/'FINAL_TWO_PASS_REVIEW_CONTRACT.json')['sha256'] in pinned,'native session/token/contract pins')
check('CREATE_NEW' in boot and 'NATIVE_ONCE' in boot and 'Authorization exact content mismatch' in boot and 'Root launch reservation mismatch' in boot and 'Fixed provider SHA256 mismatch' in boot,'one-shot native authorization and provider binding retained')
for name in ['build_a','build_b']:
 b=read(R/name/'BUILD.json');check(b['status']=='PASS_BUILD_ONLY','clean '+name);check(pin(b['exe_path'])['sha256']==b['exe_sha256'],'native '+name)
 for p in b['source_inputs']:verify(p)
 for k in ['compiler','linker','build_log','imports','headers']:verify(b[k])
check(read(R/'build_a/BUILD.json')['exe_sha256']==read(R/'build_b/BUILD.json')['exe_sha256']=='991492809897e3333fdc1422e70d70690906f59d722e1e99088fb55bd56432ce','matching samePE clean builds')
latest=read(R/'reports/LATEST_QUALIFICATION.json');verify(latest['report']);test=read(latest['report']['path']);check(test['status']=='PASS' and test['passed_cases']==test['test_cases']==38 and test['physical_operations']==test['real_provider_loads']==0,'new focused suite evidence')
for p in test['source_and_build_pins']:verify(p)
check(test['positive_cases']==4 and test['negative_cases']==34,'four positives34negatives honestly counted')
control_names=['launch_final_once.py','launch_oem_return_once.py','seal_oem_return_final.py','check_clients.ps1','validate_final.py','seal_final_result.py','complete_project.py','test_launcher_offline.py','test_oem_return_controls.py']
sources={name:text(A/name) for name in control_names}
for name in control_names:check((A/name).read_bytes()==(R/'release_controls'/name).read_bytes(),'tracked active control matches '+name);pin(R/'release_controls'/name)
launch=sources['launch_final_once.py'];recovery=sources['launch_oem_return_once.py'];validation=sources['validate_final.py'];seal=sources['seal_final_result.py'];complete=sources['complete_project.py'];clients=sources['check_clients.ps1']
check('rk03_bounded_rom_read_128_physical32' in clients and 'rk03_final_two_pass_128_physical32' in clients,'previous128 and newfinal client names both retained')
check("TOKEN = 'PROCEED RK03 FINAL TWO PASS ACQUISITION'" in launch and "['IGNITION OFF', 'TEST MODE ON']" in launch and "gates['full_acquisition_allowed'] is True" in launch and "gates['retry_allowed'] is False" in launch,'fresh human final-scope gates')
check("'PASS_OFFLINE_QUALIFIED_PHYSICAL_FINAL_TWO_PASS_128'" in launch and "cert['files']" in launch and ".open('x'" in launch and 'wait_for_child' in launch,'complete certificate closure plus once reservation and child ownership')
check("['IGNITION OFF','NORMAL MODE ON']" in recovery and 'times[0]<=times[1]<=times[2]' in recovery and "'--count','120'" in recovery and "'--authorize-physical-read-only'" in recovery,'fresh recovery before unchanged passive120')
check('txcount<16408' in validation and 'expected=frame(txcount-24)' in validation and 'Exact control schedule' in validation and 'Immediate second-pass identity' in validation,'independent streaming exact schedule and pass equality')
check('Full byte equality' in validation and 'Independent final comparison' in validation and 'Terminal cleanup' in validation,'independent complete image/status reconstruction')
check('Every saved byte equals independently reconstructed physical responses' in seal and "retry_allowed=False" in seal and "next_required_state='IGNITION OFF'" in seal,'physical result binds actual files and transitions to recovery only')
check("'Both physical and recovery PASS'" in complete and "'Final raw byte audit'" in complete and "'Release source commit'" in complete and "'Clean source worktree'" in complete,'completion requires bothPASS fresh byte audit and source integrity')
check('CURRENT_PHYSICAL_CAPTURE' in complete and 'factory_stock_claim=False' in complete and 'additional_physical_operation_allowed=False' in complete and "'git','tag','-a'" in complete,'honest capture designation and local completion tag only')
check(complete.index("write_new(out/'INTEGRITY_AUDIT.json'")<complete.index("subprocess.run(['git','tag','-a'")<complete.index("write_new(out/'PROJECT_COMPLETE.json'"),'project completion emitted only after successful local tag')
for name,count,key in [('LAUNCHER_TESTS.json',36,'launcher'),('OEM_RETURN_CONTROL_TESTS.json',14,'wrapper')]:
 t=read(A/name);check(t['status']=='PASS' and t['checks_passed']==count and t['physical_operations']==t['provider_loads']==0,'new mocked control evidence '+name);verify(t[key]);verify(t['test_source'])
vt=read(A/'FINAL_VALIDATOR_TESTS.json');check(vt['status']=='PASS' and vt['passed_cases']==vt['test_cases']==65 and vt['physical_operations']==vt['real_provider_loads']==vt['native_test_reruns']==0,'independent validator65 checks reuse existing journals')
for p in vt['files']:verify(p)
vts=text(A/'test_final_validator.py');check("'--offline-fixture','success'" in vts and "'--physical" not in vts and '38_RETAINED_NATIVE_CASES' in vts,'validator source uses retained evidence and only offline CLI negatives')
check(not (R.parent/'physical_session').exists(),'no final physical session/authorization created')
pin(Path(__file__))
report={'schema':1,'status':'PASS','scope':'INDEPENDENT_REVIEW_ROOT_AUTHORED_FINAL_NATIVE_AND_RELEASE_CONTROLS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'passive_review','checks_passed':len(checks),'checks':checks,'blocking_findings':[],
 'author_roles':{'native_schedule_parser_image_sink_main_build_and_controls':'root; independently reviewed here','fake_backend_physical_replay_headers_and38case_runner':'passive_review; root independent review required separately','unchanged128kernel':'prior passive_review implementation independently reviewed by root and physically validated; not rebuilt here'},
 'physical_executable':test['physical_executable'],'qualification_test_report':latest['report'],'test_counts':{'positive':4,'negative':34,'total':38,'author_execution_checks':test['checks_passed']},
 'resolved_findings':[{'issue':'Client-name detector initially replaced rather than retained preceding128 PE name.','resolution':'Root now retains both previous128 and newfinal names; tracked copy matches.'}],
 'conclusions':['The only acquisition suffix is two complete sequential128-byte passes over address0..0xFFFFF. All16384 request bytes/checksums match independently derived manifest; maximum totalTX16408.','The unchanged physical128 kernel, entry, first24 admission frames, initializer, deadlines and cleanup mechanisms are reused with exact source/evidence pins.','The new image sink rejects a pass1 mismatch before writing that block, persists exact1MiB files, then checks every saved byte and SHA256. Reference-baseline differences remain a separate result.','New launcher gates/certificate/token/session and once reservations precede the provider. Result validation reconstructs images from complete wire evidence, requires cleanup, and OEM recovery precedes any offline project completion.'],
 'limitations':['No final physical acquisition is executed or authorized by this review. Full-session timing and silicon behavior remain unproven until the separately gated run.','38 representative new-PE cases are not a Cartesian fault matrix; prior349 tests were reused rather than rerun.','Only first24 fake transactions retain historical physical RX/version metadata; all full-image suffix replies are synthetic.','completed_reads appears in compact fake suffix state only; physical progress remains observable through ordered rom_block and full_read_result records.','The physical-capable PE intentionally contains provider loader/imports behind its gate; fake qualification never selects that path.','Root independent audit of reviewer-authored fixtures/runner remains separately required, along with final packaging review.','Cosmetic inherited probe wording in control docstrings does not change dispatch or scope; exact new status/token/path checks are active.'],
 'reviewed_files':list(pins.values()),'physical_operations_by_reviewer':0,'provider_loads_by_reviewer':0,'new_native_fixture_executions_by_reviewer':38,'prior_suite_reruns':0}
with (OUT/'REVIEW.json').open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks),'report':pin(OUT/'REVIEW.json')}))
