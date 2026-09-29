# RK02: one human-operated acquisition-only session

Release class: **TEMP_RAM_ACQUISITION_TOOL**. Offline software is qualified; hardware remains **PHYSICAL_REQUIRED**. This procedure was prepared, not executed. It authorizes no flash Write, Test Write, erase, program, commit, persistent modification or active engine/transmission control. Installed ECUFlash Read, DUAL1.07 and RK01 are excluded.

## Fixed identities

| Item | Exact binding |
|---|---|
| RK02 kernel SHA256 | `3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581` |
| Kernel | 1808 bytes, SH-2E / SH7058, big endian |
| Upload / entry | `[FFFF3000,FFFF3710)` / `FFFF3004` |
| Total temporary takeover / private stack | `[FFFF3000,FFFF3730)` / `[FFFF371C,FFFF372C)` |
| Version | `A2WC511R-RK02` followed by NUL |
| ECU BF identity | `2F12515306` |
| Physical host SHA256 | `58d0867b85162e6fa4ccd3ac7fe0413c40e4054cbc416d12e39e29f926e60862` |
| Offline certificate SHA256 | `effd2cb9158f10a2a6ca517dae8390553392035b640af360dfbb923e1bab59d5` |
| Qualified fake host SHA256 | `4b681bcdb3c178b89382b37b207b4a7679f0a1e87ab13c7051e8cf8019c094ec` |
| Provider | `C:\Windows\SysWOW64\op20pt32.dll` |
| Provider SHA256 | `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf` |

`RELEASE_CERTIFICATE.json` binds this document, the exact physical executable, qualification index and checker. Preserve the whole project at its qualified paths. The executable accepts no provider, kernel, address or opcode selection. It embeds the RK02 bytes and certificate hash. Its real-provider path was only hashed during qualification; the executable has never been launched, including self-test.

## Before connecting

Use the actual stationary vehicle with engine OFF. Have its correct service procedure for diagnostic/programming-mode admission, stable electrical power and **verified ECU power-down/reset** available before starting. Confirm the physical conditions for the OEM RAM-loader session, supported SH7058 clock/SCI path and watchdog behavior. No connector jumper, pin meaning or numerical key-off interval is certified by this software package. If those conditions or the power-down method are unknown, stop before takeover; do not improvise wiring or assume a timed wait proves RAM loss. Disconnecting USB alone is not ECU reset.

Close ECUFlash, RomRaider and every other J2534 client. No concurrent client is allowed. Keep ignition off until the applicable service procedure calls for it; never start the engine during this session. Record operator, vehicle association, UTC, ignition events, power support and the chosen power-down verification method in the session notes. A matching BF identity does not by itself identify the current calibration or prove that a tuned image retained its stock loader.

Run this **offline-only** check first in PowerShell. Require exit code 0, `software_status: PASS`, overall `CONDITIONAL`, and only the documented physical gates. FAIL, missing data or changed hashes stop the session.

```powershell
py -3.14 -B C:\Dev\A2WC511R_ReadKernel\tools\validate.py --report C:\Dev\A2WC511R_ReadKernel\evidence\rk02\PRE_CONNECTION_VALIDATION.json
if ($LASTEXITCODE -ne 0) { throw 'RK02 qualification failed; do not connect or upload' }
```

The report filename is exclusive. If it already exists, retain it and choose a new report filename; never remove qualification evidence. Create a new acquisition folder and copy only the pinned executable. These commands are preparation and do not load a provider:

```powershell
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath 'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01') { throw 'Session path already exists; preserve it' }
New-Item -ItemType Directory -Path 'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01' | Out-Null
Copy-Item -LiteralPath 'C:\Dev\A2WC511R_ReadKernel\host\physical_build\rk02_physical_01\owned_physical_read32.exe' -Destination 'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\owned_physical_read32.exe'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\owned_physical_read32.exe').Hash.ToLowerInvariant() -ne '58d0867b85162e6fa4ccd3ac7fe0413c40e4054cbc416d12e39e29f926e60862') { throw 'Wrong acquisition executable' }
```

## Single connection and acquisition order

