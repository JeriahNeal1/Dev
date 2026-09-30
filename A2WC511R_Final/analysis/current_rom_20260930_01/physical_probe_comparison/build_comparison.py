"""Analyze preserved files only; no client, provider, test or vehicle invocation."""
from pathlib import Path
import datetime as dt
import hashlib,json

OUT=Path(__file__).resolve().parent
BASE=OUT.parent
OLD=BASE.parent/'rk02_vehicle_03_transition'
SESSION=Path(r'C:\Dev\A2WC511R_RK03_TransitionProbe\physical_session\RK03_TRANSITION_PROBE_01')
RK=Path(r'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_03')
def ref(p):
 p=Path(p);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
paths={
 'new_native':SESSION/'native_api.jsonl','new_execution':SESSION/'EXECUTION.json',
 'new_postexit':SESSION/'POSTEXIT_CLIENT_CHECK.json',
 'new_result':BASE/'physical_probe_result/PHYSICAL_RESULT.json',
 'current_log':BASE/'ecuflash_current_session/ecuflash_log_20260929t172612.preserved.txt',
 'current_evidence':BASE/'ecuflash_current_session/SESSION_EVIDENCE.json',
 'aug_log':BASE/'ecuflash_current_session/aug18_success.supplement.txt',
 'rk02_native':RK/'native_api.jsonl','rk02_readiness':RK/'G11_READINESS.json',
 'rk02_source':Path(r'C:\Dev\A2WC511R_ReadKernel\host\physical_build\rk02_physical_01\native_physical.cpp'),
 'dev_source':Path(r'C:\Dev\A2WC511R_RK03_TransitionDev\src\native_transition.cpp'),
 'dev_readme':Path(r'C:\Dev\A2WC511R_RK03_TransitionDev\README.md'),
 'static_json':OLD/'ecuflash_static_findings.json','static_md':OLD/'ecuflash_static_findings.md',
 'host_prefix':OLD/'historical_offline_host_trace_prefix.json',
 'prior_analysis':OLD/'RK02_VEHICLE_03_SESSION_TRANSITION_ANALYSIS.md',
 'rom_status':BASE/'CURRENT_ROM_STATUS.md','rom_status_json':BASE/'CURRENT_ROM_STATUS.json',
 'rk02_qualification':Path(r'C:\Dev\A2WC511R_ReadKernel\evidence\rk02\FINAL_QUALIFICATION.md'),
 'probe_contract':BASE/'PROBE_REVIEW_CONTRACT.json',
 'probe_core':Path(r'C:\Dev\A2WC511R_RK03_TransitionProbe\probe\src\probe_core.hpp'),
 'probe_pins':Path(r'C:\Dev\A2WC511R_RK03_TransitionProbe\probe\src\pins.hpp'),
 'owned_kernel':Path(r'C:\Dev\A2WC511R_ReadKernel\build\rk02_01\kernel.bin')}
gate_snapshot=OUT/'PROBE_GATE_STATE.snapshot.json'
if not gate_snapshot.exists():gate_snapshot.write_bytes((BASE/'PROBE_GATE_STATE.json').read_bytes())
paths['gate_snapshot']=gate_snapshot
sources={k:ref(p) for k,p in paths.items()}
rows=[]
for line,text in enumerate(paths['new_native'].read_text().splitlines(),1):
 r=json.loads(text);r['source_line']=line;rows.append(r)
returns=[r for r in rows if r.get('type')=='api_return']
intents=[r for r in rows if r.get('type')=='api_intent']
tx=[r for r in returns if r['function']=='PassThruWriteMsgs']
rx=[r for r in returns if r['function']=='PassThruReadMsgs']
rkrows=[json.loads(s) for s in paths['rk02_native'].read_text().splitlines()]
expected_tx=['8010f001bf40','8010f0018102','8010f002830005']
assert [r['input']['message']['data_hex'] for r in tx]==expected_tx
assert all(r['status']==0 for r in returns) and len(returns)==22
assert rows[-1]['status']=='PASS_TRANSITION_PROBE_ONLY' and rows[-1]['cleanup_confirmed']
assert read(paths['new_execution'])['exit_code']==0
frames=[r for r in rx if r['output']['message']['data_size']]
assert [r['output']['message']['data_hex'] for r in frames[1:]]==['80f01003c1ef8fc2','80f01007c30000ff00ff0048']
for r in frames:
 b=bytes.fromhex(r['output']['message']['data_hex']);assert len(b)==b[3]+5 and (sum(b[:-1])&255)==b[-1]
