# What executable ECU changes add beyond stock calibration

## Clarify the current method
We are **not rebuilding the entire Subaru ECU from recovered original C source**. We have disassembled selected parts of A2WC511R, identified addresses/call conventions and runtime variables, and are preparing compiled MerpMod-derived additions/patches that preserve most OEM code. A decompiler output, when supported, is an approximation for analysis—not a clean original source tree that can automatically be rebuilt into a matching firmware.

Stock tune, custom calibration, executable patch and complete replacement firmware are four different things:

| Approach | Changes | Main benefit | Additional burden |
|---|---|---|---|
| OEM calibration | None | Known original behavior for original hardware | Does not establish suitability for modified intake/turbo/fuel hardware |
| Custom calibration | Existing maps/constants/scales | Match fueling, boost, timing and transient behavior within existing algorithms | Measurement quality, correct definitions and operating coverage |
| Selective executable patch (our route) | New routines, hooks, conditions, tables and RAM state while retaining OEM base | Functions or selection logic absent from the original calibration interface | ABI/register preservation, scheduling, memory, failure paths, metadata/checksums and validation |
| Full replacement firmware | Scheduler, drivers, crank/cam processing, injection/ignition, DBW, diagnostics, communications and control algorithms | Broad architectural freedom within hardware limits | Much larger control-software and validation project; NOT the current scope |

## Documented MerpMod examples versus new proposals
At pinned revision 8720d209df107a81fd171131cfba96d8cae1f118 the README documents Flash-family speed density, launch control, flat-foot shift and CEL signaling; it labels Gratis deprecated and Switch alpha/untested with advanced launch and map switching/blending. These are upstream capabilities for supported ports/configurations, not evidence our A2WC511R build is done or that every feature suits a 5EAT. Its default mod tables are expressly not basemaps.

New development that could be designed here includes richer diagnostic traces and reason bits; a state machine keyed to both target and current gear plus proven signal freshness; custom map selectors/compensations; alternate sensor interpretation with validated ADC/wiring/scalings and fault response; or special boost/torque/fueling strategies. Each needs exact hooks, available hardware/CPU/RAM/ROM, units and tests. This is a menu of engineering possibilities, not implemented features.

The engine ECU and the 5EAT transmission controller are distinct control roles. Reading a TCU gear byte or changing engine torque does not automatically reprogram shift pressures, solenoid schedules or converter control in the TCU. That is a separate identification/communication/firmware task. A manual-gear request does not turn a torque-converter automatic into a DCT.

## Power, response and evidence
A compiled firmware patch is not inherently more powerful than a well-calibrated stock algorithm on the same hardware. Useful improvements come from a needed control capability, correctly matched calibration or more trustworthy instrumentation. Software does not remove turbo compressor limits, fuel capacity, knock margin, thermal limits, mechanical stress or transmission torque constraints.

There is no single formula that turns every table into its best value. Fuel instrumentation calibration can sometimes use a specific error relationship. Timing for best torque requires suitable torque and knock evidence; an ordinary road log cannot demonstrate maximum-brake-torque timing in every cell. Boost control is dynamic and depends on actuator/plumbing/turbo behavior. Axes, switches and protection thresholds express algorithm structure or requirements rather than a universal power objective.

Before enabling any new behavior, separate a diagnostic-only build from actuator-changing code. Verify memory allocation, stack/calling convention, timing deadlines, reset/fallback paths and exact original bytes. A first-gear predicate is not data freshness. Active-table choice and total compensated commands cannot be inferred merely from a base table lookup.

## Current highest-value sequence
Finish direct editor/IDA access and evidence checkpoints -> reconcile exact source/tool versions -> pending TCU status/freshness investigation and parallel ROM/RAM audits -> diagnostic-only A2WC511R patch preserving OEM paths -> independent offline diff/checksum review -> separate operator-approved physical test plan. Do not mix an OEM-sensor delete or new exhaust configuration into this integration milestone.

References: pinned upstream README.md and README_PORTING.md in sources/upstream; docs/MERPMOD_VERSION_AND_BUILD.md; state/SYMBOLS.json; original logs in evidence. These distinguish source facts, user observations and proposed design.
