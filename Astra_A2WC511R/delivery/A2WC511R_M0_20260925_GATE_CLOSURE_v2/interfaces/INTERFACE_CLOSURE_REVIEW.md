# Interface gate closure — A2WC511R final05

Completed offline. The actual installed RomRaider 1.1.0 editor and logger workflows passed. Physical SSM collection and OEM address support remain **PHYSICAL/BENCH REQUIRED**. No ECU/TCU/device connection, write, reset, flash or kernel upload was performed. The original frozen final05 payload/package was not changed.

| Gate | Result | Evidence |
|---|---|---|
| Actual editor confirmation/edit/display/undo/Save As/reopen | PASS | `gui_run11/events.json` and screenshots |
| Final persistent loopback client | PASS | 31 Python tests; final actual GUI run |
| Native SSM definitions/protocol/conversions | PASS | 8599 checks, 20 channels, 15 compiled samples |
| Full native virtual logger GUI and CSV | PASS | 300 displayed values; 6,667 CSV rows match compiled snapshots |
| Read-only collector, exact launcher, 32-bit runtime | PASS offline | 9,002 requests, two identical full ROMs, 260 six-byte samples |
| Native collector command/address guard independent review | PASS scoped | 285 checks; installed JAR bytecode corroboration |
| Physical transport/OEM A0 access | PHYSICAL/BENCH REQUIRED | No physical acceptance was attempted |

## Actual editor acceptance

The driver used the unchanged deployed Java agent and its real visible `JOptionPane` confirmation. It activated actual Yes/No `JButton` events on Swing EDT; it did not replace the callback or assign a dialog return value. This is automated UI acceptance under explicit authorization, not a claim that a person clicked the dialog.

On a disposable baseline copy, Idle Speed Target A cell 0 changed by four native raw counts, from displayed 1700 to 1701 RPM. Preview restored the complete buffer. Positive confirmation updated the actual display; cancellation changed nothing; native Compare Original/Off actions and screenshots were captured; native Undo restored the exact original buffer. An intervening edit while approval was visible caused postapproval stale rejection. The last confirmation stayed visible for 232 seconds, then its actual Yes button was pressed: the unchanged agent rejected its 230-second request deadline and the model remained unchanged.

Raw export reopened through native Open, including acknowledgment of the real Checksum Failed warning. All 488 table/axis records compared equal after excluding `original_raw`, which correctly resets on reopen. The native Save As menu and native JFileChooser Save button produced `de821aaac257e8704616a87378c936eda751ab2b05e8087050f04e6fc8388781`. All checksum corrections matched the independent installed-source audit; the only bytes beyond correction were the native edit stamp atFFC4C..FFC4F, `ffffffff -> 26092501`. Native reopen matched disk bytes. This is a disposable editor integration test, not a calibration recommendation.

The old urllib `Connection: close` path intermittently reset the local connection after repeated requests on both bundled Java 11 and side-by-side Java 21. Chunked reads and temporary server exception logging did not solve it. A serialized persistent direct loopback HTTP client did. `integrations/romraider_mcp/core.py` now reuses one connection, validates loopback identity, follows no redirects/proxies, resets failed connections and never automatically replays a request. Six real HTTP tests cover reuse, concurrent callers, uncertain commit response, redirect rejection, endpoint identity changes and external URL refusal. The previous core.py is preserved in `backups/`. Native run11 uses the final production client, with no retries or resets recorded. Runs01..09 preserve fixture debugging and superseded failures; run10 passed the test client, run11 is authoritative.

## Native virtual logging and the 32-byte layout

The frozen final05 logger fragment was inserted, unchanged, into a separate copy of the existing local logger definition. Existing definition bytes and parsed native parameter metadata were checked unchanged. No normal profile or installed definition was replaced. The actual installed native loader, EcuQuery conversions, SSM encoder/parser, response checksum validator and SSMLoggerConnection processed the final05 fields: five big-endian unsigned 32-bit words atFF7400..FF7413 and twelve unsigned bytes atFF7414..FF741F. Tests include unsigned maxima and big-endian ordering. Three unchanged historical definitions expose FF4BC1, FF4BC2 andFF4C8D.

The endpoint serves immutable RAM snapshots from 15 sequential executions of the compiled final05 payload. Snapshot hash: `fee2ff989929917ee55823cf3584c92bcfa1ff8984bee1232373a0fc8f5c1632`. It serves the raw final05 ROM read-only, hash `8092a20fd37f17dd351d18c805fdf195c2207af9adecca25e388146c7a9acc37`. Unknown RAM, other modules, malformed packets, writes and resets fail explicitly. BF identity/capability bytes are explicitly virtual, with zero capability flags; no physical sensor values are invented.

The full installed logger GUI ran with two narrowly scoped classes ahead of the installed JAR **only in its isolated test process**: provider discovery returns no providers, and the connection factory permits only `A2WC-VIRTUAL`. The rest of its controller, native parameter UI, displayed values, native Log To File action and CSV writer were used. All 300 displayed values and all 6,667 CSV rows match one of the 15 compiled snapshots. CSV SHA256: `e066732717e0d7701341982c6996dd03fef7c1788109614574612b20796c7b55`. Host logger timestamps and scenario 10 ms indices are software timing, not measured ECU cadence; repeated rows are not independent observations. GUI override classes are excluded from the collector classpath. No OpenPort/J2534 provider was loaded or globally modified.

