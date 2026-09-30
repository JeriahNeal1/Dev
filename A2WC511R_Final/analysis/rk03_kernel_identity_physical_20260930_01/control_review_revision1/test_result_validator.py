"""Offline result-validator checks over existing fake journals; no executable invocation."""
from pathlib import Path
import copy,json
import seal_identity_result as m
ROOT=Path(r'C:\Dev\A2WC511R_RK03_KernelIdentityPhysical\kernel_identity_physical')
latest=json.loads((ROOT/'reports/LATEST_QUALIFICATION.json').read_text())
report=json.loads(Path(latest['report']['path']).read_text())
contract=m.read(m.HERE/'PHYSICAL_IDENTITY_REVIEW_CONTRACT.json')
checks=[];base=None
for case in report['cases']:
    if case['mode']!='real_clock':continue
    rows=[json.loads(x) for x in Path(case['journal']['path']).read_text().splitlines()]
    result=m.validate_rows(rows,contract,physical=False)
    m.require(result['transfers']==15 and result['acknowledgements']==15,'All chunks/ACKs')
    checks.append('accept_'+case['case'])
    if case['case']=='success':base=rows
m.require(base is not None,'Positive fixture exists')
def reject(name,change):
    rows=copy.deepcopy(base);change(rows)
    try:m.validate_rows(rows,contract,physical=False)
    except (RuntimeError,KeyError,ValueError,IndexError):checks.append(name)
    else:raise RuntimeError('Accepted '+name)
def replace_tx(rows,stage,wire):
    indices=[r['sequence'] for r in rows if r.get('type')=='api_intent' and r.get('function')=='PassThruWriteMsgs']
    for r in rows:
        if r.get('sequence')==indices[stage]:
            for side in ('input','output'):
                if 'message' in r.get(side,{}):r[side]['message']['data_hex']=wire
def bad_ack(rows,stage):
    writes=[r for r in rows if r.get('type')=='api_return' and r.get('function')=='PassThruWriteMsgs']
    r=next(r for r in rows if r.get('type')=='api_return' and r.get('function')=='PassThruReadMsgs' and r['sequence']>writes[stage]['sequence'])
    r['output']['message']['data_hex']='80f0100175f6'
for stage in range(7,22):reject('reject_wrong_ACK_chunk'+str(stage-6),lambda r,s=stage:bad_ack(r,s))
reject('reject_kernel_start_at_final_frame',lambda r:replace_tx(r,21,'8010f003310101b6'))
reject('reject_duplicate_final_frame',lambda r:replace_tx(r,21,contract['ordered_requests'][20]['wire_hex']))
reject('reject_changed_seed_derived_key',lambda r:replace_tx(r,4,'8010f006270200000000af'))
reject('reject_second_start_at_identity',lambda r:replace_tx(r,23,'8010f003310101b6'))
reject('reject_ROM_command_at_identity',lambda r:replace_tx(r,23,'beef000103b1'))
reject('reject_wrong_fixed_start',lambda r:replace_tx(r,22,'8010f003310102b7'))
reject('reject_wrong_identity_response',lambda r:bad_ack(r,23))
reject('reject_wrong_start_ACK',lambda r:bad_ack(r,22))
reject('reject_cleanup_failure',lambda r:r[-1].update(cleanup_confirmed=False))
reject('reject_physical_label_in_fake_test',lambda r:r[0].update(physical=True))
bindings={'session_id':'OFFLINE_RESULT_VALIDATOR_FIXTURE','exe_sha256':'a'*64,'contract_sha256':'b'*64,'provider_sha256':contract['physical_provider']['sha256']}
physical_fixture=copy.deepcopy(base)
for row in physical_fixture:
    if 'physical' in row:row['physical']=True
physical_fixture[0].update(bindings,provider_path=contract['physical_provider']['path'],authorization_verified=True,
    root_reservation_verified=True,native_invocation_reserved=True,synthetic_fixture_for_validator_only=True)
physical_fixture[-1]['status']='PASS_KERNEL_START_IDENTITY_ONLY'
m.validate_rows(physical_fixture,contract,bindings=bindings);checks.append('accept_synthetic_physical_envelope_no_PE')
def reject_physical(name,change):
    rows=copy.deepcopy(physical_fixture);change(rows)
    try:m.validate_rows(rows,contract,bindings=bindings)
    except (RuntimeError,KeyError,ValueError,IndexError):checks.append(name)
    else:raise RuntimeError('Accepted '+name)
for key in ('session_id','exe_sha256','contract_sha256','provider_sha256','provider_path'):
    reject_physical('reject_startup_'+key,lambda r,k=key:r[0].update({k:'WRONG'}))
for key in ('authorization_verified','root_reservation_verified','native_invocation_reserved'):
    reject_physical('reject_startup_'+key,lambda r,k=key:r[0].update({k:False}))
reject_physical('reject_duplicate_startup',lambda r:r.insert(1,copy.deepcopy(r[0])))
def wrong_control(rows,function,change):
    seq=next(r['sequence'] for r in rows if r.get('type')=='api_intent' and r.get('function')==function)
    for row in rows:
        if row.get('sequence')==seq:change(row)
reject_physical('reject_initial_SET_value',lambda r:wrong_control(r,'PassThruIoctl',lambda x:x['input']['config']['owned_buffer_entries'][0].update(value=9)))
reject_physical('reject_filter_type',lambda r:wrong_control(r,'PassThruStartMsgFilter',lambda x:x['input'].update(filter_type=2)))
def wrong_get(rows):
    r=next(r for r in rows if r.get('type')=='api_return' and r.get('function')=='PassThruIoctl' and r['input']['ioctl']==1)
    r['output']['config']['owned_buffer_entries'][0]['value']=1
reject_physical('reject_effective_GET_value_even_with_true_state_flag',wrong_get)
def swapped_setup(rows):
    selected=[r for r in rows if r.get('type')=='api_intent' and r.get('function')=='PassThruIoctl' and r['input']['ioctl']==2][:2]
    values=[copy.deepcopy(r['input']) for r in selected]
    for r in rows:
        for i,s in enumerate(selected):
            if r.get('sequence')==s['sequence']:r['input']=copy.deepcopy(values[1-i])
reject_physical('reject_reordered_initial_SET_calls',swapped_setup)
m.write_new(m.HERE/'RESULT_VALIDATOR_TESTS.json',{'status':'PASS','checks_passed':len(checks),'checks':checks,
    'physical_operations':0,'provider_loads':0,'PE_invocations':0,'validator':m.pin(Path(m.__file__)),'test':m.pin(Path(__file__))})
print(json.dumps({'status':'PASS','checks':len(checks)}))
