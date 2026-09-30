# Stock ECU 81 -> 83 00 transition: independent offline findings

## Conclusion

The verified A2WC511R stock firmware supports the exact request `80 10 F0 02 83 00 05` after `80 10 F0 01 81 02` and produces the exact positive reply `80 F0 10 07 C3 00 00 FF 00 FF 00 48`. It is not an intentionally silent baud transition in this stock implementation. Request and response lengths/checksums used by RK02 are correct for this implementation. The missing physical reply therefore is not explained by an intrinsically unsupported `83 00`, a stock no-reply rule, or a baud switch implemented by that handler.

This is a statement about verified stock SHA256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`, not the currently installed, previously edited vehicle ROM. No current ROM was acquired. A matching BF ID and C1 EF 8F reply do not prove executable-code equality.

## Direct stock instruction evidence

- `0x47132` accepts the `80` frame prefix, destination `10` or `12`, and tester `F0`; it calls KWP dispatch `0x476E0` and serializer setup `0x4735C` only after the receive parser's checksum comparison at `0x47FC8..0x47FD8`.
- Dispatcher `0x4770E..0x47714`, `0x47750..0x47756` recognizes opcode `83`, sets response-kind bit `04`, and calls validator `0x473F0`.
- Validator `0x473F0..0x47436` requires payload length exactly 2, communication-session RAM `FFFF63E1` bit `20` set, and request subfunction byte at `FFFF640D` equal to zero. It selects opcode C3 and payload length 7. A missing session or nonzero subfunction selects negative response `7F 83 10`, rather than intentionally suppressing a reply.
- Valid `81` reply producer `0x477DE..0x477FA` writes EF 8F, clears two communication counters, and sets `FFFF63E1` bit `20`. This update occurs while serializing the response body, before the final C1-frame checksum is emitted.
- `83` reply producer `0x477FC..0x47828` writes the fixed body `00 00 FF 00 FF 00` in two buffer portions. It contains no baud-register, protocol-selector, board-pin, or Test Mode read/write. The validator likewise contains no Test Mode gate.
- The later `10 85 02` request has a separate validator at `0x47634` and sets response-kind bit `10`. The final-response hook at `0x4717E` takes the boot transition only when that bit is set. `83` uses bit `04`, so this boot/baud change is not entered by `83 00`.

Disassembly copied from the exact stock bytes is `oem_transition_stock_47108_48240.asm`. Literal pools appear as pseudo-instructions in objdump output; only the stated reachable code ranges are interpreted as code. Existing IDA extraction `BOOT_KWP_IDA_FUNCTIONS.json` independently names the same functions.

## Receive and echo behavior omitted from the old wire harness

The actual receive handler `0x47E24` reads SCI2 RDR at `FFFFF015`, captures/clears receive errors from SSR `FFFFF014`, and resets transport state on an error. If `FFFF649A` bit `20` is set, it compares the received byte with the expected self-echo at `FFFF63F9`. An exact echo advances the actual serializer at `0x4808C`; a mismatch invokes `0x47ECC` and `0x47230`. With that bit clear, the handler dispatches the actual request parser at `0x47F20`.

The retained `verify_kwp_wire.py` injects bytes directly into parser RAM and manually advances the serializer. It does not execute this RDR/error/self-echo admission path. It also explicitly begins first-byte transmission at `0x47DEE`, after assuming the periodic counter has reached 3. It therefore proves payload/framing/state logic, but does not prove electrical timing or interrupt scheduling.

The new analysis-only `oem_transition_replay.py` now feeds both request frames and every response self-echo through the real `0x47E24` handler. It executes 4,322 instructions for normal echo, obtaining exactly C1 EF 8F followed by C3 00 00 FF 00 FF 00. A 4,330-instruction negative variant corrupts the final C1 self-echo; the stock reset still permits the following `83 00` under the supplied boundary conditions. Consequently, a simple final-C1-echo mismatch alone is not a reproduced explanation for this physical failure.

The new replay observes writes only to the permitted stock communication RAM/stack and SCI SCR/TDR/SSR on this transition. It observes no SMR (`FFFFF010`), BRR (`FFFFF011`), or SDCR (`FFFFF016`) write. It is fully offline; no real provider is imported or loaded, and no qualified source/binary or physical-session evidence is modified.

## Timing and remaining limits

Periodic routine `0x47D94` increments `FFFF63F6`; reaching at least 8 invokes reset paths. It also increments the pending reply counter `FFFF6400` and starts the first response byte at value 3 (`0x47DE4..0x47DF4`). Every actual receive handler resets `FFFF63F6` at `0x47E48..0x47E4C`. The units depend on the periodic caller schedule. This analysis does not invent milliseconds from those counter values.

The additional `oem_transition_gap_replay.py` executes that complete periodic routine as well as the actual RXI/parser/echo path. After completing a valid81 transaction, it inserts 0, 7, 8, or 9 periodic calls between the first byte `80` and second byte `10` of the valid83 frame. At 0 and 7 calls the exact C3 reply is produced. At 8 and 9 calls the receive cursor resets to zero and the remainder of the exact same request produces no reply, while communication-session bit20 remains set. All four cases pass their explicit assertions. This independently reproduces a mechanism for no reply from excessive interbyte spacing, without changing baud or requiring missing Test Mode. It does not prove that the installed provider imposed that spacing, that a nominal5ms delay crosses eight ticks, or that this was the physical root cause.

This second replay runs full47D94 including its three-tick first-response starter, so it removes the first-TDR fragment assumption for these four cases. It supplies SR390 so the existing reviewed3AF4/3B08 path preserves a nonzero interrupt mask; the scheduler descriptor and asynchronous preemption still are not modeled. The periodic caller chain is `64A4 -> call6542 -> 470A6 -> 47C66 -> 47D94`, with the entry64A4 in the stock task descriptor at4948. Resolving its actual timebase is separate work; no elapsed-time guarantee is inferred from the descriptor alone.

The successful81 producer does not select a different receive parser or tighten this eight-tick interbyte threshold. The session bit it sets is checked by83's validator, but not by the eight-tick transport guard. The same receive path/guard applies before and after81. Thus a proposed uniform fatal interbyte delay needs an explanation for81's preceding success; the mere presence of a nominal provider default cannot prove that explanation. Scheduler phase, a differing actual gap, and the extra byte in83's seven-byte frame are possible variables, not demonstrated causes. No inspected hard guard imposes a special new81-to83 maximum delay; the demonstrated counter resets framing while retaining the communication-session bit.

A bounded follow-up traced task entry64A4 to descriptor index7 (`48D8 + 7*16 = 4948`) and the RTOS descriptor constructor at3930. The descriptor contains control/priority/stack/entry data, not a proven standalone milliseconds period. Establishing the task release source, clock divisor, and actual dispatch latency would require a wider RTOS/timer contract than the retained qualification covers. The present result therefore deliberately leaves tick duration unknown.

The new replay retains explicit error-free/ready SCI status and a first-TDR scheduling boundary. It does not establish physical UART speed, interbyte gaps, delayed/missing ECU self-echo, asynchronous interrupts, adapter buffering, or current-vehicle executable compatibility. These remain distinct from its exact instruction/byte conclusions. A live no-reply observation cannot by itself distinguish ECU rejection, incomplete/incorrect electrical transmission, missed receive data, or a host/provider contract mismatch.

The physical trace's sequence 8 C1 read-return to sequence 9 `83` write-return is 77.0782 ms using its performance-counter frequency. This is API completion-to-completion elapsed time, not the measured bus idle interval. The record does not expose the write call's entry time or the adapter's actual transmit timestamps.

## Evidence hashes

Paths below are under `C:\Dev\A2WC511R_ReadKernel\evidence\contracts` unless otherwise specified.

| Evidence | SHA256 |
|---|---|
| `C:\Dev\SubaruRoms\OEM\A2WC511R.bin` | `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218` |
| `KWP_WIRE_CONTRACT.json` | `118b7f5e9537ac1e1700b67ce16799d8d357692c84ab80fd42dffdca207c23a2` |
| `KWP_WIRE_TRACE.json.gz` | `6c1e03791eb1e52bb4d3efa5def5c956bf098d36e7cf915c6bf1a75f9623edff` |
| `KWP_PRODUCER_REGRESSIONS.json` | `9bc39da629507ecfe76ec4c76e6d6efdaee6745480c506ac1fd5c4edae2cdbfe` |
| `BOOT_KWP_IDA_FUNCTIONS.json` | `95299c5b97bc0f4c7b3f0447ca95fc1d09dceb9529742afb07176f03b9a96332` |
| Local `oem_transition_stock_47108_48240.asm` | `ab609533fcc0bb82b9688323b075fa8d86c09a4cd8204d0d6d081052569b269b` |
| Local `oem_transition_rx_isr_replay.json` | `9d40dc870ae88da586aa60ce1c9d3e37011e691e116820feddbea8bdc11599be` |

`oem_transition_evidence.json` contains canonical file pins, exact frames, checksums and scoped conclusions. `oem_transition_rx_isr_replay.json` additionally pins the new source, trace, and reused imports. The replay's first development execution hit its fixture guard because its intentionally bounded first-byte fragment left `memory.pc` set; clearing it between independent harness invocations corrected this analysis harness only. The final execution completed both cases. This is not a discovered RK02 production defect.
