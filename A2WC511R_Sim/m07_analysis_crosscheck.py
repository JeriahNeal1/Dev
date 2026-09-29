"""Scoped address/target predictions and negative controls for M0.7 objects."""
from hashlib import sha256
from pathlib import Path
import json

from m07_semantic import OUT, artifacts, fixture, execute, compare, SP, RETURN
from m06_value_analysis import Analysis, State
from sh2e import RAM_START, SimulationStop


def main():
    stock, patched, manifest = artifacts()
    contracts = []
    cases = [('division_nonzero', 0x4260, {0: 3, 1: 12345}, {}),
             ('division_zero', 0x4260, {0: 0, 1: 0x80000000}, {}),
             ('range_low', 0x1466E, {}, {0xFFFF4C8C: b'\x07', 0xFFFF4BA4: b'\xFF', 0xFFFF4BC0: b'\xA5'}),
             ('range_invalid', 0x1466E, {}, {0xFFFF4C8C: b'\xEA', 0xFFFF4BA4: b'\x55', 0xFFFF4BC0: b'\xA5'})]
    for name, entry, registers, ram in cases:
        for version, rom in [('stock', stock), ('replacement', patched)]:
            cpu = fixture(rom, entry, registers, ram)
            initial_ram = dict(ram)
            initial_ram[SP - 32] = b'\xA5' * 48
            state = State.fixture(dict(enumerate(cpu.r)), initial_ram, pr=cpu.pr, sr=cpu.sr, mach=cpu.mach, macl=cpu.macl)
            abstract = Analysis(rom, allowed_exits={RETURN}, max_steps=2000, widen_after=40).run([(entry, state)])
            execute(cpu)
            inclusion = abstract.check_concrete(cpu.memory.events, cpu.branch_edges, cpu.trace)
            assert inclusion['status'] == 'PASS', inclusion
            contracts.append(dict(name=name, version=version, inclusion=inclusion, analysis=abstract.report()))
    negatives = []
    bad_loop = patched.with_overlay(0x427A, bytes.fromhex('0009'), 'negative omitted MOVT preservation')
    try:
        compare(execute(fixture(stock, 0x4260, {0: 3, 1: 12345})), execute(fixture(bad_loop, 0x4260, {0: 3, 1: 12345})), True)
    except AssertionError as exc:
        negatives.append(dict(name='omitted_loop_T_save', detected=True, failure=str(exc)))
    else:
        raise AssertionError('Corrupt division loop escaped equivalence oracle')
    # Infer the table pointer from the linked literal, avoiding a stale hand address.
    candidate = manifest['candidates']['range_tail']
    blob = Path(candidate['binary']).read_bytes()
    table = bytes([0, 1, 2, 4, 8, 16, 32, 64, 128, 128, 128, 128, 128, 128, 128, 15])
    index = blob.index(table)
    bad_table = patched.with_overlay(candidate['start'] + index + 7, b'\x41', 'negative corrupted finite mapping')
    ram = {0xFFFF4C8C: b'\x07', 0xFFFF4BA4: b'\xFF', 0xFFFF4BC0: b'\xA5'}
    try:
        compare(execute(fixture(stock, 0x1466E, ram=ram)), execute(fixture(bad_table, 0x1466E, ram=ram)))
    except AssertionError as exc:
        negatives.append(dict(name='corrupted_range_mapping', detected=True, failure=str(exc)))
    else:
        raise AssertionError('Corrupt range table escaped equivalence oracle')
    cpu = fixture(patched, 0x4260, {0: 3, 1: 7})
    cpu.stack_bounds = (SP - 8, SP)
    try:
        execute(cpu)
    except SimulationStop as exc:
        negatives.append(dict(name='missing_extra_four_stack_bytes', detected=True, failure=str(exc)))
    else:
        raise AssertionError('Undeclared additional stack escaped harness')
    result = dict(status='PASS', contracts=contracts, negative_controls=negatives,
                  interpretation='Concrete observed accesses and targets lie inside modeled predictions for these explicit fixtures. Any abstraction unknown or cutoff blocks that contract exclusion; this is not whole-firmware ownership.',
                  source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  abstract_source_sha256=sha256(Path(__file__).with_name('m06_value_analysis.py').read_bytes()).hexdigest())
    (OUT / 'abstract_concrete_crosscheck.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', contracts=len(contracts), negative_controls=len(negatives),
                         abstract_unknowns={c['name'] + '_' + c['version']: len(c['analysis']['unknowns']) for c in contracts})))


if __name__ == '__main__':
    main()
