# RK02_VEHICLE_03 session-transition analysis

The exact host-side failure is known: after transmitting `80 10 F0 02 83 00 05`, the installed provider returned `ERR_BUFFER_EMPTY` (`16`, `0x10`) with zero messages; RK02's nonzero-status guard then terminated the invocation. The evidence does **not** uniquely establish why no physical reply reached the host.

The first verified implementation divergence occurs earlier, immediately after `PassThruConnect`: the installed ECUFlash path explicitly sets parity, receive/intermessage/interbyte timing and loopback. RK02 omits all initial `SET_CONFIG` calls and never records the inherited defaults. This is a concrete transport-reproducibility defect and a plausible contributor to the silence, not a proved single physical cause. A development correction must address that omission and reproduce the known API contract without claiming vehicle acceptance.

## Evidence boundary and preserved state

G13/ignition OFF and OEM return were confirmed by the user. No new physical check was performed. RK02 invocation count remains **1**. The complete failed acquisition directory is sealed by `FAILED_EVIDENCE_BEFORE.json`; analysis and recovery observations are outside it. No seed/key, kernel upload/start, ROM read or flash operation occurred. Both partial files are zero bytes. Finalizer exit1 correctly rejected the incomplete journal. The terminal journal contains no StopFilter/Disconnect/Close; process exit is not evidence of successful explicit provider cleanup or ECU reset.

There are three distinct comparators: historical physical **application logs**, archived actual installed-host calls to a **fake provider**, and **stock instruction execution**. Their provenance is preserved in the event diff. Neither synthetic replies nor stock replay bytes are substituted for unlogged historical physical data. The current vehicle ROM was previously edited and remains unacquired; stock instruction results do not prove its executable regions are identical.

## Best historical successful sessions

The best comparator is the August18 log, SHA256 `aa3918b717f72fe82fb50d600310b267f0e90a80eb310572a8b284139e020978`. It records ECU ID2F12515306 at line89, Requesting Seed90, Sending Key91, first FFFF3000/0080 RAM block93, DUAL1.07 response131, A2WC511R metadata1340–1341, and a1MiB raw save1355–1356. July26 independently records a successful read after an earlier key-stage failure; those attempts remain separate.

August's identity label is12:03:31.926; seed32.005; key32.051; upload-area32.682; first block32.698. The key-to-first-block label interval is647ms. These are application-log times, not wire/API times. No historical successful raw81/83 capture, provider call returns, configuration or bus timing was found in the scoped evidence. Consequently the last directly common historical physical observation is the ECU identity; historical full C1/C3 bytes remain unknown. See `historical_evidence.json` for exact source lines, July comparison and copy/hash provenance.

## Ordered transition through first upload

The following full byte values come from the archived installed-host **offline** API trace and the current RK02 physical journal. All historical physical raw request/response fields remain null in the machine-readable diff. The archived C1/C3/50/74 replies are minimal synthetic positives, not observed OEM responses. The table starts at the common BF operation; the JSON retains the entire API prefix, including initialization, through the first36 acknowledgement.

| Stage | Installed-host TX against fake provider | Fake reply | RK02 physical reply/outcome |
|---|---|---|---|
| BF | `8010f001bf40` | `80f01039ffa210112f1251530673facba62b81fea800000060ce54f9b1e4000c200000000000dc00005d1f3080f226000043fb00e1000000000000c1f0c2` | `80f01039ffa210112f1251530673facba62b81fea800000060ce54f9b1e4000c200000000000dc00005d1f3080f226000043fb00e1000000000000c1f0c2` |
| 81 | `8010f0018102` | `80f01001c142` | `80f01003c1ef8fc2` |
| 83 00 | `8010f002830005` | `80f01001c344` | `status16, count0` |
| 27 01 seed | `8010f0022701aa` | `80f0100667011234567802` | `not reached` |
| 27 02 key | `8010f0062702e78f1f2165` | `80f0100367023420` | `not reached` |
| 10 85 02 session | `8010f0031085021a` | `80f0100150d1` | `not reached` |
| 34 declaration first | `8010f00834ff30000400123435` | `80f0100174f5` | `not reached` |
| 34 declaration second | `8010f00834ff30000400123435` | `80f0100174f5` | `not reached` |
| 36 first RAM transfer | `137-byte frame; complete bytes in event diff` | `80f0100176f7` | `not reached` |

