# Current physical ECU ROM status

CURRENT_ROM_SHA256 = bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2
CURRENT_ROM_SIZE = 1048576 bytes (1 MiB)
CURRENT_CAL_ID = A2WC511R (0x2000; also present at 0xC0000)
CURRENT_ECU_ID = 2F12515306 (0xCDAD8)
CURRENT_SUBARU_CHECKSUM = PASS
EXECUTABLE_BYTES_IDENTICAL_TO_STOCK = true
EXECUTABLE_FUNCTIONS_CHANGED = []
UNKNOWN_CHANGED_RANGES = []

The original `C:\Dev\SubaruRoms\current.bin` is unchanged. Its read-only preserved copy is `current.preserved.bin`; initial filesystem timestamps and hashes are in `INGEST_MANIFEST.json`. The latest successful ECUFlash log records this exact saved path, 1 MiB size and 2026-09-30 00:29:13.123 UTC save time, matching the file timestamp. This direct acquisition is the authoritative current-image input.

The exact stock baseline is `C:\Dev\SubaruRoms\OEM\A2WC511R.bin`, SHA256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`. Complete comparison finds **1,856 differing bytes in 517 contiguous ranges**. Every changed byte has an exact definition/object or checksum/stamp classification; proximity to a table was not used.

| Classification | Changed bytes |
|---|---:|
| Calibration table | 1765 |
| Axis | 62 |
| Scalar | 21 |
| Checksum correction | 4 |
| RomRaider metadata stamp | 4 |
| Executable code / padding / unknown | 0 / 0 / 0 |

`CURRENT_ROM_STATUS.json` and `rom_classification/CHANGED_RANGES.json` contain all exact ranges and old/new bytes. `CHANGED_OBJECTS.json` records the 53 changed native definition objects. Both retained instruction inventories match; the broader Diaphora export covers 68,739 unique instruction words in 1,147 functions. These inventories are partial static discovery, but every changed byte outside them is also accounted for as exact data. All bytes outside the identified data changes match stock.

One function extent, `sub_151DC`, contains the changed float at 0x155FC (90.0 to 65.0), named Max Wastegate Duty Limit Post-Compensation. Only byte 0x155FD changes. The unchanged MOVA at 0x15474 and FMOV.S load at 0x15478 establish that this is embedded calibration data, not a changed instruction. No new Diaphora structural matching was needed. Unchanged instructions do not imply unchanged calibration behavior.

The closest historical tune is an **exact byte match**: `C:\Users\Jeriah Neal\Desktop\AdjustedBaseTimingANDNOCLOLD.bin`. It also matches all 16 retained historical page CRC values. Historical files provide provenance only; they do not override current.bin. Exact comparisons against all 18 historical inventory images are preserved in `historical_comparison/HISTORICAL_COMPARISON.json`.

The latest successful ECUFlash read is the primary physical comparator. `ecuflash_current_session/SESSION_COMPARISON.md` compares it with RK02_VEHICLE_03 and the August success. It records API 04.04, DLL 1.02.4870, firmware 1.17.4877, serial TAPoN7at, successful seed/key labels, DUAL 1.07 upload/start, ROM reading and save. Its application log does not expose raw 81/83 bytes, exact bus timing, provider defaults or that session's actual Test Mode observation. The saved file association is strong; the log alone does not prove every saved byte was transmitted from the ECU.

The current file provides strong evidence against changed executable instructions as the explanation for RK02's failure. Electrical cadence, provider behavior and receive/filter/queue behavior remain unresolved; no individual configuration change is claimed causal. The original transition analysis remains sealed, and this report is a supplement.

**CURRENT PHYSICAL ECU IMAGE: calibration differs from stock; executable code identical to stock.**

This is not factory stock. Physical transition-probe status at this milestone: NOT RUN.
