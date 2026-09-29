"""Exact m06_03 compiler closure: finite CFG/frames and executable test fixtures."""
from pathlib import Path
from hashlib import sha256
from collections import deque
from functools import lru_cache
import json

from sh2e import ROM, Memory, CPU, OPCODES, STOCK_SHA256, RAM_START, sx
from runtime_audit import StaticAudit, READS, WRITES, REGISTER_WRITES

BUILD = Path('C:/Dev/Astra_A2WC511R/work/builds/m06_04')
REQ, TX, FLAGS = 0xFFFF6408, 0xFFFF6492, 0xFFFF649A
CODE, LENGTH = 0xFFFF6401, 0xFFFF6405
SP, RETURN = 0xFFFFBFA0, 0xFFFFFFFC
INPUTS = dict(source=0xFFFF4C75, snapshot=0xFFFF4C8D, latch=0xFFFF4CA1,
              flags=0xFFFF4C50, target=0xFFFF4BC1, current=0xFFFF4BC2)
ENTRY = dict(default=0x4F544, refill_hook=0x4F5A8, match=0x4F608, page=0x4F660, refill=0x4F6F4)
BOUNDS = {0x4F544: 0x4F59E, 0x4F5A8: 0x4F5FA, 0x4F608: 0x4F648,
          0x4F660: 0x4F6E0, 0x4F6F4: 0x4F742}


@lru_cache(None)
def artifacts():
    manifest = json.loads((BUILD / 'manifest.json').read_text())
    stock = ROM.load('C:/Dev/SubaruRoms/OEM/A2WC511R.bin', STOCK_SHA256)
    raw = ROM.load(BUILD / 'A2WC511R_M06.EXPERIMENTAL_NOT_FLASH_READY.raw.bin', manifest['raw_sha256'])
    for name in ('A2WC511R_M06.EXPERIMENTAL.elf', 'm06.EXPERIMENTAL.code.bin', 'm06.disassembly.txt'):
        if sha256((BUILD / name).read_bytes()).hexdigest() != manifest['artifacts'][name]:
            raise AssertionError(f'Changed build artifact {name}')
    for fragment in manifest['overlay_fragments']:
        a = fragment['address']
        before, after = bytes.fromhex(fragment['expected_before_hex']), bytes.fromhex(fragment['after_hex'])
        if stock.data[a:a + len(before)] != before or raw.data[a:a + len(after)] != after:
            raise AssertionError(f'Overlay mismatch {fragment["name"]}')
    if raw.data[0x11ADC:0x11AE0] != stock.data[0x11ADC:0x11AE0]:
        raise AssertionError('Task9 decoder hook changed')
    return stock, raw, manifest


def request(page=0):
    data = bytes.fromhex('8010F007BE4D303601') + bytes([page, 4])
    return data + bytes([sum(data) & 255])


def response(payload):
    data = bytes.fromhex('80F01005FE') + bytes(payload)
    return data + bytes([sum(data) & 255])


def expected_page(page, inputs):
    if page == 0:
        return bytes(inputs[name] for name in ('source', 'snapshot', 'latch', 'flags'))
    a, b, packed = (inputs[name] for name in ('target', 'current', 'snapshot'))
    reason = 128 + (packed != 17) + 2 * (a != 1 or b != 1) + 4 * (max(divmod(packed, 16)) > 8)
    return bytes([a, b, packed, reason])


