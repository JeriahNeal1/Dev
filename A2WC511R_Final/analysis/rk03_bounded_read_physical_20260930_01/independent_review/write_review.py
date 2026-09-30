"""Read-only evidence audit and new review output; no executable/provider invocation."""
from pathlib import Path
import datetime,hashlib,json,difflib
ROOT=Path(r'C:\Dev\A2WC511R_RK03_BoundedReadPhysical\bounded_read_physical')
OLD=Path(r'C:\Dev\A2WC511R_RK03_KernelIdentityPhysical\kernel_identity_physical')
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_read_physical_20260930_01')
OUT=A/'independent_review'
checks=[];verified={}
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def verify(p):
 actual=pin(p['path']);check(actual['sha256']==p['sha256'],'hash '+p['path']);verified[actual['path']]=actual
def walk(obj):
 if isinstance(obj,dict):
  if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str):verify(obj)
  for v in obj.values():walk(v)
 elif isinstance(obj,list):
  for v in obj:walk(v)
def section(t,start,end):return t[t.index(start):t.index(end,t.index(start))]
def write_new(p,obj):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')

contract=read(A/'PHYSICAL_BOUNDED_REVIEW_CONTRACT.json')
check(pin(A/'PHYSICAL_BOUNDED_REVIEW_CONTRACT.json')['sha256']=='be14e560229f5a7eb1904cc18c47dc9c36fe6df3b79c86be12f844640fe15e02','fixed contract pin')
check(contract['maximum_tx']==contract['maximum_requests']==len(contract['ordered_requests'])==25,'25 fixed requests only')
check(contract['bounded_read']['request']=='beef00080300000000000200ba' and contract['bounded_read']['address']==0 and contract['bounded_read']['length']==512,'fixed pass0 address0 length512')
reply=bytes.fromhex(contract['bounded_read']['response'])
check(len(reply)==523 and reply[:10]==bytes.fromhex('beef0206830000000000') and reply[-1]==sum(reply[:-1])%256,'exact523 framing and checksum')
check(hashlib.sha256(reply).hexdigest()=='796f64cefcd2b81c5c7662b2bdacad828c0a948c55bfdc5d002ac5c8da7f898e','fixed response hash')
check(hashlib.sha256(reply[10:-1]).hexdigest()=='d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01','fixed data hash')
walk(contract['offline_bounded_contract']);walk(contract['offline_bounded_qualification']);walk(contract['bounded_read']['current_rom']);walk(contract['physical_provider'])
builds=[read(ROOT/n/'BUILD.json') for n in ('build_a','build_b')]
for b in builds:
 check(b['status']=='PASS_BUILD_ONLY','clean build completed')
 walk(b)
 check(pin(b['exe_path'])['sha256']==b['exe_sha256'],'executable matches build record')
check(builds[0]['source_inputs']==builds[1]['source_inputs'],'identical complete compiled input lists')
check(builds[0]['exe_sha256']==builds[1]['exe_sha256']=='5a66a0848601c8564a6896ddabbc35af453179c68c79ec871bee6d73e120bfb9','identical clean native builds')
for name in ['common.hpp','protocol.hpp','identity_response.hpp','bootstrap.hpp','bootstrap_tests.hpp','owned_artifact.h','real_clock.hpp','j2534_tactrix.h','fixtures.hpp','physical_replay.hpp','first_physical_replay.hpp','full_physical_replay.hpp']:
 check((ROOT/'src'/name).read_bytes()==(OLD/'src'/name).read_bytes(),'retained component byte-identical '+name)
core=(ROOT/'src/probe_core.hpp').read_text();old=(OLD/'src/probe_core.hpp').read_text();parser=(ROOT/'src/bounded_response.hpp').read_text();main=(ROOT/'src/main.cpp').read_text();gate=(ROOT/'src/bootstrap.hpp').read_text()
for start,end in [(' void setup()', ' Bytes exchange('),(' void identity_transport()', ' int run()'),(' template<class F> long cleanup_call',' void identity_transport()')]:
 check(section(core,start,end)==section(old,start,end),'retained normalized section '+start.strip())
