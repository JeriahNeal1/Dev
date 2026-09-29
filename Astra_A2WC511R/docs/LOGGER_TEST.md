# Pending six-channel snapshot/status observation

Use the latest full XML in `definitions/`. It preserves the previous channels. This is an observation definition, not proof of the semantics implied by a channel's historical name.

| Select this exact channel | Physical ECU RAM | XML SSM address | Interpretation |
|---|---|---|---|
| A2WC511R TCU Status Flags* | FFFF4C50 | FF4C50 | Whole byte, raw. Analyze mask 0x02 afterward. |
| A2WC511R TCU Derived Data Valid* | FFFF4CA1 | FF4CA1 | Historical name; global freshness is not proven. |
| A2WC511R Packed Target/Current Gear Source* | FFFF4C75 | FF4C75 | Upstream byte copied by the updater. |
| A2WC511R Packed Target/Current Gear Snapshot* | FFFF4C8D | FF4C8D | Downstream snapshot, interpreted as target/current nibbles. |
| Engine Speed | Standard P8 | 00000E, length 2 | Existing RPM conversion. |
| Vehicle Speed | Standard P9 | 000010 | Record which units are selected. |

Keep these six selected for this narrow test. Do not disable ECU protections or reconfigure hardware. No new ROM flash or MerpMod installation is required. Fewer requested channels may reduce polling load; they do not guarantee an exact sample rate.

Suggested observation: connect with the key ON and engine OFF when available; capture startup; then dwell about three seconds in each of P, R, N and D while stationary with the service brake held. If the vehicle is mechanically sound and the operator judges it appropriate, capture a short gentle 1–2–3 drive. The agent does not drive or operate the laptop while driving. Return to a complete stop before N/P and normal shutdown. Never select Reverse or Park while moving. No hard throttle, brake-boosting, launch or forced-fault test is required.

ECU communication may stop during cranking or key-off. Save/restart logging normally and record the gap. Do not invent zero channel values after disconnection or repeatedly cycle power just to force a desired result.

Calculate row counts, header-only files, timestamp gaps, raw value counts, source/snapshot mismatch durations, CA1 and `(C50 & 2)` states, and startup/shutdown transitions. Record any normal first-gear state with different status values. Preserve original row order and keep a separate event note. A constant 1 during normal operation does not prove that the flag drops on communication loss. Pair observations with static packet/timeout analysis; one-sample order alone does not establish causality.

The historical XML description calls CA1 a statically verified validity latch. It is preserved byte-for-byte for continuity, but that description is not a machine-validated fact. Do not alter conversions to force the expected result.
