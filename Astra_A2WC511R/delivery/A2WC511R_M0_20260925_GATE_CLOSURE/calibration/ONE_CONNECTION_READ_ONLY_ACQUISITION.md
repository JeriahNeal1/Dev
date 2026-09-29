# One future physical connection: current ROM and six TCU bytes

**Prepared for a human-run acquisition; not executed in this engineering run.** This reads the existing ECU without installing M0. ROM/RAM allocation approval is not required to read the current stock/OEM diagnostic services. Success identifies the read image; it does not approve a calibration, prove TCU freshness or authorize flashing.

The prepared collector uses the installed native RomRaider SSM protocol with a strict command/address filter: BF identification, A0 reads confined to[000000,100000), and A8 reads of exactly the six reviewed RAM addresses. It rejects write/reset/break/kernel-upload commands and has no automatic alternative transport. The registered32-bit OpenPort provider and32-bit Java are hash-checked; their installation is unchanged. The source, classpath manifest and virtual tests are linked by `interfaces/interface_gate_status.json`.

## Minimal procedure

1. Use the current ECU in a secured, engine-off setup with stable power sufficient for a long read. Keep other ECUFlash/logger applications closed. Record which ECU is connected, the operator, UTC time, ignition/startup state and any known changes since the previous flash. Connect the existing OpenPort once. At4800baud, two full1MiB SSM reads take roughly80minutes including protocol overhead; the exact duration is transport-dependent.
2. From C:\Dev, the operator invokes the reviewed script below. This explicit physical mode is the future bench action. Use a new output directory; preserve an aborted run and choose a new suffix for a retry.

```powershell
& 'C:\Dev\Astra_A2WC511R\integrations\romraider\virtual\Invoke-ReadOnlySSM.ps1' `
  -Mode PhysicalJ2534 `
  -OutputDirectory 'C:\Dev\Astra_A2WC511R\work\acquisition\one_connection_readonly_01' `
  -AcknowledgeReadOnlyPhysicalConnection
```

3. The collector checks ECU identity 2F12515306 and an A2WC511R pilot read, collects 60 consecutive six-channel samples, reads the complete ROM twice with 70 samples interleaved per pass, and collects 60 final samples. All 260 samples retain phase, index, UTC and monotonic host time. Keep the same physical connection throughout. It validates response framing/checksums, payload lengths, the full-image identities and matching SHA256 hashes. Retain both image files, raw samples, acquisition result and console log together. No edited/checksum-corrected replacement should overwrite either acquired image.
4. End only after the collector reports a successful identical two-image acquisition and the expected CALID/ECUID. Record that no flash occurred during or after the read. Disconnect normally. The two acquired hashes and the operator's physical-ECU note become the current-image evidence for a later offline comparison against the historical inventory and stock. Any subsequent flash invalidates that identity for a new candidate.

## Six pending channels

| Physical RAM | SSM address | Meaning retained in the evidence |
|---|---|---|
| FFFF4C75 | FF4C75 | Packed source byte |
| FFFF4C8D | FF4C8D | Packed snapshot byte |
| FFFF4CA1 | FF4CA1 | Update validity latch; global freshness unproved |
| FFFF4C50 | FF4C50 | Whole status byte; bit02 has only the supported local prerequisite meaning |
| FFFF4BC1 | FF4BC1 | OEM decoded upper-nibble target/range |
| FFFF4BC2 | FF4BC2 | OEM decoded lower-nibble current/range |

Keep raw values and host request/response timing; label observed startup and communication states. The collector does not command gear changes, throttle, brakes, RPM, actuators or TCU faults. A normal engine-off trace supplies the missing synchronized channel set but cannot establish stale/fault semantics. If a qualified bench session also provides an independently controlled, documented TCU-communication state, retain the same read-only connection and label that phase. Otherwise fault-state validity remains a separate **PHYSICAL/BENCH REQUIRED** gate; do not manufacture it from constant bytes, sample counters or packed11.

## Abort boundary

Actual A2WC511R acceptance of the full A0 ROM range is unproven until this physical run. A denied/unsupported range, timeout, missing echo, invalid reply, unexpected identity, partial read, changed tool/provider hash or unequal full reads must stop the acquisition with failure evidence. An incomplete directory is not a current-ROM attestation. Do not switch automatically to another command or provider.

ECUFlash's historical **Read** operation uploaded a temporary RAM kernel atFFFF3000. Therefore it is not the zero-commanded-RAM-write route specified here, even though it reads rather than programs flash. This procedure does not invoke that operation, Write, Test Write, erase, recovery, B0/B8 RAM writes or reset. If pure SSM A0 is unsupported, the bench result is a precise protocol blocker requiring a separately reviewed acquisition method; no fallback is silently authorized.
