"""Narrow, fail-closed SH-2E integer function interpreter (not an ECU simulator).

Original implementation. Architectural reference: Renesas REJ09B0316-0200,
SH-2E Software Manual, Rev. 2.00. No vendor simulator code is incorporated.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json

MASK32 = 0xFFFFFFFF
ROM_SIZE = 0x100000
RAM_START, RAM_END = 0xFFFF0000, 0xFFFFC000
STOCK_SHA256 = "22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218"


class SimulationStop(RuntimeError):
    """A visible failure; no unsupported behavior is silently substituted."""


def sx(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def hx(value):
    return f"{value:08X}"


def div1_step(dividend, divisor, sr, same_register=False):
    """One architectural DIV1 step, including SR.Q/M/T (manual7.2.18)."""
    old_q, mode = (sr >> 8) & 1, (sr >> 9) & 1
    shifted = ((dividend << 1) | (sr & 1)) & MASK32
    if same_register:
        divisor = shifted
    subtract = old_q == mode
    result = (shifted - divisor if subtract else shifted + divisor) & MASK32
    carry_or_borrow = int(result > shifted if subtract else result < shifted)
    new_q = (dividend >> 31) ^ carry_or_borrow ^ mode
    new_sr = (sr & ~0x101) | (new_q << 8) | int(new_q == mode)
    return result, new_sr


@dataclass(frozen=True)
class ROM:
    data: bytes
    source: str
    base_sha256: str
    overlays: tuple = ()

    def __post_init__(self):
        if type(self.data) is not bytes or len(self.data) != ROM_SIZE:
            raise ValueError("ROM must be immutable bytes of exactly 1 MiB")

    @classmethod
    def load(cls, path, expected_sha256):
        path = Path(path).resolve()
        data = path.read_bytes()
        digest = sha256(data).hexdigest()
        if digest != expected_sha256:
            raise SimulationStop(f"ROM identity mismatch: {digest} != {expected_sha256}")
        return cls(data, str(path), digest)

    @classmethod
    def synthetic(cls, data, label):
        if not label:
            raise ValueError("Synthetic ROMs require an explicit label")
        return cls(bytes(data), "SYNTHETIC: " + label, sha256(data).hexdigest())

    @property
    def sha256(self):
        return sha256(self.data).hexdigest()

    def with_overlay(self, address, payload, label):
        if not label or not payload or address < 0 or address + len(payload) > ROM_SIZE:
            raise ValueError("Overlay requires label and an in-ROM nonempty span")
        data = self.data[:address] + bytes(payload) + self.data[address + len(payload):]
        record = (hx(address), bytes(payload).hex(), label)
        return ROM(data, self.source, self.base_sha256, self.overlays + (record,))

    def identity(self):
        return dict(source=self.source, sha256=self.sha256,
                    base_sha256=self.base_sha256, overlays=self.overlays, size=len(self.data))


class Memory:
    """Big-endian ROM/RAM only. RAM reads require explicit fixture initialization."""

    def __init__(self, rom):
        self.rom = rom
        self.ram = bytearray(RAM_END - RAM_START)
        self.initialized = bytearray(len(self.ram))
        self.origins = {}
        self.events = []
        self.watchpoints = []
        self.protected = []
        self.write_allowlist = None
        self.pc = None
        self.call_context = []
        self.in_delay_slot = False
        self.control_sources = set()

    @staticmethod
    def _check(address, size):
        if size not in (1, 2, 4) or address < 0 or address + size > (1 << 32):
            raise SimulationStop(f"Invalid memory access {address:#x}+{size}")
        if address % size:
            raise SimulationStop(f"Unaligned memory access {address:#010x}+{size}")

    def watch(self, start, end, name, modes="rw"):
        if not start < end or set(modes) - set("rw"):
            raise ValueError("Invalid watchpoint")
        self.watchpoints.append((start, end, name, modes))

    def _event(self, mode, address, size, value, sources, address_sources):
        self.events.append(dict(mode=mode, address=hx(address), size=size, value=hx(value),
                                pc=hx(self.pc) if self.pc is not None else None,
                                call_context=list(self.call_context), delay_slot=self.in_delay_slot,
                                value_sources=sorted(sources), address_sources=sorted(address_sources),
                                control_sources=sorted(self.control_sources),
                                watchpoints=[name for start, end, name, modes in self.watchpoints
                                             if mode in modes and address < end and address + size > start]))

    def initialize(self, address, payload):
        """Fixture-only RAM setup, never an emulated write or claimed ECU sample."""
        if self.pc is not None:
            raise SimulationStop("Cannot inject fixture data during execution")
        payload = bytes(payload)
        if not RAM_START <= address < address + len(payload) <= RAM_END:
            raise SimulationStop("Fixture initialization must be inside RAM")
        offset = address - RAM_START
        self.ram[offset:offset + len(payload)] = payload
        self.initialized[offset:offset + len(payload)] = b"\x01" * len(payload)
        for i in range(len(payload)):
            self.origins.pop(address + i, None)

    def read(self, address, size, address_sources=(), fetch=False):
        self._check(address, size)
        if 0 <= address < address + size <= ROM_SIZE:
            payload = self.rom.data[address:address + size]
            sources = {f"rom:{hx(address)}"}
        elif RAM_START <= address < address + size <= RAM_END:
            if fetch:
                raise SimulationStop("RAM instruction execution is not supported")
            offset = address - RAM_START
            if not all(self.initialized[offset:offset + size]):
                raise SimulationStop(f"Uninitialized RAM read {address:#010x}+{size}")
            payload = self.ram[offset:offset + size]
            sources = {f"ram:{hx(address + i)}" for i in range(size)}
            for i in range(size):
                sources.update(self.origins.get(address + i, ()))
        else:
            raise SimulationStop(f"Unmapped/peripheral access unsupported: {address:#010x}+{size}")
        value = int.from_bytes(payload, "big")
        if not fetch:
            self._event("r", address, size, value, sources, address_sources)
        return value, sources

    def write(self, address, size, value, sources=(), address_sources=()):
        self._check(address, size)
        if 0 <= address < ROM_SIZE:
            raise SimulationStop(f"Read-only ROM write {address:#010x}")
        if not RAM_START <= address < address + size <= RAM_END:
            raise SimulationStop(f"Unmapped/peripheral write unsupported: {address:#010x}+{size}")
        if any(address < end and address + size > start for start, end in self.protected):
            raise SimulationStop(f"Stack guard/reserved-memory collision at {address:#010x}")
        if self.write_allowlist is not None and not any(start <= address and address + size <= end
                                                       for start, end in self.write_allowlist):
            raise SimulationStop(f"Undeclared RAM write {address:#010x}+{size}")
        value &= (1 << (size * 8)) - 1
        offset = address - RAM_START
        self.ram[offset:offset + size] = value.to_bytes(size, "big")
        self.initialized[offset:offset + size] = b"\x01" * size
        for i in range(size):
            self.origins[address + i] = set(sources)
        self._event("w", address, size, value, sources, address_sources)


@dataclass(frozen=True)
class Opcode:
    name: str
    mask: int
    value: int
    branch: bool = False


# The decoder and generated supported-opcode report use this same table.
OPCODES = (
    Opcode("nop", 0xFFFF, 0x0009), Opcode("rts", 0xFFFF, 0x000B, True),
    Opcode("clrt", 0xFFFF, 0x0008), Opcode("sett", 0xFFFF, 0x0018),
    Opcode("movt", 0xF0FF, 0x0029), Opcode("mov_imm", 0xF000, 0xE000),
    Opcode("add_imm", 0xF000, 0x7000), Opcode("movl_pc", 0xF000, 0xD000),
    Opcode("movw_pc", 0xF000, 0x9000), Opcode("movb_load", 0xF00F, 0x6000),
    Opcode("movw_load", 0xF00F, 0x6001), Opcode("movl_load", 0xF00F, 0x6002),
    Opcode("mov_reg", 0xF00F, 0x6003), Opcode("movb_store", 0xF00F, 0x2000),
    Opcode("movw_store", 0xF00F, 0x2001), Opcode("movl_store", 0xF00F, 0x2002),
    Opcode("and_reg", 0xF00F, 0x2009), Opcode("extub", 0xF00F, 0x600C), Opcode("extuw", 0xF00F, 0x600D),
    Opcode("cmpeq_reg", 0xF00F, 0x3000), Opcode("cmpeq_imm", 0xFF00, 0x8800),
    Opcode("tst_reg", 0xF00F, 0x2008), Opcode("tst_imm", 0xFF00, 0xC800),
    Opcode("shar", 0xF0FF, 0x4021), Opcode("neg", 0xF00F, 0x600B),
    Opcode("bf_s", 0xFF00, 0x8F00, True), Opcode("bt_s", 0xFF00, 0x8D00, True),
    Opcode("bf", 0xFF00, 0x8B00, True), Opcode("bt", 0xFF00, 0x8900, True),
    Opcode("bra", 0xF000, 0xA000, True), Opcode("bsr", 0xF000, 0xB000, True),
    Opcode("jmp", 0xF0FF, 0x402B, True), Opcode("jsr", 0xF0FF, 0x400B, True),
    Opcode("sts_pr_push", 0xF0FF, 0x4022), Opcode("lds_pr_pop", 0xF0FF, 0x4026),
    Opcode("movl_predec", 0xF00F, 0x2006), Opcode("movl_postinc", 0xF00F, 0x6006),
    Opcode("movb_postinc", 0xF00F, 0x6004), Opcode("movl_store_disp", 0xF000, 0x1000),
    Opcode("movl_load_disp", 0xF000, 0x5000), Opcode("add_reg", 0xF00F, 0x300C),
    Opcode("or_reg", 0xF00F, 0x200B), Opcode("cmphi", 0xF00F, 0x3006),
    Opcode("cmphs", 0xF00F, 0x3002),
    Opcode("cmpge", 0xF00F, 0x3003),
    Opcode("shlr2", 0xF0FF, 0x4009), Opcode("dt", 0xF0FF, 0x4010),
    Opcode("shll", 0xF0FF, 0x4000), Opcode("shll2", 0xF0FF, 0x4008),
    Opcode("negc", 0xF00F, 0x600A),
    Opcode("stc_sr_push", 0xF0FF, 0x4003), Opcode("ldc_sr_pop", 0xF0FF, 0x4007),
    Opcode("sts_mach_push", 0xF0FF, 0x4002), Opcode("lds_mach_pop", 0xF0FF, 0x4006),
    Opcode("sts_macl_push", 0xF0FF, 0x4012), Opcode("lds_macl_pop", 0xF0FF, 0x4016),
    Opcode("movb_indexed_load", 0xF00F, 0x000C), Opcode("movl_indexed_load", 0xF00F, 0x000E),
    Opcode("sub_reg", 0xF00F, 0x3008),
    Opcode("movb_disp_load", 0xFF00, 0x8400), Opcode("movb_disp_store", 0xFF00, 0x8000),
    Opcode("and_imm", 0xFF00, 0xC900), Opcode("or_imm", 0xFF00, 0xCB00),
    Opcode("extsb", 0xF00F, 0x600E),
    Opcode("movb_indexed_store", 0xF00F, 0x0004),
    Opcode("cmpgt", 0xF00F, 0x3007),
    Opcode("div0s", 0xF00F, 0x2007), Opcode("div1", 0xF00F, 0x3004),
    Opcode("subc", 0xF00F, 0x300A), Opcode("addc", 0xF00F, 0x300E),
    Opcode("rotcl", 0xF0FF, 0x4024),
    Opcode("shll8", 0xF0FF, 0x4018), Opcode("shll16", 0xF0FF, 0x4028),
    Opcode("stc_sr_reg", 0xF0FF, 0x0002), Opcode("ldc_sr_reg", 0xF0FF, 0x400E),
)


class CPU:
    """Listed integer instructions; SR storage/T logic; no interrupts/FPU/peripherals."""

    def __init__(self, memory, execution_ranges, stack_bounds):
        self.memory = memory
        self.execution_ranges = tuple(execution_ranges)
        self.stack_bounds = stack_bounds
        self.r = [0] * 16
        self.sources = [set() for _ in range(16)]
        self.pc, self.pr, self.t = 0, 0, 0
        self.sr_other, self.mach, self.macl = 0, 0, 0
        self.system_sources = {"sr": set(), "mach": set(), "macl": set()}
        self.pr_sources, self.t_sources = set(), set()
        self.trace = []
        self.branch_edges = set()
        self.pending = None
        self.call_context = []
        self.returned = False
        self.opcodes_seen = set()
        self.control_sources = set()
        self.track_control_sources = True

    @property
    def sr(self):
        return self.sr_other | self.t

    def _set_system(self, name, value, sources):
        if name == "sr":
            # REJ09B0316-0200 LDC.L pseudocode mask. Interrupt effects are not modeled.
            value &= 0x0FFF0FFF
            self.sr_other = value & ~1
            self._t(value & 1, sources)
        else:
            setattr(self, name, value & MASK32)
        self.system_sources[name] = set(sources)

    def _reg(self, number, value, sources):
        value &= MASK32
        if number == 15:
            low, high = self.stack_bounds
            if value % 4 or not low <= value <= high:
                raise SimulationStop(f"Stack pointer outside declared aligned bounds: {value:#010x}")
        self.r[number] = value
        self.sources[number] = set(sources)

    def _t(self, value, sources):
        self.t = int(bool(value))
        self.t_sources = set(sources)

    def step(self):
        pc = self.pc
        if not any(start <= pc and pc + 2 <= end for start, end in self.execution_ranges):
            raise SimulationStop(f"PC escaped declared execution ranges: {pc:#010x}")
        self._reg(15, self.r[15], self.sources[15])
        op, _ = self.memory.read(pc, 2, fetch=True)
        spec = next((x for x in OPCODES if op & x.mask == x.value), None)
        if spec is None:
            raise SimulationStop(f"Unsupported SH-2E opcode {op:04X} at {pc:08X}")
        slot = self.pending
        if slot and spec.branch:
            raise SimulationStop(f"Illegal branch in delay slot at {pc:08X}")
        if slot and spec.name in ("movw_pc", "movl_pc"):
            raise SimulationStop(f"PC-relative load in delay slot not implemented at {pc:08X}")
        self.pending = None
        self.memory.pc = pc
        self.memory.call_context = list(self.call_context)
        self.memory.in_delay_slot = bool(slot)
        self.memory.control_sources = set(self.control_sources)
        before = list(self.r)
        before_pr, before_t = self.pr, self.t
        before_system = {key: hx(getattr(self, key)) for key in ("sr", "mach", "macl")}
        n, m, imm = (op >> 8) & 15, (op >> 4) & 15, op & 255
        name = spec.name
        next_pc = (pc + 2) & MASK32
        const = {f"instruction:{hx(pc)}"}
        if name == "nop":
            pass
        elif name in ("clrt", "sett"):
            self._t(name == "sett", const)
        elif name == "movt":
            self._reg(n, self.t, self.t_sources)
        elif name == "stc_sr_reg":
            self._reg(n, self.sr, self.system_sources["sr"] | self.t_sources)
        elif name == "ldc_sr_reg":
            self._set_system("sr", self.r[n], self.sources[n])
        elif name == "mov_imm":
            self._reg(n, sx(imm, 8), const)
        elif name == "add_imm":
            self._reg(n, self.r[n] + sx(imm, 8), self.sources[n] | const)
        elif name == "add_reg":
            self._reg(n, self.r[n] + self.r[m], self.sources[n] | self.sources[m])
        elif name == "sub_reg":
            self._reg(n, self.r[n] - self.r[m], self.sources[n] | self.sources[m])
        elif name in ("subc", "addc"):
            left, right, carry = self.r[n], self.r[m], self.t
            origins = self.sources[n] | self.sources[m] | self.t_sources
            value = left - right - carry if name == "subc" else left + right + carry
            self._reg(n, value, origins)
            self._t(left < right + carry if name == "subc" else value > MASK32, origins)
        elif name == "rotcl":
            value, carry = self.r[n], self.t
            origins = self.sources[n] | self.t_sources
            self._reg(n, (value << 1) | carry, origins)
            self._t(value >> 31, origins)
        elif name == "div0s":
            q, mode = self.r[n] >> 31, self.r[m] >> 31
            origins = self.sources[n] | self.sources[m]
            self.sr_other = (self.sr_other & ~0x300) | (q << 8) | (mode << 9)
            self.system_sources["sr"].update(origins)
            self._t(q ^ mode, origins)
        elif name == "div1":
            origins = self.sources[n] | self.sources[m] | self.t_sources | self.system_sources["sr"]
            value, sr = div1_step(self.r[n], self.r[m], self.sr, n == m)
            self._reg(n, value, origins)
            self.sr_other = sr & ~1
            self.system_sources["sr"].update(origins)
            self._t(sr & 1, origins)
        elif name in ("and_imm", "or_imm"):
            value = self.r[0] & imm if name == "and_imm" else self.r[0] | imm
            self._reg(0, value, self.sources[0] | const)
        elif name in ("movb_disp_load", "movb_disp_store"):
            address = (self.r[m] + (op & 15)) & MASK32
            if name == "movb_disp_load":
                value, origins = self.memory.read(address, 1, self.sources[m] | const)
                self._reg(0, sx(value, 8), origins)
            else:
                self.memory.write(address, 1, self.r[0], self.sources[0], self.sources[m] | const)
        elif name in ("movb_indexed_load", "movl_indexed_load"):
            size = 1 if name == "movb_indexed_load" else 4
            address = (self.r[0] + self.r[m]) & MASK32
            value, origins = self.memory.read(address, size, self.sources[0] | self.sources[m])
            self._reg(n, sx(value, 8) if size == 1 else value, origins)
        elif name == "movb_indexed_store":
            address = (self.r[0] + self.r[n]) & MASK32
            self.memory.write(address, 1, self.r[m], self.sources[m], self.sources[0] | self.sources[n])
        elif name in ("movw_pc", "movl_pc"):
            size = 2 if name == "movw_pc" else 4
            address = ((pc + 4) & ~(size - 1)) + imm * size
            value, origins = self.memory.read(address, size, const)
            self._reg(n, sx(value, 16) if size == 2 else value, origins)
        elif name in ("movb_load", "movw_load", "movl_load"):
            size = {"movb_load": 1, "movw_load": 2, "movl_load": 4}[name]
            value, origins = self.memory.read(self.r[m], size, self.sources[m])
            self._reg(n, sx(value, size * 8) if size < 4 else value, origins)
        elif name in ("movb_store", "movw_store", "movl_store"):
            size = {"movb_store": 1, "movw_store": 2, "movl_store": 4}[name]
            self.memory.write(self.r[n], size, self.r[m], self.sources[m], self.sources[n])
        elif name == "movl_predec":
            value, origins = self.r[m], set(self.sources[m])
            self._reg(n, self.r[n] - 4, self.sources[n] | const)
            self.memory.write(self.r[n], 4, value, origins, self.sources[n])
        elif name in ("movl_postinc", "movb_postinc"):
            size = 4 if name == "movl_postinc" else 1
            value, origins = self.memory.read(self.r[m], size, self.sources[m])
            self._reg(n, sx(value, 8) if size == 1 else value, origins)
            if n != m:
                self._reg(m, self.r[m] + size, self.sources[m] | const)
        elif name == "movl_store_disp":
            address = (self.r[n] + 4 * (op & 15)) & MASK32
            self.memory.write(address, 4, self.r[m], self.sources[m], self.sources[n] | const)
        elif name == "movl_load_disp":
            address = (self.r[m] + 4 * (op & 15)) & MASK32
            value, origins = self.memory.read(address, 4, self.sources[m] | const)
            self._reg(n, value, origins)
        elif name == "mov_reg":
            self._reg(n, self.r[m], self.sources[m])
        elif name == "and_reg":
            self._reg(n, self.r[n] & self.r[m], self.sources[n] | self.sources[m])
        elif name == "or_reg":
            self._reg(n, self.r[n] | self.r[m], self.sources[n] | self.sources[m])
        elif name == "extub":
            self._reg(n, self.r[m] & 255, self.sources[m])
        elif name == "extuw":
            self._reg(n, self.r[m] & 65535, self.sources[m])
        elif name == "extsb":
            self._reg(n, sx(self.r[m] & 255, 8), self.sources[m])
        elif name == "neg":
            self._reg(n, -self.r[m], self.sources[m])
        elif name == "negc":
            value, borrow = self.r[m], self.t
            origins = self.sources[m] | self.t_sources
            self._reg(n, -value - borrow, origins)
            self._t(value != 0 or borrow != 0, origins)
        elif name == "shlr2":
            self._reg(n, self.r[n] >> 2, self.sources[n])
        elif name == "shll":
            value, origins = self.r[n], self.sources[n]
            self._reg(n, value << 1, origins)
            self._t(value >> 31, origins)
        elif name == "shll2":
            self._reg(n, self.r[n] << 2, self.sources[n])
        elif name in ("shll8", "shll16"):
            self._reg(n, self.r[n] << (8 if name == "shll8" else 16), self.sources[n])
        elif name == "dt":
            self._reg(n, self.r[n] - 1, self.sources[n] | const)
            self._t(self.r[n] == 0, self.sources[n])
        elif name == "shar":
            value, origins = self.r[n], self.sources[n]
            self._reg(n, sx(value, 32) >> 1, origins)
            self._t(value & 1, origins)
        elif name == "cmpeq_reg":
            self._t(self.r[n] == self.r[m], self.sources[n] | self.sources[m])
        elif name == "cmphi":
            self._t(self.r[n] > self.r[m], self.sources[n] | self.sources[m])
        elif name == "cmphs":
            self._t(self.r[n] >= self.r[m], self.sources[n] | self.sources[m])
        elif name == "cmpge":
            self._t(sx(self.r[n], 32) >= sx(self.r[m], 32), self.sources[n] | self.sources[m])
        elif name == "cmpgt":
            self._t(sx(self.r[n], 32) > sx(self.r[m], 32), self.sources[n] | self.sources[m])
        elif name == "cmpeq_imm":
            self._t(self.r[0] == (sx(imm, 8) & MASK32), self.sources[0] | const)
        elif name == "tst_reg":
            self._t((self.r[n] & self.r[m]) == 0, self.sources[n] | self.sources[m])
        elif name == "tst_imm":
            self._t((self.r[0] & imm) == 0, self.sources[0] | const)
        elif name == "sts_pr_push":
            self._reg(n, self.r[n] - 4, self.sources[n] | const)
            self.memory.write(self.r[n], 4, self.pr, self.pr_sources, self.sources[n])
        elif name == "lds_pr_pop":
            self.pr, self.pr_sources = self.memory.read(self.r[n], 4, self.sources[n])
            self._reg(n, self.r[n] + 4, self.sources[n] | const)
        elif name in ("stc_sr_push", "sts_mach_push", "sts_macl_push"):
            key = name.split("_")[1]
            origins = self.system_sources[key] | (self.t_sources if key == "sr" else set())
            self._reg(n, self.r[n] - 4, self.sources[n] | const)
            self.memory.write(self.r[n], 4, getattr(self, key), origins, self.sources[n])
        elif name in ("ldc_sr_pop", "lds_mach_pop", "lds_macl_pop"):
            key = name.split("_")[1]
            value, origins = self.memory.read(self.r[n], 4, self.sources[n])
            self._set_system(key, value, origins)
            self._reg(n, self.r[n] + 4, self.sources[n] | const)
        elif spec.branch:
            action = None
            if name in ("bf", "bt", "bf_s", "bt_s"):
                taken = self.t == int(name.startswith("bt"))
                target = (pc + 4 + 2 * sx(imm, 8)) & MASK32
                if self.track_control_sources:
                    self.control_sources.update(self.t_sources)
                self.branch_edges.add((pc, target if taken else pc + 2, taken))
                if taken:
                    if name.endswith("_s"):
                        self.pending = (target, action)
                    else:
                        next_pc = target
                # Not-taken BF/S or BT/S falls through, as in the manual pseudocode.
            else:
                if name in ("bra", "bsr"):
                    target = (pc + 4 + 2 * sx(op & 0xFFF, 12)) & MASK32
                elif name in ("jmp", "jsr"):
                    target = self.r[n]
                else:
                    target = self.pr
                    action = "return"
                if name in ("bsr", "jsr"):
                    self.pr, self.pr_sources = (pc + 4) & MASK32, const
                    action = "call"
                self.pending = (target, action)
                self.branch_edges.add((pc, target, True))
        else:
            raise AssertionError(f"Decode table has no implementation: {name}")
        self.opcodes_seen.add(name)
        self.trace.append(dict(pc=hx(pc), opcode=f"{op:04X}", instruction=name, delay_slot=bool(slot),
                               call_context=list(self.call_context),
                               registers={f"r{i}": hx(v) for i, v in enumerate(self.r) if v != before[i]},
                               t_before=before_t, t_after=self.t,
                               system_before=before_system,
                               system_after={key: hx(getattr(self, key)) for key in ("sr", "mach", "macl")},
                               pr_before=hx(before_pr), pr_after=hx(self.pr)))
        if slot:
            next_pc, action = slot
            if action == "call":
                self.call_context.append(hx(next_pc))
            elif action == "return":
                if not self.call_context:
                    raise SimulationStop("Return without an active function context")
                self.call_context.pop()
                self.returned = not self.call_context
        self.pc = next_pc


class FunctionHarness:
    """Explicit fixture and write/execute boundaries; ABI checks are caller-configured."""

    RETURN_SENTINEL = 0xFFFFFFFC

    def __init__(self, memory, execution_ranges, stack_pointer=0xFFFFBFA0, stack_size=0x400):
        self.memory = memory
        self.stack = (stack_pointer - stack_size, stack_pointer)
        low, high = self.stack
        if low - 16 < RAM_START or high + 16 > RAM_END or stack_size <= 0:
            raise ValueError("Invalid harness stack bounds")
        memory.initialize(low - 16, b"\xA5" * (stack_size + 32))
        memory.protected += [(low - 16, low), (high, high + 16)]
        self.cpu = CPU(memory, execution_ranges, self.stack)

    def run(self, entry, allowed_writes=(), registers=None, preserve=tuple(range(8, 16)), max_steps=1000,
            system_registers=None, preserve_system=("mach", "macl"), stop_at=None):
        cpu = self.cpu
        if cpu.trace:
            raise SimulationStop("Use a fresh harness per independent run")
        initial = {i: (0x10203040 + i * 0x01010101) & MASK32 for i in range(16)}
        initial[15] = self.stack[1]
        initial.update(registers or {})
        for i, value in initial.items():
            cpu._reg(i, value, {f"fixture:register:r{i}"})
        initial = list(cpu.r)
        system_initial = dict(sr=0x3F2, mach=0x89ABCDEF, macl=0x12345678)
        system_initial.update(system_registers or {})
        for key, value in system_initial.items():
            if key not in ("sr", "mach", "macl"):
                raise ValueError(f"Unsupported system register fixture {key}")
            cpu._set_system(key, value, {f"fixture:system:{key}"})
        system_initial = {key: getattr(cpu, key) for key in system_initial}
        cpu.pc, cpu.pr = entry, self.RETURN_SENTINEL
        cpu.pr_sources = {"harness:return_sentinel"}
        cpu.call_context = [hx(entry)]
        self.memory.write_allowlist = list(allowed_writes) + [self.stack]
        for _ in range(max_steps):
            cpu.step()
            if stop_at is not None and cpu.pc == stop_at and not cpu.pending:
                if cpu.returned or cpu.call_context != [hx(entry)]:
                    raise SimulationStop("Continuation reached with unexpected call context")
                break
            if cpu.returned:
                if stop_at is not None:
                    raise SimulationStop("Fragment returned before its declared continuation")
                if cpu.pc != self.RETURN_SENTINEL or cpu.pending:
                    raise SimulationStop("Function returned to an unexpected address")
                break
        else:
            raise SimulationStop(f"Instruction budget exceeded: {max_steps}")
        for i in preserve:
            if cpu.r[i] != initial[i]:
                raise SimulationStop(f"Configured preservation check failed for R{i}")
        expected_pr = self.RETURN_SENTINEL if stop_at is None else stop_at
        if cpu.pr != expected_pr:
            raise SimulationStop("PR boundary check failed")
        for key in preserve_system:
            if getattr(cpu, key) != system_initial[key]:
                raise SimulationStop(f"Configured system preservation check failed for {key}")
        for low, high in ((self.stack[0] - 16, self.stack[0]), (self.stack[1], self.stack[1] + 16)):
            if self.memory.ram[low - RAM_START:high - RAM_START] != b"\xA5" * 16:
                raise SimulationStop("Stack guard changed")
        self.memory.pc = None
        return dict(entry=hx(entry), steps=len(cpu.trace), registers=[hx(v) for v in cpu.r],
                    control_provenance_enabled=cpu.track_control_sources,
                    rom_sha256=self.memory.rom.sha256, base_rom_sha256=self.memory.rom.base_sha256,
                    preserved_registers=[f"r{i}" for i in preserve], pr_preserved=stop_at is None,
                    completion="function return" if stop_at is None else f"continuation {hx(stop_at)}",
                    pr_matches_boundary=True,
                    stack_pointer_restored=cpu.r[15] == initial[15],
                    system_registers={key: hx(getattr(cpu, key)) for key in ("sr", "mach", "macl", "pr")},
                    trace_sha256=sha256(json.dumps(cpu.trace, sort_keys=True).encode()).hexdigest(),
                    memory_trace_sha256=sha256(json.dumps(self.memory.events, sort_keys=True).encode()).hexdigest())
