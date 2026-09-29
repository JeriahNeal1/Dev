"""Real OEM4260 signed division; no host division substitution in execution."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sh2e import ROM, Memory, CPU, FunctionHarness, STOCK_SHA256, RAM_START, sx, div1_step

ROM_PATH = 'C:/Dev/SubaruRoms/OEM/A2WC511R.bin'
COUNTS = {}


class OEMDivisionTests(unittest.TestCase):
    def test_actual_4260_all_SSM_length_dividends_and_signed_boundaries(self):
        rom = ROM.load(ROM_PATH, STOCK_SHA256)
        rng = random.Random(0x4260)
        cases = [(n, 3) for n in range(-2, 254)]
        values = [0, 1, -1, 2, -2, 0x7FFFFFFF, -0x80000000, 65535, -65535]
        cases.extend((a, b) for a in values for b in values if b)
        cases.extend((rng.randrange(-0x80000000, 0x80000000), rng.choice([3, -3, 7, -7, 255, -255, 0x7FFFFFFF])) for _ in range(256))
        for dividend, divisor in cases:
            m = Memory(rom)
            h = FunctionHarness(m, [(0x4260, 0x430A)])
            h.cpu.track_control_sources = False
            h.run(0x4260, registers={0: divisor, 1: dividend, 2: 0x12345678, 3: 0x87654321}, max_steps=150)
            expected = abs(dividend) // abs(divisor)
            if (dividend < 0) != (divisor < 0):
                expected = -expected
            self.assertEqual(h.cpu.r[0], expected & 0xFFFFFFFF, (dividend, divisor))
            self.assertEqual(h.cpu.r[2:4], [0x12345678, 0x87654321])
            self.assertEqual(min(int(e['address'], 16) for e in m.events if e['mode'] == 'w'), h.stack[1] - 8)
        COUNTS['actual_signed_divisions'] = len(cases)

    def test_actual_zero_divisor_error_side_effect(self):
        rom = ROM.load(ROM_PATH, STOCK_SHA256)
        m = Memory(rom)
        h = FunctionHarness(m, [(0x4260, 0x430A)])
        h.run(0x4260, registers={0: 0, 1: 123, 2: 0xA55AA55A}, allowed_writes=[(0xFFFF130C, 0xFFFF1310)])
        self.assertEqual(h.cpu.r[0], 0)
        self.assertEqual(h.cpu.r[2], 0xA55AA55A)
        self.assertEqual(m.ram[0x130C:0x1310], bytes.fromhex('0000044E'))
        COUNTS['zero_divisor_cases'] = 1

    def test_div1_all_control_bits_against_manual_branch_cases(self):
        values = [0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
        for q in (0, 1):
            for mode in (0, 1):
                for t in (0, 1):
                    for dividend in values:
                        for divisor in values:
                            initial_sr = 0x0ACE0C00 | (q << 8) | (mode << 9) | t
                            sign = dividend >> 31
                            shifted = ((dividend << 1) | t) & 0xFFFFFFFF
                            if q == 0 and mode == 0:
                                result = (shifted - divisor) & 0xFFFFFFFF
                                newq = (result > shifted) if sign == 0 else not (result > shifted)
                            elif q == 0 and mode == 1:
                                result = (shifted + divisor) & 0xFFFFFFFF
                                newq = not (result < shifted) if sign == 0 else result < shifted
                            elif q == 1 and mode == 0:
                                result = (shifted + divisor) & 0xFFFFFFFF
                                newq = (result < shifted) if sign == 0 else not (result < shifted)
                            else:
                                result = (shifted - divisor) & 0xFFFFFFFF
                                newq = not (result > shifted) if sign == 0 else result > shifted
                            expected_sr = (initial_sr & ~0x101) | (int(newq) << 8) | int(newq == mode)
                            self.assertEqual(div1_step(dividend, divisor, initial_sr), (result, expected_sr))
        COUNTS['DIV1_control_cases'] = 200


if __name__ == '__main__':
    unittest.main(verbosity=2)
