import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sh2e import (ROM, Memory, CPU, FunctionHarness, SimulationStop, OPCODES,
                 ROM_SIZE, RAM_START, RAM_END, STOCK_SHA256)

ROM_PATH = Path(r"C:\Dev\SubaruRoms\OEM\A2WC511R.bin")
DECODER = (0x147AC, 0x14802)
STATUS = (0x15A02, 0x15A16)
PACKED, TARGET, CURRENT, STATUS_BYTE = 0xFFFF4C8D, 0xFFFF4BC1, 0xFFFF4BC2, 0xFFFF4C50
PRIOR_PAIRS = ((0, 0), (1, 5), (7, 8), (8, 7), (0xF, 0x80), (0x80, 0xF), (0xFF, 0xFF))


def synthetic(words, extra=None):
    data = bytearray(b"\xFF" * ROM_SIZE)
    data[0x100:0x100 + len(words) * 2] = b"".join(w.to_bytes(2, "big") for w in words)
    for address, payload in (extra or {}).items():
        data[address:address + len(payload)] = payload
    return ROM.synthetic(data, "independent architecture fixture")


def run_synthetic(words, registers=None, allowed=(), extra=None, ranges=None, preserve=tuple(range(8, 16)),
                  system_registers=None, preserve_system=("mach", "macl")):
    memory = Memory(synthetic(words, extra))
    harness = FunctionHarness(memory, ranges or [(0x100, 0x100 + len(words) * 2)])
    result = harness.run(0x100, registers=registers, allowed_writes=allowed, preserve=preserve,
                         system_registers=system_registers, preserve_system=preserve_system)
    return harness, result


def decode_fixture(rom, packed, prior):
    memory = Memory(rom)
    memory.initialize(PACKED, bytes([packed]))
    memory.initialize(TARGET, bytes(prior))
    memory.watch(PACKED, PACKED + 1, "packed input")
    memory.watch(TARGET, CURRENT + 1, "decoded target/current")
    harness = FunctionHarness(memory, [DECODER])
    result = harness.run(DECODER[0], allowed_writes=[(TARGET, CURRENT + 1)])
    offset = TARGET - RAM_START
    output = tuple(memory.ram[offset:offset + 2])
    return output, harness, result


def expected_nibble(nibble, previous):
    return nibble if nibble < 8 else 0 if nibble == 8 else previous


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(synthetic([0x0009]))

    def test_big_endian_and_bounds(self):
        m = self.memory
        m.initialize(RAM_START, bytes.fromhex("12345678"))
        self.assertEqual(m.read(RAM_START, 4)[0], 0x12345678)
        self.assertEqual(m.read(RAM_START + 2, 2)[0], 0x5678)
        m.write(RAM_END - 4, 4, 0xAABBCCDD)
        self.assertEqual(m.ram[-4:], bytes.fromhex("aabbccdd"))
        for address, size in [(RAM_END, 1), (RAM_START - 1, 1), (0xFFFFF000, 4),
                              (RAM_END - 1, 2), (RAM_START + 1, 4), (0xFFFFFFFF, 2)]:
            with self.subTest(address=hex(address)), self.assertRaises(SimulationStop):
                m.read(address, size)

    def test_uninitialized_read_is_failure(self):
        with self.assertRaisesRegex(SimulationStop, "Uninitialized"):
            self.memory.read(RAM_START, 1)

    def test_rom_readonly_and_immutable_overlay(self):
        rom = self.memory.rom
        overlay = rom.with_overlay(0x100, bytes.fromhex("000b"), "test only")
        self.assertEqual(rom.data[0x100:0x102], bytes.fromhex("0009"))
        self.assertEqual(overlay.base_sha256, rom.sha256)
        self.assertNotEqual(overlay.sha256, rom.sha256)
        with self.assertRaisesRegex(SimulationStop, "Read-only"):
            self.memory.write(0x100, 2, 0)
        with self.assertRaises(TypeError):
            rom.data[0] = 0

    def test_watchpoint_has_pc_call_address_and_value_sources(self):
        m = self.memory
        m.watch(RAM_START, RAM_START + 1, "input")
        m.initialize(RAM_START, b"\x42")
        m.pc, m.call_context = 0x100, ["00000100"]
        m.read(RAM_START, 1, {"rom:00000180"})
        event = m.events[-1]
        self.assertEqual(event["pc"], "00000100")
        self.assertEqual(event["call_context"], ["00000100"])
        self.assertEqual(event["watchpoints"], ["input"])
        self.assertIn("rom:00000180", event["address_sources"])
        self.assertIn("ram:FFFF0000", event["value_sources"])


