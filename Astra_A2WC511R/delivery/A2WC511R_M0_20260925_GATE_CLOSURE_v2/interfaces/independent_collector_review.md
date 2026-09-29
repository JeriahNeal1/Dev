# Independent review of the prepared read-only SSM collector

**PASS for the reviewed offline command policy, local integrity guards and failure handling. Physical acquisition remains unvalidated.** No collector physical mode, serial connection, J2534 provider or device was opened by this review.

Final runtime manifest reviewed: SHA-256 `53275a23d23a01ac8aa3b0df1bc4efd2b7cbac392bade076ffd731960f5d0e84`. Independent JSON result: `independent_collector_review.json`, SHA-256 `7b689cfa0d397985e8488028fd59b47fda9b31fc86c1d7b31433eb0137d65a3d`. The JSON records source, launcher, compiled gate, installed-JAR bytecode and test hashes. All 107 manifest artifact hashes and both exact runtime-directory inventories were independently checked.

Reviewed files are `integrations/romraider/virtual/src/a2wc/virtualrr/ReadOnlySSMCollector.java`, `Invoke-ReadOnlySSM.ps1`, the runtime manifest, actual installed RomRaider source, and bytecode read directly from `C:\Program Files\RomRaider\RomRaider.jar` (SHA-256 `43f0e92d652a5d2dde57fbe76ef99ff4f18c8147b0cbc20c0c4ccb33a7fe6635`).

## Command and acquisition policy

The gate validates the SSM header, tester/ECU IDs, frame length and checksum before delegation. It permits only BF identification; A0 reads of 1..240 bytes wholly inside `[0x000000,0x100000)`; and A8 reads whose addresses are drawn from the six reviewed raw bytes. Those addresses are `FF4C75`, `FF4C8D`, `FF4CA1`, `FF4C50`, `FF4BC1` and `FF4BC2`. The acquisition code requests all six, in that order. The validator also permits subsets/repetitions within this same address set; that does not expand accessible memory or permit a write.

B0, B8, reset at 000060, kernel upload, other command codes, nonzero A0/A8 mode padding, direct line clearing and `open` commands are rejected. Known-length sends require both polling states to remain STATE_0 and fast polling to remain disabled. These checks exclude the native connection manager's line-break and cached-response branches.

The collector checks BF ECU ID `2F12515306`, then reads the eight-byte A0 pilot at 2000 and requires `A2WC511R`. Each complete 1 MiB pass independently checks its CALID against that pilot. The two complete image SHA-256 values must match. Reads advance by 240 with a final 16-byte block, covering every byte exactly once in each pass. The code does not substitute a RAM kernel or fall back to another transport after failure.

There are 60 initial and 60 final consecutive A8 samples plus 70 interleaved samples per ROM pass: 260 six-channel samples and 9002 total requests in the successful virtual scenario. Host UTC/elapsed times and phases are recorded; these are not TCU heartbeat or fresh-CAN assertions. Successful output is explicitly acquisition-only and not flash-ready. Virtual output identifies itself as a software scenario rather than physical telemetry.

## Native initialization corroboration

The actual installed-JAR bytecode confirms that `J2534ConnectionISO9141` initialization calls provider construction, open, version query, ISO9141 connect, timing/loopback/data/parity configuration and a pass-message filter. That constructor does not call `writeMsg`, five-baud initialization, fast initialization, programming voltage or `clearLine`. Its known-length `send` implementation enters the break path only for current STATE_0/last STATE_1, and the cached-response path only for current STATE_1. The collector rejects both states before delegation.

The reviewed serial source/bytecode opens and configures the explicitly named port. The serial setup clears RTS but does not send an SSM request, line break or initialization sequence. These are Java implementation observations; physical provider/interface behavior was not exercised.

The PowerShell launcher defaults to Virtual. Physical modes require the explicit acknowledgement switch and pass a separate literal authorization argument to Java. J2534 mode pins the exact provider path/hash and checks x86 PE machine type plus a 32-bit JVM before constructing the native manager. The launcher pins the Java executable and installed libraries. The OpenPort provider is never treated as a COM port.

## Findings fixed during review

1. The initial wrapper checked hashes of listed inputs but admitted additional class/JAR inputs. It now uses an explicit classpath, exact class/resource inventories, `-Force` enumeration for hidden/system files, and rejection of reparse-point roots or descendants. The manifest generator applies the same reparse-point rejection. The implementation agent additionally exercised hidden-file rejection before Java launch. Reparse-point rejection was independently inspected in the final source.
2. Initial constructor failure and cleanup exceptions could suppress acquisition evidence. Construction is now inside the evidence try/finally, cleanup handles a null manager, and cleanup failures are recorded without skipping the result writes. Current pass/offset and completed image hashes are retained on a normal exception path.
3. Two mutually identical full reads could previously contradict the initial CALID pilot. Each full image now checks its embedded CALID against the pilot before success.
4. Native serial BF initialization waits for a quiet interval and could otherwise extend indefinitely under continuous input. The collector now applies a 10-second Future timeout, cancels the daemon worker and performs no retry/fallback.

No substantive finding remains open in this bounded offline review. A blocked native call/cleanup or forced process termination is still not a demonstrated graceful-abort path; the timeout does not validate the provider's behavior.

## Independent validation performed

`IndependentCollectorGateCheck.java` ran 285 policy checks on the actual compiled gate with an in-memory `ConnectionManager`. It tested every non-BF empty command, A0 size/end boundaries, mutations outside the six-address set, malformed headers/length/checksum, B0/B8, forbidden polling states, clearLine and open. No rejected operation reached the delegate. The test did not invoke collector main, create a physical connection object or include JNA libraries on its execution classpath.

`independent_collector_review.py` checks the final manifest hashes, exact runtime inventories, reparse-point absence, explicit classpath, final source guards and captured native constructor bytecode. It does not launch Java or load any provider. Captures are `independent_j2534_iso9141_bytecode.txt`, `independent_serial_manager_bytecode.txt` and `independent_collector_gate_test.log`.

The implementation agent's final launcher virtual run and constructor-failure and hidden-file regressions are additional evidence, not physical acceptance. OEM A0 accessibility, actual 24-bit RAM addressing, communication timing, current-image identity and device cleanup behavior remain for the separately authorized physical procedure. Nothing in this review closes the RAM ownership, scheduler deadline, checksum/flash or production-release gates.
