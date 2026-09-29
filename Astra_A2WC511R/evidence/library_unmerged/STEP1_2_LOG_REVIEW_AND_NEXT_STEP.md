# Step 1.2 Log Review and Next Step

Project: 2005 Subaru Outback XT A2WC511R, VF52, GrimmSpeed 3-port, 3-inch MAF, 5EAT

Input reviewed: `F:\`

## File Cross-Check

`logcfg.out` parsed successfully this time:

- No parser error found.
- 31 log parameters.
- `log stringlist`: 280 chars.
- Logging interval: 250 ms.
- New short-header channels are present.

Stale / old-layout files:

- `log0002.csv` through `log0007.csv` use the previous long-header layout and older 11:00 timestamps.
- `log0001.csv`, `log0008.csv`, `log0009.csv`, and `log0010.csv` are empty.

Fresh files used for this review:

- `log0011.csv`: 32 rows, 10.25 seconds.
- `log0012.csv`: 87 rows, 21.75 seconds.
- `log0013.csv`: 17 rows, 4.25 seconds.
- `log0014.csv`: 63 rows, 15.75 seconds.
- `log0015.csv`: 23 rows, 5.75 seconds.
- `log0016.csv`: 546 rows, 136.5 seconds.

Fresh usable short-header data: 768 rows, about 194.25 seconds total.

## Decision

There is enough detail to make a safety decision, but not enough to make tune-value changes.

Do not change:

- MAF scaling
- Injector data
- Open-loop fueling
- Timing
- Target boost
- WGDC
- Turbo dynamics
- DBW
- Rev limit / speed limit
- Any safety, diagnostic, limp, knock, IAM/DAM, or boost-cut behavior

The next step is mechanical/logging verification, not a new ROM and not a table edit.

No ROM was modified by this review.

## What Improved

Compared with the previous batch:

- The new short `logcfg.txt` parsed successfully.
- The logs are warm enough for a basic health review.
- Coolant temperature was normal, about 192-205 F.
- Battery voltage was mostly healthy after initial sample-fill artifacts.
- `wgdc`, `mwgdc`, `tdi`, and `tdp` stayed at 0.0 in all valid rows.

This confirms the Part 1 zero-WGDC / no-positive-turbo-dynamics strategy is still represented in the logs.

## Critical Blocker 1 - Manifold Pressure Signal Is Not Plausible

The new log includes:

- `mrp`
- `map`
- `baro`
- `bcalc = map - baro`

But `bcalc` never exceeded about 0.145 psi in valid rows.

Valid-row pressure summary:

- `bcalc`: 0.0 to 0.145 psi.
- `mrp`: 0.0 to 0.145 psi.
- `map`: about 13.20 to 13.35 psi.
- `baro`: about 13.20 psi.

This is not physically plausible as a complete manifold-pressure picture. At warm idle, manifold pressure should show vacuum. During higher-load rows, it should move meaningfully. Instead, it stays essentially at atmospheric pressure.

Examples:

- Warm idle rows show `bcalc` around 0.0-0.145 psi instead of vacuum.
- High-load rows show MAF over 100 g/s and load around 1.7-1.8 g/rev, but `bcalc` still stays about 0.145 psi.
- `log0016.csv` reached about 129 g/s, 3.70 V MAF, 1.79 g/rev load, and 100% throttle, while pressure still logged near atmospheric.

Conclusion:

Do not tune boost from this signal. Either the logger channel/scaling is wrong for this ECU, the manifold pressure sensor signal is not being represented correctly, or there is a sensor/plumbing issue. Verify manifold pressure with RomRaider live logging and an external boost/vacuum gauge before any WGDC or boost work.

## Critical Blocker 2 - Knock Activity Is Too High

Valid-row knock indicators:

- `fbkc`: down to about -8.09 degrees.
- `flkc`: 0.0 throughout.
- `ksum`: increased up to 18.
- `iamd`: 0.0 throughout.

Examples from `log0016.csv`:

- Around 81.2-81.8 seconds, `fbkc` reached about -8.09 degrees at roughly 3900-4000 rpm, high throttle, high MAF, and high load.
- `ksum` reached 18 and stayed high afterward.

If `iamd` is real, IAM/DAM is not healthy. If `iamd` is not real, the direct RAM logger channel is not trustworthy. Either way, this blocks boost/timing/performance progression.

Required next action:

- Verify IAM/DAM in RomRaider Logger directly.
- Verify the direct RAM address/channel for IAM on this ECU.
- Do not do additional high-load pulls until knock behavior is understood.

## Fuel Trim / MAF Review

Warm rows show large trim error:

- `afc1`: -25.0% to +25.0%.
- `afl1`: mostly negative, down to about -11.7%.
- Combined `afc1 + afl1` exceeded +/-10% in 288 warm rows.
- Combined `afc1 + afl1` exceeded +/-15% in 78 warm rows.

Warm idle is generally rich by trim:

- Idle `afl1` averaged about -9.4%.
- Idle combined trim often sat around -5% to -15%, with worse outliers.

Warm low-load MAF-voltage buckets, filtered for closed-loop-ish no-knock rows, mostly show negative trim:

- 1.2-1.3 V: about -4.9% average combined trim.
- 1.3-1.4 V: about -10.6% average combined trim.
- 1.4-1.5 V: about -6.5% average combined trim.

This suggests the ECU is often removing fuel in low-load regions. However, do not apply MAF changes yet because:

- Manifold pressure logging is not trustworthy.
- Knock activity is high.
- IAM/DAM is unverified or unhealthy.
- There is not a clean 10-15 minute steady cruise set.
- Fuel pressure and injector condition are still unknown.
- The sign and size of trims could be caused by mechanical or fuel-system issues, not just MAF scaling.

## Boost / Wastegate Review

WGDC-related channels look safe:

- `wgdc`: 0.0 in all valid rows.
- `mwgdc`: 0.0 in all valid rows.
- `tdi`: 0.0 in all valid rows.
- `tdp`: 0.0 in all valid rows.

But spring-pressure validation is not complete because manifold pressure data is not credible.

Do not reintroduce WGDC.

## Heat / Electrical Review

Coolant temperature:

- About 192-205 F.
- Acceptable for a warm health log.

Intake air temperature:

- About 108-131 F in valid rows.
- Hot enough to treat any high-load knock/trim data cautiously.

Battery voltage:

- Mostly around 13.7-14.1 V after initial sample-fill artifacts.
- A few early rows around 12.8 V occurred in `log0011.csv`.

## Required Mechanical / Logger Checks Before More Pulls

Do these before another boost-onset or high-load log:

1. Verify a real boost/vacuum gauge reading at warm idle. It should show vacuum.
2. Compare the gauge to RomRaider live `Manifold Relative Pressure` or equivalent.
3. Verify the MAP/manifold pressure sensor hose, wiring, and connector.
4. Verify the logger channel names/scalings against RomRaider live values.
5. Verify IAM/DAM in RomRaider.
6. Inspect for intake/MAF installation issues, post-MAF leaks, and unusual MAF turbulence.
7. Confirm fuel pump, injector model, and fuel pressure behavior.
8. Confirm spark plug condition, heat range, gap, and coil health.
9. Confirm wideband status before any open-loop or WOT work.

## Next Logging Procedure

Do not do high-load or WOT logs yet.

Next useful log set:

1. Warm idle with external vacuum/boost gauge visible to the user.
2. Confirm logged pressure shows vacuum at idle.
3. If logged pressure does not show vacuum, stop and fix the sensor/logger issue.
4. Once pressure is credible, log 10-15 minutes of steady closed-loop light cruise.
5. Keep accelerator pedal low and steady.
6. Do not perform boost-onset testing until pressure, IAM/DAM, and knock behavior are credible.

## Status

PASS WITH WARNINGS: This batch is warm and the logger parsed correctly, so it is useful diagnostically. It is not safe to create a tune change from it. The blocking issues are implausible manifold-pressure data, significant FBKC/knock-sum activity, unverified or unhealthy IAM/DAM, and no clean steady cruise dataset.

