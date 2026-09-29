"""Read-only review probes against the actual root reachability implementation."""
import ast
import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, 'C:/Dev/A2WC511R_Sim')
from sh2e import ROM, Memory, CPU


def actual_functions(rom, raw):
    source = ROOT / 'rom/reachability.py'
    tree = ast.parse(source.read_text())
    funcs = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
    incoming = collections.defaultdict(set)
    for pc, row in raw.items():
        w = row['word']
        if w >> 12 in (10, 11):
            displacement = (w & 4095) - (4096 if w & 2048 else 0)
            incoming[pc + 4 + 2 * displacement].add(pc)
    namespace = dict(rom=rom, raw=raw, crefs=collections.defaultdict(set),
                     incoming=incoming, joins=set(incoming), targets=set(incoming))
    exec(compile(funcs, str(source), 'exec'), namespace)
    return namespace


def word_image(words):
    data = bytearray(b'\xFF' * 0x100000)
    for pc, word in words.items():
        data[pc:pc + 2] = word.to_bytes(2, 'big')
    return data


def review():
    # A delayed branch slot later entered normally must gain its normal fallthrough.
    words = {0: 0xA002, 2: 0x0009, 4: 0xE100, 6: 0x0009, 8: 0xAFFB, 10: 0x0009}
    data = word_image(words)
    raw = {pc: dict(word=w, defined=True, ops=[]) for pc, w in words.items()}
    namespace = actual_functions(data, raw)
    walked = namespace['walk']({0})
    cpu = CPU(Memory(ROM.synthetic(data, 'review: separate ordinary-entry and delayed-slot contexts')),
              [(0, 12)], (0xFFFFBE00, 0xFFFFBFA0))
    cpu.pc, cpu.r[15] = 0, 0xFFFFBFA0
    actual_pcs = []
    for _ in range(6):
        actual_pcs.append(cpu.pc)
        cpu.step()
    assert 4 in actual_pcs

    # A branch may enter a call below a lexically preceding pointer definition.
    words = {0: 0xA002, 2: 0x0009, 4: 0xD104, 6: 0x0009, 8: 0x410B, 10: 0x0009}
    data = word_image(words)
    data[24:28] = (0x40).to_bytes(4, 'big')
    raw = {pc: dict(word=w, defined=True, ops=[]) for pc, w in words.items()}
    namespace = actual_functions(data, raw)
    resolved = namespace['constant'](8, 1)
    cpu = CPU(Memory(ROM.synthetic(data, 'review: incoming branch bypasses pointer load')),
              [(0, 12)], (0xFFFFBE00, 0xFFFFBFA0))
    cpu.pc, cpu.r[1], cpu.r[15] = 0, 0x80, 0xFFFFBFA0
    for _ in range(4):
        cpu.step()
    assert cpu.pc == 0x80

    sources = ['rom/audit.py', 'rom/reachability.py', 'rom/definitions.py',
               'rom/immediate_propagation.py', 'rom/test_rom_routines.py',
               'rom/routine_regression.json', 'calibration/inventory_all.py',
               'calibration/compare_history.py', 'calibration/inventory.json',
               'calibration/history_comparison.json']
    report = dict(
        status='PASS', allocation_gate='FAIL', current_calibration_identity='PHYSICAL/BENCH REQUIRED',
        scope='Independent bounded review; no root scripts or frozen artifacts changed. PASS means review probes reproduced expected limitations.',
        source_hashes={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        findings=[
            dict(id='R1', classification='PASS' if 4 in walked['reached'] else 'FAIL', issue='Delay-slot execution must be distinct from ordinary entry.',
                 demonstration=dict(words={f'{p:08X}': f'{w:04X}' for p, w in
                                    {0: 0xA002, 2: 0x0009, 4: 0xE100, 6: 0x0009, 8: 0xAFFB, 10: 0x0009}.items()},
                                    actual_first_pcs=actual_pcs, walker_reached=walked['reached'], ordinary_pc_required=4),
                 impact='Reachability result is not a guaranteed overapproximation. Does not change already-open allocation decision.',
                 fix='Separate ordinary-entry visited states from delay-slot words counted as executed; visit ordinary entry even if previously counted only as a slot.'),
            dict(id='R2', classification='PASS' if resolved is None else 'FAIL', issue='Backward constant resolver must reject incoming CFG joins.',
                 demonstration=dict(reported_call_target=resolved[0] if resolved else None, actual_target=cpu.pc, skipped_load=4, call=8),
                 existing_windows_crossing_incoming_joins=['0003DFA4', '0000025A', '0007C454', '0002841E'],
                 impact='Root corrected this during review; join crossing now loses the local constant. Actual four windows use loop-held pointers and may be sound after ABI-specific proof. Any remaining IDA targets remain positive evidence, not an exhaustive target theorem.',
                 fix='Discard a backward value across incoming branch targets unless a proper predecessor meet proves equal constants; handle implicit pointer updates or discard them.'),
            dict(id='R3', classification='PASS', issue='Existing actual OEM regressions are appropriately scoped.',
                 evidence='Root added the requested completed-cal/completed-code guard fragment, stopping before the finishing FPU helper. The report now has 22 executed scenarios including this guard and the mutated exclusive-bound negative control.',
                 followup='Finishing FPU work and full reset/peripheral execution remain explicitly outside coverage.'),
            dict(id='R4', classification='PASS', issue='Whole-hole scans and loaded-definition extents do not prove exclusive allocation.',
                 evidence='Byte-unaligned 32-bit scan, even-word PC-relative/direct-transfer scan, loaded table extents, and immediate construction searches identify positive evidence only. Unknown computed pointers, indirect dispatch, data accesses and undocumented definitions remain.'),
            dict(id='R5', classification='PASS', issue='Calibration inventory correctly leaves current ECU identity unknown.',
                 evidence='73 candidates/17 hashes in inspected inventory; one historical image matches all 16 logged CRC pages. CRC/log/date equality is not fresh cryptographic ECU identity.',
                 limitation='Inventory explicitly records absent roots and one access-denied temporary folder. Generic classification from path is a discovery hint, not an ECU identity claim.')])
    return report


if __name__ == '__main__':
    result = review()
    path = Path(__file__).with_suffix('.json')
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], path=str(path), findings=len(result['findings']))))
