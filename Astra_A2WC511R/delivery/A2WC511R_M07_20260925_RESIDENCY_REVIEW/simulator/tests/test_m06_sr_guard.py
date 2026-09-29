"""Actual OEM interrupt-mask guard; no interrupt delivery or latency simulation."""
import sys
import unittest
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sh2e import ROM, Memory, CPU, FunctionHarness, STOCK_SHA256, RAM_START
from m06_value_analysis import Analysis, State

ROM_PATH = 'C:/Dev/SubaruRoms/OEM/A2WC511R.bin'
COUNTS = {}


class OEMSRGuardTests(unittest.TestCase):
    def test_register_SR_transfers_mask_and_T_Q_M_sources(self):
        data = bytearray(b'\xFF' * 0x100000)
        data[0x100:0x104] = bytes.fromhex('420E0302')  # ldc r2,sr; stc sr,r3
        values = [0, 1, 0x100, 0x200, 0x301, 0xF0, 0xFFFF0000, 0xFFFFFFFF]
        rom = ROM.synthetic(data, 'STC/LDC register SR storage semantics')
        for value in values:
            memory = Memory(rom)
            cpu = CPU(memory, [(0x100, 0x104)], (0xFFFFB000, 0xFFFFBFA0))
            cpu.pc, cpu.r[2], cpu.r[15] = 0x100, value, 0xFFFFBFA0
            cpu.sources[2] = {'fixture:requested_sr'}
            initial = list(cpu.r)
            state = State.fixture(dict(enumerate(initial)), sr=cpu.sr)
            abstract = Analysis(rom, allowed_exits={0x104}).run([(0x100, state)])
            cpu.step()
            self.assertEqual(cpu.sr, value & 0x0FFF0FFF)
            self.assertEqual(cpu.r, initial)
            cpu.step()
            self.assertEqual(cpu.r[3], value & 0x0FFF0FFF)
            self.assertEqual(cpu.t, value & 1)
            self.assertIn('fixture:requested_sr', cpu.sources[3])
            self.assertEqual(memory.events, [])
            self.assertEqual(abstract.check_concrete(memory.events, cpu.branch_edges, cpu.trace)['status'], 'PASS')
            self.assertTrue(abstract.states[(0x104, None)].r[3].contains(cpu.r[3]))
        COUNTS['SR_transfer_boundary_cases'] = len(values)

    def test_actual_2088_guard_saves_only_old_interrupt_mask_and_2098_restores(self):
        rom = ROM.load(ROM_PATH, STOCK_SHA256)
        # Pin the whole two-function fixture, including both RTS delay slots.
        actual = rom.data[0x2088:0x209C]
        self.assertEqual(actual.hex().upper(), '0002C9F035028D0124026503000B450E000B440E')
        destination = 0xFFFF5080
        cases = 0
        for old_mask in range(0, 0x100, 0x10):
            for requested in range(0, 0x100, 0x10):
                for extra in (0, 1, 0x300, 0x0ACE0301):
                    old_sr = old_mask | extra
                    memory = Memory(rom)
                    memory.initialize(destination, bytes.fromhex('DEADBEEF'))
                    memory.watch(destination, destination + 4, 'OEM_saved_interrupt_mask', modes='rw')
                    harness = FunctionHarness(memory, [(0x2088, 0x209C)])
                    harness.run(0x2088, registers={4: destination, 5: requested}, system_registers={'sr': old_sr},
                                allowed_writes=[(destination, destination + 4)], max_steps=10)
                    self.assertEqual(harness.cpu.sr, max(old_mask, requested))
                    self.assertEqual(memory.ram[destination - RAM_START:destination - RAM_START + 4], old_mask.to_bytes(4, 'big'))
                    writes = [e for e in memory.events if e['mode'] == 'w']
                    self.assertEqual(len(writes), 1)
                    self.assertEqual(writes[0]['address'], 'FFFF5080')
                    self.assertEqual(writes[0]['pc'], '00002090')
                    self.assertEqual(harness.cpu.r[15], harness.stack[1])
                    self.assertEqual(harness.cpu.r[4], destination)
                    # Restore takes the saved mask as an argument. Full old SR is not retained.
                    restored = FunctionHarness(Memory(rom), [(0x2098, 0x209C)])
                    restored.run(0x2098, registers={4: old_mask}, system_registers={'sr': harness.cpu.sr}, max_steps=2)
                    self.assertEqual(restored.cpu.sr, old_mask)
                    self.assertEqual(restored.memory.events, [])
                    cases += 1
        COUNTS.update(actual_guard_restore_pairs=cases, stock_ROM_sha256=rom.sha256,
                      fixture_start='00002088', fixture_end_exclusive='0000209C', fixture_sha256=sha256(actual).hexdigest(),
                      contract='Stores old SR & 0xF0, sets SR=max(old interrupt mask,requested mask); restore loads supplied saved mask. No full-SR preservation claim.',
                      timing='No interrupt delivery, LDC interrupt-suppression latency, or hardware timing modeled.')


if __name__ == '__main__':
    unittest.main(verbosity=2)
