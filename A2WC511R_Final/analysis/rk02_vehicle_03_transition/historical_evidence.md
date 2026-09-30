# Historical success evidence for RK02 transition analysis

This is offline extraction of existing evidence. No provider, vehicle client, RK02, finalizer, test, or hardware attempt was executed.

## Best historical physical comparator

Use `C:\Dev\A2WC511R_ReadKernel\preservation\snapshot_20260927\roaming_OpenECU\EcuFlash\logs\ecuflash_log_20260818t120321.txt` (SHA256 `aa3918b717f72fe82fb50d600310b267f0e90a80eb310572a8b284139e020978`). It is the latest preserved successful read, with a clean single attempt, ECU ID `2F12515306`, DUAL1.07 response, A2WC511R metadata selection and an explicit 1 MiB raw-file save. Historical log content is preserved byte-for-byte; current AppData, preservation and recovered copies all match the previously recorded original hash.

| Stage | August 18 local time / line | July 26 successful local time / line |
|---|---|---|
| SSM2 init | 12:03:31.786 / 88 | 17:47:25.802 / 111 |
| ECU identity | 12:03:31.926 / 89 | 17:47:25.935 / 112 |
| Requesting Seed | 12:03:32.005 / 90 | 17:47:26.031 / 113 |
| Sending Key [1] | 12:03:32.051 / 91 | 17:47:26.062 / 114 |
| Upload-area label | 12:03:32.682 / 92 | 17:47:26.712 / 115 |
| First RAM block FFFF3000/0080 | 12:03:32.698 / 93 | 17:47:26.712 / 116 |
| DUAL1.07 response | 12:03:36.635 / 131 | 17:47:30.641 / 154 |

August reports `[FFFF3000,FFFF4234)` upload, first block at line93, DUAL1.07 at line131, A2WC511R selection at1340-1341 and1MiB raw save at1355-1356. Key-label to upload-area label is631ms; key-label to first-block label647ms. These are application-log intervals, not physical message timing.

July comparator `C:\Dev\A2WC511R_ReadKernel\preservation\snapshot_20260927\roaming_OpenECU\EcuFlash\logs\ecuflash_log_20260726t174613.txt` has SHA256 `b02a9ea761aed4db17f5094b3188f9b67082fca434a592db8e62566285c51b68`. Its first attempt closes632ms after Sending Key (lines88-93); a later attempt succeeds (lines111-116; key-to-first-block650ms). The next read-template label occurs55.808s after the earlier close. No intervening connector/ignition/voltage action is logged. The September29 ECUFlash diagnostic similarly closes618ms after key label; it is not the later RK02 failure.

## What the physical historical logs do not contain

No complete BF,81,83,seed,key,session-transition or upload wire bytes are logged. No baud, timing configuration, filter, buffer-clear, IOCTL, receive metadata or exact provider-call ordering appears. The physical logs do not independently locate81/83 between identity and the seed label. Their labels cannot distinguish a reject, timeout, malformed reply or host parser failure. Do not copy fake response bytes into a historical physical row.

## Separate installed-host offline API trace

`C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\qualification_01\j2534.jsonl` (SHA256 `d0a9d8ae43b5595578f0c9989d04e33ec3e7b9dd31ed7c5d400694800937af28`) contains actual calls made by the installed ECUFlash host in an isolated fake-provider run. Every extracted record is `physical:false`. `historical_offline_host_trace_prefix.json` retains complete sequences0-72, source lines1-73, full request/reply bytes and metadata through the first36 upload and76 acknowledgement.

| Step | TX bytes | Fake RX bytes | Source sequence TX/RX |
|---|---|---|---|
| 51 | `8010f001bf40` | `80f01039ffa210112f1251530673facba62b81fea800000060ce54f9b1e4000c200000000000dc00005d1f3080f226000043fb00e1000000000000c1f0c2` | 51/52 |
| 53 | `8010f0018102` | `80f01001c142` | 53/54 |
| 55 | `8010f002830005` | `80f01001c344` | 55/56 |
| 57 | `8010f0022701aa` | `80f0100667011234567802` | 57/58 |
| 60 | `8010f0062702e78f1f2165` | `80f0100367023420` | 60/61 |
| 62 | `8010f0031085021a` | `80f0100150d1` | 62/63 |
| 67 | `8010f00834ff30000400123435` | `80f0100174f5` | 67/68 |
| 69 | `8010f00834ff30000400123435` | `80f0100174f5` | 69/70 |

First full36 transfer is retained in JSON, sequence71/source line72; it is137 bytes total, including128 encrypted kernel-data bytes. Its fake acknowledgement is `80f0100176f7` at sequence72/source line73.

At sequence36 the host connects protocol3, flags0x200, baud4800. Before BF it sets PARITY22=0, P1_MAX7=1, P3_MIN10=0, P4_MIN12=0 and LOOPBACK3=0; clears TX/RX queues; installs pass filter1 with four zero bytes in mask/pattern/flow records; calls programming-voltage OFF on pin9; clears queues again. No API/configuration call intervenes between the81 read and83 write. After key acceptance it transmits10 85 02, changes data rate to15625, clears queues and issues two identical34 declarations before the first36. Full ordered records and timestamps are retained.

The recorded native PassThruWriteMsgs/ReadMsgs timeout arguments are400ms for BF,2000ms for81, and500ms for83 and security exchanges. These are API-call timeout arguments, not measured or guaranteed bus idle periods. The actual fake read implementation reports its wait capped at50ms, so the supplied native timeout must not be mistaken for elapsed wait.

The fake81 reply is onlyC1 and the fake83 reply onlyC3. Both are expressly `REFERENCE_MINIMAL_POSITIVE_RESPONSE_NOT_INSTALLED_ACCEPTANCE`, `VIRTUAL_RESPONSE_HYPOTHESIS`; RX timestamps are `SYNTHETIC_ZERO_UNTIMED`. The fake queue reads are immediate with timeout capped50ms, and SET_CONFIG merely stores values. Read-call-start81 to write-call-start83 is2.4987ms in this isolated run; that is host/RPC timing and cannot establish a working physical inter-message delay.

These records demonstrate installed-host ordering and argument values against a model. They do not demonstrate a successful physical83 response or prove that the RK02 transition should work on the vehicle. Current failed physical wire and source/stock-handler analysis must supply that comparison.

## Machine-readable evidence

- `historical_evidence.json`: source hashes, exact physical log events/line pointers, best-log rationale, copy provenance checks, missing fields and limitations.
- `historical_offline_host_trace_prefix.json`: complete prefix of existing fake API trace and ordered full wire exchanges.

Source evidence distinguishes historical application logs, installed-host fake API execution, and prior static reconstruction. The search found no raw physical successful81/83 capture in the scoped evidence directories.
