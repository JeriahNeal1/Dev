# Simulator final handoff

The isolated simulator at `C:\Dev\A2WC511R_Sim` validates actual stock bytes and the frozen experimental diagnostic payload. It does not accept a real ECU allocation or flash.

- 31 core/anchor tests pass; all51 supported integer/system-transfer forms exercised.
- Stock decoder:1792 cases, all43 instruction addresses and both outcomes of all4 conditional branches. Status helper:256 cases, all10 instructions.
- Frozen build: `C:\Dev\Astra_A2WC511R\work\builds\m0_final_05`. Payload SHA-256 `b5004baa2863bf571eb1ab014f93f0316b3500c5b154e47de2e42f904234b2ff`.
- 1024 stock/compiled-wrapper pairs pass at direct and actual1193A→11940 callsite boundaries. All16 general registers, SR/MACH/MACL/PR, continuation and OEM data effects match.
- All diagnostic state writes obey odd/even publication;10 explicit init/reinit cases and4 explicitly modeled second-read changes pass. Observer freshness stays UNKNOWN.
- Observed extra stack124bytes;291..483 extra executed instructions. Separate task/dispatcher frames add8bytes; RTOS/interrupt headroom and cycle/scheduler timing remain unproven.

Executed02, reviewed03, frozen05 and repeat06 payload/ELF identities were checked byte-for-byte by SHA-256. The full pair test is reused by identical binary identity. The final JSON records exact manifests, logs and source hashes.

Reproduce from the simulator directory with `py -3.14 run_validation.py` and `py -3.14 run_differential.py`. Each run preserves reports under a new UTC directory. Unsupported opcodes, peripherals, uninitialized RAM and memory-policy violations stop visibly.

Final manifest: `C:\Dev\Astra_A2WC511R\reports\local\simulator\final_20260925T202206.384242Z\final_validation.json`

Anchor report: `C:\Dev\A2WC511R_Sim\runs\20260925T202126.230415Z\coverage.json`

Differential report: `C:\Dev\A2WC511R_Sim\runs\20260925T201917.102870Z_differential\coverage.json`

No physical device or real RomRaider/J2534 provider was accessed. Full boot, FPU, interrupts, watchdog, DMA, analog behavior, transmission mechanics and active-control safety remain outside coverage.
