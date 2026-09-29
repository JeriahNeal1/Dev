"""Persist final M0.6 compiler/runtime proof and explicitly virtual callback fixtures."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import io
import json
import sys
import unittest

from m06_runtime import artifacts, fixture, run, output, request, response, expected_page, Closure, BUILD, INPUTS, SP, ENTRY
from m06_lookup_differential import algebra, cpu_fixture, execute as lookup_execute
from sh2e import RAM_START, OPCODES

ROOT = Path(__file__).parent
OUT = Path('C:/Dev/Astra_A2WC511R/reports/local/m06_architecture/runtime')


def callback_fixtures():
    _, raw, manifest = artifacts()
    scenarios = [dict(source=17, snapshot=17, latch=1, flags=2, target=1, current=1),
                 dict(source=33, snapshot=17, latch=0, flags=0, target=2, current=1),
                 dict(source=136, snapshot=136, latch=255, flags=128, target=0, current=0),
                 dict(source=159, snapshot=159, latch=1, flags=2, target=5, current=4),
                 dict(source=255, snapshot=255, latch=255, flags=255, target=255, current=255),
                 dict(source=0, snapshot=0, latch=0, flags=0, target=1, current=1)]
    cases = []
    for i, values in enumerate(scenarios):
        for page in (0, 1):
            cpu, inputs = fixture(req=request(page), inputs=values)
            run(cpu, 0x484F4)
            payload = output(cpu)
            if payload != expected_page(page, inputs):
                raise AssertionError('Fixture payload mismatch')
            cases.append(dict(case_id=f'scenario_{i}_page_{page}', page=page,
                request_hex=request(page).hex(), response_hex=response(payload).hex(), payload_hex=payload.hex(),
                inputs=inputs, event_id=len(cases), scheduling='Separate explicit callback execution; not an atomic paired sample.',
                provenance='Actual compiled m06_04 response-refill adapter and C functions, explicit virtual OEM RAM/context.',
                framing_provenance='SSM header/checksum assembled by host from actual four TX-buffer bytes. Root full-OEM TX harness supplies separate wire-framing validation.',
                instruction_count=len(cpu.trace), trace_sha256=sha256(json.dumps(cpu.trace, sort_keys=True).encode()).hexdigest(),
                tx_writes=[e for e in cpu.memory.events if e['mode'] == 'w' and 0xFFFF6492 <= int(e['address'], 16) < 0xFFFF6496],
                source_reads=[e for e in cpu.memory.events if e['mode'] == 'r' and int(e['address'], 16) in INPUTS.values()]))
    return dict(status='PASS', classification='VIRTUAL_COMPILED_HANDLER_PAYLOAD_NOT_PHYSICAL_TELEMETRY',
                build=str(BUILD), ROM_sha256=raw.sha256,
                payload_sha256=manifest['artifacts']['m06.EXPERIMENTAL.code.bin'],
                ELF_sha256=manifest['artifacts']['A2WC511R_M06.EXPERIMENTAL.elf'], cases=cases,
                limitations='No actual serial echo/device/TCU behavior; page reads sequential, freshness/coherence unproved. Each page invokes a separate callback.')


def lookup_extension():
    stock, raw, manifest = artifacts()
    result = algebra(stock, raw)
    for kind in ('getter', 'setter'):
        for i in (0, 399, 400, 799, 800, 65535):
            a = lookup_execute(cpu_fixture(stock, kind, i), kind)
            b = lookup_execute(cpu_fixture(raw, kind, i), kind)
            if (a.r, a.pc, a.pr, a.sr, a.mach, a.macl) != (b.r, b.pc, b.pr, b.sr, b.mach, b.macl):
                raise AssertionError('Expanded overlay changed lookup behavior')
    result['actual_boundary_cases'] = 12
    result['prior_full_concrete_domain_report'] = '../lookup_validation/20260925T221333.336500Z/lookup_differential.json'
    result['unchanged_helper_hash'] = manifest['overlay_fragments'][5]['sha256']
    result['dependency_argument'] = 'New diagnostic code lies entirely in reconstructed original setter-table span; lookup helper/index/dictionary unchanged. Algebra rechecks every getter/setter u16 index against complete m06_04 ROM.'
    return result


def main():
    output_dir = OUT / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output_dir.mkdir(parents=True, exist_ok=False)
    log = io.StringIO()
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / 'tests'), pattern='test_m06*.py')
    suite.addTests(loader.discover(str(ROOT / 'tests'), pattern='test_sim.py'))
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (output_dir / 'tests.log').write_text(log.getvalue(), encoding='utf-8')
    if not result.wasSuccessful():
        raise AssertionError(f'Regression failed: {output_dir}')
    from test_m06_runtime import COUNTS
    from test_m06_division import COUNTS as DIVISION_COUNTS
    closure = Closure().report()
    fixtures = callback_fixtures()
    extended = lookup_extension()
    reports = dict(compiled_closure=closure, compiled_callback_fixtures=fixtures, expanded_lookup_algebra=extended)
    for name, report in reports.items():
        (output_dir / f'{name}.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    summary = dict(status='PASS', build=str(BUILD), tests=result.testsRun, scenario_counts=COUNTS,
                   division_regressions=DIVISION_COUNTS,
                   core_forms=len(OPCODES), payload_sha256=fixtures['payload_sha256'], raw_ROM_sha256=fixtures['ROM_sha256'],
                   gates=dict(compiled_CFG_frames='PASS', preserved_live_state='PASS', independent_page_reason_tests='PASS',
                              nested_leaf_with_private_outputs='PASS', no_periodic_task9_hook='PASS',
                              whole_firmware_exclusive_ROM_ownership='FAIL',
                              OEM_transport_serialization='FAIL', physical_timing='PHYSICAL/BENCH REQUIRED'),
                   bounds={name: dict(peak_stack_bytes=f['peak_stack_bytes'], hook_instruction_upper=f['instruction_upper'],
                                     memory_access_upper=f['memory_access_upper']) for name, f in closure['functions'].items()},
                   entry_trampoline_instructions=3,
                   limitations=['Rejected ordinary SSM requests still incur adapter check overhead; zero background hook is a distinct claim.',
                     'Reentry test covers leaf with private output and register contexts; shared OEM TX/request ownership is separate.',
                     'Frame sizes and instruction bounds exclude OEM caller/ISR stack, bus wait and interrupt interference.',
                     'Fixture SSM framing is host generated around actual compiled payload; root owns actual OEM framing validation.'],
                   source_hashes={name: sha256((ROOT / name).read_bytes()).hexdigest() for name in
                       ('sh2e.py', 'm06_value_analysis.py', 'm06_runtime.py', 'm06_runtime_run.py',
                        'tests/test_m06_analysis.py', 'tests/test_m06_lookup.py', 'tests/test_m06_runtime.py', 'tests/test_m06_division.py')})
    (output_dir / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(dict(status='PASS', tests=result.testsRun, scenario_counts=COUNTS, directory=str(output_dir))))


if __name__ == '__main__':
    main()
