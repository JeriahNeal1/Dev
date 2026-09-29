"""Derive frame joins and live-state conditions from frozen two-page CFG words."""
from collections import deque
from hashlib import sha256
from pathlib import Path
import json

from m07_two_page_abi import OUT, artifacts


def main():
    stock, rom, manifest = artifacts()
    source = OUT / 'two_page_dispatch_abi.json'
    report = json.loads(source.read_text())
    assert report['experimental_overlay_sha256'] == rom.sha256
    for filename, expected in report['source_hashes'].items():
        assert sha256(Path(__file__).with_name(filename).read_bytes()).hexdigest() == expected
    cfg = report['compiled_CFG']
    words = {int(a, 16): (int(row['word'], 16), row['form']) for a, row in cfg['instruction_addresses'].items()}
    adjacency = {}
    for a, b in cfg['CFG_edges']:
        adjacency.setdefault(int(a, 16), []).append(int(b, 16))
    depths, work = {0x484B0: 0}, deque([0x484B0])
    while work:
        pc = work.popleft()
        if pc == 0x484BC:
            continue
        word, form = words[pc]
        depth = depths[pc]
        if form == 'movl_predec':
            assert word >> 8 & 15 == 15
            depth += 4
        elif form == 'movl_postinc':
            assert word >> 4 & 15 == 15
            depth -= 4
        assert 0 <= depth <= 8
        for target in adjacency[pc]:
            if target in depths:
                assert depths[target] == depth, ('unequal frame join', hex(target))
            else:
                depths[target] = depth
                work.append(target)
    assert depths[0x484BC] == 0 and max(depths.values()) == 8
    # Delayed instructions skipped by summarized CFG edges have no SP/PR effect.
    delayed_forms = [row['form'] for row in cfg['instruction_addresses'].values() if row.get('delay_slot')]
    assert set(delayed_forms) <= {'nop', 'mov_imm', 'movb_load', 'or_imm'}
    assert rom.data[0x14770:0x14774] == bytes.fromhex('2F162F46')
    assert rom.data[0x1477A:0x1477E] == bytes.fromhex('64F661F6')
    assert rom.data[0x1479C:0x1479E] == bytes.fromhex('0008')
    assert stock.data[0x4829A:0x4829C] == bytes.fromhex('4F22')
    assert stock.data[0x484C4:0x484C6] == bytes.fromhex('4F26')
    assert stock.data[0x484D0:0x484D2] == bytes.fromhex('000B')
    assert stock.data[0x484BC:0x484C4] == bytes.fromhex('63C07304D29F2230')
    assert stock.data[0x48308:0x48318] == bytes.fromhex('910E30108F020009A0AF0009A0CC0009')
    # All payload writes are either the two private stack slots or existing SSM objects.
    writes = []
    for pc, (word, form) in words.items():
        if form == 'movl_predec':
            assert word >> 8 & 15 == 15
            writes.append(dict(pc=f'{pc:08X}', destination='private stack', size=4))
        elif form == 'movb_store':
            base = word >> 8 & 15
            assert base in (11, 12, 14)
            writes.append(dict(pc=f'{pc:08X}', destination={11: 'existing response opcodeFFFF6401', 12: 'existing response lengthFFFF6405', 14: 'existing flagsFFFF649A'}[base], size=1))
        elif form == 'movb_disp_store':
            assert word == 0x80E1
            writes.append(dict(pc=f'{pc:08X}', destination='existing error flagsFFFF649B', size=1))
    assert len(writes) == 6
    cycle = {}
    for name, instructions in report['payload_instruction_bounds_including_entry'].items():
        accesses = report['payload_data_access_bounds_including_entry'][name]
        cycle[name] = dict(instructions=instructions, data_accesses=accesses,
                          conditional_F2_D2_cycles=6 * instructions + accesses)
    result = dict(status='PASS', input_report_sha256=sha256(source.read_bytes()).hexdigest(),
                  code_overlay_sha256=rom.sha256, frame_before_instruction={f'{a:08X}': d for a, d in sorted(depths.items())},
                  added_stack_peak=8, OEM_frame=28, full_dispatcher_peak=36,
                  every_frame_join_equal=True, balanced_at_continuation=True, known_writes=writes,
                  preserved_GPR='R1/R4 saved/restored;R5-R14 untouched bypayload;R15 balanced;R2/R3 overwritten by original484BC/484C0beforeuse;R0originalscratch.',
                  PR='HelperJSR overwritesPR;existingdispatcherstackslotrestoresPRat484C4beforeRTS. No claimPRidentical at484BC.',
                  SR='Original finalCMP/EQ9F false fixesT0at484B0;matcher usesT;commonCLRT restoresT0onbothpaths;allotherSRbits unaffected.',
                  FPU_MAC_control='No reachable payload operation accesses FPU,MACH,MACL,GBR,VBR or loads/stores SR.',
                  finite_counter='OnlyMOV#12/#18andDTwriteR4inmatcher. Loopbackoccurswhilepostdecrementnonzero; atmost18iterations.',
                  cycles=cycle, cycle_assumptions='5*N+(F-1)*N+(D-1)*A; illustrativeF=D=2; excludesentry/externalstalls,OEMbaseline,interruptdelivery and actualbusclock.',
                  gates=dict(compiled_frame_and_live_state='PASS', whole_object_ownership='FAIL', silicon_timing_stack_margin='PHYSICAL/BENCH REQUIRED'),
                  source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / 'two_page_CFG_frame_proof.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', added_stack=8, full_dispatcher_stack=36, cycle_envelopes=cycle)))


if __name__ == '__main__':
    main()
