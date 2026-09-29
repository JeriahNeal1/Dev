# Compiled kernel execution model

`KernelSession` executes the exact hash-pinned uploaded bytes. The frozen interpreter at `C:/Dev/A2WC511R_Sim/sh2e.py` remains unchanged. The project subclass adds only six instruction forms needed by this kernel, strict executable-address and private-memory checks, and aggregate execution evidence. Unsupported instructions, MMIO, code targets, uninitialized reads, ROM writes and writes outside private RAM fail visibly.

```python
from sim.harness import KernelSession

session = KernelSession(manifest_path, rom_path, rom_sha256,
                        kernel_bytes=actual_uploaded_plaintext,
                        trace_dir=new_evidence_directory)
ready = session.start(entry=0xFFFF3004)
result = session.exchange(actual_request_bytes)
wire_reply = result.tx_bytes
coverage = session.coverage()
```

The session persists across requests. `start()` emits no invented greeting. Replies consist exclusively of bytes transmitted by executed SCI2 TDR/SSR writes. `exchange()` accepts a complete frame or a partial prefix; a partial request can stop in `RX_WAIT` without a reply. The host must impose its own deadline. `COMPLETE` means the compiled kernel finished both passes, observed TEND, disabled SCI and entered its permanent halt. `KERNEL_REJECT`, `KERNEL_EXCEPTION` and `SIMULATION_FAILURE` are distinct unsuccessful outcomes.

SCI2 models documented read-one/write-zero flags, separate TDR/TSR stages, final TEND, receive flag lifetime and TE0 abort. Scheduling uses explicit virtual instruction ticks. It does not model physical baud, bit waveforms, automatic overrun from an analog source or interrupt delivery. The default collapsed one-tick schedule is useful for complete bytecode execution; delayed-stage controls exercise buffering and polling independently. Registers have an explicit fixture state, never a zero-default MMIO fallback. RAMER/FMATS guards, PCCR, DMAOR and WDT are the only other admitted peripheral surfaces.

The optimized path is generated from the pinned frozen `CPU.step` AST by `generate_fast.py`. It removes verbose trace/provenance allocations and caches immutable opcode lookup; it executes every architectural instruction and loop iteration. `verify_fast.py` compares complete architectural and memory/peripheral state after every instruction. Saved models used by full runs remain under `evidence/sim/model_v1` and `model_v2`; `verify_model_projection.py` proves the precise collapsed-schedule applicability to the later two-stage model. Earlier runs are not relabeled as having used later source.

From the project root:

```powershell
py -3 -B -m unittest sim.test_model -v
py -3 -B -m sim.verify_fast --manifest build/attempt_03/manifest.json --rom C:/Dev/SubaruRoms/OEM/A2WC511R.bin --rom-sha256 22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218 --out evidence/sim/NEW_parity.json
py -3 -B -m sim.full_read --manifest build/attempt_03/manifest.json --rom C:/Dev/SubaruRoms/OEM/A2WC511R.bin --rom-sha256 22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218 --out evidence/sim/NEW_stock
py -3 -B -m sim.qualify_faults --manifest build/attempt_03/manifest.json --rom C:/Dev/SubaruRoms/OEM/A2WC511R.bin --rom-sha256 22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218 --out evidence/sim/NEW_faults
```

Use fresh output paths; these commands refuse to overwrite prior run evidence. `package_qualification.py` packages the specifically named completed stock/fault/parity/projection runs into `evidence/sim/QUALIFICATION.json` and `coverage.json`. The original qualification includes 319/319 executed instructions, both outcomes of all 39 conditional branches, 535 compiled fault/fuzz cases, 14 closed-world controls, and two full stock reads with exact byte/hash equality. Host-native composite/random fixtures are linked separately by the project validator.

The kernel consumes zero software stack bytes. One explicitly injected virtual NMI consumes the documented eight-byte hardware frame and reaches the actual private vector/handler, whose first instruction resets SP. No result proves the prefix before private SP/VBR, arbitrarily rapid repeated NMIs, physical clocks, prior DMA corruption, external watchdog behavior or actual power/reset restoration. These remain physical/entry requirements. No physical provider is loaded by this package.
