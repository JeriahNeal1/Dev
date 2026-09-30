# Final physical acquisition run plan

Exactly one physical milestone remains: RK03 FINAL TWO-PASS 128-BYTE ACQUISITION.
This release is qualified offline and is NOT authorized for execution in its preparation run.
No intermediate read-size milestone is required.

## Retained prerequisite evidence

RK03_BOUNDED_ROM_READ_128_PHYSICAL = PASS. The fixed128 kernel returned one exact139-byte response containing current.bin[0:128]; 25TX,15 uploadACKs, one start, one identity, one read, clean cleanup. OEM return afterward: BF2F12515306,120/120 six-variable PASS_CAPTURE_ONLY, observer/broker/provider cleanupPASS. The previous failed512 session remains unchanged; its application frame was incomplete, not a valid shorter217-byte response. The prior cutoff cause is unresolved.

## New final source and immutable contract

Source branch rk03/final-two-pass-128. Active folder final_two_pass_128.
Fixed kernel SHA256808a5523d47de11881bfc2ea06a35278aedb5122ed51e8110f817b3210adb653,1808 bytes, entryFFFF3004, identity A2WC511R-RK02 followed byNUL. No alternate image/start input.
Keep the proven24-request transport/upload/start/identity prefix. Then16384 fixed reads: pass0 indices0..8191 and pass1 indices0..8191, each128 bytes. Addresses0 through000FFF80, exclusiveROMend00100000; exactly1048576 bytes/pass,2097152 bytes total. Require exact139-byte framed replies, pass/address/bodylength/checksum, immediate pass1 block comparison, exact raw-file lengths/fullbyte identity/SHA identity. Baseline current.bin comparison is separate; consistent changed bytes in both passes do not fail transport solely because they differ from the previous image.

The qualification certificate identifies both byte-identical executables and exact fixed schedule hash. Historical fixture JSON files are retained reference data. Physical execution uses compiled FixedReads and the fixed pinned kernel; no JSON actions table or external payload/address is executed.

## Future human/software sequence

1. On a separately requested future final run, verify the sealed certificate and every pinned input. Recover FINAL_GATE_STATE.json with invocation0 and no reservation/session files. Do not erase/reset a consumed marker.
2. Request only IGNITION OFF; wait for that exact human reply and persist its session-bound timestamp/source.
3. Request only TEST MODE ON; wait and persist. EngineOFF. The operator manages electrical support, OpenPort, connectors and intentionally disconnected fans; no component or numerical-voltage gates.
4. Run the pinned check_clients.ps1 to a new preauthorization output. Require PASS. Display expectedBF2F12515306, physical executable and certificateSHA256, kernelSHA256, fixed schedule, and no flash/arbitrary/retry path. Do not reuse an old client check.
5. Require exactly PROCEED RK03 FINAL TWO PASS ACQUISITION. Persist exact user authorization with session/certificate/UTC binding; set status AUTHORIZED_FINAL_TWO_PASS_128_ONLY only then. No physical-state changes while active.
6. Invoke the pinned launch_final_once.py --run-once exactly once. The launcher revalidates all pins and clients, reserves the launch, and the native gate independently consumes invocation.once before loading the fixed provider. Await that same child if bookkeeping is interrupted; never relaunch.
7. After process exit, run pinned check_clients.ps1 to physical_session/RK03_FINAL_TWO_PASS_128_01/POSTEXIT_CLIENT_CHECK.json. Then seal_final_result.py --seal-completed-session. It independently validates every API exchange, reconstructs both raw images, compares every saved byte, and preserves immutable session copies. Any first failure ends acquisition with no retry, no fallback, no later command.
8. Regardless of acquisition PASS/FAIL, request IGNITION OFF and wait; then NORMAL MODE ON and wait. Persist completed_recovery_gates in that order, physical_state NORMAL MODE ON, engineOFF, status RECOVERY_NORMAL_MODE_CONFIRMED.
9. Invoke launch_oem_return_once.py --run-once-oem-return once. It runs only the unchanged passiveBF/A8 observer. Await exit and clean client/provider scan, then run seal_oem_return_final.py. Require BF2F12515306,120/120 six-variable PASS_CAPTURE_ONLY and clean observer/broker/provider exit. No programming fallback/retry.
10. If acquisition and OEM return bothPASS, run complete_project.py --audit-completed-project OFFLINE. It verifies the certificate/evidence hashes, all wire and raw bytes again, independent current.bin comparisons, source commit/worktree, then creates a local completion tag and PROJECT_COMPLETE only after tag success. It never modifies either raw image or current.bin. Designate images CURRENT_PHYSICAL_CAPTURE, not factory stock.
11. If any acquisition/recovery/integrity stage fails, preserve exact evidence and report the first divergence; do not claimPROJECTCOMPLETE. If passive recovery fails, ask only IGNITION OFF and stop further physical work.

## Remaining human actions

IGNITION OFF -> TEST MODE ON -> PROCEED RK03 FINAL TWO PASS ACQUISITION -> acquisition/cleanup -> IGNITION OFF -> NORMAL MODE ON -> automatic passive return/final offline audit.

## Limits

Full-duration silicon behavior has not been physically demonstrated. New final qualification uses the same provider-capablePE solely in static fake modes; complete scheduled data are simulated. The single128 physical success validates the selected frame/transport path, not every future ROM byte or the old512 failure's cause. All final images receive independent wire/file integrity checks. No additional physical acquisition is permitted during release preparation.
