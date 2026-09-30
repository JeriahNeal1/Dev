# Future RK03_KERNEL_START_IDENTITY_ONLY_PHYSICAL

Status: design plan only. No physical release, provider loading, vehicle action, or kernel execution is authorized by this offline result.

Use the already qualified full-upload physical source as the future native base. Add only the reviewed one-start/one-identity suffix. Do not make the offline zipapp provider-capable. Preserve its static-fake qualification unchanged.

The native dispatcher must bound total transmissions to24, with the first22 unchanged; index22 must be `8010f003310101b6`, and index23 must be `beef000101af`. Require all fifteen76ACKs before start, exact start ACK `80f01003710101f6` before identity, and exact20-byte identity response `beef000f8141325743353131522d524b3032005f` before success. The only permitted operations afterward are cleanup. No16thchunk,secondstart,ROM or arbitrary-memory read,flash command,address/payload selection,or automatic retransmission may exist.

Retain the proven initial4800baud setup: protocol3,flags512; PARITY0,P1_MAX1,P3_MIN0,P4_MIN0,LOOPBACK0; fiveSET calls and checkedGET; broad receive filter. Retain200/100/200ms waits,15625 transition andTX/RX clears,one34,and all fifteen fixed36frames. After the start ACK, the retained reviewed host stops the OEM filter, sets62500baud and installs a fixed BEEF pass filter (maskFFFF,patternBEEF,null flow). This suffix has offline evidence, not a physical RK03 pass. It adds no speculative delay or queue clear. Any departure must receive its own documented justification and tests.

Before physical authorization, independently qualify the actual native executable, not only this model: exact transcript equivalence, all seed vectors, minimum wall-clock waits, J2534 ABI and output bounds, fragmented/coalesced/echo/status-only BEEF reception, whole-frame deadline,62500baud configuration failure,filter ownership/cleanup on every failure,and launch-once persistence. Compare the native call graph and emitted frames to the sealed static model. Extend tests for malformed lengths/checksums,wrong identity/version,timeout,extra bytes,negative ACKs and cleanup failures. Require two clean byte-identical builds,independent review,and a new hash-bound physical certificate. Reuse unchanged prefix evidence; do not recount its prior tests as new.

The uploaded image must remain exactly1808bytes with SHA256 `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`,entryFFFF3004. Its actual version string remains A2WC511R-RK02 plusNUL. The instruction model supports control-flow/framing correctness under declared peripheral assumptions; it cannot establish silicon timing,electrical conditions,or physical kernel entry success.

Only after that future release qualifies, use these human states, one at a time:

1. IGNITION OFF.
2. TEST MODE ON.
3. Display expectedECU2F12515306,exact executable/certificate/image hashes,the fixed start/identity contract,closed competing clients,and invocation count0. Require exactly `PROCEED RK03 KERNEL START IDENTITY`.
4. Launch once. Qualified full upload → one fixed start → one fixed identity/version validation → STOP → cleanup. No ROM read. No physical state changes while active.
5. On either success or terminal failure: IGNITION OFF, then NORMAL MODE ON, then qualified passive BF/A8 OEM-return verification (BF2F12515306,120/120,PASS_CAPTURE_ONLY,clean observer/broker/provider exit).

Do not create battery,charger,voltage,OpenPort,or connector sub-gates. The operator manages those under the simplified policy. On a reported power/electrical/adapter problem, stop software activity and request only the appropriate ignition state. Preserve all logs; no fallback ECUFlash,no retry,no further physical stage in that session.

The next recommended milestone is **separately qualify RK03_KERNEL_START_IDENTITY_ONLY_PHYSICAL**. A physical run requires its own later explicit authorization. This plan does not authorize ROM acquisition after identity.
