# Physical transition comparison

The one authorized `RK03_TRANSITION_PROBE_01` completed **BF → 81 → 83** and returned the full expected C3 response. It exited with code 0, and StopMsgFilter, Disconnect and Close each returned 0. This validates the limited transition in this session; it does not qualify security access, kernel upload or full acquisition, and it does not isolate one cause of the earlier failure.

## New direct evidence

The physical journal SHA256 is `57352963c842fa8cef0f45769a8c0f9613994df9c198fe434ee78e73d262a68b`. It contains exactly three transmissions and 22 successful API calls. BF reports ECU `2F12515306`; the complete BF and C1 reply bytes match the failed RK02 session. Native line 39 records:

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

The DLL build-time suffix difference is preserved, not normalized away. The probe pins `C:\Windows\SysWOW64\op20pt32.dll` to SHA256 `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`, also identified for RK02 in the earlier sealed analysis. Present installed files do not establish which module was loaded in the completed ECUFlash session. Numeric DLL-version equality is insufficient to assert identical session-time libraries. No provider change is proposed here.

The current ECUFlash session remains the primary full-read comparator; August is supplemental. Both log the same 37-block DUAL 1.07 upload sequence and 1,200 explicit read blocks, followed by a 1 MiB save. Current `current.bin` is strongly associated by exact save path, size and timestamp and is the authoritative acquired-image input. Sealed classification accounts for all 1,856 changed bytes as data, with no changed instructions; this supersedes the earlier analysis's unacquired-ROM uncertainty. It does not equate calibration behavior with stock or prove that every saved byte crossed the bus.

## Timing and causality limits

The new C1 API return → 83 API entry interval is **0.0433 ms**; 83 call duration is **15.0924 ms**; 83 write return → full C3 read return is **30.7277 ms**. For the directly comparable return-to-return measurement, new C1 return → 83 write return is **15.1357 ms**, versus **77.0782 ms** in RK02. RK02's subsequent empty-read return took **1001.8799 ms** after its write return.

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

The static delay sites are RVA 9B648–9B64D (post-key), 9B69A–9B6C5 (post-session), and selected upload routine 9C0F0 (pre-upload). Duplicate 34 calls are 9C154 and 9C164, corroborated by offline API sequences 67 and 69. Current key-label → first-upload interval is 618 ms and August's is 647 ms; these composite application timestamps do not measure an individual delay. The separate kernel hash is `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`.

## Evidence preservation

`PHYSICAL_TRANSITION_COMPARISON.json` pins every input and retains all 22 physical API returns with arguments, outputs, source lines and timing, the exact C3 record, the comparison matrix, and 16 remaining-difference records. The preserved installed-host API extract is explicitly labelled offline/fake; its replies are not promoted to physical evidence. `PROBE_GATE_STATE.snapshot.json` preserves a point-in-time copy of root's evolving gate record. Existing sealed reports, binaries, logs and ROM files were not changed. No client, provider, test, build or vehicle operation was invoked for this comparison.
