"""Read-only protocol/evidence comparison; writes only new offline analysis reports."""
from pathlib import Path
import json,hashlib,datetime
A=Path(__file__).resolve().parent
S=Path(r'C:\Dev\A2WC511R_RK03_BoundedReadPhysical\physical_session\RK03_BOUNDED_ROM_READ_01')
P=Path(r'C:\Dev\A2WC511R_RK03_KernelIdentityPhysical\physical_session\RK03_KERNEL_START_IDENTITY_01\native_api.jsonl')
O=Path(r'C:\Dev\A2WC511R_RK03_BoundedRomReadOffline\bounded_rom_read\contract\CONTRACT.json')
H=Path(r'C:\Dev\A2WC511R_RK03_BoundedReadPhysical\bounded_read_physical\src\j2534_tactrix.h')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def pin(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,o):
 with p.open('x',encoding='utf8') as f:json.dump(o,f,indent=2);f.write('\n')
def callrows(r):return [x for x in r if x.get('type')=='api_return']
r=rows(S/'native_api.jsonl');calls=callrows(r);prior=callrows(rows(P));oracle=read(O);contract=read(A/'PHYSICAL_BOUNDED_REVIEW_CONTRACT.json')
tx=[x for x in calls if x['function']=='PassThruWriteMsgs'];oldtx=[x for x in prior if x['function']=='PassThruWriteMsgs']
assert len(tx)==25 and len(oldtx)==24 and tx[-1]['input']['message']['data_hex']==contract['bounded_read']['request']
assert tx[-1]['status']==0 and tx[-1]['output']['count']==1
assert all(t['input']['message']['data_hex']==oldtx[i]['input']['message']['data_hex'] for i,t in enumerate(tx[:24]) if i!=4)
rx=[x for x in calls if x['function']=='PassThruReadMsgs' and x['sequence']>tx[-1]['sequence']]
assert [x['sequence'] for x in rx]==[92,93,94] and [x['status'] for x in rx]==[0,0,16] and [x['output']['count'] for x in rx]==[1,1,0]
actual=bytes.fromhex(rx[1]['output']['message']['data_hex']);expected=bytes.fromhex(contract['bounded_read']['response'])
assert len(actual)==228 and len(expected)==523 and actual[:227]==expected[:227] and actual[227]==0xf8 and expected[227]==0x28
assert actual[:10]==bytes.fromhex('beef0206830000000000') and actual[10:227]==Path(r'C:\Dev\SubaruRoms\current.bin').read_bytes()[:217]
assert r[-1]['cleanup_confirmed'] and not r[-1]['cleanup_error_mask'] and r[-1]['state']['identity_validated'] and not r[-1]['state']['bounded_validated']
assert [x['function'] for x in calls[-3:]]==['PassThruStopMsgFilter','PassThruDisconnect','PassThruClose'] and all(x['status']==0 for x in calls[-3:])
assert '#define ERR_BUFFER_EMPTY' in H.read_text() and '0x10' in next(l for l in H.read_text().splitlines() if l.startswith('#define ERR_BUFFER_EMPTY'))
def ms(x):return x['api_elapsed_ticks']*1000/x['qpc_frequency']
identity_rx=next(x for x in calls if x['sequence']==90)
def config(cs):
 return [dict(ioctl=x['input']['ioctl'],requested=x['input'].get('config',{}).get('owned_buffer_entries'),effective=x['output'].get('config',{}).get('owned_buffer_entries')) for x in cs if x['function']=='PassThruIoctl']
assert config(calls)==config(prior)
out=A/'failure_analysis';out.mkdir(exist_ok=True)
for name,b in [('RECEIVED_INCOMPLETE_FRAME.bin',actual),('UNVALIDATED_CANDIDATE_PAYLOAD_PREFIX.bin',actual[10:]),('EXPECTED_COMPLETE_FRAME.bin',expected)]:
 with (out/name).open('xb') as f:f.write(b)