cfg=[{'parameter':22,'value':0},{'parameter':7,'value':1},{'parameter':10,'value':0},{'parameter':12,'value':0},{'parameter':3,'value':0}]
get=next(r for r in returns if r['function']=='PassThruIoctl' and r['input']['ioctl']==1)
assert get['output']['config']['owned_buffer_entries']==cfg
version=next(r for r in returns if r['function']=='PassThruReadVersion')
frequency=tx[0]['qpc_frequency']
ms=lambda ticks:round(ticks*1000/frequency,4)
timing={'probe_C1_return_to_83_entry_ms':ms(tx[2]['qpc_before']-frames[1]['qpc_after']),
 'probe_C1_return_to_83_return_ms':ms(tx[2]['qpc_after']-frames[1]['qpc_after']),
 'probe_83_call_duration_ms':ms(tx[2]['api_elapsed_ticks']),
 'probe_83_write_return_to_full_C3_return_ms':ms(frames[2]['qpc_after']-tx[2]['qpc_after']),
 'probe_83_entry_to_full_C3_return_ms':ms(frames[2]['qpc_after']-tx[2]['qpc_before']),
 'rk02_C1_return_to_83_return_ms':round((rkrows[9]['counter']-rkrows[8]['counter'])*1000/rkrows[9]['frequency'],4),
 'rk02_83_return_to_empty_read_return_ms':round((rkrows[10]['counter']-rkrows[9]['counter'])*1000/rkrows[9]['frequency'],4),
 'limits':'New QPC brackets actual API calls. RK02 has only post-call timestamps. These are host API intervals, not measured K-line symbol gaps; provider RX timestamps are preserved without inferring TX cadence.'}
events=[]
for r in returns:
 events.append({'source_line':r['source_line'],'sequence':r['sequence'],'function':r['function'],'status':r['status'],
  'input':r['input'],'output':r['output'],'qpc_before':r['qpc_before'],'qpc_after':r['qpc_after'],
  'qpc_frequency':r['qpc_frequency'],'api_elapsed_ms':ms(r['api_elapsed_ticks']),'utc_filetime':r['utc_filetime']})

