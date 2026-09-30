"""Offline exact-stock RXI/self-echo replay; no provider or hardware imports.

This adds actual RXI admission and self-echo handling to the retained scoped
parser/serializer transcript. It deliberately does not claim elapsed timing,
interrupt scheduling, live ROM identity, or electrical behavior.
"""
import sys
sys.dont_write_bytecode = True
import json
import hashlib
import gzip
from pathlib import Path

OUT = Path(__file__).resolve().parent
CONTRACTS = Path('C:/Dev/A2WC511R_ReadKernel/evidence/contracts')
sys.path.insert(0, str(CONTRACTS))
from verify_kwp_wire import CPU, sh, common, TranscriptMemory


def pin(path):
    path = Path(path)
    content = path.read_bytes()
    return {'path': str(path), 'bytes': len(content),
            'sha256': hashlib.sha256(content).hexdigest()}


class RXIMemory(TranscriptMemory):
    def __init__(self, rom):
        super().__init__(rom)
        self.rdr = 0
        self.rdr_reads = []

    def read(self, address, size, address_sources=(), fetch=False):
        if address == 0xFFFFF015 and size == 1 and not fetch:
            self.rdr_reads.append({'pc': f'{self.pc:08X}', 'value': self.rdr})
            return self.rdr, {'explicit_RDR_byte_transcript'}
        return super().read(address, size, address_sources, fetch)


def main():
    rom = sh.ROM.load(common.STOCK, sh.STOCK_SHA256)
    ref = common.module('oem_transition_reference', common.REF)
    rows, all_traces = [], []
    for case in ('normal_echo', 'corrupted_final_C1_echo'):
        mem = RXIMemory(rom)
        mem.initialize(0xFFFF63E0, bytes(0xC0))
        ranges = [(0x47108, 0x47192), (0x471C2, 0x47AFA),
                  (0x47E24, 0x48070), (0x4808C, 0x4823A),
                  (0x484F4, 0x4857E), (0x2534, 0x2550)]
        traces = []
        def call(entry):
            h = sh.FunctionHarness(mem, ranges)
            h.cpu = CPU(mem, ranges, h.stack)
            h.cpu.track_control_sources = False
            result = h.run(entry, allowed_writes=[(0xFFFF63E0, 0xFFFF64A0)],
                           max_steps=3500)
            traces.extend(h.cpu.trace)
            return result

        def receive(byte):
            mem.rdr = byte
            call(0x47E24)

        transactions = []
        for payload, expected in ((bytes.fromhex('81'), bytes.fromhex('c1ef8f')),
                                  (bytes.fromhex('8300'), bytes.fromhex('c30000ff00ff00'))):
            frame = ref.ssm(payload)
            offset = len(mem.tx)
            mmio_offset = len(mem.mmio)
            for byte in frame:
                receive(byte)
            c = CPU(mem, [(0x47DEE, 0x47E02)], (0xFFFFBBA0, 0xFFFFBFA0))
            c.pc, c.r[15], c.call_context = 0x47DEE, 0xFFFFBFA0, ['00047DEE']
            for _ in range(20):
                c.step()
                if c.pc == 0x47E06 and not c.pending:
                    break
            assert c.pc == 0x47E06 and not c.pending
            traces.extend(c.trace)
            mem.pc = None
            expected_frame = ref.ssm(expected, response=True)
            echoes = []
            for index in range(len(expected_frame)):
                assert len(mem.tx) == offset + index + 1
                byte = mem.tx[-1]
                if case == 'corrupted_final_C1_echo' and payload == b'\x81' and index == len(expected_frame)-1:
                    byte ^= 1
                echoes.append(byte)
                receive(byte)
            actual = bytes(mem.tx[offset:])
            assert actual == expected_frame, (case, payload.hex(), actual.hex())
            assert not (mem.ram[0x649A] & 0x20)
            mmio = mem.mmio[mmio_offset:]
            assert not any(item['mode'] == 'write' and item['address'] in ('FFFFF010', 'FFFFF011', 'FFFFF016') for item in mmio)
            transactions.append({'request': frame.hex(), 'reply': actual.hex(),
                                 'self_echo_bytes': bytes(echoes).hex(),
                                 'state_after': {'session_63E1': mem.ram[0x63E1],
                                                 'transmitting_649A_bit20': bool(mem.ram[0x649A] & 0x20)},
                                 'mmio_writes': [item for item in mmio if item['mode'] == 'write']})
        row = {'case': case, 'transactions': transactions,
               'executed_instructions': len(traces), 'RDR_reads': len(mem.rdr_reads)}
        rows.append(row)
        all_traces.append({'case': case, 'instructions': traces, 'memory': mem.events,
                           'mmio': mem.mmio, 'rdr_reads': mem.rdr_reads})
    packed = gzip.compress(json.dumps(all_traces, sort_keys=True, separators=(',', ':')).encode(), mtime=0)
    trace_path = OUT/'oem_transition_rx_isr_trace.json.gz'
    trace_path.write_bytes(packed)
    report = {'status': 'PASS_SCOPED_STOCK_RXI_AND_ECHO_TRANSCRIPT',
              'inputs': [pin(common.STOCK), pin(__file__), pin(CONTRACTS/'verify_kwp_wire.py'),
                         pin(CONTRACTS/'verify_kwp_contract.py'), pin(CONTRACTS/'verify_oem_contracts.py')],
              'trace': pin(trace_path), 'cases': rows,
              'physical_operations': 0, 'provider_loaded': False,
              'limits': ['Exact stock baseline only; current vehicle code is unacquired.',
                         'SCI SSR=84 readiness/error-free transcript, not electrical simulation.',
                         'RDR bytes supplied through actual 47E24 receiver handler; no real interrupt scheduler.',
                         'First reply TDR store starts at47DEE, conditional on periodic counter reaching3.',
                         'No elapsed-time, CPU-speed, wire-gap or adapter timing claim.',
                         'Corrupt final echo negative case demonstrates reset still permits following83 under supplied inputs; does not assert physical echo corruption.']}
    (OUT/'oem_transition_rx_isr_replay.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'cases': [{'case': r['case'], 'instructions': r['executed_instructions']} for r in rows]}))


if __name__ == '__main__':
    main()
