import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from m06_lookup_differential import artifacts, algebra, cpu_fixture, execute


class M06LookupTests(unittest.TestCase):
    def test_complete_domain_algebra_and_boundary_execution(self):
        stock, patched, _ = artifacts()
        self.assertEqual(algebra(stock, patched)['cases'], 131072)
        for kind in ('getter', 'setter'):
            for index in (0, 1, 399, 400, 401, 799, 800, 65535):
                a = execute(cpu_fixture(stock, kind, index), kind)
                b = execute(cpu_fixture(patched, kind, index), kind)
                self.assertEqual((a.r, a.pc, a.pr, a.sr, a.mach, a.macl),
                                 (b.r, b.pc, b.pr, b.sr, b.mach, b.macl))

    def test_corrupt_dictionary_index_changes_both_lookup_aliases(self):
        stock, patched, _ = artifacts()
        bad = patched.with_overlay(0x4F310, b'\x01', 'negative: wrong first compact index')
        with self.assertRaises(AssertionError):
            algebra(stock, bad)
        for kind, index in (('setter', 0), ('getter', 400)):
            a = execute(cpu_fixture(stock, kind, index), kind)
            b = execute(cpu_fixture(bad, kind, index), kind)
            self.assertNotEqual(a.pc, b.pc)

    def test_missing_SR_restore_breaks_original_call_boundary_contract(self):
        stock, patched, _ = artifacts()
        bad = patched.with_overlay(0x4F52C, bytes.fromhex('0009'), 'negative: omit SR pop/restore')
        a = execute(cpu_fixture(stock, 'setter', 1), 'setter')
        b = execute(cpu_fixture(bad, 'setter', 1), 'setter')
        self.assertNotEqual(a.r[15], b.r[15])
        self.assertNotEqual(a.sr, b.sr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
