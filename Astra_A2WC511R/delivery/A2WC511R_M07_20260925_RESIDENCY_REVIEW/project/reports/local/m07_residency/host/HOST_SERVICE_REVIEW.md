# M0.7 supported host diagnostic service

**PASS for the implemented offline host service.** One unchanged native OEM A8
request returns all six reviewed bytes, which the host records and explains.
No ECU patch, added ECU state, periodic ECU task, physical provider, or vehicle
connection is involved. The supported artifact is
`integrations/m07/capture.py`; usage and field semantics are in that directory's
`README.md`. M0.6 artifacts and the sealed collector were not modified.

The final request is
`8010F014A800FF4C75FF4C8DFF4CA1FF4C50FF4BC1FF4BC272`. Its control byte is zero
(one-shot). The six values are source, snapshot, latch, flags, actual OEM target,
and actual OEM current, in that order. The six-byte E8 reply is parsed only after
an exact request echo, direction/header/length validation, and checksum
validation. Every other request is rejected before the backend exchange.

`stock_six_a8_fixtures.json` contains eight scenarios executed through the
unchanged stock ROM (`22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`).
The stock receive entry `47E24`, parser, classifier, A8 payload production, and
transmit/echo handling run in the existing SH-2E interpreter. All returned raw
bytes equal the explicitly initialized scenario bytes. The request remains
unchanged during each response transmission. Full memory events and actual TDR
writes are retained, and fixture loading checks their hashes and reply equality.
Fixture SHA256:
`1d6b4d789c74caee36506e3d831207f3d2039b1a3a9f584d6acff2d7498664fb`.

This is a bounded instruction-level experiment. SCI readiness, raw inputs, and
host echo are virtual. The harness releases the first response byte from the
OEM-built FIFO; later response bytes are actual OEM TDR writes. It does not
model electrical timing, timers, interrupts, telemetry, or concurrent OEM data
updates. Six bytes in one response do not prove an atomic snapshot or data age.

The `native-virtual` backend constructs that request and parses every response
using the actual installed RomRaider SSMProtocol in an isolated Java process.
Its custom in-memory ConnectionManager enforces exactly that one-shot request.
Only three explicit JARs are on the classpath; JNA/provider libraries and
physical factories are not used. The endpoint JAR SHA256 is
`246e4ea0eb00773f06c733bfb06caf53ee6315b1167a785bf8d80f3738f4ba21`.
The local profile pins the fixture, ROM, Java executable, and all three JARs;
runtime hash failure is rejected before starting Java. The profile is not a
signed defense against deliberate replacement of the profile itself.

Both final JSONL captures contain eight validated samples and terminate with
`PASS_OFFLINE_CAPTURE`, with no abort or cleanup errors:
`capture_replay_final.jsonl` and `capture_native_final.jsonl`. Their raw values,
predicates, and reason masks agree exactly. Each sample has UTC and monotonic
request/response timestamps, elapsed host time, raw-by-name/address values, both
wire frames, and provenance. Reason bit `80` is always set. There is no inferred
physical gear, eligibility, freshness, or pair/snapshot coherence.

Fifteen regression groups pass in `host_service_tests.log`: all single-byte
request mutations, frame/echo/checksum rejection, all 65,536 OEM target/current
pairs and 256 snapshot values, timestamps, one outstanding request, concurrent
close rejection, parser failure, bounded timeout and discarded late result,
terminal/no-retry behavior, retained abort/constructor/cleanup failures, finite
replay, exact native parity, hash rejection before process creation, actual owned
JVM abort/wait/stream cleanup, and output/no-physical-backend constraints. The
Windows lifetime test disposes its Popen object before deleting its temporary
log, because the retained process handle can delay file release after exit.

Exact final validation commands (working directory `C:\Dev`):

```powershell
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\generate_stock_fixture.py
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\build_native.py
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\test_host_service.py
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\capture.py --backend replay --output C:\Dev\Astra_A2WC511R\reports\local\m07_residency\host\capture_replay_final.jsonl
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\capture.py --backend native-virtual --output C:\Dev\Astra_A2WC511R\reports\local\m07_residency\host\capture_native_final.jsonl
py -3 -B C:\Dev\Astra_A2WC511R\integrations\m07\verify_evidence.py
```

Use new output names when rerunning captures. Regeneration updates M0.7 files
only; timestamps in fixtures/captures and JAR entry timestamps make their full
file hashes specific to the recorded build/run. `host_evidence_manifest.json`
pins the final tested files, dependencies, and captures. No global installation
or configuration was changed. New source lives under `integrations/m07`, build
output under `work/m07_host`, and evidence under this directory.

Full-ROM A0 attestation remains **FAIL/WITHDRAWN**: OEM masking means two equal
one-megabyte responses and matching CALID can differ from the actual ROM. The
frozen M0.6 advisory remains authoritative for that defect; the M0.7 service has
no full-ROM reader. No additional passive RAM address is needed for these six
observations. Physical capture and live validity/fault semantics remain deferred
and unproved; this result does not revive the withdrawn acquisition procedure.
