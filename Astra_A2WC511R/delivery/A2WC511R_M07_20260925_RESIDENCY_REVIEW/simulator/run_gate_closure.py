"""Run current simulator regressions and save bounded runtime/allocation evidence."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
import test_differential
import test_gate_closure
from sh2e import CPU, OPCODES
from differential import CODE_BASE, CODE_END, HOOK_ENTRY
from runtime_audit import StaticAudit
from dma_setup_probe import run_setup
from gate_scenarios import scenario_series
from reentry_probe import probe_reentry

HOLES = {"contiguous_CE754_FFAF8": (0xCE754, 0xFFAF8), "alternative_859BC_C0000": (0x859BC, 0xC0000)}


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def account_holes(harness):
    result = {}
    for name, (start, end) in HOLES.items():
        fetched = Counter(int(row["pc"], 16) for row in harness.cpu.trace if start <= int(row["pc"], 16) < end)
        read, written = Counter(), Counter()
        for event in harness.memory.events:
            address = int(event["address"], 16)
            if address < end and address + event["size"] > start:
                (read if event["mode"] == "r" else written)[address] += 1
        all_addresses = set(fetched) | set(read) | set(written)
        undeclared = sorted(a for a in all_addresses if not CODE_BASE <= a < CODE_END)
        if undeclared:
            raise AssertionError(f"Unexpected candidate-hole access in tested closure: {undeclared}")
        result[name] = dict(fetches=sum(fetched.values()), reads=sum(read.values()), writes=sum(written.values()),
                            executed_pcs=sorted(fetched), read_addresses=sorted(read), write_addresses=sorted(written))
    return result


def main():
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "_gate_closure_runtime"
    out = ROOT / "runs" / name
    out.mkdir(parents=True, exist_ok=False)
    seen, paired, ram_test = set(), [], []
    real_step, real_compare, real_ram = CPU.step, test_differential.compare, test_gate_closure.run_ram_pattern

    def observed_step(cpu):
        value = real_step(cpu)
        seen.update(cpu.opcodes_seen)
        return value

    def measured_compare(stock, patched):
        record = real_compare(stock, patched)
        record["entry"] = patched[1]["entry"]
        record["stock_hole_accounting"] = account_holes(stock[0])
        record["patched_hole_accounting"] = account_holes(patched[0])
        paired.append(record)
        return record

    def measured_ram(start, end, memory_class=test_gate_closure.Memory):
        h, result = real_ram(start, end, memory_class)
        if start == 0xFFFF2D00 and end == 0xFFFFBFFB:
            ram_test.append(dict(start=f"{start:08X}", end_parameter=f"{end:08X}", final_r4=f"{h.cpu.r[4]:08X}",
                result=result, write_count=sum(e["mode"] == "w" for e in h.memory.events),
                read_count=sum(e["mode"] == "r" for e in h.memory.events),
                candidate_hex=h.memory.ram[0x7400:0x7420].hex(),
                lower_boundary_sentinel_hex=h.memory.ram[0x2CFC:0x2D00].hex(),
                upper_boundary_sentinel_hex=h.memory.ram[0xBFFC:0xC000].hex(),
                watchpoint_hits=[e for e in h.memory.events if e["watchpoints"]],
                control_provenance_note="Cumulative branch-origin decoration disabled explicitly for bulk loop; all value/address origins, data accesses and instruction PCs retained"))
        return h, result

    CPU.step, test_differential.compare, test_gate_closure.run_ram_pattern = observed_step, measured_compare, measured_ram
    with (out / "tests.log").open("w", encoding="utf-8") as log:
        log.write("Command: py -3.14 run_gate_closure.py\n")
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(
            unittest.defaultTestLoader.discover(str(ROOT / "tests")))
    CPU.step, test_differential.compare, test_gate_closure.run_ram_pattern = real_step, real_compare, real_ram
    static = StaticAudit().report()
    dump(out / "cfg_frames_registers_timing.json", static)
    dump(out / "ram_pattern_FA58.json", ram_test)
    dump(out / "dma_setup_C31E.json", [run_setup(i, j) for i, j in ((0, 0), (255, 0), (0, 255), (255, 255))])
    dump(out / "nested_writer_negative.json", probe_reentry())
    dump(out / "sequential_virtual_ram_snapshots.json", scenario_series())
    dump(out / "paired_cases_hole_watchpoints.json", paired)
    dump(out / "supported_opcodes.json", [dict(name=s.name, mask=f"{s.mask:04X}", value=f"{s.value:04X}",
                                               exercised=s.name in seen) for s in OPCODES])
    holes = {}
    for hole, span in HOLES.items():
        holes[hole] = dict(span=[f"{a:08X}" for a in span])
        for variant in ("stock", "patched"):
            records = [r[f"{variant}_hole_accounting"][hole] for r in paired]
            holes[hole][variant] = {kind: sum(r[kind] for r in records) for kind in ("fetches", "reads", "writes")}
            for key in ("executed_pcs", "read_addresses", "write_addresses"):
                holes[hole][variant][key] = [f"{a:08X}" for a in sorted({a for r in records for a in r[key]})]
    dump(out / "whole_hole_dynamic_summary.json", dict(paired_cases=len(paired), holes=holes,
        scope="Only supplied actual-ROM decoder/status/compiled-wrapper scenarios; zero accesses do not prove whole-firmware ownership.",
        writes_policy="ROM is immutable; any attempted ROM write hard-fails. Instruction fetches are classified from executed PC traces separately from data reads."))
    status = "PASS" if result.wasSuccessful() else "FAIL"
    gate_report = dict(schema=1, classification="OFFLINE_GATE_EVIDENCE_NOT_PHYSICAL_ACCEPTANCE", status=status,
        run_directory=str(out), final_build=static["build"], payload_sha256=static["payload_sha256"],
        test_summary=dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
                          supported_opcode_forms=len(OPCODES), exercised_forms=len(seen), unexercised_forms=sorted({s.name for s in OPCODES} - seen)),
        paired_cases=len(paired), exact_added_stack_bytes=124, known_surrounding_oem_frames=8,
        all_path_instruction_upper_bound=static["instruction_bound"], added_instruction_upper_bound=static["instruction_bound"] - static["functions"]["000147AC"]["instruction_upper_bound"],
        observed_extra_instruction_range=[min(r["extra_instructions"] for r in paired), max(r["extra_instructions"] for r in paired)],
        gates={"injected_cfg_and_balanced_stack": status, "register_preservation_under_disjoint_private_stack": status,
               "watchpoints_propagation_replay_differential": status, "reset_RAM_pattern_and_finite_DMA_setup_regressions": status,
               "unconditional_observer_reentrancy": "FAIL", "OEM_task_reentry_exclusion": "PHYSICAL/BENCH REQUIRED",
               "absolute_hook_cadence_and_silicon_margin": "PHYSICAL/BENCH REQUIRED", "total_context_stack_headroom": "PHYSICAL/BENCH REQUIRED"},
        reentry_explanation="A deliberate nested writer closes sequence14 inside outer sequence13; outer resumes writing fields under even14. Actual OEM reentry possibility is separately gated; one nonreentrant writer remains mandatory.",
        cadence="RAM/RTOS agent identified CMT1 Pphi/8, CMCOR2499 ->20000Pphi cycles/tick; task9 every8D936 ticks ->160000Pphi cycles/normal enqueue. Actual clock, missed events, queueing, and higher-priority response-time bound require separate proof.",
        documentation=[dict(url="https://www.renesas.com/en/document/mah/sh-2e-software-manual", revision="REJ09B0316-0200 Rev2.00", sections="7 instruction semantics;8.1..8.8/Table8.1 stage and contention descriptions"),
                       dict(url="https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual", revision="Rev3.00 Sep2004", sections="1.1 CPU maximum;14 CMT;24.1 RAM read/write access states")],
        tracing_limit="Full default control origins retained for wrapper scenarios. FA58 bulk test explicitly disables cumulative control-source decoration to avoid quadratic trace growth; this is a trace option and does not change instruction/memory behavior.",
        source_hashes={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in
                       [ROOT / "sh2e.py", ROOT / "runtime_audit.py", ROOT / "dma_setup_probe.py", ROOT / "gate_scenarios.py", ROOT / "reentry_probe.py", ROOT / "run_gate_closure.py", ROOT / "tests/test_gate_closure.py"]},
        reproduce=["py -3.14 run_gate_closure.py", "py -3.14 gate_scenarios.py"],
        limitations=["Frozen payload unchanged; simulator source backed up before focused opcode additions",
                     "No DMA engine, status completion, real logger provider, physical CAN/device or active control commands",
                     "Static timing examples are conditional serialized envelopes; entry stalls and external interference are not bounded",
                     "Root whole-ROM/RTOS ownership gates remain separate from the observed zero-hole-access scenarios"])
    dump(out / "runtime_gate_report.json", gate_report)
    frames = "\n".join(f"| {f['name']} | {f['local_frame_peak']} | {f['transitive_frame_peak']} | {f['instruction_upper_bound']} |" for f in static["functions"].values())
    md = f"""# M0 runtime gate evidence