matched_different_unknown=[
 {'field':'ECU identity','classification':'MATCHED_IDENTITY','probe':'Full BF reply contains2F12515306; native line27','rk02':'Same complete BF wire bytes','ecuflash_physical':'Current line90 and August line89 report2F12515306; fullBF wire bytes absent','sources':['new_native','rk02_native','current_log','aug_log']},
 {'field':'BF/81/83 requests','classification':'MATCHED_REQUESTS_WITH_PROVENANCE_LIMIT','probe':expected_tx,'rk02':expected_tx,'ecuflash_physical':None,'installed_host_offline':'Exactly same request bytes, archived seq51/53/55; actual installed host against fake provider','sources':['new_native','rk02_native','host_prefix']},
 {'field':'81 reply','classification':'MATCHED_PHYSICAL_PROBE_AND_RK02','probe':'80f01003c1ef8fc2','rk02':'80f01003c1ef8fc2','ecuflash_physical':None,'installed_host_offline':'Synthetic minimal C1 only; not a physical comparator','sources':['new_native','rk02_native','current_log','aug_log','host_prefix']},
 {'field':'83 outcome','classification':'NEW_PHYSICAL_SUCCESS_DIFFERENT_FROM_RK02','probe':'80f01007c30000ff00ff0048,12bytes,status0,count1,ExtraDataIndex12,line39','rk02':'ReadMsgs status16,count0,no message','ecuflash_physical':'Successful later seed/key and upload labels, but83request/reply itself unlogged','sources':['new_native','rk02_native','current_log','aug_log']},
 {'field':'Connect','classification':'MATCHED_REQUESTED_CONTRACT','probe':{'protocol':3,'flags':512,'baud':4800},'rk02':'Same parameters from pinned source; old journal omitted arguments','ecuflash_physical':None,'installed_host_offline':'protocol3,flags512,4800baud,seq36','sources':['new_native','rk02_source','host_prefix']},
 {'field':'Five serial settings','classification':'PROBE_MATCHES_INSTALLED_HOST_ARGUMENTS_BUT_DIFFERS_FROM_RK02','probe':cfg,'probe_effective':'All5 GET_CONFIG results match, native line19; status0 and owned pointer/count integrity','rk02':'No SET orGET; inherited defaults unknown','ecuflash_physical':None,'installed_host_offline':'Same five values,seq40–44; configuration stored in fake only','sources':['new_native','rk02_native','host_prefix','static_json']},
 {'field':'Receive filter','classification':'PROBE_MATCHES_INSTALLED_HOST_ARGUMENTS_BUT_DIFFERS_FROM_RK02','probe':'PASS_FILTER,type1,protocol3;4zero mask/pattern/nonnullflow; native line21','rk02':'FFFFFF mask,80F010 pattern,nullflow from pinned source','ecuflash_physical':None,'installed_host_offline':'Same4zero mask/pattern/nonnullflow,seq47','sources':['new_native','rk02_source','host_prefix']},
 {'field':'Provider version','classification':'PARTIAL_VERSION_MATCH_FULL_STRING_DIFFERS','probe':{k:version['output'][k]['value'] for k in ['firmware','dll','api']},'ecuflash_physical':{'firmware':'1.17.4877','dll':'1.02.4870 Feb  3 2017 23:36:31','api':'04.04'},'rk02':'ReadVersion not called','limit':'Numeric DLL version,firmware/API match; build-time suffix05vs31 differs. No session-time ECUFlash module path/hash was captured, so identical loaded-provider binary is not proved.','sources':['new_native','current_log','aug_log']},
 {'field':'Provider file identity','classification':'PROBE_PINNED_RK02_PIN_MATCH_ECUFLASH_SESSION_UNKNOWN','probe':{'path':rows[0]['provider_path'],'sha256':rows[0]['provider_sha256']},'rk02':'Earlier sealed analysis records same selected file hash f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf','ecuflash_physical':'Module path/hash absent; later installed-file hashes are not session-time module evidence','sources':['new_native','prior_analysis','current_evidence']},
 {'field':'Adapter serial','classification':'PROBE_UNKNOWN','probe':None,'ecuflash_physical':'TAPoN7at in current/August logs','limit':'Probe ReadVersion does not record adapter serial; user readiness says genuine OpenPort2.0. Do not infer serial from firmware version.','sources':['new_native','current_log','aug_log','gate_snapshot']},
 {'field':'Test Mode and voltage','classification':'PROBE_AND_RK02_HUMAN_EVIDENCE_CURRENT_ECUFLASH_UNKNOWN','probe':'FreshG06–G09 completed; user reported CEL/fuel pump cycling; ignitionON/engineOFF; charger10A; operator monitors voltage without numeric log','rk02':'G11 records Test Mode with CEL/pump cycling; fans intentionally disconnected','ecuflash_physical':None,'limit':'These human observations are session-specific. No numeric voltage or ECUFlash-session indication is invented.','sources':['gate_snapshot','rk02_readiness','current_evidence']},
 {'field':'Cleanup/exit','classification':'PROBE_EXPLICIT_SUCCESS_DIFFERS_FROM_RK02','probe':'StopMsgFilter/Disconnect/Close all0,lines41/43/45; exit0; postexit scan clean','rk02':'Terminal journal ends without cleanup calls; process exit alone is not cleanup proof','ecuflash_physical':'Application interface-close messages and later GUIexit; no raw cleanup API statuses','sources':['new_native','new_execution','new_postexit','rk02_native','current_evidence']},
 {'field':'Current executable instruction evidence','classification':'UPDATED_BY_CURRENT_ROM_ANALYSIS','result':'Authoritative acquired current.bin bf10be... has1856classified data changes, no changed executable instructions; all bytes outside identified data changes match stock. Earlier unacquired-ROM uncertainty is superseded by sealedA/A4analysis, not by the transition probe.','limit':'Calibration behavior differs; ECUFlash saved image is authoritative user input but not proof every byte was independently transferred.','sources':['rom_status','rom_status_json','current_evidence']}
]

