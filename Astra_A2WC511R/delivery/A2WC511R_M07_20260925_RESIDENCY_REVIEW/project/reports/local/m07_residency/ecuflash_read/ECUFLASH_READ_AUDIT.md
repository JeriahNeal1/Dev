# ECUFlash Read audit for future exact-ROM acquisition

**FAIL to approve the installed ECUFlash Read path as an independently attested exact 1 MiB acquisition method.** This audit confirms a historical kernel-based read workflow and identifies concrete RAM effects. The exact installed kernel and complete host read/cleanup implementation remain unresolved. No application, provider, device or kernel was executed during this audit.

## Installed evidence

`C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe` is a validly signed Tactrix PE32 executable, 7,840,904 bytes, SHA-256 `5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115`. Its actual Windows FileVersion and ProductVersion are `1.44.0.4868`, while existing local logs identify the historical application banner as `1.44.4870`. These are distinct observations; their differing suffixes are not silently reconciled into a binary-to-history identity proof. The definitions for `read_sti05` and `A2WC511R` both select `sti05`, `SH7058`, and `subarudbw`; the target definition contains CALID `A2WC511R` and ECUID `2F12515306`.

The PE inventory exposes two ordinary imports, irregular sections with expanded virtual sizes, and entry VA `015D9000`. The follow-up static probe identified **Themida/Winlicense 1.XX–2.XX** through the official Detect It Easy signature database and a recovered `Themida` marker; the exact minor version is unknown. Its guarded byte-buffer transforms recovered a 4,096-byte first loader, independently cross-checked aPLib decompression of a 4,173,012-byte protection block, and decoded a further 28,672-byte arithmetic layer. These remain protection-loader bytes: the installed application Read path and exact embedded kernel have not been recovered. The next inspected code installs exception handlers and modifies saved contexts. See [the static extraction review](static_extraction/STATIC_EXTRACTION_REVIEW.md) and its hash-linked extraction manifest for transforms, inputs, outputs, negative controls and the precise remaining recovery work. No loose kernel, internal flash-method module or memory-model file was found in the installed distribution. No ECUFlash process was running. The program was not launched: existing logs show that startup can itself open the interface. Neither the provider DLL nor a substituted provider was loaded.

`inventory.json`, `installed_signature.json`, `installed_entry_disassembly.json` and `binary_boundaries.json` preserve the initial inventory. Their original packer uncertainty is superseded by `static_extraction/extraction_manifest.json` and the review above. Recovering loader bytes does not establish the hidden read-method control flow. No license mechanism or installed configuration was changed.

## What historical Read actually did

Two local logs independently record the same pattern: `ecuflash_log_20260726t174613.txt` and `ecuflash_log_20260818t120321.txt`. Each performs initialization, obtains ECUID `2F12515306`, requests a security seed and sends a key, then writes a kernel into ECU RAM. The log labels identify upload `[FFFF3000,FFFF4234)`: `0x1234` bytes (4,660), transferred as 36 blocks of 128 bytes plus 52 bytes. The running kernel identifies itself as `OpenECU Subaru SH7058 DUAL  Kernel V1.07`. Reported communication and flash-buffer capacities are 512 and 4,096 bytes.

Both then log exactly 1,200 read-area operations, each 512 bytes. Their union is:

| Half-open range | Explicitly logged read bytes |
|---|---:|
| `[000000,086000)` | 548,864 |
| `[0C0000,0CF000)` | 61,440 |
| `[0FF000,100000)` | 4,096 |
| Total | 614,400 |

No read-area operation is logged for `[086000,0C0000)` or `[0CF000,0FF000)`, totaling 434,176 bytes. A blank/CRC optimization is one possible explanation; it is an inference, not established implementation behavior. The logs contain neither raw response bytes nor enough coverage evidence to resolve this. The two preserved historical 1 MiB files `ECUFlashReadRaw(1).bin` and `ECUFlashReadRR(1).bin` contain only `FF` in those gaps, consistent with that explanation but not proof of exact live bytes. Their hashes are recorded separately and neither is asserted to be the current ECU image.

This is more capable than the withdrawn stock-A0 dump in one observable respect: kernel reads are logged for the low vectors and high tail that stock A0 masks. It still does not justify an exact-current-ROM claim for every byte. Saved length, repeated hashes, CALID/ECUID and a checksum do not by themselves account for synthesized or skipped spans.

Neither read log contains flash-enable, erase-page or commit-flash events. A separate historical write log (`ecuflash_log_20260818t134942.txt`) does contain all three after the same kernel upload. This establishes a logged distinction between those operations; log absence is not a proof that no unlogged flash-register access or command occurred. The read logs end with interface-close entries. They do not prove a kernel-exit command, restored OEM RAM/peripherals, or automatic reset.

The machine-readable `historical_log_audit.json` retains exact log hashes, line numbers, read/upload geometry, and milestones while omitting unrelated device-identifying fields.

## Open-source reference, kept separate from installed ECUFlash

The local reference checkouts are read-only analytical inputs:

