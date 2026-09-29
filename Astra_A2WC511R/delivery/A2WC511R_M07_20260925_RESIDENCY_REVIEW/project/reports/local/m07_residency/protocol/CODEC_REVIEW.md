# Isolated M0.7 ECU research codec acceptance

**PASS for offline codec/fixture acceptance only.** The preferred supported
diagnostic service remains `integrations/m07`, using native A8/E8 with no ECU
changes. `work/M07/protocol/research_codec.py` is separate research support for
the two unapproved ECU payload builds. It has no transport, provider, or ROM
write operation and does not approve ROM ownership or physical behavior.

| Exact build profile | Page/version | Request bytes including checksum | Reply header | Payload bytes | Total reply bytes |
|---|---|---|---|---:|---:|
| `one_page_01` | 0/1 | `8010F014BE10FF4C75FF4C8DFF4CA1FF4C50FF4BC1FF4BC298` | `80F01007FC` | 6 | 12 |
| `two_pages_01` | 0/1 | `8010F00EBE10FF4C75FF4C8DFF4CA1FF4C507B` | `80F01005FC` | 4 | 10 |
| `two_pages_01` | 1/1 | `8010F008BE11FF4BC1FF4BC26E` | `80F01003FD` | 2 | 8 |

Request lengths are 25, 19, and 13 bytes respectively, including checksum.
Reply lengths include header, command, payload, and checksum. The page-zero
fields are source/snapshot/latch/flags. Page one contains actual OEM target and
current; the one-page profile returns all six in that order. There is no ECU
reason computation or new sample counter.

FC identifies version 1/page 0 and FD identifies version 1/page 1 within these
exact profiles. Future versions must use different response opcodes and explicit
new profiles. One-page FC carries six bytes; two-page FC carries four. Their
different exact lengths prevent cross-profile admission. One-page rejects every
page other than zero. The parser requires the exact canonical request, exact
echo, reply direction/length/opcode, additive checksum, and exact total size.
It rejects mixed pages/profiles even with a recomputed valid checksum. Host
freshness remains unknown and physical gear is not inferred.

Manifest pins:

- `one_page_01/manifest.json`: `a69589a230a9de0b75530cfa867feaef48ac1fd438f2029d20dd32695e5a8f21` (100-byte research payload).
- `two_pages_01/manifest.json`: `cd2f4267c0f4e09a43fe9e89785cce566917713d84dd65362b80e91211321a53` (88-byte matcher plus 60-byte main fragment).
- `execution_01/compiled_protocol_fixtures.json`: `8f1bf4e238e1b4e604d33ae16fcb14e76e8b969bd74ebc065600b9d061fd7868`.

`replay_codec.py` checks both manifest hashes and every manifest-listed artifact,
compares schema fields against the canonical codec, verifies the fixture hash,
overlay identity, event digests and actual OEM transmit writes, and checks the
returned raw bytes against the initialized scenario. All three accepted
compiled frames parse; all fifteen compiled negative ingress requests fail the
host request whitelist. Original-stock BE requests remain rejected in these
fixtures. Each requested raw address occurs once in the recorded raw-read list;
the OEM count prevents discarded resampling after the requested bytes.

Six regression groups pass: manifest-bound actual fixtures; strict profile/page/
version selection; every single-byte canonical request mutation with checksum
repair; exhaustive reply header byte mutations with checksum repair, echo and
checksum errors; cross-profile/page response and request rejection; and every
raw byte value preserving unknown freshness/physical gear. Synthetic response
vectors in the unit tests are clearly separate from actual compiled responses.

Run from `C:\Dev`:

```powershell
py -3 -B C:\Dev\Astra_A2WC511R\work\M07\protocol\test_research_codec.py
py -3 -B C:\Dev\Astra_A2WC511R\work\M07\protocol\replay_codec.py
```

The replay output records UTC and monotonic host replay times and explicitly
marks them as unrelated to ECU data age. It does not combine two pages into an
atomic sample. There is no nonce for repeated requests to the same page: any
future transport must enforce one outstanding request, bounded deadlines,
isolated response queues and terminal failure with no stale-response retry.
This codec has no physical transport to make those guarantees itself.

Native compatibility remains scoped. The installed RomRaider response parser
does not accept FC/FD, so these research replies require the separate codec;
the supported host service continues to use unchanged native E8. Absence of
FC/FD in that parser is not proof of global protocol/KWP opcode vacancy. The
research adapter must retain the OEM outer ingress/security rejection path and
the exact address whitelist. Page-one control `11` has low bit one; the new
adapter must clear the OEM continuous-response flag explicitly instead of
calling the ordinary A8 control initializer, which interprets bit zero as
continuous polling. The A8 payload producer tests bit one for its low-address
getter mode; both reviewed controls have that bit clear and every fixed address
is above `190`. These details do not authorize generic-address or existing A8
behavior changes.

The compiled fixture supplies SCI status/echo events and releases the first
reply byte from the OEM-built FIFO. It is instruction-level software evidence,
not an electrical, timer, interrupt, concurrency, or silicon model. ROM
reclamation/ownership, total context behavior, and physical acceptance remain
separate gates. Full-ROM A0 image attestation remains withdrawn.
