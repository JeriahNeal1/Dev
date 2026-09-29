import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from differential import (artifacts, execute, compare, HOOK_ENTRY, DIAG_BASE, DIAG_END,
                          initial_state, validate_publication, SOURCE, PACKED, LATCH, FLAGS)
from sh2e import SimulationStop, Memory, FunctionHarness, RAM_START


class ExperimentalDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock, cls.patched, _ = artifacts()

    def test_all_packed_bytes_cold_warm_direct_and_real_callsite(self):
        for caller in (False, True):
            for warm in (False, True):
                for packed in range(256):
                    with self.subTest(caller=caller, warm=warm, packed=packed):
                        compare(execute(self.stock, packed, warm, caller),
                                execute(self.patched, packed, warm, caller, patched=True))

    def test_identical_patched_replay(self):
        first = execute(self.patched, 0x9F, True, True, patched=True)
        second = execute(self.patched, 0x9F, True, True, patched=True)
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[0].cpu.trace, second[0].cpu.trace)
        self.assertEqual(first[0].memory.events, second[0].memory.events)

    def test_mutated_register_restore_is_detected(self):
        # Replace restore R0 with restore R1: same stack movement, wrong caller state.
        mutant = self.patched.with_overlay(HOOK_ENTRY + 0x58, bytes.fromhex("61f6"), "negative regression: wrong R0 restore")
        with self.assertRaisesRegex(AssertionError, "General register divergence"):
            compare(execute(self.stock, 0x21, caller=True),
                    execute(mutant, 0x21, caller=True, patched=True))

    def test_mutated_unsupported_instruction_is_detected(self):
        mutant = self.patched.with_overlay(HOOK_ENTRY, bytes.fromhex("ffff"), "negative regression: unsupported opcode")
        with self.assertRaisesRegex(SimulationStop, "Unsupported"):
            execute(mutant, 0x21, caller=True, patched=True)

    def test_explicit_init_publication_invalid_and_valid_prior_states(self):
        for warm in (False, True):
            for sequence in (0, 1, 12, 0xFFFFFFFE, 0xFFFFFFFF):
                state = bytearray(initial_state(warm, 0x21))
                state[:4] = sequence.to_bytes(4, "big")
                memory = Memory(self.patched)
                memory.initialize(DIAG_BASE, state)
                harness = FunctionHarness(memory, [(0xE10BC, 0xE110E)])
                harness.run(0xE10BC, registers={4: DIAG_BASE}, allowed_writes=[(DIAG_BASE, DIAG_END)])
                commits = validate_publication(memory.events)
                expected_sequence = (((sequence & ~1) if warm else 0) + 2) & 0xFFFFFFFF
                self.assertEqual(commits, [expected_sequence])
                expected = b"".join(v.to_bytes(4, "big") for v in
                                    (expected_sequence, 0x4D304431, 0, 0x208, 0)) + b"\x00" * 10 + b"\x01\x00"
                self.assertEqual(bytes(memory.ram[DIAG_BASE - RAM_START:DIAG_END - RAM_START]), expected)

    def test_even_sequence_during_field_write_is_rejected(self):
        _, result, _ = execute(self.patched, 0x21, caller=True, patched=True)
        del result
        bad_events = [dict(mode="w", address=f"{DIAG_BASE:08X}", size=4, value="00000002"),
                      dict(mode="w", address=f"{DIAG_BASE + 4:08X}", size=4, value="4D304431")]
        with self.assertRaisesRegex(AssertionError, "outside odd"):
            validate_publication(bad_events)

    def test_scripted_input_change_sets_changed_reason_without_freshness_claim(self):
        # Explicitly modeled RAM changes between sampler reads; these are not real fault telemetry.
        for change_address in (SOURCE, PACKED, LATCH, FLAGS):
            class ScriptedMemory(Memory):
                def __init__(self, rom):
                    super().__init__(rom)
                    self.read_counts = {}
                    self.scripted_changes = []

                def read(self, address, size, address_sources=(), fetch=False):
                    if not fetch and size == 1 and address == change_address:
                        count = self.read_counts.get(address, 0) + 1
                        self.read_counts[address] = count
                        trigger = 3 if address == PACKED else 2  # OEM decoder reads packed once first.
                        if count == trigger:
                            offset = address - RAM_START
                            before = self.ram[offset]
                            self.ram[offset] ^= 1
                            self.scripted_changes.append(dict(address=f"{address:08X}", before=before,
                                                              after=self.ram[offset], sampler_read=2))
                    return super().read(address, size, address_sources, fetch)

            harness, _, expected = execute(self.patched, 0x11, caller=True, patched=True, memory_class=ScriptedMemory)
            state = harness.memory.ram[DIAG_BASE - RAM_START:DIAG_END - RAM_START]
            reasons = int.from_bytes(state[12:16], "big")
            self.assertEqual(len(harness.memory.scripted_changes), 1)
            self.assertEqual(state[31], 1)
            self.assertEqual(state[28], 0)
            self.assertEqual(reasons & (0x100 | 0x208), 0x308)
            expected = bytearray(expected)
            expected[12:16] = (int.from_bytes(expected[12:16], "big") | 0x100).to_bytes(4, "big")
            expected[31] = 1
            self.assertEqual(bytes(state), bytes(expected))
            validate_publication(harness.memory.events)


if __name__ == "__main__":
    unittest.main(verbosity=2)
