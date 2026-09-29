"""Independent full OEM4828C return-boundary checks for M0.7 protocol payloads."""
from hashlib import sha256
from pathlib import Path
import json
import random

from sh2e import ROM, Memory, FunctionHarness, STOCK_SHA256, RAM_START
from m07_semantic import artifacts as semantic_artifacts

PROJECT = Path('C:/Dev/Astra_A2WC511R')
OUT = PROJECT / 'reports/local/m07_residency/semantic'


def dispatcher(rom, request, flags=0xFF, error=0xFF, sr=0x0ACE03F1):
    memory = Memory(rom)
    memory.initialize(0xFFFF63E0, b'\xA5' * 0xDC)
    memory.initialize(0xFFFF6408, bytes(request) + b'\x00' * (0x8A - len(request)))
    memory.initialize(0xFFFF649A, bytes([flags, error]))
    memory.watch(0xFFFF63E0, 0xFFFF64BC, 'OEM SSM objects')
    harness = FunctionHarness(memory, [(0x4828C, 0x484D4), (0x4260, 0x430A), (0x14770, 0x147AC)])
    harness.cpu.track_control_sources = False
    harness.run(0x4828C, allowed_writes=[(0xFFFF63E0, 0xFFFF6408), (0xFFFF649A, 0xFFFF649C)],
                system_registers={'sr': sr}, max_steps=600)
    return harness.cpu


def full_unmatched_equal(old, new):
    for key in ('r', 'sr', 'pc', 'pr', 'mach', 'macl'):
        assert getattr(old, key) == getattr(new, key), key
    # Dispatcher already owns28 bytes, adapter adds8. Keep original slots identical.
    stack_extra = (0xFFFFBFA0 - 36, 0xFFFFBFA0 - 28)
    a, b = (v - RAM_START for v in stack_extra)
    assert old.memory.ram[:a] == new.memory.ram[:a]
    assert old.memory.ram[b:] == new.memory.ram[b:]
    def writes(cpu):
        return [(e['address'], e['size'], e['value']) for e in cpu.memory.events
                if e['mode'] == 'w' and not stack_extra[0] <= int(e['address'], 16) < stack_extra[1]]
    assert writes(old) == writes(new)


def one_page_artifacts():
    directory = PROJECT / 'reports/local/m07_residency/protocol/one_page_01'
    manifest = json.loads((directory / 'manifest.json').read_text())
    stock, patched, _ = semantic_artifacts()
    blob = (directory / 'payload.bin').read_bytes()
    assert sha256(blob).hexdigest() == manifest['artifacts']['payload.bin']
    patched = patched.with_overlay(manifest['VMA'], blob, 'M07 prototype one-page protocol')
    hook = bytes.fromhex('D201422B00090009') + manifest['VMA'].to_bytes(4, 'big')
    patched = patched.with_overlay(0x484B0, hook, 'M07 default adapter entry')
    return stock, patched, manifest


def main():
    # Kept as a reusable API until the parent's two-page payload is frozen.
    stock, patched, manifest = one_page_artifacts()
    request = bytes.fromhex(manifest['request_without_checksum_hex'])
    accepted = dispatcher(patched, request)
    assert accepted.memory.ram[0x6401] == 0xFC and accepted.memory.ram[0x6405] == 7
    assert accepted.memory.ram[0x63FF] == 11
    assert accepted.memory.ram[0x649B] & 1 == 0
    assert accepted.memory.ram[0x649A] & 0x90 == 0x10
    assert accepted.sr & 1 == 0
    count = 0
    for index in range(len(request)):
        for value in (0, 1, 0x7F, 0x80, 0xFE, 0xFF):
            if value == request[index]:
                continue
            changed = bytearray(request)
            changed[index] = value
            # Known OEM commands use other handlers and belong to the parent's wire suite.
            if changed[4] in (0xA0, 0xA8, 0xB0, 0xB8, 0xBF, 0x9F):
                continue
            a, b = dispatcher(stock, changed), dispatcher(patched, changed)
            full_unmatched_equal(a, b)
            count += 1
    result = dict(status='PASS', scope='Prototype one-page only; full4828C return boundary, pending final two-page artifact.',
        rejected_pairs=count, accepted_cases=1, dispatcher_frame_bytes=28, extra_adapter_frame_bytes=8,
        maximum_observed_frame_bytes=36, initial_T_requirement='GuaranteedT=0 at OEM default484B0 from finalCMP/EQ9F false and48314BRA.',
        PR_contract='Dispatcher savesPR at4829A and restores it at484C4; the adapter may useJSR internally ifSPbalanced and no earlierPR use occurs.',
        original_SR_other_preserved=True, root_manifest_sha256=sha256((PROJECT / 'reports/local/m07_residency/protocol/one_page_01/manifest.json').read_bytes()).hexdigest(),
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / 'one_page_dispatch_abi.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
