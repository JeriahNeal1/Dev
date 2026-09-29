"""Read-only static target domains for0042 andDE3E; no execution scenarios."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

PROJECT = Path('C:/Dev/Astra_A2WC511R')
OUT = PROJECT / 'reports/local/m07_residency/semantic'
ROM_PATH = Path('C:/Dev/SubaruRoms/OEM/A2WC511R.bin')
raw = ROM_PATH.read_bytes()


def word(pc):
    return int.from_bytes(raw[pc:pc + 2], 'big')


def writes(w):
    """Only GPR effects needed by the recorded local argument slices; opaque=>all."""
    n, m, low, top = w >> 8 & 15, w >> 4 & 15, w & 15, w >> 12
    if top in (0xE, 7, 9, 0xD, 5):
        return {n}
    if top == 6:
        return {n, m} if low in (4, 6) else {n}
    if top == 1:
        return set()
    if top == 2:
        return {n} if low in (6, 9, 0xB) else set() if low in (0, 1, 2, 7, 8) else set(range(16))
    if top == 3:
        return set() if low in (0, 2, 3, 6, 7) else {n}
    if top == 0xF and low in (0, 1, 2, 3, 4, 5, 8, 0xA, 0xC):
        # These actual caller instructions are FPU arithmetic/comparison, register
        # transfers, or nonincrementing FMOV. They do not change integer registers.
        return set()
    if w & 0xFF00 in (0x8400, 0xC900, 0xCB00):
        return {0}
    if w & 0xFF00 in (0x8000, 0x8800, 0xC800):
        return set()
    if w & 0xF0FF in (0x4022, 0x4026):
        return {n}
    if w & 0xF0FF == 0x0029:
        return {n}
    if w == 0x0009:
        return set()
    return set(range(16))


def resolve(reg, before, call, remaining=64):
    """Find a local constant definition, failing at branches/calls/opaque writes."""
    for pc in range(before - 2, max(-1, before - remaining - 2), -2):
        w = word(pc)
        if pc == call:
            continue  # Transfer has not executed when its delay-slot arguments form.
        if w >> 12 in (0xA, 0xB) or w & 0xFF00 in (0x8900, 0x8B00, 0x8D00, 0x8F00) or w & 0xF0FF in (0x400B, 0x402B):
            raise AssertionError(('unclosed local control boundary', hex(pc), reg))
        if reg not in writes(w):
            continue
        if w >> 12 == 0xE and w >> 8 & 15 == reg:
            value = w & 255
            return (value - 256 if value & 128 else value) & 0xFFFFFFFF, [pc]
        if w & 0xF00F == 0x6003 and w >> 8 & 15 == reg:
            value, chain = resolve(w >> 4 & 15, pc, call, remaining)
            return value, chain + [pc]
        raise AssertionError(('nonconstant local definition', hex(pc), reg, hex(w)))
    raise AssertionError(('no local constant definition', reg, before))


def main():
    pool_users, direct_edges = [], []
    for pc in range(0, len(raw) - 1, 2):
        w = word(pc)
        if w >> 12 == 0xD:
            pool = ((pc + 4) & ~3) + 4 * (w & 255)
            if pool + 4 <= len(raw) and int.from_bytes(raw[pool:pool + 4], 'big') == 0xDDF4:
                pool_users.append((pc, pool, w >> 8 & 15))
        target = None
        if w >> 12 in (0xA, 0xB):
            disp = w & 4095
            target = pc + 4 + 2 * (disp - 4096 if disp & 2048 else disp)
        elif w & 0xFF00 in (0x8900, 0x8B00, 0x8D00, 0x8F00):
            disp = w & 255
            target = pc + 4 + 2 * (disp - 256 if disp & 128 else disp)
        if target is not None:
            direct_edges.append((pc, target))
    callers = []
    for pc, pool, reg in pool_users:
        call = None
        for q in range(pc + 2, pc + 0x40, 2):
            w = word(q)
            if w in (0x400B | reg << 8, 0x402B | reg << 8):
                call = q
                break
            assert reg not in writes(w), ('target clobbered', hex(pc), hex(q))
        assert call is not None
        selector, chain4 = resolve(4, call + 4, call)
        index, chain5 = resolve(5, call + 4, call)
        selector, index = selector & 255, index & 65535
        base = int.from_bytes(raw[0x1023C + 4 * selector:0x10240 + 4 * selector], 'big')
        descriptor = base + 8 * index
        assert descriptor % 4 == 0 and descriptor + 8 <= len(raw)
        header = int.from_bytes(raw[descriptor:descriptor + 2], 'big')
        argc = int.from_bytes(raw[descriptor + 2:descriptor + 4], 'big')
        callback = int.from_bytes(raw[descriptor + 4:descriptor + 8], 'big') if header == 0xFFFF else None
        beginning = min(pc, *chain4, *chain5)
        incoming = [(a, b) for a, b in direct_edges if beginning < b <= call + 2 and not beginning <= a <= call + 2]
        callers.append(dict(load_pc=f'{pc:08X}', literal_pool=f'{pool:08X}', transfer_pc=f'{call:08X}',
            transfer='JMP' if word(call) & 255 == 0x2B else 'JSR', selector=selector, index=index,
            selector_definitions=[f'{a:08X}' for a in chain4], index_definitions=[f'{a:08X}' for a in chain5],
            local_slice_start=f'{beginning:08X}', local_slice_hex=raw[beginning:call + 4].hex(),
            descriptor=f'{descriptor:08X}', descriptor_hex=raw[descriptor:descriptor + 8].hex(),
            argument_words=argc, callback=f'{callback:08X}' if callback is not None else None,
            noncallback_path='DC3C' if callback is None else None,
            encoded_external_direct_entries_to_slice=[[f'{a:08X}', f'{b:08X}'] for a, b in incoming]))
    assert len(callers) == 33
    assert {r['callback'] for r in callers if r['callback']} == {'000129D4', '000129DA', '000129E0'}
    all_pools = [a for a in range(0, len(raw) - 3, 4) if int.from_bytes(raw[a:a + 4], 'big') == 0xDDF4]
    assert set(all_pools) == {pool for _, pool, _ in pool_users}
    # Pin the unconstrained byte assembler and exact RAM-word store/transfer chain.
    assert raw[0xB4:0xC2].hex() == 'd33b7402d23b2342d13b412b6422'
    assert raw[0x12C:0x152].hex() == '8441600c624040286303622c84424228600c4018330c42188443332c600c6433340c000b6043'
    assert raw[0x996:0x99C].hex() == 'd32e944c2302'
    assert int.from_bytes(raw[0x1004:0x1008], 'big') == 0x125C
    rtos = json.loads((PROJECT / 'reports/local/m07_residency/ownership_review/rtos_target_exclusion.json').read_text())
    assert rtos['target_words']['00004AA4'] == '00000040'
    report = dict(classification='BOUNDED_STATIC_TARGET_DOMAIN_CLOSURE_NOT_GLOBAL_OWNERSHIP',
        stock_rom_sha256=sha256(raw).hexdigest(), no_simulation_scenarios=True,
        descriptor_callback=dict(site='0000DE3E', bounded_literal_caller_contract='PASS', complete_domain='FAIL',
            raw_PC_relative_load_count=len(pool_users), all_aligned_literal_pool_count=len(all_pools), callers=callers,
            selector_index_domains={str(s): sorted({r['index'] for r in callers if r['selector'] == s}) for s in (0, 1, 2)},
            callback_targets=['000129D4', '000129DA', '000129E0'], candidate_object_intersection=[],
            residuals=['No proof that every incoming DDF4 path uses one of these ordinary local call slices.',
                       'Calculated pointers, arbitrary interior entry, RAM-built targets and unknown broad-analysis paths remain outside this literal search.',
                       'Local argument slices are conditional on entry through their recorded definitions; recorded external direct entries, if any, need separate predecessor contracts.',
                       'Immutable descriptor ROM and ordinary noncorrupt stack/arguments are assumed. Other descriptor types go toDC3C, whose transitive behavior is not analyzed here.']),
        caller_R4_trampoline=dict(site='00000042', complete_target_exclusion='FAIL',
            fixed_ROM_transition=dict(caller='000471BE', target_source='BE32(ROM[1004])', target='0000125C', target_specific_exclusion='PASS'),
            boot_transition=dict(caller='00000700', visible_target_definitions=['constant00000868', 'BE32(ROM[1000])=00001150', 'BE32(ROM[FFFF8])=0000F60C'],
                scope='Local boot target assignments only; no new whole-reset/callee/hardware theorem.'),
            boot_protocol_transition=dict(dispatch='00000900 -> handler000000B4 -> trampoline00000040',
                target_source='BE32(RAM[FFFFBFA0]) loaded in00BE JMPdelay at00C0',
                producer='00000978 handler -> byte assembler0000012C -> write0000099A toFFFFBFA0',
                formula='(u8(b0)<<24)|(u8(b1)<<16)|(u8(b2)<<8)|u8(b3)',
                range='All32-bit words from unconstrained four input bytes; aligned words include both proposed tails.',
                constraint='Observed header-length/type checks do not whitelist this assembled target address.',
                interpretation='Caller-directed boot execution is an explicit external-control boundary, not evidence that normal task firmware enters reclaimed interiors. Excluding it requires a stated operating/entry contract.'),
            RTOS_transitive_residual=dict(source='3980 source-word superset includes4AA4=00000040',
                example_index_relation='sign8(state)=40,zero8(index)=0 gives4A7C+40=4AA4',
                interpretation='Existing3980PASS excludes a direct hit only. It does not prove that a subsequent0042JMP cannot target an object; valid context invariants are required.')),
        final_gate='FAIL', exact_residual_unknowns=['Caller-directed RAM target at0042 is not bounded to ordinary function entries.',
            'All other incoming computed paths toDDF4 and0040 are not exhaustively enumerated.',
            'RTOS state/context validity, exceptions/interrupts, flash mutation and broader calculated control remain outside this static slice.'],
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / 'TARGET_DOMAIN_CLOSURE.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status='FAIL', bounded_literal_descriptor_domain='PASS', literal_callers=33,
                         descriptor_targets=report['descriptor_callback']['callback_targets'],
                         local_direct_entry_flags=sum(len(r['encoded_external_direct_entries_to_slice']) for r in callers))))


if __name__ == '__main__':
    main()
