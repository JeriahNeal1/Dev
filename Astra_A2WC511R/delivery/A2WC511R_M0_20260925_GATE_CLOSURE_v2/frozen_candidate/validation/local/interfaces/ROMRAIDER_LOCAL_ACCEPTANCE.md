# Local native RomRaider acceptance — 2026-09-25

Result: read/snapshot, reversible preview, quantization, stale-state and native checksum-core acceptance passed against the actual installed RomRaider binary on an offline disposable A2WC511R copy. Persistent editor commits remain gated by the existing local confirmation workflow. This is not full GUI acceptance and does not authorize any vehicle operation or calibration change.

Session: `01a0da26-addc-7fe1-84df-8c0baa8174f8`.

## Actual installation and isolation

- Used `C:\Program Files\RomRaider\RomRaider.jar`, version 1.1.0 NOV26 2025 build 1227, SHA256 `43f0e92d652a5d2dde57fbe76ef99ff4f18c8147b0cbc20c0c4ccb33a7fe6635`.
- Runtime was its bundled Temurin Java 11.0.14.1+1, 64-bit. Bridge compilation used the existing Renesas Eclipse JDK 21.0.11 with `--release 8`; no runtime/dependency installation was required.
- No RomRaider/java/ECUFlash process was running when inventoried. The test opened only a native editor in its own process and closed it after each bounded run. No logger was created, and no serial/J2534/device API was invoked.
- The installed profile was copied to `work/romraider_acceptance/settings.xml`; native user level 1, locks and definition path were preserved. `user.home` was isolated and current directory was the acceptance workspace. Original program/user settings and original bridge JAR have restorable backups under `work/romraider_acceptance/backups`.
- ROM input was `work/romraider_acceptance/A2WC511R.disposable.bin`, copied from immutable baseline SHA256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`. All original ROM/profile/install hashes remained unchanged.
- Definition was the native installed profile's `C:\Dev\SubaruDefs\RomRaider\ecu\standard\ecu_defs.xml`; exact file/document hashes appear in inventory and snapshots.

## Observed results

`bridge_build_test.log`: 22 source-contract fixture assertions passed. `bridge_transport_test.log`: 11 real Java-agent HTTP/EDT transport assertions passed against fixtures. These are explicitly separate from actual installed-editor tests.

`native_http_status.json` and `native_http_snapshot.json` were captured through the real deployed Java agent attached to the installed native editor. `native_snapshot.json` was independently read through the same adapter using a provider for the actual native editor; no fixture classes were on that process's class path.

The native snapshot contains 488 table/axis records: 132 TableSwitch, 139 Table2D, 191 Table1D (including axes), 26 Table3D. It reports zero faulty or unsupported tables. All 6,059 nonstatic numeric cells/axes were compared with direct native `getBinValue`/`getRealValue` getters, including the native 3D `[x][y]` orientation. All match. Static axis labels were captured and excluded from numeric assertions. Coverage is the loaded A2WC511R definition; this does not claim other ROM layouts or masked/signed/swap variants absent from this definition.

`native_acceptance_results.json`: 16 actual installed-model assertions passed:

- Full 1 MiB buffer and exact baseline identity.
- Full snapshot agreement with native values.
- Native checksum detects a disposable perturbation and repairs a cloned buffer.
- Integer preview returns exact bytes matching a direct native setter, then restores the entire buffer.
- Direct native cell mutation makes the previous preview request stale; restoration returns the original hash.
- A second-cell clamp failure rolls back an earlier valid change.
- Fractional integer raw value with zero tolerance is rejected with full rollback.
- Wrong expected old cell, wrong model fingerprint and expired request are rejected without buffer mutation.
- A mixed integer-table/float-stored-axis batch previews successfully and rolls back completely, preserving native monotonic-axis rules.
- Read-only launch refuses commit before invoking the approval callback.
- Native `Rom.saveFile()` core's checksum/stamp experiment is restored completely.

The numeric example used one raw count in `Idle Speed Target A`; this was a disposable API encoding test, not a proposed idle-speed setting. The float axis example used `MAF Sensor Scaling::axis` through its native permitted axis setter. No numeric result from this test is a tuning recommendation. Exported buffers retain `NOT_FLASH_READY` in their names.

## Checksum and stamp evidence

The actual installed `RomChecksum.java` and native JAR agree. Native checksum metadata is at `0xFFB80`, size 168 bytes (14 descriptors). The only active descriptor is `(start=0x2000, end_parameter=0xFFAF7, correction=0x0C5824A8)`; the correction word is at `0xFFB88`. The other 13 records are disabled `(0,0,0x5AA5A55A)`.

The native loop sums big-endian 32-bit words with `i=start; i<end_parameter; i+=4`, modulo 2^32. Because this ROM's end parameter is unaligned, the final word begins at `0xFFAF4` and includes byte `0xFFAF7`: the effective covered byte interval is `[0x2000,0xFFAF8)`. The correction equals `0x5AA5A55A - sum` modulo 2^32. This distinction is enforced in the audit.

Baseline validates as 0 (all active checksums valid). A disposable XOR at `0x2100` validates as block 1 invalid. Native repair validates 0, with SHA256 `7c064c794338f8246ae70960c70f26e3ec77aa9d29f5060a8be24511c780ec07`. Independently implemented Python arithmetic produces exactly that repaired buffer. `checksum_audit.py` never writes its inputs and rejects a disabled first descriptor or changed descriptor geometry. The first-disabled guard matters because native validation returns -1 and treats all checksums disabled in that state.

Native `Rom.saveFile()` writes the four-byte `yyMMdd`/edit-count stamp at checksum table +204 = `[0xFFC4C,0xFFC50)`. On the untouched disposable baseline its only change was `FFFFFFFF -> 26092501`; checksum remains valid because the stamp is outside coverage. This confirms the historical `26082301` stock-name variant is consistent with the native edit stamp. GUI Save As itself was not clicked.

`checksum_audit.json` also verifies both named baseline variants and the three actual desktop tuning binaries have valid enabled checksum geometry; validity does not establish calibration suitability or current flash identity. SharpTune's local `ChecksumSubaruDBW` only returns the name `subarudbw`. The actual ECUFlash proprietary checksum module was not invoked. The available native RomRaider arithmetic and exact binary match provide the tested offline checksum workflow.

## Local log/calibration inventory and remaining human evidence

`local_inventory.json` inventories C:\Tuning, C:\Dev\SubaruRoms and the user's Desktop, with hashes, sizes, times and CSV headers/row counts. User Documents/Downloads/AppData and hidden .RomRaider profiles were also searched to locate the active configuration and other evidence paths. Twenty actual CSVs were found in `C:\Tuning\Logger\Output`. Newest is `romraiderlog_20260824_143124.csv`, 6,453 rows, SHA256 `ccbf129cdb36867c5c0bfdfed8571cc8350f6a988d3941dc8951c826179e380b`; its channels are packed/decoded gear state, RPM/speed and BC0/BC3. No subsequent requested freshness/status six-channel trace was found in the searched local tuning locations. Existing logs do not prove communication-fault behavior.

Desktop `ECUFlashReadRaw.bin` SHA256 is `1aac3214ec276822f1343e66fc1b8af83be8e61866d2d182882beb88317b4920`; `REV3Map.bin` is `d2dc34e1b21985c89b49996c9dedd88494c90c65e2da0c0a735d31d54ca92171`; `AdjustedBaseTimingANDNOCLOLD.bin` is `bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2`. Names and times do not prove which is currently installed in the ECU. A human-confirmed current read-back/hash and installed-hardware calibration review remain required before recommending a running-car candidate.

Remaining RomRaider acceptance is a human confirmation/display workflow: positively approve one disposable batch, cancel another, inspect visible tables/aliases/compare/undo, and reopen an exported copy through the UI. No automation bypassed the required local YES/NO. Post-approval stale checks are source/fixture tested; they have not been induced inside a real human approval dialog. These GUI checks do not block unrelated offline compilation or checksum review.

## Reproduction and changes

Build/test command: `tools\Build-RomRaiderBridge.ps1 -JdkBin <existing Renesas JDK bin> -RunModelTests`. Transport smoke: set `JAVA_EXE` to the installed RR Java and execute `tests\agent_transport_smoke.py`. Exact native process command is in `native_command.txt`; invoke `work\romraider_acceptance\run_native.py` after compiling `NativeAcceptance.java` as recorded in that workspace. Run `reports\local\interfaces\checksum_audit.py` for independent checksum validation.

Changed host artifacts: source-built bridge JAR, bridge build classes/manifest/test classes, isolated acceptance profile/classes/scripts/disposable ROM, report/export files, and ACL-restricted `.runtime/romraider_acceptance` session connection configuration. Bridge source itself needed no compatibility change. No user program/profile, ECU definition, original ROM, driver/provider or vehicle artifact was overwritten. Initial native test's guessed table name was corrected to the actual loaded name; the failure log is retained separately. Final program/install hashes and artifact hashes are in `verification_manifest.json`.
