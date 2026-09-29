"""Persist bounded M0.6 static/concrete checks; no whole-ROM acceptance implied."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from collections import Counter
import io
import json
import sys
import unittest

from sh2e import ROM, STOCK_SHA256, OPCODES
from differential import artifacts, execute
from m06_value_analysis import Analysis, State, Value, metadata_audit

ROOT = Path(__file__).parent
PROJECT = Path('C:/Dev/Astra_A2WC511R')
EXPORTS = PROJECT / 'reports/local/gate_closure/ida'


def seed_manifest():
    rom = ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin', STOCK_SHA256)
    path = EXPORTS / 'defined_code_export.json'
    db = json.loads(path.read_text())
    seeds = {}
    rejected = []

    def add(value, origin):
        if 0 <= value < 0x100000 and value % 2 == 0:
            seeds.setdefault(value, []).append(origin)
        else:
            rejected.append(dict(value=f'{value:08X}', origin=origin,
                                 classification='not a known aligned ROM entry; not evidence of unreachable behavior'))

    # Reset PC words; SP words are intentionally not mislabeled code entries.
    for a in (0, 8, 0xFFFF8):
        add(int.from_bytes(rom.data[a:a + 4], 'big'), dict(kind='reset_PC', word=f'{a:08X}'))
    for a in range(0xFFC50, 0xFFFF8, 4):
        add(int.from_bytes(rom.data[a:a + 4], 'big'), dict(kind='VBR_candidate_vector', word=f'{a:08X}'))
    for f in db['functions']:
        add(f['start'], dict(kind='IDA_defined_function', start=f"{f['start']:08X}"))
    for r in db['code']:
        pc = r['ea']
        w = int.from_bytes(rom.data[pc:pc + 2], 'big')
        if w >> 12 == 13:
            a = ((pc + 4) & ~3) + 4 * (w & 255)
            if a + 4 <= len(rom.data):
                add(int.from_bytes(rom.data[a:a + 4], 'big'),
                    dict(kind='defined_PC_relative_load_potential_pointer', pc=f'{pc:08X}', pool=f'{a:08X}'))
    # Known dispatcher target export remains separate. Missing it forces an open gate;
    # do not infer that these candidate roots enumerate every runtime entry mechanism.
    return dict(schema=1, rom=rom.identity(), export_sha256=sha256(path.read_bytes()).hexdigest(),
                entry_manifest_complete=False, whole_firmware_exclusion_gate='FAIL',
                explicit_unknown_entry_sources=['runtime VBR changes', 'computed dispatch tables and RAM-loaded function pointers',
                    'exception/interrupt contexts', 'RAM execution and peripheral/DMA changes', 'unlabeled executable paths'],
                dispatch_manifest_status='M0.6 diagnostic-dispatch owner has not supplied a complete manifest to this analyzer',
                seeds=[dict(pc=f'{pc:08X}', origins=origins) for pc, origins in sorted(seeds.items())],
                rejected_candidate_values=rejected,
                initial_state_policy='Whole-program attempts seed GPR/special/RAM as TOP unless an explicit entry contract proves values.',
                limitations='Candidate roots expand exploration. They are not asserted exhaustive or necessarily executable.')


def bounded_decoder():
    stock, _, _ = artifacts()
    state = State.fixture(memory={0xFFFF4BC1: b'\x00\x07'}, pr=0xFFFFFFFC)
    state.memory[0xFFFF4C8D] = Value.interval(0, 255)
    abstract = Analysis(stock, allowed_exits=[0xFFFFFFFC]).run([(0x147AC, state)])
    totals = Counter()
    for packed in range(256):
        h, _, _ = execute(stock, packed)
        checked = abstract.check_concrete(h.memory.events, h.cpu.branch_edges, h.cpu.trace)
        if checked['status'] != 'PASS':
            raise AssertionError(checked)
        totals.update(checked['checked'])
    return dict(analysis=abstract.report(), concrete_cases=256, inclusion=dict(totals),
                contract='Sequential OEM decoder call; PR sentinel is an explicit exit, prior outputs00/07, packed byte any0..255. No asynchronous hardware mutations.',
                hole_reads=abstract.exclusion(0xCE754, 0xFFAF8, 'read'),
                candidate_RAM_writes=abstract.exclusion(0xFFFF7400, 0xFFFF7420, 'write'))


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output = PROJECT / 'reports/local/m06_architecture/static_analysis' / stamp
    output.mkdir(parents=True, exist_ok=False)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_m06_analysis.py')
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (output / 'tests.log').write_text(log.getvalue(), encoding='utf-8')
    if not result.wasSuccessful():
        raise RuntimeError(f'Abstract analysis regression failed: {output}')
    reports = {'seed_manifest': seed_manifest(), 'metadata_audit': metadata_audit(), 'decoder_crosscheck': bounded_decoder()}
    for name, report in reports.items():
        (output / f'{name}.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    source_names = ['sh2e.py', 'm06_value_analysis.py', 'm06_analysis_run.py', 'tests/test_m06_analysis.py']
    summary = dict(status='PASS', tests=result.testsRun, concrete_decoder_cases=256, abstract_forms=len(OPCODES),
                   core_changed=(ROOT / 'sh2e.py').read_bytes() != (ROOT / 'backups/m06_architecture_core/sh2e.py').read_bytes(),
                   whole_firmware_exclusion_gate='FAIL', broad_run_performed=False,
                   source_hashes={name: sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names},
                   reason='Bounded inclusion infrastructure validated; incomplete entry/hardware/opaque-instruction obligations remain explicit.',
                   reports={name: str(output / f'{name}.json') for name in reports})
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(dict(status='PASS', tests=result.testsRun, directory=str(output), whole_firmware_gate='FAIL')))


def broad():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output = PROJECT / 'reports/local/m06_architecture/static_analysis' / (stamp + '_broad')
    output.mkdir(parents=True, exist_ok=False)
    manifest = seed_manifest()
    rom = ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin', STOCK_SHA256)
    analysis = Analysis(rom, max_steps=100000, max_memory=256, widen_after=3)
    analysis.uncertain(-1, 'entry_manifest_not_exhaustive', universal=True)
    analysis.uncertain(-1, 'asynchronous_interrupt_DMA_flash_effects_not_bounded', universal=True)
    analysis.run([(int(row['pc'], 16), State()) for row in manifest['seeds']])
    report = analysis.report()
    report['source_hashes'] = {name: sha256((ROOT / name).read_bytes()).hexdigest()
                               for name in ('sh2e.py', 'm06_value_analysis.py', 'm06_analysis_run.py')}
    report['seed_count'] = len(manifest['seeds'])
    report['exclusions'] = {label: analysis.exclusion(lo, hi, mode) for label, lo, hi, mode in
                            [('provisional_ROM_reads', 0xCE754, 0xFFAF8, 'read'),
                             ('alternative_ROM_reads', 0x859BC, 0xC0000, 'read'),
                             ('M0_RAM_writes', 0xFFFF7400, 0xFFFF7420, 'write'),
                             ('setter_table_reads', 0x4F310, 0x4F950, 'read')]}
    (output / 'entry_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (output / 'broad_value_analysis.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    summary = dict(status='FAIL', meaning='Whole-firmware exclusion is unproved; unknown behavior represented universally.',
                   steps=analysis.steps, states=len(analysis.states), worklist_complete=analysis.terminated,
                   seed_count=len(manifest['seeds']), unknown_count=len(analysis.unknowns),
                   unknown_reasons=dict(Counter(reason for _, reason in analysis.unknowns)),
                   supported_forms_observed=len(set(analysis.decoded) - {'OPAQUE'}), opaque_transfers=analysis.decoded['OPAQUE'],
                   exclusions={name: dict(status=result['status'], possible_accesses=len(result['possible_accesses']))
                               for name, result in report['exclusions'].items()},
                   report=str(output / 'broad_value_analysis.json'))
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in summary.items() if key != 'unknown_reasons'}))


if __name__ == '__main__':
    broad() if '--broad' in sys.argv else main()