class ArchitectureTests(unittest.TestCase):
    def test_predecrement_uses_original_value_when_register_aliases(self):
        h, _ = run_synthetic([0x2116, 0x6216, 0x000B, 0x0009], registers={1: RAM_START + 4},
                              allowed=[(RAM_START, RAM_START + 4)])
        self.assertEqual(h.cpu.r[1:3], [RAM_START + 4, RAM_START + 4])

    def test_postincrement_same_register_does_not_increment_loaded_value(self):
        for load, expected in [(0x6116, 0x12345680), (0x6114, 0xFFFFFF80)]:
            words = [0x2122 if load == 0x6116 else 0x2120, load, 0x000B, 0x0009]
            h, _ = run_synthetic(words, registers={1: RAM_START, 2: 0x12345680},
                                  allowed=[(RAM_START, RAM_START + 4)])
            self.assertEqual(h.cpu.r[1], expected)

    def test_postincrement_byte_sign_and_pointer(self):
        h, _ = run_synthetic([0x2120, 0x6314, 0x000B, 0x0009],
                              registers={1: RAM_START, 2: 0x80}, allowed=[(RAM_START, RAM_START + 1)])
        self.assertEqual((h.cpu.r[1], h.cpu.r[3]), (RAM_START + 1, 0xFFFFFF80))

    def test_displacement_long_scale(self):
        h, _ = run_synthetic([0x1123, 0x5313, 0x000B, 0x0009],
                              registers={1: RAM_START, 2: 0x89ABCDEF},
                              allowed=[(RAM_START + 12, RAM_START + 16)])
        self.assertEqual(h.cpu.r[3], 0x89ABCDEF)

    def test_add_or_unsigned_compare_and_shift(self):
        h, _ = run_synthetic([0xE0FF, 0xE101, 0x301C, 0xE280, 0x221B, 0x3216,
                              0x0329, 0x4209, 0x0429, 0x000B, 0x0009])
        self.assertEqual(h.cpu.r[:5], [0, 1, 0x3FFFFFE0, 1, 1])

    def test_dt_decrements_and_sets_t_for_zero(self):
        h, _ = run_synthetic([0xE000, 0xE103, 0x7001, 0x4110, 0x8FFC,
                              0x0009, 0x000B, 0x0229])
        self.assertEqual(h.cpu.r[:3], [3, 0, 1])

    def test_negc_borrow_boundaries(self):
        for value in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
            for borrow in (0, 1):
                h, _ = run_synthetic([0x610A, 0x0229, 0x000B, 0x0009],
                                      registers={0: value}, system_registers={"sr": borrow})
                self.assertEqual(h.cpu.r[1], (-value - borrow) & 0xFFFFFFFF)
                self.assertEqual(h.cpu.r[2], int(value != 0 or borrow != 0))

    def test_sr_and_mac_stack_transfers(self):
        h, _ = run_synthetic([0x4F03, 0x0008, 0x4F07, 0x4F02, 0x4F12,
                              0x4F06, 0x4F16, 0x000B, 0x0009],
                              system_registers={"sr": 0x3F3, "mach": 0xABCDEF01, "macl": 0x12345678},
                              preserve_system=())
        self.assertEqual(h.cpu.sr, 0x3F3)
        self.assertEqual((h.cpu.mach, h.cpu.macl), (0x12345678, 0xABCDEF01))

    def test_decode_table_unambiguous(self):
        for word in range(65536):
            matches = [s.name for s in OPCODES if word & s.mask == s.value]
            self.assertLessEqual(len(matches), 1, (hex(word), matches))

    def test_signed_immediate_arithmetic_extub_and_movt(self):
        h, _ = run_synthetic([0xE080, 0x7001, 0x610B, 0x620C, 0x8800,
                              0x0329, 0x000B, 0x0009])
        self.assertEqual(h.cpu.r[:4], [0xFFFFFF81, 0x7F, 0x81, 0])

    def test_shar_negative_and_t_bit(self):
        h, _ = run_synthetic([0xE0FD, 0x4021, 0x0129, 0x000B, 0x0009])
        self.assertEqual(h.cpu.r[:2], [0xFFFFFFFE, 1])

    def test_pc_relative_load_sign_and_alignment(self):
        h, _ = run_synthetic([0x9004, 0xD103, 0x000B, 0x0009], extra={
            0x10C: bytes.fromhex("8001"), 0x110: bytes.fromhex("12345678")})
        self.assertEqual(h.cpu.r[:2], [0xFFFF8001, 0x12345678])

    def test_big_endian_load_store_forms_and_sign_extension(self):
        address = RAM_START + 0x100
        words = [0x2120, 0x6310, 0x2421, 0x6541, 0x2722, 0x6672, 0x000B, 0x0009]
        h, _ = run_synthetic(words, registers={1: address, 2: 0xFEDCBA98,
                                              4: address + 2, 7: address + 4},
                              allowed=[(address, address + 8)])
        self.assertEqual((h.cpu.r[3], h.cpu.r[5], h.cpu.r[6]),
                         (0xFFFFFF98, 0xFFFFBA98, 0xFEDCBA98))

    def test_taken_bra_runs_slot_once_and_skips_fallthrough(self):
        h, _ = run_synthetic([0xE000, 0xA001, 0x7001, 0x7008, 0x000B, 0x7002])
        self.assertEqual(h.cpu.r[0], 3)
        self.assertEqual([x["pc"] for x in h.cpu.trace if x["delay_slot"]],
                         ["00000104", "0000010A"])

    def test_conditional_delayed_branch_both_outcomes(self):
        for initial_t, branch in [(0x0008, 0x8F), (0x0018, 0x8D)]:
            h, _ = run_synthetic([0xE000, initial_t, (branch << 8) | 1,
                                  0x7001, 0x7008, 0x000B, 0x7002])
            self.assertEqual(h.cpu.r[0], 3)
            h, _ = run_synthetic([0xE000, initial_t ^ 0x10, (branch << 8) | 1,
                                  0x7001, 0x7008, 0x000B, 0x7002])
            self.assertEqual(h.cpu.r[0], 11)

    def test_nondelayed_branches_skip_next_instruction(self):
        for set_t, op in [(0x0018, 0x8900), (0x0008, 0x8B00)]:
            h, _ = run_synthetic([0xE000, set_t, op, 0x7008, 0x000B, 0x7001])
            self.assertEqual(h.cpu.r[0], 1)

    def test_jump_destination_latched_before_slot_changes_register(self):
        h, _ = run_synthetic([0x412B, 0xE100, 0xE07F, 0x0009, 0x000B, 0xE02A],
                              registers={1: 0x108})
        self.assertEqual(h.cpu.r[0], 42)

    def test_nested_call_pr_stack_and_watch_context(self):
        # Caller saves PR; BSR subroutine writes RAM and returns; caller restores PR.
        words = [0x4F22, 0xB003, 0xE22A, 0x4F26, 0x000B, 0x0009,
                 0x2120, 0x000B, 0x0009]
        h, result = run_synthetic(words, registers={1: RAM_START}, allowed=[(RAM_START, RAM_START + 1)])
        write = next(e for e in h.memory.events if e["address"] == "FFFF0000" and e["mode"] == "w")
        self.assertEqual(write["call_context"], ["00000100", "0000010C"])
        self.assertTrue(result["stack_pointer_restored"])
        self.assertTrue(result["pr_preserved"])

    def test_jsr_returns_and_preserves_pr_via_stack(self):
        words = [0x4F22, 0x410B, 0xE22B, 0x4F26, 0x000B, 0x0009,
                 0x6023, 0x000B, 0x0009]
        h, _ = run_synthetic(words, registers={1: 0x10C})
        self.assertEqual(h.cpu.r[0], 43)

    def test_unknown_opcode_and_slot_constraints_fail(self):
        for words, text in [([0xFFFF], "Unsupported"),
                            ([0xA000, 0x000B, 0x0009], "Illegal branch"),
                            ([0xA000, 0x9000, 0x0009], "PC-relative")]:
            with self.subTest(words=words), self.assertRaisesRegex(SimulationStop, text):
                run_synthetic(words)

    def test_stack_overflow_collision_and_undeclared_write_fail(self):
        cases = [([0x4F22, 0x000B, 0x0009], {15: 0xFFFFBBA0}, "Stack pointer"),
                 ([0x2120, 0x000B, 0x0009], {1: 0xFFFFBFA0}, "collision"),
                 ([0x2120, 0x000B, 0x0009], {1: RAM_START}, "Undeclared RAM")]
        for words, registers, text in cases:
            with self.subTest(text=text), self.assertRaisesRegex(SimulationStop, text):
                run_synthetic(words, registers=registers)

    def test_preservation_and_instruction_budget_failures(self):
        with self.assertRaisesRegex(SimulationStop, "preservation.*R8"):
            run_synthetic([0xE800, 0x000B, 0x0009])
        m = Memory(synthetic([0xAFFE, 0x0009]))
        h = FunctionHarness(m, [(0x100, 0x104)])
        with self.assertRaisesRegex(SimulationStop, "budget"):
            h.run(0x100, max_steps=12)


class StockRoutineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.load(ROM_PATH, STOCK_SHA256)

    def test_reset_vector_decode(self):
        m = Memory(self.rom)
        self.assertEqual(m.read(0, 4)[0], 0xAAC)
        self.assertEqual(m.read(4, 4)[0], 0xFFFFBFA0)

    def test_identity_mismatch_is_failure(self):
        with self.assertRaisesRegex(SimulationStop, "identity mismatch"):
            ROM.load(ROM_PATH, "0" * 64)

    def test_all_packed_bytes_cross_prior_values(self):
        pcs, branch_edges = set(), set()
        for packed in range(256):
            for prior in PRIOR_PAIRS:
                output, harness, _ = decode_fixture(self.rom, packed, prior)
                expected = (expected_nibble(packed >> 4, prior[0]),
                            expected_nibble(packed & 15, prior[1]))
                self.assertEqual(output, expected, (packed, prior))
                pcs.update(int(row["pc"], 16) for row in harness.cpu.trace)
                branch_edges.update(harness.cpu.branch_edges)
                writes = [e for e in harness.memory.events if e["mode"] == "w"]
                self.assertTrue(all(e["address"] in ("FFFF4BC1", "FFFF4BC2") for e in writes))
                self.assertEqual(len(writes), int((packed >> 4) <= 8) + int((packed & 15) <= 8))
        self.assertEqual(pcs, set(range(*DECODER, 2)))
        for branch_pc in (0x147BA, 0x147C8, 0x147E8, 0x147F6):
            self.assertEqual({taken for pc, _, taken in branch_edges if pc == branch_pc}, {True, False})

    def test_all_status_bytes_exact_r0_and_no_writes(self):
        for status in range(256):
            memory = Memory(self.rom)
            memory.initialize(STATUS_BYTE, bytes([status]))
            harness = FunctionHarness(memory, [STATUS])
            harness.run(STATUS[0], preserve=tuple(range(1, 16)))
            self.assertEqual(harness.cpu.r[0], int(bool(status & 2)))
            self.assertFalse(any(e["mode"] == "w" for e in memory.events))
            self.assertEqual({int(t["pc"], 16) for t in harness.cpu.trace}, set(range(*STATUS, 2)))

    def test_replay_byte_trace_and_propagation_reproducibility(self):
        first = decode_fixture(self.rom, 0x21, (0xAA, 0xBB))
        second = decode_fixture(self.rom, 0x21, (0xAA, 0xBB))
        self.assertEqual(first[2], second[2])
        self.assertEqual(first[1].cpu.trace, second[1].cpu.trace)
        self.assertEqual(first[1].memory.events, second[1].memory.events)
        for event in first[1].memory.events:
            if event["mode"] == "w":
                self.assertIn("ram:FFFF4C8D", event["value_sources"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
