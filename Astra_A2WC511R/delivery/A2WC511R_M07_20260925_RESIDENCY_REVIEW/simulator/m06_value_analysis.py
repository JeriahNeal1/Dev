"""Conservative value-set transfer infrastructure, separate from concrete SH-2E core.

No absence-of-hit allocation theorem is emitted. Unmodeled instructions, asynchronous
hardware, unknown transfer targets, symbolic fetches and bounded-work cutoffs explicitly
make the global exclusion gate FAIL and denote universal downstream behavior.
"""
from dataclasses import dataclass, field
from collections import deque, Counter
from itertools import product
from hashlib import sha256
from pathlib import Path
import json

from sh2e import OPCODES, MASK32, ROM_SIZE, RAM_START, RAM_END, sx, div1_step

SET_CAP = 8
ENUM_CAP = 64


@dataclass(frozen=True)
class Value:
    """Nonempty finite set, inclusive unsigned interval, or TOP (all 32-bit values)."""
    kind: str
    data: tuple = ()

    @staticmethod
    def finite(values):
        values = tuple(sorted({v & MASK32 for v in values}))
        if not values:
            raise ValueError('Empty values require an unreachable state, never an empty target set')
        return Value('set', values) if len(values) <= SET_CAP else Value.interval(values[0], values[-1])

    @staticmethod
    def interval(lo, hi):
        if not 0 <= lo <= hi <= MASK32:
            return TOP
        if lo == 0 and hi == MASK32:
            return TOP
        if hi - lo < SET_CAP:
            return Value('set', tuple(range(lo, hi + 1)))
        return Value('range', (lo, hi))

    @property
    def bounds(self):
        return (0, MASK32) if self.kind == 'top' else (self.data[0], self.data[-1])

    def contains(self, n):
        n &= MASK32
        return n in self.data if self.kind == 'set' else self.bounds[0] <= n <= self.bounds[1]

    def enumerate(self, cap=ENUM_CAP):
        if self.kind == 'set':
            return self.data
        lo, hi = self.bounds
        return tuple(range(lo, hi + 1)) if hi - lo + 1 <= cap else None

    def join(self, other):
        if self == other:
            return self
        if self.kind == 'top' or other.kind == 'top':
            return TOP
        if self.kind == other.kind == 'set':
            return Value.finite(self.data + other.data)
        return Value.interval(min(self.bounds[0], other.bounds[0]), max(self.bounds[1], other.bounds[1]))

    def widen(self, other):
        joined = self.join(other)
        return self if joined == self else TOP

    def unary(self, fn, fallback=None):
        values = self.enumerate()
        return Value.finite(fn(v) for v in values) if values is not None else (fallback or TOP)

    def binary(self, other, fn, fallback=None):
        a, b = self.enumerate(), other.enumerate()
        if a is not None and b is not None and len(a) * len(b) <= ENUM_CAP:
            return Value.finite(fn(x, y) for x, y in product(a, b))
        return fallback or TOP

    def add(self, other):
        lo = self.bounds[0] + other.bounds[0]
        hi = self.bounds[1] + other.bounds[1]
        fallback = Value.interval(lo, hi) if hi <= MASK32 else TOP
        return self.binary(other, lambda a, b: a + b, fallback)

    def bitand(self, other):
        fallback = Value.interval(0, min(self.bounds[1], other.bounds[1]))
        return self.binary(other, lambda a, b: a & b, fallback)

    def compare(self, other, relation):
        return self.binary(other, lambda a, b: int(relation(a, b)), BOOL)

    def to_json(self):
        return dict(kind=self.kind, values=[f'{v:08X}' for v in self.data])


TOP = Value('top')
BOOL = Value('set', (0, 1))


def V(value):
    return Value.finite([value])