The exact stock positive83 reply is `80f01007c30000ff00ff0048` (12 bytes). The83 request is7bytes, declares2payload bytes and has checksum05. C1 EF8F is8bytes, payload3, checksumC2. All captured nonempty RK02 frames have valid declared lengths and additive checksums. Complete137-byte first36 frames, their lengths/checksums, API status values and source line numbers are retained in the JSON; no upload bytes are omitted there.

## Requested fifteen-point comparison

| # | Topic | Result and confidence |
|---|---|---|
| 1 | Complete wire bytes | RK02 and installed-host offline TX match BF/81/8300 exactly. Full historical physical replies were not logged. High confidence in captured bytes; historical raw comparison unavailable. |
| 2 | Checksums/lengths | RK02 BF,81,C1 and8300 framing is valid. Verified stock accepts exact8300 and produces C30000FF00FF00. No framing defect found. |
| 3 | J2534 calls/status | RK02 Open/Connect/Filter/BF/81/83Write all return0. The next ReadMsgs returns16/count0. API arguments for Connect/filter are inferred from the hash-bound source because the native journal omits them. |
| 4 | Connect | Both host paths select protocol3/flags0x200/4800. Opaque IDs differ legitimately. ECUFlash subsequently configures the channel; RK02 does not. |
| 5 | Baud/protocol | ISO9141=3, ISO9141_NO_CHECKSUM=0x200,4800 baud through83 and security. Both plan15625 only after108502. No83 baud/protocol change is found in installed-host or verified stock code. |
| 6 | Filters | RK02 PASS_FILTER maskFFFFFF/pattern80F010; ECUFlash all-pass four-byte zero mask/pattern. Expected stockC3 has the accepted80F010 prefix. Strict filtering could conceal an unexpected frame, but no such physical frame was recorded. |
| 7 | Echo | ECUFlash explicitly LOOPBACK0; RK02 leaves default unknown and accepts bounded emptySOM/TXDONE/exactTX echoes. Real BF/81 have SOM but no echo. This failure is distinct from the corrected passive observer's SOM defect. |
| 8 | Read timeouts | ECUFlash uses BF400ms,812000ms,83500ms; RK02 uses one1000ms slice inside a2000ms upper frame bound. Both hosts fail on a nonzero API result. RK02 did not exhaust its upper bound, but increasing its wait is not supported as the root-cause correction. |
| 9 | 81→83 timing | RK02 API-return to API-return:77.0782ms;83 write-return to empty-read-return:1001.8799ms. Exact physical bus gap and successful historical gap are unknown. Offline host RPC times are not comparable electrical measurements. |
| 10 | IOCTL/config | ECUFlash explicitly PARITY22=0,P1_MAX7=1,P3_MIN10=0,P4_MIN12=0,LOOPBACK3=0, plus queue clears. RK02 omits initial configuration/clears and does not query defaults. This is the earliest verified implementation divergence. |
| 11 | Missing intermediate command | No opcode/IOCTL/delay occurs between81-positive and8300 in the selected installed caller. Later differences include vendor key app-service, explicit200ms after key,100ms after108502,200ms before upload, queue clears after baud change and two34 declarations before first36. RK02 omits those delays and sends one declaration. Those were never reached by RK02. |
| 12 | Programming/Test Mode | User confirmed active mode, CEL/fuel-pump cycling, engineOFF; intentionally disconnected fans do not negate that observation. Stock83 validation checks length/session/subfunction, with no Test Mode test in the bounded handler. No Test Mode failure is inferred. |
| 13 | ECUFlash after C1 EF8F | Static StartCommunication/generic positive predicate checks C1 service success; it does not branch on EF8F in the selected caller. It next invokes AccessTimingParameters subfunction0 with zero extra bytes, then seed only after success. |
| 14 | Actual83 request | Yes: installed-host static path and recorded fake API TX both show exactly8010f002830005. It is not an invented opcode. Historical physical application logs alone cannot independently show those bytes. |
| 15 | ECU state change at83 | Stock81 sets communication-session bit20. Stock83 returns fixed timing bytes; it does not change baud. The separate108502 transition, which RK02 never reached, changes programming state. Current edited-code equivalence is unknown. |

## Status16 and installed provider definition

