# Current ECUFlash session evidence

The newest successful ECUFlash read is preserved as `ecuflash_log_20260929t172612.preserved.txt` (79,435 bytes), SHA256 `9fecae4b465edfbe6d7ad9b75ff8cfb39101dac67efd655dcbf151d50ad73f30`. It is the primary comparator; August 18 remains a supplemental earlier success.

The app was idle with the completed read and save visible in `ecuflash_printwindow_01.png`. Initial directory metadata reported an empty log. By 00:36:50.849Z, before close, the source metadata and `log_copy_before_close.txt` already contained 79,435 bytes with the same final hash. The exact flush time/cause is unknown. Parent-authorized normal application close was requested at 00:36:50.9227335Z; process exit was confirmed at 00:37:08.9861718Z. Closing is not credited with producing the log content. No session button, provider invocation, forced termination or new vehicle command was issued.

## Image association

Lines 1352–1353 record saving `C:/Dev/SubaruRoms/current.bin` at 17:29:13.122 and writing 1,048,576 bytes at 17:29:13.123 local (00:29:13.123Z). The file timestamp is 00:29:13.1231299Z. Original and preserved copy are 1 MiB with SHA256 `bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2`; the hash stayed unchanged across app close. The screenshot title and save lines independently show `current.bin`. This is a strong session-to-file association; the application log does not itself record a content hash.

## Session milestones

| Evidence | Current successful session | August18 success | RK02_VEHICLE_03 |
|---|---|---|---|
| Identity | line 90: 2F12515306 | line 89: 2F12515306 | BF raw reply contains 2F12515306 |
| 81/83 | raw bytes/API calls absent | raw bytes/API calls absent | 81 → C1 EF 8F; 83 → status 16, count 0 |
| Seed/key | lines 91–92: labels only | lines 90–91: labels only | never reached |
| RAM upload | lines 93–130: FFFF3000, size 0x1234, 37 blocks | lines 92–129: same address/length sequence | never reached |
| Kernel | line 132: OpenECU Subaru SH7058 DUAL Kernel V1.07 | line 131: same | never reached |
| Read/save | lines 137–1337: dump; 1352–1353: save | same read address/length sequence; 1355–1356: save | zero-byte partials |
| Physical Test Mode | unknown for this exact read | absent from log | G11 records connected greens, ignition ON, engine OFF, CEL/pump cycling |

Current and August report ECUFlash 1.44.4870, API 04.04, DLL 1.02.4870, firmware 1.17.4877 and serial TAPoN7at. Current source lines 3, 16, 42–45 and 73–88 establish these labels. Installed file hashes captured afterward are in JSON; they are not a session-time loaded-module hash. Executable/DLL PE version resources differ from runtime labels (1.44.0.4868/1.02.0.4868), so both are kept separate.

Current seed-label → key-label is 43.0 ms; key-label → first RAM block is 618.0 ms. August equivalents are 46.0 ms and 647.0 ms. These are application label intervals, not on-wire timing or proof of a specific wait.

The log records an initial kernel-version probe (77), interface close (78), another version block (79–82), unsupported VIN (83), interface close (84), then another version block (85–88) before SSM2 init (89). Two interface closes follow the dump (1338–1339). These show application lifecycle messages; no raw Open/Disconnect/Close statuses are logged. Normal GUI exit afterward does not prove ECU reset.

## Limits

The explicit read-area entries total 1200 blocks / 614,400 bytes across 0x000000..0x086000; 0x0C0000..0x0CF000; 0x0FF000..0x100000 (end-exclusive), while the saved image is 1,048,576 bytes. This log alone cannot prove every saved byte was transferred from the ECU; it does not explicitly explain omitted read ranges. Full-byte acquisition claims require separate evidence.

The new successful read demonstrates a working ECUFlash read through this adapter/ECU combination in this session. It does not establish the physical cause of RK02's missing 83 response. Actual provider defaults/configuration, filter, baud transitions, raw 81/83 responses, seed/key bytes, exact Test Mode observation and voltage remain absent from this successful-session log. Prior RK02 observations and desired future probe state are not attributed to this read.

`SESSION_EVIDENCE.json` contains source hashes, full relevant event arrays, block sequences, the unchanged RK02 raw event stream, timestamp interpretations and explicit nulls. `EVIDENCE_MANIFEST.json` pins generated/preserved outputs. No original evidence or saved ROM was modified.
