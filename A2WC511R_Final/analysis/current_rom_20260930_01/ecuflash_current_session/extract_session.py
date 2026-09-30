"""Read existing session evidence; write analysis only in this directory."""
from pathlib import Path
import datetime as dt
import hashlib,json,re,shutil

OUT=Path(__file__).resolve().parent
BASE=OUT.parent
CURRENT=OUT/'ecuflash_log_20260929t172612.preserved.txt'
AUG=Path(r'C:\Dev\A2WC511R_ReadKernel\preservation\snapshot_20260927\roaming_OpenECU\EcuFlash\logs\ecuflash_log_20260818t120321.txt')
RK=Path(r'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_03')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
for src,name in [(AUG,'aug18_success.supplement.txt'),(RK/'native_api.jsonl','RK02_VEHICLE_03_native_api.supplement.jsonl'),(RK/'G11_READINESS.json','RK02_VEHICLE_03_G11_READINESS.supplement.json')]:
    dest=OUT/name
    if dest.exists():assert sha(dest)==sha(src)
    else:shutil.copy2(src,dest)

def events(p,date):
    result=[]
    for i,line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
        m=re.match(r'^\[(\d\d:\d\d:\d\d\.\d+)\] (.*)$',line)
        utc=None
        if m:utc=dt.datetime.fromisoformat(date+'T'+m[1]+'-07:00').astimezone(dt.timezone.utc).isoformat()
        result.append({'line':i,'local_timestamp':m[1] if m else None,'utc_timestamp':utc,'text':m[2] if m else line})
    return result
def matching(rows,pattern):return [e for e in rows if re.search(pattern,e['text'])]
def ranges(rows,pattern):
    blocks=[]
    for e in rows:
        m=re.search(pattern,e['text'])
        if m:blocks.append(dict(e,address=int(m[1],16),length=int(m[2],16)))
    spans=[]
    for b in blocks:
        if spans and spans[-1]['end_exclusive']==b['address']:
            spans[-1]['end_exclusive']+=b['length'];spans[-1]['last_line']=b['line']
        else:spans.append({'start':b['address'],'end_exclusive':b['address']+b['length'],'first_line':b['line'],'last_line':b['line']})
    return {'count':len(blocks),'sum_logged_bytes':sum(b['length'] for b in blocks),'spans':spans,'events':blocks}
def summary(p,date):
    rows=events(p,date)
    important=matching(rows,r'Version|Device Serial|using metadata XML ID (read_sti05|A2WC511R)|SSM2 init|ECU ID|Requesting Seed|Sending Key|writing kernel area|kernel get version|kernel version is|comm buffer|flash buffer|dumping ECU|interface close|saving rom|image written|VIN read')
    ram=ranges(rows,r'SSM2 write kernel ram block addr: ([0-9A-F]+) len: ([0-9A-F]+)')
    read=ranges(rows,r'kernel read area: addr: ([0-9A-F]+) len: ([0-9A-F]+)')
    seed=matching(rows,'Requesting Seed')[0];key=matching(rows,'Sending Key')[0];identity=matching(rows,'ECU ID')[0]
    first=ram['events'][0];last=ram['events'][-1]
    delta=lambda a,b:round((dt.datetime.fromisoformat(b['utc_timestamp'])-dt.datetime.fromisoformat(a['utc_timestamp'])).total_seconds()*1000,3)
    return {'source':ref(p),'evidence_class':'PHYSICAL_SESSION_APPLICATION_LOG_NOT_RAW_WIRE_OR_API_CAPTURE','date_local':date,'timezone_interpretation':'America/Los_Angeles UTC-07 on recorded date','line_count':len(rows),'important_events':important,'ram_upload':ram,'logged_read_areas':read,'label_timing_ms':{'identity_to_request_seed':delta(identity,seed),'request_seed_to_sending_key':delta(seed,key),'sending_key_to_first_ram_block':delta(key,first),'first_to_last_ram_block':delta(first,last)},'raw_BF_request':None,'raw_BF_reply':None,'raw_81_request':None,'raw_81_reply':None,'raw_83_request':None,'raw_83_reply':None,'seed_bytes':None,'key_bytes':None,'connect_flags_baud_config_filter_ioctl':None,'test_mode_observation':None,'numeric_voltage':None,'unknown_reason':'Application log does not contain these details; installed-host fake/static evidence is not substituted for this physical session.'}