## Prepared read-only collector

`integrations/romraider/virtual/Invoke-ReadOnlySSM.ps1` is the reviewed executable entrypoint. Default mode is virtual. It pins 107 artifacts, an explicit JAR classpath, exact class/resource file inventories including hidden/system files, and rejects reparse points. Independent review resolved missing runtime inventory, constructor/cleanup evidence loss, full-ROM/pilot CALID disagreement and unbounded BF quiet-wait findings. BF waits at most 10 seconds at the Java task level; native provider cleanup/hang behavior remains untested.

The native installed source and bytecode construct A0 as `80 10 F0 06 A0 00 aa bb cc (count-1) checksum`, using 24-bit addresses. The collector requests at most 240 ROM bytes per transaction, validates response code/E0, exact echo, length and native checksum, and bounds all addresses to the 1 MiB ROM. A8 reads only FF4C75, FF4C8D, FF4CA1, FF4C50, FF4BC1 andFF4BC2. Its wrapper rejects every other command/address and fast-poll mode before transport invocation. It never calls clearLine, reset, WriteMemory, WriteAddress or a kernel uploader. Each complete ROM must agree with the initial A2WC511R pilot; two full hashes must agree. Failure records include the current pass/offset and no transport fallback occurs.

The existing registered provider is `C:\Windows\SysWOW64\op20pt32.dll`, PE x86, SHA256 `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`. The collector uses existing `C:\Program Files (x86)\Java\jre1.8.0_503\bin\java.exe`; the complete virtual collection passed on that 32-bit runtime. The registry advertises ISO9141 support, but actual provider/device operation and OEM A0 access are untested. OpenPort J2534 is not assumed to expose a COM port.

The future command is **for the human after reviewing the root one-connection procedure**, with engine off and stable bench power:

```powershell
& C:\Dev\Astra_A2WC511R\integrations\romraider\virtual\Invoke-ReadOnlySSM.ps1 -Mode PhysicalJ2534 -OutputDirectory C:\Dev\Astra_A2WC511R\work\acquisition\one_connection_readonly_01 -AcknowledgeReadOnlyPhysicalConnection
```

It performs BF identity and CALID pilot reads; 60 consecutive initial six-byte samples; two full ROM reads with interleaved samples; then 60 consecutive final samples. All 260 sample records contain phase, sample index, UTC and monotonic host time. At 4800 baud the two full reads can take roughly 80 minutes. Denial, unexpected echo/code, invalid checksum, timeout or inconsistent ROM aborts; there is no ECUFlash/kernel fallback. A normal trace alone still does not establish communication-fault semantics, physical gear engagement or freshness guarantees.

## Reproduction and identities

Latest native protocol tests: `py -3 integrations/romraider/virtual/run_acceptance.py` -> `virtual_20260925T213711Z/`.
32-bit collector and constructor-failure tests: `py -3 integrations/romraider/virtual/run_collector_virtual.py` -> `collector_20260925T213714Z/`.
Exact sealed launcher: `Invoke-ReadOnlySSM.ps1 -Mode Virtual -OutputDirectory <new folder>` -> authoritative `collector_launcher_final03/`.
GUI logger: `py -3 integrations/romraider/virtual/run_gui_acceptance.py`; displayed/CSV verification: `verify_gui_csv.py` -> `logger_gui_20260925T213026Z/`.
Editor actual command and full events: `gui_run11/command.txt`, `gui_run11/events.json`; driver under `work/gate_closure/romraider_gui/`. Its fixed output label must be advanced for another run to preserve existing evidence.
Python tests: `py -3 -m unittest discover -s tests -p test_romraider*.py` -> 31 passed.

Installed RomRaider JAR: `43f0e92d652a5d2dde57fbe76ef99ff4f18c8147b0cbc20c0c4ccb33a7fe6635`.
Unchanged Java bridge JAR: `88183aa9a7e84503f23a412b8490f644dda5153dcaf2f035f5e9e5b788f644b0`.
Final collector manifest: `53275a23d23a01ac8aa3b0df1bc4efd2b7cbac392bade076ffd731960f5d0e84`.
`final_interface_identities.json` binds all changed sources and verified originals; `independent_collector_review.json` binds independent review and 285 policy checks. Original baseline, installed settings/JAR, existing logger XML, fragment and frozen raw ROM hashes were rechecked. All owned Java processes ended normally; no original editor state was open when acceptance began.

Automatic approval review rejected the optional local junction-creation regression as “blocked by policy” before process creation. No junction was created. The hidden-file rejection test passed; reparse-point rejection has source/real-inventory review, not an executed junction-probe claim. This is recorded in `runtime_junction_guard_test.json` and does not leave an original requested interface workflow unfinished.