def fixture(rom=None, req=None, inputs=None, out=TX, code=0xFE, length=5, flags=0x20, flags2=0x80, sp=SP):
    rom = rom or artifacts()[1]
    memory = Memory(rom)
    memory.initialize(0xFFFF63F0, b'\x55' * 0xC0)
    memory.initialize(REQ, req if req is not None else request())
    for address, value in ((CODE, code), (LENGTH, length), (FLAGS, flags), (FLAGS + 1, flags2)):
        memory.initialize(address, bytes([value]))
    values = dict(source=0x11, snapshot=0x11, latch=1, flags=2, target=1, current=1)
    values.update(inputs or {})
    for name, address in INPUTS.items():
        memory.initialize(address, bytes([values[name]]))
    memory.initialize(out - 1, b'\xA5' + b'\xC7' * 4 + b'\x5A')
    memory.initialize(sp - 132, b'\xDE\xAD\xC0\xDE' + b'\xC7' * 128 + b'\xFE\xED\xFA\xCE')
    memory.write_allowlist = [(sp - 128, sp), (out, out + 4), (CODE, CODE + 1), (LENGTH, LENGTH + 1), (FLAGS, FLAGS + 2)]
    memory.watch(out - 1, out + 5, 'output and sentinels')
    memory.watch(sp - 132, sp + 4, 'private stack and sentinels')
    for name, address in INPUTS.items():
        memory.watch(address, address + 1, 'source ' + name)
    cpu = CPU(memory, [(0x4F544, 0x4F75C), (0x484B0, 0x484C4), (0x484F4, 0x48500)], (sp - 128, sp))
    cpu.r = [((r + 1) * 0x9E3779B9) & 0xFFFFFFFF for r in range(16)]
    cpu.r[3], cpu.r[4], cpu.r[5] = 0x13572468, 0, out
    cpu.r[11], cpu.r[12], cpu.r[14], cpu.r[15] = CODE, LENGTH, FLAGS, sp
    cpu.pr, cpu.sr_other, cpu.t, cpu.mach, cpu.macl = RETURN, 0x0ACE0356, 1, 0xDEADBEEF, 0xFEDCBA98
    cpu.call_context = ['fixture']
    cpu.track_control_sources = False
    return cpu, values


def run(cpu, entry, exits=(RETURN,), max_steps=500):
    cpu.pc = entry
    for _ in range(max_steps):
        if cpu.pc in exits and cpu.pending is None:
            return cpu
        cpu.step()
    raise AssertionError(f'Execution exceeded fixture budget at {cpu.pc:08X}')


def output(cpu, address=TX):
    offset = address - RAM_START
    return bytes(cpu.memory.ram[offset:offset + 4])