- [FastECU](https://github.com/miikasyvanen/FastECU/tree/d7198f1c47791e67738576015789ebc2d740e55e), commit `d7198f1c47791e67738576015789ebc2d740e55e`.
- [FastECU-kernels](https://github.com/miikasyvanen/FastECU-kernels/tree/d185a3e160a83e78425593c4c6450175bfa711e1), commit `d185a3e160a83e78425593c4c6450175bfa711e1`.
- [Subaru ECU flashing research](https://github.com/james-portman/subaru-ecu-flashing/tree/332a4858e2cc82f4d6131f4e94b633ced99a3a7b), commit `332a4858e2cc82f4d6131f4e94b633ced99a3a7b`; this describes an older OCP V0.21 kernel, so its command-response details are not substituted for DUAL V1.07.

In FastECU's `flash_ecu_subaru_denso_sh705x_kline.cpp`, `run()` uses a common bootloader-connect and kernel-upload path before distinguishing Read from Write/Test Write. The connect path performs SSM initialization, session/security operations, then programming-session entry. The upload path changes baud rate, loads/encrypts kernel bytes, uses services `34` and `36` to transfer RAM data, invokes routine `31 01 01`, and switches to kernel communication. The read loop builds kernel read-area requests and advances across the whole requested range. Write/Test Write instead enters `write_mem`; `init_flash_write` selects flash-enable or flash-disable, with buffer, erase and commit operations in the write path. The helper names and source call branches were inspected, but this alternative host implementation was not compiled, run or certified as a replacement.

These paths have different effects from OEM read-only logger requests. Kernel upload is a live ECU RAM write and changes execution context even when the intended final operation is Read. The source's success handler closes its dialog; it does not itself establish restoration of the original firmware execution state. Its supplied kernel binary also differs from the installed historical one.

The FastECU `ssmk_kline_sh7058.bin` reference is 6,056 bytes, SHA-256 `101fb08e033db71f68c69ecbd9a133b9abef91cd10127d706ae52f0b8c373aaf`, and identifies K-Line kernel v1.00. Actual SH-2E disassembly and guarded entry-byte analysis show it clears `[FFFF47A8,FFFF6CF8)`, 9,552 bytes, installs SP `FFFFBFFC`, then calls `FFFF3FE4`. The cleared interval contains all six requested TCU-state addresses. The binary main entry changes the interrupt mask and calls initialization before the command loop. This is positive evidence that a Read kernel can destroy the prior live diagnostic state; it is not a claim that DUAL V1.07 clears that same interval.

Current FastECU-kernels source separately initializes watchdog, peripheral and pin state, including flash-write-enable preparation, and has distinct flash command handlers. It has not been rebuilt and matched to either binary; its exact side effects cannot be attributed to the installed kernel. Thus even replacing ECUFlash with an open host tool would require a separately reviewed, hash-matched kernel and host path, rather than assuming Read means no state changes.

The reference binary entry proof has an exact-byte regression and a negative changed-byte guard in `binary_boundaries.py`. The unmodified SH compiler objdump produced `reference_kernel.disassembly.txt`. This branch added no emulator instructions and executed no kernel.

## Gate result and smallest missing evidence

| Obligation | Result |
|---|---|
| Installed target/method/host binary identity | PASS, bounded local inventory |
| Read uses temporary RAM upload rather than pure OEM SSM polling | PASS, historical logs |
| Exact installed kernel bytes and complete RAM/peripheral footprint | FAIL, unresolved |
| Read path excludes flash enable/erase/commit in all branches | FAIL, unresolved; log evidence only |
| Every one of 1 MiB returned from current ECU or validated under explicit exact coverage semantics | FAIL, 434,176 bytes lack read-area evidence |
| Kernel exit/reset and restored OEM execution after success/failure | FAIL, unresolved |
| Current physical ECU image attested | FAIL, no acquisition performed |

An approving audit needs either a vendor-supported exact-read mode with documented/recorded full coverage and kernel identity, or a separately reviewed host+kernel pair with complete command framing, response coverage, RAM/MMIO footprint, flash-operation exclusion and exit/reset behavior. The observed gaps cannot be closed by assuming they are unused or `FF`. No custom kernel or physical procedure is approved by this report.

## Conditional future single-connection workflow

This is dependency ordering for a later human session, not an executable or approved acquisition procedure. One physical adapter connection can contain separate software phases; it cannot make kernel execution and intact OEM-state logging simultaneous.

1. While OEM firmware is running, obtain timestamped read-only samples of `FFFF4C75`, `FFFF4C8D`, `FFFF4CA1`, `FFFF4C50`, `FFFF4BC1` and `FFFF4BC2`, plus ECUID/CALID under an independently validated logger path. Save the raw responses and label them pre-kernel. SSM polling sends requests but does not upload code or write the measured RAM.
2. Close that logger channel and keep exclusive adapter ownership. Proceed to a kernel-based ROM Read only after the FAIL obligations above are closed and the user has explicitly accepted the RAM upload/programming-session effects. Never use Write or Test Write to obtain a ROM, and never run concurrent logging against the kernel.
3. Save the untouched acquisition, per-range coverage and response evidence, exact tool/kernel identities and a cryptographic hash. Reject missing/synthesized spans unless the approved exact-read contract independently justifies them. Keep postprocessing/checksum repair outside the original capture.
4. Use the proven human-operated kernel-exit/reset procedure and verify OEM identity/communications before any further logger samples. Record any ignition transition separately. Post-reset samples are new observations and cannot recover the pre-kernel state.

No physical step was attempted, scheduled or automated. The frozen M0.6 files remain unchanged.
