from pathlib import Path
import sys
import unittest
import random

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sh2e import ROM, Memory, FunctionHarness, RAM_START, STOCK_SHA256, SimulationStop, hx
from differential import ROM_PATH, artifacts
from runtime_audit import StaticAudit, ENTRIES
from gate_scenarios import scenario_series
from test_sim import run_synthetic
from dma_setup_probe import run_setup, DMAConfigurationMemory
from reentry_probe import probe_reentry


def run_ram_pattern(start, end, memory_class=Memory):
    rom = ROM.load(ROM_PATH, STOCK_SHA256)
    memory = memory_class(rom)
    memory.initialize(0xFFFF2CFC, bytes.fromhex("11223344"))
    memory.initialize(0xFFFFBFFC, bytes.fromhex("55667788"))
    memory.initialize(0xFFFF73FC, bytes.fromhex("11223344") + b"\xC7" * 32 + bytes.fromhex("55667788"))
    memory.watch(0xFFFF7400, 0xFFFF7420, "candidate diagnostic RAM")
    memory.watch(0xFFFF73FC, 0xFFFF7400, "adjacent before candidate")
    memory.watch(0xFFFF7420, 0xFFFF7424, "adjacent after candidate")
    memory.watch(0xFFFF2CFC, 0xFFFF2D00, "outside lower reset bound")
    memory.watch(0xFFFFBFFC, 0xFFFFC000, "outside upper reset bound")
    # Deliberately below the reset test region; reset-vector stack would overlap it.
    harness = FunctionHarness(memory, [(0xFA58, 0xFA84)], stack_pointer=0xFFFF2000, stack_size=0x100)
    # Bulk-loop path-condition unions grow quadratically in event logs. Keep complete
    # value/address provenance and disable only cumulative control-origin decoration.
    harness.cpu.track_control_sources = False
    limit = start if start >= end else start + ((end - start + 3) // 4) * 4
    result = harness.run(0xFA58, registers={4: start, 5: end}, allowed_writes=[(start, limit)], max_steps=160000)
    return harness, result


class GateClosureTests(unittest.TestCase):
    def test_nested_writer_negative_fixture_exposes_one_writer_precondition(self):
        result = probe_reentry()
        self.assertTrue(result["publication_violation_detected"])
        self.assertEqual(result["paused_outer_sequence"], 13)
        self.assertEqual(result["nested_writer_sequence"], 14)
        self.assertEqual(result["final_outer_sequence"], 14)

    def test_cmpge_signed_boundaries(self):
        for left, right, expected in ((0, 0, 1), (0xFFFFFFFF, 0, 0), (0, 0xFFFFFFFF, 1),
                                      (0x80000000, 0x7FFFFFFF, 0), (0x7FFFFFFF, 0x80000000, 1),
                                      (0x80000000, 0x80000000, 1)):
            h, _ = run_synthetic([0x3013, 0x0229, 0x000B, 0x0009], registers={0: left, 1: right})
            self.assertEqual(h.cpu.r[2], expected)

    def test_extuw_masks_without_changing_t_including_alias(self):
        for value in (0, 0x8000, 0xFFFF, 0xFFFF8001, 0xFFFFFFFF):
            h, _ = run_synthetic([0x0018, 0x610D, 0x600D, 0x0229, 0x000B, 0x0009], registers={0: value})
            self.assertEqual(h.cpu.r[:3], [value & 0xFFFF, value & 0xFFFF, 1])

    def test_standalone_compiled_decode_and_reason_entries(self):
        _, patched, _ = artifacts()
        for nibble in range(16):
            for prior in (0, 0xA5, 0xFF):
                h = FunctionHarness(Memory(patched), [(0xE1000, 0xE101A)])
                h.run(0xE1000, registers={4: nibble, 5: prior})
                self.assertEqual(h.cpu.r[0], nibble if nibble < 8 else 0 if nibble == 8 else prior)
        for freshness in (0, 1, 2, 3, 255):
            for packed in (0x11, 0x88, 0x9F):
                memory = Memory(patched)
                memory.initialize(0xFFFF7500, bytes([packed ^ 1, packed, 0, 0, freshness, 1, 0, 0]))
                h = FunctionHarness(memory, [(0xE101C, 0xE10B2)])
                h.run(0xE101C, registers={4: 0xFFFF7500})
                expected = 512 | 2 | 4 | 32 | 256
                expected |= int(packed != 0x11)
                expected |= 128 if packed == 0x9F else 0
                expected |= {0: 8, 1: 0, 2: 16}.get(freshness, 64)
                self.assertEqual(h.cpu.r[0], expected)

    def test_shift_left_forms_bits_and_t(self):
        h, _ = run_synthetic([0x4000, 0x0229, 0x4108, 0x0329, 0x000B, 0x0009],
                              registers={0: 0x80000001, 1: 0x40000001})
        self.assertEqual(h.cpu.r[:4], [2, 4, 1, 1])

    def test_dma_setup_real_fragment_extrema_seeded_inputs_and_propagation(self):
        rng = random.Random(0xA2C511)
        pairs = [(i, j) for i in (0, 1, 127, 255) for j in (0, 1, 127, 255)]
        pairs += [(rng.randrange(256), rng.randrange(256)) for _ in range(64)]
        for i, j in pairs:
            result = run_setup(i, j)
            expected = dict(rx_tcr=2, rx_sar=0xFFFFF00D, rx_dar=0xFFFF315A + 2 * i, rx_chcr=0x00040100,
                            tx_tcr=2, tx_sar=0xFFFF310A + 40 * j + 2 * i, tx_dar=0xFFFFF00B, tx_chcr=0x00031000)
            self.assertEqual(result["registers"], expected)
            self.assertEqual(result["instruction_count"], (0xC376 - 0xC31E) // 2)
            self.assertLess(expected["rx_dar"] + 2, 0xFFFF7400)
            self.assertLess(expected["tx_sar"] + 2, 0xFFFF7400)
            tx_write = next(e for e in result["accesses"] if e["address"] == "FFFFECE0" and e["mode"] == "w")
            self.assertIn("ram:FFFF31AC", tx_write["value_sources"])
            self.assertIn("ram:FFFF31AE", tx_write["value_sources"])

    def test_dma_fixture_rejects_enable_status_and_unmapped_peripherals(self):
        memory = DMAConfigurationMemory(ROM.load(ROM_PATH, STOCK_SHA256))
        with self.assertRaisesRegex(SimulationStop, "enable unsupported"):
            memory.write(0xFFFFECEC, 4, 0x31001)
        with self.assertRaisesRegex(SimulationStop, "status/peripheral reads"):
            memory.read(0xFFFFECEC, 4)
        with self.assertRaisesRegex(SimulationStop, "Unmapped/peripheral"):
            memory.write(0xFFFFECC0, 4, 0)

    def test_cmphs_unsigned_boundaries(self):
        for left, right in ((0, 0), (0, 1), (1, 0), (0xFFFFFFFF, 0), (0x7FFFFFFF, 0x80000000), (0xFFFFFFFF, 0xFFFFFFFF)):
            h, _ = run_synthetic([0x3012, 0x0229, 0x000B, 0x0009], registers={0: left, 1: right})
            self.assertEqual(h.cpu.r[2], int(left >= right))

    def test_actual_ram_pattern_full_reset_range_candidate_and_boundary_sentinels(self):
        h, result = run_ram_pattern(0xFFFF2D00, 0xFFFFBFFB)
        self.assertEqual(h.cpu.r[0], 0)
        self.assertEqual(h.cpu.r[4], 0xFFFFBFFC)
        self.assertEqual(h.memory.ram[0x2D00:0xBFFC], bytes.fromhex("a55a5aa5") * 0x24BF)
        self.assertEqual(h.memory.ram[0x2CFC:0x2D00], bytes.fromhex("11223344"))
        self.assertEqual(h.memory.ram[0xBFFC:0xC000], bytes.fromhex("55667788"))
        hits = [e for e in h.memory.events if "candidate diagnostic RAM" in e["watchpoints"]]
        self.assertEqual(len([e for e in hits if e["mode"] == "w"]), 16)
        self.assertEqual({e["pc"] for e in hits if e["mode"] == "w"}, {"0000FA64", "0000FA6C"})
        for event in hits:
            self.assertEqual(event["call_context"], ["0000FA58"])
            self.assertIn("fixture:register:r4", event["address_sources"])
        self.assertTrue(result["stack_pointer_restored"])

    def test_pattern_empty_reverse_and_one_word_span(self):
        for start, end, words in ((0xFFFF7400, 0xFFFF7400, 0), (0xFFFF7404, 0xFFFF7400, 0),
                                  (0xFFFF7400, 0xFFFF7401, 1), (0xFFFF7400, 0xFFFF7404, 1)):
            h, _ = run_ram_pattern(start, end)
            self.assertEqual(h.cpu.r[0], 0)
            self.assertEqual(sum(e["mode"] == "w" for e in h.memory.events), words * 2)

    def test_pattern_reports_explicitly_modeled_readback_corruption(self):
        for corrupt_pc in (0xFA66, 0xFA70):
            class CorruptRead(Memory):
                def read(self, address, size, address_sources=(), fetch=False):
                    value, origins = super().read(address, size, address_sources, fetch)
                    if not fetch and self.pc == corrupt_pc and address == 0xFFFF7400:
                        self.events[-1]["value"] = hx(value ^ 1)
                        self.events[-1]["value_sources"] += ["explicit_virtual_readback_fault"]
                        self.events[-1]["fixture_readback_corruption"] = True
                        return value ^ 1, origins | {"explicit_virtual_readback_fault"}
                    return value, origins
            h, _ = run_ram_pattern(0xFFFF7400, 0xFFFF7404, CorruptRead)
            self.assertEqual(h.cpu.r[0], 1)

    def test_dma_configuration_arithmetic_only(self):
        # Configuration contract only: no peripheral execution or DMA completion is fabricated.
        start, inclusive_end, transfer_size = 0xFFFF2D00, 0xFFFFBFFB, 4
        transfer_count = (inclusive_end - start + 1) >> 2
        self.assertEqual(transfer_count, 0x24BF)
        self.assertEqual(start + transfer_count * transfer_size, 0xFFFFBFFC)
        self.assertTrue(start <= 0xFFFF7400 < 0xFFFF7420 <= start + transfer_count * transfer_size)
        with self.assertRaisesRegex(SimulationStop, "Unmapped/peripheral"):
            Memory(ROM.load(ROM_PATH, STOCK_SHA256)).read(0xFFFFECC0, 4)

    def test_frozen_closure_all_paths_stack_and_preservation(self):
        audit = StaticAudit()
        report = audit.report()
        self.assertEqual(report["exact_added_stack_peak_bytes"], 124)
        self.assertEqual(report["instruction_bound"], 562)
        self.assertEqual(report["memory_access_bound"], 178)
        self.assertEqual(set(report["functions"]), {f"{entry:08X}" for entry in ENTRIES})
        self.assertEqual(report["preserved_state_proof"]["status"], "PASS")

    def test_sequential_scenarios_replay_and_candidate_propagation(self):
        first, second = scenario_series(), scenario_series()
        self.assertEqual(first, second)
        self.assertEqual(len(first["snapshots"]), 15)
        transition = first["snapshots"][4]
        self.assertEqual(transition["bytes"]["FFFF4BC1"], 2)
        self.assertEqual(transition["bytes"]["FFFF4BC2"], 1)
        state_writes = [e for e in transition["propagation"] if e["mode"] == "w" and e["address"] == "FFFF7415"]
        self.assertTrue(state_writes)
        self.assertIn("ram:FFFF4C8D", state_writes[-1]["value_sources"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