@dataclass
class State:
    r: list = field(default_factory=lambda: [TOP] * 16)
    pr: Value = TOP
    sr: Value = TOP
    mach: Value = TOP
    macl: Value = TOP
    memory: dict = field(default_factory=dict)  # known byte values only; absent means TOP

    def copy(self):
        return State(list(self.r), self.pr, self.sr, self.mach, self.macl, dict(self.memory))

    @property
    def t(self):
        return self.sr.bitand(V(1))

    def set_t(self, t):
        self.sr = self.sr.bitand(V(MASK32 ^ 1)).binary(t, lambda a, b: a | b)

    def join(self, other, widening=False):
        combine = (lambda a, b: a.widen(b)) if widening else (lambda a, b: a.join(b))
        memory = {a: combine(self.memory[a], other.memory[a]) for a in self.memory.keys() & other.memory.keys()}
        memory = {a: v for a, v in memory.items() if v != TOP}
        return State([combine(a, b) for a, b in zip(self.r, other.r)],
                     *(combine(getattr(self, k), getattr(other, k)) for k in ('pr', 'sr', 'mach', 'macl')),
                     memory)

    @staticmethod
    def fixture(registers=None, memory=None, **system):
        state = State()
        for reg, value in (registers or {}).items():
            state.r[reg] = value if isinstance(value, Value) else V(value)
        for key, value in system.items():
            setattr(state, key, value if isinstance(value, Value) else V(value))
        for address, payload in (memory or {}).items():
            for i, value in enumerate(payload):
                state.memory[address + i] = V(value)
        return state


