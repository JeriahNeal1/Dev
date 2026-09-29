"""Run real-byte anchors and architecture tests, preserving an immutable run report."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
import test_sim
from sh2e import ROM, CPU, OPCODES, STOCK_SHA256


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    run = ROOT / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run.mkdir(parents=True, exist_ok=False)
    seen = set()
    real_step = CPU.step

    def observed_step(cpu):
        result = real_step(cpu)
        seen.update(cpu.opcodes_seen)
        return result

    CPU.step = observed_step
    with (run / "test_log.txt").open("w", encoding="utf-8") as log:
        log.write("Command: py -3.14 run_validation.py\n")
        log.write(f"Python: {sys.version}\nStock SHA256: {STOCK_SHA256}\n")
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromModule(test_sim))
    CPU.step = real_step
    stock = ROM.load(test_sim.ROM_PATH, STOCK_SHA256)
    names = {s.name for s in OPCODES}
    dump(run / "supported_opcodes.json", [dict(name=s.name, mask=f"{s.mask:04X}",
         value=f"{s.value:04X}", branch=s.branch, exercised_by_tests=s.name in seen) for s in OPCODES])
    sample_traces = []
    for packed, label in ((0x88, "modeled Park"), (0x77, "modeled Reverse"), (0x00, "modeled Neutral"),
                          (0x11, "modeled stable first"), (0x21, "modeled upshift"),
                          (0x12, "modeled downshift"), (0x9F, "out-of-range hold previous")):
        output, h, res = test_sim.decode_fixture(stock, packed, (0xAA, 0xBB))
        sample_traces.append(dict(label=label, fixture={"packed": packed, "prior": [0xAA, 0xBB]},
                                 output=output, result=res, instructions=h.cpu.trace, memory=h.memory.events))
    dump(run / "sample_traces.json", sample_traces)
    dump(run / "address_propagation.json", {
        "semantics": "Value-source union plus effective-address origins and conservative executed-path condition origins; not static alias analysis or physical freshness evidence.",
        "sample": "0x21 with prior AA/BB; actual stock decoder instructions",
        "rom_sha256": stock.sha256,
        "events": [event for event in sample_traces[4]["memory"] if event["watchpoints"]],
    })
    unsupported = {
        "opcodes": "Every opcode not matching supported_opcodes.json stops before execution.",
        "context_restrictions": ["PC-relative loads in taken-branch delay slots explicitly unsupported",
                                 "Branch instructions in delay slots rejected", "RAM execution unsupported"],
        "peripherals": "All addresses outside ROM 00000000..000FFFFF and RAM FFFF0000..FFFFBFFF fail; no MMIO is stubbed.",
        "not_modeled": ["interrupts/exceptions and vector dispatch", "FPU execution", "DMA",
                        "watchdog", "CPU pipeline/cycle time", "SR effects other than storage and T bit",
                        "engine dynamics", "transmission hydraulics", "ADC/analog/electrical behavior",
                        "SSM/J2534 transport", "RomRaider backend", "full firmware boot"],
    }
    dump(run / "unsupported.json", unsupported)
    report = {
        "schema": 1, "status": "PASS" if result.wasSuccessful() else "FAIL",
        "classification": "OFFLINE FUNCTION VALIDATION ONLY; NOT A FLASH CANDIDATE OR PHYSICAL SAFETY ACCEPTANCE",
        "run_directory": str(run), "command": "py -3.14 run_validation.py",
        "rom": stock.identity(), "host_python": sys.version, "platform": platform.platform(),
        "tests": dict(run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                      skipped=len(result.skipped), supported_forms=len(names),
                      supported_forms_exercised=len(seen), unexercised_forms=sorted(names - seen)),
        "stock_decoder": dict(entry="000147AC", end_exclusive="00014802", instruction_pcs=43,
                              instruction_pc_coverage="43/43", conditional_branch_outcomes="8/8",
                              cases=256 * len(test_sim.PRIOR_PAIRS), packed_values="all 0..255",
                              prior_pairs=test_sim.PRIOR_PAIRS, writes_only=["FFFF4BC1", "FFFF4BC2"],
                              code_sha256=sha256(stock.data[0x147AC:0x14802]).hexdigest()),
        "stock_status": dict(entry="00015A02", end_exclusive="00015A16", cases=256,
                             instruction_pc_coverage="10/10", result="R0 = bool(FFFF4C50 & 0x02)",
                             writes=0, code_sha256=sha256(stock.data[0x15A02:0x15A16]).hexdigest()),
        "determinism": "same stock fixture produces identical registers, memory bytes, instruction trace and data-access trace",
        "scenario_seed": "No random generator; exhaustive packed/status values and explicit prior-pair enumeration",
        "memory": dict(rom_readonly=True, ram_uninitialized_reads_fail=True, big_endian=True,
                       reset_vector_decode=dict(pc="00000AAC", sp="FFFFBFA0"),
                       stack_policy="Harness virtual stack FFFFBBA0..FFFFBF9F; 16-byte guards either side; not proof of real allocation"),
        "coverage_limitations": ["P/R/N/forward naming comes from historical interpretation, not mechanical simulation",
                                 "8 maps to zero and 9..F holds are verified for the decoder only",
                                 "No global freshness or CAN-health conclusion follows from the status helper",
                                 "No reset-code execution; vectors decoded only",
                                 "No full ROM or calibration acceptance", "No patched candidate tested in this anchor report"],
        "source_hashes": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                          for p in (ROOT / "sh2e.py", ROOT / "tests/test_sim.py", ROOT / "run_validation.py")},
        "architectural_reference": "https://www.renesas.com/en/document/mah/sh-2e-software-manual",
        "local_static_reference": r"C:\Dev\Astra_A2WC511R\reports\local\ida\initial_static_audit.json",
    }
    dump(run / "coverage.json", report)
    print(json.dumps({"status": report["status"], "report": str(run / "coverage.json"), "tests": report["tests"]}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
