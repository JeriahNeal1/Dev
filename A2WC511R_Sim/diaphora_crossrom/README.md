# Cross-ROM correspondence regressions

This independent branch compares actual stock division and range routines across the ten pinned public ROMs in `C:/Dev/Astra_A2WC511R/reports/local/diaphora/rom_inventory/public_rom_manifest.json`. It preserves the frozen M0.7 simulator, source, reports and payloads. The75-form `sh2e.py` remains SHA256 `b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff`.

Run from `C:/Dev`:

```powershell
py -3 C:\Dev\A2WC511R_Sim\diaphora_crossrom\crossrom_regression.py
```

`LATEST.json` identifies the timestamped report and its hash. Each run writes only this subtree:

- `mapping.json`: pinned ROMs, concrete entry/pool/RAM-role mappings, native disposable-export provenance, and static instruction/span accounting.
- `crossrom_regression.json`: final counts, exact comparison contract, instruction coverage, negative controls and limitations.
- `representative_traces.json`: one actual compiled range trace per ROM, including all reads/writes, address origins, call context and initialized virtual input values.
- `small_wrapper_prefix_candidates.json`: six bounded wrapper/reader proposals, including duplicate matches; these remain unexecuted proposals without ownership claims.

The interpreter is imported with bytecode-cache writes disabled. ROMs are immutable and SHA256 checked. Unsupported instructions, uninitialized RAM, undeclared writes, execution outside the validated CFG and unmapped peripherals fail explicitly. No timing, DMA, interrupt, floating-point or physical vehicle model is substituted.

## Validated correspondence

Division bytes `[4260,430A)` are identical in all ten ROMs. Its two external pool words at `430C` and `4310` are also explicitly checked: error destination `FFFF130C` and value `0000044E`. The suite runs633 dividend/divisor scenarios per ROM, including signed boundaries, zero divisors, all256 existing SSM length-domain dividends and256 seeded random pairs. It compares actual addresses without relocation normalization.

Range candidates are found independently of Diaphora by a strict masked entry pattern, then checked with a complete supported leaf CFG. Both branch outcomes and every delay word are included. Calls, indirect control transfers and opaque instructions reject the candidate. PC-relative operands are resolved from each ROM rather than copied from A2WC511R.

| ROM | Entry | Input byte | Updated flags byte | Range output byte |
|---|---:|---:|---:|---:|
| A2WC412D | `1447C` | `FFFF4C58` | `FFFF4BA4` | `FFFF4BB4` |
| A2WC500R | `146AE` | `FFFF4C8C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WC510C | `1466E` | `FFFF4C8C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WC510R | `1466E` | `FFFF4C8C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WC510S | `1466E` | `FFFF4C8C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WC511R | `1466E` | `FFFF4C8C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WC521C | `1466E` | `FFFF4C9C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WC521R | `1466E` | `FFFF4C9C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WC522S | `1466E` | `FFFF4C9C` | `FFFF4BA4` | `FFFF4BC0` |
| A2WF200R | `1590E` | `FFFF4CA8` | `FFFF4BB0` | `FFFF4BCC` |

All ten range functions contain95 reachable instructions, or190 instruction bytes. Their four literal dependencies are retained individually. A2WC412D's entry-to-return span is232 bytes; the others are318 bytes. The difference is the intervening pool/layout, not executable compression. Its first three instructions also reorder independent immutable-ROM/immediate loads into distinct R3/R4/R6; the comparison explicitly allows this scheduling difference. It changes ROM read order, which is reported rather than silently treated as an identical bus trace.

The recorded disposable native export recognizes all ten division entries and nine range entries. A2WC412D `1447C` has no exact native function start in `A2WC412D_stock_01.analysis.json`; its correspondence here is independently checked raw-code/CFG/emulator evidence, not a reported native Diaphora function match.

Each ROM runs every256 input-byte values with eight prior flag seeds, for2,048 range scenarios. The comparison normalizes only the three declared RAM roles and the final R3 output pointer. It compares all other GPRs, SR, PR, SP, MACH, MACL, return PC, full canonical RAM bytes and initialization bitmap, and ordered RAM/MMIO access events exactly. Neither routine calls another function. Stack sentinels are included; there is no excluded extra-stack slot because both sides are OEM routines.

The initial complete suite passes6,330 division and20,480 range comparisons and executes all85 division/95 range reachable instructions per ROM. No reachable instruction touches the FPU. That is static instruction exclusion; the integer interpreter does not simulate FPU preservation.

## Negative controls and boundaries

The suite changes the `range=1` result instruction to return2 and requires both structural and actual state/RAM comparisons to detect it. It also requires failure when the521R candidate is initialized at511R's wrong input address, when an input ROM hash is incorrect, and when the division entry is replaced with an unsupported opcode. These controls fail before any correspondence is accepted.

Function correspondence under the stated entry/input/memory contract is **PASS**. Exclusive ROM/RAM ownership and complete firmware correspondence remain **FAIL**. Silicon timing, interrupts, peripheral behavior and physical transmission interpretation remain **PHYSICAL/BENCH REQUIRED**. The scenarios are finite and do not prove arbitrary machine states, interior entries or all consumers. Diaphora matches and native xrefs are proposals/evidence, not a replacement for those gates.

The small-function inventory includes existing division-adjacent wrapper `4B04`, packed decoder `147AC`, status reader `15A02`, cruise readers `18012/18026` and clutch reader `23B12`. Prefix matches can be nonunique, data or dependent on different external literals. Even full span equality is not a free-space or semantic proof. No replacement is built or enabled by this branch.

## Existing MerpMod mapping branch

`merpmod_mapping.py` separately consumes the pinned final03 Diaphora results and supplemented510S/522S/archive native exports. It writes only `C:/Dev/Astra_A2WC511R/reports/local/diaphora/merpmod_mapping`, with frequent checkpoint files. Run it directly with `py -3` to reproduce four hook/callsite assertions, six stock function identities, twenty negative controls, archived code/data classification and the isolated120-byte virtual RAM-clear leaf test.

The archive's RAM base is `FFFF73B0`, its clear endpoint `FFFF7428`, and its custom control routine is called from MAF. These are existing binary facts, not current-source build assumptions. `REVIEWED_MATCHES.json` records six structural identities and three rejected matcher proposals in actual primary→secondary result direction. No active control, FPU/kernel/MMIO path, source build, ROM patch, IDA update or core mutation occurs.
