# A2WC511R Simulator Acceptance Checklist

Use this as the minimum checklist before treating the simulator as a substitute for plugging into the vehicle for a RAM/function investigation.

## Identity and memory
- [ ] Test ROM hash recorded.
- [ ] 1 MiB ROM mapped read-only.
- [ ] FFFF0000-FFFFBFFF RAM mapped with bounds checking.
- [ ] Big-endian multi-byte operations verified.
- [ ] Reset PC 00000AAC and SP FFFFBFA0 decode regression passes.
- [ ] Stack overflow/collision detection enabled.

## CPU/execution
- [ ] Supported opcode list generated automatically.
- [ ] Unsupported opcode is a hard/visible stop.
- [ ] SH delay-slot behavior has independent tests.
- [ ] Function harness verifies register/stack preservation.
- [ ] Memory watchpoints report PC + call context.

## Known-routine anchors
- [ ] sPull2DFloat 0000209C
- [ ] sPull3DFloat 00002150
- [ ] sMafCalc 000079A8
- [ ] sWgdc 00014B20
- [ ] sDecodePackedGearRangeByte 000147AC-00014802
- [ ] sTestTcuStatusMask02 00015A02-00015A16
- [ ] sUpdateTcuDerivedSnapshot 00015A2C-00015D46
- [ ] sResetTcuDerivedSnapshot 00015D46-00015D92
- [ ] sRevLimStart 000317D8 only after remaining exact flags are proven

## 5EAT behavioral tests
- [ ] 88=P, 77=R, 00=N
- [ ] 11..55 stable forward states
- [ ] 21/32/43/54 upshift transitions
- [ ] downshift transition equivalents
- [ ] 8 maps to 0 in decoded nibble path
- [ ] 9..F hold-last-value decoder behavior
- [ ] Reverse normalization to E8/E9=1 behavior
- [ ] source/snapshot disagreement scenario
- [ ] candidate validity/status drop scenario
- [ ] stale-data scenario clearly marked as modeled, not proven real behavior

## Differential execution
- [ ] Same stock scenario replay is byte/trace reproducible.
- [ ] Diagnostic patched candidate changes only declared code/RAM/diagnostic allowlist.
- [ ] Undeclared timing/fuel/WGDC/DBW/rev-limit/transmission-torque differences fail.

## Definitions/tables
- [ ] Actual ROM bytes are authoritative for each run.
- [ ] Axis ordering and storage endianness verified.
- [ ] Pull2D/Pull3D randomized cross-checks pass for selected tables.
- [ ] Native RomRaider model agrees with independent decoding or discrepancy is documented.

## Virtual logger
- [ ] Existing A2WC511R logger definition used unchanged.
- [ ] ECU ID 2F12515306 presented by simulator backend where applicable.
- [ ] Direct RAM reads return simulator RAM.
- [ ] Standard SSM parameters used by tests return expected virtual state.
- [ ] Simulator transport/provider is side-by-side with real OpenPort provider and reversible.
- [ ] No physical PassThru calls occur in simulator mode.

## Reporting
- [ ] Coverage report saved.
- [ ] Unsupported opcode/peripheral list saved.
- [ ] Scenario seeds saved.
- [ ] Dynamic address propagation report saved.
- [ ] ROM hashes saved.
- [ ] Explicit list of remaining bench/vehicle-only validations saved.
