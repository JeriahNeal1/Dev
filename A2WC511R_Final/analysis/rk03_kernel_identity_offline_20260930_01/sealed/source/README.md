# RK03 kernel start and identity — offline model

This package is a deterministic static-fake transcript model. It is not a physical release. It imports no provider, simulator, device, filesystem, process or network interface. Its entry point takes no arguments and prints one simulated journal.

The unchanged 1,808-byte image SHA256 is `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`. It loads at `FFFF3000` and enters at `FFFF3004`. The embedded identity is **A2WC511R-RK02 followed by NUL**. RK03 names the host workflow; no new kernel identity is invented.

The fixed sequence is the already successful setup, BF,81,8300,2701,2702, virtual200ms,108502, virtual100ms,15625 baud,TX/RX clears, virtual200ms,one34,fifteen36 transfers with exact76 ACKs; then:

| Action | Fixed frame |
|---|---|
| Start at15625 baud | `8010f003310101b6` |
| Required OEM start ACK | `80f01003710101f6` |
| Stop OEM filter, set62500 baud, install BEEF pass filter | mask `ffff`, pattern `beef`, null flow |
| Identity request | `beef000101af` |
| Required identity reply | `beef000f8141325743353131522d524b3032005f` |

After the identity reply only filter/channel/device cleanup is modeled. There are24fixed transmissions:22retained upload/session transmissions,one start,one identity. Every preceding ACK is required. The three wait values total500virtual milliseconds; no physical timing is inferred.

SSM frames use one-byte body length and an additive checksum of preceding bytes. BEEF frames use `BE EF`,two-byte big-endian body length,body,and the same additive checksum. The identity response body is15bytes (`81` plus14identity bytes); the complete response is20bytes.

`contract/CONTRACT.json` preserves the exact reviewed frames and semantic call arguments. The first82actions derive from the successful physical upload log, with pointer addresses and provider timestamps removed and waits represented virtually. The seed/key pair is the captured fixed vector `b99d2bfd` / `51f7b537`. This model does not requalify arbitrary-seed logic, native ABI, physical receive fragmentation, or electrical timing. Earlier native qualification remains pinned evidence.

The distributable closure contains exactly `__main__.py`, `fixed_data.py`, `identity_model.py`. It has no generic transport callback, entry/payload/file input, command dispatcher for memory access, or physical mode. The test harness may select only enumerated fake faults at bounded action ordinals. These test controls are not CLI options. Captured device/channel/filter identifiers are fixture labels; a future native host must continue using provider-returned opaque identifiers. Captured provider-version strings describe the historical reference, not a provider loaded by this model.

Two independent clean output directories contain byte-identical Python zipapps and canonical build manifests. They are source-based executable models requiring Python, not Windows native executables. To run the sealed positive model offline:

```
py -3 -I -B kernel_identity/build_a/rk03_kernel_start_identity_offline.pyz
```

The SH-2E instruction review is separate from the distributable closure. It resumes the retained completed upload state, executes only the fixed OEM start and unchanged kernel identity path, and records code coverage and accesses. Generic simulator capabilities are not shipped inside the artifact. The retained kernel image itself has a ROM-acquisition command from its earlier design; this stage sends only identity command01 and never reaches that acquisition path. Qualification is bounded to this artifact and path, not a claim that the underlying unchanged kernel lacks other functionality.

Sealed analysis lives at `C:\Dev\A2WC511R_Final\analysis\rk03_kernel_identity_offline_20260930_01`. Prior sealed evidence remains unchanged. See `FUTURE_PHYSICAL_RELEASE_PLAN.md` for the next separately qualified stage.