Frozen final05 payload `{static['payload_sha256']}` is unchanged. {result.testsRun} regression tests returned {status}; {len(paired)} paired stock/wrapper cases were rerun on the extended interpreter. The generated JSON files contain exact code bytes, CFG edges, call literals, frame depths, source hashes and watchpoint records.

| Routine | Local frame bytes | Peak including callees | Conservative instruction bound |
| --- | ---: | ---: | ---: |
{frames}

The full injected graph is hook → OEM decoder, then hook → sampler → observer → initializer (conditional) and reasons. The compiler inlines decoded-nibble logic; standalone m0_decode is unused by the hook. All returns balance SP, all graph joins agree on frame depth, and the only injected back edge is the initializer's fixed 28-iteration loop. The exact added stack maximum is124 bytes; the surrounding known OEM task/dispatcher save another8 bytes. This does not bound full RTOS/ISR occupancy.

The actual wrapper's45 save/restore words establish R0–R14, SR, MACH, MACL, PR and SP preservation at return, assuming writable private stack disjoint from observer state. Every reachable instruction is decoded; none accesses FR0–FR15, FPUL, FPSCR, GBR or VBR. This is architectural preservation, not an interrupt-latency equivalence claim.

The conservative full-hook bound is562 instructions including the original decoder; additional instruction work is bounded by526. The refreshed scenarios observed291–483 additional instructions. A serialized envelope is `C <= 5*N + (F-1)*N + (D-1)*A + entry_stalls + external_interference`, where F/D are explicitly assumed upper memory-service times, N=562 and A=178. Example F=2,D=2 with no external/entry term gives3550 cycles,44.375µs at an assumed80MHz. The hardware maximum frequency is not a measured ECU clock. Silicon timing and scheduling margin remain **PHYSICAL/BENCH REQUIRED**. [Renesas software manual](https://www.renesas.com/en/document/mah/sh-2e-software-manual), [SH7058 hardware manual](https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual).

An explicitly modeled nested writer reproduces invalid publication while an even sequence is visible. Unconditional reentrancy is **FAIL**; one nonreentrant writer is mandatory. Normal task activation is reported separately by the RAM/RTOS investigation as160000Pphi cycles per task9 enqueue. Reentry exclusion, actual clock, missed/coalesced events and response time must be established by that gate.

The actual FA58 routine overwrites the full [FFFF2D00,FFFFBFFC) reset-test span withA55A5AA5, including the proposed state. Watchpoints identify both write PCs and pointer/value origins; outer2CFC/BFFC sentinels remain unchanged. The C31E..C376 setup fragment writes an explicit finite DMA2/3 configuration fixture; activation and status reads fail. No DMA transfer is fabricated. Full-byte index arithmetic keeps that setup's ordinary buffers below7400; this is scoped access evidence, not lifetime ownership.

`whole_hole_dynamic_summary.json` separately counts ROM fetch/read/write access in [CE754,FFAF8) and [859BC,C0000) across every paired case. Stock known-routine cases have zero access; patched access is confined to the injected code/literals. No inference about unexplored firmware paths is made.

Use `py -3.14 run_gate_closure.py` for all regressions, or `py -3.14 gate_scenarios.py` for15 sequential immutable RAM snapshots usable by Codex and the isolated virtual-logger backend. Unknown RAM/peripheral reads fail; snapshots label their timing and input values as virtual. Historical runs and the pre-extension source backup are retained.
"""
    (out / "RUNTIME_HANDOFF.md").write_text(md, encoding="utf-8")
    dest = Path(r"C:\Dev\Astra_A2WC511R\reports\local\gate_closure\runtime") / name
    shutil.copytree(out, dest)
    print(json.dumps(dict(status=status, tests=result.testsRun, paired_cases=len(paired), report=str(dest / "runtime_gate_report.json"), handoff=str(dest / "RUNTIME_HANDOFF.md"))))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
