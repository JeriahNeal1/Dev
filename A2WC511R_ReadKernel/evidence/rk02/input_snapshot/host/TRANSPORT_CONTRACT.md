# Scoped native receive contract

The native host loads one compile-time pinned fake-DLL path in the new tree. It does not enumerate registrations or load the real OpenPort provider. Its fixed sequence has no transmit retries and no caller-specified byte, address, provider or kernel API.

The installed Tactrix `samples/common/j2534_tactrix.h` defines `TX_MSG_TYPE=1`, `START_OF_MESSAGE=2`, `RX_BREAK=4`, and `TX_DONE=8`. The installed `samples/klogger/klogger.cpp` discards start indications before printing received bytes. Context7 was consulted for current J2534 API guidance; it did not supply authoritative OpenPort-specific ExtraDataIndex or ISO9141 fragmentation behavior. Consequently, the narrower supported contract below is explicit, and actual hardware behavior remains a bench gate.

The host assembles each response across bounded J2534 messages. Protocol must remain ISO9141, TxFlags must be zero, and ExtraDataIndex must be either zero or DataSize (no inferred stripping of unexplained extra data). Up to four empty START_OF_MESSAGE/TX_DONE events or exact request TX echoes may precede received data. Nonempty start indicators, unknown status bits, RX_BREAK, mismatched echoes and indications after partial data fail immediately. RX data cannot exceed523bytes. Exact framing length, checksum, response opcode, pass and address are then checked. Complete bytes followed by extra bytes are rejected.

At most527 receive messages and a two-second host monotonic receive deadline are allowed for one response. A receive timeout fails the transaction; the host does not retransmit. This bound constrains host behavior and is not a verified silicon timing budget. Partial raw files and traces are preserved on failure.

The composite native test uses fragmented messages, start indications, exact TX echoes and both supported no-extra-data index encodings. The random fixture uses full messages. Negative tests cover breaks, interior extra-data indices, echo mismatch, empty data, checksum/address/pass errors, duplication and truncation.

On a failure the native process makes no further J2534 API calls. Process teardown ends the fake socket. This is not proof of adapter cleanup, ECU reset or OEM restoration. Normal success explicitly stops the filter, disconnects and closes the provider; that also does not reset the ECU. The parent runner bounds and terminates its owned Job Object and separately stops its exact owned loopback server.
