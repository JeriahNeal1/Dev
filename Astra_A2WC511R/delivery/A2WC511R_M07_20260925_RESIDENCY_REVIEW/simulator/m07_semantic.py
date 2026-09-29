"""M0.7 compiled semantic equivalence and scoped original-object inventory.

No firmware ownership inference follows from a function-level differential pass.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import random

from sh2e import ROM, Memory, CPU, STOCK_SHA256, RAM_START, OPCODES

PROJECT = Path('C:/Dev/Astra_A2WC511R')
OUT = PROJECT / 'reports/local/m07_residency/semantic'
EXPORT = PROJECT / 'reports/local/gate_closure/ida/defined_code_export.json'
SP = 0xFFFFBFA0
RETURN = 0xFFFFFFFC


def artifacts():
    manifest = json.loads((OUT / 'candidate_manifest.json').read_text())
    stock = ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin', STOCK_SHA256)
    patched = stock
    for name, candidate in manifest['candidates'].items():
        blob = Path(candidate['binary']).read_bytes()
        start = candidate['start']
        if sha256(blob).hexdigest() != candidate['binary_sha256']:
            raise AssertionError('Compiled candidate changed')
        if stock.data[start:start + len(blob)].hex() != candidate['expected_before_hex']:
            raise AssertionError('Original expected bytes changed')
        patched = patched.with_overlay(start, blob, 'M07 experimental semantic replacement ' + name)
    return stock, patched, manifest


def fixture(rom, entry, registers=None, ram=None, sr=0x0ACE03F1):
    memory = Memory(rom)
    memory.initialize(SP - 32, b'\xA5' * 48)
    for address, value in (ram or {}).items():
        memory.initialize(address, value)
    memory.watch(SP - 32, SP + 16, 'private stack including sentinels')
    for start, end, label in ((0x4260, 0x430A, 'division object'), (0x1466E, 0x147AC, 'range object')):
        memory.watch(start, end, label, modes='rw')
    memory.write_allowlist = [(SP - 12, SP), (0xFFFF130C, 0xFFFF1310), (0xFFFF4BA4, 0xFFFF4BA5), (0xFFFF4BC0, 0xFFFF4BC1)]
    cpu = CPU(memory, [(0x4260, 0x430A), (0x1466E, 0x147AC)], (SP - 16, SP))
    cpu.r = [((i + 1) * 0x1234567) & 0xFFFFFFFF for i in range(16)]
    for reg, value in (registers or {}).items():
        cpu.r[reg] = value & 0xFFFFFFFF
    cpu.r[15] = SP
    cpu.pc, cpu.pr, cpu.mach, cpu.macl = entry, RETURN, 0x89ABCDEF, 0x13579BDF
    cpu._set_system('sr', sr, {'fixture:SR'})
    cpu.call_context = [f'{entry:08X}']
    cpu.track_control_sources = False
    return cpu


def execute(cpu):
    for _ in range(400):
        cpu.step()
        if cpu.returned:
            if cpu.pc != RETURN or cpu.pending or cpu.r[15] != SP:
                raise AssertionError('Invalid return boundary')
            return cpu
    raise AssertionError('Bounded semantic candidate exceeded400 instructions')


def compare(original, candidate, extra_stack=False):
    for key in ('r', 'sr', 'pr', 'pc', 'mach', 'macl'):
        if getattr(original, key) != getattr(candidate, key):
            raise AssertionError(('architectural_state', key, getattr(original, key), getattr(candidate, key)))
    lo, hi = SP - 12 - RAM_START, SP - 8 - RAM_START
    old, new = original.memory.ram, candidate.memory.ram
    if (old[:lo] != new[:lo] or old[hi:] != new[hi:]) if extra_stack else old != new:
        raise AssertionError('RAM changed outside explicit additional private stack slot')
    def visible_events(cpu):
        rows = []
        for event in cpu.memory.events:
            address = int(event['address'], 16)
            if address < RAM_START:
                continue  # Instruction/literal addresses differ by design; report separately.
            if extra_stack and SP - 12 <= address < SP - 8:
                continue
            rows.append((event['mode'], event['address'], event['size'], event['value']))
        return rows
    if visible_events(original) != visible_events(candidate):
        raise AssertionError('Ordered RAM/MMIO access trace changed')
    calls = lambda cpu: [e for e in cpu.trace if e['instruction'] in ('jsr', 'bsr')]
    if calls(original) != calls(candidate):
        raise AssertionError('Called-function trace changed')


def object_inventory(stock, manifest):
    db = json.loads(EXPORT.read_text())
    rows = {}
    for name, candidate in manifest['candidates'].items():
        entry = 0x4260 if name == 'division' else 0x1466E
        start, end = candidate['start'], candidate['original_end_exclusive']
        tail = candidate['replacement_end_exclusive']
        inbound = [x for x in db['xrefs'] if start <= x['to'] < end and not entry <= x['from'] < end]
        pointers = []
        for a in range(len(stock.data) - 3):
            value = int.from_bytes(stock.data[a:a + 4], 'big')
            if start <= value < end:
                pointers.append(dict(address=a, value=value, aligned=a % 4 == 0, into_reclaimed_tail=tail <= value))
        direct = []
        reads = []
        for ins in db['code']:
            pc, word = ins['ea'], ins['word']
            target = None
            if word >> 12 in (10, 11):
                disp = word & 4095
                target = pc + 4 + 2 * (disp - 4096 if disp & 2048 else disp)
            elif word & 0xFF00 in (0x8900, 0x8B00, 0x8D00, 0x8F00):
                disp = word & 255
                target = pc + 4 + 2 * (disp - 256 if disp & 128 else disp)
            if target is not None and start <= target < end and not entry <= pc < end:
                direct.append(dict(pc=pc, target=target, instruction=ins['text']))
            if word >> 12 in (9, 13):
                width = 2 if word >> 12 == 9 else 4
                address = pc + 4 + 2 * (word & 255) if width == 2 else ((pc + 4) & ~3) + 4 * (word & 255)
                if address < end and start < address + width:
                    reads.append(dict(pc=pc, address=address, size=width, instruction=ins['text']))
        chunks = [f for f in db['functions'] if any(a < end and start < b for a, b in f['chunks'])]
        # Every supplied defined instruction is cross-checked with immutable baseline.
        mismatch = [x['ea'] for x in db['code'] if entry <= x['ea'] < end and x['word'] != int.from_bytes(stock.data[x['ea']:x['ea'] + 2], 'big')]
        rows[name] = dict(original_entry=entry, changed_object=[start, end], proposed_tail=[tail, end],
            exported_function_chunks=chunks, outside_exported_xrefs=inbound, outside_defined_direct_branches=direct,
            all_byte_offsets_big_endian_pointer_matches=pointers, defined_PC_relative_reads=reads,
            stock_defined_instruction_mismatches=mismatch, ownership_gate='FAIL',
            limits=['Defined-code export is incomplete executable-entry coverage.',
                    'Computed pointers, generic diagnostic ROM readers, exception contexts and opaque instructions are not excluded by these scans.',
                    'The proposed tail is original live code until replacement and object ownership are separately established.',
                    'A direct interior entry would invalidate the function-entry-only semantic proof.'])
    return dict(stock_sha256=stock.sha256, IDA_export_path=str(EXPORT), IDA_export_sha256=sha256(EXPORT.read_bytes()).hexdigest(),
                IDA_export_ROM_sha256=db['rom_sha256'], baseline_difference_note='IDA stamp variant; all defined candidate words explicitly verified against baseline.', objects=rows)


def validate():
    stock, patched, manifest = artifacts()
    rng = random.Random(0xA207)
    counts = Counter()
    max_steps, max_stack = {}, {}
    digest = sha256()
    samples = []
    values = [0, 1, -1, 2, -2, 3, -3, 0x7FFFFFFF, -0x80000000, 65535, -65535]
    pairs = [(a, b) for a in values for b in values]
    pairs += [(a, 3) for a in range(-2, 254)]
    pairs += [(rng.randrange(-0x80000000, 0x80000000), rng.randrange(-0x80000000, 0x80000000)) for _ in range(1024)]
    for dividend, divisor in pairs:
        regs = {0: divisor, 1: dividend, 2: rng.getrandbits(32), 3: rng.getrandbits(32), 4: rng.getrandbits(32)}
        sr = rng.getrandbits(32) & 0x0FFF0FFF
        old = execute(fixture(stock, 0x4260, regs, sr=sr))
        new = execute(fixture(patched, 0x4260, regs, sr=sr))
        compare(old, new, extra_stack=True)
        counts['division_pairs'] += 1
        max_steps['division_original'] = max(max_steps.get('division_original', 0), len(old.trace))
        max_steps['division_replacement'] = max(max_steps.get('division_replacement', 0), len(new.trace))
        max_stack['division_original'] = max(max_stack.get('division_original', 0), SP - min(old.r[15], *(int(e['address'], 16) for e in old.memory.events if e['mode'] == 'w' and int(e['address'], 16) >= SP - 32)))
        max_stack['division_replacement'] = max(max_stack.get('division_replacement', 0), SP - min(new.r[15], *(int(e['address'], 16) for e in new.memory.events if e['mode'] == 'w' and int(e['address'], 16) >= SP - 32)))
        digest.update(json.dumps([dividend, divisor, new.r, new.sr]).encode())
        if len(samples) < 3:
            samples.append(dict(kind='division', dividend=dividend, divisor=divisor, original_trace=old.trace, replacement_trace=new.trace,
                                original_accesses=old.memory.events, replacement_accesses=new.memory.events))
    for raw in range(256):
        for prior in (0, 1, 0x55, 0x7F, 0x80, 0xAA, 0xFF):
            ram = {0xFFFF4C8C: bytes([raw]), 0xFFFF4BA4: bytes([prior]), 0xFFFF4BC0: b'\xA5'}
            sr = rng.getrandbits(32) & 0x0FFF0FFF
            old = execute(fixture(stock, 0x1466E, ram=ram, sr=sr))
            new = execute(fixture(patched, 0x1466E, ram=ram, sr=sr))
            compare(old, new)
            counts['range_function_pairs'] += 1
            max_steps['range_original'] = max(max_steps.get('range_original', 0), len(old.trace))
            max_steps['range_replacement'] = max(max_steps.get('range_replacement', 0), len(new.trace))
            digest.update(json.dumps([raw, prior, new.r, new.sr]).encode())
    # Concrete counterexample: arbitrary interior-entry state violates the tail precondition.
    old = execute(fixture(stock, 0x1473A, {5: 7, 6: 0x12345678}, {0xFFFF4BC0: b'\x00'}))
    new = execute(fixture(patched, 0x1473A, {5: 7, 6: 0x12345678}, {0xFFFF4BC0: b'\x00'}))
    try:
        compare(old, new)
    except AssertionError:
        counts['interior_entry_negative_control_detected'] = 1
    else:
        raise AssertionError('Invalid interior-entry assumption escaped negative control')
    return dict(status='PASS', classification='SCOPED_FUNCTION_EQUIVALENCE_ONLY', counts=counts, max_executed_instructions=max_steps,
                stack_bytes=max_stack, output_digest=digest.hexdigest(), stock_sha256=stock.sha256, overlay_sha256=patched.sha256,
                gates=dict(function_differential='PASS', complete_original_object_ownership='FAIL', timing_and_stack_margin='PHYSICAL/BENCH REQUIRED'),
                compared='All16 GPRs,SR,PR,MACH,MACL,returnPC,SP; final RAM and ordered RAM/MMIO accesses except one explicit additional division private stack slot. No function calls in either object.',
                FPU='No supported or decoded candidate instruction touches FPU; no floating execution simulated.',
                extra_private_stack='Division only:[initialSP-12,initialSP-8),4bytes, one saved/restoredR4; originalR2/R3stackaccesses unchanged. This is additional memory traffic, not byte-identical whole-RAM execution.',
                samples=samples)


def main():
    stock, _, manifest = artifacts()
    inventory = object_inventory(stock, manifest)
    (OUT / 'object_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    result = validate()
    result['created_utc'] = datetime.now(timezone.utc).isoformat()
    result['source_hashes'] = {name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                               for name in ('sh2e.py', 'm07_semantic.py', 'm07_semantic_build.py')}
    (OUT / 'semantic_differential.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'samples'}))


if __name__ == '__main__':
    main()
