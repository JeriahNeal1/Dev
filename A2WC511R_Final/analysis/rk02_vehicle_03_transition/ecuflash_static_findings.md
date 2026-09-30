# Installed ECUFlash 81 -> 83 00 static findings

The command order is consistent with RK02. The concrete implementation gap is RK02's omitted explicit initial serial configuration. Its causal role in the missing physical reply is not established.

This review decoded the previously captured installed ECUFlash image offline. It did not launch ECUFlash, a provider, a vehicle tool, RK02, or a test. Existing acquisition and qualification files were read only. Address references below are RVAs in the captured image at base `0xE80000`; each companion assembly file identifies its source hash. The JSON records all input/output hashes.

## Provenance

- Installed ECUFlash executable SHA256: `5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115`.
- Captured image SHA256: `1c9b664dd8c27bc0db4fdc3dcb07e8b8e3e8abd39152c4f89f8367e508380c18`.
- Archived qualification_01 journal is actual installed-host API behavior against a **fake provider/model**. All events are physical=false. Its replies C1 and C3 are synthetic hypotheses, not captured physical C1EF8F/C30000FF00FF00. Fake timestamps are synthetic and read waits capped50ms. API arguments remain useful evidence of what the installed host requested.

## Exact transition

`ecuflash_static_selected_transition.asm` RVA9B5FE loads the protocol object; 9B601 calls StartCommunication at41AC0. At9B606 success is checked. 9B623/625/627 push zero length, null data and subfunction00 for AccessTimingParameters at416C0 (call9B629). 9B62E checks success, then9B638 calls the seed/key routine9AFD0. There is no intermediate opcode, IOCTL, explicit delay, baud change or EF8F-derived setting at this transition.

The81wrapper reserves a response buffer, invokes the named generic service, and returns its boolean without inspecting the returned data. GenericSIDcheck424D0 validates the framed response and compares responseSID to requestSID+40 at42583..4258E. The83caller likewise ignores returned timing bytes. Thus fullC1EF8F has no special configuration branch in this reviewed path. RK02 deliberately requires exact full reply payloads; that stricter policy did not trigger the physical failure, because no83reply was delivered.

The archived host confirms exact frames `8010F0018102` then `8010F002830005`, then seed `8010F0022701AA` (journal lines54,56,58; sequence=source line-1).

## Explicit initial serial setup

| Setting | ECUFlash host value | Evidence |
| --- | ---: | --- |
| Protocol / flags / baud | 3 / 0x200 /4800 | journalseq36; initializer9BB7F..9BB98 |
| PARITY(22) |0| static9BBBA..9BBC1 ->97BE0 ->97C9C; seq37,40 |
| P1_MAX(7) |1| static9BBC4..9BBCD; seq41 |
| P3_MIN(10) |0| static9BBD0..9BBD9; seq42 |
| P4_MIN(12) |0| static9BBDC..9BBE5; seq43 |
| LOOPBACK(3) |0| static9BBE8..9BBF1; seq44 |

The configuration vtable at87B694 maps slot+5C to97B50, which constructs a one-item SET_CONFIG and invokesIoctl2 at97BA9. Slot+3C maps to97BE0, which routes parity through parameter22 at97C9C. The vendor header defines the parameter identifiers at lines156..178. Values are independently established by code and archived host API arguments; flags0x200 are directly established by the archived host trace.

Frozen RK02 native_physical.cpp opens protocol3/flags0x200/4800 and sets its filter but sends no initial SET_CONFIG. Its physical journal has no GET_CONFIG, so actual timing/parity/loopback defaults remain unknown. The successfully corrected passive uses explicit configuration too, but has intentional differences: P3_MIN=1 and LOOPBACK=1 versus ECUFlash's zero values. It is therefore evidence that explicit setup is available, not proof that either value set alone fixes83.

ECUFlash uses four-zero-byte PASS_FILTER, LOOPBACK0, and clearsTX/RX buffers. RK02 uses a strict80F010 filter and explicit exact-request echo handling. These differ but no evidence isolates either as the cause. The archived pin9 voltageOFF command establishes no need for positive programming voltage or a new physical pin action.

## Timeouts and receive policy

Archived requested ReadMsgs timeouts: BF400ms,81 2000ms,83 500ms,seed/key500ms (seq52,54,56,58,61). Static generic return42612..4261A restores timeout from protocol+20, default500 at3D817, through vtable+68. That slot is310F00, a setter for transport+0C. Read consumer9735F passes that value to ReadMsgs.

Read consumer9737D..973A7 fails on any nonzero API status; on successful metadata it skips RxStatus bits0x0E. Thus there is no evidence that ECUFlash would retry the ERR_BUFFER_EMPTY returned to RK02. RK02's nominal2000ms transaction deadline does not mean it waited2000ms: it aborted after its first1000ms ReadMsgs returned16. That is a concrete timing-policy difference; ECUFlash's archived83timeout is shorter, so increasing a timeout alone is not an evidence-backed cure.

## After83

On success the selected caller performs seed/key, then a200ms delay call (9B648..9B64D), sets timeout2000 (9B655..9B65C), sends108502 through the session wrapper (9B68D), then a100ms delay call and baud15625 (9B69A..9B6C5). Selected upload9C0F0 adds200ms, sends34 twice at9C154/9C164, then transfers128-byte chunks beginningFFFF3000. Archived first declaration is34FF300004001234 and first36 is seq71. This is the installed DUAL1.07/0x1234-byte kernel path, not RK02. It does not identify a missing operation before83.

## Bounded conclusion

An isolated development correction can explicitly set and journal the serial configuration beforeBF, retaining the sealed RK02 artifacts. That would address a confirmed reproducibility gap. Physical root cause remains unproven: no captured wire timing/default configuration establishes whether83was emitted, ignored, filtered, or lost; no responseNRC establishes ECU rejection. Static and fake-host evidence cannot authorize a new physical attempt. Process exit alone proves neither provider cleanup nor ECU reset.
