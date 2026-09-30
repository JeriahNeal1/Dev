"""Read-only independent audit of root-authored model and saved qualification.

Never imports or executes the distributable, its build/test tools, or a provider.
Writes only new review artifacts beside this script.
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import gzip
import hashlib
import json
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = Path(r'C:\Dev\A2WC511R_RK03_KernelIdentityOffline\kernel_identity')
ANALYSIS = OUT.parent
REPLAY = OUT/'replay_20260930T054149444398Z/INSTRUCTION_REPLAY.json'


def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p = Path(p)
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': sha(b)}
def compact(v): return json.dumps(v, sort_keys=True, separators=(',', ':')).encode()
def normalize(v):
    if isinstance(v, list): return [normalize(x) for x in v]
    if isinstance(v, dict):
        return {k: normalize(x) for k, x in v.items() if k not in ('config_pointer', 'owned_buffer_pointer', 'timestamp')}
    return v


def main():
    checks = []
    def check(name, condition, detail=None):
        checks.append({'name': name, 'pass': bool(condition), 'detail': detail})
        assert condition, name

    sourcepins = read(ROOT/'contract/SOURCE_PINS.json')
    verified = []
    def verify(item):
        actual = pin(item['path'])
        check('hash:'+item['path'], actual['sha256']==item['sha256'] and
            ('bytes' not in item or actual['bytes']==item['bytes']))
        verified.append(actual)
    for item in sourcepins['inputs']: verify(item)
    contract = read(ROOT/'contract/CONTRACT.json')
    data_ast = ast.parse((ROOT/'src/fixed_data.py').read_text())
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in data_ast.body if isinstance(n, ast.Assign)}
    check('embedded_contract_equals_reviewed_contract', json.loads(constants['CONTRACT_JSON'])==contract)
    check('embedded_contract_digest', sha(constants['CONTRACT_JSON'].encode())==constants['CONTRACT_SHA256'])
    rawpin = next(p for p in sourcepins['inputs'] if p['path'].endswith('native_api.jsonl'))
    raw = [json.loads(line) for line in Path(rawpin['path']).read_text().splitlines()]
    calls = [r for r in raw if r['type']=='api_return']
    check('retained_physical_reference_success',len(calls)==85 and all(r['status']==0 for r in calls))
    reference = []
    for row in calls[:-3]:
        action = {'function':row['function'], 'input':normalize(row['input']),
            'output':normalize(row['output']), 'source_sequence':row['sequence']}
        if row['function']=='MonotonicMinimumWait':
            action = {'function':'VirtualWait', 'input':{k:row['input'][k] for k in ('milliseconds','reason')},
                'output':{}, 'source_sequence':row['sequence']}
        reference.append(action)
    check('all_82_normalized_prefix_actions_match',contract['actions'][:82]==reference)
    check('all_3_retained_cleanup_actions_match',contract['cleanup']==[
        {'function':r['function'],'input':normalize(r['input']),'output':normalize(r['output'])} for r in calls[-3:]])
    check('fixed_dimensions',len(contract['actions'])==91 and len(contract['frames'])==24 and len(contract['cleanup'])==3)
    check('fixed_start_and_identity',contract['frames'][22:]==[
        {'tx':'8010f003310101b6','rx':'80f01003710101f6'},
        {'tx':'beef000101af','rx':'beef000f8141325743353131522d524b3032005f'}])
    check('fixed_chunks_exact_ACKs',len(contract['full_upload_chunks'])==15 and
        [x['rx'] for x in contract['frames'][7:22]]==['80f0100176f7']*15)
    check('only_fixed_command_alphabet', [bytes.fromhex(x['tx'])[4] for x in contract['frames']]
        ==[0xbf,0x81,0x83,0x27,0x27,0x10,0x34]+[0x36]*15+[0x31,1])
    check('post_start_controls',[(x['function'],x['input'].get('ioctl')) for x in contract['actions'][85:88]]
        ==[('PassThruStopMsgFilter',None),('PassThruIoctl',2),('PassThruStartMsgFilter',None)])
    check('post_start_baud',contract['actions'][86]['input']['config']['owned_buffer_entries']==[{'parameter':1,'value':62500}])
    flt=contract['actions'][87]['input']
    check('legacy_BEEF_filter',flt['mask']['data_hex']=='ffff' and flt['pattern']['data_hex']=='beef' and flt['flow'] is None)

    imports=[]
    forbidden=[]
    for name in ('__main__.py','fixed_data.py','identity_model.py'):
        tree=ast.parse((ROOT/'src'/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imports.extend(n.name for n in node.names)
            if isinstance(node,ast.ImportFrom): imports.append(node.module)
            if (isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in
                ('open','exec','eval','compile','__import__','input','getattr','setattr')):
                forbidden.append(node.func.id)
    check('closed_static_imports',set(imports)=={'json','sys','hashlib','identity_model','fixed_data'},imports)
    check('no_external_IO_or_dynamic_execution_calls',not forbidden,forbidden)
    # Manual source review complements the narrow AST check: every output call
    # is print; names resembling provider APIs occur only as inert JSON strings.
    manifests=[]
    for label in ('a','b'):
        folder=ROOT/('build_'+label)
        manifest=read(folder/'BUILD_MANIFEST.json');manifests.append(manifest)
        artifact=folder/'rk03_kernel_start_identity_offline.pyz'
        check('artifact_hash_'+label, pin(artifact)['sha256']==manifest['output']['sha256']==
            '04d8332493c98e90fa3c537c8ea0bc12926b5a85e37ea8ea9c826ec8e03c34fe')
        with zipfile.ZipFile(artifact) as archive:
            check('exact_archive_members_'+label,archive.namelist()==['__main__.py','fixed_data.py','identity_model.py'])
            for item in manifest['source']:
                payload=archive.read(item['name'])
                check('archive_source_'+label+'_'+item['name'],payload==(ROOT/'src'/item['name']).read_bytes()
                    and sha(payload)==item['sha256'] and len(payload)==item['bytes'])
        check('build_script_pin_'+label,sha((ROOT/'tools/build.py').read_bytes())==manifest['build_script_sha256'])
    check('byte_identical_builds', (ROOT/'build_a/rk03_kernel_start_identity_offline.pyz').read_bytes()==
        (ROOT/'build_b/rk03_kernel_start_identity_offline.pyz').read_bytes())
    check('byte_identical_manifests',(ROOT/'build_a/BUILD_MANIFEST.json').read_bytes()==(ROOT/'build_b/BUILD_MANIFEST.json').read_bytes())

    q=ANALYSIS/'qualification_tests'
    tests=read(q/'TEST_REPORT.json')
    check('root_saved_qualification',tests['status']=='PASS' and tests['test_count']==tests['passed']==526
        and tests['negative_cases']==433 and all(x['pass'] for x in tests['tests']))
    good=read(q/'POSITIVE_RESULT.json')
    check('positive_completion',good['status']=='PASS_OFFLINE_KERNEL_START_IDENTITY_ONLY' and
        good['tx_attempts']==good['acknowledged_exchanges']==24 and good['identity_validated']
        and good['cleanup_confirmed'] and not any(good['remaining_resources'].values()))
    actions=contract['actions']+contract['cleanup']
    check('positive_journal_all_94_actions',len(good['journal'])==94 and all(
        row['sequence']==i and row['source_action']==i and row['function']==a['function']
        and row['input']==a['input'] and row['output']==a['output'] and row['status']==0
        and row['cleanup']==(i>=91) and row['physical'] is False
        for i,(row,a) in enumerate(zip(good['journal'],actions))))
    negatives=json.loads(gzip.decompress((q/'NEGATIVE_JOURNALS.json.gz').read_bytes()))
    check('unique_433_negative_journals',len(negatives)==433 and len({(x['mode'],x['action']) for x in negatives})==433)
    testmap={x['case']:x for x in tests['tests']}
    negative_pins=[]
    for case in negatives:
        mode,ordinal,result=case['mode'],case['action'],case['result']
        journal=result['journal'];key=mode+'_'+str(ordinal)
        detail=testmap[key]['detail']
        check('negative_saved_digest_'+key,sha(compact(result))==detail['result_sha256'])
        check('negative_stop_boundary_'+key,result['status']=='FAIL_TERMINAL' and
            result['retry_count']==0 and len([x for x in journal if x['source_action']==ordinal])==1 and
            not any(x['source_action']>ordinal and not x['cleanup'] for x in journal))
        transmitted=[x['input']['message']['data_hex'] for x in journal if x['function']=='PassThruWriteMsgs']
        check('negative_fixed_prefix_'+key,transmitted==[f['tx'] for f in contract['frames'][:len(transmitted)]]
            and len(transmitted)==result['tx_attempts']<=24)
        releases=[x['function'] for x in journal if x['cleanup']]
        check('negative_no_release_retry_'+key,len(releases)==len(set(releases)))
        for row in journal:
            a=actions[row['source_action']]
            assert row['function']==a['function'] and row['input']==a['input'] and row['physical'] is False
            if row['source_action']!=ordinal: assert row['status']==0 and row['output']==a['output']
        negative_pins.append({'case':key,'sha256':sha(compact(result)),'tx_attempts':len(transmitted)})
    for index in range(7,22):
        ordinal=next(i for i,a in enumerate(contract['actions']) if a['function']=='PassThruReadMsgs'
            and a['output']['message']['rx_status']==0 and
            len([v for v in contract['actions'][:i] if v['function']=='PassThruWriteMsgs'])==index+1)
        check('each_chunk_ACK_fail_closed_'+str(index-6),all((fault,ordinal) in {(n['mode'],n['action']) for n in negatives}
            for fault in ('api_failure','bad_checksum','wrong_ack','truncated','wrong_length','trailing_bytes')))

    replay=read(REPLAY)
    check('instruction_replay_pass',replay['status']=='PASS_OFFLINE_OEM_START_AND_SINGLE_KERNEL_IDENTITY')
    for item in replay['inputs']+replay['artifacts']: verify(item)
    check('OEM_start_exact_2902',replay['OEM_start']['instructions']==2902 and
        replay['OEM_start']['reply_from_executed_TDR']=='80f01003710101f6' and
        replay['OEM_start']['entry_reached']=='FFFF3004' and replay['OEM_start']['exact_retained_stock_start_suffix_match'])
    for name,variant in replay['kernel_identity_variants'].items():
        coverage=read(variant['coverage']['path'])
        trace=json.loads(gzip.decompress(Path(variant['trace']['path']).read_bytes()))
        check('kernel_identity_'+name,variant['request']=='beef000101af' and
            variant['response_from_executed_SCI']=='beef000f8141325743353131522d524b3032005f'
            and variant['startup']['instruction_count']==4214 and variant['exchange']['instruction_count']==564
            and variant['host_requests']==1 and variant['ROM_data_read_events']==0 and variant['flash_write_events']==0)
        counts=coverage['instruction_counts']
        check('identity_only_coverage_'+name,'FFFF311E' in counts and 'FFFF3134' not in counts
            and 'FFFF323C' not in counts and coverage['registers']['r8']=='00000000'
            and coverage['registers']['r9']=='00000000' and coverage['registers']['r10']=='00000001')
        check('trace_actual_ROM_read_count_zero_'+name,not any(x['mode']=='r' and int(x['address'],16)<0x100000
            for x in trace['memory']))
    reviewed=[ROOT/'src'/x for x in ('__main__.py','identity_model.py','fixed_data.py')]
    reviewed += [ROOT/'tools'/x for x in ('derive_contract.py','build.py','qualify.py')]
    reviewed += [ROOT/'contract/CONTRACT.json',ROOT/'contract/SOURCE_PINS.json',ROOT/'README.md',ROOT/'FUTURE_PHYSICAL_RELEASE_PLAN.md']
    reviewed += [ROOT/('build_'+v)/x for v in ('a','b') for x in ('BUILD_MANIFEST.json','rk03_kernel_start_identity_offline.pyz')]
    reviewed += [q/x for x in ('TEST_REPORT.json','POSITIVE_RESULT.json','NEGATIVE_JOURNALS.json.gz')]
    reviewed += [REPLAY,OUT/'INSTRUCTION_REVIEW.json',OUT/'replay_identity_only.py',Path(__file__)]
    report={'schema':1,'status':'PASS_INDEPENDENT_OFFLINE_MODEL_AND_INSTRUCTION_REVIEW','reviewer':'passive_review',
        'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'physical_operations':0,'provider_loads':0,
        'root_artifact_reexecuted_by_reviewer':False,'blocking_findings':[],
        'ownership':{'root':'static model, contract derivation, builds and 526 qualification checks',
            'passive_review':'bounded CPU replay and independent read-only source/artifact/journal audit'},
        'checks':checks,'checks_passed':len(checks),'reviewed_inputs':[pin(p) for p in reviewed],
        'verified_reference_pins':verified,'negative_journal_audits':negative_pins,
        'instruction_results':{'OEM_start_instructions':2902,'exact_retained_stock_suffix_match':True,
            'kernel_passes':2,'startup_instructions_each':4214,'identity_instructions_each':564,
            'identity_PC':'FFFF311E','raw_read_PC':'FFFF3134','raw_read_executed':False,
            'kernel_ROM_data_read_events':0,'fixed_response':'beef000f8141325743353131522d524b3032005f'},
        'preserved_reviewer_attempts':[
            {'report':pin(OUT/'replay_20260930T053541869778Z/INSTRUCTION_REPLAY.json'),
             'script':pin(OUT/'replay_identity_only_attempt01.py'),
             'reason':'RAM bytes restored correctly but initialize clears retained source-taint origins; restored origins from each recorded write before exact comparison.'},
            {'report':pin(OUT/'replay_20260930T054051015474Z/INSTRUCTION_REPLAY.json'),
             'script':pin(OUT/'replay_identity_only_attempt02.py'),
             'reason':'Reviewer incorrectly excluded shared tx_data loop; actual identity uses it for fifteen RAM-resident identity bytes. Corrected assertion verifies those exact addresses and keeps raw_read/tx_raw excluded.'}],
        'limits':[
            'This is a static fake transcript model. All J2534 function names are inert strings; no provider or native host exists in its three-source closure.',
            'The unchanged kernel has an existing raw-read branch; its absence from execution applies to the fixed identity-only path, not to the complete kernel capability.',
            'The first 82 actions are normalized historical semantics. Pointer addresses and provider timestamps are removed, wait durations are virtual, and start/identity receive metadata is a synthetic fixture.',
            'Captured seed/key and resource IDs are fixed fixtures. Arbitrary seed handling, ABI bounds, actual provider-returned IDs, fragmented streams and wall-clock deadlines are not qualified by this model.',
            'The CPU replay reuses the completed upload state. It executes only the OEM start frame, then two separate KernelSession instances, each with one identity request.',
            'The actual-register instance transfers r0..15/SR/PR/MACH/MACL from the ending OEM parser CPU. VBR1F44 is admitted from retained boot-entry evidence; SCR and readySSR/WDT link to declared OEM fixtures; remaining peripheral defaults and the abstract SCI scheduler are explicit.',
            'No complete reset-to-identity or uninterrupted physical peripheral state is claimed. Model ticks are not silicon cycles or baud measurements. OEM phase ROM-constant reads are separate from zero kernel identity ROM-data reads.',
            'Future native physical release remains separately unqualified and unauthorized. Current model qualification gives no permission for physical start, identity or ROM acquisition.'
        ]}
    target=OUT/'INDEPENDENT_REVIEW.json'
    with target.open('x',encoding='utf-8',newline='\n') as f: json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'report':pin(target)}))


if __name__=='__main__': main()
