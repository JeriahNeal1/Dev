# Fixed host observations, pre-hardware extension

The frozen M07 `SnapshotClient`, response validation, six raw fields and host
reason predicates are reused. `transport.create_transport()` selects `replay`,
`native-virtual`, `fake-j2534`, or `physical-j2534` for the same caller.
No real provider has been loaded during qualification. Physical electrical
transport acceptance remains a first-connection observation, not an offline PASS.

Run the complete offline regression command from any working directory:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\integrations\prehardware\test_read_only.py
```

Rebuild only if source changed:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\integrations\prehardware\build_broker.py
```

Example disposable capture (choose a new output filename):

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\integrations\prehardware\capture.py --backend fake-j2534 --count 8 --interval-ms 100 --output C:\Dev\Astra_A2WC511R\reports\local\prehardware\example-new.jsonl
```

`native-virtual` uses the installed RomRaider codec through the accepted isolated
JVM, unchanged. `replay` uses the unchanged compiled OEM fixture. Fake mode uses
a separately compiled x86 DLL with the J2534 04.04 ABI and records every call.
Its values are fabricated provider tests, never vehicle telemetry. Physical
mode has its own explicit `--authorize-physical-read-only` selector and is not
part of this run's commands. See the withheld acquisition procedure before any
later physical invocation.

## Read-only construction argument

The x86 worker accepts only the exact, bounded ASCII lines `IDENTITY`,
`SNAPSHOT`, `CLOSE`, each terminated by LF. These are operation names, not bus
bytes. Every other string, extra field, CR, embedded NUL or overlong line takes
the terminal rejection branch. The first bus operation must be IDENTITY, once;
only SNAPSHOT may follow. A bad command ends the worker without processing later
queued commands. EOF and CLOSE clean up host channel resources.

There is exactly one J2534 transmit callsite. Its message is constructed only
from one of two immutable constants and rechecked immediately before the call:

- BF identity: `8010f001bf40`.
- Fixed A8: `8010f014a800ff4c75ff4c8dff4ca1ff4c50ff4bc1ff4bc272`.

The worker has no address, frame, protocol, baud, flags, IOCTL, provider-path,
kernel or actuation input field. It resolves only Open/Close/Connect/Disconnect,
ReadMsgs/WriteMsgs, fixed SET_CONFIG, and start/stop receive filter exports.
SET_CONFIG fixes ISO9141 timing/loopback/8N1, without initialization commands.
Connect is fixed to ISO9141, flags0200,4800baud. No periodic send, break,
programming voltage, reset, B0/B8, A0, flash or kernel command is constructible.
`PassThruWriteMsgs` here transmits a read request; it is not ECU RAM/flash writing.

The reviewed physical DLL path and SHA256 are pinned in the native worker;
the build manifest binds host source/executable/fake-provider hashes. Absolute
paths and scoped DLL dependency search avoid current-directory lookup. Provider
loading is lazy, after a valid first IDENTITY. All current tests select `--fake`.

The exact-equality parser and enum-to-constant mapping cover the unbounded
invalid-input domain structurally. Regressions exhaust all256 opcode values,
19,176 frame edits,11,520 native token edits and273 malformed worker inputs;
these finite tests check the implementation of that argument. Eleven provider
fault classes and byte-fragmented responses exercise the ABI boundary. The fake
independently rejects any other transmitted frame/configuration and includes
tripwire voltage/periodic exports. Caller objects cannot cause worker input to
be treated as raw bytes. This is not a security sandbox against a same-user
actor modifying these binaries or independently opening the real provider.

## Identity, timing and failure contract

The BF response is62bytes, opcodeFF,56payload bytes, additive checksum; ECUID
`2F12515306` is at full-response offsets[8,13). This contract comes from the
executed stock producer4857E and pointer table4EB0C, recorded in
`reports/local/prehardware/acquisition/BF_RESPONSE_CONTRACT.json`. It replaces
neither current-image attestation nor CALID acquisition. No extra CALID read is
exposed through this transport.

Both operations require exact request echo, direction, opcode, length and
checksum. No retry, protocol fallback, cached reply or masked-read attestation
exists. Provider metadata outside the reviewed framing is a terminal failure.
Provider timestamps/raw frames survive in JSONL and the worker stderr log;
UTC/monotonic host times are recorded by the common M07 client. Provider clocks
can wrap and are not ECU data-age measurements. Sequential reads do not prove
snapshot coherence, TCU freshness or physical gear engagement.

Read/transport failure ends the session. Normal close stops the receive filter,
disconnects and closes the device, checking return codes. If a provider hangs,
the host first submits only CLOSE and waits at most500ms for cleanup, then kills
its owned process if needed; this is not proof of driver/electrical cleanup.
Unconfirmed cleanup is an explicit close failure, including an unexpectedly
dead worker. Cleanup failures are latched across repeated cleanup calls.
No reset is sent to compensate. The physical
procedure must stop on a fault, preserving logs and without automatic retry.

The six channel reason semantics and unknown freshness bit remain exactly M07.
Physical capture is compatible with the same host API; its provenance honestly
reports `native_RomRaider_parser:false`. The native-virtual backend retains the
actual installed RomRaider parser acceptance path.

References used for API review: the installed RomRaider J2534 bytecode report,
[RomRaider ISO9141 implementation](https://github.com/RomRaider/RomRaider/blob/master/src/main/java/com/romraider/io/j2534/api/J2534ConnectionISO9141.java),
[RomRaider API definitions](https://github.com/RomRaider/RomRaider/blob/master/src/main/java/com/romraider/io/j2534/api/J2534Impl.java),
and [Tactrix documentation index](https://www.tactrix.com/index.php?Itemid=41&catid=41%3Aj2534&id=65%3Awhere-can-i-find-j2534-documentation&option=com_content&view=article).
Context7 was consulted for API discovery; the OEM frame/identity contract is
local firmware evidence, not a generic OBD initialization recipe.
