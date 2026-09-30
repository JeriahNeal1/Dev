# Future RK03_BOUNDED_ROM_READ_PHYSICAL

Design only. This plan and the offline zipapp authorize no additional physical
operation in the completed kernel-start/identity session. Do not convert the
offline model into a provider-capable artifact.

Derive a separate native release from the sealed physical identity host at
commit `a8cb760b09e6219ae640419ddb030af2037a432e`. Retain its proven setup,
serial readback, filters, BF/81/83, seed/key, waits, baud/queue transitions,
one34, all 15 fixed chunks and ACKs, one start, and one identity exchange.

Only after exact identity validation may it transmit
`beef00080300000000000200ba` once. Require a 523-byte reply with BEEF framing,
body length 518, command83, pass0, echoed address00000000, exactly512 data bytes,
and valid additive checksum. The data must equal the pinned current.bin block,
SHA256 `d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01`.
The complete expected reply hash is
`796f64cefcd2b81c5c7662b2bdacad828c0a948c55bfdc5d002ac5c8da7f898e`.

The native dispatcher must stop after the 25th acknowledged exchange and permit
only cleanup. Prove no 26th transmission, second read, second start, arbitrary
address/length/payload input, full-acquisition loop, flash path or retry exists.
The uploaded kernel image and identity string must remain unchanged.

Before any proposed physical use, separately qualify the actual native executable:

- Compare all retained 24 requests and API ordering to the successful physical
  identity transcript. Reuse the existing prefix qualification where unchanged.
- Add a bounded streaming receiver for the 523-byte reply. The current native
  identity receiver is limited to20 bytes and is insufficient for this response.
- Test every byte split, realistic multi-record fragmentation, exact echo,
  status-only records, empty/oversize records, flags, counts, unexpected frames,
  coalesced trailing bytes, malformed length, wrong pass/address/command/data,
  checksum failure, timeout and transport failure. Preserve all API arguments.
- Retain bounded whole-frame timing. Determine whether the existing deadline
  covers the fixed523-byte response using known baud and the measured identity
  path; document any intentional change. Do not claim simulator ticks as timing.
- Verify failure before or during this exchange leads only to cleanup, never a
  retransmission or later read. Verify filter/channel/provider cleanup and
  process exit under each failure state.
- Require two identical clean native builds, independent review, a fresh pinned
  certificate and fresh one-shot session identity. Existing physical identity
  authorization cannot authorize this later artifact.

Use only the simplified states: IGNITION OFF, TEST MODE ON, then a newly agreed
explicit software authorization token. After the one bounded read, on either
PASS or failure: IGNITION OFF, NORMAL MODE ON, then qualified passive BF/A8 OEM
return (BF2F12515306,120/120,PASS_CAPTURE_ONLY,clean observer/broker/provider exit).
No battery, charger, voltage, OpenPort or connector sub-gates. The operator manages
physical context. No ECUFlash fallback, retry, full read or further physical stage
in that session.

Success would establish only that the first512 bytes were returned correctly in
that physical session. Because that block equals current.bin and stock, it would
not establish the whole current image, calibration provenance or flash contents
outside the block. Any later broader acquisition remains a separate milestone.
