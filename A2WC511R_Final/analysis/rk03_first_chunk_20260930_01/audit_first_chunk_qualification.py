"""Root evidence audit: read/hash only; never invoke a PE or provider."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,collections
HERE=Path(__file__).resolve().parent
ROOT=Path(r'C:\Dev\A2WC511R_RK03_FirstChunkPhysical\first_chunk')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(c,m):
    if not c:raise RuntimeError(m)
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
pointer=read(ROOT/'reports/LATEST_QUALIFICATION.json');report_path=Path(pointer['report']['path'])
require(sha(report_path)==pointer['report']['sha256'],'Qualification pointer')
report=read(report_path)
require(report['status']=='PASS' and report['passed_cases']==report['test_cases']==156,'All156cases')
require(report['physical_operations']==report['real_provider_loads']==0,'No physical test operations')
require(report['physical_controls_before']==report['physical_controls_after'] and all(v is None for v in report['physical_controls_after'].values()),'Real session remains unused')
checked={}
def verify_tree(v):
    if isinstance(v,dict):
        if 'path' in v and 'sha256' in v:
            p=Path(v['path']); expected=v['sha256'].lower()
            require(p.is_file() and sha(p)==expected,'Changed report input: '+str(p))
            if str(p) in checked: require(checked[str(p)]==expected,'Conflicting pin')
            checked[str(p)]=expected
        for x in v.values():verify_tree(x)
    elif isinstance(v,list):
        for x in v:verify_tree(x)
verify_tree(report)
contract=read(HERE/'FIRST_CHUNK_REVIEW_CONTRACT.json')
wires=[r['wire_hex'] for r in contract['ordered_requests']]
wires[4]='8010f0062702e78f1f2165'
seed_cases=read(Path(r'C:\Dev\A2WC511R_ReadKernel\evidence\contracts\KWP_PRODUCER_REGRESSIONS.json'))['seed_cases']
def frame(hexbody):
    body=bytes.fromhex(hexbody);raw=bytes.fromhex('8010f0')+bytes([len(body)])+body
    return (raw+bytes([sum(raw)&255])).hex()
counts=collections.Counter();writes=0;waits=[]
for case in report['cases']:
    require(case['status']=='PASS','Case not passing');counts[case['mode']]+=1
    rows=[json.loads(x) for x in Path(case['journal']['path']).read_text().splitlines()]
    require(all(r.get('physical',False) is False for r in rows),'Physical event in qualification')
    tx=[r for r in rows if r.get('type')=='api_intent' and r.get('function')=='PassThruWriteMsgs']
    expected=wires.copy()
    if case['case'].startswith('seed_vector_'):
        vector=seed_cases[int(case['case'].rsplit('_',1)[1])]
        expected[4]=frame('2702'+vector['timer_and_stored_expected_key'])
    require(len(tx)<=8 and [r['input']['message']['data_hex'] for r in tx]==expected[:len(tx)],'Fixed wire prefix or count')
    require(sum(r['input']['message']['data_hex'][8:10]=='36' for r in tx)<=1,'Repeated36')
    writes+=len(tx)
    if case['mode']=='real_clock':
        require([w['requested_ms'] for w in case['real_wait_measurements']]==[200,100,200],'Wait schedule')
        for w in case['real_wait_measurements']:
            require(w['elapsed_qpc_ticks']*1000>=w['requested_ms']*w['qpc_frequency'],'Short real wait')
            waits.append(w['elapsed_qpc_ticks']*1000/w['qpc_frequency'])
    if case['case']=='physical_transition_replay':
        previous=[json.loads(x) for x in Path(report['inputs']['successful_physical_transition']['path']).read_text().splitlines()]
        old=[r['output'] for r in previous if r.get('type')=='api_return' and r.get('function')=='PassThruReadMsgs']
        new=[r['output'] for r in rows if r.get('type')=='api_return' and r.get('function')=='PassThruReadMsgs'][:6]
        require(new==old,'Exact successful physical RX replay')
require(counts=={'virtual':128,'real_clock':4,'bootstrap':24},'Required category coverage')
for row in read(ROOT/'INPUT_PINS.json')['inputs']:verify_tree(row)
for leaf in ('LAUNCHER_TESTS_V2.json','LAUNCHER_TESTS_V2_OPTIMIZED.json','OEM_RETURN_CONTROL_TESTS_V2.json'):
    doc=read(HERE/leaf);require(doc['status']=='PASS','Root control test');verify_tree(doc)
out=HERE/'root_review';out.mkdir(exist_ok=False)
doc=dict(status='PASS_INDEPENDENT_ROOT_RUNNER_AND_EVIDENCE_REVIEW',created_utc=datetime.now(timezone.utc).isoformat(),
    reviewer='root',native_execution_by_this_audit=False,physical_authorization=False,
    reviewed_runner=pin(ROOT/'tools/test_first_chunk_independent.py'),qualification_report=pin(report_path),
    reviewed_build=pin(ROOT/'build_a/rk03_first_chunk_probe32.exe'),category_counts=dict(counts),
    unique_hashes_verified=len(checked),fixed_transmit_records_checked=writes,
    actual_fake_host_wait_ms=waits,unresolved_findings=[],
    review_basis=[
      'Root read the independent runner in full and its final startup, bootstrap, real-clock and dispatcher deltas.',
      'Expected wire and reply evidence derives from sealed physical log and retained OEM instruction replay; malformed fixtures are checked at the intended failure boundary.',
      'All16 reviewed seed vectors, initial five configuration readbacks, broad filter, queue ordering, later strict ACKs and cleanup failure cases remain represented.',
      'Root independently checked every journal transmit prefix/count and all twelve real-clock minimum wait measurements from156 reported cases.',
      'Both successful physical transcript fixture variants retain the exact six historical RX outputs; synthetic handles and new host timing are explicitly distinguished.',
      'Native offline bootstrap uses dummy files and shares gate/export validation; no loader branch executes in tests.',
      'Root reviewed main/bootstrap/real-clock source; separate native reviewer assesses structural exclusions and compiled artifacts.',
      'Original ROM/846 checkpoint files remain hash-identical; no ingestion or old qualification repeated.'],
    files=[dict(path=p,sha256=s) for p,s in sorted(checked.items())],audit_source=pin(Path(__file__)))
with (out/'ROOT_REVIEW.json').open('x',encoding='utf-8') as f:json.dump(doc,f,indent=2);f.write('\n')
print(json.dumps({'status':doc['status'],'hashes_verified':len(checked),'writes_checked':writes,'review':pin(out/'ROOT_REVIEW.json')}))
