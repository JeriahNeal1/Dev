"""Explicit nested-writer experiment; not a claim that the OEM task can reenter."""
from differential import artifacts, initial_state, DIAG_BASE, DIAG_END, validate_publication
from sh2e import Memory, FunctionHarness, RAM_START


def probe_reentry():
    _, rom, _ = artifacts()
    ranges = [(0xE1114, 0xE1232), (0xE10BC, 0xE110E), (0xE101C, 0xE10B2)]
    outer = Memory(rom)
    outer.initialize(DIAG_BASE, initial_state(True, 0x22))
    outer.initialize(0xFFFF7500, bytes([0x11, 0x11, 1, 2, 0, 0, 0, 0]))
    harness = FunctionHarness(outer, ranges)
    cpu = harness.cpu
    for register in range(15):
        cpu._reg(register, 0, {f"fixture:register:r{register}"})
    for register, value in ((4, DIAG_BASE), (5, 0xFFFF7500), (15, harness.stack[1])):
        cpu._reg(register, value, {f"fixture:register:r{register}"})
    cpu.pc, cpu.pr, cpu.call_context = 0xE1114, FunctionHarness.RETURN_SENTINEL, ["000E1114_OUTER"]
    outer.write_allowlist = [(DIAG_BASE, DIAG_END), harness.stack]
    while not any(e["mode"] == "w" and e["address"] == "FFFF7400" for e in outer.events):
        cpu.step()
    split = len(outer.events)
    paused_state = bytes(outer.ram[DIAG_BASE - RAM_START:DIAG_END - RAM_START])
    inner = Memory(rom)
    inner.initialize(DIAG_BASE, paused_state)
    inner.initialize(0xFFFF7500, bytes([0x22, 0x22, 1, 2, 0, 0, 0, 0]))
    inner_harness = FunctionHarness(inner, ranges)
    inner_harness.run(0xE1114, registers={4: DIAG_BASE, 5: 0xFFFF7500}, allowed_writes=[(DIAG_BASE, DIAG_END)])
    inner_state = bytes(inner.ram[DIAG_BASE - RAM_START:DIAG_END - RAM_START])
    # Explicit shared-state transfer at a virtual nested-call boundary; no other RAM is copied.
    outer.ram[DIAG_BASE - RAM_START:DIAG_END - RAM_START] = inner_state
    while not cpu.returned:
        cpu.step()
    interleaved_events = outer.events[:split] + inner.events + outer.events[split:]
    detected = False
    try:
        validate_publication(interleaved_events)
    except AssertionError as error:
        detected = "outside odd" in str(error)
    if not detected:
        raise AssertionError("Nested-writer negative fixture did not expose required one-writer precondition")
    return dict(classification="EXPLICIT_VIRTUAL_NESTED_WRITER_NEGATIVE_TEST", publication_violation_detected=True,
                paused_outer_sequence=int.from_bytes(paused_state[:4], "big"),
                nested_writer_sequence=int.from_bytes(inner_state[:4], "big"),
                final_outer_sequence=int.from_bytes(outer.ram[0x7400:0x7404], "big"),
                state_store_events=[e for e in interleaved_events if e["mode"] == "w" and 0xFFFF7400 <= int(e["address"], 16) < 0xFFFF7420],
                implication="M0 observer requires one nonreentrant writer. This experiment does not establish that OEM task9 permits reentry.")
