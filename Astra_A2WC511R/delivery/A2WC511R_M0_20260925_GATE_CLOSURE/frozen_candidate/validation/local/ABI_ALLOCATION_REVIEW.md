# A2WC511R diagnostic hook and allocation investigation

Status: integration allocation and timing gates remain OPEN. This document records actual static evidence, not approval to flash.

The existing IDB was opened through official Hex-Rays ida-mcp 20260924.0.3 after a closed-database backup of the .i64 and sidecars. No ROM byte patch was made in IDA. IDB image SHA256 is a34c4ce8238bf28bdc18c191bbe73b2179130aa9846e952a6fa332bae442de96; the independent baseline is 22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218. Their only difference is the editor stamp at [FFC4C,FFC50), outside all routine windows discussed below. Exports in reports/local/ida contain exact bytes and distinguish persistent IDA code from forced displayed disassembly.

## Hook evidence

The existing named function sDecodePackedGearRangeByte occupies [147AC,14802). Its 43 instructions read the packed byte at FFFF4C8D and conditionally write only FFFF4BC1 and FFFF4BC2. It has no calls, stack access or FPU instructions. High and low nibble values 0..7 are copied, 8 becomes 0, and 9..15 retain the corresponding prior destination. These are software decoder semantics; they do not establish physical gear engagement.

The actual call sequence is 1193A: D268, loading r2 from the pool word at11ADC; 1193C: jsr @r2; 1193E: nop. The original pool word is000147AC. Normal continuation is11940, which loads the next routine14882 into r3, then calls it. A raw PC-relative MOV.L scan over [0,859BC) finds exactly one instruction loading11ADC, at1193A. The IDB has a real call xref1193C to147AC plus separate data references1193A/11ADC. Data references are not counted as additional callers.

The diagnostic wrapper must invoke the original decoder, preserve its post-return integer registers, SR, MACH/MACL and caller return path, and avoid FPU instructions throughout its linked closure. Differential execution against the compiled wrapper is a separate evidence gate. No MAF/WGDC/rev-limit/timing/fueling hook is required for this observer. The surrounding scheduler dispatcher is not represented as a complete function in the current IDB. Call frequency, all entry paths, reentrancy, interrupt nesting and worst-case task-stack headroom have not been established.

## Actual reset and memory evidence

ROM words FFE4/FFE8 contain FFFF0000/FFFF1FFF, FFEC/FFF0 contain FFFF2000/FFFF2CFF, and FFF4/FFF8 contain FFFF2D00/FFFFBFFB. The reset routine atF928 reads the final pair, invokes the RAM-test helperFA58, uses alternate-stack helpers4BB8/4BBE, and invokesF9BC. AtF9BC, DMA channel registers ECC0/ECC4/ECC8/ECCC are configured using those bounds. The transfer count calculation is `(end - start + 1) >> 2`, and the routine waits on completion. This is positive evidence of a bulk access crossingFFFF7400; an absent pointer literal to7400 is not evidence of no access. Reset-time clearing can be compatible with later diagnostic initialization, but does not prove exclusive runtime ownership.

The boot vectors contain SP FFFFBFA0. The normal runtime entryF60C sets VBR toFFC50, sets FPSCR to00040001, and loads SP from the ROM wordFFE0, which isFFFF1304, through4BC2. The RTOS code at3CBA saves a stack pointer throughFFFF12D8; at3CC8 it loads another from ROM4880, whose value isFFFF119C. Accordingly, using only the reset-vector SP as the runtime task-stack bound is incorrect. The boot code also reads/writesFFFFBFFC as the5AA5A55A marker; the final RAM word is not a free allocation alternative.

The highest ordinary absolute RAM scalar in the observed lower data area includesFFFF736C. Code71CDE clears that byte, while7BC2A and other routines consume it. TheFFFF7FFF literal at3870 is used as an AND mask at37DA, not as a pointer into a buffer. These distinctions narrow investigation, but the current IDB contains only913 defined functions and has many executable regions without complete function metadata. A complete indirect/base-plus-offset/DMA access and task-stack proof is not supplied by the literal inventory.

### Bounded task-owner follow-up

A subsequent focused trace narrows the owner chain. RTOS routine3930 indexes ROM table48D8 in16-byte records. Slot9 begins4968: its state pointer at496C isFFFF11E4 and entry address at4970 is6580. At6580 the entry saves PR;659A loads11134 from pool6624, then659C calls it. The dispatcher at11134 saves PR, contains the1193A packed-decoder call, and eventually tail-jumps at11A7A while restoring PR in the delay slot11A7C. Thus the task and dispatcher contribute8 bytes of saved return addresses around the candidate wrapper. The original decoder itself is a leaf without stack use.

The table's type/priority bytes must not be interpreted as an integer stack size. At3FE4 the scheduler initializes its saved-SP field from4880=FFFF119C. At3DC8 and following it saves general registers, GBR and MAC state, and conditionally FPU registers for task type4. At3DF8 it records a live SP into a control structure; resume paths later restore saved contexts. Those are positive evidence of context-dependent stack use, not separate fixed stack budgets per table row. This follow-up identifies a task entry and nominal call nesting, but does not bound every interrupted/preempted context or establish the periodic trigger/cadence. Additional wrapper cost and actual total headroom remain separate questions.

## Experimental locations and remaining gates

E1000 is inside an FF-filled region of the exact baseline. FFFF7400 is a proposed32-byte observer state region above observed scalar736C. Neither is certified exclusively available. Experimental linking and emulator overlays at these addresses are useful to measure exact size, test wrapper behavior and verify patch serialization. They do not transfer ownership of those addresses to the new code.

Before a physical-test candidate is recommended, establish the final linked ROM interval against vectors, checksums, indirect table readers and boot/reprogramming behavior; establish the32-byte RAM interval against all relevant runtime bulk/indirect writes; and bound the actual caller task's stack and execution-time budget with the compiled wrapper included. The extra stack size alone does not prove headroom. Simulator instruction counts are not SH7058 cycle/watchdog/interrupt timing measurements.

Freshness remains UNKNOWN in the real hardware binding. Neither4CA1 nor4C50:02 is promoted to a global communication-validity guard. Repeated raw reads can detect a change but cannot prove a coherent asynchronous snapshot. Diagnostic reasons retain those uncertainties and confer no output authority.

## Exact evidence files

- reports/local/ida/initial_static_audit.json: input identity, saved function boundaries, decoder/reset windows.
- reports/local/ida/allocation_static_audit.json: known-code special instructions, candidate literals, call-site/reset windows.
- reports/local/ida/hook_ownership.json: raw pool-load scan, runtime entry, stack-switch and nearby RAM windows.
- reports/local/ida/task_stack_audit.json: task-table indexing, slot9 entry6580, caller11134, and RTOS save/restore windows.
- work/ida_audit_initial.py, work/ida_allocation_audit.py, work/ida_hook_ownership.py: repeatable read-only vendor-MCP analysis scripts.
- reports/local/ida/*.json timestamped records: actual MCP requests/responses and discovered tool schema.
