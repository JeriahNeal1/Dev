# Current calibration identity

**LOCAL_CALIBRATION_SEARCH: PASS within enumerated readable roots. CURRENT_CALIBRATION: PHYSICAL/BENCH REQUIRED.** No exact current ECU image is established.

The final pre-package inventory covers 16,355 files, 93 matching image paths and 18 distinct A2WC511R hashes. The independent review's earlier 73-path/17-hash snapshot predates additional disposable GUI and virtual-collector outputs. Those generated copies do not add another historical tune or current-ECU attestation. The new evidence package will duplicate these already classified artifacts; it is deliberately created after this timestamped inventory.

`inventory_all.py` enumerates every regular file in C:\Dev, C:\Tuning, Desktop, Documents, Downloads, ECUFlash install/profile/ROM/upload/history directories, VirtualStore, .RomRaider, C:\SubaruDefs, C:\WorkSpace and temporary-work roots. It checks every1MiB file regardless of extension, ZIP members of that size and SRF payloads. The timestamped `inventory.json` records every identity/path, archive inspection and error; `enumerated_files.json` records all file sizes. Absent OpenECU locations are explicit. The extra Windows WinSAT temp directory denied listing; it is not an ECUFlash/tuning directory. No requested tuning or C:\Dev root was denied. Generated disposable test images are classified separately from original historical tunes.

ECUFlash's registry recent-file/ROM-directory list resolves to the already scanned Desktop files. Only those relevant registry keys are retained; unrelated hardware/license settings were excluded. Manifest/text searches and seven ECUFlash operation logs yielded no later hash-linked acquisition establishing current flash. The August23 log contains interface discovery, not another recorded successful programming operation.

| Historical image | SHA256 | Differences from stock |
|---|---|---:|
| ECUFlashReadRaw.bin; also SRF payload at offset1CD | 1aac3214ec276822f1343e66fc1b8af83be8e61866d2d182882beb88317b4920 | 1856bytes |
| ECUFlashReadRR(1).bin | 2f9c2f8af56e337e9fa31fd5efd4b1f01d3474f78396065ad3fc9a0bd132cbdc | 1856bytes |
| AdjustedBaseTimingANDNOCLOLD.bin | bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2 | 1856bytes |
| REV3Map.bin | d2dc34e1b21985c89b49996c9dedd88494c90c65e2da0c0a735d31d54ca92171 | 1857bytes |

Raw→RR differs only3 stamp bytes. Raw→Adjusted differs53bytes, Raw→REV3 differs94bytes, and Adjusted→REV3 differs60bytes. `history_comparison.json` contains every changed interval and a16-pageCRC comparison for every distinct image.

The August18 13:49:42 ECUFlash log opens AdjustedBaseTimingANDNOCLOLD.bin and finishes at13:50:27 with all16 ECU/image pageCRC32 values equal. The saved Adjusted image matches all16 values. It is the unique full match in the inventory. This establishes a strong **historical match**; CRC32 is not cryptographic byte identity, and the local log history is not proof that the ECU has had no subsequent write from another session or host. REV3 is a later edited file whose name/date does not establish that it was flashed.

Stock is analysis material, not a substitute for the tuned VF52/3-port/3-inch-MAF calibration. A fresh read is required before any current-calibration integration. The future procedure in `ONE_CONNECTION_READ_ONLY_ACQUISITION.md` collects the ROM identity and the pending six TCU bytes with one human-operated physical connection. It does not flash M0 or change calibration values.
