# Read-only Dev audit

CALID: A2WC511R; ECU ID: 2F12515306

## Findings

- **WRONG_TARGET** (build_blocker): A8DH202X
- **AUTO_TRANS_NOT_SET** (build_blocker): 0
- **MISSING_TARGET_FILES** (port_work): No A2WC511R target header/map/linker/config in uploaded MerpMod/Targets.
- **RAM_HOLE_UNPROVEN** (integration_blocker): FFFF7400 is a prior candidate, not an allocation. No absence-of-xref proof accepted.
- **CURRENT_FLASH_UNKNOWN** (vehicle_test_blocker): The uploaded baseline identity does not identify the current modified calibration in the car.
- **FRESHNESS_UNPROVEN** (active_control_blocker): 4CA1 and 4C50:02 have not been proven to exclude stale gear data under communication failure.

## ROM identities

- `SubaruRoms/Backup/A2WC511R_STOCK_ROMRAIDER.bin`: `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`
- `SubaruRoms/OEM/A2WC511R.bin`: `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`
- `SubaruRoms/OEM/A2WC511R_STOCK_ROMRAIDER.bin`: `a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96`

## Repository revisions

- MerpMod: `8720d209df107a81fd171131cfba96d8cae1f118`
- SharpTune: `ecabea89615132dac2de37c05f72adae16d966d1`
- SubaruDefs: `9b2992eba8133fe5338b89aa77b22c1bb14d6507`

This report does not modify a ROM, certify unused memory, identify the currently flashed tune, or authorize flashing.
