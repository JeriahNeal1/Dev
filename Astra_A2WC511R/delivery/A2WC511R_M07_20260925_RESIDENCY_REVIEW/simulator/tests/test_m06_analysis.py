import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sh2e import ROM, Memory, CPU, OPCODES, STOCK_SHA256
from differential import artifacts, execute
from m06_value_analysis import Analysis, State, Value, V, TOP, BOOL, metadata_audit


def single_opcode(word):
    data = bytearray(b'\xFF' * 0x100000)
    data[0x100:0x108] = word.to_bytes(2, 'big') + bytes.fromhex('0009FEDCBA98')
    rom = ROM.synthetic(data, 'abstract/concrete single instruction contract')
    mem = Memory(rom)
    payload = bytes(range(256))
    mem.initialize(0xFFFF5000, payload)
    cpu = CPU(mem, [(0x100, 0x108)], (0xFFFFB000, 0xFFFFBFA0))
    cpu.pc, cpu.pr, cpu.sr_other, cpu.t, cpu.mach, cpu.macl = 0x100, 0x108, 0x102, 1, 0xDEADBEEF, 0xFEDCBA98
    cpu.call_context = ['00000100']
    cpu.r = [0x33] * 16
    cpu.r[1], cpu.r[2], cpu.r[15] = 0xFFFF5040, 0xFFFF5080, 0xFFFFBFA0
    if word & 0xF00F in (0x000C, 0x000E):
        cpu.r[0] = 0x30
    state = State.fixture(dict(enumerate(cpu.r)), {0xFFFF5000: payload},
                          pr=cpu.pr, sr=cpu.sr, mach=cpu.mach, macl=cpu.macl)
    abstract = Analysis(rom)
    next_states = abstract.transfer(0x100, None, state)
    cpu.step()
    for i, value in enumerate(cpu.r):
        if not any(s.r[i].contains(value) for _, _, s in next_states):
            raise AssertionError(f'{word:04X} r{i} escaped abstract value {value:08X}')
    for key in ('pr', 'sr', 'mach', 'macl'):
        if not any(getattr(s, key).contains(getattr(cpu, key)) for _, _, s in next_states):
            raise AssertionError(f'{word:04X} {key} escaped abstract value')
    return abstract.check_concrete(mem.events, cpu.branch_edges, cpu.trace)


