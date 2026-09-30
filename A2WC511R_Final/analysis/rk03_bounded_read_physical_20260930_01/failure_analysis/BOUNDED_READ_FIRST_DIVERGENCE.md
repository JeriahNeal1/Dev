# RK03 bounded physical read: terminal failure

RK03_BOUNDED_ROM_READ_PHYSICAL = FAIL. One invocation; no retry. All15 upload acknowledgements, the fixed start and exact kernel identity passed. One correct bounded request was transmitted: `beef00080300000000000200ba`. Cleanup passed.

The ECU/provider returned an empty start-of-message record, then228 bytes beginning with the correct `BEEF0206830000000000` header. The first227 frame bytes match the expected reply: header10 plus217 payload bytes. At frame offset227 (candidate ROM address000000D9), expected28 becameF8. The remaining295 expected frame bytes were not delivered. The finalF8 is not a valid checksum of the preceding bytes (that sum is39).

The next PassThruReadMsgs returned decimal16, count0, after1005.3896ms. The pinned Tactrix header defines16 as ERR_BUFFER_EMPTY; ERR_TIMEOUT is9. This is an incomplete/corrupt response, not an absence of all ECU response.

No complete returned512-byte hash exists. Expected payload SHA256: `d3421c81a4380638a8844e34012db592ba6eed35ca5cb8402880b79869e71f01`. Incomplete228-byte frame SHA256: `ce0c68f88b65e0e85c7bd3e9f538b3406bf2f39f494e332ce99d8512fbdbb1b6`. Extracted218-byte candidate payload is explicitly unvalidated; only its first217 bytes match current.bin.

The recorded serial configuration, baud transitions and queue clears match the successful physical identity session. The previous physical identity session does not supply a successful physical ROM-read comparator. The sealed instruction/fake model supplies the expected523 bytes but cannot establish silicon or K-line timing.

The fixed source contains no217-byte stop boundary: its read loop is512 bytes. Fatal/exception paths disable SCI, but this log does not establish that either path ran. An ECU transmission interruption, electrical fault, or provider/filter handling remains unresolved. Current OEM executable modification is downgraded by the established stock-identical executable comparison; that does not prove execution/timing of the uploaded kernel on silicon.

The final two-pass release is NOT qualified. Do not retry, extend timeouts, change baud settings, or execute another read on the vehicle in this run. Minimum useful next evidence is a separately authorized physical K-line waveform capture at ECU and adapter, correlated with this host exchange. It should distinguish an incomplete electrical transmission from a complete reply lost by the provider; if transmission stops at the ECU, investigate reset/NMI/watchdog/SCI behavior with appropriate instrumentation.

Exact API arguments, message/status records, durations, comparison bytes and hashes are in EVENT_DIFF.json. Raw sealed physical evidence is unchanged. Recovery OEM status is reported separately.
