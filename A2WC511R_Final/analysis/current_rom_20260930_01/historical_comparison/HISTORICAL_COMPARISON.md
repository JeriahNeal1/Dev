# A2 current image versus historical images

The authoritative preserved current image is exactly byte-identical to the historical `AdjustedBaseTimingANDNOCLOLD.bin`: SHA256 `bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2`, 1,048,576 bytes. This is a direct byte comparison, not an inference from the filename or historical CRC values.

The two existing inventories identify 1 historical alias for this hash:

- `C:\Users\Jeriah Neal\Desktop\AdjustedBaseTimingANDNOCLOLD.bin` — VERIFIED_BYTE_IDENTICAL.

The alias list covers the union of the existing inventory and attestation catalog, not a new exhaustive filesystem search. The authoritative new input remains `current.preserved.bin`; historical aliases remain provenance material.

| Historical image | Changed bytes to current | Contiguous ranges |
| --- | ---: | ---: |
| A2WC511R.analysis_baseline.bin | 1856 | 517 |
| ECUFlashReadRaw(1).bin | 53 | 16 |
| ECUFlashReadRR(1).bin | 51 | 16 |
| AdjustedBaseTimingANDNOCLOLD.bin | 0 | 0 |
| REV3Map.bin | 60 | 9 |

The current input matches all 16/16 retained historical ECU and image CRC32 values, covering the full1MiB in the recorded page geometry. The prior suspected-current candidate is therefore an exact file match to the new input; the historical CRC result now serves only as corroboration.

The original August18 13:49:42 log is absent from its recorded AppData path. Its CRC table remains in the hash-pinned `history_comparison.json`; `ecuflash_history.json` retains the line-numbered operation extracts and recorded original log hash. This review does not claim to have freshly verified the absent raw log.

`HISTORICAL_COMPARISON.json` includes every exact changed interval (start inclusive/end exclusive, historical bytes and current bytes) for all18 distinct images in the original inventory. It separates historical tunes, stock, editor stamps and generated/test images. The later attestation catalog supplies additional aliases without replacing the historical comparison scope.

No ROM bytes, sealed reports, RK03 history or physical state were changed. No probe was built or executed.
