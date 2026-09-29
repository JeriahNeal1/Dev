# M0 runtime gate evidence

Frozen final05 payload `b5004baa2863bf571eb1ab014f93f0316b3500c5b154e47de2e42f904234b2ff` is unchanged. 52 regression tests returned PASS; 1024 paired stock/wrapper cases were rerun on the extended interpreter. The generated JSON files contain exact code bytes, CFG edges, call literals, frame depths, source hashes and watchpoint records.

| Routine | Local frame bytes | Peak including callees | Conservative instruction bound |
| --- | ---: | ---: | ---: |
| OEM decoder | 0 | 0 | 36 |
| m0_decode | 0 | 0 | 11 |
| m0_reasons | 0 | 0 | 68 |
| m0_init | 0 | 0 | 202 |
| m0_observe | 24 | 24 | 412 |
| m0_sample_hardware | 24 | 48 | 478 |
| m0_decoder_hook | 76 | 124 | 562 |

The full injected graph is hook → OEM decoder, then hook → sampler → observer → initializer (conditional) and reasons. The compiler inlines decoded-nibble logic; standalone m0_decode is unused by the hook. All returns balance SP, all graph joins agree on frame depth, and the only injected back edge is the initializer's fixed 28-iteration loop. The exact added stack maximum is124 bytes; the surrounding known OEM task/dispatcher save another8 bytes. This does not bound full RTOS/ISR occupancy.

The actual wrapper's45 save/restore words establish R0–R14, SR, MACH, MACL, PR and SP preservation at return, assuming writable private stack disjoint from observer state. Every reachable instruction is decoded; none accesses FR0–FR15, FPUL, FPSCR, GBR or VBR. This is architectural preservation, not an interrupt-latency equivalence claim.

The conservative full-hook bound is562 instructions including the original decoder; additional instruction work is bounded by526. The refreshed scenarios observed291–483 additional instructions. A serialized envelope is `C <= 5*N + (F-1)*N + (D-1)*A + entry_stalls + external_interference`, where F/D are explicitly assumed upper memory-service times, N=562 and A=178. Example F=2,D=2 with no external/entry term gives3550 cycles,44.375µs at an assumed80MHz. The hardware maximum frequency is not a measured ECU clock. Silicon timing and scheduling margin remain **PHYSICAL/BENCH REQUIRED**. [Renesas software manual](https://www.renesas.com/en/document/mah/sh-2e-software-manual), [SH7058 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual).

An explicitly modeled nested writer reproduces invalid publication while an even sequence is visible. Unconditional reentrancy is **FAIL**; one nonreentrant writer is mandatory. Normal task activation is reported separately by the RAM/RTOS investigation as160000Pphi cycles per task9 enqueue. Reentry exclusion, actual clock, missed/coalesced events and response time must be established by that gate.

The actual FA58 routine overwrites the full [FFFF2D00,FFFFBFFC) reset-test span withA55A5AA5, including the proposed state. Watchpoints identify both write PCs and pointer/value origins; outer2CFC/BFFC sentinels remain unchanged. The C31E..C376 setup fragment writes an explicit finite DMA2/3 configuration fixture; activation and status reads fail. No DMA transfer is fabricated. Full-byte index arithmetic keeps that setup's ordinary buffers below7400; this is scoped access evidence, not lifetime ownership.

`whole_hole_dynamic_summary.json` separately counts ROM fetch/read/write access in [CE754,FFAF8) and [859BC,C0000) across every paired case. Stock known-routine cases have zero access; patched access is confined to the injected code/literals. No inference about unexplored firmware paths is made.

Use `py -3.14 run_gate_closure.py` for all regressions, or `py -3.14 gate_scenarios.py` for15 sequential immutable RAM snapshots usable by Codex and the isolated virtual-logger backend. Unknown RAM/peripheral reads fail; snapshots label their timing and input values as virtual. Historical runs and the pre-extension source backup are retained.