check(section(core,'try{setup();','identity_validated=true;')==section(old,'try{setup();','identity_validated=true;'),'full protocol prefix unchanged through identity')
check(core.count('exchange(24)')==1 and 'stage<25' in core and 'next_tx<25' in core,'single final fixed read and maximum25 dispatch')
check('if(stage==24){require(identity_validated&&kernel_filter&&filtered&&requested_baud==62500' in core,'read guard requires accepted identity and transport')
check('++pieces<=527' in parser and 'm.DataSize<=523' in parser and 'bytes.size()+data.size()<=523' in parser and '++indicators<=4' in parser,'bounded parser sizes records and indications')
check('require(bytes.empty()' in parser and 'require(data==tx' in parser and 'Unknown bounded RX status' in parser,'only leading empty indicators or exact echoes')
check('beef0206830000000000' in parser and 'Bounded response checksum' in parser,'fixed header includes length command pass address and checksum validation')
check('for(unsigned i=0;i<512;i++)' in core and core.index('require(reply==expected')<core.index('bounded_validated=true;protocol_complete=true'),'all mismatch evidence precedes validated state')
check('GetTickCount64()+2000' in core and 'Whole frame deadline after API return' in core,'two-second whole-frame deadline retained before and after API return')
check(main.index('return probe.run();')<main.index('const Bindings b=physical_bindings()')<main.index('LoadLibraryExW('),'offline selection returns before physical gates and loader')
check(main.count('LoadLibraryExW(')==1 and main.index('gate.lock_provider(b)')<main.index('LoadLibraryExW('),'single fixed provider loader after hash lock')
check('CREATE_NEW' in gate and 'b.token+"\\nSESSION_ID="' in gate and 'Root launch reservation mismatch' in gate,'native exact authorization reservation and one-shot marker')
check('argc==6' in main and '--physical-bounded-rom-read' in main and 'Probe probe(api,journal.value,true,true)' in main,'physical entry fixed scope with mandatory real clock')

latest=read(ROOT/'reports/LATEST_QUALIFICATION.json');walk(latest);tests=read(latest['report']['path'])
check(tests['status']=='PASS' and tests['test_cases']==tests['passed_cases']==1116,'1116 focused tests passed once')
check(tests['physical_operations']==tests['real_provider_loads']==0 and tests['prior386_reused_not_rerun'],'offline new suite with old386 evidence reused')
walk(tests['inputs'])
positive=negative=total_tx=0
for case in tests['cases']:
 check(case['status']=='PASS','case accepted '+case['case']+' '+case['mode'])
 for k in ['journal','stdout','stderr']:verify(case[k])
 check(case['command'][1] in ['--offline-fixture','--offline-real-clock-fixture'] and case['command'][2]==case['case'],'explicit fake CLI '+case['case'])
 check(case['tx_attempts']<=25,'TX bound '+case['case'])
 positive+=case['exit_code']==0;negative+=case['exit_code']==1;total_tx+=case['tx_attempts']
check(tests['all522_splits_passed'] and tests['all512_data_positions_rejected'] and tests['all512_simultaneous_mismatches_preserved'],'complete bounded matrix assertions')
check([c['case'] for c in tests['cases'] if c['mode']=='real_clock']==['success','physical_identity_replay','bounded_indicators_fragmented'],'three real-clock cases')
root_review=read(A/'root_review/REVIEW.json');check(root_review['status']=='PASS' and root_review['checks_passed']==5582,'independent root review of authored fixtures and runner');walk(root_review)

controls=['launch_bounded_once.py','launch_oem_return_once.py','check_clients.ps1','seal_bounded_result.py','seal_oem_return_bounded.py','test_launcher_offline.py','test_oem_return_controls.py','test_result_validator.py']
for n in controls:check((ROOT/'release_controls'/n).read_bytes()==(A/n).read_bytes(),'tracked control matches release '+n)
launcher=(A/'launch_bounded_once.py').read_text();recovery=(A/'launch_oem_return_once.py').read_text();clients=(A/'check_clients.ps1').read_text();validator=(A/'seal_bounded_result.py').read_text();oem=(A/'seal_oem_return_bounded.py').read_text();sealer=(ROOT/'tools/seal_bounded_release.py').read_text()
check("TOKEN = 'PROCEED RK03 BOUNDED ROM READ'" in launcher and "['IGNITION OFF', 'TEST MODE ON']" in launcher,'new human states and exact scope token required')
check("row['source'] == 'user'" in launcher and "auth['qualification_sha256'] == cert_sha" in launcher and 'times[0] <= times[1] <= stamp' in launcher,'human provenance chronological certificate-bound gates')
check(".open('x'" in launcher and 'SINGLE_LAUNCH_RESERVED_NO_RETRY' in launcher and launcher.count('subprocess.Popen(')==1,'exclusive one-shot launch and no retry')
check('wait_for_child' in launcher and 'except KeyboardInterrupt' in launcher and 'finally:' in launcher,'retain child ownership despite bookkeeping or console error')
check('rk03_kernel_start_identity_physical32|rk03_bounded_rom_read_physical32' in clients,'fixed review finding retain both diagnostic clients')
check("module_inspection_failures=$inspectionFailures" in clients and '$inspectionFailures.Count -eq 0' in clients,'client inspection fails closed on inspection errors')
check("['IGNITION OFF','NORMAL MODE ON']" in recovery and 'times[0]<=times[1]<=times[2]' in recovery,'recovery only after confirmed process exit and fresh states')
check("'--count','120'" in recovery and "'--interval-ms','250'" in recovery and 'validate_reuse(reuse_sha)' in recovery,'fixed qualified passive BF/A8 return only')
check("len(tx)==25" in validator and "terminal['state']['bounded_validated']" in validator and 'bounded_ROM_read=True if validation else "UNCONFIRMED"' in validator,'fixed review findings exact TX state and honest failed-read status')
check("len(bounded_events)==1" in validator and "'Result must precede immediate cleanup'" in validator and "'Exact current.bin bounded data'" in validator,'independent full-frame data and event boundary validation')
check("'OFFLINE ONLY: exact first-divergence analysis; no retry or further physical attempt.'" in oem,'failed bounded result cannot advance into further physical work')
check('First512 bytes equal current.bin and stock; no whole-ROM provenance claim.' in sealer,'512-byte comparison is not full-ROM attestation')
check("physical_authorization_received=False" in sealer and "status='WAITING_IGNITION_OFF'" in sealer and "probe_invocation_count=0" in sealer,'qualification does not preauthorize physical session')
check('if p.resolve().is_relative_to(ROOT.resolve()) or p.resolve().is_relative_to(OUT.resolve()):p.chmod(0o444)' in sealer,'only new release-owned paths made read-only')
check("reviews=[OUT/'independent_review/REVIEW.json',OUT/'root_review/REVIEW.json']" in sealer and 'verify(r)' in sealer,'both author-separated reviews mandatory and pins rechecked')
check("assert not (REPO/'physical_session').exists()" in sealer and "for p in sorted(paths)" in sealer,'sealing before physical activity with explicit file closure')
for n,count in [('LAUNCHER_TESTS_V2.json',36),('OEM_RETURN_CONTROL_TESTS_V2.json',14),('RESULT_VALIDATOR_TESTS.json',54)]:
 r=read(A/n);check(r['status']=='PASS' and r['checks_passed']==count,'control checks '+n);walk(r)
