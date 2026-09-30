"""Execute the stock seven/eight periodic tick interbyte boundary, offline.

Ticks are actual calls of stock47D94. Their physical duration is not assumed.
"""
import sys
sys.dont_write_bytecode = True
import json
import gzip
from pathlib import Path
from oem_transition_replay import OUT, CONTRACTS, CPU, sh, common, RXIMemory, pin


def main():
    rom = sh.ROM.load(common.STOCK, sh.STOCK_SHA256)
    ref = common.module('oem_transition_gap_reference', common.REF)
    rows, traces = [], []
    for ticks in (0, 7, 8, 9):
        mem = RXIMemory(rom)
        mem.initialize(0xFFFF63E0, bytes(0xC0))
        ranges = [(0x47108, 0x47192), (0x471C2, 0x47AFA),
                  (0x47D94, 0x48070), (0x4808C, 0x4823A),
                  (0x484F4, 0x4857E), (0x251C, 0x2550),
                  (0x3AF4, 0x3B20)]
        trace = []

        def call(entry):
            h = sh.FunctionHarness(mem, ranges)
            h.cpu = CPU(mem, ranges, h.stack)
            h.cpu.track_control_sources = False
            result = h.run(entry, allowed_writes=[(0xFFFF63E0, 0xFFFF64A0)],
                           system_registers={'sr': 0x390}, max_steps=3500)
            trace.extend(h.cpu.trace)
            return result

        def receive(byte):
            mem.rdr = byte
            call(0x47E24)

        # Complete81 through the realRXI and three realperiodic servicecalls.
        for byte in ref.ssm(bytes.fromhex('81')):
            receive(byte)
        for _ in range(3):
            call(0x47D94)
        c1 = ref.ssm(bytes.fromhex('c1ef8f'), response=True)
        for index in range(len(c1)):
            assert len(mem.tx) == index+1
            receive(mem.tx[-1])
        assert bytes(mem.tx) == c1
        assert mem.ram[0x63E1] == 0x20
        assert not (mem.ram[0x649A] & 0x20)

        # Gap only between the first and second bytes of8300.
        request = ref.ssm(bytes.fromhex('8300'))
        receive(request[0])
        for _ in range(ticks):
            call(0x47D94)
        state_at_gap = {'counter_63F6': int.from_bytes(mem.ram[0x63F6:0x63F8], 'big'),
                        'receive_cursor_63FD': mem.ram[0x63FD],
                        'session_63E1': mem.ram[0x63E1]}
        for byte in request[1:]:
            receive(byte)
        for _ in range(3):
            call(0x47D94)
        if ticks < 8:
            expected = ref.ssm(bytes.fromhex('c30000ff00ff00'), response=True)
            offset = len(c1)
            for index in range(len(expected)):
                assert len(mem.tx) == offset+index+1
                receive(mem.tx[-1])
            assert bytes(mem.tx[offset:]) == expected
        else:
            assert len(mem.tx) == len(c1)
        rows.append({'periodic_ticks_between_header_byte0_and_byte1': ticks,
                     'tick_duration_seconds': None,
                     'state_at_gap_end': state_at_gap,
                     'request_83': request.hex(),
                     'response_after_83': bytes(mem.tx[len(c1):]).hex(),
                     'executed_instructions': len(trace)})
        traces.append({'ticks': ticks, 'instructions': trace, 'memory': mem.events,
                       'mmio': mem.mmio, 'rdr_reads': mem.rdr_reads})
    trace_path = OUT/'oem_transition_gap_trace.json.gz'
    trace_path.write_bytes(gzip.compress(json.dumps(traces, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    report = {'status': 'PASS_STOCK_INTERBYTE_PERIODIC_TICK_BOUNDARY',
              'cases': rows, 'inputs': [pin(common.STOCK), pin(__file__), pin(OUT/'oem_transition_replay.py'),
                                      pin(CONTRACTS/'verify_kwp_contract.py'), pin(CONTRACTS/'verify_kwp_wire.py')],
              'trace': pin(trace_path), 'physical_operations': 0,
              'limits': ['No milliseconds assigned to periodic ticks.',
                         'Each periodiccall completes between suppliedRXI calls; asynchronouspreemption unmodeled.',
                         'No provider, adapter, waveform, currentvehicleROM or electricalacceptanceclaim.',
                         'SR390 supplied to preserve a nonzero mask through3AF4/3B08; schedulerdescriptor domainnotexecuted.',
                         'SCI ready/noerror transcript retained; actual requestparser, RXI, echo and periodicfunctionexecute.']}
    (OUT/'oem_transition_gap_replay.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'cases': rows}))


if __name__ == '__main__':
    main()
