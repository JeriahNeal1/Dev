"""Separate M0.7 conservative whole-firmware attempt; unknowns always fail."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

from m06_analysis_run import seed_manifest
from m06_value_analysis import Analysis, State
from sh2e import ROM, STOCK_SHA256, OPCODES


def main():
    root = Path(__file__).parent
    out = Path('C:/Dev/Astra_A2WC511R/reports/local/m07_residency/static_analysis') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    seeds = seed_manifest()
    seeds['dispatch_manifest_status'] = 'M07 whole-firmware dynamic entry coverage remains incomplete; diagnostic-owner paths are scoped, not exhaustive firmware roots.'
    rom = ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin', STOCK_SHA256)
    analysis = Analysis(rom, max_steps=100000, max_memory=256, widen_after=3)
    analysis.uncertain(-1, 'M07_entry_manifest_not_exhaustive', universal=True)
    analysis.uncertain(-1, 'asynchronous_interrupt_DMA_flash_effects_not_bounded', universal=True)
    analysis.run([(int(row['pc'], 16), State()) for row in seeds['seeds']])
    report = analysis.report()
    report['source_hashes'] = {name: sha256((root / name).read_bytes()).hexdigest() for name in
                             ('sh2e.py', 'm06_value_analysis.py', 'm06_analysis_run.py', 'm07_broad_analysis.py')}
    report['candidate_exclusions'] = {name: analysis.exclusion(lo, hi, 'read') for name, lo, hi in
                                      [('division_changed_object', 0x4260, 0x430A), ('division_tail', 0x42A4, 0x430A),
                                       ('range_changed_object', 0x1473C, 0x147AC), ('range_tail', 0x14770, 0x147AC)]}
    (out / 'entry_manifest.json').write_text(json.dumps(seeds, indent=2) + '\n')
    (out / 'broad_value_analysis.json').write_text(json.dumps(report, indent=2) + '\n')
    summary = dict(status='FAIL', interpretation='All unknown downstream behavior is universal; no candidate ownership is certified.',
                   seed_count=len(seeds['seeds']), steps=analysis.steps, states=len(analysis.states),
                   worklist_complete=analysis.terminated, unknown_count=len(analysis.unknowns),
                   unknown_reasons=dict(Counter(reason for _, reason in analysis.unknowns)), core_forms=len(OPCODES),
                   opaque_transfers=analysis.decoded['OPAQUE'],
                   exclusions={name: result['status'] for name, result in report['candidate_exclusions'].items()},
                   source_hashes=report['source_hashes'], report=str(out / 'broad_value_analysis.json'))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'unknown_reasons'}))


if __name__ == '__main__':
    main()
