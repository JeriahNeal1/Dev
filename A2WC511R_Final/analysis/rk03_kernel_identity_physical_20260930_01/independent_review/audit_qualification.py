"""Read-only source/result audit after same-PE fake qualification. No PE launch."""
from pathlib import Path
from collections import Counter
import difflib
import hashlib
import json

OUT=Path(__file__).resolve().parent
ROOT=Path(r'C:\Dev\A2WC511R_RK03_KernelIdentityPhysical\kernel_identity_physical')
BASE=Path(r'C:\Dev\A2WC511R_RK03_FullUploadPhysical\full_upload_physical')
REPORT=ROOT/'reports/qualification_20260930T061208911770Z/TEST_REPORT.json'
CONTRACT=OUT.parent/'PHYSICAL_IDENTITY_REVIEW_CONTRACT.json'

def pin(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
def section(text,start,end):return text.split(start,1)[1].split(end,1)[0].strip()
def loc(name,text):
    p=ROOT/'src'/name
    lines=p.read_text().splitlines()
    return {'path':str(p),'line':next(i+1 for i,x in enumerate(lines) if text in x),'match':text}

def main():
    report=read(REPORT)
    assert report['status']=='PASS' and report['test_cases']==report['passed_cases']==386
    assert report['physical_operations']==report['real_provider_loads']==0
    assert report['input_pins_unchanged'] is True
    assert report['physical_controls_before']==report['physical_controls_after']=={'new_worktree_physical_session_exists':False}
    # Only paths explicitly referenced by the completed report are read.
    pins={};refs=0
    def visit(value):
        nonlocal refs
        if isinstance(value,list):
            for x in value:visit(x)
        elif isinstance(value,dict):
            if 'path' in value and 'sha256' in value:
                refs+=1;p=Path(value['path']);actual=pin(p)
                assert actual['sha256']==value['sha256']
                if 'bytes' in value:assert actual['bytes']==value['bytes']
                if str(p) in pins:assert pins[str(p)]==actual
                pins[str(p)]=actual
            for x in value.values():visit(x)
    visit(report)
    mode_counts=Counter(x['mode'] for x in report['cases'])
    assert mode_counts=={'virtual':358,'real_clock':4,'bootstrap':24}
    cases={(x['mode'],x['case']):x for x in report['cases']}
    prior=read(BASE/'reports/qualification_20260930T045456687736Z/TEST_REPORT.json')
    assert len(prior['cases'])==311
    assert {(x['mode'],x['case']) for x in prior['cases']} <= set(cases)
    positive=sum(x['exit_code']==0 and x['mode']!='bootstrap' for x in report['cases'])
    negative=sum(x['exit_code']==1 for x in report['cases'])
    assert positive==50 and negative==312
    late=[]
    for name in ('start_late_reply','identity_late_reply'):
        item=cases['virtual',name]
        rows=[json.loads(x) for x in Path(item['journal']['path']).read_text().splitlines()]
        returned=[x for x in rows if x.get('type')=='api_return' and not x.get('cleanup',False)]
        last=returned[-1]
        assert last['function']=='PassThruReadMsgs' and last['status']==0
        elapsed=last['api_elapsed_ticks']*1000/last['qpc_frequency']
        assert elapsed>=2000 and 'deadline' in rows[-1]['failure'].lower()
        late.append({'case':name,'elapsed_ms':elapsed,'tx_attempts':rows[-1]['state']['tx_attempts'],
                     'reply':last['output']['message']['data_hex'],'failure':rows[-1]['failure']})
    builds=[read(ROOT/f'build_{x}/BUILD.json') for x in ('a','b')]
    assert all(pin(b['exe_path'])['sha256']==b['exe_sha256']==
        '623dc766ca69a97b16f7beabc9acb909a1225eabb8a21c40fe8379b4f72b593f' for b in builds)
    core=(ROOT/'src/probe_core.hpp').read_text();oldcore=(BASE/'src/probe_core.hpp').read_text()
    unchanged=['common.hpp','protocol.hpp','owned_artifact.h','real_clock.hpp','j2534_tactrix.h',
               'bootstrap.hpp','bootstrap_tests.hpp','physical_replay.hpp','first_physical_replay.hpp']
    for name in unchanged:assert (ROOT/'src'/name).read_bytes()==(BASE/'src'/name).read_bytes()
    for start,end in [(' void setup(){',' Bytes exchange('),(' template<class F> long cleanup_call(',' void cleanup(){'),
                      (' void wait(',' void identity_transport(){')]:
        oldend=' int run(){' if end==' void identity_transport(){' else end
        assert section(core,start,end)==section(oldcore,start,oldend)
    patch=''.join(difflib.unified_diff(oldcore.splitlines(True),core.splitlines(True),
        fromfile=str(BASE/'src/probe_core.hpp'),tofile=str(ROOT/'src/probe_core.hpp')))
    with (OUT/'REVIEWED_NATIVE_CORE_DIFF.patch').open('x',encoding='utf-8',newline='\n') as f:f.write(patch)
    findings=[
        {'finding':'Two suffix stages are selected before cipher-offset arithmetic; fixed24TX ceiling and all15ACK/start/filter admission guards.',
         'source':loc('probe_core.hpp','Bytes request(unsigned stage)const')},
        {'finding':'Exactly20 identity bytes;24 records maximum includes20one-byte fragments plus4 leading indicators; only exact fixed reply prefixes accepted.',
         'source':loc('identity_response.hpp','struct IdentityReply')},
        {'finding':'SSM parser remains byte-identical; shared exchange adds explicit identity branch plus post-return whole-frame deadline. Both delayed valid replies fail.',
         'source':loc('probe_core.hpp','require(GetTickCount64()<deadline')},
        {'finding':'OEM Stop marks attempt only when call occurs, clears ownership on success before logging and records failed ownership as unconfirmed; cleanup never retries that Stop.',
         'source':loc('probe_core.hpp','void identity_transport()')},
        {'finding':'62500 configuration is checked for status, list/count/pointer/value/canary mutation. New BEEF maskffff/patternbeef has null flow and allocation tracked before output/log failure.',
         'source':loc('probe_core.hpp','kernel_filter=true;filter_requested=true')},
        {'finding':'Completion requires exact start ACK then exact identity response; after success only cleanup and terminal output remain.',
         'source':loc('probe_core.hpp','require(exchange(23)==IdentityReply::expected()')},
        {'finding':'Same native core receives either static in-process fake API or gated physical API; fake/bootstrap dispatch returns before provider loading.',
         'source':loc('main.cpp','const bool real_fake=')},
        {'finding':'Fake enforces OEMfilter702 removal before62500/newfilter703 and identity; complete recorded physical prefix is retained as fake data with explicit handle mapping.',
         'source':loc('fake_backend.hpp','if(state().writes==23)')}
    ]
    result={'schema':1,'status':'PASS_NATIVE_SOURCE_AND_NEW_PE_FAKE_QUALIFICATION_REVIEW',
        'reviewer':'passive_review','blocking_native_findings':[],
        'review_role':'Independent reviewer of root-authored native code; author/executor of the new runner. Root independently reviews runner/results.',
        'physical_operations':0,'provider_loads':0,'no_real_session_created':True,
        'qualification_report':pin(REPORT),'contract':pin(CONTRACT),'runner':pin(ROOT/'tools/test_identity_physical_independent.py'),
        'executable':pin(builds[0]['exe_path']),'second_executable':pin(builds[1]['exe_path']),
        'mode_counts':dict(mode_counts),'protocol_positive_cases':positive,'protocol_negative_cases':negative,'bootstrap_cases':24,
        'retained_cases_exercised_only_on_new_PE':311,'new_suffix_cases':75,
        'hash_references_verified':refs,'unique_paths_verified':len(pins),'verified_files':list(pins.values()),
        'late_valid_reply_negatives':late,'native_findings':findings,
        'unchanged_native_files':[pin(ROOT/'src'/name) for name in unchanged],
        'normalized_unchanged_functions':['setup','cleanup_call','wait','change_baud_and_clear'],
        'core_diff':pin(OUT/'REVIEWED_NATIVE_CORE_DIFF.patch'),'audit_source':pin(Path(__file__)),
        'limits':[
            'This review qualifies bounded offline behavior of the physical-capable artifact; no physical session, provider load or vehicle success is demonstrated.',
            'The unchanged kernel contains its earlier raw-read branch. The native host exposes no path to a raw-read request, arbitrary entry, address or payload.',
            'The22TX/44RX historical prefix preserves provider metadata; new host timing, handle IDs and start/identity responses in these tests are synthetic.',
            'BAUD SET success/output checks do not attest measured effective electrical baud. The instruction replay is separate pinned evidence with declared peripheral fixtures.',
            'The fixed parser rejects coalesced trailing data; no extra receive is issued to attest absence of a separately queued record after an accepted full reply.',
            'Release-control review remains separate; publication of this source report does not authorize a physical invocation.'
        ]}
    save(OUT/'NATIVE_AND_QUALIFICATION_REVIEW.json',result)
    print(json.dumps({'status':result['status'],'report':pin(OUT/'NATIVE_AND_QUALIFICATION_REVIEW.json'),
                      'refs':refs,'unique':len(pins),'late':late}))

if __name__=='__main__':main()