cur=summary(CURRENT,'2026-09-29');aug=summary(AUG,'2026-08-18')
rkrows=[json.loads(x) for x in (RK/'native_api.jsonl').read_text().splitlines()]
current_bin=Path(r'C:\Dev\SubaruRoms\current.bin')
assert sha(current_bin)=='bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2'
assert sha(current_bin)==sha(BASE/'current.preserved.bin')
assert sha(CURRENT)=='9fecae4b465edfbe6d7ad9b75ff8cfb39101dac67efd655dcbf151d50ad73f30'
saveevents=matching(events(CURRENT,'2026-09-29'),'saving rom|image written')
installed=[ref(Path(p)) for p in [r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe',r'C:\Windows\SysWOW64\op20pt32.dll']]
data={'schema':1,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'EXISTING_CURRENT_PHYSICAL_ECUFLASH_READ_EVIDENCE_PRESERVATION_AND_OFFLINE_COMPARISON','new_vehicle_operations':0,'ecuflash_close':{'method':'Normal Process.CloseMainWindow / WM_CLOSE after PrintWindow showed idle completed read/save','pid':22004,'initial_observed_log_bytes':0,'before_close_log_bytes':79435,'after_log_bytes':79435,'preclose_copy':ref(OUT/'log_copy_before_close.txt'),'flush_causation':'Unknown: initial directory metadata reported0bytes; before_close.json and the pre-close copy already had79435bytes before normal close. Do not credit closing with causing the flush.','process_exit_observed':True,'source':'before_close.json, normal_close_request.json, after_close.json','no_session_button_or_forced_termination':True},'current_session':cur,'saved_image_association':{'source_image':ref(current_bin),'preserved_image':ref(BASE/'current.preserved.bin'),'save_events':saveevents,'file_metadata':json.loads((BASE/'INGEST_MANIFEST.json').read_text(encoding='utf-8-sig')),'association':'Strong same-session application evidence: GUI title current.bin; exact log save path and1048576byte size; log17:29:13.123 local matches file00:29:13.1231299Z; source/preserved SHA agree. Log itself contains no content hash.','byte_exact_physical_capture_proven':False,'byte_exact_limit':'1MiB saved image does not prove every byte was transmitted; explicit logged read regions are partial and no raw bus capture exists.'},'current_installed_files':{'captured_after_session':installed,'registry_read_only_snapshot':{'key':r'HKLM\SOFTWARE\WOW6432Node\PassThruSupport.04.04\Tactrix Inc. - OpenPort 2.0 J2534 ISO/CAN/VPW/PWM','FunctionLibrary':r'C:\WINDOWS\SysWOW64\op20pt32.dll'},'binding_limit':'These are present installed file hashes and registry selection, not a module-memory hash captured during the successful read. The log records API04.04/DLL1.02.4870/firmware1.17.4877/serialTAPoN7at. PE file resources separately report exe1.44.0.4868 andDLL1.02.0.4868; do not conflate with runtime log versions.'},'test_mode_provenance':{'current_success':None,'why':"No current-success log entry or fresh timestamped human indication was supplied for this exact ECUFlash read. Latest desired probe state is not a historical observation. RK02 G09 belongs only to RK02_VEHICLE_03.",'rk02_03':json.loads((RK/'G11_READINESS.json').read_text())['test_mode_state'],'rk02_source':ref(RK/'G11_READINESS.json')},'rk02_failed_session':{'source':ref(RK/'native_api.jsonl'),'events':rkrows,'last_successful_reply':'80f01003c1ef8fc2','last_request':'8010f002830005','terminal_status':16,'terminal_status_name':'ERR_BUFFER_EMPTY','seed_key_upload_ROM_read_reached':False,'raw_reads_vs_new_success':'New successful ECUFlash log has no raw81/83 bytes or API outcomes for a like-for-like wire comparison.'},'august_success_supplement':aug,'comparison_conclusions':['Current and August success logs report ECU2F12515306, ECUFlash1.44.4870, API04.04, DLL1.02.4870, firmware1.17.4877, serialTAPoN7at, read_sti05 and DUAL1.07.','Both successful logs proceed from identity through seed/key labels, FFFF3000/1234 kernel upload, memory dump and1MiB save; RK02_03 ends at83 with status16 before seed/key.','Current and August application-log read address/length sequences and kernel-upload address/length sequences are compared explicitly below; timestamps are application labels, not byte timing.','The newest success establishes that this ECU/adapter/software combination completed an ECUFlash read in this session. It does not identify which transport/timing/configuration difference caused RK02_03 failure.','No actual Test Mode state, numerical voltage, raw81/83, seed/key bytes, initial baud/filter/IOCTL values or exact provider defaults are inferred from success.'],'sequence_comparison':{'ram_upload_address_lengths_equal':[(x['address'],x['length']) for x in cur['ram_upload']['events']]==[(x['address'],x['length']) for x in aug['ram_upload']['events']],'read_address_lengths_equal':[(x['address'],x['length']) for x in cur['logged_read_areas']['events']]==[(x['address'],x['length']) for x in aug['logged_read_areas']['events']]},'screenshots':{'ecuflash_printwindow_01.png':'Direct PrintWindow capture of ECUFlash, successfulidle/saveevidence','window_visible_01.png':'Occluded desktop capture showing foreground VSCode; not ECUFlash evidence'},'limitations':['Application interface close records and later normal GUI exit do not establish ECU reset or physical power state.','Application log has no explicit PassThruOpen/Disconnect/Close API statuses. Repeated version blocks after interface close support application reopen activity but not exact raw calls.','No provider was loaded, no new vehicle operation or test was initiated for this task. Normal closing may unload the app but is not claimed as hardware cleanup qualification.']}
save('SESSION_EVIDENCE.json',data)
readspans='; '.join(f"0x{x['start']:06X}..0x{x['end_exclusive']:06X}" for x in cur['logged_read_areas']['spans'])
md=f'''# Current ECUFlash session evidence

The newest successful ECUFlash read is preserved as `ecuflash_log_20260929t172612.preserved.txt` ({CURRENT.stat().st_size:,} bytes), SHA256 `{sha(CURRENT)}`. It is the primary comparator; August 18 remains a supplemental earlier success.

The app was idle with the completed read and save visible in `ecuflash_printwindow_01.png`. Initial directory metadata reported an empty log. By 00:36:50.849Z, before close, the source metadata and `log_copy_before_close.txt` already contained 79,435 bytes with the same final hash. The exact flush time/cause is unknown. Parent-authorized normal application close was requested at 00:36:50.9227335Z; process exit was confirmed at 00:37:08.9861718Z. Closing is not credited with producing the log content. No session button, provider invocation, forced termination or new vehicle command was issued.

## Image association

Lines 1352–1353 record saving `C:/Dev/SubaruRoms/current.bin` at 17:29:13.122 and writing 1,048,576 bytes at 17:29:13.123 local (00:29:13.123Z). The file timestamp is 00:29:13.1231299Z. Original and preserved copy are 1 MiB with SHA256 `{sha(current_bin)}`; the hash stayed unchanged across app close. The screenshot title and save lines independently show `current.bin`. This is a strong session-to-file association; the application log does not itself record a content hash.

## Session milestones

| Evidence | Current successful session | August18 success | RK02_VEHICLE_03 |
|---|---|---|---|
| Identity | line 90: 2F12515306 | line 89: 2F12515306 | BF raw reply contains 2F12515306 |
| 81/83 | raw bytes/API calls absent | raw bytes/API calls absent | 81 → C1 EF 8F; 83 → status 16, count 0 |
| Seed/key | lines 91–92: labels only | lines 90–91: labels only | never reached |
| RAM upload | lines 93–130: FFFF3000, size 0x1234, 37 blocks | lines 92–129: same address/length sequence | never reached |
| Kernel | line 132: OpenECU Subaru SH7058 DUAL Kernel V1.07 | line 131: same | never reached |
| Read/save | lines 137–1337: dump; 1352–1353: save | same read address/length sequence; 1355–1356: save | zero-byte partials |
| Physical Test Mode | unknown for this exact read | absent from log | G11 records connected greens, ignition ON, engine OFF, CEL/pump cycling |

Current and August report ECUFlash 1.44.4870, API 04.04, DLL 1.02.4870, firmware 1.17.4877 and serial TAPoN7at. Current source lines 3, 16, 42–45 and 73–88 establish these labels. Installed file hashes captured afterward are in JSON; they are not a session-time loaded-module hash. Executable/DLL PE version resources differ from runtime labels (1.44.0.4868/1.02.0.4868), so both are kept separate.

Current seed-label → key-label is {cur['label_timing_ms']['request_seed_to_sending_key']} ms; key-label → first RAM block is {cur['label_timing_ms']['sending_key_to_first_ram_block']} ms. August equivalents are {aug['label_timing_ms']['request_seed_to_sending_key']} ms and {aug['label_timing_ms']['sending_key_to_first_ram_block']} ms. These are application label intervals, not on-wire timing or proof of a specific wait.

The log records an initial kernel-version probe (77), interface close (78), another version block (79–82), unsupported VIN (83), interface close (84), then another version block (85–88) before SSM2 init (89). Two interface closes follow the dump (1338–1339). These show application lifecycle messages; no raw Open/Disconnect/Close statuses are logged. Normal GUI exit afterward does not prove ECU reset.

## Limits

The explicit read-area entries total {cur['logged_read_areas']['count']} blocks / {cur['logged_read_areas']['sum_logged_bytes']:,} bytes across {readspans} (end-exclusive), while the saved image is 1,048,576 bytes. This log alone cannot prove every saved byte was transferred from the ECU; it does not explicitly explain omitted read ranges. Full-byte acquisition claims require separate evidence.

The new successful read demonstrates a working ECUFlash read through this adapter/ECU combination in this session. It does not establish the physical cause of RK02's missing 83 response. Actual provider defaults/configuration, filter, baud transitions, raw 81/83 responses, seed/key bytes, exact Test Mode observation and voltage remain absent from this successful-session log. Prior RK02 observations and desired future probe state are not attributed to this read.

`SESSION_EVIDENCE.json` contains source hashes, full relevant event arrays, block sequences, the unchanged RK02 raw event stream, timestamp interpretations and explicit nulls. `EVIDENCE_MANIFEST.json` pins generated/preserved outputs. No original evidence or saved ROM was modified.
'''
(OUT/'SESSION_COMPARISON.md').write_text(md,encoding='utf-8')
manifest={'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='EVIDENCE_MANIFEST.json']}
save('EVIDENCE_MANIFEST.json',manifest)
print(json.dumps({'current_log':ref(CURRENT),'evidence':ref(OUT/'SESSION_EVIDENCE.json'),'comparison':ref(OUT/'SESSION_COMPARISON.md'),'manifest':ref(OUT/'EVIDENCE_MANIFEST.json'),'ram_blocks':cur['ram_upload']['count'],'read_blocks':cur['logged_read_areas']['count'],'read_bytes':cur['logged_read_areas']['sum_logged_bytes'],'read_spans':readspans,'sequence_comparison':data['sequence_comparison']},indent=2))
