"""Exact-image, read-only audit of discovered RAM/reset/DMA/task paths.

This is a typed extraction and arithmetic regression, not a whole-ROM proof.
Actual instruction execution belongs to the independent simulator regression.
Only report/disassembly files beside this script are written.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess

ROOT = Path(r'C:\Dev\Astra_A2WC511R')
OUT = Path(__file__).resolve().parent
ROM = Path(r'C:\Dev\SubaruRoms\OEM\A2WC511R.bin')
OBJDUMP = Path(r'C:\Program Files (x86)\Renesas\Hew\Tools\KPIT\GNUSH-ELF\v13.01\sh-elf\bin\sh-elf-objdump.exe')
BASELINE = '22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218'
PAYLOAD = 'b5004baa2863bf571eb1ab014f93f0316b3500c5b154e47de2e42f904234b2ff'
MANUAL = 'https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual'
CANDIDATE = (0xffff7400, 0xffff7420)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def overlaps(a, b):
    return max(a[0], b[0]) < min(a[1], b[1])


def u16(r, a):
    return int.from_bytes(r[a:a+2], 'big')


def u32(r, a):
    return int.from_bytes(r[a:a+4], 'big')


def pc_literal(r, ea):
    word = u16(r, ea)
    if word >> 12 == 13:
        pool = ((ea + 4) & ~3) + (word & 255) * 4
        val = u32(r, pool)
    elif word >> 12 == 9:
        pool = ea + 4 + (word & 255) * 2
        val = u16(r, pool)
        if val & 0x8000:
            val |= 0xffff0000
    else:
        raise AssertionError(f'not literal load: {ea:x} {word:04x}')
    return dict(ea=ea, word=word, pool=pool, value=val, reg=(word >> 8) & 15)


def references(r, value):
    pools = [a for a in range(len(r)-3) if u32(r, a) == value]
    pool_set = set(pools)
    loads = []
    branches = []
    for ea in range(0, len(r)-3, 2):
        w = u16(r, ea)
        if w >> 12 == 13 and ((ea+4) & ~3) + (w & 255)*4 in pool_set:
            loads.append(ea)
        if w >> 12 in (10, 11):
            target = (ea+4 + (((w & 4095) ^ 2048)-2048)*2) & 0xffffffff
            if target == value:
                branches.append(dict(ea=ea, word=w, kind='bsr' if w >> 12 == 11 else 'bra'))
    return dict(value=value, literal32_pools_all_alignments=pools, pc_relative_loads=loads, relative_branches=branches)


def channel(chcr):
    return dict(value=chcr, request_source=(chcr >> 16) & 31,
                source_mode=(chcr >> 12) & 3, destination_mode=(chcr >> 8) & 3,
                transfer_size_code=(chcr >> 4) & 3, burst=bool(chcr & 8),
                interrupt_enabled=bool(chcr & 4), end=bool(chcr & 2), enabled=bool(chcr & 1))


def memcpy_dispatch_contract(r):
    """Only valid, aligned longword table loads can reach the jump at43E8."""
    expected = {0x43de: 0xe340, 0x43e0: 0x3302, 0x43e2: 0x8b4b,
                0x43e4: 0xd301, 0x43e6: 0x033e, 0x43e8: 0x432b, 0x43ea: 0x0009}
    assert all(u16(r, a) == w for a, w in expected.items())
    assert pc_literal(r, 0x43e4)['value'] == 0x4438
    table = [u32(r, 0x4438+4*i) for i in range(17)]
    assert table == [0x4432-4*i for i in range(17)]
    assert u16(r, 0x4432) == 0x000b and u16(r, 0x4434) == 0x63f6
    # Every nonempty case performs exactly size/4 descending longword copies,
    # then joins the common return; source/destination registers are unchanged.
    for i, target in enumerate(table):
        for word_index in range(i):
            ea = target+4*word_index
            displacement = i-1-word_index
            assert u16(r, ea) == (0x5020+displacement if displacement else 0x6022)
            assert u16(r, ea+2) == (0x1100+displacement if displacement else 0x2102)
    return table


def main():
    r = ROM.read_bytes()
    assert len(r) == 0x100000 and sha(r) == BASELINE
    build = ROOT / 'work/builds/m0_final_05'
    manifest_path = build / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['ram_bytes'] == 32 and int(manifest['ram_base'], 0) == CANDIDATE[0]
    code = build / 'm0.EXPERIMENTAL_UNAPPROVED.code.bin'
    assert sha(code.read_bytes()) == PAYLOAD

    # Decode actual load addresses; no assumed literal-pool displacement.
    expected = {
        0xc31e: 0xffffecf8, 0xc322: 0xfffff00d, 0xc324: 0xffffecf0,
        0xc32c: 0xffff315a, 0xc33e: 0x40100, 0xc342: 0xffffece8,
        0xc348: 0xffff310a, 0xc360: 0xffffece0, 0xc364: 0xfffff00b,
        0xc366: 0xffffece4, 0xc372: 0x31000,
        0x45d40: 0xffff6390, 0x45d42: 0xffff6368, 0x45d44: 0xc5ca,
        0xd3ee: 0x3a28, 0xd93c: 0x1019c, 0xd944: 0xffff31f2,
        0xd958: 0xffff31f0, 0xd962: 0x10200, 0x5eaa: 0xd936,
        0xd90a: 0xfffff718, 0xd912: 2499, 0xd914: 0xfffff71c,
        0xd904: 0xfffff710, 0xd918: 0xfffff71a,
        0x3fe8: 0x4880, 0x3fea: 0xffff12b0, 0x3934: 0x48d8,
        0x51dc: 0xffffec26, 0xf9bc: 0xffffecb0,
        0x4fc: 0xffffb4e0, 0x544: 0xffffb4e0,
        0x71c9c: 0xffff736c, 0x71cb8: 0xffff736c, 0x71ce0: 0xffff736c,
    }
    loads = [pc_literal(r, ea) for ea in expected]
    assert all(x['value'] == expected[x['ea']] for x in loads)
    words = {0xc30e: 0x622c, 0xc312: 0x611c, 0xc32e: 0x600c, 0xc330: 0x4000,
             0xc34e: 0x4308, 0xc350: 0x331c, 0xc352: 0x4308, 0xc356: 0x4300,
             0xc358: 0x611c, 0xc35a: 0x4100, 0xc35c: 0x330c, 0xc35e: 0x313c,
             0x45d46: 0x430b, 0x45d48: 0xe614, 0xd3f0: 0x430b, 0xd3f2: 0xe409,
             0x3ff8: 0x1e33, 0x3964: 0x53c3, 0x3966: 0x1e31, 0x3df8: 0x14f3,
             0x3a1c: 0x6f53, 0x3f5e: 0x53d1, 0x3f62: 0x1e33, 0xd91c: 0xe302}
    words.update({0x3bcc:0x3627,0x3bce:0x8b12,0x3a68:0x2008,0x3a6a:0x891c,0x3aa6:0x4d0e,
                  0x71ca0:0x2320,0x71cc4:0x2360,0x71cde:0xe300,0x71ce2:0x000b,0x71ce4:0x2230})
    assert all(u16(r, ea) == word for ea, word in words.items())

    boot = (u32(r, 0xfff4), u32(r, 0xfff8)+1)
    assert boot == (0xffff2d00, 0xffffbffc)
    count = (boot[1]-boot[0])//4
    assert count == 0x24bf and overlaps(boot, CANDIDATE)
    # Full-byte indices deliberately overapproximate protocol-valid indices.
    rx_addresses = [0xffff315a + 2*i for i in range(256)]
    tx_addresses = [0xffff310a + 40*j + 2*i for i in range(256) for j in range(256)]
    rx_span = (min(rx_addresses), max(rx_addresses)+2)
    tx_span = (min(tx_addresses), max(tx_addresses)+2)
    assert rx_span == (0xffff315a, 0xffff335a)
    assert tx_span == (0xffff310a, 0xffff5ae2)
    assert not overlaps(rx_span, CANDIDATE) and not overlaps(tx_span, CANDIDATE)
    sync_tx = (expected[0x45d42], expected[0x45d42]+20*2)
    sync_rx = (expected[0x45d40], expected[0x45d40]+20*2)
    assert sync_tx == (0xffff6368, 0xffff6390) and sync_rx == (0xffff6390, 0xffff63b8)
    assert not overlaps(sync_rx, CANDIDATE) and not overlaps(sync_tx, CANDIDATE)
    refs = {hex(v): references(r, v) for v in (0xc5ca, 0xfa58, 0xf9bc, 0xf928, 0xd3ec, 0xd936, 0x5ea0, 0x1019c, 0x3a28)}
    assert refs['0xc5ca']['literal32_pools_all_alignments'] == [0x45ddc]
    assert refs['0xc5ca']['pc_relative_loads'] == [0x45d44]
    assert not refs['0xc5ca']['relative_branches']
    assert refs['0xd3ec']['literal32_pools_all_alignments'] == [0x101a4]
    assert refs['0xd936']['literal32_pools_all_alignments'] == [0x5f74]
    assert refs['0x5ea0']['literal32_pools_all_alignments'] == [0x3104]

    # Actual timer selection table, callback pointers and task state geometry.
    index_map = list(r[0x10200:0x10209])
    assert index_map == [1, 2, 4, 5, 6, 7, 8, 9, 10]
    callback = [u32(r, 0x1019c+4*i) for i in range(25)]
    assert callback[2] == 0xd3ec
    assert u32(r, 0x1020c) == 21 and u32(r, 0x10214) == 23
    tasks = []
    assert u16(r, 0x4884) == 19
    for i in range(19):
        a = 0x48d8+16*i
        tasks.append(dict(slot=i, descriptor=a, kind=r[a], priority=r[a+2],
                          state=u32(r, a+4), entry=u32(r, a+8), activation_capacity=r[a+12]))
    assert tasks[9] == dict(slot=9, descriptor=0x4968, kind=4, priority=2,
                           state=0xffff11e4, entry=0x6580, activation_capacity=2)
    assert u32(r, 0x4880) == 0xffff119c
    # Check every 16-bit timer counter transition, including wrap, at software
    # level. Instruction-level event-boundary tests are reported independently.
    selected = []
    for n in range(65536):
        selected_index = next((index_map[b] for b in range(9) if n & (1 << b)), None)
        if selected_index == 2:
            selected.append(n)
        assert (selected_index == 2) == (n % 4 == 2)
    assert len(selected) == 16384

    copy_targets = memcpy_dispatch_contract(r)
    negative_rejected = []
    for label, address, replacement in (
            ('table_entry_redirect_to_candidate_rom', 0x4438, bytes.fromhex('000e1000')),
            ('bound_expanded_past_table', 0x43de, bytes.fromhex('e344'))):
        mutated = bytearray(r)
        mutated[address:address+len(replacement)] = replacement
        try:
            memcpy_dispatch_contract(mutated)
        except AssertionError:
            negative_rejected.append(label)
        else:
            raise AssertionError('negative dispatch contract accepted: '+label)
    assert len(negative_rejected) == 2
    # The ring's 16-bit index is nonnegative; nominal producer/consumer code
    # initializes0 and wraps after99. There is no downward address arithmetic.
    assert u16(r, 0x52a) == 0xe364 and u16(r, 0x542) == 0xe164
    assert u16(r, 0x56a) == 0x2341 and u16(r, 0x56e) == 0x2241
    ring = (0xffffb4e0, 0xffffb4e0+100*8)
    assert ring == (0xffffb4e0, 0xffffb800) and not overlaps(ring, CANDIDATE)
    assert u16(r, 0x4bb8) == 0x24f6 and u16(r, 0x4bbc) == 0x6f43
    assert u16(r, 0x4bc0) == 0x6ff2

    windows = {
        'boot_stack_and_ram_test': (0xf928, 0xfab0),
        'dma_interrupt_setup': (0xc2de, 0xc504),
        'dma_synchronous_routine': (0xc5ca, 0xc810),
        'dma_synchronous_caller': (0x45d3a, 0x45df4),
        'dma_fault_handlers': (0x52c8, 0x5420),
        'runtime_sp_and_context': (0x3930, 0x3cfb),
        'rtos_dispatch_and_init': (0x3dc8, 0x41bc),
        'task_descriptors': (0x4880, 0x4a9c),
        'task9_activate_and_timer': (0xd3ec, 0xd408),
        'timer_init_and_dispatch': (0xd904, 0xdc38),
        'timer_interrupt_handler': (0x5e84, 0x5f84),
        'timer_callback_tables': (0x10198, 0x1021c),
        'ram_emulation_disable': (0x51dc, 0x51ec),
        'bounded_memcpy_dispatch': (0x43dc, 0x449c),
        'boot_communication_ring': (0x4f4, 0x5ac),
        'temporary_boot_stack_switch': (0x4bb8, 0x4bc6),
        'temporary_boot_stack_calls': (0xd1ac, 0xd200),
        'highest_scalar_neighbor': (0x71c88, 0x71cfc),
    }
    dis = OUT / 'disassembly'
    dis.mkdir(exist_ok=True)
    outputs = {}
    for name, (a, b) in windows.items():
        cmd = [str(OBJDUMP), '-D', '-b', 'binary', '-m', 'sh2e', '-EB',
               f'--start-address={a}', f'--stop-address={b}', str(ROM)]
        run = subprocess.run(cmd, capture_output=True, text=True, check=True)
        path = dis / (name+'.txt')
        path.write_text(run.stdout, encoding='utf-8')
        outputs[name] = dict(start=a, end=b, rom_bytes_sha256=sha(r[a:b]),
                             disassembly=str(path), disassembly_sha256=sha(path.read_bytes()), argv=cmd)
    report = dict(
        status='STATIC_IDENTIFIED_PATHS_BOUNDED_NOT_WHOLE_RAM_OWNERSHIP_APPROVAL',
        baseline=dict(path=str(ROM), sha256=BASELINE),
        frozen_payload=dict(path=str(code), sha256=PAYLOAD, manifest_sha256=sha(manifest_path.read_bytes())),
        candidate=dict(start=CANDIDATE[0], end_exclusive=CANDIDATE[1], bytes=32),
        decoded_literal_loads=loads, verified_instruction_words=words, raw_references=refs,
        dma=dict(
            reset=dict(routine=0xf9bc, start=boot[0], end_exclusive=boot[1], transfer_words=count,
                       config=channel(0x001f0128), candidate_written=True,
                       lifetime='Before RTOS launch from D210; not preserved across boot memory-test/clear.'),
            async_rx=dict(setup_start=0xc31e, setup_end=0xc376, destination_span=rx_span,
                          source=0xfffff00d, transfers=2, config=channel(0x40100), index_domain=[0, 255]),
            async_tx=dict(source_span=tx_span, destination=0xfffff00b, transfers=2,
                          config=channel(0x31000), index_domain=[0, 255]),
            sync=dict(routine=0xc5ca, only_identified_caller=0x45d3a, count=20,
                      transfers_per_iteration=2, tx_span=sync_tx, rx_span=sync_rx),
            fault_handlers='53A6/53B4/53F4/5404 only clear TE;530A modifies DMAOR, no new destination.'),
        ram_test=dict(routine=0xfa58, candidate_written=True, final_pattern=0xa55a5aa5,
                      first_pattern=0x5aa5a55a,
                      simulator_report='../runtime/20260925T211558.608898Z_gate_closure_runtime/ram_pattern_FA58.json'),
        boot_storage=dict(communication_ring=ring, ring_index_width=16, nominal_ring_slots=100,
                          ring_start_is_not_stack_base=True, temporary_sp=0xffffbff8,
                          temporary_stack_written_span=[0xffffbfec,0xffffbffc],
                          temporary_stack_calls=[0xfa58,0xd1ac,0x2088,0x2098,0x2410],
                          initial_vector_sp=0xffffbfa0,
                          caveat='Temporary F928 call chain bounded; entire boot/exception stack not proved here.'),
        highest_scalar_neighbor=dict(address=0xffff736c, accessed_bytes=1,
                                     direct_write_sites=[0x71ca0,0x71cc4,0x71ce4],
                                     end_exclusive=0xffff736d, gap_before_candidate=0x93,
                                     caveat='This highest literal scalar does not prove absence of arrays or computed higher addresses.'),
        memcpy_dispatch=dict(jump=0x43e8, table=0x4438, unsigned_maximum_size=64,
                             valid_aligned_targets=copy_targets, generic_loop=0x447c,
                             alignment_required=4, negative_contract_tests_rejected=negative_rejected,
                             caveat='Bounds control target only; caller-supplied destination ownership remains separate.'),
        hardware=dict(manual=MANUAL, manual_id='REJ09B0046-0300H Rev.3.00, September 2004',
                      on_chip_ram=[0xffff0000, 0xffffc000], ram_manual_section='24.1/24.2',
                      ram_emulation_physical_span=[0xffff0000, 0xffff1000], ram_emulation_register=0xffffec26,
                      candidate_overlaps_ram_emulation=False, alias_manual_section='9.2.2 / Table9.4',
                      dma_manual_section='10.2.1..10.2.5',
                      flash_kernel_download_start_domain=[0xffff0000, 0xffff2800],
                      flash_kernel_manual_section='23.6.4 FTDAR; start selector00..05 in2KiB units'),
        task9=dict(tasks=tasks, shared_stack_initial=0xffff119c,
                   task_state_is_not_stack_base=True, scheduler_context=0xffff12b0,
                   current_sp_field=0xffff12bc, saved_predecessor_sp_field=0xffff11e8,
                   callback_table=0x1019c, callback_index=2, activation_wrapper=0xd3ec,
                   activation_call=0xd3f0, activation_api=0x3a28, timer_routine=0xd936,
                   index_map=index_map, task9_enqueues_per_65536_half_ticks=len(selected),
                   timer_invocation_interval=8, zero_initialized_phase_first_invocation=3,
                   alternate_dispatch_indices=[21,23],
                   cmt1=dict(cmcsr=0x00c0, cmcor=2499, divider=8, peripheral_clocks_per_tick=20000,
                             peripheral_clocks_per_enqueue=160000, absolute_hz_unknown=True,
                             source_sections='14.2.2,14.4.2: compare flag occurs next timer clock after equal'),
                   limitations=['enqueue cadence does not prove completion deadline or physical frequency',
                                'task activation capacity two permits pending activation; scheduler dispatch/liveness still matters',
                                'shared stack inheritance excludes high candidate only under valid, uncorrupted saved contexts'],
                   same_priority_enqueue=dict(incoming=2, decision=0x3bcc, no_switch_branch=0x3bce,
                                              enclosing_return_path=[0x3a68,0x3aa6],
                                              inference='Incoming priority2 does not request immediate dispatch when current priority>=2; context/ISR invariant remains to prove.')),
        regression=dict(full_byte_index_pairs=65536, full_timer_counter_values=65536,
                        exact_image_and_frozen_code_checks=True, result='PASS'),
        windows=outputs,
        limitations=['Does not prove all indirect CPU writes, external diagnostic writes, boot/programming scratch or asynchronous contexts.',
                     'Raw literal/reference search includes data and cannot prove absence of computed pointers.',
                     'No physical ECU, bus, DMA execution, or flash action occurred.'])
    dest = OUT / 'ram_path_audit.json'
    dest.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(report=str(dest), sha256=sha(dest.read_bytes()), regression='PASS',
                          candidate_bytes=32, reset_transfer_words=count, runtime_dma_rx_max_end=hex(sync_rx[1]),
                          task9_timer_interval=8)))


if __name__ == '__main__':
    main()
