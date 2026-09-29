"""Final two-page fragment ABI and bounded compiled CFG proof at OEM return."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

from sh2e import OPCODES, sx
from m07_dispatch_abi import PROJECT, OUT, dispatcher, full_unmatched_equal
from m07_semantic import artifacts as semantic_artifacts

DIRECTORY = PROJECT / 'reports/local/m07_residency/protocol/two_pages_01'


def artifacts():
    manifest = json.loads((DIRECTORY / 'manifest.json').read_text())
    stock, patched, _ = semantic_artifacts()
    for fragment in manifest['fragments']:
        blob = (DIRECTORY / (fragment['name'] + '.bin')).read_bytes()
        assert len(blob) == fragment['bytes'] and sha256(blob).hexdigest() == fragment['sha256']
        assert fragment['start'] + len(blob) == fragment['end_exclusive']
        patched = patched.with_overlay(fragment['start'], blob, 'M07 two-page ' + fragment['name'])
    patched = patched.with_overlay(0x484B0, bytes.fromhex('D201422B0009000900014770'), 'M07 default entry trampoline')
    return stock, patched, manifest


def compiled_cfg(rom, observed_pcs, observed_edges):
    """Separate literal/data pools from reachable compiled instructions mechanically."""
    ranges = [(0x42A4, 0x42CE), (0x14770, 0x147A4), (0x484B0, 0x484B6)]
    words, edges, pending = {}, set(), [0x484B0]
    calls = {0x14776: (0x42A4, 0x1477A)}
    jumps = {0x484B2: 0x14770, 0x147A0: 0x484BC}
    while pending:
        pc = pending.pop()
        if pc == 0x484BC or pc in words:
            continue
        assert any(a <= pc < b for a, b in ranges), f'CFG escaped executable fragments: {pc:X}'
        word = int.from_bytes(rom.data[pc:pc + 2], 'big')
        spec = next((s for s in OPCODES if word & s.mask == s.value), None)
        assert spec is not None, f'Unknown compiled opcode at{pc:X}'
        words[pc] = dict(word=f'{word:04X}', form=spec.name)
        if spec.name in ('bf', 'bt'):
            targets = [pc + 2, pc + 4 + 2 * sx(word & 255, 8)]
        elif spec.name == 'bra':
            delay = pc + 2
            delayed_word = int.from_bytes(rom.data[delay:delay + 2], 'big')
            delayed = next(s for s in OPCODES if delayed_word & s.mask == s.value)
            assert not delayed.branch
            words[delay] = dict(word=f'{delayed_word:04X}', form=delayed.name, delay_slot=True)
            targets = [pc + 4 + 2 * sx(word & 4095, 12)]
        elif spec.name in ('jsr', 'jmp', 'rts'):
            delay = pc + 2
            delayed_word = int.from_bytes(rom.data[delay:delay + 2], 'big')
            delayed = next(s for s in OPCODES if delayed_word & s.mask == s.value)
            assert not delayed.branch
            words[delay] = dict(word=f'{delayed_word:04X}', form=delayed.name, delay_slot=True)
            if spec.name == 'jsr':
                targets = list(calls[pc])
            elif spec.name == 'jmp':
                targets = [jumps[pc]]
            else:
                targets = [0x1477A]
        else:
            targets = [pc + 2]
        for target in targets:
            edges.add((pc, target))
            pending.append(target)
    assert set(words) <= observed_pcs, sorted(set(words) - observed_pcs)
    assert not any(v['form'].startswith(('stc', 'ldc', 'sts_', 'lds_')) for v in words.values())
    # Pin actual indirect destinations and the bounded counter initialization/step.
    assert int.from_bytes(rom.data[0x147A4:0x147A8], 'big') == 0x42A4
    assert int.from_bytes(rom.data[0x147A8:0x147AC], 'big') == 0x484BC
    assert int.from_bytes(rom.data[0x484B8:0x484BC], 'big') == 0x14770
    assert rom.data[0x42AE:0x42B0] == bytes.fromhex('E412')
    assert rom.data[0x42B6:0x42B8] == bytes.fromhex('E40C')
    assert rom.data[0x42C2:0x42C4] == bytes.fromhex('4410')
    assert rom.data[0x42C4:0x42C6] == bytes.fromhex('8BF9')
    counter_writes = [pc for pc, v in words.items()
                      if v['form'] in ('mov_imm', 'dt') and (int(v['word'], 16) >> 8 & 15) == 4]
    assert set(counter_writes) == {0x42AE, 0x42B6, 0x42C2}
    return dict(status='PASS', instruction_addresses={f'{a:08X}': v for a, v in sorted(words.items())},
                CFG_edges=[[f'{a:08X}', f'{b:08X}'] for a, b in sorted(edges)],
                called_functions=[dict(call='00014776', target='000042A4', return_pc='0001477A')],
                loops=[dict(header='000042BA', counter='R4', initial_values=[12, 18], update='DT R4', backedge='000042C4', maximum_iterations=18)],
                frame=dict(main_pushes=['R1', 'R4'], main_peak=8, matcher_peak=0, main_pops=['R4', 'R1'], OEM_frame=28, combined_peak=36),
                return_contract='One synchronous helpercall; SPbalancedbefore484BC; existing484C4restores callerPR before484D0RTS.',
                state_contract='NoSRsave/load,interruptmask,MACH/MACL/GBR/VBR/FPUinstruction in reachable payload. CLRT restores provenT0; allotherSRbits unchanged.',
                coverage='Every statically reachable compiled instruction was executed by validpages or single-byte negative cases; literal pools were not decoded as code.')


def validate():
    stock, patched, manifest = artifacts()
    observed_pcs, observed_edges = set(), set()
    counters = Counter()
    path_counts = Counter()
    max_steps, max_access = {}, {}
    examples = []
    def observe(cpu, key):
        payload = [e for e in cpu.trace if 0x42A4 <= int(e['pc'], 16) < 0x42CE or
                   0x14770 <= int(e['pc'], 16) < 0x147A4 or 0x484B0 <= int(e['pc'], 16) < 0x484B6]
        addresses = {int(e['pc'], 16) for e in payload}
        observed_pcs.update(addresses)
        observed_edges.update(cpu.branch_edges)
        max_steps[key] = max(max_steps.get(key, 0), len(payload))
        accesses = [e for e in cpu.memory.events if int(e['pc'], 16) in addresses]
        max_access[key] = max(max_access.get(key, 0), len(accesses))
        return len(payload), len(accesses)
    for page in manifest['pages']:
        request = bytes.fromhex(page['request_without_checksum'])
        for flags in (0, 0x10, 0x20, 0x80, 0xFF):
            for error in (0, 1, 8, 0xFF):
                for sr in (0, 1, 0x0ACE03F0, 0x0ACE03F1):
                    before = dispatcher(stock, request, flags, error, sr)
                    after = dispatcher(patched, request, flags, error, sr)
                    for reg in range(16):
                        if reg not in (0, 3):
                            assert before.r[reg] == after.r[reg], (page['page'], reg)
                    for key in ('sr', 'pr', 'pc', 'mach', 'macl'):
                        assert getattr(before, key) == getattr(after, key), key
                    ram = after.memory.ram
                    assert ram[0x6401] == page['response_opcode']
                    assert ram[0x6405] == page['data_bytes'] + 1
                    assert ram[0x63FF] == page['data_bytes'] + 5
                    assert ram[0x649A] & 0x90 == 0x10 and ram[0x649B] & 1 == 0
                    allowed = {0x63FF, 0x6401, 0x6405, 0x649A, 0x649B}
                    diff = {i for i, (a, b) in enumerate(zip(before.memory.ram, ram)) if a != b}
                    diff -= set(range(0xBFA0 - 36, 0xBFA0 - 28))
                    assert diff <= allowed, diff
                    counts = observe(after, 'accepted_page' + str(page['page']))
                    counters['accepted_full_dispatcher_cases'] += 1
                    if flags == error == sr == 0:
                        examples.append(dict(page=page['page'], payload_instructions=counts[0], payload_accesses=counts[1],
                                             return_registers=after.r, return_SR=after.sr, return_PR=after.pr,
                                             trace=after.trace, memory_events=after.memory.events))
        for index in range(len(request)):
            for value in range(256):
                if value == request[index]:
                    continue
                changed = bytearray(request)
                changed[index] = value
                if changed[4] in (0xA0, 0xA8, 0xB0, 0xB8, 0xBF, 0x9F):
                    counters['mutations_routed_to_existing_OEM_handlers_separate_scope'] += 1
                    continue
                before, after = dispatcher(stock, changed), dispatcher(patched, changed)
                full_unmatched_equal(before, after)
                observe(after, 'rejected')
                counters['rejected_full_dispatcher_pairs'] += 1
    cfg = compiled_cfg(patched, observed_pcs, observed_edges)
    report = dict(status='PASS', stock_sha256=stock.sha256, experimental_overlay_sha256=patched.sha256,
        manifest_sha256=sha256((DIRECTORY / 'manifest.json').read_bytes()).hexdigest(), counts=counters,
        complete_dispatcher_entry='0004828C', complete_dispatcher_return='HARNESS_RETURN_SENTINEL_FFFFFFFC',
        exact_frame_bytes=36, OEM_frame_bytes=28, added_adapter_frame_bytes=8,
        payload_instruction_bounds_including_entry=max_steps, payload_data_access_bounds_including_entry=max_access,
        bound_argument='Matcher selects12or18comparisons and either fails at one checkedbyte or completes; final-byte failure/acceptance and both header partitions exhaust all count bounds. Complete-byte mutation domain plus accepted paths covers every reachable opcode.',
        qualified_predicate='Canonical header/body match only; original upstream parser/checksum/security/serialization gates are separate root-owned wire evidence.',
        gates=dict(full_dispatcher_preservation='PASS', finite_matcher_and_frame_CFG='PASS', complete_object_ownership='FAIL', physical_timing='PHYSICAL/BENCH REQUIRED'),
        no_background_hook=True, no_new_refill_hook=True, no_persistent_state=True,
        examples=examples, compiled_CFG=cfg,
        source_hashes={n: sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ('m07_two_page_abi.py', 'm07_dispatch_abi.py', 'sh2e.py')})
    (OUT / 'two_page_dispatch_abi.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('examples', 'compiled_CFG', 'source_hashes')}))


if __name__ == '__main__':
    validate()
