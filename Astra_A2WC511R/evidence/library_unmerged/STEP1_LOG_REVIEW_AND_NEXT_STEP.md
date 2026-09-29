# Step 1 Log Review and Next Step

Project: 2005 Subaru Outback XT A2WC511R, VF52, GrimmSpeed 3-port, 3-inch MAF, 5EAT

Input folder reviewed: `C:\Users\JeriahN\Documents\SUBARU TUNING\Step 1 Logs`

Reviewed files:

- `log0001.csv`: empty
- `log0002.csv`: 47 data rows, 14.1 seconds
- `log0003.csv`: 2 data rows, 0.6 seconds
- `log0004.csv`: 128 data rows, 38.4 seconds
- `log0005.csv`: 14 data rows, 4.2 seconds
- `log0006.csv`: 38 data rows, 11.4 seconds
- `log0007.csv`: 14 data rows, 4.2 seconds
- `log0008.csv`: empty
- `log0009.csv`: empty
- `log0010.csv`: empty
- `logcfg.txt` / `logcfg.out`: logger config and parsed output

Total usable data: 243 rows, about 72.9 seconds of logging.

## Decision

Do not make calibration value changes from these logs.

The correct next step is not a new tune revision and not Part 2. The correct next step is a better Step 1 / Part 1.5 logging pass after fixing the boost-channel confidence issue and collecting fully warmed idle, steady cruise, and gentle boost-onset data.

No ROM was modified by this review.

## What Passed

Part 1 boost-control safety behavior appears to be doing what it was supposed to do in the logs:

- `wgdc_primary_pct`: 0.0% for all logged rows.
- `max_wgdc_current_pct`: 0.0% for all logged rows.
- `td_integral_pct`: 0.0% for all logged rows.
- `td_proportional_pct`: 0.0% for all logged rows.

This supports that the manual Part 1 zero-WGDC / neutralized-positive-TD strategy is at least being represented in the logged channels.

## Major Blockers

### 1. The engine was not fully warmed

Coolant temperature ranged from about 91.4 F to 120.2 F.

This is too cold for MAF scaling, fuel trim judgment, boost validation, or any performance-tune decision. Closed-loop MAF review should be done only after normal operating temperature and stable trims.

### 2. Boost validation did not happen

Logged boost channels did not show meaningful boost:

- `boost_psi_ssm`: 0.0 to 0.145 psi
- `boost_psi_direct`: about 0.038 to 0.098 psi

Those readings are not credible during rows where airflow and load were high, including:

- MAF voltage up to 3.88 V
- MAF airflow up to 145.09 g/s
- calculated load up to about 2.08 g/rev
- throttle opening up to 100%

Conclusion: these logs do not prove the car stayed at spring pressure, and they do not prove boost creep is absent. The boost signal must be fixed or cross-checked before reintroducing any WGDC.

### 3. High pedal/throttle occurred while cold

Several rows show high pedal and throttle while coolant was only about 91-108 F:

- `log0004.csv`: up to 100% accelerator / 100% throttle around 91-93 F coolant.
- `log0005.csv`: up to 100% accelerator / 100% throttle around 106-108 F coolant.

Do not repeat this. For Step 1/Part 1.5, use no WOT and no aggressive throttle, especially before full warmup.

### 4. Fuel trims are not usable for MAF changes yet

Combined trim behavior was large and inconsistent:

- `af_correction_1_pct`: -25.0% to +25.0%
- `af_learning_1_pct`: 0.0% throughout
- Combined trim exceeded +/-10% in 104 of 243 rows.
- Combined trim exceeded +/-15% in 77 of 243 rows.

These rows are not valid for MAF scaling because the logs are short, cold, transient-heavy, and include invalid/uncertain boost data. The sign also conflicts with the normal expectation for a larger 3-inch MAF housing, which is another reason not to guess a curve.

### 5. Knock/IAM data blocks progression

Logged knock indicators:

- `feedback_knock_deg`: minimum -2.11 degrees, 12 nonzero rows.
- `fine_learning_knock_deg`: 0.0 degrees throughout.
- `knock_sum`: increased up to 5.
- `iam_direct`: 0.0 to 0.5.
- `iam_ssm`: constant 15.9375, which is not credible and should be ignored.

The direct IAM value may be real or may need validation against RomRaider live logging. Either way, this is not a "go add boost" condition.

### 6. Some logger channels are not trustworthy

Do not use these channels for tuning decisions from this batch:

- `iam_ssm`: invalid-looking constant 15.9375.
- `gear_position_ssm`: invalid-looking constant 256.
- `boost_psi_direct`: invalid-looking near-zero values.
- Initial zero values in slower sampled channels such as battery, IAT, atmospheric pressure, and fuel target are startup/sample interpolation artifacts.

Useful channels from this batch:

- RPM
- vehicle speed
- accelerator pedal
- throttle opening
- MAF voltage
- MAF g/s
- WGDC primary
- current max WGDC
- turbo dynamics integral/proportional
- A/F Correction #1, with caution
- coolant temp
- intake air temp after initial samples
- battery voltage after initial samples
- direct FBKC/FLKC/knock sum, with caution

## Next Step

Do not change:

- Target boost
- WGDC tables
- turbo dynamics
- MAF scaling
- fueling
- timing
- DBW
- rev limit
- speed limit
- safety/diagnostic/protection tables

Before any table-value change, collect a clean Step 1.5 logging set:

1. Confirm the boost gauge/log channel works.
2. Warm the car fully before logging. Target normal operating coolant temperature, not 90-120 F.
3. Log 3-5 minutes of warm idle.
4. Log 10-15 minutes of steady light cruise with varied MAF voltage.
5. Log gentle transient throttle only.
6. Only after the above are clean, do one gentle partial-throttle boost-onset check.
7. Abort immediately if boost exceeds expected wastegate spring behavior, WGDC is not near zero, IAM/DAM is unhealthy, or repeatable FBKC/FLKC appears.

## Specific Logging Fix

For the next `logcfg.txt`, add a standard SSM manifold absolute pressure channel and calculate boost from MAP minus atmospheric pressure. Do not rely on `boost_psi_direct` from this batch.

Recommended additional channels:

- `manifold_absolute_pressure_psi`: SSM parameter `0x0D`, scaling `x,37,*,255,/`
- `atmospheric_pressure_psi`: SSM parameter `0x23`, scaling `x,37,*,255,/`
- calculated `boost_calc_psi`: `manifold_absolute_pressure_psi,atmospheric_pressure_psi,-`

Keep `boost_psi_ssm` as a comparison channel if logging rate remains acceptable.

## Required Mechanical/Instrumentation Checks

Before the next boost-onset test:

- Confirm external boost gauge or known-good logged boost value.
- Confirm no boost leaks or post-MAF leaks.
- Confirm MAF sensor orientation and housing installation.
- Confirm fuel pump model and fuel pressure health.
- Confirm wideband status. WOT/open-loop tuning remains blocked without wideband.
- Confirm the wastegate actuator spring pressure target if possible.

## Status

PASS WITH WARNINGS: Part 1 zero-WGDC behavior is represented in the logs, but the dataset is too cold, too short, too transient, and has invalid/uncertain boost and IAM/gear channels. Do not create a new ROM from these logs.

