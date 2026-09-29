"""Focused synthetic regressions against actual reachability.py function bodies.

AST extraction avoids rerunning or overwriting the full-ROM report at import.
The simulator supplies an independent executed-path oracle for delayed branches.
"""
import ast
import collections
import hashlib
import json
import sys
import unittest
from pathlib import Path

OUT = Path(__file__).parent
sys.path.insert(0, 'C:/Dev/A2WC511R_Sim')
from sh2e import CPU, Memory, ROM


def fixture(words, longs=()):
    data = bytearray(b'\xFF' * 0x100000)
    for pc, w in words.items():
        data[pc:pc + 2] = w.to_bytes(2, 'big')
    for pc, v in longs:
        data[pc:pc + 4] = v.to_bytes(4, 'big')
    raw = {pc: dict(word=w, defined=True, ops=[]) for pc, w in words.items()}
    tree = ast.parse((OUT / 'reachability.py').read_text())
    body = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
    ns = dict(rom=data, raw=raw, crefs=collections.defaultdict(set), joins=set())
    exec(compile(body, str(OUT / 'reachability.py'), 'exec'), ns)
    for pc in words:
        t = ns['transfer'](pc)
        if t and t[1] is not None:
            ns['joins'].add(t[1])
    return ns


class AnalysisTests(unittest.TestCase):
    def test_delay_slot_later_ordinary_entry_retains_fallthrough(self):
        ns = fixture({0: 0xA002, 2: 0x0009, 4: 0xE100, 6: 0x0009, 8: 0xAFFB, 10: 0x0009})
        cpu = CPU(Memory(ROM.synthetic(ns['rom'], 'branch-slot/ordinary-entry regression')),
                  [(0, 12)], (0xFFFFBE00, 0xFFFFBFA0))
        cpu.pc, cpu.r[15] = 0, 0xFFFFBFA0
        actual = []
        for _ in range(6):
            actual.append(cpu.pc)
            cpu.step()
        self.assertEqual(actual, [0, 2, 8, 10, 2, 4])
        self.assertTrue(set(actual).issubset(ns['walk']({0})['reached']))

    def test_incoming_join_cannot_inherit_skipped_literal_load(self):
        ns = fixture({0: 0xA002, 2: 0x0009, 4: 0xD104, 6: 0x0009, 8: 0x410B, 10: 0x0009},
                     [(24, 0x40)])
        self.assertIsNone(ns['constant'](8, 1))

    def test_implicit_pointer_updates_discard_backward_constants(self):
        for instruction in (0x6216, 0x2126):  # mov.l @r1+,r2 / mov.l r2,@-r1
            with self.subTest(word=f'{instruction:04X}'):
                ns = fixture({0: 0xD105, 2: instruction, 4: 0x410B, 6: 0x0009}, [(24, 0x40)])
                self.assertIsNone(ns['constant'](4, 1))

    def test_unjoined_literal_load_still_resolves(self):
        ns = fixture({0: 0xD105, 2: 0x0009, 4: 0x410B, 6: 0x0009}, [(24, 0x40)])
        self.assertEqual(ns['constant'](4, 1), (0x40, 0))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AnalysisTests))
    report = dict(status='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
                  failures=len(result.failures), errors=len(result.errors),
                  source_sha256=hashlib.sha256((OUT / 'reachability.py').read_bytes()).hexdigest(),
                  test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  classification='Synthetic analysis regressions, not whole-program ownership proof')
    (OUT / 'analysis_regression.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
