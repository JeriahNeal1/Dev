# Current ROM and RK03 transition run

The requested scope is complete. **RK03_TRANSITION_PHYSICAL = PASS** and **OEM_RETURN_AFTER_TRANSITION_PROBE = PASS**. The transition probe ran exactly once, returned `80 F0 10 07 C3 00 00 FF 00 FF 00 48` after `83 00`, and completed explicit filter/channel/provider cleanup. The subsequent normal-mode passive observer confirmed BF identity `2F12515306` and 120 samples of six variables with PASS_CAPTURE_ONLY and clean observer/broker/provider exit.

Reproducing the reviewed ECUFlash-style explicit serial initialization and broad filtering restored successful progression through `83 00` in this session. No individual change is claimed uniquely causal. Both requested and effective initial values were `PARITY=0`, `P1_MAX=1`, `P3_MIN=0`, `P4_MIN=0` and `LOOPBACK=0`. The broad PASS filter used four zero bytes in mask, pattern and a nonnull flow object. Full arguments and timing are preserved in the physical journal.

The separate offline continuation passed **127/127** cases and two identical clean builds. Executable SHA256: `e16d47a1d7fda7058016cf0f392aca1b64d1a6077353185eda8d3bb33ed68c86`. Branch `rk03/post-transition-offline`, commit `2a8eeee2a7ff251346314c54d6dd028f6df93766`. Independent native and runner reviews passed. It has only a static fake backend and stops after the first 128-byte `36` acknowledgment; no full physical acquisition was performed or qualified.

The continuation checks 16 OEM-derived seed vectors, exact later ACKs, 200/100/200 ms virtual waits, the 15625 baud SET, TX/RX queue clears, one `34` and the first fixed encrypted chunk. Actual stock/current instruction replay independently confirms that one `34` suffices at the tested admitted loader boundary and that the first chunk yields `76` and 32 correct decrypted stores. Virtual timing and supplied peripheral/admission inputs do not establish later physical behavior. A failed `36` may already have changed RAM; the host does not retry.

**CURRENT PHYSICAL ECU IMAGE: calibration differs from stock; executable code identical to stock.**

- Designation: CURRENT_PHYSICAL_CAPTURE, not factory stock.
- SHA256: `bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2`
- Size: 1,048,576 bytes; CAL ID: A2WC511R; ECU ID: 2F12515306; Subaru checksum: PASS.
- Exact stock baseline SHA256: `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`.
- 1,856 changed bytes in 517 ranges: 1765 table, 62 axis, 21 scalar, 4 checksum, 4 metadata; 0 changed executable instructions/functions and 0 unknown ranges.
- Exact historical match: `AdjustedBaseTimingANDNOCLOLD.bin`. Direct current.bin bytes remain authoritative.

The latest successful ECUFlash log is preserved and associated by exact saved path, size and timestamp. Its raw 81/83 bytes and session-time provider hash are not exposed. API 04.04 and firmware 1.17.4877 match the probe; full DLL build strings differ (:31 in ECUFlash logs, :05 from the probe). The saved 1 MiB file is authoritative for analysis, while the application log does not prove every saved byte crossed the bus.

Earlier component gates and voltage reports remain historical evidence. The operator explicitly replaced those gates with IGNITION OFF / TEST MODE ON / NORMAL MODE ON. OEM return followed the exact NORMAL MODE ON reply. No measured vehicle-side power-loss assertion is made. The software interlocks and one-shot limit remain in force, and no further physical operation is authorized here.

Reports:

- [Current ROM detail](../CURRENT_ROM_STATUS.md)
- [Current/August/RK02/physical-probe comparison](../physical_probe_comparison/PHYSICAL_TRANSITION_COMPARISON.md)
- [Physical probe result](../physical_probe_result/PHYSICAL_RESULT.md)
- [Passive OEM return](../oem_return_after_probe_01/OEM_RETURN_RESULT.md)
- [Stock/current first-chunk instruction review](../post83_oem_review/OEM_POST83_REVIEW.md)
- [Offline continuation qualification](CONTINUATION_QUALIFICATION.json)

RK02 artifacts, failed RK02_VEHICLE_03 evidence, the original development/probe branches, current.bin and successful ECUFlash evidence remain unchanged. PRESERVATION_MANIFEST.json pins all verified inputs and final outputs. Full kernel upload/start, complete custom ROM acquisition and physical behavior beyond `83 00` remain separate future work.
