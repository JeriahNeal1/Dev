import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sh2e import RAM_START
from m06_runtime import artifacts, fixture, run, output, request, expected_page, ENTRY, Closure, SP, RETURN, REQ, TX, FLAGS, CODE, LENGTH, INPUTS

COUNTS = {}


def inc(name, number=1):
    COUNTS[name] = COUNTS.get(name, 0) + number


class M06RuntimeTests(unittest.TestCase):
    def test_matcher_exact_header_body_and_all_single_byte_mutations(self):
        for page in (0, 1):
            original = request(page)
            for position in range(11):
                for value in range(256):
                    mutated = bytearray(original)
                    mutated[position] = value
                    expected = mutated[9] + 1 if (mutated[:9] == bytes.fromhex('8010F007BE4D303601')
                                                 and mutated[9] < 2 and mutated[10] == 4) else 0
                    cpu, _ = fixture(req=mutated)
                    run(cpu, ENTRY['match'])
                    self.assertEqual(cpu.r[0], expected, (page, position, value))
                    self.assertFalse([e for e in cpu.memory.events if e['mode'] == 'w'])
                    inc('match_single_byte_cases')

    def test_page_payload_and_source_independent_reason_partitions(self):
        for packed in range(256):
            for a, b in ((1, 1), (0, 1), (1, 0), (0, 0), (255, 255), (8, 9), (2, 1), (1, 2)):
                values = dict(source=packed ^ 0x5A, snapshot=packed, latch=(packed + 77) & 255,
                              flags=packed ^ 0xA5, target=a, current=b)
                for page in (0, 1):
                    cpu, values = fixture(inputs=values, out=0xFFFF7500)
                    cpu.r[4] = page
                    before = list(cpu.r)
                    run(cpu, ENTRY['page'])
                    self.assertEqual(output(cpu, 0xFFFF7500), expected_page(page, values))
                    self.assertEqual(cpu.r[8:], before[8:])
                    writes = [e for e in cpu.memory.events if e['mode'] == 'w']
                    self.assertEqual([(int(e['address'], 16), e['size']) for e in writes],
                                     [(0xFFFF7500 + i, 1) for i in range(4)])
                    source_reads = [int(e['address'], 16) for e in cpu.memory.events
                                    if e['mode'] == 'r' and int(e['address'], 16) in INPUTS.values()]
                    self.assertEqual(source_reads, [INPUTS[n] for n in
                        (('source', 'snapshot', 'latch', 'flags') if page == 0 else ('target', 'current', 'snapshot'))])
                    inc('page_partition_cases')
        # Each target/current byte equivalence class is backed by all 256 byte values.
        for value in range(256):
            for values in (dict(target=value, current=1), dict(target=1, current=value)):
                cpu, values = fixture(inputs=values, out=0xFFFF7500)
                cpu.r[4] = 1
                run(cpu, ENTRY['page'])
                self.assertEqual(output(cpu, 0xFFFF7500), expected_page(1, values))
                inc('reason_byte_equivalence_cases')

    def test_unmatched_default_replays_full_live_state_after_dead_registers(self):
        stock, _, _ = artifacts()
        malformed = []
        for p in range(11):
            data = bytearray(request())
            data[p] ^= 0x55
            malformed.append(data)
        for flags in range(256):
            req = malformed[flags % len(malformed)]
            a, _ = fixture(rom=stock, req=req, flags=flags, flags2=flags ^ 0x5A)
            b, _ = fixture(req=req, flags=flags, flags2=flags ^ 0x5A)
            run(a, 0x484B0, exits=(0x484C2,))
            run(b, 0x484B0, exits=(0x484C2,))
            self.assertEqual(a.r, b.r)
            self.assertEqual((a.sr, a.pr, a.mach, a.macl), (b.sr, b.pr, b.mach, b.macl))
            self.assertEqual(a.memory.ram[:SP - 128 - RAM_START], b.memory.ram[:SP - 128 - RAM_START])
            self.assertFalse(any(int(e['address'], 16) in INPUTS.values() for e in b.memory.events))
            inc('default_unmatched_pairs')

    def test_accepted_default_only_updates_expected_OEM_response_context(self):
        for page in (0, 1):
            for flags in range(256):
                cpu, _ = fixture(req=request(page), flags=flags, flags2=0xA4)
                before, sr, pr = list(cpu.r), cpu.sr, cpu.pr
                run(cpu, 0x484B0, exits=(0x484C2,))
                for r in (1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
                    self.assertEqual(cpu.r[r], before[r])
                self.assertEqual((cpu.sr, cpu.pr), (sr, pr))
                for address, expected in ((CODE, 0xFE), (LENGTH, 5), (FLAGS, flags & 127), (FLAGS + 1, 0xA4)):
                    self.assertEqual(cpu.memory.ram[address - RAM_START], expected)
                nonstack = [int(e['address'], 16) for e in cpu.memory.events if e['mode'] == 'w' and int(e['address'], 16) < SP - 128]
                self.assertEqual(nonstack, [LENGTH, CODE, FLAGS])
                inc('default_accepted_cases')

    def test_refill_rejections_replay_original_including_first_error_gate(self):
        stock, _, _ = artifacts()
        cases = []
        for value in range(256):
            if value != 0xFE:
                cases.append(dict(code=value))
            if value != 5:
                cases.append(dict(length=value))
            if value & 0x20 == 0:
                cases.append(dict(flags=value))
            if value & 1:
                cases.append(dict(flags2=value))
        bad = bytearray(request()); bad[5] ^= 1
        cases.append(dict(req=bad))
        for args in cases:
            a, _ = fixture(rom=stock, **args)
            b, _ = fixture(**args)
            run(a, 0x484F4, exits=(0x48500,))
            run(b, 0x484F4, exits=(0x48500,))
            self.assertEqual((a.r, a.sr, a.pr, a.mach, a.macl), (b.r, b.sr, b.pr, b.mach, b.macl), args)
            self.assertEqual(output(b), b'\xC7' * 4)
            self.assertFalse(any(int(e['address'], 16) in INPUTS.values() for e in b.memory.events))
            inc('refill_rejected_pairs')

    def test_accepted_refill_restores_preserved_registers_and_private_stack(self):
        for page in (0, 1):
            for flags in range(256):
                if flags & 0x20 == 0:
                    continue
                cpu, values = fixture(req=request(page), flags=flags,
                                      inputs=dict(snapshot=flags, target=flags ^ 0x5A, current=1))
                before, sr, pr = list(cpu.r), cpu.sr, cpu.pr
                run(cpu, 0x484F4)
                for r in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
                    self.assertEqual(cpu.r[r], before[r])
                self.assertEqual((cpu.sr, cpu.pr), (sr, pr))
                self.assertEqual(output(cpu), expected_page(page, values))
                stack_addresses = [int(e['address'], 16) for e in cpu.memory.events if e['mode'] == 'w' and int(e['address'], 16) >= SP - 128]
                self.assertEqual(min(stack_addresses), SP - 36)
                inc('refill_accepted_cases')

    def test_nested_page_execution_with_private_outputs_at_every_instruction_boundary(self):
        for page in (0, 1):
            baseline, values = fixture(out=0xFFFF7500, inputs=dict(snapshot=0x9F, target=0, current=255))
            baseline.r[4] = page
            run(baseline, ENTRY['page'])
            for boundary in range(len(baseline.trace) + 1):
                outer, values = fixture(out=0xFFFF7500, inputs=dict(snapshot=0x9F, target=0, current=255))
                outer.r[4], outer.pc = page, ENTRY['page']
                for _ in range(boundary):
                    outer.step()
                # Nested leaf shares read-only inputs, but has private registers/output.
                inner, _ = fixture(out=0xFFFF7600, inputs=values, sp=SP - 0x200)
                inner.memory = outer.memory
                inner.memory.ram[0x7600:0x7604] = b'\xC7' * 4
                inner.memory.initialized[0x7600:0x7604] = b'\x01' * 4
                inner.memory.write_allowlist.append((0xFFFF7600, 0xFFFF7604))
                inner.r[4], inner.r[5] = 1 - page, 0xFFFF7600
                run(inner, ENTRY['page'])
                run(outer, outer.pc)
                self.assertEqual(output(outer, 0xFFFF7500), expected_page(page, values))
                self.assertEqual(output(outer, 0xFFFF7600), expected_page(1 - page, values))
                inc('private_output_nested_boundaries')

    def test_complete_compiler_CFG_and_no_background_hook(self):
        report = Closure().report()
        self.assertEqual(report['functions']['default']['peak_stack_bytes'], 28)
        self.assertEqual(report['functions']['refill_hook']['peak_stack_bytes'], 36)
        self.assertEqual(report['functions']['page']['peak_stack_bytes'], 0)
        self.assertFalse(report['new_background_hook'])
        stock, raw, manifest = artifacts()
        self.assertEqual(raw.data[0x1193A:0x11940], stock.data[0x1193A:0x11940])
        self.assertTrue(all(not (f['address'] <= 0x11ADC < f['address'] + len(bytes.fromhex(f['after_hex']))) for f in manifest['overlay_fragments']))

