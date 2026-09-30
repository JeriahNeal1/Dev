# RK03_KERNEL_START_IDENTITY_ONLY — OFFLINE PASS

The static-fake model passed **526/526 checks**, including **433 negative cases**. Independent review passed. No physical operation or provider load occurred in this scope. Completed transition, first-chunk, full-upload and OEM-return physical PASS evidence remains unchanged.

Source branch: `rk03/kernel-start-identity-offline`. Commit: `8ccd48b6e7dda637d13eaed33175a1c415d8bfc1`.

Both clean builds produced the same 81,146-byte Python zipapp. This is an executable model, not a native physical release:

`04d8332493c98e90fa3c537c8ea0bc12926b5a85e37ea8ea9c826ec8e03c34fe`

Canonical build manifest SHA256: `bf3aaa321fcf09e7a8af69b5eabe45e87a95654d0886b4a481e654a2f69b58fe`.

Qualification certificate SHA256: `1ea49f1c26570305e15801e27408a0b0c0f153e35e32df8d09e73dd121d34c27`.

## Fixed boundary

The reviewed transport/session setup and all 15 fixed upload chunks are retained. All 15 exact `76` acknowledgements are required before one start. The modeled sequence contains 24 transmissions total and stops after one exact identity response, followed only by cleanup.

| Contract | Value |
|---|---|
| Unchanged uploaded image | 1,808 bytes, SHA256 `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581` |
| Entry | `FFFF3004` |
| Start at 15625 baud | `8010f003310101b6` |
| Start ACK | `80f01003710101f6` |
| After ACK | stop OEM filter, set 62500 baud, install fixed BEEF pass filter |
| Identity request | `beef000101af` |
| Identity reply | `beef000f8141325743353131522d524b3032005f` |
| Actual identity | `A2WC511R-RK02` followed by NUL |

SSM uses an 8-bit payload length; BEEF uses a 16-bit big-endian length. Both append the sum of preceding frame bytes modulo 256. The identity body is 15 bytes and the complete reply is 20 bytes. RK03 names the host workflow; the pinned kernel identity remains RK02.

## Evidence and exclusions

The first 22 frames match the successful physical full-upload log. Address, length, cipher hash and frame checks retain all 15 chunks, including repeated payload hashes at different addresses. The previously verified complete RAM image is reused unchanged.

The instruction review resumes retained post-upload state and verifies that the exact OEM start path reaches `FFFF3004`; it then executes the unchanged kernel's identity path. Both poisoned-register and actual OEM-register cases pass. Its detailed report records peripheral assumptions and coverage. No kernel ROM-data read or flash write occurs in that path. Simulation does not establish silicon timing or a physical kernel-start PASS.

The distributable contains only three Python modules and standard-library JSON, hash and console support. It has no external file input, provider loading, OpenPort interface, dynamic backend, entry/payload/address selector, ROM-read command, flash operation, second start or retry. The fixed identity request is the only custom-kernel command. The underlying unchanged kernel's older read capability is not exposed by this artifact.

Negative cases cover every modeled call failure, output mismatch, each exchange's malformed/checksum/length/status replies, wrong identity and version, short virtual waits, and cleanup failure. Cleanup after failures is verified without a later protocol transmission. The existing 287 native qualification cases were reused, not counted again.

## Next milestone

Separately qualify **RK03_KERNEL_START_IDENTITY_ONLY_PHYSICAL** using the future plan. Native boundary integration, ABI/stream handling, real deadlines and timing, filter/baud transition and launch-once controls remain release work. No vehicle run is authorized by this package. A later qualified release must use only IGNITION OFF, TEST MODE ON, NORMAL MODE ON and require exactly `PROCEED RK03 KERNEL START IDENTITY` before its single invocation.

The future stage ends after identity and cleanup, then ignition OFF, normal mode, and passive OEM return. It must not read ROM.
