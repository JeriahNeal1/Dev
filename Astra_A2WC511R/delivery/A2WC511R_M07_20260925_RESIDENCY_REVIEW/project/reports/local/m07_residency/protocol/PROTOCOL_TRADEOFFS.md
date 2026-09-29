# M0.7 raw-only protocol research

The smallest implemented ECU extension is **100 bytes**: one version1/page0 response containing all six raw bytes. Its canonical request is25 bytes including checksum, and its response is12 bytes. A fully implemented two-page alternative uses **148 bytes**, split into88-byte and60-byte fragments; a complete six-variable observation takes19+13 request bytes and10+8 response bytes. These are measured compiled designs, not a theorem that no smaller encoding exists.

Both variants reuse the unchanged OEM A8 payload producer, memory-access classifier, RX validation, TX FIFO and byte-progress counter. They add only an exact-match branch to the live unknown-command path. They do not install a refill hook, compute predicates in the ECU, rewrite the request buffer, or allocate persistent RAM. The fixed canonical address list ensures the project request exposes only the six already-reviewed RAM bytes. Existing OEM arbitrary-address requests retain their own unchanged permission behavior.

| Profile | Version/page selector in request | Exact response | Raw bytes |
| --- | --- | --- | --- |
| One page | BE command, control10, full six-address canonical request | FC, length7 | source,snapshot,latch,flags,target,current |
| Two pages, page0 | BE command, control10, exact four-address canonical request | FC, length5 | source,snapshot,latch,flags |
| Two pages, page1 | BE command, control11, exact two-address canonical request | FD, length3 | target,current |

FC and FD identify version1/page0 and version1/page1 within the selected profile. They must not be reused for future incompatible protocol versions. Host parsers validate the selected profile, exact echoed request, direction, opcode, length and checksum. A checksum-valid wrong-page response is rejected. The one-page and two-page FC replies also have different required lengths. No transaction nonce or ECU timestamp is added: an identical valid stale reply can still be indistinguishable, so host serialization, terminal faults, raw capture and explicit unknown freshness remain necessary. This is a scoped SSM extension, not a claim that these bytes are globally unused by every protocol.

The apparent low control bit in page1 is a page selector here. The new adapter does not call the native484D4 auto-repeat setter and explicitly clears649A.bit80, so neither page enables continuous polling. The A8 reader's control&02 distinction is unchanged; every fixed address is above its indexed-getter range. The OEM receive/header/checksum gate and the refill's649B.bit0 rejection remain intact. Installed native RomRaider accepts its ordinary E8 reply; these new FC/FD replies require the isolated research codec. The preferred supported host service continues to use ordinary A8/E8 with no ECU modification.

## Discarded refill resolved through existing state

The OEM A8 producer maintains its existing progress byte6403 and checks it against responseLength-1 before reading another requested address. Full47E24 receive/echo/parser/dispatch/transmit execution shows exactly six source reads for the one-page profile and exactly four/two for the two-page profile. The driver's extra callback after a four-byte payload performs no additional source sampling. There is no new counter and no new writer to any persistent diagnostic object. This reuses already-proven behavior rather than adding a second conditional custom producer.

`execution_01/compiled_protocol_fixtures.json` records three valid profile/page exchanges,15 invalid checksum/version/page/address/destination cases, and two unchanged nativeA8 stock-versus-research comparisons. Ordered nonstack writes and final OEMSSM state match on the native pairs. Input RAM and SCI status/echo events are explicitly virtual; the first transmitted byte is released from the OEM-built FIFO by the fixture. No first-byte timer, interrupt-delivery, electrical or silicon-timing claim follows.

## ABI and candidate residency

The adapter saves R1/R4 on an8-byte private frame. R2/R3 are overwritten by the unchanged484BC/C0 continuation. The incoming unknown-command path has T=0; the adapter rejoins with T=0 while leaving otherSR bits intact. The two-page matcher uses a local call, but the original4828C prologue already savedPR and the484C4 epilogue restores it before use. Independent full-function return tests check this contract; comparison at an intermediate deadPR point would be inappropriate. No new interrupt masking or FPU operation occurs.

One-page placement is the candidate division tail[42A4,4308). The two-page matcher occupies[42A4,42FC), and its adapter occupies[14770,147AC). Both are research placements inside proposed executable-function replacements. The compacted setter table and E1000 are unchanged. Function-equivalence proofs, complete inbound ownership, and physical timing are separate gates. **These fragments are not approved ROM residency.**

The division replacement changes the execution cost of its existing callers even when the project service is idle. The two-page alternative additionally changes the cost of the OEM range routine. No new periodic diagnostic hook exists, but the timing consequences of those OEM replacements must be included in bench qualification. A smaller ROM footprint does not imply lower instruction count.
