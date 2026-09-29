import hashlib,json,pathlib,datetime
here=pathlib.Path(__file__).parent;root=here.parents[3]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
native=here/'virtual_20260925T213711Z';gui=here/'gui_run11';logger=here/'logger_gui_20260925T213026Z';collector=here/'collector_launcher_final03'
assert read(gui/'events.json')[-1]['result']['status']=='PASS'
v=read(native/'result.json');log=read(logger/'display_and_csv_verification.json');c=read(collector/'acquisition_result.json');ind=read(here/'independent_collector_review.json')
assert v['status']==log['status']=='PASS' and c['two_full_reads_identical']
protected=read(gui/'protected_before.json')
for path,h in protected.items():assert sha(pathlib.Path(path))==h,path
inputs=read(native/'identities.json')
for path,h in inputs.items():assert sha(pathlib.Path(path))==h,path
manifest=root/'integrations/romraider/virtual/collector_runtime_manifest.json';m=read(manifest)
assert sha(manifest)==ind['manifest_sha256']
for item in m['artifacts']:assert sha(pathlib.Path(item['path']))==item['sha256']
source_paths=[root/'integrations/romraider_mcp/core.py',root/'tests/test_romraider_transport.py',root/'work/gate_closure/romraider_gui/GuiAcceptanceHost.java',root/'work/gate_closure/romraider_gui/run_gui.py',*sorted((root/'integrations/romraider/virtual').rglob('*.java')),*sorted((root/'integrations/romraider/virtual').glob('*.py')),root/'integrations/romraider/virtual/Invoke-ReadOnlySSM.ps1',manifest]
identities={'protected_originals':protected,'changed_or_added_integration_files':{str(p):sha(p) for p in source_paths},'native_virtual_inputs':inputs,'collector_manifest_sha256':sha(manifest),'native_logger_csv_sha256':log['native_CSV_sha256']}
(here/'final_interface_identities.json').write_text(json.dumps(identities,indent=2))
gates=[
 {'id':'NATIVE_ROMRAIDER_GUI','status':'PASS','reason':'Installed1.1.0 actual visible approval, native edit/display/compare/undo, cancel, postapproval stale rejection, actual232-second approval deadline rejection, rawexport/reopen and nativeSaveAs/reopen on disposable ROM; no approval callback bypass. All488 table/axis records match after export reopen excluding expected original_raw reset.','evidence':['interfaces/gui_run11/events.json','interfaces/gui_run11/positive_dialog.png','interfaces/gui_run11/edited_display.png','interfaces/gui_run11/native_save_chooser.png','interfaces/gui_run11/protected_after.json']},
 {'id':'NATIVE_ROMRAIDER_HTTP_TRANSPORT','status':'PASS','reason':'Serialized persistent loopback client fixes repeatedConnection:close resets observed onWindows/JVM. ActualfinalGUIrun11 zero resets;31Python tests pass including6 realloopback transport tests. No automatic retry of failedcommit.','evidence':['interfaces/romraider_python_tests.log','interfaces/gui_run11/events.json']},
 {'id':'VIRTUAL_NATIVE_SSM','status':'PASS','reason':f'{v["checks"]} checks of installednative loader/query/conversion/SSM connection;17 unchangedfinal05 diagnostic fields covering32bytes plus3 unchangedhistorical fields,15 compiledsamples, unsignedword/byte extremes andbigendian checks. Full1MiB nativeA0 reconstructionexact.','evidence':['interfaces/virtual_20260925T213711Z/result.json','interfaces/virtual_20260925T213711Z/native_loaded_definitions.json','interfaces/virtual_20260925T213711Z/native_virtual_samples.json']},
 {'id':'NATIVE_VIRTUAL_LOGGER_GUI','status':'PASS','reason':f'InstallednativeGUIlogger20channels andactualLogToFile;{log["native_GUI_display_checks"]} displayedvalues verified,{log["native_CSV_rows"]} nativeCSVrows each exactlymatchesoneof15compiledsnapshots. Isolatedfactoryhasno realtransport andproviderdiscoveryissuppressed.','evidence':['interfaces/logger_gui_20260925T213026Z/display_and_csv_verification.json','interfaces/logger_gui_20260925T213026Z/native_logger_sample_14.png','interfaces/logger_gui_20260925T213026Z/native_gui_views.json']},
 {'id':'READ_ONLY_COLLECTOR_OFFLINE','status':'PASS','reason':f'ExactsealedPowerShelllauncher oninstalled32bitJava passes9002 virtualrequests,twoidentical1MiBreadbacks and260sixbytesamplesincludinginitial/final60samplebursts.285 independentpolicy checks, constructorfailure evidence andhiddenclassguard pass;107artifacthashes andexactruntimeinventory reviewed.','evidence':['interfaces/collector_launcher_final03/acquisition_result.json','interfaces/collector_launcher_final03/raw_six_channel_samples.json','interfaces/collector_20260925T213714Z/negative_constructor_hash/acquisition_result.json','interfaces/independent_collector_review.json','interfaces/runtime_guard_test.json']},
 {'id':'READ_ONLY_COLLECTOR_PHYSICAL','status':'PHYSICAL/BENCH REQUIRED','reason':'No provider DLL loaded and no physicalconnection made. PreparednativeJ2534 ISO9141 path is bound toexisting32bitJava andregisteredOpenPortDLL; OEMA0 access,timing,responseecho andfaultbehavior areunproven.','evidence':['interfaces/independent_collector_review.json','interfaces/independent_j2534_iso9141_bytecode.txt','interfaces/final_interface_identities.json'],'remaining':'Human-only oneconnection BF+CALIDpilot+60initialA8samples+twofullROMreads+interleavedA8+60finalsamples; abortdenied/malformed/mismatched responses. Engineoffstablebenchpower, roughly80minutes at4800baud. See root acquisition procedure; no kernel fallback.'}
]
reasons={
'NATIVE_ROMRAIDER_GUI':'Installed RomRaider 1.1.0 passed actual visible approval, edit/display/compare/undo, cancellation, postapproval stale rejection, approval timeout, raw export/reopen and native Save As/reopen on disposable copies. No callback bypass; all 488 table/axis records matched after excluding the expected original_raw reset.',
'NATIVE_ROMRAIDER_HTTP_TRANSPORT':'A serialized persistent loopback client resolved repeated Connection:close resets observed on Windows/JVM. Final actual GUI run11 had no resets. All 31 Python tests passed, including six real transport tests. Failed commits are never automatically replayed.',
'VIRTUAL_NATIVE_SSM':'8,599 checks passed using the installed native loader, queries, conversions and SSM connection. All 17 unchanged final05 fields cover the 32-byte state, alongside three unchanged historical channels and 15 compiled samples. Unsigned limits, big-endian words and full virtual ROM reconstruction passed.',
'NATIVE_VIRTUAL_LOGGER_GUI':'The installed native logger GUI displayed 20 channels and wrote CSV through its actual Log To File action. All 300 displayed values and all 6,667 CSV rows matched compiled snapshots. An isolated factory allowed only the virtual endpoint; provider discovery was suppressed.',
'READ_ONLY_COLLECTOR_OFFLINE':'The exact sealed PowerShell launcher passed 9,002 virtual requests on installed 32-bit Java, two identical 1 MiB reads and 260 six-byte samples, including initial/final bursts of 60. Independent review passed 285 policy checks and verified 107 artifact hashes and exact runtime inventories.',
'READ_ONLY_COLLECTOR_PHYSICAL':'No provider DLL was loaded and no physical connection occurred. The prepared native J2534 ISO9141 path is bound to existing 32-bit Java and the registered OpenPort DLL. OEM A0 access, physical timing, response echo and fault behavior remain unproven.'}
for gate in gates:gate['reason']=reasons[gate['id']]
gates[-1]['remaining']='Human-only one-connection BF identity and CALID pilot, initial 60-sample A8 burst, two full ROM reads with interleaved samples, and final 60-sample burst. Abort denied, malformed or mismatched responses. Follow the root engine-off stable bench-power procedure; roughly 80 minutes at 4800 baud, with no kernel fallback.'
status={'schema':1,'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Offline native interfaces and prepared read-only collection; no physical acceptance','gates':gates,'verification_limitations':[read(here/'runtime_junction_guard_test.json')],'final_manifest_sha256':sha(manifest)}
(here/'interface_gate_status.json').write_text(json.dumps(status,indent=2))
text=f'''# Interface gate closure — A2WC511R final05

Completed offline. The actual installed RomRaider 1.1.0 editor and logger workflows passed. Physical SSM collection and OEM address support remain **PHYSICAL/BENCH REQUIRED**. No ECU/TCU/device connection, write, reset, flash or kernel upload was performed. The original frozen final05 payload/package was not changed.

| Gate | Result | Evidence |
|---|---|---|
| Actual editor confirmation/edit/display/undo/Save As/reopen | PASS | `gui_run11/events.json` and screenshots |
| Final persistent loopback client | PASS | 31 Python tests; final actual GUI run |
| Native SSM definitions/protocol/conversions | PASS | {v['checks']} checks, 20 channels, 15 compiled samples |
| Full native virtual logger GUI and CSV | PASS | 300 displayed values; 6,667 CSV rows match compiled snapshots |
| Read-only collector, exact launcher, 32-bit runtime | PASS offline | 9,002 requests, two identical full ROMs, 260 six-byte samples |
| Native collector command/address guard independent review | PASS scoped | 285 checks; installed JAR bytecode corroboration |
| Physical transport/OEM A0 access | PHYSICAL/BENCH REQUIRED | No physical acceptance was attempted |

## Actual editor acceptance

The driver used the unchanged deployed Java agent and its real visible `JOptionPane` confirmation. It activated actual Yes/No `JButton` events on Swing EDT; it did not replace the callback or assign a dialog return value. This is automated UI acceptance under explicit authorization, not a claim that a person clicked the dialog.

On a disposable baseline copy, Idle Speed Target A cell0 changed by four native raw counts, from displayed1700 to1701 RPM. Preview restored the complete buffer. Positive confirmation updated the actual display; cancellation changed nothing; native Compare Original/Off actions and screenshots were captured; native Undo restored the exact original buffer. An intervening edit while approval was visible caused postapproval stale rejection. The last confirmation stayed visible232seconds, then its actual Yes button was pressed: the unchanged agent rejected its230second request deadline and the model remained unchanged.

Raw export reopened through native Open, including acknowledgment of the real Checksum Failed warning. All488 table/axis records compared equal after excluding `original_raw`, which correctly resets on reopen. The native Save As menu and native JFileChooser Save button produced `de821aaac257e8704616a87378c936eda751ab2b05e8087050f04e6fc8388781`. All checksum corrections matched the independent installed-source audit; the only bytes beyond correction were the native edit stamp atFFC4C..FFC4F, `ffffffff -> 26092501`. Native reopen matched disk bytes. This is a disposable editor integration test, not a calibration recommendation.

The old urllib `Connection: close` path intermittently reset the local connection after repeated requests on both bundled Java11 and side-by-side Java21. Chunked reads and temporary server exception logging did not solve it. A serialized persistent direct loopback HTTP client did. `integrations/romraider_mcp/core.py` now reuses one connection, validates loopback identity, follows no redirects/proxies, resets failed connections and never automatically replays a request. Six real HTTP tests cover reuse, concurrent callers, uncertain commit response, redirect rejection, endpoint identity changes and external URL refusal. The previous core.py is preserved in `backups/`. Native run11 uses the final production client, with no retries or resets recorded. Runs01..09 preserve fixture debugging and superseded failures; run10 passed the test client, run11 is authoritative.

## Native virtual logging and the32-byte layout

The frozen final05 logger fragment was inserted, unchanged, into a separate copy of the existing local logger definition. Existing definition bytes and parsed native parameter metadata were checked unchanged. No normal profile or installed definition was replaced. The actual installed native loader, EcuQuery conversions, SSM encoder/parser, response checksum validator and SSMLoggerConnection processed the final05 fields: five big-endian unsigned32-bit words atFF7400..FF7413 and twelve unsigned bytes atFF7414..FF741F. Tests include unsigned maxima and big-endian ordering. Three unchanged historical definitions expose FF4BC1, FF4BC2 andFF4C8D.

The endpoint serves immutable RAM snapshots from15 sequential executions of the compiled final05 payload. Snapshot hash: `fee2ff989929917ee55823cf3584c92bcfa1ff8984bee1232373a0fc8f5c1632`. It serves the raw final05 ROM read-only, hash `8092a20fd37f17dd351d18c805fdf195c2207af9adecca25e388146c7a9acc37`. Unknown RAM, other modules, malformed packets, writes and resets fail explicitly. BF identity/capability bytes are explicitly virtual, with zero capability flags; no physical sensor values are invented.

The full installed logger GUI ran with two narrowly scoped classes ahead of the installed JAR **only in its isolated test process**: provider discovery returns no providers, and the connection factory permits only `A2WC-VIRTUAL`. The rest of its controller, native parameter UI, displayed values, native Log To File action and CSV writer were used. All300 displayed values and all6,667 CSV rows match one of the15 compiled snapshots. CSV SHA256: `{log['native_CSV_sha256']}`. Host logger timestamps and scenario10ms indices are software timing, not measured ECU cadence; repeated rows are not independent observations. GUI override classes are excluded from the collector classpath. No OpenPort/J2534 provider was loaded or globally modified.

## Prepared read-only collector

`integrations/romraider/virtual/Invoke-ReadOnlySSM.ps1` is the reviewed executable entrypoint. Default mode is virtual. It pins107 artifacts, an explicit JAR classpath, exact class/resource file inventories including hidden/system files, and rejects reparse points. Independent review resolved missing runtime inventory, constructor/cleanup evidence loss, full-ROM/pilot CALID disagreement and unbounded BF quiet-wait findings. BF waits at most10seconds at the Java task level; native provider cleanup/hang behavior remains untested.

The native installed source and bytecode construct A0 as `80 10 F0 06 A0 00 aa bb cc (count-1) checksum`, using24-bit addresses. The collector requests at most240 ROM bytes per transaction, validates response code/E0, exact echo, length and native checksum, and bounds all addresses to the1MiB ROM. A8 reads only FF4C75, FF4C8D, FF4CA1, FF4C50, FF4BC1 andFF4BC2. Its wrapper rejects every other command/address and fast-poll mode before transport invocation. It never calls clearLine, reset, WriteMemory, WriteAddress or a kernel uploader. Each complete ROM must agree with the initial A2WC511R pilot; two full hashes must agree. Failure records include the current pass/offset and no transport fallback occurs.

The existing registered provider is `C:\\Windows\\SysWOW64\\op20pt32.dll`, PE x86, SHA256 `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`. The collector uses existing `C:\\Program Files (x86)\\Java\\jre1.8.0_503\\bin\\java.exe`; the complete virtual collection passed on that32-bit runtime. The registry advertises ISO9141 support, but actual provider/device operation and OEM A0 access are untested. OpenPort J2534 is not assumed to expose a COM port.

The future command is **for the human after reviewing the root one-connection procedure**, with engine off and stable bench power:

```powershell
& C:\\Dev\\Astra_A2WC511R\\integrations\\romraider\\virtual\\Invoke-ReadOnlySSM.ps1 -Mode PhysicalJ2534 -OutputDirectory C:\\Dev\\Astra_A2WC511R\\work\\acquisition\\one_connection_readonly_01 -AcknowledgeReadOnlyPhysicalConnection
```

It performs BF identity and CALID pilot reads;60 consecutive initial six-byte samples; two full ROM reads with interleaved samples; then60 consecutive final samples. All260 sample records contain phase, sample index, UTC and monotonic host time. At4800baud the two full reads can take roughly80minutes. Denial, unexpected echo/code, invalid checksum, timeout or inconsistent ROM aborts; there is no ECUFlash/kernel fallback. A normal trace alone still does not establish communication-fault semantics, physical gear engagement or freshness guarantees.

## Reproduction and identities

Latest native protocol tests: `py -3 integrations/romraider/virtual/run_acceptance.py` -> `virtual_20260925T213711Z/`.
32-bit collector and constructor-failure tests: `py -3 integrations/romraider/virtual/run_collector_virtual.py` -> `collector_20260925T213714Z/`.
Exact sealed launcher: `Invoke-ReadOnlySSM.ps1 -Mode Virtual -OutputDirectory <new folder>` -> authoritative `collector_launcher_final03/`.
GUI logger: `py -3 integrations/romraider/virtual/run_gui_acceptance.py`; displayed/CSV verification: `verify_gui_csv.py` -> `logger_gui_20260925T213026Z/`.
Editor actual command and full events: `gui_run11/command.txt`, `gui_run11/events.json`; driver under `work/gate_closure/romraider_gui/`. Its fixed output label must be advanced for another run to preserve existing evidence.
Python tests: `py -3 -m unittest discover -s tests -p test_romraider*.py` ->31passed.

Installed RomRaider JAR: `43f0e92d652a5d2dde57fbe76ef99ff4f18c8147b0cbc20c0c4ccb33a7fe6635`.
Unchanged Java bridge JAR: `88183aa9a7e84503f23a412b8490f644dda5153dcaf2f035f5e9e5b788f644b0`.
Final collector manifest: `{sha(manifest)}`.
`final_interface_identities.json` binds all changed sources and verified originals; `independent_collector_review.json` binds independent review and285 policy checks. Original baseline, installed settings/JAR, existing logger XML, fragment and frozen raw ROM hashes were rechecked. All owned Java processes ended normally; no original editor state was open when acceptance began.

Automatic approval review rejected the optional local junction-creation regression as “blocked by policy” before process creation. No junction was created. The hidden-file rejection test passed; reparse-point rejection has source/real-inventory review, not an executed junction-probe claim. This is recorded in `runtime_junction_guard_test.json` and does not leave an original requested interface workflow unfinished.
'''
for old,new in {'cell0':'cell 0','displayed1700':'displayed 1700','to1701':'to 1701','visible232seconds':'visible for 232 seconds','its230second':'its 230-second','All488':'All 488','final05 fields':'final05 fields','the32-byte':'the 32-byte','unsigned32-bit':'unsigned 32-bit','from15':'from 15','all300':'all 300','All300':'All 300','all6,667':'all 6,667','the15':'the 15','scenario10ms':'scenario 10 ms','pins107':'pins 107','at most10seconds':'at most 10 seconds','using24-bit':'using 24-bit','most240':'most 240','the1MiB':'the 1 MiB','that32-bit':'that 32-bit',';60':'; 60','then60':'then 60','All260':'All 260','At4800baud':'At 4800 baud','roughly80minutes':'roughly 80 minutes','->31passed':'-> 31 passed','and285':'and 285','Java11':'Java 11','Java21':'Java 21'}.items():text=text.replace(old,new)
(here/'INTERFACE_CLOSURE_REVIEW.md').write_text(text,encoding='utf-8')
print(json.dumps({'report':str(here/'INTERFACE_CLOSURE_REVIEW.md'),'status':str(here/'interface_gate_status.json'),'manifest_sha256':sha(manifest),'gates':[(g['id'],g['status']) for g in gates]},indent=2))