class M06AnalysisTests(unittest.TestCase):
    def test_all_supported_opcode_forms_match_single_step_concrete(self):
        self.assertEqual(metadata_audit()['overlaps'], [])
        for spec in OPCODES:
            word = spec.value | ((2 << 8) & ~spec.mask) | ((1 << 4) & ~spec.mask)
            # Small displacement keeps synthetic PC-relative loads in the explicit ROM.
            if spec.name in ('movl_pc', 'movw_pc'):
                word = spec.value | (2 << 8)
            with self.subTest(form=spec.name, word=f'{word:04X}'):
                self.assertEqual(single_opcode(word)['status'], 'PASS')

    def test_alias_postincrement_and_predecrement(self):
        for word in (0x6226, 0x6224, 0x2226, 0x622A):
            with self.subTest(word=f'{word:04X}'):
                self.assertEqual(single_opcode(word)['status'], 'PASS')

    def test_new_lookup_opcode_semantics_independent_boundary_values(self):
        # Indexed byte load must use old r0 before overwriting it, then sign-extend.
        for opcode, raw, expected in ((0x001C, b'\x80', 0xFFFFFF80),
                                      (0x001E, bytes.fromhex('81234567'), 0x81234567)):
            data = bytearray(b'\xFF' * 0x100000)
            data[0x100:0x102] = opcode.to_bytes(2, 'big')
            memory = Memory(ROM.synthetic(data, 'indexed-load alias semantics'))
            memory.initialize(0xFFFF5080, raw)
            cpu = CPU(memory, [(0x100, 0x102)], (0xFFFFB000, 0xFFFFBFA0))
            cpu.pc, cpu.r[0], cpu.r[1], cpu.r[15], cpu.t = 0x100, 0x40, 0xFFFF5040, 0xFFFFBFA0, 1
            cpu.step()
            self.assertEqual(cpu.r[0], expected)
            self.assertEqual(cpu.r[1], 0xFFFF5040)
            self.assertEqual(cpu.t, 1)
            self.assertEqual(memory.events[0]['address'], 'FFFF5080')

    def test_RX_indexed_byte_store_truncates_value_and_preserves_registers_T(self):
        data = bytearray(b'\xFF' * 0x100000)
        data[0x100:0x102] = bytes.fromhex('0324')
        memory = Memory(ROM.synthetic(data, 'actual RX indexed byte store form'))
        memory.initialize(0xFFFF5083, b'\x55')
        cpu = CPU(memory, [(0x100, 0x102)], (0xFFFFB000, 0xFFFFBFA0))
        cpu.pc, cpu.r[0], cpu.r[2], cpu.r[3], cpu.r[15], cpu.t = 0x100, 3, 0x12345680, 0xFFFF5080, 0xFFFFBFA0, 1
        before = list(cpu.r)
        cpu.step()
        self.assertEqual(cpu.r, before)
        self.assertEqual(cpu.t, 1)
        self.assertEqual(memory.events[0]['address'], 'FFFF5083')
        self.assertEqual(memory.events[0]['value'], '00000080')

    def test_RX_signed_greater_than_boundaries(self):
        for a, b, expected in ((0, 0, 0), (0, 0xFFFFFFFF, 1), (0xFFFFFFFF, 0, 0),
                               (0x80000000, 0x7FFFFFFF, 0), (0x7FFFFFFF, 0x80000000, 1)):
            data = bytearray(b'\xFF' * 0x100000)
            data[0x100:0x102] = bytes.fromhex('3017')
            cpu = CPU(Memory(ROM.synthetic(data, 'CMP/GT signed boundary')), [(0x100, 0x102)], (0xFFFFB000, 0xFFFFBFA0))
            cpu.pc, cpu.r[0], cpu.r[1], cpu.r[15] = 0x100, a, b, 0xFFFFBFA0
            cpu.step()
            self.assertEqual(cpu.t, expected)

    def test_A8_shift8_shift16_preserve_T_and_truncate(self):
        for word, bits in ((0x4018, 8), (0x4028, 16)):
            for value in (0, 1, 0xFFFF, 0x80000001, 0xFFFFFFFF):
                data = bytearray(b'\xFF' * 0x100000)
                data[0x100:0x102] = word.to_bytes(2, 'big')
                cpu = CPU(Memory(ROM.synthetic(data, 'OEM A8 address construction shift')), [(0x100, 0x102)], (0xFFFFB000, 0xFFFFBFA0))
                cpu.pc, cpu.r[0], cpu.r[15], cpu.t = 0x100, value, 0xFFFFBFA0, 1
                cpu.step()
                self.assertEqual(cpu.r[0], (value << bits) & 0xFFFFFFFF)
                self.assertEqual(cpu.t, 1)
    def test_sub_register_wrap_and_T_preservation(self):
        for left, right, expected in ((0, 1, 0xFFFFFFFF), (0x80000000, 1, 0x7FFFFFFF),
                                      (0x7FFFFFFF, 0xFFFFFFFF, 0x80000000)):
            data = bytearray(b'\xFF' * 0x100000)
            data[0x100:0x102] = bytes.fromhex('3018')
            cpu = CPU(Memory(ROM.synthetic(data, 'SUB wrap semantics')), [(0x100, 0x102)], (0xFFFFB000, 0xFFFFBFA0))
            cpu.pc, cpu.r[0], cpu.r[1], cpu.r[15], cpu.t = 0x100, left, right, 0xFFFFBFA0, 1
            cpu.step()
            self.assertEqual(cpu.r[0], expected)
            self.assertEqual(cpu.t, 1)

    def test_lattice_join_widen_wrap_and_bitand_inclusion(self):
        rng = random.Random(0xA2C511)
        for _ in range(1000):
            left = [rng.randrange(1 << 32) for _ in range(10)]
            right = [rng.randrange(1 << 32) for _ in range(10)]
            a, b = Value.finite(left), Value.finite(right)
            for n in left + right:
                self.assertTrue(a.join(b).contains(n))
                self.assertTrue(a.widen(b).contains(n))
            for x, y in zip(left, right):
                self.assertTrue(a.add(b).contains(x + y))
                self.assertTrue(a.bitand(b).contains(x & y))
        self.assertTrue(V(0xFFFFFFFF).add(V(1)).contains(0))
        self.assertEqual(TOP.bitand(V(255)).bounds, (0, 255))

    def test_unknown_store_havocs_aliases_and_blocks_exclusion(self):
        stock, _, _ = artifacts()
        state = State.fixture(memory={0xFFFF7400: b'\xA5\x5A'})
        abstract = Analysis(stock)
        abstract.write(state, 0x100, TOP, 1, V(0))
        self.assertEqual(state.memory, {})
        self.assertEqual(abstract.exclusion(0xFFFF7400, 0xFFFF7420, 'write')['status'], 'FAIL')

    def test_overlapping_weak_stores_preserve_all_alternatives(self):
        stock, _, _ = artifacts()
        state = State.fixture(memory={0xFFFF7400: b'\xAA' * 6})
        abstract = Analysis(stock)
        abstract.write(state, 0x100, Value.finite([0xFFFF7400, 0xFFFF7402]), 4, V(0x11223344))
        # Unaligned second possibility itself creates an exception/hardware frontier.
        self.assertTrue(abstract.unknowns)
        self.assertEqual(state.memory, {})
        state = State.fixture(memory={0xFFFF7400: b'\xAA' * 3})
        abstract.write(state, 0x100, Value.finite([0xFFFF7400, 0xFFFF7401]), 1, V(0x11))
        self.assertTrue(state.memory[0xFFFF7400].contains(0xAA))
        self.assertTrue(state.memory[0xFFFF7400].contains(0x11))

    def test_opaque_instruction_and_unknown_control_are_universal_fail(self):
        data = bytearray(b'\xFF' * 0x100000)
        data[0x102:0x104] = bytes.fromhex('6212')  # read through now-unknown r1
        rom = ROM.synthetic(data, 'unknown instruction exclusion negative control')
        abstract = Analysis(rom, max_steps=3).run([(0x100, State.fixture({1: 0x2000}))])
        self.assertEqual(abstract.exclusion(0xE1000, 0xE1364, 'read')['status'], 'FAIL')
        self.assertIn((0x102, 'read', 4), abstract.observations)
        self.assertEqual(abstract.observations[(0x102, 'read', 4)][0], TOP)
        self.assertTrue(any(mode == 'unknown_downstream_target' for _, mode, _ in abstract.observations))

    def test_unknown_branch_executes_slot_observation_without_target_pruning(self):
        data = bytearray(b'\xFF' * 0x100000)
        data[0x100:0x104] = bytes.fromhex('410B2230')  # jsr @r1 ; mov.b r3,@r2
        rom = ROM.synthetic(data, 'unknown branch preserves slot write observation')
        abstract = Analysis(rom).run([(0x100, State.fixture({2: 0xFFFF7400, 3: 0xA5}))])
        self.assertTrue(abstract.observations[(0x102, 'write', 1)][0].contains(0xFFFF7400))
        self.assertEqual(abstract.exclusion(0xFFFF7400, 0xFFFF7420, 'write')['status'], 'FAIL')

    def test_worklist_budget_never_accepts_absence(self):
        data = bytearray(b'\xFF' * 0x100000)
        data[0x100:0x102] = bytes.fromhex('0009')
        abstract = Analysis(ROM.synthetic(data, 'budget negative'), max_steps=1).run([(0x100, State())])
        self.assertFalse(abstract.terminated)
        self.assertEqual(abstract.exclusion(0xE1000, 0xE1364, 'read')['status'], 'FAIL')

    def test_unstarted_or_empty_seed_analysis_cannot_accept_exclusion(self):
        stock, _, _ = artifacts()
        for abstract in (Analysis(stock), Analysis(stock).run([])):
            self.assertEqual(abstract.exclusion(0x4F310, 0x4F950, 'read')['status'], 'FAIL')
            self.assertEqual(abstract.report()['global_exclusion_gate'], 'FAIL')

    def test_stock_decoder_all_inputs_concrete_memory_targets_included(self):
        stock, _, _ = artifacts()
        for packed in range(256):
            harness, result, _ = execute(stock, packed)
            # Exact declared initial fixture, copied before the concrete run by the helper
            # below from independent constants rather than post-execution RAM.
            state = State.fixture({i: ((0x9E3779B9 * (i + 1)) ^ (packed * 0x01010101)) & 0xFFFFFFFF for i in range(15)},
                                  {0xFFFF4C8D: bytes([packed]), 0xFFFF4BC1: b'\x00\x07'},
                                  pr=0xFFFFFFFC, sr=0xF0, mach=0x89ABCDEF ^ packed, macl=0x76543210 ^ packed)
            state.r[15] = V(0xFFFFBFA0)
            abstract = Analysis(stock, allowed_exits=[0xFFFFFFFC]).run([(0x147AC, state)])
            checked = abstract.check_concrete(harness.memory.events, harness.cpu.branch_edges, harness.cpu.trace)
            self.assertEqual(checked['status'], 'PASS', (packed, checked['failures'][:1]))

    def test_joined_decoder_contract_contains_all_256_concrete_cases(self):
        stock, _, _ = artifacts()
        state = State.fixture(memory={0xFFFF4BC1: b'\x00\x07'}, pr=0xFFFFFFFC)
        state.memory[0xFFFF4C8D] = Value.interval(0, 255)
        abstract = Analysis(stock, allowed_exits=[0xFFFFFFFC]).run([(0x147AC, state)])
        self.assertEqual(abstract.exclusion(0xE1000, 0xE1364, 'read')['status'], 'PASS')
        self.assertEqual(abstract.exclusion(0xFFFF7400, 0xFFFF7420, 'write')['status'], 'PASS')
        for packed in range(256):
            h, _, _ = execute(stock, packed)
            self.assertEqual(abstract.check_concrete(h.memory.events, h.cpu.branch_edges, h.cpu.trace)['status'], 'PASS')

    def test_ordinary_entry_into_former_delay_slot_keeps_distinct_successor(self):
        data = bytearray(b'\xFF' * 0x100000)
        data[0:12] = bytes.fromhex('A0020009E1000009AFFB0009')
        abstract = Analysis(ROM.synthetic(data, 'abstract delay-slot context regression')).run([(0, State())])
        self.assertIn((4, None), abstract.states)
        self.assertIn((2, 8), abstract.states)
        self.assertIn((2, None), abstract.states)
