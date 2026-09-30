"""Bounded offline OEM start and one kernel identity exchange; no physical APIs."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(r'C:\Dev\A2WC511R_ReadKernel')
OUT = Path(__file__).resolve().parent
CONTRACTS = ROOT/'evidence/contracts'
MANIFEST = ROOT/'build/rk02_01/manifest.json'
KERNEL = ROOT/'build/rk02_01/kernel.bin'
CURRENT = Path(r'C:\Dev\SubaruRoms\current.bin')
CURRENT_SHA = 'bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2'
KERNEL_SHA = '3a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581'
PRIOR = Path(r'C:\Dev\A2WC511R_Final\analysis\rk03_full_upload_no_start_20260930_01\current_instruction_replay')
START = bytes.fromhex('8010f003310101b6')
START_ACK = bytes.fromhex('80f01003710101f6')
IDENTITY_REQUEST = bytes.fromhex('beef000101af')
IDENTITY_RESPONSE = bytes.fromhex('beef000f8141325743353131522d524b3032005f')
EXPECTED_MODELS = {
    '__init__.py': '8e8b1da117fdc2ba4fe06edfc32b9c8d67176ab69a9470ee21151018bc85fbd8',
    'core.py': 'caf6571a836676b82bec8f8a5eaa356590532e15931fae2da4b5822fe8ef0f90',
    'cpu.py': '5043dafdfe59447cb8d906f7570907c472e1d638deb507dc4af8546e9b0f1980',
    'fast_step.py': '029bb2b484911289b19e5cdbad35bbbbdc80af05420e91dad6884e0ff0484cfa',
    'harness.py': '0496579da46daf66eb3be3847da0f3e94f8f45bf6f0b494a1f89a97853a8b4c6',
    'memory.py': 'd6062f1dde275b9611d1b631f8151eac567314c603a533dad8751eede3fa2a38',
    'sci.py': '6f3b4b38ae6e12ac75d5101c767f10b106e9676c322eac3a0e39a67a9c0030c1',
    'self_echo.py': '87896f45a074fcff5132a6faa57af48f5444de13fdf67f00a4f1304ea583da5d',
}


def pin(path):
    path = Path(path)
    blob = path.read_bytes()
    return {'path': str(path), 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def packed(path, value):
    blob = gzip.compress(json.dumps(value, sort_keys=True, separators=(',', ':')).encode(), mtime=0)
    with Path(path).open('xb') as f:
        f.write(blob)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def main():
    run = OUT/('replay_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir(exist_ok=False)
    report = {'schema': 1, 'status': 'FAIL', 'scope': 'OFFLINE_OEM_START_AND_SINGLE_IDENTITY_ONLY',
        'physical_operations': 0, 'provider_loads': 0, 'acquisition_requests': 0,
        'reviewer': 'passive_review', 'upload_instructions_reexecuted': 0}
    try:
        assert pin(MANIFEST)['sha256'] == 'a35562a19f21d4a2815e88fb729d21dd2cc08bf702c0d866f88ffc9e3ddb659e'
        assert pin(KERNEL)['sha256'] == KERNEL_SHA and KERNEL.stat().st_size == 1808
        assert pin(CURRENT)['sha256'] == CURRENT_SHA
        manifest = read(MANIFEST)
        assert manifest['entry'] == 0xffff3004 and manifest['load_address'] == 0xffff3000
        for relative, expected in manifest['sources'].items():
            assert pin(ROOT/relative)['sha256'] == expected
        models = [pin(ROOT/'sim'/name) for name in EXPECTED_MODELS]
        assert all(x['sha256'] == EXPECTED_MODELS[Path(x['path']).name] for x in models)
        core_path = Path(r'C:\Dev\A2WC511R_Sim\sh2e.py')
        assert pin(core_path)['sha256'] == 'b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff'
        upload_contract_path = CONTRACTS/'UPLOAD_WIRE_CONTRACT_RK02.json'
        assert pin(upload_contract_path)['sha256'] == 'b1c5431141f9b249b16dd15938c290f20b99593e7ab8512caebcde1906c37f50'
        upload = read(upload_contract_path)
        assert upload['frames'][16] == {'frame_index': 16, 'request': START.hex(),
            'reply_from_executed_TDR': START_ACK.hex(), 'instructions': 2902}
        for item in upload['inputs'] + [upload['trace']]:
            assert pin(item['path'])['sha256'] == item['sha256']
        prior_path = PRIOR/'CURRENT_NO_START_REPLAY.json'
        prior = read(prior_path)
        assert prior['status'] == 'PASS_CURRENT_INSTRUCTIONS_FULL_FIXED_UPLOAD_NO_START'
        assert prior['instruction_count'] == 476281 and prior['kernel_started'] is False
        assert prior['uploaded_ram_sha256'] == KERNEL_SHA
        for item in prior['inputs'] + [prior['trace'], prior['derived_ram']]:
            assert pin(item['path'])['sha256'] == item['sha256']
        retained = json.loads(gzip.decompress(Path(prior['trace']['path']).read_bytes()))
        assert len(retained['instructions']) == 476281
        source = CONTRACTS/'verify_upload_wire_rk02.py'
        sys.path.insert(0, str(CONTRACTS))
        loader = module('identity_oem_loader_classes_no_main', source)
        rom = loader.sh.ROM.load(CURRENT, CURRENT_SHA)
        memory = loader.Memory(rom)
        memory.initialize(0xffffbfa0, bytes(0x60))
        memory.initialize(0xffffbfba, b'\x01')
        memory.initialize(0xffffbfc8, b'\x01')
        memory.initialize(0xffffbb80, bytes(0x420))
        reconstructed_writes = 0
        for event in retained['memory']:
            if event['mode'] != 'w':
                continue
            address, size = int(event['address'], 16), event['size']
            assert loader.sh.RAM_START <= address < address+size <= loader.sh.RAM_END
            memory.initialize(address, int(event['value'], 16).to_bytes(size, 'big'))
            reconstructed_writes += 1
        scr_writes = [e['value'] for e in retained['mmio'] if e['mode']=='w' and e['address']=='FFFFF012']
        assert scr_writes
        memory.scr = scr_writes[-1]
        assert bytes(memory.ram[0x3000:0x3710]) == KERNEL.read_bytes()
        assert not memory.events and not memory.mmio and not memory.tx
        memory.write_allowlist = [(0xffffbb80, 0xffffc000), (0xffff3000, 0xffff3710)]
        loader_trace, per_byte = [], []
        entered = False
        for ordinal, byte in enumerate(START):
            assert not entered
            memory.byte = byte
            cpu = loader.CPU(memory, [(0x13f6, 0x1f40)], (0xffffbb80, 0xffffbfa0))
            cpu.pc = 0x1440
            cpu.pr = 0xfffffffc
            cpu.r[15] = 0xffffbfa0
            cpu.call_context = ['00001440']
            cpu._set_system('sr', 0xf0, {'boot_loop_mask15'})
            cpu.track_control_sources = False
            for _ in range(15000):
                cpu.step()
                if cpu.pc == 0xffff3004 and not cpu.pending:
                    assert ordinal == len(START)-1 and cpu.r[15] == 0xffffbfa0 and cpu.sr & 0xf0 == 0xf0
                    entered = True
                    break
                if cpu.returned:
                    assert cpu.pc == 0xfffffffc and cpu.r[15] == 0xffffbfa0 and not cpu.pending
                    break
            else:
                raise AssertionError('OEM start exceeded per-byte15000instruction limit')
            loader_trace.extend(cpu.trace)
            per_byte.append({'ordinal': ordinal, 'byte': byte, 'instructions': len(cpu.trace),
                'end_pc': f'{cpu.pc:08X}', 'pending_branch': cpu.pending, 'returned': cpu.returned})
        assert entered and bytes(memory.tx) == START_ACK and len(loader_trace) == 2902
        assert all(0x13f6 <= int(x['pc'], 16) < 0x1f40 for x in loader_trace)
        old_trace = json.loads(gzip.decompress(Path(upload['trace']['path']).read_bytes()))
        assert old_trace['instructions'][len(retained['instructions']):] == loader_trace
        assert old_trace['memory'][len(retained['memory']):] == memory.events
        assert old_trace['mmio'][len(retained['mmio']):] == memory.mmio
        packed(run/'OEM_START_TRACE.json.gz', {'instructions': loader_trace, 'memory': memory.events, 'mmio': memory.mmio})
        oem_reads = [x for x in memory.events if x['mode']=='r' and int(x['address'],16)<0x100000]
        report['OEM_start'] = {'request': START.hex(), 'reply_from_executed_TDR': bytes(memory.tx).hex(),
            'instructions': len(loader_trace), 'per_byte': per_byte, 'entry_reached': f'{cpu.pc:08X}',
            'SP': f'{cpu.r[15]:08X}', 'SR': f'{cpu.sr:08X}', 'kernel_instructions_executed_in_OEM_phase': 0,
            'restored_prior_memory_write_events': reconstructed_writes, 'restored_SCR': memory.scr,
            'exact_retained_stock_start_suffix_match': True, 'OEM_ROM_constant_read_events': oem_reads,
            'trace': pin(run/'OEM_START_TRACE.json.gz')}
        del retained, old_trace

        sys.path.insert(0, str(ROOT))
        from sim.harness import KernelSession
        from sim.sci import Schedule
        from sim.self_echo import EchoProfile
        session = KernelSession(MANIFEST, CURRENT, CURRENT_SHA, kernel_bytes=KERNEL.read_bytes(),
            trace_dir=run/'kernel_exchanges', detailed=True, optimized=False,
            schedule=Schedule(rx_gap_ticks=1, tx_complete_ticks=1, brr_settle_ticks=1, tx_load_ticks=1),
            receiver_self_echo=True, echo_profile=EchoProfile(start_delay_ticks=0))
        assert session.entry == 0xffff3004 and session.identity['model_sources'] == EXPECTED_MODELS
        started = session.start(entry=0xffff3004, instruction_budget=20000)
        assert started.status == 'PASS' and started.stop_reason == 'RX_WAIT' and started.tx_bytes == b''
        response = session.exchange(IDENTITY_REQUEST, instruction_budget=20000)
        assert response.status == 'PASS' and response.stop_reason == 'RX_WAIT'
        assert response.tx_bytes == IDENTITY_RESPONSE
        identity_ascii = bytes.fromhex(manifest['protocol']['identity_hex'])
        assert IDENTITY_RESPONSE[4:-1] == b'\x81'+identity_ascii
        assert identity_ascii == b'A2WC511R-RK02\0' and IDENTITY_RESPONSE[-1] == sum(IDENTITY_RESPONSE[:-1]) & 255
        coverage = session.coverage()
        assert len(coverage['exchanges']) == 2 and coverage['terminal'] is None
        symbols = manifest['symbols']
        forbidden_symbols = ['raw_read', 'decode_address', 'pass_done', 'complete', 'tx_raw', 'tx_address', 'tx_data',
            'fatal', 'halt_fail', 'exception_handler', 'halt_exception']
        assert symbols['identity'] in session.cpu.pc_counts
        assert all(symbols[name] not in session.cpu.pc_counts for name in forbidden_symbols)
        assert set(session.cpu.pc_counts) <= set(manifest['instruction_addresses'])
        assert session.cpu.r[8] == session.cpu.r[9] == session.cpu.r[11] == 0 and session.cpu.r[10] == 1
        assert session.cpu.vbr == manifest['vector_base'] and session.cpu.sr & 0xf0 == 0xf0
        assert coverage['stack_max_bytes'] <= manifest['stack_high']-manifest['stack_low']
        assert session.memory.kernel == KERNEL.read_bytes()
        rom_reads = [x for x in session.memory.events if x['mode']=='r' and int(x['address'],16)<0x100000]
        assert not rom_reads
        writes = [x for x in session.memory.events if x['mode']=='w']
        mmio_writes = [x for x in writes if int(x['address'],16)>=0xffffc000]
        allowed_mmio_writes = {0xffffecb0, 0xffffec10, 0xfffff73c, *range(0xfffff010, 0xfffff017)}
        assert all(int(x['address'],16) in allowed_mmio_writes for x in mmio_writes)
        assert all(not (0xffffe800<=int(x['address'],16)<0xffffe810) for x in writes)
        assert all(not (0<=int(x['address'],16)<0x100000) for x in writes)
        assert session.peripheral.sci.event_counts['host_rx_enqueued'] == 1
        assert session.peripheral.sci.event_counts['tx_character_complete'] == len(IDENTITY_RESPONSE)
        assert session.peripheral.sci.rx_empty and session.peripheral.sci.tx_idle and session.peripheral.sci.line_idle
        assert bytes(session.peripheral.sci.tx) == IDENTITY_RESPONSE
        save(run/'KERNEL_COVERAGE.json', coverage)
        packed(run/'KERNEL_IDENTITY_TRACE.json.gz', {'instructions': session.cpu.trace.rows,
            'memory': session.memory.events, 'SCI_events': session.peripheral.sci.events,
            'other_peripheral_events': session.peripheral.events})
        report['kernel_identity'] = {'request': IDENTITY_REQUEST.hex(), 'response_from_executed_SCI': response.tx_bytes.hex(),
            'identity_ascii': manifest['protocol']['identity_ascii'], 'startup': started.as_dict(),
            'exchange': response.as_dict(), 'entry': 'FFFF3004', 'end_pc': f'{session.cpu.pc:08X}',
            'stop_reason': 'RX_WAIT_AFTER_ONE_IDENTITY_EXCHANGE', 'raw_read_branch_executed': False,
            'forbidden_symbols_unexecuted': forbidden_symbols, 'ROM_data_read_events': 0, 'flash_write_events': 0,
            'host_requests': 1, 'response_bytes': len(response.tx_bytes), 'model_identity': session.identity,
            'MMIO_write_addresses': sorted({x['address'] for x in mmio_writes}),
            'private_RAM_write_count': len(writes)-len(mmio_writes),
            'coverage': pin(run/'KERNEL_COVERAGE.json'), 'trace': pin(run/'KERNEL_IDENTITY_TRACE.json.gz')}
        imported = []
        for obj in list(sys.modules.values()):
            path = getattr(obj, '__file__', None)
            if path and str(path).lower().startswith('c:\\dev\\') and Path(path).suffix == '.py':
                imported.append(Path(path).resolve())
        inputs = [MANIFEST, KERNEL, CURRENT, core_path, source, upload_contract_path, prior_path,
            Path(prior['trace']['path']), Path(prior['derived_ram']['path']), Path(upload['trace']['path']), Path(__file__)]
        inputs += [ROOT/'sim'/name for name in EXPECTED_MODELS] + imported
        report['inputs'] = [pin(p) for p in sorted(set(inputs))]
        for item in models:
            assert pin(item['path']) == item
        assert pin(KERNEL)['sha256'] == KERNEL_SHA and pin(CURRENT)['sha256'] == CURRENT_SHA
        report['status'] = 'PASS_OFFLINE_OEM_START_AND_SINGLE_KERNEL_IDENTITY'
        report['limits'] = [
            'No hardware, provider load, native physical host, acquisition or flash operation was invoked.',
            'The completed upload was reused. OEM parser RAM was reconstructed from the retained current-ROM trace writes, then only the fixed start frame was executed.',
            'OEM start uses the retained admitted-parser/RDR/readyTEND/watchdog fixtures and fresh bounded CPU calls per byte. Its ROM constant reads are legitimate OEM execution, not ROM acquisition.',
            'KernelSession begins at the verified entry with its recorded poisoned-register and peripheral fixtures. This is a linked boundary proof, not one uninterrupted vehicle or reset-to-identity simulation.',
            'One instruction tick is an abstract schedule unit, not a CPU cycle, measured baud, UART waveform or physical elapsed time. Default collapsed SCI scheduling and explicit self-echo are recorded.',
            'Only one fixed identity request was fed. The kernel remains at an empty RX wait afterward; the model does not prove physical shutdown or recovery.',
            'The unchanged kernel contains a raw-read command, but this replay never enters that branch and performs zero kernel ROM-data reads. No claim covers all malformed requests or later commands.'
        ]
    except Exception:
        report['error'] = traceback.format_exc()
    report['artifacts'] = [pin(p) for p in sorted(run.rglob('*')) if p.is_file()]
    save(run/'INSTRUCTION_REPLAY.json', report)
    if report['status'].startswith('PASS'):
        save(OUT/'INSTRUCTION_REVIEW.json', {'status': report['status'], 'replay': pin(run/'INSTRUCTION_REPLAY.json'),
            'scope': report['scope'], 'physical_operations': 0, 'provider_loads': 0, 'acquisition_requests': 0})
    print(json.dumps({'status': report['status'], 'report': pin(run/'INSTRUCTION_REPLAY.json'), 'error': report.get('error')}))
    return 0 if report['status'].startswith('PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