1. Connect the OpenPort according to the vehicle service procedure. Establish the documented ignition-on, engine-off diagnostic state. Do not open ECUFlash or another logger.
2. Obtain passive OEM **BF identity first**. The following fixed observer command performs BF before any A8 request and refuses an ECU identity other than `2F12515306`.
3. Capture the six fixed raw observations with their request/response timestamps and host reason predicates: `FFFF4C75`, `FFFF4C8D`, `FFFF4CA1`, `FFFF4C50`, `FFFF4BC1`, `FFFF4BC2`.

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\integrations\prehardware\capture.py --backend physical-j2534 --authorize-physical-read-only --count 120 --interval-ms 250 --output C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\pre_kernel_A8.jsonl
if ($LASTEXITCODE -ne 0) { throw 'Passive OEM capture failed; do not enter RAM session' }
```

4. Confirm `PASS_CAPTURE_ONLY`, 120 samples, null error/cleanup_error, expected BF identity, and that the observer and its broker have exited. Its raw observations are untouched OEM evidence; their reason predicates do not certify TCU freshness or fault coverage. Retain the JSONL and provider stderr file. Close the passive observer fully before continuing.
5. Enter the reviewed OEM RAM-upload session using **only** the fixed executable below. It repeats BF, performs the reviewed session/security sequence and fails on any unexpected reply. This is a temporary RAM takeover, not flash programming.
6. The same invocation uploads exactly the embedded, hash-pinned RK02 object to `[FFFF3000,FFFF3710)` in fixed reviewed chunks. No arbitrary upload is possible through its interface.
7. It starts exactly `FFFF3004` through the reviewed OEM start command.
8. It verifies the exact RK02 identity/version before accepting any ROM block.
9. It reads `[000000,100000)` twice, 2048 ascending 512-byte blocks per pass. Every response must match opcode, pass, address, size and checksum. There is no CRC-based page substitution.

Run the following **once**, manually. This is the first command in this document that performs temporary ECU RAM writes. `cmd.exe` redirection retains an ASCII/UTF-8-compatible native log instead of PowerShell 5 UTF-16 redirection. Keep the terminal until the process exits; do not launch it again on a failure.

```powershell
cmd.exe /d /c "C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\owned_physical_read32.exe --acquire-owned-readkernel --certificate-sha256 effd2cb9158f10a2a6ca517dae8390553392035b640af360dfbb923e1bab59d5 > C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\native.log 2>&1"
$acquisitionExit = $LASTEXITCODE
```

10. Require exit code 0 and `PASS_NATIVE_FIXED_PHYSICAL_TWO_FULL_READS` in `native.log`. The host compares every second-pass block with the first; both raw files must be exactly 1,048,576 bytes. Run the offline finalizer to replay the entire journal, verify the strict transmitted command sequence and actual received bytes, and require equal SHA256 hashes:

```powershell
if ($acquisitionExit -ne 0) { throw 'Terminal acquisition failure; follow the failure exit below' }
py -3.14 -B C:\Dev\A2WC511R_ReadKernel\host\finalize.py --physical-build rk02_physical_01 C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01
if ($LASTEXITCODE -ne 0) { throw 'Capture integrity failed; follow the failure exit below' }
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\finalized\raw_pass0.bin', 'C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\finalized\raw_pass1.bin'
```

11. Preserve both original `pass0.partial.bin` / `pass1.partial.bin`, `native_api.jsonl`, `native.log`, executable and the read-only finalized raw copies with `FINALIZATION.json`. Do not normalize checksums, fill gaps, edit, resave through a ROM editor or rename an incomplete result as the current ROM. The finalizer must report `PASS_RAW_CAPTURE_INTEGRITY`; its physical-session association deliberately remains unproved by software. Associate the real vehicle and capture using the operator notes plus pre/post BF records. Missing or unexpected A2WC511R identity literals are a reason for offline review, never correction of the raw capture.
12. Confirm transport close. On the successful path the last native API records are StopMsgFilter, Disconnect and Close; the process exits. The kernel stays in its private terminal state. Adapter close does not restart OEM software.
13. Turn ignition OFF and apply the pre-established vehicle-specific **verified power-down** method. Record actual evidence and elapsed interval. Do not substitute an arbitrary wait or USB removal for ECU power loss. Do not leave the vehicle in the RAM-kernel session.
14. Restore ignition ON, engine OFF, according to the service procedure. OEM reset must occur from ROM after RAM loss; no jump-back command is sent.
15. Verify fresh OEM BF identity `2F12515306` with the same passive-only observer. This also captures the optional six observations in step 16:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\integrations\prehardware\capture.py --backend physical-j2534 --authorize-physical-read-only --count 8 --interval-ms 250 --output C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_01\post_restart_A8.jsonl
if ($LASTEXITCODE -ne 0) { throw 'OEM return not confirmed; stop and follow the approved vehicle recovery procedure' }
```

16. Retain the optional eight post-restart six-channel snapshots and compare BF identity with the pre-kernel record. Require `PASS_CAPTURE_ONLY` and confirmed broker cleanup. This is an OEM-return check, not validation of engine/transmission outputs or any active feature.
17. Close all clients and disconnect OpenPort according to the vehicle procedure. Preserve the session folder and an independent backup of both raw images. Return to offline analysis; this procedure includes no vehicle firmware write.

## Failure exit

At the first identity, upload, start, version, read, checksum, transport or finalizer failure: preserve all partial files and journals, label the capture **INCOMPLETE_NOT_CURRENT_ROM**, and do not retry, re-upload, invoke another provider/tool or fall back to ECUFlash. The host stops issuing J2534 calls on a terminal fault. Its process exit releases host resources, but that is not a proved ECU reset or an explicitly successful provider Close. Confirm the client has exited, then use the pre-established ignition OFF/verified power-down/ON sequence and passive BF check. If OEM return is not confirmed, stop and use the vehicle's approved recovery process. No erase/program/reset opcode is an allowed recovery action here.

## Evidence this session can close

The session can associate two byte-identical, lossless raw captures with this actual ECU, record real provider/session acceptance, and demonstrate OEM BF return after independently verified power-down. It does not prove every silicon timing margin, arbitrary NMI/watchdog behavior, calibration safety, or firmware residency. Those physical claims must be recorded from actual observations; no software PASS is a substitute. Read-only file attributes and hash seals make alteration detectable; they are not WORM storage or a signature against a same-user attacker.
