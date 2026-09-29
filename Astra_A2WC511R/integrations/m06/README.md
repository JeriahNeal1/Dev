# M0.6 RAW4 v1 host codec

This isolated module implements the project-specific observational SSM request.
It has no physical transport, does not load a provider, and does not change the
installed RomRaider application or the sealed M0 read-only acquisition collector.

From `C:\Dev`, run the synthetic host regression and record its report:

```powershell
py -3 C:\Dev\Astra_A2WC511R\integrations\m06\run_validation.py
```

The wire request is exactly 12 bytes:

```text
80 10 F0 07 BE 4D 30 36 01 page 04 checksum
```

`4D 30 36` is ASCII `M06`, version is 1, and page must be 0 or 1. `04`
requires four response data bytes. The SSM length includes the command byte.
The checksum is the low byte of the sum of all preceding bytes.

| Page | Exact request | Four returned bytes |
| --- | --- | --- |
| 0 | `8010F007BE4D3036010004FD` | source `FFFF4C75`, snapshot `FFFF4C8D`, latch `FFFF4CA1`, flags `FFFF4C50` |
| 1 | `8010F007BE4D3036010104FE` | actual OEM target `FFFF4BC1`, actual OEM current `FFFF4BC2`, snapshot `FFFF4C8D`, reason |

The response is exactly 10 bytes:

```text
80 F0 10 05 FE data0 data1 data2 data3 checksum
```

Page 1 reason bits are computed from its own three returned bytes:

| Bit | Meaning |
| --- | --- |
| `01` | Snapshot differs from `11` |
| `02` | OEM target differs from 1 or OEM current differs from 1 |
| `04` | At least one snapshot nibble exceeds 8 |
| `80` | Freshness and coherence remain unproven; always set |
| `78` | Reserved; zero in version 1 |

These are observations, not control eligibility or physical gear assertions.
Even `reason == 80` confers no validity guarantee. The original OEM decoder holds
the previous decoded value for nibble 9 through 15; the service therefore returns
the actual OEM bytes instead of reconstructing that history. Nibble 8 maps to 0.

The injected `Session(exchange)` callable must own an isolated, bounded exchange
and return exactly the 12-byte request echo followed by one 10-byte response.
`read_page(Page.RAW)` and `read_page(Page.OEM_DECODED)` return separate immutable
objects. Concurrent or reentrant requests are rejected. Any I/O, cancellation, or
framing failure faults the session, with no automatic retry. A new object alone
does not resynchronize a transport; the caller must independently re-establish
an isolated channel before constructing another session.

There is no nonce, page identifier, timestamp, or freshness counter in the reply.
The host validates the exact request echo, direction, lengths, command, checksum,
and page 1 reason. It cannot distinguish all stale or wrong-page replies whose
bytes also satisfy this schema. Do not serve cached responses or enable fast
polling. Do not combine the two pages into a coherent sample. Sequential byte
reads within one callback also do not establish an atomic producer snapshot.

The currently installed RomRaider parser rejects `FE`; ordinary address-based
logger definitions emit `A8` and cannot express this request. This module is a
separate codec, not a claim of unchanged native GUI logger compatibility. The
six existing OEM RAM definitions remain valid for their original `A8` use;
the retired persistent M0 state layout at `FFFF7400` is not this protocol.

Firmware acceptance must preserve the existing `A0`, `A8`, `B0`, `B8`, `BF`, and
`9F` behavior and the OEM ingress checks. A malformed or unsupported project
request must follow the original unsupported-command path. Magic and checksum
are framing constraints, not authentication. The intended implementation uses
one existing four-byte TX refill per request, with no new persistent RAM, saved
snapshot pointer, background hook, or counters. See the separate firmware and
simulator evidence for whether those implementation conditions are established.