The selected provider remains `C:\Windows\SysWOW64\op20pt32.dll`, SHA256 `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`. Both installed OpenPort and ECUFlash SDK headers match the build header byte-for-byte: SHA256 `c559ea33654af59ad147eedfcccd56a1f2cb6e95daeb2412b53f6f4bbc76a7d9`. Their Error IDs define ERR_BUFFER_EMPTY=0x10 and ERR_TIMEOUT=0x09. Status16 is therefore an empty receive-queue result, not a negative ECU response, adapter disconnect code or a synonym for9. See `installed_provider_definition_check.json`.

The DLL resource version reads1.02.0.4868, while historical runtime ReadVersion logging reports1.02.4870/API04.04. Those are different evidence fields; no DLL was loaded to reconcile them during this analysis. The pinned binary hash identifies the selected file. Context7 was consulted but returned generic third-party J2534 guidance rather than this provider's exact behavior; installed SDK definitions and the physical journal control this finding. General vendor documentation corroborates the empty-queue meaning: [PassThruReadMsgs](https://quantexlab.de/en/develop/j2534/pt_readmsg.html). No generic retry example was adopted.

## Stock replay, causal candidates and exclusions

Independent replay executes actual stock RXI47E24 and response self-echo processing, obtaining full C1EF8F and C30000FF00FF00. No SMR/BRR/SDCR baud/protocol writes occur on that path. A separate actual-instruction replay shows that8periodic ticks between frame symbols reset the receive parser and can produce no reply to otherwise correct8300;0or7ticks pass. The tick duration and physical driver interbyte spacing are not established. Successful81 does not change the parser or this guard; a uniformly excessive gap should also affect81, so defaults alone cannot explain the different outcomes without actual cadence evidence. These tests establish a possible mechanism, not the vehicle cause. See `oem_transition_findings.md` and replay artifacts.

Ranked findings:

1. **Confirmed software contract defect:** explicit serial initialization was dropped from the reviewed installed-host path, and the physical logger omitted the argument/default evidence needed to audit it. Correct in a separate development branch; do not alter qualified RK02.
2. **Plausible physical cause:** an inherited timing/format setting produced an unacceptable frame gap or receive condition after81. Actual defaults and bus waveform are missing, so causality remains unproved.
3. **Other unresolved causes:** unexpected response hidden by the narrow filter, physical delivery/receive behavior, or a current-ROM executable difference. No observations distinguish these conclusively.
4. **Not supported:** wrong8300 checksum/length, an intentional stock baud switch/no-reply service, absent Test Mode inferred from disconnected fans, or a need simply to lengthen the timeout. ECUFlash's configured83 wait is shorter than RK02's.

BF/81 success proves communication at that stage; WriteMsgs success records provider acceptance, not ECU receipt. The final empty queue cannot alone distinguish malformed/missing electrical transmission from an ECU/parser or reception outcome.

## Development and qualification boundary

This analysis and event diff are produced before any corrective development. A new RK03-derived development branch may make the initialization contract explicit and improve argument/timing evidence, then test it against the archived host transcript and stock simulator. The frozen RK02 executable and failed acquisition remain untouched.

A valid replay must distinguish exact host requests/configuration from synthetic replies and stock instruction responses. Intentional differences—strict full replies/filtering, no programming-pin call, local seed transform, owned kernel size/content and no duplicate download/retry—require independent rationale. A fake replay cannot fill the missing successful physical83 waveform. No new physical attempt is qualified, requested or permitted in this run.

## Evidence and machine-readable diff

`RK02_VEHICLE_03_SESSION_TRANSITION_EVENT_DIFF.json` contains last-common/first-divergence records, full ordered frame comparison, physical historical event labels, timing/configuration deltas, confidence and canonical source paths/hashes. It points to the complete73-event installed-host offline API prefix and12-record RK02 journal. Unknown historical physical fields are explicitly null.

| Key evidence | SHA256 |
|---|---|
| `ecuflash_log_20260818t120321.txt` | `aa3918b717f72fe82fb50d600310b267f0e90a80eb310572a8b284139e020978` |
| `native_api.jsonl` | `e277405b588f5cfeec12a073f1ab0ac447945b23e3e48ba2303035c4caa6e53f` |
| `owned_physical_read32.exe` | `58d0867b85162e6fa4ccd3ac7fe0413c40e4054cbc416d12e39e29f926e60862` |
| `j2534_tactrix.h` | `c559ea33654af59ad147eedfcccd56a1f2cb6e95daeb2412b53f6f4bbc76a7d9` |
| `op20pt32.dll` | `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf` |

The complete hash manifest is in the JSON rather than duplicating every path here. Original raw images and failed logs are never rewritten.
