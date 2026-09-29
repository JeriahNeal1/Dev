# A2WC511R offline function simulator

This isolated project executes selected SH-2E big-endian instructions from the user's actual A2WC511R ROM. It is a software function harness, not an engine/transmission simulation or a flashable image. It never opens a physical device, calls J2534, or changes the OEM ROM.

Run from this directory with the existing Python 3.14 installation:

```powershell
py -3.14 run_validation.py
```

Each invocation creates a new immutable `runs/<UTC>/` report directory. `coverage.json` records ROM SHA-256, source hashes, test count, exact function coverage and limitations. `test_log.txt`, `supported_opcodes.json`, `unsupported.json`, `sample_traces.json` and `address_propagation.json` provide review evidence. No dependencies are installed.

The compiled diagnostic wrapper has a separate validation command:

```powershell
py -3.14 run_differential.py
```

This verifies the manifest hash of the compiled experimental closure, overlays only its declared code and hook-pointer spans in immutable in-memory ROM, and runs 1,024 stock-versus-patched cases: all 256 packed bytes, cold/warm observer state, direct function boundaries and the actual `1193A..1193F` callsite through continuation `11940`. It compares all 16 integer registers, SR/MACH/MACL/PR, return PC, original decoder instruction/data behavior and RAM outside the explicit diagnostic/stack allowlist. It also checks the 32-byte observer result against an independent reference, publication writes under odd sequence, counter wrapping, deterministic replay and negative mutations. Four separate, explicitly modeled input changes verify capture-change reporting without claiming communication freshness.

For compiled payload SHA-256 `b5004baa2863bf571eb1ab014f93f0316b3500c5b154e47de2e42f904234b2ff`, the observed maximum extra stack is 124 bytes and extra executed instructions range from 291 to 483. This measures functional execution overhead, not CPU cycles or scheduler acceptance. Separate static evidence identifies another eight bytes in the surrounding task/dispatcher PR frames; RTOS/interrupt headroom is still unbounded. The ROM/RAM spans `E1000..E1363` and `FFFF7400..FFFF741F` are virtual experimental allocations and remain unaccepted for physical deployment.

The initial anchors are the original packed decoder at `147AC..14801` (all 256 inputs crossed with seven prior-byte pairs) and status helper at `15A02..15A15` (all 256 status bytes). All 43 decoder instruction addresses and both outcomes of its four conditional branches are exercised. All 10 status instructions are exercised. The known 8-to-zero and 9..F hold behavior is validated from actual ROM execution. The P/R/N names remain historical software interpretations and do not prove physical engagement or freshness.

`sh2e.py` supplies immutable, hash-checked 1 MiB ROM with labeled in-memory overlays; a bounded `FFFF0000..FFFFBFFF` RAM map; uninitialized-read failures; aligned big-endian loads/stores; a table-driven supported-opcode list; instruction budgets; execution-range restrictions; guarded virtual stack; caller-configured register preservation; trace/watchpoints with PC, nested call context, value/address provenance and conservative path-condition provenance. Unknown instructions, peripherals, RAM execution and unsupported PC-relative delay-slot cases fail explicitly. SR storage and T-bit operations are modeled; other SR effects, interrupt timing and FPU execution are not.

The harness uses a declared virtual stack ending at the decoded OEM reset SP. Its guard checks do not establish real ECU stack headroom or prove any RAM allocation unused. Diagnostic differential tests may exclude explicitly declared transient stack bytes and diagnostic state, while failing other writes. Such exclusions are test policy, not an accepted physical memory map.

The core is an original, small implementation based on the [Renesas SH-2E Software Manual, REJ09B0316-0200](https://www.renesas.com/en/document/mah/sh-2e-software-manual). Local HEW includes a proprietary SH-2E simulator DLL but no auditable core/API was found for this task. The existing KPIT SH objdump independently disassembles the two ROM anchors; the live official IDA export provides separate static evidence. No competing IDA tool or provider was installed.

Still outside coverage: Pull2D/Pull3D, MAF/WGDC/rev-limit code, normalized gear updater, TCU snapshot/reset code, interrupt/exception dispatch, DMA, watchdog, pipeline/cycle accuracy, physical communication timing, analog/electrical behavior, fuel/boost/AFR/knock, transmission hydraulics, and virtual RomRaider transport. No simulator pass here accepts active controls or substitutes for those bench/vehicle checks.