remaining=[
 {'topic':'Scope and earlier discovery','ecuflash':'Full read path includes initial kernel-version/VIN probes and interface close/reopen activity. Current log77–89 records these labels.','probe':'One initial Open/ReadVersion/Connect then BF/81/83; ends immediately afterC3.','rk03_development':'Existing TransitionDev is fake-only through first36; no full physical RK03 acquisition implementation is qualified.','evidence':['current_log','new_native','dev_source']},
 {'topic':'Initial configuration verification and filter','ecuflash':'Archived initializer sets parity earlier and again with four timing/loopback settings; no matching5-itemGET in preserved prefix. Broad4zero filter.','probe':'One5-setting sequence plus immediate strictGET; same broad filter.','rk03_development':'Old TransitionDev adds fiveSET but retains narrow80F010/nullflow filter and has noGET. Successful probe setup cannot be silently assumed integrated into it.','evidence':['host_prefix','new_native','dev_source']},
 {'topic':'Queue clears','ecuflash':'Archived IOCTL7/8 pairs atseq38/39,45/46,49/50 and65/66(after15625).','probe':'No queue clear; this particular pre83 session succeeded without it.','rk03_development':'No queue clears. Later baud/session boundaries remain untested physically; do not infer clears always unnecessary.','evidence':['host_prefix','new_native','dev_source']},
 {'topic':'Pin9 voltageOFF','ecuflash':'Archived seq48 calls SetProgrammingVoltage(pin9,VOLTAGE_OFF=FFFFFFFF).','probe':'No programming-voltage API.','rk03_development':'No pin action. Archived OFF is not a requirement for positive voltage or authorization to alter pins.','evidence':['host_prefix','probe_core','dev_source']},
 {'topic':'Read/write timeouts','ecuflash':'Archived request/read pairs: BF400ms;812000ms;83500ms;seed/key500ms;1085022000ms;34/36 500ms.','probe':'Write1000ms and read slices<=1000ms within2000ms frame deadline; fatal nonzero status.','rk03_development':'Same1000ms slice/2000ms bound across stages. Full later-stage timeout equivalence is not established.','evidence':['host_prefix','static_json','probe_core','dev_source']},
 {'topic':'Strict response/metadata acceptance','ecuflash':'Selected wrappers accept positive serviceSID and do not use returnedC1/C3payload; lower read skips statusbits0E. Archived positives after83 are partly minimal synthetic fixtures.','probe':'Exact fullC1/C3 plus strict bounded framing/status/echo/metadata. Actual fullC3 now observed.','rk03_development':'Also expects full67 02 34,50 85,74 84 and76 later; those physical responses were not exercised by probe.','evidence':['static_json','host_prefix','probe_core','dev_source']},
 {'topic':'Security seed/key','ecuflash':'After83 invokes2701 and2702, with vendor application-service key transformation in archived trace. Successful physical logs contain labels, not seed/key bytes.','probe':'No security operation exists.','rk03_development':'Local key_for_seed transform and strict key acknowledgement; prior fake/offline validation is not this vehicle-session authorization or physical security validation.','evidence':['host_prefix','static_json','current_log','dev_source']},
 {'topic':'Post-key delay','ecuflash':'Explicit200ms delay in selected static callerRVA9B648–9B64D. Current key-label→firstupload618ms; August647ms are composite log intervals, not a direct200ms measurement.','probe':'Not reached.','rk03_development':'No corresponding delay in old TransitionDev/nativeRK02 sequence; retain as unresolved intentional difference for next review.','evidence':['static_json','static_md','current_evidence','dev_source']},
 {'topic':'108502 session and post-session delay','ecuflash':'Sends108502 with2000ms API timeout, then explicit100ms delay beforeDATA_RATE15625 (RVA9B69A–9B6C5).','probe':'Not sent; stays4800.','rk03_development':'Sends108502, expects5085, then immediately sets15625; no100msdelay. Neither later ECU state change nor baud transition is validated byC3 success.','evidence':['static_json','host_prefix','dev_source','new_native']},
 {'topic':'Pre-upload delay','ecuflash':'Selected upload routine9C0F0 adds200ms before download declaration.','probe':'No upload.','rk03_development':'No explicit200ms delay before34. No timing change is proposed by this comparison.','evidence':['static_json','static_md','dev_source']},
 {'topic':'Duplicate34 declaration and retry policy','ecuflash':'Static calls9C154/9C164 and archivedseq67/69 send the same34twice after firstpositive reply. This is an observed duplicate declaration, not evidence of retrying ERR_BUFFER_EMPTY. Selected lower read fails nonzero API status.','probe':'Only one eachBF/81/83; no retry; terminal success or failure.','rk03_development':'One34 and noautomaticretry. Adding duplicates or retries would require separate rationale and qualification.','evidence':['host_prefix','static_json','dev_source','probe_core']},
 {'topic':'Kernel bytes,size and transfer','ecuflash':'DUAL1.07 atFFFF3000,size0x1234=4660,37RAMblocks; first36 has128data bytes. Current andAugust upload address/length sequences match.','probe':'No kernel bytes,34or36.','rk03_development':'OwnedRK02 kernel0x710=1808bytes, SHA3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581; distinct ciphertext and declaration. Existing fakeTransitionDev stops after first128-byte36 ACK.','evidence':['current_evidence','host_prefix','owned_kernel','dev_source','rk02_qualification']},
 {'topic':'Kernel start and kernel transport','ecuflash':'Successful physical log obtains DUAL1.07 kernel version and buffer sizes; actual raw later API sequence not in physical application log.','probe':'No31,start,baud transition or kernel protocol.','rk03_development':'FrozenRK02 source plans310101, then62500 andBEEF filter/version protocol; fakeTransitionDev does not reach this scope. Native integration/failure cleanup must be separately reviewed.','evidence':['current_log','rk02_source','dev_source']},
 {'topic':'ROM acquisition and finalization','ecuflash':'Current app log explicitly lists1200read blocks/614400bytes, then writes1MiB; a saved1MiB image does not prove all bytes crossedthebus. Existing exactness analysis rejects genericCRC-based substitution for universal exact capture.','probe':'No ROM bytes acquired and no finalizer.','rk03_development':'FrozenRK02 design uses two complete1MiB exact512-byte reads with equality, then qualified finalization and separate human restart/OEM check; not exercised or qualified by transitionPASS.','evidence':['current_evidence','rk02_source','rk02_qualification','dev_source']},
 {'topic':'Cleanup and evidence instrumentation','ecuflash':'Physical app log has lifecycle labels; archived fakehost records API calls. No matchingphysicalentry/returnQPCtranscript.','probe':'Fulltimedentry/return evidence, returnedconfig/filter guards and ordered cleanup on every allocated exit, allsuccessful here.','rk03_development':'Old fakeTransitionDev has simplerlogging and no physical cleanup/fullacquisitionqualification; future integration must preserve probe cleanup/evidence guarantees.','evidence':['new_native','probe_core','current_evidence','dev_readme','dev_source']},
 {'topic':'Provider/version identity','ecuflash':'RuntimeDLLbuildtimesuffix23:36:31; no session-loadedmodulehash.','probe':'PinnedSysWOW64DLLf432...; runtimeDLLsuffix23:36:05.','rk03_development':'Do not equate the runtime libraries solely because numeric1.02.4870 matches, nor change provider selection to chase the string. Exact cause of suffixdifference remains unestablished.','evidence':['new_native','current_log','aug_log','current_evidence']}
]

