"""Deterministic sequential virtual observations from the actual frozen payload."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from sh2e import Memory, FunctionHarness, RAM_START
from differential import (artifacts, DECODER, CODE_BASE, CODE_END, CALL_ENTRY, CALL_CONTINUE,
                          DIAG_BASE, DIAG_END, SOURCE, PACKED, LATCH, FLAGS, TARGET, CURRENT,
                          reference_state, validate_publication)

ROOT = Path(__file__).resolve().parent


def scenario_series():
    stock, patched, _ = artifacts()
    observations = [
        (0x88, 0x88, 0, 0), (0x77, 0x77, 1, 2), (0x00, 0x00, 1, 2),
        (0x11, 0x11, 1, 2), (0x21, 0x21, 1, 2), (0x22, 0x22, 1, 2),
        (0x32, 0x32, 1, 2), (0x33, 0x33, 1, 2), (0x23, 0x23, 1, 2),
        (0x22, 0x22, 1, 2), (0x11, 0x22, 1, 2), (0x11, 0x11, 0, 0),
        (0x9F, 0x9F, 1, 2), (0x11, 0x11, 1, 2), (0x11, 0x11, 1, 2),
    ]
    previous_diag, previous_oem = b"\xA5" * 32, bytes([0xA7, 0xB8])
    snapshots = []
    addresses = [SOURCE, PACKED, LATCH, FLAGS, TARGET, CURRENT] + list(range(DIAG_BASE, DIAG_END))
    for sample, (source, packed, latch, flags) in enumerate(observations):
        runs = []
        for rom, is_patched in ((stock, False), (patched, True)):
            memory = Memory(rom)
            for address, value in ((SOURCE, source), (PACKED, packed), (LATCH, latch), (FLAGS, flags)):
                memory.initialize(address, bytes([value]))
                memory.watch(address, address + 1, "virtual scenario input")
            memory.initialize(TARGET, previous_oem)
            memory.initialize(DIAG_BASE, previous_diag)
            memory.watch(TARGET, CURRENT + 1, "OEM decoded bytes")
            memory.watch(DIAG_BASE, DIAG_END, "observer bytes")
            ranges = [DECODER, (CALL_ENTRY, CALL_CONTINUE)] + ([(CODE_BASE, CODE_END)] if is_patched else [])
            harness = FunctionHarness(memory, ranges)
            result = harness.run(CALL_ENTRY, stop_at=CALL_CONTINUE,
                                 allowed_writes=[(TARGET, CURRENT + 1)] + ([(DIAG_BASE, DIAG_END)] if is_patched else []))
            runs.append((harness, result))
        baseline, observed = runs[0][0], runs[1][0]
        if baseline.cpu.r != observed.cpu.r or runs[0][1]["system_registers"] != runs[1][1]["system_registers"]:
            raise AssertionError("Sequential stock/patched register divergence")
        oem_slice = slice(TARGET - RAM_START, CURRENT + 1 - RAM_START)
        if baseline.memory.ram[oem_slice] != observed.memory.ram[oem_slice]:
            raise AssertionError("Sequential stock/patched OEM state divergence")
        actual_diag = bytes(observed.memory.ram[DIAG_BASE - RAM_START:DIAG_END - RAM_START])
        if actual_diag != reference_state(previous_diag, source, packed, latch, flags):
            raise AssertionError("Sequential observer state diverges from reference")
        validate_publication(observed.memory.events)
        previous_diag = actual_diag
        previous_oem = bytes(observed.memory.ram[oem_slice])
        snapshots.append(dict(sample_id=sample, virtual_time_ms=sample * 10,
            scheduling_note="10 ms is an explicit virtual scenario spacing, not measured hook cadence",
            input=dict(source=source, snapshot=packed, latch=latch, flags=flags),
            bytes={f"{address:08X}": observed.memory.ram[address - RAM_START] for address in addresses},
            provenance="Actual compiled final05 caller/wrapper execution, explicit virtual inputs, carried prior observer and OEM state",
            stock_comparison="PASS", result=runs[1][1], diagnostic_state_hex=actual_diag.hex(),
            propagation=[e for e in observed.memory.events if e["watchpoints"]]))
    return dict(schema=1, classification="VIRTUAL_SOFTWARE_SCENARIO_NOT_VEHICLE_TELEMETRY",
                target="A2WC511R", ecuid="2F12515306", stock_rom=stock.identity(),
                overlay_rom=patched.identity(), payload_sha256=sha256(patched.data[CODE_BASE:CODE_END]).hexdigest(),
                unknown_read_policy="Reject any requested RAM address absent from snapshot bytes",
                time_policy="Explicit virtual spacing only; no actual task cadence claimed", snapshots=snapshots)


if __name__ == "__main__":
    run = ROOT / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "_gate_scenarios")
    run.mkdir(parents=True, exist_ok=False)
    report = scenario_series()
    path = run / "virtual_ram_snapshots.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(path=str(path), sha256=sha256(path.read_bytes()).hexdigest(), samples=len(report["snapshots"]))))
