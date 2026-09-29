# Vehicle and hardware ledger
All vehicle details below are user/conversation reports, not physical inspection by the handoff author. Verify current installed state before calibration or testing.

| Item | Last reported state | Confidence / action |
|---|---|---|
| Chassis | 2005 USDM Subaru Outback XT Limited | Verify VIN/model/ECU part label locally; no VIN included here. |
| Engine | EJ255 turbocharged2.5L | Confirm actual engine/rebuild/compression before power tuning. |
| Transmission | 5EAT, automatic Drive and manual/SportShift gears1–5 | Not dual clutch; no separate TCU firmware modification authorized. |
| ECU | A2WC511R, ID2F12515306,1MiB SH7058-family ROM | Identity appears in archived reads and user IDA output. Exact CPU suffix/ECU PCB part number still needs physical/document confirmation. |
| Turbo | IHI VF52, reported remanufactured | Actuator preload/spring, reman specification and health unverified. |
| Boost control | GrimmSpeed3-port electronic boost-control solenoid | Confirm actual port routing, restrictor configuration and leak-free reference lines before boost commands. |
| Intake/MAF |3-inch housing cold-air intake | Exact geometry/scaling/current filter arrangement needs inventory. |
| Intercooler | Stock TMIC reported earlier | Treat as last report, not newly verified. |
| Bypass/BOV | HKS SSQV4 / VTA reported earlier | Current installed/recirculated state not verified. Do not disable OEM valve as a prerequisite. |
| Fuel |93-octane reported earlier | Grade, AKI/RON, ethanol content and actual tank fuel must be measured/confirmed. |
| Pump/injectors | Upgrade questions asked; no definitive current upgrade evidence | Record part numbers, flow/reference pressure and latency source; never assume larger parts. |
| Gauge/controller | Innovate ECB-1, reportedFW1.02; LM Programmer4.09 | Verify exact versions, wiring, grounds and scaling locally. |
| Wideband | BoschLSU4.9 via ECB-1, previously in downpipe | Do not wire directly to OEM A/F inputs or assume measured accuracy from brand alone. |
| Other gauge sensors | Boost sensor; ethanol/fuel-temp sensor reportedly all installed | Physical routing and wiring not inspected here. No extra AFR sensors assumed. |
| USB interfaces | Tactrix OpenPort2; serial adapter for Innovate previouslyCOM3 | Resolve ports/device serials on host. No simultaneous hardware clients. |
| Exhaust/O2 | Original sensor arrangement retained for current work | Hood dump-only/wideband-only retrofit explicitly deferred. Prior welding/catalyst changes need current photo/inspection before testing. |

## Mechanical/logging history to retain
Earlier boost noise investigation considered up-pipe/turbo flange leak, downpipe weld/sealer, and boost-hose tee routing. A through-bolt repair improved boost to a reported16psi; smoke did not substantially improve. Turbo oil-feed leakage had been addressed earlier. Neither a historic boost number nor a repair report proves current health.
There were earlier unintended stalls (distinct from an intentional shutdown), with engine power/steering assistance lost. The prior tuning discussion also included shift/tach/TCU-code issues P0700/P0725/P1718, and locked fine-learning. Their present resolution is not established by the gear-only logs.

The user wants a responsive/fun rally/track car and eventually automatic-compatible launch/limited ALS, not street manners as the main objective. That does not establish mechanical endurance, safe temperature margins, or firmware correctness. Keep tuning/calibration validation separate from the current code port.

## Measurements needed before later power work
Current fuel grade/ethanol; actual injector/pump/pressure; wideband calibration/ground offset and logging delay; boost control plumbing and spring response; compression/leak-down when indicated; oil/coolant/ATF health; present DTCs and protection configuration; wheel/tire and gear-speed assumptions; engine/TCU/calibration hashes. These are not prerequisites to doing read-only offline IDA analysis.
