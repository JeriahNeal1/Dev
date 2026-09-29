# v2 integration update — 2026-09-25
The custom IDA MCP is removed. Use the official Hex-Rays IDA MCP; local beta/idalib acceptance remains pending. New native RomRaider model + immutable history/proposal/timeline MCP is implemented and tested against model doubles; actual Windows/RomRaider smoke tests are pending. No additional ECU calibration or firmware changes were applied by this revision. See docs/MIGRATION_V2.md and reports/V2_TEST_STATUS.md. Preserve any newer local state from v1 before replacing it.

# Current state at handoff

## Authoritative next task
The user has moved the project to local Codex. Establish local context and tool access first. The last requested physical experiment is the six-channel TCU snapshot/status observation described in `docs/LOGGER_TEST.md`. Its **definition exists; its result is not present in this archive**. Search the user's local tuning folder before asking for it.

## What exists
IDA names, comments, code heads and these reported function boundaries were recovered and manually saved:
- `147AC–14802`: packed gear decoder.
- `24950–24A9C`: normalized gear-state updater.
- `24A9C–24AA4`: E8 default setter.
- `15A02–15A16`: tests `FFFF4C50 & 0x02`.
- `15A2C–15D46`: TCU-derived snapshot updater.
The reported reset function at `15D46` shares/falls through into code at `15D5E`; inspect actual chunks/control flow before splitting it.

The current range/gear observation is sufficiently clear to stop repeatedly testing E8/E9: reverse maps to the same normalized gear1 as forward1. Packed `FFFF4C8D` preserves target/current codes; `0x11` is a candidate first-gear-state condition, not a complete safety condition.

## What does not yet exist as a verified artifact
- A proven free ROM/RAM allocation for the port.
- A complete audited A2WC511R target map/header/config and successful matching build/patch.
- A verified first diagnostic-only firmware flash.
- A proven communication freshness/dropout guard or calibrated launch thresholds.
- A verified baseline stock hash for the user's live IDB input.

## Software provenance
MerpMod observed `v0.1-73-g8720d20`, full source revision `8720d209df107a81fd171131cfba96d8cae1f118`.
SharpTune observed banner `0.1.9-RC2-10-gfcf9fdb`; resolved upstream commit `fcf9fdbafc2ba5bf04674fcad253fbda404aa171`. The starter suggested `ecabea89615132dac2de37c05f72adae16d966d1`, not necessarily what is now running. SubaruDefs proposed pin `9b2992eba8133fe5338b89aa77b22c1bb14d6507`; verify actual host branch/hash.

## Baselines and paths
Likely local resources: `C:\Dev\MerpMod`, `C:\Dev\SharpTune`, `C:\Dev\SubaruDefs`, `C:\Dev\SubaruRoms\OEM\A2WC511R_STOCK_ROMRAIDER.bin`, plus a Subaru tuning folder under Documents. A separately retrieved project report names `C:\Users\JeriahN\Documents\SUBARU TUNING`; earlier tool logs use a different Windows profile. Resolve, don't assume.
Historical archived reads have A2WC511R identity but uncertain modification state:
- `ECUFlashReadRaw(1).bin`: `1aac3214ec276822f1343e66fc1b8af83be8e61866d2d182882beb88317b4920`.
- `ECUFlashReadRR(1).bin`: `2f9c2f8af56e337e9fa31fd5efd4b1f01d3474f78396065ad3fc9a0bd132cbdc`.
A separate library guide claims baseline `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`; do not substitute it without finding and reconciling the actual file.

## User decisions
Keep OEM O2/exhaust setup for now. Wideband-only control/hood-dump work is deferred. Remain on the working Windows environment. Prefer precise direct tooling and a persistent local record. Manual IDA save works; broken Python save call must not recur. Ultimately interested in rally/track/automatic launch and mild ALS, but not yet authorized/validated as a running implementation.
