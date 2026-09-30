# Native identity release: independent review

**PASS — no remaining blocking finding in the reviewed native source, offline qualification evidence or release controls.** No physical session, provider load or vehicle operation was performed by this reviewer.

The two clean x86 builds match SHA256 `623dc766ca69a97b16f7beabc9acb909a1225eabb8a21c40fe8379b4f72b593f`. The same physical-capable executable passed all 386 offline cases on its first qualification run: 358 virtual fixtures, four real-clock fake fixtures and 24 disposable bootstrap fixtures. This comprises 50 complete protocol successes, 312 expected terminal failures and 24 bootstrap checks. The retained 311 cases ran only against the new executable; the prior executable and evidence were unchanged. There are 75 additional start/identity cases.

The native host permits exactly 24 transmissions: the retained 22-request upload sequence, fixed start `8010f003310101b6`, then fixed identity request `beef000101af`. All 15 chunk ACKs precede start. Exact start ACK `80f01003710101f6` precedes removal of the OEM filter, the checked 62500-baud SET and the BEEF filter with mask `ffff`, pattern `beef` and null flow. The fake returns a distinct new filter ID to verify ownership and cleanup. No queue clear or added wait follows start.

The identity parser accepts only `beef000f8141325743353131522d524b3032005f`, including the terminating NUL in `A2WC511R-RK02`. It bounds input to 20 bytes, 24 records and four leading indications. Tests cover every two-part split, one-byte fragments, exact echoes and indications, malformed metadata, wrong identity/version, missing NUL, invalid lengths/checksums, trailing data, API errors and filter/baud failures. Late otherwise-valid start and identity replies took 2100.5638 ms and 2100.0378 ms respectively; both failed the post-return deadline check. The initial SSM parser and nine shared source files remain byte-identical to the prior release.

The reviewer verified 1,724 hash references covering 1,332 distinct paths. The native source was authored by root and independently reviewed here. The qualification runner was authored and executed by this reviewer; root separately reviews that runner and its results. No claim of independent authorship is made for the runner-author audit.

Release controls have 36 mocked launcher checks, 14 mocked recovery checks and 46 pure result-validator checks. Review findings were corrected before completion: both competing executable names remain detected; result/state labels now identify this stage; the validator requires each reply before any following control operation and rejects observed receive windows of 2000 ms or longer. Earlier control revisions remain archived. Canonical controls and tracked copies match exactly.

Machine-readable evidence:

- `NATIVE_AND_QUALIFICATION_REVIEW.json`: SHA256 `885bc4febf2a30a67028a62c13449dd185a62a61a215c829d9a72b55946d6a0a`.
- `RELEASE_CONTROLS_REVIEW.json`: SHA256 `d7213de862bd2d773311b7057344deac0518eb58b709c20296cf1982fe099825`.
- New test report `qualification_20260930T061208911770Z/TEST_REPORT.json`: SHA256 `0be7a4c5d0291af17f9d02b144580457cb5d4ab1ddc9601bb8bc6c68270a7a49`.

The kernel image remains unchanged and still contains its earlier raw-read implementation. This host provides no request path to it, arbitrary entry, address or payload. Fake and instruction-model evidence does not establish physical kernel entry, measured electrical baud or silicon timing. Coalesced trailing data is rejected; the host does not perform an extra receive to attest absence of a separately queued record after the complete identity reply.

This review grants no physical authorization. The release still requires its certificate, fresh human states and the exact authorization token before one invocation. No ROM acquisition or subsequent physical stage is authorized by this review.