class Analysis:
    """Worklist analysis; states keyed by PC and latched delay-slot continuation.

    Finite supported transfer paths are conservatively joined. Unknown-control edges
    denote all 32-bit successors without trying to enumerate them. Their universal
    downstream marker forbids treating the explored subgraph as a closed program.
    """
    def __init__(self, rom, allowed_exits=(), max_steps=20000, max_memory=512, widen_after=4):
        self.rom = rom
        self.allowed_exits = set(allowed_exits)
        self.max_steps, self.max_memory, self.widen_after = max_steps, max_memory, widen_after
        self.states, self.visits = {}, Counter()
        self.observations = {}  # (PC, mode, size) -> (addresses/targets, values)
        self.unknowns = set()
        self.decoded = Counter()
        self.steps = 0
        self.terminated = False
        self.run_started = False
        self.seed_count = 0

    def observe(self, pc, mode, addresses, size=0, value=TOP):
        key = (pc, mode, size)
        previous = self.observations.get(key)
        self.observations[key] = (previous[0].join(addresses), previous[1].join(value)) if previous else (addresses, value)

    def uncertain(self, pc, reason, universal=False):
        self.unknowns.add((pc, reason))
        if universal:
            self.observe(pc, 'unknown_downstream_target', TOP)
            self.observe(pc, 'unknown_downstream_ROM_read', TOP)
            self.observe(pc, 'unknown_downstream_RAM_write', TOP)

    def read(self, state, pc, addresses, size):
        values = addresses.enumerate()
        result = None
        if values is None:
            self.uncertain(pc, 'nonfinite_memory_read_address')
            self.observe(pc, 'read', addresses, size)
            return TOP
        for address in values:
            if address % size or address + size > 1 << 32:
                value = TOP
                self.uncertain(pc, 'possible_alignment_or_address_exception', universal=True)
            elif 0 <= address < address + size <= ROM_SIZE:
                value = V(int.from_bytes(self.rom.data[address:address + size], 'big'))
            elif RAM_START <= address < address + size <= RAM_END:
                value = V(0)
                for a in range(address, address + size):
                    value = value.binary(state.memory.get(a, TOP), lambda x, y: (x << 8) | y)
            else:
                value = TOP
                self.uncertain(pc, 'unmodeled_peripheral_or_memory_read', universal=True)
            result = value if result is None else result.join(value)
        self.observe(pc, 'read', addresses, size, result)
        return result

    def write(self, state, pc, addresses, size, value):
        self.observe(pc, 'write', addresses, size, value.bitand(V((1 << (size * 8)) - 1)))
        values = addresses.enumerate()
        if values is None:
            state.memory.clear()
            self.uncertain(pc, 'nonfinite_store_address_RAM_havoc', universal=True)
            return
        old = dict(state.memory)
        unsafe = False
        for address in values:
            if address % size or not RAM_START <= address < address + size <= RAM_END:
                # Peripheral writes can trigger DMA/flash commands; do not model as benign.
                state.memory.clear()
                unsafe = True
                self.uncertain(pc, 'possible_ROM_peripheral_or_exception_write', universal=True)
                continue
            for i in range(size):
                byte = value.unary(lambda x: (x >> (8 * (size - i - 1))) & 255, Value.interval(0, 255))
                a = address + i
                if len(values) != 1:
                    byte = old.get(a, TOP).join(state.memory.get(a, TOP)).join(byte)
                if byte == TOP:
                    state.memory.pop(a, None)
                else:
                    state.memory[a] = byte
        if unsafe:
            state.memory.clear()
        if len(state.memory) > self.max_memory:
            state.memory.clear()
            self.uncertain(pc, 'abstract_RAM_cell_budget_havoc')

    def transfer(self, pc, pending, original):
        state = original.copy()
        if not 0 <= pc < pc + 2 <= ROM_SIZE or pc & 1:
            self.uncertain(pc, 'unmodeled_fetch_or_exception', universal=True)
            return []
        word = int.from_bytes(self.rom.data[pc:pc + 2], 'big')
        self.observe(pc, 'fetch', V(pc), 2, V(word))
        spec = next((s for s in OPCODES if word & s.mask == s.value), None)
        if spec is None or pending is not None and (spec.branch or spec.name in ('movw_pc', 'movl_pc')):
            self.uncertain(pc, f'opaque_instruction_{word:04X}', universal=True)
            self.decoded['OPAQUE'] += 1
            # Opaque architectural effects are all TOP. Fallthrough is extra exploration;
            # the universal frontier, not this one edge, represents possible control flow.
            state = State()
            return [(pending if pending is not None else (pc + 2) & MASK32, None, state)]
        name = spec.name
        self.decoded[name] += 1
        n, m, imm = word >> 8 & 15, word >> 4 & 15, word & 255
        if spec.branch:
            if name.startswith(('bf', 'bt')):
                target = (pc + 4 + 2 * sx(imm, 8)) & MASK32
                successors = []
                for t in (0, 1):
                    if not state.t.contains(t):
                        continue
                    taken = t == int(name.startswith('bt'))
                    refined = state.copy()
                    refined.set_t(V(t))
                    self.observe(pc, 'target', V(target if taken else pc + 2))
                    successors.append((pc + 2, target, refined) if taken and name.endswith('_s')
                                      else (target if taken else pc + 2, None, refined))
                return successors
            if name in ('bra', 'bsr'):
                targets = V(pc + 4 + 2 * sx(word & 4095, 12))
            elif name in ('jmp', 'jsr'):
                targets = state.r[n]
            else:
                targets = state.pr
            self.observe(pc, 'target', targets)
            if name in ('bsr', 'jsr'):
                state.pr = V(pc + 4)
            addresses = targets.enumerate()
            if addresses is None:
                self.uncertain(pc, 'universal_indirect_control_frontier', universal=True)
                # Execute delay-slot effects before marking the downstream PC unknown.
                self.transfer(pc + 2, 0, state)
                return []
            return [(pc + 2, a, state.copy()) for a in addresses]
        if name == 'nop':
            pass
        elif name in ('clrt', 'sett'):
            state.set_t(V(int(name == 'sett')))
        elif name == 'movt':
            state.r[n] = state.t
        elif name == 'stc_sr_reg':
            state.r[n] = state.sr
        elif name == 'ldc_sr_reg':
            state.sr = state.r[n].bitand(V(0x0FFF0FFF))
        elif name == 'mov_imm':
            state.r[n] = V(sx(imm, 8))
        elif name == 'mov_reg':
            state.r[n] = state.r[m]
        elif name in ('add_imm', 'add_reg'):
            state.r[n] = state.r[n].add(V(sx(imm, 8)) if name == 'add_imm' else state.r[m])
        elif name == 'sub_reg':
            state.r[n] = state.r[n].binary(state.r[m], lambda a, b: a - b)
        elif name in ('subc', 'addc', 'div0s', 'div1', 'rotcl'):
            left, right, sr_values = state.r[n].enumerate(), state.r[m].enumerate(), state.sr.enumerate()
            if left is None or right is None or sr_values is None or len(left) * len(right) * len(sr_values) > ENUM_CAP:
                if name != 'div0s':
                    state.r[n] = TOP
                state.sr = TOP
            else:
                results, statuses = [], []
                for a, b, sr in product(left, right, sr_values):
                    if name == 'div1':
                        value, status = div1_step(a, b, sr, n == m)
                    elif name == 'div0s':
                        q, mode = a >> 31, b >> 31
                        value, status = a, (sr & ~0x301) | (q << 8) | (mode << 9) | (q ^ mode)
                    elif name == 'rotcl':
                        value, status = (a << 1) | (sr & 1), (sr & ~1) | (a >> 31)
                    else:
                        value = a - b - (sr & 1) if name == 'subc' else a + b + (sr & 1)
                        carry = a < b + (sr & 1) if name == 'subc' else value > MASK32
                        status = (sr & ~1) | int(carry)
                    results.append(value); statuses.append(status)
                state.r[n], state.sr = Value.finite(results), Value.finite(statuses)
        elif name in ('and_imm', 'or_imm'):
            state.r[0] = state.r[0].bitand(V(imm)) if name == 'and_imm' else state.r[0].binary(V(imm), lambda a, b: a | b)
        elif name in ('movb_disp_load', 'movb_disp_store'):
            address = state.r[m].add(V(word & 15))
            if name == 'movb_disp_load':
                state.r[0] = self.read(state, pc, address, 1).unary(lambda v: sx(v, 8))
            else:
                self.write(state, pc, address, 1, state.r[0])
        elif name in ('movb_indexed_load', 'movl_indexed_load'):
            size = 1 if name == 'movb_indexed_load' else 4
            value = self.read(state, pc, state.r[0].add(state.r[m]), size)
            state.r[n] = value.unary(lambda v: sx(v, 8)) if size == 1 else value
        elif name == 'movb_indexed_store':
            self.write(state, pc, state.r[0].add(state.r[n]), 1, state.r[m])
        elif name in ('movw_pc', 'movl_pc'):
            size = 2 if name == 'movw_pc' else 4
            address = ((pc + 4) & ~(size - 1)) + imm * size
            value = self.read(state, pc, V(address), size)
            state.r[n] = value.unary(lambda v: sx(v, 16)) if size == 2 else value
        elif name in ('movb_load', 'movw_load', 'movl_load', 'movb_postinc', 'movl_postinc', 'movl_load_disp'):
            size = 1 if name in ('movb_load', 'movb_postinc') else 2 if name == 'movw_load' else 4
            address = state.r[m].add(V(4 * (word & 15))) if name == 'movl_load_disp' else state.r[m]
            value = self.read(state, pc, address, size)
            old_m = state.r[m]
            state.r[n] = value.unary(lambda v: sx(v, size * 8)) if size < 4 else value
            if name.endswith('postinc') and n != m:
                state.r[m] = old_m.add(V(size))
        elif name in ('movb_store', 'movw_store', 'movl_store', 'movl_predec', 'movl_store_disp'):
            size = 1 if name == 'movb_store' else 2 if name == 'movw_store' else 4
            value = state.r[m]
            if name == 'movl_predec':
                state.r[n] = state.r[n].add(V(-4))
            address = state.r[n].add(V(4 * (word & 15))) if name == 'movl_store_disp' else state.r[n]
            self.write(state, pc, address, size, value)
        elif name in ('and_reg', 'or_reg'):
            state.r[n] = state.r[n].bitand(state.r[m]) if name == 'and_reg' else state.r[n].binary(state.r[m], lambda a, b: a | b)
        elif name in ('extub', 'extuw'):
            state.r[n] = state.r[m].bitand(V(255 if name == 'extub' else 65535))
        elif name == 'extsb':
            state.r[n] = state.r[m].unary(lambda v: sx(v & 255, 8))
        elif name == 'neg':
            state.r[n] = state.r[m].unary(lambda a: -a)
        elif name == 'negc':
            a, t = state.r[m], state.t
            state.r[n] = a.binary(t, lambda x, y: -x - y)
            state.set_t(a.compare(t, lambda x, y: x != 0 or y != 0))
        elif name in ('shll', 'shll2', 'shll8', 'shll16', 'shlr2', 'shar'):
            value = state.r[n]
            fn = {'shll': lambda a: a << 1, 'shll2': lambda a: a << 2,
                  'shll8': lambda a: a << 8, 'shll16': lambda a: a << 16,
                  'shlr2': lambda a: a >> 2, 'shar': lambda a: sx(a, 32) >> 1}[name]
            state.r[n] = value.unary(fn)
            if name == 'shll':
                state.set_t(value.unary(lambda a: a >> 31, BOOL))
            elif name == 'shar':
                state.set_t(value.bitand(V(1)))
        elif name == 'dt':
            state.r[n] = state.r[n].add(V(-1))
            state.set_t(state.r[n].compare(V(0), lambda a, b: a == b))
        elif name in ('cmpeq_reg', 'cmpeq_imm', 'cmphi', 'cmphs', 'cmpge', 'cmpgt', 'tst_reg', 'tst_imm'):
            a = state.r[0] if name.endswith('imm') else state.r[n]
            b = V(sx(imm, 8)) if name == 'cmpeq_imm' else V(imm) if name == 'tst_imm' else state.r[m]
            fn = {'cmpeq_reg': lambda a, b: a == b, 'cmpeq_imm': lambda a, b: a == b,
                  'cmphi': lambda a, b: a > b, 'cmphs': lambda a, b: a >= b,
                  'cmpge': lambda a, b: sx(a, 32) >= sx(b, 32),
                  'cmpgt': lambda a, b: sx(a, 32) > sx(b, 32),
                  'tst_reg': lambda a, b: a & b == 0, 'tst_imm': lambda a, b: a & b == 0}[name]
            state.set_t(a.compare(b, fn))
        elif name.endswith('_push'):
            key = name.split('_')[1]
            state.r[n] = state.r[n].add(V(-4))
            self.write(state, pc, state.r[n], 4, getattr(state, key))
        elif name.endswith('_pop'):
            key = name.split('_')[1]
            value = self.read(state, pc, state.r[n], 4)
            setattr(state, key, value.bitand(V(0x0FFF0FFF)) if key == 'sr' else value)
            state.r[n] = state.r[n].add(V(4))
        else:
            raise AssertionError(f'Listed opcode lacks abstract transfer: {name}')
        return [(pending if pending is not None else (pc + 2) & MASK32, None, state)]

    def run(self, seeds):
        if self.run_started:
            raise ValueError('Use a fresh Analysis for each explicit seed contract')
        self.run_started = True
        seeds = list(seeds)
        self.seed_count = len(seeds)
        if not seeds:
            self.uncertain(-1, 'empty_seed_contract', universal=True)
        work = deque()
        for pc, state in seeds:
            key = (pc, None)
            if key in self.states:
                self.states[key] = self.states[key].join(state)
            else:
                self.states[key] = state.copy()
            work.append(key)
        while work and self.steps < self.max_steps:
            key = work.popleft()
            pc, pending = key
            if pc in self.allowed_exits and pending is None:
                continue
            state = self.states[key]
            self.steps += 1
            for next_pc, next_pending, new in self.transfer(pc, pending, state):
                out = (next_pc, next_pending)
                if out in self.states:
                    self.visits[out] += 1
                    new = self.states[out].join(new, self.visits[out] > self.widen_after)
                    if new == self.states[out]:
                        continue
                self.states[out] = new
                work.append(out)
        self.terminated = not work
        if work:
            self.uncertain(-1, 'worklist_budget_cutoff_universal_remaining_paths', universal=True)
        return self

    def exclusion(self, start, end, mode):
        if not 0 <= start < end <= 1 << 32:
            raise ValueError('Invalid half-open exclusion interval')
        matches = []
        for (pc, observed_mode, size), (addresses, value) in self.observations.items():
            if observed_mode != mode:
                continue
            addresses_list = addresses.enumerate()
            possible = (any(a < end and a + max(1, size) > start for a in addresses_list) if addresses_list is not None
                        else addresses.bounds[0] < end and addresses.bounds[1] + max(1, size) > start)
            if possible:
                matches.append(dict(pc=f'{pc:08X}', mode=mode, size=size, addresses=addresses.to_json()))
        # All uncertainty prevents a global exclusion claim, including assumptions
        # that might not affect this particular interval without additional proof.
        valid_run = self.run_started and self.seed_count > 0 and self.terminated and self.steps > 0
        return dict(status='FAIL' if matches or self.unknowns or not valid_run else 'PASS', possible_accesses=matches,
                    unknown_count=len(self.unknowns), scope='Only the explicitly seeded, modeled execution contract')

    def check_concrete(self, memory_events=(), branch_edges=(), trace=()):
        checked = Counter()
        failures = []
        for event in memory_events:
            pc = int(event['pc'], 16)
            mode = 'read' if event['mode'] == 'r' else 'write'
            key = (pc, mode, event['size'])
            prediction = self.observations.get(key)
            if prediction is None or not prediction[0].contains(int(event['address'], 16)) or not prediction[1].contains(int(event['value'], 16)):
                failures.append(dict(kind='memory', event=event))
            checked['memory_events'] += 1
        for pc, target, taken in branch_edges:
            prediction = self.observations.get((pc, 'target', 0))
            if prediction is None or not prediction[0].contains(target):
                failures.append(dict(kind='branch', pc=pc, target=target, taken=taken))
            checked['branch_edges'] += 1
        for event in trace:
            pc = int(event['pc'], 16)
            if (pc, 'fetch', 2) not in self.observations:
                failures.append(dict(kind='fetch', pc=pc))
            checked['fetches'] += 1
        return dict(status='FAIL' if failures else 'PASS', checked=dict(checked), failures=failures)

    def report(self):
        return dict(schema=1, rom=self.rom.identity(), steps=self.steps, states=len(self.states),
                    run_started=self.run_started, seed_count=self.seed_count, worklist_complete=self.terminated,
                    global_exclusion_gate='FAIL' if self.unknowns or not (self.run_started and self.seed_count > 0 and self.terminated and self.steps > 0) else 'PASS',
                    contract='Global means only explicit seeds/initial-state/hardware assumptions. Whole-firmware acceptance additionally requires exhaustive entry/hardware manifests.',
                    unknowns=[dict(pc=f'{pc:08X}' if pc >= 0 else 'GLOBAL', reason=reason) for pc, reason in sorted(self.unknowns)],
                    decoded=dict(self.decoded), observations=[dict(pc=f'{pc:08X}' if pc >= 0 else 'GLOBAL', mode=mode, size=size,
                        addresses=addresses.to_json(), value=value.to_json()) for (pc, mode, size), (addresses, value) in sorted(self.observations.items())])


def metadata_audit():
    overlaps = []
    for word in range(65536):
        matches = [s.name for s in OPCODES if word & s.mask == s.value]
        if len(matches) > 1:
            overlaps.append(dict(word=f'{word:04X}', matches=matches))
    return dict(status='FAIL' if overlaps else 'PASS', forms=len(OPCODES), exhaustive_words=65536,
                overlaps=overlaps, source_sha256=sha256(Path(__file__).with_name('sh2e.py').read_bytes()).hexdigest(),
                scope='Decode-mask disjointness only; architectural semantics require transfer regression/manual evidence')