record=dict(schema=1,status='CONFIRMED_TERMINAL_INCOMPLETE_RESPONSE_CAUSE_UNRESOLVED',session_id='RK03_BOUNDED_ROM_READ_01',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),physical_invocations=1,retry_allowed=False,final_full_acquisition_qualified=False,
 last_common_event=dict(function='PassThruReadMsgs',sequence=90,meaning='Complete fixed identity reply',bytes=identity_rx['output']['message']['data_hex']),
 first_divergence=dict(physical_sequence=93,kind='INCOMPLETE_FRAME_AND_MISMATCHING_LAST_RECEIVED_BYTE',first_mismatching_frame_offset=227,candidate_payload_offset=217,candidate_ROM_address='000000D9',expected_byte='28',observed_byte='F8',expected_frame_bytes=523,received_frame_bytes=228,absent_frame_bytes=295,matching_payload_prefix_bytes=217,remaining_ROM_payload_bytes_not_received=294,complete_response_checksum='NOT_AVAILABLE',observed_trailing_byte_is_checksum_of_received_prefix=False,checksum_of_received_prefix_without_last='39'),
 historical_successful_event=dict(identity_session=pin(P),extent='Previously successful physical upload/start/identity ends before a ROM read; no successful physical RK03 bounded reply exists.'),
 expected_offline_event=dict(contract=pin(O),request_hex=oracle['frames'][24]['tx'],response_hex=oracle['frames'][24]['rx'],expected_payload_sha256=contract['bounded_read']['payload_sha256']),
 RK03_event=dict(request=tx[-1],received_status_records=rx,terminal=r[-1]),
 timing_delta=dict(identity_reply_to_read_call_ms=(tx[-1]['qpc_before']-identity_rx['qpc_after'])*1000/tx[-1]['qpc_frequency'],read_write_call_ms=ms(tx[-1]),SOM_call_ms=ms(rx[0]),data_call_ms=ms(rx[1]),empty_call_ms=ms(rx[2]),read_write_return_to_data_return_ms=(rx[1]['qpc_after']-tx[-1]['qpc_after'])*1000/tx[-1]['qpc_frequency'],physical_versus_model_delta=None,model_delta_reason='Offline virtual/instruction timing is not a physical latency comparator.'),
 configuration_delta=dict(compared_to_successful_identity='NONE_IN_RECORDED_IOCTL_VALUES',configuration=config(calls),read_state=tx[-1]['state']),
 J2534_status=dict(decimal=16,hex='0x10',name='ERR_BUFFER_EMPTY',source=pin(H),count=0,distinct_timeout_code=9),
 evidence=[pin(S/'native_api.jsonl'),pin(S/'EXECUTION.json'),pin(A/'physical_result/PHYSICAL_RESULT.json'),pin(A/'qualification/QUALIFICATION.json'),pin(P),pin(O),pin(r'C:\Dev\SubaruRoms\current.bin'),pin(r'C:\Dev\A2WC511R_ReadKernel\src\kernel.S')],
 returned_complete_payload_sha256=None,expected_payload_sha256=contract['bounded_read']['payload_sha256'],incomplete_frame_sha256=hashlib.sha256(actual).hexdigest(),unvalidated_candidate_payload_bytes=218,unvalidated_candidate_payload_sha256=hashlib.sha256(actual[10:]).hexdigest(),extracted_artifacts=[pin(out/n) for n in ['RECEIVED_INCOMPLETE_FRAME.bin','UNVALIDATED_CANDIDATE_PAYLOAD_PREFIX.bin','EXPECTED_COMPLETE_FRAME.bin']],
 confidence=dict(wire_API_observation='HIGH',all_prefix_stages_passed='HIGH',software_or_electrical_root_cause='UNRESOLVED'),
 conclusions=['Correct fixed read reached a BEEF response with the expected read header and217matching ROM bytes.','The received228-byte frame is incomplete and has a differing final candidate data byte; it is not a valid512-byte capture.','Status16 with count0 is buffer-empty; it does not prove that the ECU never replied.','Host remained fail-closed and sent no second read; all resources closed.','No justification exists to qualify the final two-pass physical release or increase timeouts.'],
 remaining_hypotheses=['Actual ECU SCI transmission stops or is interrupted (fatal/exception/reset or peripheral behavior); not established from API logs.','Electrical K-line corruption or timing interruption.','Provider framing/buffering or filter handling of a longer response; API transcript alone cannot distinguish bus traffic.'],
 downgraded_hypotheses=['Current OEM executable-code modification: prior current.bin classification found executable bytes identical to stock; this failure occurs in the uploaded fixed kernel path.','A deterministic range/length/checksum request error: transmitted request exactly matches the sealed reviewed frame.'],
 next_minimum_measurement='A separately authorized instrumented capture of K-line TX at the ECU and adapter for this same fixed exchange, correlated with host QPC; determine whether all523 response bytes exist electrically. If TX cuts off at the ECU, correlate reset/NMI/watchdog/SCI state using suitable hardware instrumentation. No further software-guess physical run is authorized here.')
