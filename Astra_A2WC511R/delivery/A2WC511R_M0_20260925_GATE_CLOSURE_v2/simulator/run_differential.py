"""Preserve hash-linked reports for experimental compiled stock-vs-patched execution."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
import test_differential
import differential
from differential import artifacts, execute, compare, BUILD
from run_validation import dump


def main():
    run = ROOT / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "_differential")
    run.mkdir(parents=True, exist_ok=False)
    records, covered, writes = [], set(), set()
    real_compare = compare

    def measured_compare(stock_run, patched_run):
        record = real_compare(stock_run, patched_run)
        h = patched_run[0]
        covered.update(int(row["pc"], 16) for row in h.cpu.trace)
        writes.update(int(e["address"], 16) for e in h.memory.events if e["mode"] == "w")
        record["caller"] = h.cpu.trace[0]["pc"] == "0001193A"
        record["packed"] = h.memory.ram[differential.PACKED - differential.RAM_START]
        records.append(record)
        return record

    test_differential.compare = measured_compare
    with (run / "test_log.txt").open("w", encoding="utf-8") as log:
        log.write("Command: py -3.14 run_differential.py\n")
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromModule(test_differential))
    test_differential.compare = real_compare
    stock, patched, manifest = artifacts()
    samples = []
    for packed, warm in ((0x21, False), (0x9F, True)):
        h, res, expected = execute(patched, packed, warm, True, patched=True)
        samples.append(dict(fixture=dict(packed=packed, warm=warm), result=res,
                            expected_state=expected.hex(), instructions=h.cpu.trace, memory=h.memory.events))
    dump(run / "differential_cases.json", records)
    dump(run / "sample_traces.json", samples)
    dump(run / "address_propagation.json", [dict(fixture=s["fixture"], rom_sha256=patched.sha256,
         events=[e for e in s["memory"] if "experimental observer RAM" in e["watchpoints"]]) for s in samples])
    report = {
        "schema": 1, "status": "PASS" if result.wasSuccessful() else "FAIL",
        "classification": "EXPERIMENTAL_UNAPPROVED VIRTUAL MEMORY MAPPING; NOT REAL ECU ALLOCATION ACCEPTANCE",
        "command": "py -3.14 run_differential.py", "run_directory": str(run),
        "tests": dict(run=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped)),
        "stock_rom": stock.identity(), "virtual_overlay_rom": patched.identity(),
        "build_manifest": str(BUILD / "manifest.json"),
        "build_manifest_sha256": sha256((BUILD / "manifest.json").read_bytes()).hexdigest(),
        "code_sha256": manifest["artifacts"]["m0.EXPERIMENTAL_UNAPPROVED.code.bin"],
        "code_span": ["000E1000", "000E1364"], "diagnostic_ram_span": ["FFFF7400", "FFFF7420"],
        "hook_pointer": dict(address="00011ADC", before="000147AC", after="000E12DC"),
        "cases": len(records), "scenario_seed": "No random generator; 256 packed bytes x cold/warm x direct/callsite boundaries",
        "cold_fixture": "diagnostic RAM filled A5; init path required; OEM prior target/current 00/07",
        "warm_fixture": "initialized diagnostic state; publication/sample/transition counter wrap boundaries and held AA/BB OEM prior values",
        "boundary": ["direct original147AC vs hookE12DC through return sentinel", "actual caller1193A..1193F through continuation11940"],
        "verified_equal": ["all16 general registers including SP", "SR, MACH, MACL and PR",
                           "continuation/return PC", "all RAM outside diagnostic32 and declared transient stack",
                           "original decoder executed opcode/PC sequence and T behavior", "original decoder data reads/writes"],
        "extra_writes_allowlist": ["FFFF7400..FFFF741F diagnostic state", "virtual guarded stack FFFFBBA0..FFFFBF9F"],
        "observed_max_extra_stack_bytes": max((r["max_extra_stack_bytes"] for r in records), default=None),
        "extra_instruction_range": [min((r["extra_instructions"] for r in records), default=None),
                                    max((r["extra_instructions"] for r in records), default=None)],
        "covered_instruction_pcs": [f"{pc:08X}" for pc in sorted(covered)],
        "written_addresses": [f"{address:08X}" for address in sorted(writes)],
        "negative_regressions": ["incorrect R0 restore detected as general-register divergence", "unsupported opcode stops visibly"],
        "publication": "Every non-sequence diagnostic write occurred under odd sequence; each sample finished even. Explicit init checked10 invalid/valid and wrap scenarios. Field write under even sequence negative test fails.",
        "scripted_input_changes": "Four explicitly virtual second-read mutations (source/snapshot/latch/status) all set capture_changed=1 and retain UNKNOWN freshness/coherence-unproven reasons; no real telemetry.",
        "limitations": ["No cycle count, real-time schedule or interrupt acceptance; extra instructions are an overhead measurement only",
                        "Virtual allocation does not prove ROM/RAM unused or sufficient physical stack headroom",
                        "Differential matrix uses stable virtual bytes per call; four separate scripted mutations test capture-change handling only",
                        "All sampler results keep freshness UNKNOWN and coherence-unproven reason",
                        "Observer reconstructed decoded fields use its own prior samples, not direct capture of OEM decoded bytes",
                        "No full firmware boot, physical peripherals, SSM/J2534 or vehicle operation",
                        "Separate static task/dispatcher frames add8bytes outside measured124; RTOS/interrupt stack context remains unbounded"],
        "source_hashes": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                          for p in (ROOT / "sh2e.py", ROOT / "differential.py", ROOT / "run_differential.py", ROOT / "tests/test_differential.py")},
    }
    dump(run / "coverage.json", report)
    print(json.dumps({"status": report["status"], "report": str(run / "coverage.json"), "cases": len(records),
                      "extra_instruction_range": report["extra_instruction_range"],
                      "max_extra_stack": report["observed_max_extra_stack_bytes"]}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
