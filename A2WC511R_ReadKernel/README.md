# A2WC511R temporary RAM acquisition tool

Artifact class: **TEMP_RAM_ACQUISITION_TOOL**. This is a separate SH-2E / SH7058, big-endian RAM program and fixed-purpose host acquisition stack. It is not MerpMod and must never be combined with a 1MiB ECU flash image. No real provider or vehicle operation is part of the offline commands below.

RK01 is permanently **SUPERSEDED_NOT_FOR_HARDWARE**. Its source snapshot and failed self-echo evidence remain unchanged.

The kernel uploads at `FFFF3000` and enters at `FFFF3004`. The RK02 1,808-byte object has SHA256 `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581`. Its total temporary RAM takeover is `[FFFF3000, FFFF3730)`: uploaded code/constants/vectors/integrity word followed by 32 bytes for receive storage, canaries, and an exception stack. It neither calls OEM routines nor reads inherited OEM RAM. It deliberately stops DMA and the on-chip watchdog, installs private CPU state/vectors, and initializes documented SCI2 state. Remaining hardware and entry assumptions, with the corrected RK02 SCI sequence, are enumerated in `evidence/rk02/ENTRY_PERIPHERAL_CONTRACT.json`. The earlier contract is preserved unchanged as historical RK01 evidence.

The only accepted requests are one fixed identity request and exactly two ascending passes of 512-byte raw reads covering `[000000,100000)`. The response echoes its page address and pass number. It has no CRC page replacement, flash operation, arbitrary memory access, RAM poke, or caller-selected entry point. Bad input terminates communication; partial input waits for the host deadline and subsequent power-cycle exit. There is no return into overwritten OEM RAM.

Rebuild into a **new** directory:

```powershell
py -3.14 -B C:\Dev\A2WC511R_ReadKernel\tools\build_checked.py unique_build_name
```

The checked builder enforces the exact independently reviewed instruction/store contract after compilation. A changed binary fails that guard and requires a new review; compilation alone does not qualify it. The unguarded build driver is a development component.

Verify the two reviewed build objects and byte-level layout:

```powershell
py -3.14 -B C:\Dev\A2WC511R_ReadKernel\tools\artifact_review.py
```

Verify preserved source material without launching applications or providers:

```powershell
py -3.14 -B C:\Dev\A2WC511R_ReadKernel\tools\preserve.py --verify
```

The prior ECUFlash exact-image rejection is permanent. Its FF-CRC collision counterexample remains evidence; it is not a fixture to be averaged away. DUAL1.07 is preserved solely as prior evidence and is not uploaded by this tool.

RK02 alternates receive-only SCR10 and transmit-only SCR20. It rejects pre-existing receive/error flags before TX, waits for final TEND with both transmit stages empty, then restores RX. The self-echo model records receive-start admission; a genuinely late new start fails closed. No modeled timing is a measured electrical delay.

The mandatory offline release check is:

```powershell
py -3.14 -B C:\Dev\A2WC511R_ReadKernel\tools\validate.py
```

Missing or changed evidence is FAIL. Software PASS with explicit physical gates is reported as CONDITIONAL. The final human-only procedure, when released, is `HUMAN_ACQUISITION_RK02.md`, bound by `RELEASE_CERTIFICATE.json` to the exact physical host and RK02 kernel. Final qualification and the procedure must be read with that validator report. Simulator timing does not certify silicon timing. Electrical behavior, real OpenPort behavior, actual ECU acceptance, external watchdog behavior, and verified power-loss/reset remain physical gates.