save(out/'EVENT_DIFF.json',record)
text=f'''# RK03 bounded physical read: terminal failure

RK03_BOUNDED_ROM_READ_PHYSICAL = FAIL. One invocation; no retry. All15 upload acknowledgements, the fixed start and exact kernel identity passed. One correct bounded request was transmitted: `beef00080300000000000200ba`. Cleanup passed.

The ECU/provider returned an empty start-of-message record, then228 bytes beginning with the correct `BEEF0206830000000000` header. The first227 frame bytes match the expected reply: header10 plus217 payload bytes. At frame offset227 (candidate ROM address000000D9), expected28 becameF8. The remaining295 expected frame bytes were not delivered. The finalF8 is not a valid checksum of the preceding bytes (that sum is39).

The next PassThruReadMsgs returned decimal16, count0, after{ms(rx[2]):.4f}ms. The pinned Tactrix header defines16 as ERR_BUFFER_EMPTY; ERR_TIMEOUT is9. This is an incomplete/corrupt response, not an absence of all ECU response.

No complete returned512-byte hash exists. Expected payload SHA256: `{record['expected_payload_sha256']}`. Incomplete228-byte frame SHA256: `{record['incomplete_frame_sha256']}`. Extracted218-byte candidate payload is explicitly unvalidated; only its first217 bytes match current.bin.

The recorded serial configuration, baud transitions and queue clears match the successful physical identity session. The previous physical identity session does not supply a successful physical ROM-read comparator. The sealed instruction/fake model supplies the expected523 bytes but cannot establish silicon or K-line timing.

The fixed source contains no217-byte stop boundary: its read loop is512 bytes. Fatal/exception paths disable SCI, but this log does not establish that either path ran. An ECU transmission interruption, electrical fault, or provider/filter handling remains unresolved. Current OEM executable modification is downgraded by the established stock-identical executable comparison; that does not prove execution/timing of the uploaded kernel on silicon.

The final two-pass release is NOT qualified. Do not retry, extend timeouts, change baud settings, or execute another read on the vehicle in this run. Minimum useful next evidence is a separately authorized physical K-line waveform capture at ECU and adapter, correlated with this host exchange. It should distinguish an incomplete electrical transmission from a complete reply lost by the provider; if transmission stops at the ECU, investigate reset/NMI/watchdog/SCI behavior with appropriate instrumentation.

Exact API arguments, message/status records, durations, comparison bytes and hashes are in EVENT_DIFF.json. Raw sealed physical evidence is unchanged. Recovery OEM status is reported separately.
'''
with (out/'BOUNDED_READ_FIRST_DIVERGENCE.md').open('x',encoding='utf8') as f:f.write(text)
print(json.dumps(dict(status=record['status'],report=pin(out/'BOUNDED_READ_FIRST_DIVERGENCE.md'),event_diff=pin(out/'EVENT_DIFF.json'))))
