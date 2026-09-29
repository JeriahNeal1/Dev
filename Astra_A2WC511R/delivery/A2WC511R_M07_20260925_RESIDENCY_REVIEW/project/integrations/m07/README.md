# M0.7 host observations

This is the supported host-only diagnostic path. It sends one ordinary, one-shot
OEM A8 read of six existing bytes and computes explanatory predicates on the
host. It needs no ECU patch, allocated ECU RAM, periodic task, or custom ECU
command. The supplied backends are **offline only**: finite replay of executed
stock-ROM fixtures, and the actual installed RomRaider encoder/parser connected
to those fixtures in an isolated JVM. There is no physical transport option.

From `C:\Dev`, capture all eight reviewed virtual scenarios with either command:

```powershell
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\capture.py --backend replay --output C:\Dev\Astra_A2WC511R\reports\local\m07_residency\host\my_replay.jsonl
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\capture.py --backend native-virtual --output C:\Dev\Astra_A2WC511R\reports\local\m07_residency\host\my_native.jsonl
```

Choose a new output filename each time; existing output is never replaced. An
optional `--count 1` through `--count 8` limits the finite capture. The default
exchange deadline is 1000 ms (`--timeout-ms 1..60000`); `--interval-ms 0..60000`
adds host pacing between samples. Neither setting models ECU scheduling or data
age. Exhausted fixtures are not repeated or cached. Exit code 0 means a completed
offline capture, 1 a terminal runtime/cleanup failure, and 2 rejected configuration.

The exact request is:

```text
80 10 F0 14 A8 00 FF 4C 75 FF 4C 8D FF 4C A1 FF 4C 50 FF 4B C1 FF 4B C2 72
```

Only those bytes are admitted; the transport API does not accept arbitrary
addresses, continuous polling, writes, resets, A0, or a custom BE command. The
reply must follow the exact request echo and be `80 F0 10 07 E8`, six payload
bytes, and the correct additive checksum. A sample preserves both complete
frames. One client permits only one outstanding request. Any malformed reply,
transport failure, or deadline expiry faults the client permanently and aborts
its owned transport; no retry or fallback occurs. Late worker results cannot
become samples. Concurrent capture/close calls are rejected while a capture is
outstanding. The native backend kills and waits for its own child on cleanup.

| Field | Existing OEM address |
|---|---|
| `source` | `FFFF4C75` |
| `snapshot` | `FFFF4C8D` |
| `latch` | `FFFF4CA1` |
| `flags` | `FFFF4C50` |
| `oem_target` | `FFFF4BC1` |
| `oem_current` | `FFFF4BC2` |

JSONL begins with `capture_start`, contains one `sample` per completed request,
and ends with `capture_end`. A runtime failure also adds `capture_failure`.
Every sample includes named/raw-by-address values, raw hex, source frames,
fixture provenance, UTC request/response times, monotonic nanosecond times, and
host elapsed time. Host sample indexes and timestamps are local observations;
they are not ECU counters or proof of freshness. All six bytes arrive in one
reply but the OEM reads them sequentially, so atomic coherence is unproven.

Host predicates expose source/snapshot equality, latch equal to one, flags bit
`02`, snapshot equal to `11`, both actual OEM target/current bytes equal to one,
and snapshot nibbles above eight. `reason_mask` preserves the M0.6 observational
convention: bit `01` means snapshot differs from `11`; bit `02` means either OEM
target or current differs from one; bit `04` means a snapshot nibble exceeds
eight; bit `80` is always set because freshness/coherence are unproven. Other
bits are zero. These predicates do not establish eligibility, physical gear,
fault validity, or control authority.

The native path uses the installed RomRaider `SSMProtocol` encoder and response
parser with a new in-memory `ConnectionManager`. Its explicit classpath contains
only the new endpoint JAR, installed RomRaider JAR, and existing bridge JAR. It
does not instantiate a connection factory, serial port, J2534 manager, or
provider. The child inherits no Java command-line injection environment variables;
the parent environment is unchanged. The profile pins inputs and the explicit
runtime files. It is a local build profile, not a signed trust boundary against
someone deliberately replacing the profile itself.

The eight fixtures execute the unchanged stock ROM's receive/parser/classifier/
A8 response/transmit path from `47E24`. The harness initializes virtual RAM and
supplies explicit SCI-ready events. The first response byte is released from the
OEM-built FIFO by the harness; remaining bytes are actual OEM TDR writes. Echo,
electrical timing, interrupts, and physical telemetry are not proved. Replay is
labelled as virtual in every capture.

To regenerate local fixtures/profile and run regressions:

```powershell
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\generate_stock_fixture.py
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\build_native.py
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\test_host_service.py
```

The build requires the already-installed Java compiler and RomRaider Java
runtime paths recorded in `build_native.py`. Regeneration updates only M0.7
fixture/profile/build files; it does not modify RomRaider, the frozen M0.6
package, the sealed physical collector, simulator core, or stock ROM.

Full-ROM A0 attestation remains withdrawn. The OEM substitutes bytes in parts
of its address space, so two identical one-megabyte responses plus CALID do not
prove an exact current image. See
`reports/local/m06_architecture/protocol/ACQUISITION_COVERAGE_ADVISORY.md`.
This service has no ROM-dump or image-attestation command. Physical transport
and live data validity remain deferred; they are not needed to use these offline
backends or validate the supported host architecture.