host=read(paths['host_prefix'])
host_events=[]
for e in host['ordered_api_events']:
 if e['sequence']>=36:
  req=e['request'];host_events.append({'source_line':e['source_line'],'sequence':e['sequence'],'function':e['function'],'request':req,'response_status':e['response'].get('status'),'evidence_class':'INSTALLED_HOST_OFFLINE_FAKE_PROVIDER_CAPTURE','physical':False})
data={'schema':1,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
 'status':'PHYSICAL_TRANSITION_SUCCESS_SUPPLEMENT_ONLY',
 'scope':'READ_ONLY_COMPARISON_NO_NEW_PROVIDER_TEST_BUILD_EXECUTABLE_OR_VEHICLE_OPERATION',
 'new_probe_result':'PASS_TRANSITION_PROBE_ONLY','physical_invocations_in_preserved_probe':1,
 'full_acquisition_qualified':False,'isolated_physical_cause_identified':False,
 'sources':sources,'new_physical_api_events':events,'new_terminal':rows[-1],
 'new_execution':read(paths['new_execution']),'new_postexit_client_check':read(paths['new_postexit']),
 'actual_C3':{'wire_hex':frames[2]['output']['message']['data_hex'],'payload_hex':'c30000ff00ff00','total_bytes':12,'declared_payload_bytes':7,'checksum_hex':'48','checksum_valid':True,'status':0,'count':1,'source_line':39,'message_metadata':frames[2]['output']['message']},
 'timing':timing,'matched_different_unknown':matched_different_unknown,
 'remaining_intentional_or_unresolved_path_differences':remaining,
 'installed_host_offline_prefix_extract':host_events,
 'causal_interpretation':'The physically observed result changed from RK02 status16 to a fullC3 under an explicitly configured,GET-verified,broad-filtered,instrumented probe. Five settings,filter,verification/logging and session context differ together; priordefaults,waveforms and ECUFlashphysicalraw83 are missing. No singlesetting or filter is isolated as the cause.',
 'recovery_boundary':'Human recovery and later passive OEM-return are separately controlled by root. APIcleanup/process exit and thiscomparison do not establish power-loss/reset/OEM-return or physicalsessioncompletion.',
 'historical_snapshot_note':'Earlier sealed reports remain unchanged. Their statements that currentROMwasunacquired or probeNOTRUN describe earlier milestones; currentROManalysis and thisnewphysicalevidence are supplements.',
 'source_integrity_verified_at_generation':True}
