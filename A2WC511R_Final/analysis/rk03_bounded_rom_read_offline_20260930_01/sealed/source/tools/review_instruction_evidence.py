"""Independent read-only audit of the one-read SH-2E continuation evidence."""
from pathlib import Path
import collections,gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
A=Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_bounded_rom_read_offline_20260930_01')
def read(p):return json.loads(Path(p).read_text())
def pin(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
seen={}
def verify(x):
    if isinstance(x,dict):
        if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str):
            p=x['path'];actual=seen.setdefault(p,pin(p));assert actual['sha256']==x['sha256'],p
            if 'bytes' in x:assert actual['bytes']==x['bytes'],p
        for v in x.values():verify(v)
    elif isinstance(x,list):
        for v in x:verify(v)
def main():
    ref=read(A/'instruction_review/INSTRUCTION_REVIEW.json');verify(ref)
    report=read(ref['replay']['path']);verify(report)
    contract=read(A/'instruction_review/FIXED_READ_CONTRACT.json');verify(contract)
    model=read(ROOT/'contract/CONTRACT.json');root_contract=read(A/'ROOT_FIXED_READ_CONTRACT.json')
    assert model['fixed_read']['request']==root_contract['request']==contract['request_hex']==report['request_hex']=='beef00080300000000000200ba'
    assert model['fixed_read']['response']==root_contract['response']==contract['reply_hex']==report['response_hex']
    assert contract['data_hex']==root_contract['expected_bytes_hex']
    assert contract['length']==512 and contract['address']=='00000000' and contract['pass']==0
    trace=json.loads(gzip.decompress(Path(report['trace']['path']).read_bytes()))
    coverage=read(report['kernel_coverage']['path']);checkpoint=read(report['checkpoint']['path'])
    manifest=read(next(v['path'] for v in report['inputs'] if v['path'].endswith('rk02_01\\manifest.json')))
    assert len(trace['instructions'])==report['instruction_count']==10327
    assert checkpoint['new_CPU_instructions_before_read']==0 and checkpoint['queues_empty']
    assert checkpoint['registers']['r8']==checkpoint['registers']['r9']=='00000000' and checkpoint['registers']['r10']=='00000001'
    assert checkpoint['SCI_events_exactly_reproduced']==220 and checkpoint['other_peripheral_events_exactly_reproduced']==10
    assert coverage['registers']['r8']=='00000200' and coverage['registers']['r9']=='00000000'
    assert coverage['terminal'] is None and len(coverage['exchanges'])==1
    pcs={int(r['pc'],16) for r in trace['instructions']}
    assert pcs<=set(manifest['instruction_addresses'])
    assert all(manifest['symbols'][n] not in pcs for n in report['forbidden_symbols_unexecuted'])
    assert manifest['symbols']['tx_data'] in pcs and manifest['symbols']['raw_read'] in pcs
    rr=[r for r in trace['memory'] if r['mode']=='r' and int(r['address'],16)<0x100000]
    assert len(rr)==512 and [int(r['address'],16) for r in rr]==list(range(512))
    assert all(r['size']==1 and int(r['pc'],16)==manifest['symbols']['tx_data'] for r in rr)
    data=bytes(int(r['value'],16) for r in rr);expected=(A/'EXPECTED_FIRST512_CURRENT.bin').read_bytes()
    assert data==expected==bytes.fromhex(contract['data_hex'])
    assert hashlib.sha256(data).hexdigest()=='d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01'
    reply=bytes.fromhex(report['response_hex']);assert len(reply)==523 and reply[10:-1]==data
    assert reply[:10]==bytes.fromhex('beef0206830000000000') and reply[-1]==sum(reply[:-1])%256==0xe7
    writes=[r for r in trace['memory'] if r['mode']=='w']
    spans=manifest['private_ram_ranges']
    # The replay itself validates exact owned spans. Independently prohibit ROM,
    # kernel-image and flash-controller writes in every recorded event.
    assert all(int(r['address'],16)>=0xffff3710 for r in writes)
    assert all(not 0xffffe800<=int(r['address'],16)<0xffffe810 for r in writes)
    counts=collections.Counter(e['kind'] for e in trace['SCI_events'])
    assert counts['host_rx_enqueued']==1 and counts['rx_character_ready']==13 and counts['tx_character_complete']==523
    assert report['new_read_requests']==1 and report['upload_start_identity_instructions_reexecuted']==0
    assert report['physical_operations']==report['provider_loads']==report['flash_write_events']==0 and not report['kernel_mutation']
    out=A/'root_instruction_review';out.mkdir(exist_ok=False)
    result=dict(status='PASS_ROOT_INDEPENDENT_FIXED_READ_INSTRUCTION_REVIEW',reviewer='root',replay_author='passive_review',
        replay=ref['replay'],independent_fixed_contract=pin(A/'instruction_review/FIXED_READ_CONTRACT.json'),
        root_fixed_contract=pin(A/'ROOT_FIXED_READ_CONTRACT.json'),model_contract=pin(ROOT/'contract/CONTRACT.json'),
        audit_source=pin(Path(__file__)),verified_distinct_pins=len(seen),
        observed_instructions=10327,observed_sequential_ROM_byte_reads=512,range_start='00000000',range_end_exclusive='00000200',
        observed_read_requests=1,observed_reply_bytes=523,cursor_after='00000200',physical_operations=0,provider_loads=0,new_simulator_invocations=0,
        conclusions=['Independent source-derived contracts, simulated SCI response and each raw ROM load agree.',
          'Only the new read executes CPU instructions; the reviewed prior identity checkpoint supplies initial state.',
          'No second read, entry/identity execution, pass completion, kernel mutation or flash-controller store is present in the trace.'],
        limits=['Restored register/private-RAM state and SCI schedule are explicit simulation inputs; no silicon-timing or physical-ROM-read claim.'])
    with (out/'ROOT_INSTRUCTION_REVIEW.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'report':pin(out/'ROOT_INSTRUCTION_REVIEW.json')}))
if __name__=='__main__':main()