check(not (ROOT.parent/'physical_session').exists(),'no physical session created')
source_paths=[ROOT/'src'/n for n in ['bounded_response.hpp','probe_core.hpp','main.cpp','pins.hpp','bootstrap.hpp','identity_response.hpp','fake_backend.hpp','identity_physical_replay.hpp']]
source_paths += [ROOT/'tools'/n for n in ['build_probe.py','build_probe.cmd','derive_bounded_release.py','seal_bounded_release.py','root_review.py','test_bounded_physical.py']]
source_paths += [A/n for n in controls+['PHYSICAL_BOUNDED_REVIEW_CONTRACT.json','LAUNCHER_TESTS_V2.json','OEM_RETURN_CONTROL_TESTS_V2.json','RESULT_VALIDATOR_TESTS.json']]
source_paths += [ROOT/n/'BUILD.json' for n in ['build_a','build_b']]+[Path(builds[0]['exe_path']),Path(builds[1]['exe_path']),Path(latest['report']['path']),A/'root_review/REVIEW.json',Path(__file__)]
report=dict(schema=1,status='PASS',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='passive_review',roles={'native_parser_core_build_controls_author':'root','native_and_release_controls_independent_reviewer':'passive_review','fake_replay_and_test_runner_author':'passive_review','fake_and_runner_independent_reviewer':'root; root_review/REVIEW.json'},checks_passed=len(checks),checks=checks,physical_operations=0,real_provider_loads=0,qualification_summary=dict(total=1116,positive=positive,negative=negative,total_tx=total_tx,all522_splits=True,all512_individual_data_faults=True,all512_simultaneous_mismatches=True,real_clock_cases=3,prior386_reused_without_execution=True,old122_not_rerun=True,initial_execution_passed=True),resolved_findings=['Client-name check now retains previous identity executable alongside bounded executable.','Result validator now requires bounded_validated and reports UNCONFIRMED ROM-read status on failed validation.'],blocking_findings=[],reviewed_files=[pin(p) for p in source_paths],verified_evidence_pins=list(verified.values()),limitations=['Same physical-capable PE was exercised only through static fake modes; no physical authorization or provider operation was performed.','This reviewer authored fixtures/runner; parent independently reviewed those artifacts and all journals. Native/control review is independent of their author.','Retained bootstrap and protocol-prefix components are byte-identical and prior386 evidence is reused; the old suite was not rerun.','Physical replay retains exact24 writes and48 receive records/version buffers; fake resource identifiers and host timing are synthetic.','Baud SET_CONFIG acceptance is checked; no effective baud GET is claimed.','The 512-byte block equals both current and stock; successful comparison cannot attest the entire ROM or calibration.','Once the complete response is accepted, receiving stops. Separately queued trailing frames are not consumed; same-message trailing bytes are rejected.','Two-second whole-frame budget and actual minimum waits are tested offline; vehicle/provider timing remains unproven for this new stage.','Generic loader imports and the gated physical loader exist; offline branch return and fake-only command journals establish test isolation.','Mutable gate/current/checkpoint state is outside the immutable certificate file set; future fresh human receipts and exact token remain mandatory.'])
write_new(OUT/'REVIEW.json',report)
print(json.dumps(dict(status='PASS',checks=len(checks),report=pin(OUT/'REVIEW.json'),positive=positive,negative=negative)))