class Closure(StaticAudit):
    def __init__(self):
        self.stock, self.rom, self.manifest = artifacts()
        self.functions = {}

    def resolve_call(self, pc, reg, entry):
        for prev in range(pc - 2, max(entry - 2, pc - 32), -2):
            word, spec = self.decode(prev)
            n = word >> 8 & 15
            if spec.branch:
                raise AssertionError('Call/jump resolution crossed a control transfer')
            if spec.name == 'movl_pc' and n == reg:
                pool = ((prev + 4) & ~3) + 4 * (word & 255)
                target = int.from_bytes(self.rom.data[pool:pool + 4], 'big')
                if target not in BOUNDS and target not in (0x484BC, 0x48500):
                    raise AssertionError(f'Unknown closure destination {target:08X}')
                return target, pool, prev
            if spec.name in REGISTER_WRITES | {'extsb', 'extuw', 'sub_reg', 'shll2'} and n == reg:
                raise AssertionError('Call target register clobbered')
        raise AssertionError('Missing local literal target')

    def graph(self, entry):
        if entry in self.functions:
            return self.functions[entry]
        graph, depths, calls, terminals = {}, {}, [], []
        todo = deque([(entry, 0)])
        while todo:
            pc, depth = todo.popleft()
            if pc in depths:
                if depths[pc] != depth:
                    raise AssertionError(f'Unequal frame join {pc:08X}')
                continue
            if not entry <= pc < BOUNDS[entry]:
                raise AssertionError(f'Escaped code boundary {pc:08X}')
            depths[pc] = depth
            word, spec = self.decode(pc)
            pcs, successors, call, terminal = [pc], [], None, None
            if spec.branch:
                if spec.name in ('rts', 'bra', 'bsr', 'jsr', 'jmp', 'bf_s', 'bt_s'):
                    if self.decode(pc + 2)[1].branch:
                        raise AssertionError('Branch in delay slot')
                    pcs.append(pc + 2)
                if spec.name == 'rts':
                    terminal = 'caller_PR'
                elif spec.name == 'bra':
                    successors = [pc + 4 + 2 * sx(word & 4095, 12)]
                elif spec.name in ('jsr', 'jmp'):
                    target, pool, load = self.resolve_call(pc, word >> 8 & 15, entry)
                    if spec.name == 'jsr':
                        call = target
                        calls.append(dict(pc=f'{pc:08X}', target=f'{target:08X}', pool=f'{pool:08X}', load=f'{load:08X}'))
                        successors = [pc + 4]
                    else:
                        terminal = f'{target:08X}'
                elif spec.name in ('bf', 'bt', 'bf_s', 'bt_s'):
                    successors = [pc + (4 if spec.name.endswith('_s') else 2), pc + 4 + 2 * sx(word & 255, 8)]
                else:
                    raise AssertionError(f'Unhandled closure branch {spec.name}')
            else:
                successors = [pc + 2]
            after, peak = depth, depth
            for p in pcs:
                after += self.sp_delta(p)
                peak = max(peak, after)
                if after < 0:
                    raise AssertionError('Frame underflow')
            if terminal is not None:
                if after != 0:
                    raise AssertionError('Unbalanced terminal frame')
                terminals.append(dict(pc=f'{pc:08X}', target=terminal))
            graph[pc] = dict(pcs=pcs, next=successors, call=call, depth_before=depth, depth_after=after, peak=peak)
            todo.extend((target, after) for target in successors)
        result = dict(graph=graph, depths=depths, calls=calls, terminals=terminals)
        self.functions[entry] = result
        return result

    @lru_cache(None)
    def bound(self, entry, metric='instructions'):
        graph = self.graph(entry)['graph']
        visiting = set()
        @lru_cache(None)
        def walk(pc):
            if pc in visiting:
                raise AssertionError('Unexpected compiler CFG cycle')
            visiting.add(pc)
            node = graph[pc]
            if metric == 'instructions':
                own = len(node['pcs'])
            else:
                forms = READS | WRITES | {'movb_disp_load', 'movb_disp_store', 'movb_indexed_load', 'movl_indexed_load'}
                own = sum(self.decode(p)[1].name in forms for p in node['pcs'])
            if node['call']:
                own += self.bound(node['call'], metric)
            result = own + max((walk(target) for target in node['next']), default=0)
            visiting.remove(pc)
            return result
        return walk(entry)

    def report(self):
        rows = {}
        for name, entry in ENTRY.items():
            function = self.graph(entry)
            pcs = sorted({p for node in function['graph'].values() for p in node['pcs']})
            rows[name] = dict(entry=f'{entry:08X}', code_end_exclusive=f'{BOUNDS[entry]:08X}',
                instructions=[dict(pc=f'{p:08X}', word=f'{self.decode(p)[0]:04X}', form=self.decode(p)[1].name) for p in pcs],
                calls=function['calls'], terminals=function['terminals'],
                local_frame_bytes=max(n['peak'] for n in function['graph'].values()),
                peak_stack_bytes=self.stack_peak(entry), instruction_upper=self.bound(entry),
                memory_access_upper=self.bound(entry, 'memory_accesses'), balanced_all_paths=True,
                cfg=[dict(pc=f'{pc:08X}', next=[f'{t:08X}' for t in n['next']],
                          call=f'{n["call"]:08X}' if n['call'] else None,
                          frame_before=n['depth_before'], frame_after=n['depth_after']) for pc, n in sorted(function['graph'].items())])
        return dict(status='PASS', build=str(BUILD), payload_sha256=self.manifest['artifacts']['m06.EXPERIMENTAL.code.bin'],
                    functions=rows, recursion=False, loops=False, persistent_RAM_bytes=0,
                    graph='default_hook -> match; refill_hook -> refill -> match,page',
                    new_background_hook=False, task9_pool_original='000147AC',
                    caveat='Rejected SSM traffic still executes rejection adapters. No page sampling occurs unless exact request and active response identity match.',
                    preservation=dict(default='R1,R4..R15,SR,PR restored; R0 executes original replay or accepted response writes; R2/R3 overwritten by OEM at484C0/484BC before use.',
                                      refill='R1,R2,R3,R5..R15,SR,PR restored; R0/R4 are caller-clobbered original scratch/argument registers.',
                                      controls='No reachable instruction accesses MACH/MACL,GBR,VBR,FR0..FR15,FPUL,FPSCR.',
                                      assumptions='Writable private stack, writable OEM output context; interrupts/peripherals must preserve architectural context. No physical timing claim.'),
                    timing_formula='C <= 5*N + (F-1)*N + (D-1)*A + entry_stalls + external_interference',
                    timing_gate='PHYSICAL/BENCH REQUIRED')
