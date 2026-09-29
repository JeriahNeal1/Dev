# Deterministic SH7058 reset-prefix validation

This is a separate project layer over the unchanged 75-form `../sh2e.py` core. It executes an actual immutable 1 MiB image from its power-on PC/SP vectors. It does not substitute a function fixture for reset or fabricate SSM readiness. The current complete-boot classification is **CONDITIONAL**.

The default stock run retires 57,658 instructions at 801 unique PCs. It executes bus and port initialization, both HCAN configuration paths, boot communication RAM setup, the OEM seven-interval boot wait, application entry `1150` â†’ `F60C`, VBR/FPSCR initialization, the switch to application SP `FFFF1304`, and the start of module initialization. It stops **before** the write at `4B4C` that changes SYSCR2 from the earlier clock configuration to `3C88`. The post-change peripheral-clock phase and initialization contracts have not been modeled. Application SCI/SSM initialization and the main OEM RAM initialization at `F928` have not been reached.

## Reproduce and integrate

```powershell
py -3 C:\Dev\A2WC511R_Sim\preflash_boot\boot.py --image C:\Dev\SubaruRoms\OEM\A2WC511R.bin --expected-sha256 22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218 --output C:\Dev\Astra_A2WC511R\reports\local\prehardware\boot\my_new_stock_run.json
py -3 C:\Dev\A2WC511R_Sim\preflash_boot\test_boot.py
```

For a differential run add `--stock STOCK_PATH --expected-stock-sha256 STOCK_HASH` and use `--image CANDIDATE_PATH --expected-sha256 CANDIDATE_HASH`. Existing result paths are refused. Optional `--scenario-json` declares fields of the `Scenario` dataclass; `--max-steps` sets the finite instruction budget. Exit code 2 means FAIL; exit code 0 means the JSON must still be inspected, because a known frontier is CONDITIONAL. No current path can return full boot PASS.

Python API:

```python
from boot import Scenario, run_image, compare_images
result = run_image(path, expected_sha256=expected_hash,
                   scenario=Scenario(), evidence_dir=new_trace_directory)
comparison = compare_images(stock_path, candidate_path,
                            expected_stock_sha256=stock_hash,
                            expected_candidate_sha256=candidate_hash,
                            scenario=Scenario(), allowlist=(),
                            evidence_dir=new_trace_directory)
```

Results contain schema1, status, image path/SHA/size, reset vectors, scenario, reached milestones, exact stop PC/count, unsupported details, `ssm_readiness.reached`, coverage, stack bounds, IRQ decisions, watchdog state, final system registers, ordered write/control traces and trace hashes. `stop.kind` distinguishes an identified model frontier from an execution/input failure. `dependencies()` returns exactly the core, `boot.py` and `manual_evidence.json`; a validator should pin all three independently. Typical comparison time is about 10 seconds on this host, with about 3 MB of gzip traces and 9 MB JSON. A 60-second host timeout is ample for the default scenario, not for arbitrary caller budgets.

Detailed trace artifacts are deterministic `.json.gz` files with zero gzip timestamp and their own SHA256. Use `gzip.decompress(Path(path).read_bytes())` to inspect. Instruction, memory, MMIO-attempt and ordered control traces preserve addresses and inherited provenance/watchpoints. The semantic digest excludes only artifact destination paths; it includes scenario and dependency identities. Replay is deterministic, including repeated loop branches.

Comparison includes every ordered RAM/MMIO write (including transient stack), every modeled branch/delay transfer, and full terminal GPR/system/control state. A register-only mutation at51F8 is rejected even when writes and control transfers are unchanged. The optional Python allowlist admits only exact before/after write-event pairs. It cannot erase arbitrary addresses, control changes, input errors or different stop boundaries. The validator integration uses an empty allowlist. An equal stopped prefix cannot establish behavior of code never executed.

## Explicit model boundaries

- Actual CPU target: SH-2E big endian on SH7058. Ten reached forms are implemented in `BootCPU`, without modifying the frozen core: NOT, MULU.W, STS MACL,Rn, SHLR16, MOV.W displacement store, CMP/PL, CMP/PZ, XOR, LDC VBR, LDS FPSCR. No floating-point arithmetic or exception handler is stubbed.
- NMI and port-B input levels are declared virtual inputs. Peripheral defaults are finite, documented register values. Unknown MMIO fails; ADC/SCI accesses stop at named unimplemented frontiers.
- Power-on RAM is explicitly filled with scenario byte A5 by default, since physical power-on contents are undefined. `ram_power_on_byte: null` enforces uninitialized-read failure. Reset GPRs have explicit poison values and source tags; this is not a theorem over every reset state.
- HCAN configuration assumes an idle bus and no external frames. Only documented register/flag behavior and mailbox writes used by boot are admitted. The model does not claim bit timing, arbitration, a successful transmitted frame, or physical synchronization. Transmission requests fail closed.
- WDT keyed access, divisor selection, overflow flag and interval mode are modeled. The default 16 CPU clock units per instruction is a deterministic timing assumption, **not** a verified silicon bound. The actual prefix uses interval mode; seven observed overflows do not validate watchdog reset safety. Watchdog-mode overflow remains a frontier.
- Interrupt requests are checked outside delay slots and the instruction following LDC. Masked requests remain pending. At an admissible NMI/IRQ the model stops before exception entry; no IRQ is silently serviced or discarded. Full ISR stack/return behavior is unproved.
- Declared SP bounds span internal RAM through the boot SP. Actual SP relocation is recorded. Fixture-filled RAM coverage is reported separately from bytes written by actual firmware. These checks do not prove exclusive stack allocation, total ISR depth or complete RAM ownership.
- PFC writes are observed; output voltage/current, analog inputs, engine and transmission behavior are not simulated. The existing function-fixture SSM tests are separate evidence and cannot prove readiness from reset.

## Evidence and next bounded step

The 64-check run is `reports/local/prehardware/boot/run_20260926T182324.758398Z`; see `regressions.json`, `stock.json` and `stock_vs_frozen_m07.json`. It includes focused new-opcode tests, deterministic replay, real stock/candidate reset execution, ROM hash/size/target/MMIO mutation negatives, stack-bound failure, NMI-low wait, deferred/admissible interrupt boundaries, timer envelope and direct ADC/SCI fail-closed guards. Invalid-sensor recovery, actual ISR execution and application communication startup remain CONDITIONAL/unreached. The frozen M07 image remains residency FAIL even though this prefix is equal.

The next useful offline extension is the exact `4B3E` clock-change sequence: verify SH7058 CKSEL transition constraints and phase relationships, represent the resulting CPU/peripheral clocks, and test its four following NOPs before admitting later UBC/ATU/ADC/SCI setup. The manual proves the selectable multiplication factor, but this run does not invent settling/phase timing. Add peripherals only as the actual reset path reaches them. Primary source references and page numbers are in `manual_evidence.json`.

No provider DLL, J2534 interface, physical vehicle, flash command, active-feature hook, original IDB or frozen M0/M06/M07/Diaphora artifact is changed by this subtree.
