"""Execute actual OEM and compiled compact-table lookup for every u16 index.

Stops after the original handler JSR delay slot, before executing any selected
handler. Thus even out-of-range values that select invalid pointers are compared
without pretending those handlers safely execute.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

from sh2e import CPU, Memory, ROM, STOCK_SHA256, RAM_START, OPCODES
from m06_value_analysis import Analysis, State, V

ROOT = Path(__file__).parent
ART = Path('C:/Dev/Astra_A2WC511R/reports/local/m06_architecture/rom_reclamation')
OUT = Path('C:/Dev/Astra_A2WC511R/reports/local/m06_architecture/lookup_validation')
SP = 0xFFFFBFA0
GETTER_INPUT = 0xFFFF5000
LAST_REPORT = None


def artifacts():
    path = ART / 'lookup_overlay_manifest.json'
    manifest = json.loads(path.read_text())
    stock = ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin', STOCK_SHA256)
    for name, expected in manifest['artifacts'].items():
        if sha256((ART / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f'Artifact changed: {name}')
    patched = stock
    for fragment in manifest['overlay_fragments']:
        a = fragment['address']
        before, after = bytes.fromhex(fragment['expected_before_hex']), bytes.fromhex(fragment['after_hex'])
        if len(before) != len(after) or stock.data[a:a + len(before)] != before:
            raise AssertionError(f'Overlay before-byte mismatch: {fragment["name"]}')
        if sha256(after).hexdigest() != fragment['sha256']:
            raise AssertionError(f'Overlay hash mismatch: {fragment["name"]}')
        patched = patched.with_overlay(a, after, fragment['name'])
    return stock, patched, manifest


def cpu_fixture(rom, kind, index):
    m = Memory(rom)
    m.initialize(GETTER_INPUT, bytes.fromhex('A55A'))
    m.initialize(SP - 20, bytes.fromhex('DEADC0DE') + b'\xC7' * 16)
    m.initialize(SP, bytes.fromhex('FEEDFACE'))
    m.write_allowlist = [(SP - 16, SP)]
    m.watch(SP - 20, SP + 4, 'transient stack and outer sentinels')
    m.watch(0x4F310, 0x4F950, 'original setter table span')
    entry = 0x48988 if kind == 'getter' else 0x48A30
    ranges = [(entry, entry + 12), (0x4F4E8, 0x4F532)]
    cpu = CPU(m, ranges, (SP - 16, SP))
    cpu.r = [((i + 1) * 0x9E3779B9 ^ (index * 0x01010101)) & 0xFFFFFFFF for i in range(16)]
    cpu.r[3], cpu.r[15] = GETTER_INPUT, SP
    cpu.r[2 if kind == 'getter' else 1] = index | (0xA55A << 16)
    cpu.pc, cpu.pr = entry, 0x13572468
    sr = (index * 0x01010101 ^ 0x0ACE0356) & 0x0FFF0FFF
    cpu.sr_other, cpu.t = sr & ~1, sr & 1
    cpu.mach, cpu.macl = index ^ 0xDEADBEEF, index ^ 0xFEDCBA98
    cpu.call_context = [f'{entry:08X}']
    cpu.track_control_sources = False
    return cpu


def execute(cpu, kind):
    original_jsr = 0x48990 if kind == 'getter' else 0x48A38
    while len(cpu.trace) < 100:
        pc, slot = cpu.pc, cpu.pending
        cpu.step()
        if pc == original_jsr + 2 and slot is not None:
            return cpu
    raise AssertionError('Lookup failed to reach original handler call boundary')


def algebra(stock, patched):
    index = patched.data[0x4F310:0x4F4A0]
    targets = [int.from_bytes(patched.data[a:a + 4], 'big') for a in range(0x4F4A0, 0x4F4E8, 4)]
    if len(index) != 400 or len(targets) != 18 or max(index) >= len(targets):
        raise AssertionError('Invalid compact table dimensions')
    for i in range(400):
        old = int.from_bytes(stock.data[0x4F310 + 4 * i:0x4F314 + 4 * i], 'big')
        if targets[index[i]] != old:
            raise AssertionError(f'Compact entry mismatch {i}')
    counts = {}
    for name, base in [('getter', 0x4ECD0), ('setter', 0x4F310)]:
        compact = fallback = 0
        for i in range(65536):
            address = base + 4 * i
            expected = int.from_bytes(stock.data[address:address + 4], 'big')
            if 0x4F310 <= address < 0x4F950:
                value = targets[index[(address - 0x4F310) // 4]]
                compact += 1
            else:
                value = int.from_bytes(patched.data[address:address + 4], 'big')
                fallback += 1
            if expected != value:
                raise AssertionError((name, i, address, expected, value))
        counts[name] = dict(indices=65536, translated=compact, unchanged_fallback=fallback,
                            translated_index_interval=[400, 800] if name == 'getter' else [0, 400],
                            effective_address_interval=[base, base + 4 * 65535 + 4])
    return dict(status='PASS', cases=131072, domains=counts,
                theorem='For unsigned16 i, a=B+4*i is aligned and does not overflow32 bits. Exactly the setter interval is reconstructed from the validated400-element dictionary mapping; every other word remains byte-identical under these six overlays.')


def abstract_case(cpu, kind):
    memory = cpu.memory
    fixture = {GETTER_INPUT: bytes.fromhex('A55A'), SP - 20: bytes.fromhex('DEADC0DE') + b'\xC7' * 16,
               SP: bytes.fromhex('FEEDFACE')}
    state = State.fixture(dict(enumerate(cpu.r)), fixture, pr=cpu.pr, sr=cpu.sr, mach=cpu.mach, macl=cpu.macl)
    # Stop at all possible concrete handler targets after their original JSR slot.
    expected_addr = (0x4ECD0 if kind == 'getter' else 0x4F310) + 4 * (cpu.r[2 if kind == 'getter' else 1] & 0xFFFF)
    stock = ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin', STOCK_SHA256)
    target = int.from_bytes(stock.data[expected_addr:expected_addr + 4], 'big')
    analysis = Analysis(memory.rom, allowed_exits=[target], max_steps=500).run([(cpu.pc, state)])
    execute(cpu, kind)
    check = analysis.check_concrete(memory.events, cpu.branch_edges, cpu.trace)
    if check['status'] != 'PASS':
        raise AssertionError(check)
    return dict(check=check, analysis=analysis.report())


def validate(full=True):
    stock, patched, manifest = artifacts()
    algebra_report = algebra(stock, patched)
    totals = Counter()
    pcs = {'getter': set(), 'setter': set()}
    paths = Counter()
    digest = sha256()
    max_steps = 0
    selected = [0, 1, 399, 400, 401, 799, 800, 0x7FFF, 0xFFFF]
    sample_traces = []
    abstract_reports = []
    for kind in ('getter', 'setter'):
        for index in (range(65536) if full else selected):
            original = execute(cpu_fixture(stock, kind, index), kind)
            candidate = execute(cpu_fixture(patched, kind, index), kind)
            if original.r != candidate.r:
                raise AssertionError((kind, index, 'GPR mismatch', original.r, candidate.r))
            for key in ('pc', 'pr', 'sr', 'mach', 'macl'):
                if getattr(original, key) != getattr(candidate, key):
                    raise AssertionError((kind, index, key, getattr(original, key), getattr(candidate, key)))
            for address in (SP - 20, SP):
                off = address - RAM_START
                if original.memory.ram[off:off + 4] != candidate.memory.ram[off:off + 4]:
                    raise AssertionError((kind, index, 'outer stack sentinel'))
            writes = [e for e in candidate.memory.events if e['mode'] == 'w']
            if len(writes) != 4 or {int(e['address'], 16) for e in writes} != {SP - 4, SP - 8, SP - 12, SP - 16}:
                raise AssertionError((kind, index, 'unexpected RAM writes', writes))
            if any(e['mode'] == 'w' for e in original.memory.events):
                raise AssertionError('Original lookup unexpectedly wrote RAM')
            base = 0x4ECD0 if kind == 'getter' else 0x4F310
            expected = int.from_bytes(stock.data[base + index * 4:base + index * 4 + 4], 'big')
            if candidate.pc != expected or candidate.r[15] != SP:
                raise AssertionError((kind, index, 'handler target or SP'))
            pcs[kind].update(int(row['pc'], 16) for row in candidate.trace)
            translated = any(e['pc'] == '0004F516' for e in candidate.memory.events)
            paths[(kind, 'translated' if translated else 'direct')] += 1
            totals[kind] += 1
            totals['original_instructions'] += len(original.trace)
            totals['candidate_instructions'] += len(candidate.trace)
            max_steps = max(max_steps, len(candidate.trace))
            digest.update(kind.encode() + index.to_bytes(2, 'big') + b''.join(v.to_bytes(4, 'big') for v in candidate.r)
                          + candidate.pc.to_bytes(4, 'big') + candidate.sr.to_bytes(4, 'big'))
            if index in selected:
                sample_traces.append(dict(kind=kind, index=index, target=f'{candidate.pc:08X}',
                    original=original.trace, patched=candidate.trace, memory=candidate.memory.events))
            if full and index and index % 8192 == 0:
                print(json.dumps(dict(progress=kind, completed=index, total=65536)), flush=True)
        for index in selected:
            abstract_reports.append(dict(kind=kind, index=index, **abstract_case(cpu_fixture(patched, kind, index), kind)))
    return dict(status='PASS', full_u16_domain=full, payload_sha256=manifest['artifacts']['compact_lookup.EXPERIMENTAL.bin'],
                manifest_sha256=sha256((ART / 'lookup_overlay_manifest.json').read_bytes()).hexdigest(),
                stock=stock.identity(), overlay=patched.identity(), algebra=algebra_report,
                totals=dict(totals), paths={f'{kind}/{path}': count for (kind, path), count in paths.items()},
                outcome_digest=digest.hexdigest(), max_candidate_instructions=max_steps,
                transient_stack_bytes=16, persistent_RAM_bytes=0,
                executed_pcs={kind: [f'{pc:08X}' for pc in sorted(values)] for kind, values in pcs.items()},
                sample_traces=sample_traces, abstract_crosschecks=abstract_reports,
                register_proof='All16 GPR, architecturally writable SR bits, MACH, MACL, PR, SP and selected-handler PC compare at original JSR completion. No executed form accesses GBR/VBR/FPU. Four private-stack writes are the only extra RAM effects.',
                limits='Selected handlers are not executed; even invalid u16 indices preserve original pointer selection only. Reclaimed-span ownership beyond all identified lookup consumers remains separate.',
                source_hashes={name: sha256((ROOT / name).read_bytes()).hexdigest() for name in ('sh2e.py', 'm06_value_analysis.py', 'm06_lookup_differential.py')})


if __name__ == '__main__':
    import sys
    report = validate(full='--quick' not in sys.argv)
    output = OUT / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    path = output / 'lookup_differential.json'
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], full_u16_domain=report['full_u16_domain'], totals=report['totals'], path=str(path))))
