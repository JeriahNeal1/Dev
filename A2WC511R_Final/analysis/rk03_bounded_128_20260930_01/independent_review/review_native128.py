"""Read-only independent review of root-authored128 native host and offline evidence."""
from pathlib import Path
import hashlib,json,re,datetime
ROOT=Path(r'C:\Dev\A2WC511R_RK03_Bounded128Physical\bounded_128_physical')
OLD=Path(r'C:\Dev\A2WC511R_RK03_BoundedReadPhysical\bounded_read_physical')
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_128_20260930_01');OUT=A/'independent_review'
K=ROOT.parent/'kernel128';verified={};checks=0
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def check(ok,label):
 global checks
 if not ok:raise AssertionError(label)
 checks+=1
def verify(ref):
 p=pin(ref['path']);check(p['sha256']==ref['sha256'],'changed '+ref['path']);verified[p['path']]=p
def walk(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):verify(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
def transform(data,keys):
 table=[5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8];out=bytearray()
 for n in range(0,len(data),4):
  l,r=int.from_bytes(data[n:n+2],'big'),int.from_bytes(data[n+2:n+4],'big')
  for k in keys:
   e=(r^k)*0x10001;v=sum(table[(e>>s)&31]<<s for s in [0,4,8,12]);l,r=r,l^(((v>>3)|(v<<13))&65535)
  out+=r.to_bytes(2,'big')+l.to_bytes(2,'big')
 return bytes(out)
def section(t,a,b):return t[t.index(a):t.index(b,t.index(a))]
cpath=A/'PHYSICAL_BOUNDED_128_REVIEW_CONTRACT.json';c=read(cpath);oracle=read(ROOT/'fixtures/128_oracle.json')
check(pin(cpath)['sha256']=='767885ac7ec8dae204902dd0bc7dda54c8a7a3890ee9703f20a169fae05ba16a','contract pin')
check(pin(ROOT/'fixtures/128_oracle.json')['sha256']=='fe211a6c727ccd12c0b15b62630fa41e8b81f3324bf324c7f6b1fbd53e48acde','oracle pin')
kernel=(K/'build/a/kernel.bin').read_bytes();check(hashlib.sha256(kernel).hexdigest()==c['kernel_sha256']=='808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653','new pinned128 kernel')
rom=Path(c['bounded_read']['current_rom']['path']).read_bytes();check(hashlib.sha256(rom).hexdigest()==c['bounded_read']['current_rom']['sha256'],'current ROM pin')
expected=bytes.fromhex('beef0086830000000000')+rom[:128];expected+=bytes([sum(expected)%256])
check(c['maximum_requests']==c['maximum_tx']==25 and c['bounded_read']['length']==128 and c['bounded_read']['address']==0,'fixed scope count address length')
check(c['bounded_read']['request']=='beef0008030000000000008038' and bytes.fromhex(c['bounded_read']['response'])==expected and len(expected)==139,'independently derived exact128 wire')
check(oracle['frames'][24]==dict(oracle['frames'][24],tx=c['bounded_read']['request'],rx=expected.hex()),'oracle final frame matches independent contract')
owned=(ROOT/'src/owned_artifact.h').read_text();cipher=bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',owned))
check(len(cipher)==1808 and transform(cipher,[0x6E86,0xF513,0xCE22,0x7856])==kernel,'independent transform recovers exact new embedded kernel')
check(c['kernel_sha256'] in owned and 'KERNEL_SIZE=1808' in owned,'embedded identity and size')
for n in range(15):
 tx=bytes.fromhex(c['ordered_requests'][n+7]['wire_hex']);off=n*128;piece=cipher[off:off+128]
 body=b'\x36'+(0xff3000+off).to_bytes(3,'big')+piece;wire=bytes.fromhex('8010f0')+bytes([len(body)])+body;wire+=bytes([sum(wire)%256])
 check(tx==wire and oracle['frames'][n+7]['tx']==tx.hex(),'exact newly encrypted upload chunk '+str(n))
check([len(bytes.fromhex(x['wire_hex']))-9 for x in c['ordered_requests'][7:22]]==[128]*14+[16],'14 full upload chunks and16byte tail')
for name in ['common.hpp','protocol.hpp','identity_response.hpp','bootstrap.hpp','bootstrap_tests.hpp','j2534_tactrix.h','real_clock.hpp','physical_replay.hpp','first_physical_replay.hpp','full_physical_replay.hpp','identity_physical_replay.hpp']:
 check((ROOT/'src'/name).read_bytes()==(OLD/'src'/name).read_bytes(),'retained byte-identical '+name)
core=(ROOT/'src/probe_core.hpp').read_text();old=(OLD/'src/probe_core.hpp').read_text();parser=(ROOT/'src/bounded_response.hpp').read_text();main=(ROOT/'src/main.cpp').read_text()
for start,end in [(' void setup()', ' Bytes exchange('),(' Bytes exchange(', ' template<class F> long cleanup_call'),(' template<class F> long cleanup_call',' void identity_transport()'),(' void identity_transport()', ' int run()')]:check(section(core,start,end)==section(old,start,end),'unchanged protocol mechanism '+start)
check(section(core,'try{setup();','identity_validated=true;')==section(old,'try{setup();','identity_validated=true;'),'unchanged control sequence through identity')
check('++pieces<=143' in parser and 'm.DataSize<=139' in parser and 'bytes.size()+data.size()<=139' in parser and '++indicators<=4' in parser,'strict139 parser with143record limit')
check(re.search(r'static Bytes expected\(\)\{return decode\("([0-9a-f]+)"\);\}',parser).group(1)==expected.hex(),'compiled expected reply equals independent oracle')
check('beef0086830000000000' in parser and 'Bounded response checksum' in parser,'exact header and checksum acceptance')
check(core.count('exchange(24)')==1 and 'stage<25' in core and 'next_tx<25' in core and 'identity_validated&&kernel_filter&&filtered&&requested_baud==62500' in core,'one read only after valid identity')
check('for(unsigned i=0;i<128;i++)' in core and 'reply.data()+10,128' in core and '\\"length\\":128' in core,'all128 mismatch positions reported')
check(core.index('require(reply==expected')<core.index('bounded_validated=true;protocol_complete=true'),'no premature successful flags')
check(main.index('return probe.run();')<main.index('const Bindings b=physical_bindings()')<main.index('LoadLibraryExW('),'offline returns before physical bootstrap/loader')
check('--physical-bounded-rom-read-128' in main and 'argc==6' in main,'exact new physical CLI only')
builds=[read(ROOT/n/'BUILD.json') for n in ['build_a','build_b']]
for b in builds:
 walk(b);check(b['status']=='PASS_BUILD_ONLY' and pin(b['exe_path'])['sha256']==b['exe_sha256'],'build/executable pins')
check(builds[0]['source_inputs']==builds[1]['source_inputs'],'identical build source closure')
check(builds[0]['exe_sha256']==builds[1]['exe_sha256']=='1e98524252b28b634129bc3622b37e739b18d99ea5955209c9857a8f4ce02c45','identical clean new PE builds')
latest=read(ROOT/'reports/LATEST_QUALIFICATION.json');walk(latest);r=read(latest['report']['path']);walk(r['inputs'])
check(r['status']=='PASS' and r['test_cases']==r['passed_cases']==349 and r['physical_operations']==r['real_provider_loads']==0,'349 scoped fake tests passed')
old_failed=Path(r'C:\Dev\A2WC511R_RK03_BoundedReadPhysical\physical_session\RK03_BOUNDED_ROM_READ_01\native_api.jsonl');oldrows=[json.loads(x) for x in old_failed.read_text().splitlines()];failed_message=next(x['output']['message'] for x in oldrows if x.get('type')=='api_return' and x.get('sequence')==93)
positive=negative=0;total_tx=0
for case in r['cases']:
 for k in ['journal','stdout','stderr']:verify(case[k])
 check(case['command'][1] in ['--offline-fixture','--offline-real-clock-fixture'],'offline mode only')
 rows=[json.loads(x) for x in Path(case['journal']['path']).read_text().splitlines()];a=[x for x in rows if x.get('type')=='api_return'];tx=[x for x in a if x['function']=='PassThruWriteMsgs'];events=[x for x in rows if x.get('type')=='bounded_read_result'];terminal=rows[-1]
 check(rows[0]['physical'] is False and rows[0]['provider_loaded'] is False and all(x.get('physical',False) is False for x in rows),'fake journal only')
 check(len(tx)==case['tx_attempts']<=25,'bounded TX no retries');total_tx+=len(tx)
 for stage,w in enumerate(tx):
  sent=w['input']['message']['data_hex']
  if stage!=4:check(sent==c['ordered_requests'][stage]['wire_hex'],'exact fixed native wire '+str(stage))
  else:
   data=b''.join(bytes.fromhex(x['output']['message']['data_hex']) for x in a if tx[3]['sequence']<x['sequence']<w['sequence'] and x['function']=='PassThruReadMsgs' and x['status']==0 and x['output']['message']['rx_status']==0)
   key=transform(data[6:10],[0x88F0,0x6E74,0x6B70,0x3563,0x9D34,0xDBA3,0x503D,0xAFB8,0x3608,0x834F,0x3382,0x7CA3,0x437D,0x72EB,0x33BC,0x53DA]);k=bytes.fromhex('8010f0062702')+key;k+=bytes([sum(k)%256]);check(sent==k.hex(),'actual seed-derived key')
 for n,x in enumerate(a):
  if x['status'] and not x.get('cleanup'):check(all(y.get('cleanup') for y in a[n+1:]),'only cleanup follows first API error')
 if case['exit_code']==0:
  positive+=1;check(terminal['status']=='PASS_OFFLINE_BOUNDED_ROM_READ_128_ONLY' and terminal['state']['bounded_validated'] and terminal['cleanup_confirmed'],'positive complete')
  check(len(tx)==25 and len(events)==1 and events[0]['response_hex']==expected.hex() and events[0]['length']==128 and events[0]['payload_hex']==rom[:128].hex(),'positive exact139frame128data')
 else:negative+=1;check(case['exit_code']==1 and terminal['status']=='FAIL_TERMINAL','negative fail closed')
 if case['case']=='failed512_reference':
  reads=[x for x in a if x['function']=='PassThruReadMsgs' and x['sequence']>tx[-1]['sequence']];check(len(reads)==2 and reads[-1]['output']['message']==failed_message,'actual228byte failed record metadata rejected without next read');check(not events and 'metadata bounds' in terminal['failure'],'old failure cannot validate as128')
 if case['mode']=='real_clock':
  waits=[x for x in a if x['function']=='MonotonicMinimumWait'];check([x['input']['milliseconds'] for x in waits]==[200,100,200] and all(x['api_elapsed_ticks']*1000>=x['input']['milliseconds']*x['qpc_frequency'] for x in waits),'actual minima unchanged')
check(positive==154 and negative==195,'focused matrix counts')
check(r['all138_splits_passed'] and r['all128_data_positions_rejected'] and r['all128_simultaneous_mismatches_preserved'],'all new splits and mismatch positions')
controls=['launch_bounded_once.py','launch_oem_return_once.py','check_clients.ps1','seal_bounded_result.py','seal_oem_return_bounded.py','test_launcher_offline.py','test_oem_return_controls.py','test_result_validator.py']
for n in controls:check((A/n).read_bytes()==(ROOT/'release_controls'/n).read_bytes(),'tracked control matches '+n)
launch=(A/'launch_bounded_once.py').read_text();validation=(A/'seal_bounded_result.py').read_text();clients=(A/'check_clients.ps1').read_text();recovery=(A/'seal_oem_return_bounded.py').read_text()
check("TOKEN = 'PROCEED RK03 128 BYTE ROM READ'" in launch and "['IGNITION OFF', 'TEST MODE ON']" in launch and 'qualification_sha256' in launch,'fresh exact new gate and certificate binding')
check(".open('x'" in launch and 'SINGLE_LAUNCH_RESERVED_NO_RETRY' in launch and 'wait_for_child' in launch,'exclusive launch and retained child ownership')
check('rk03_bounded_rom_read_physical32|rk03_bounded_rom_read_128_physical32' in clients and 'rk03_kernel_start_identity_physical32' in clients,'old and new client names retained')
check("len(data)==139" in validation and 'address=0,length=128' in validation and "terminal['state']['bounded_validated']" in validation and 'bounded_ROM_read=True if validation else "UNCONFIRMED"' in validation,'independent result validator strict128 and honest failures')
check('RK03_FINAL_TWO_PASS_128' in recovery and "if g['bounded_physical']=='PASS' else 'OFFLINE ONLY: exact first-divergence" in recovery,'two-pass qualification remains conditional on success')
for n,count in [('LAUNCHER_TESTS_V2.json',36),('OEM_RETURN_CONTROL_TESTS_V2.json',14),('RESULT_VALIDATOR_TESTS.json',54)]:
 value=read(A/n);check(value['status']=='PASS' and value['checks_passed']==count,'retained new control test '+n);walk(value)
check(not (ROOT.parent/'physical_session').exists(),'no new physical session created')
paths=[cpath,ROOT/'fixtures/128_oracle.json',ROOT/'tools/derive_128.py',ROOT/'tools/finish_128_derivation.py',ROOT/'tools/test_bounded_physical.py',ROOT/'build_a/BUILD.json',ROOT/'build_b/BUILD.json',Path(latest['report']['path']),old_failed,A/'FIXED_UPLOAD_128_MANIFEST.json',Path(__file__)]+[ROOT/'src'/x for x in ['probe_core.hpp','bounded_response.hpp','main.cpp','pins.hpp','owned_artifact.h','fixtures.hpp','fake_backend.hpp']]+[A/n for n in controls+['LAUNCHER_TESTS_V2.json','OEM_RETURN_CONTROL_TESTS_V2.json','RESULT_VALIDATOR_TESTS.json']]
result=dict(schema=1,status='PASS',scope='INDEPENDENT_REVIEW_ROOT_AUTHORED_FIXED128_NATIVE_RELEASE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='passive_review',author_roles={'kernel128_source_and_instruction_test_author':'passive_review; independent root kernel review required separately','native_host_fixture_runner_and_controls_author':'root (adapted prior passive_review runner)','native_host_and_new_runner_reviewer':'passive_review'},checks_passed=checks,verified_pins=len(verified),test_report=latest['report'],cases=dict(total=349,positive=positive,negative=negative,total_TX=total_tx),kernel_sha256=c['kernel_sha256'],native_executable_sha256=builds[0]['exe_sha256'],reviewed_files=[pin(p) for p in paths],verification_pinset_sha256=hashlib.sha256(json.dumps(verified,sort_keys=True).encode()).hexdigest(),conclusions=['Two matching new PE builds bind the new1808-byte kernel; independent inverse transform recovers its exact bytes from embedded ciphertext and all15 upload frames match.','Transport, setup, cleanup and timeout mechanisms are unchanged; fixed128 request and139-byte parser/event bounds are correct.','All349 existing journals and pins pass this independent read-only audit. Actual failed228-byte record is rejected before another receive.','New human token/session, one-shot reservation, client detection, result and OEM-return controls preserve the existing boundaries.'],blocking_findings=[],limitations=['Kernel source/model author review is not independent; root separately reviews it.','Inherited runner report labels refer to prior passive_review authorship; current128 adaptation/execution was by root, independently reviewed here.','No old qualification suite, new native binary, provider, client scanner, or hardware was executed by this review.','The physical_identity_replay fixture reuses historical RX/version metadata with new simulated kernel upload bytes; it is not a physical128 success.','Shortening the fixed response is an authorized new experiment, not a proven correction for the prior failure.','Same kernel identity text does not distinguish new image; exact kernel/native hashes and upload bytes establish release binding.','Copied old512 sealing/root-review tools remain inactive references and were excluded from this active native/control review; final128 sealing mechanics require separate review.','Full128 two-pass physical qualification remains conditional on the new physical bounded128 and subsequent OEM return passing.'])
with (OUT/'REVIEW.json').open('x',encoding='utf8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(status='PASS',checks=checks,pins=len(verified),report=pin(OUT/'REVIEW.json'))))