for k,p in paths.items():assert ref(p)==sources[k]
json_path=OUT/'PHYSICAL_TRANSITION_COMPARISON.json'
json_path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

md=f'''# Physical transition comparison

The one authorized `RK03_TRANSITION_PROBE_01` completed **BF → 81 → 83** and returned the full expected C3 response. It exited with code 0, and StopMsgFilter, Disconnect and Close each returned 0. This validates the limited transition in this session; it does not qualify security access, kernel upload or full acquisition, and it does not isolate one cause of the earlier failure.

## New direct evidence

The physical journal SHA256 is `{sources['new_native']['sha256']}`. It contains exactly three transmissions and 22 successful API calls. BF reports ECU `2F12515306`; the complete BF and C1 reply bytes match the failed RK02 session. Native line 39 records:

```text
TX: 80 10 F0 02 83 00 05
RX: 80 F0 10 07 C3 00 00 FF 00 FF 00 48
```

The reply has 12 total bytes, seven payload bytes, valid checksum `48`, status 0, count 1 and ExtraDataIndex 12. An empty START_OF_MESSAGE record precedes each complete BF, C1 and C3 reply. This is actual physical C3 evidence; the prior stock replay predicted the same bytes, while the archived fake ECUFlash trace supplied only a synthetic minimal C3.

Native line 19 records a successful provider GET_CONFIG returning all five requested values: PARITY 0, P1_MAX 1, P3_MIN 0, P4_MIN 0 and LOOPBACK 0. The list count, owned pointer and guards pass. Line 21 records the broad PASS_FILTER with protocol 3 and four zero bytes in mask, pattern and a nonnull flow object. Connection is protocol 3 / flags 512 / 4800 baud throughout the probe. Cleanup returns are lines 41, 43 and 45; the post-exit scan reports no conflicting client or provider-module user.

Fresh G06–G09 records support this probe's Test Mode state; G09 reports CEL and fuel-pump cycling. The preserved gate snapshot distinguishes those user observations from the current ECUFlash read, whose actual Test Mode indications were not logged. No numerical voltage is inferred. Recovery and the later passive OEM-return remain separate evidence owned by root.

## What matches, differs or remains unknown

| Field | Successful probe | Failed RK02 | Current / August successful ECUFlash |
|---|---|---|---|
| Identity | Full BF: 2F12515306 | Identical full BF | Same ID label; raw BF absent |
| Requests | Exact fixed BF, 81, 83 00 | Same three bytestrings | Same requests proven in installed-host **offline** trace; physical logs omit them |
| 81 | Full C1 EF 8F | Identical reply | Raw reply absent; static caller checks positive SID |
| 83 | Full C3 00 00 FF 00 FF 00 | Status 16 / count 0 | Later seed/key/upload succeed; raw 83 reply absent |
| Initial settings | Five SET calls and verified GET | No SET/GET; defaults unknown | Same SET values in static/offline host evidence; actual physical settings unlogged |
| Filter | Broad four-zero mask/pattern/nonnull flow | Narrow FFFFFF / 80F010 / null flow | Broad filter matches installed-host offline arguments |
| API / firmware | 04.04 / 1.17.4877 | No ReadVersion record | Same numeric versions |
| Full DLL string | `1.02.4870 Feb  3 2017 23:36:05` | Pinned provider file, no runtime string | `1.02.4870 Feb  3 2017 23:36:31` |
| Adapter serial | Not queried by this probe | Not established by its journal | TAPoN7at logged |
| Cleanup | Three explicit API successes, exit 0 | Cleanup absent from terminal journal | Application close labels; raw API statuses absent |

The DLL build-time suffix difference is preserved, not normalized away. The probe pins `C:\\Windows\\SysWOW64\\op20pt32.dll` to SHA256 `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`, also identified for RK02 in the earlier sealed analysis. Present installed files do not establish which module was loaded in the completed ECUFlash session. Numeric DLL-version equality is insufficient to assert identical session-time libraries. No provider change is proposed here.

The current ECUFlash session remains the primary full-read comparator; August is supplemental. Both log the same 37-block DUAL 1.07 upload sequence and 1,200 explicit read blocks, followed by a 1 MiB save. Current `current.bin` is strongly associated by exact save path, size and timestamp and is the authoritative acquired-image input. Sealed classification accounts for all 1,856 changed bytes as data, with no changed instructions; this supersedes the earlier analysis's unacquired-ROM uncertainty. It does not equate calibration behavior with stock or prove that every saved byte crossed the bus.

## Timing and causality limits

The new C1 API return → 83 API entry interval is **{timing['probe_C1_return_to_83_entry_ms']} ms**; 83 call duration is **{timing['probe_83_call_duration_ms']} ms**; 83 write return → full C3 read return is **{timing['probe_83_write_return_to_full_C3_return_ms']} ms**. For the directly comparable return-to-return measurement, new C1 return → 83 write return is **{timing['probe_C1_return_to_83_return_ms']} ms**, versus **{timing['rk02_C1_return_to_83_return_ms']} ms** in RK02. RK02's subsequent empty-read return took **{timing['rk02_83_return_to_empty_read_return_ms']} ms** after its write return.

These are host API intervals. RK02 lacked entry timestamps; no K-line waveform establishes exact interbyte cadence. The successful probe changed five settings, receive filter, configuration verification, logging and session context together. It does not identify which change mattered, nor show that increasing timeouts, adding retries or adding delays is required. Both the reviewed ECUFlash read wrapper and the probe treat a nonzero provider result as failure.

## Remaining path differences

The existing `A2WC511R_RK03_TransitionDev` executable is a separate fake-only development host ending at the first 36 acknowledgement. It is not a full physical RK03 acquisition tool. Its setup still needs explicit reconciliation with the successful probe's GET verification, broad filter and cleanup guarantees. The following differences remain intentional or unresolved; recording them is not a proposal to copy them blindly.

| Area | Reviewed ECUFlash behavior | Probe / existing development boundary |
|---|---|---|
| Discovery and initial setup | Earlier kernel/VIN probes, close/reopen sequence, repeated parity SET | Probe uses one fresh connection; old development retains narrow filter and lacks GET |
| Queue clears | IOCTL 7/8 pairs before BF and after baud change | None in probe or old development; one successful pre-83 run does not validate later queue boundaries |
| Pin 9 | Archived `VOLTAGE_OFF` call | None; no positive voltage requirement inferred |
| API timeouts | BF 400, 81 2000, 83/security 500, 108502 2000, 34/36 500 ms | Write 1000; reads ≤1000 within a 2000 ms frame bound |
| Reply policy | Generic positive-SID checks; physical later payloads absent | Exact full replies and strict metadata; later 67 02 34, 50 85 and 74 84 remain untested physically |
| Seed/key | 27 01 / 27 02 with vendor application-service transform | Probe has none; old development uses local `key_for_seed` |
| After key | Explicit **200 ms** delay | Absent from old development; probe never reaches it |
| 10 85 02 | Session request, then explicit **100 ms** before 15625 baud | Probe stays 4800; old development changes to 15625 immediately after acknowledgement |
| Before upload | Explicit **200 ms** delay | Absent from old development |
| Download declaration | Two identical 34 calls, both acknowledged in archived fake trace | One 34 in old development; duplication is not evidence of retrying status 16 |
| Kernel | DUAL 1.07, 0x1234 / 4,660 bytes at FFFF3000 | Owned RK02 kernel, 0x710 / 1,808 bytes, different content/ciphertext; no probe upload |
| Start / kernel transport | Physical application log reports DUAL version and buffer sizes | Frozen RK02 plans 31 01 01, then 62500 / BEEF; neither probe nor first-36 development validates this physically |
| ROM exactness | Explicit logged reads total 614,400 bytes, then 1 MiB saved; generic CRC substitution is not universally exact | Frozen RK02 design requires two complete equal 1 MiB reads without synthesized pages; no probe ROM reads |
| Error recovery | Physical logs show lifecycle labels, not complete API status evidence | Probe has explicit fail-closed cleanup; full acquisition integration and finalizer remain separate qualification work |

The static delay sites are RVA 9B648–9B64D (post-key), 9B69A–9B6C5 (post-session), and selected upload routine 9C0F0 (pre-upload). Duplicate 34 calls are 9C154 and 9C164, corroborated by offline API sequences 67 and 69. Current key-label → first-upload interval is 618 ms and August's is 647 ms; these composite application timestamps do not measure an individual delay. The separate kernel hash is `{sources['owned_kernel']['sha256']}`.

## Evidence preservation

`PHYSICAL_TRANSITION_COMPARISON.json` pins every input and retains all 22 physical API returns with arguments, outputs, source lines and timing, the exact C3 record, the comparison matrix, and 16 remaining-difference records. The preserved installed-host API extract is explicitly labelled offline/fake; its replies are not promoted to physical evidence. `PROBE_GATE_STATE.snapshot.json` preserves a point-in-time copy of root's evolving gate record. Existing sealed reports, binaries, logs and ROM files were not changed. No client, provider, test, build or vehicle operation was invoked for this comparison.
'''
(OUT/'PHYSICAL_TRANSITION_COMPARISON.md').write_text(md,encoding='utf-8')
manifest={'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'inputs':sources,
 'outputs':[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='COMPARISON_MANIFEST.json']}
(OUT/'COMPARISON_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'json':ref(json_path),'markdown':ref(OUT/'PHYSICAL_TRANSITION_COMPARISON.md'),
 'manifest':ref(OUT/'COMPARISON_MANIFEST.json'),'timing':timing,'api_calls':len(returns),'remaining_differences':len(remaining)},indent=2))
