"""Actual-image reset-prefix harness. Known hardware frontiers never count as boot success.

This module imports the frozen integer core without altering it. Peripheral behavior
is deliberately finite; unsupported reads/writes do not return a default value.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import gzip
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SIM = HERE.parent
CORE_SHA256 = "b47ac261634c116c3ffcdf19da9ec73e7014c034cd349ea8867f5f54895cdfff"
sys.path.insert(0, str(SIM))
import sh2e

MANUAL_URL = "https://www.renesas.com/en/document/mah/sh-2e-sh7058-f-ztat-tm-hardware-manual"
MODEL_ID = "SH7058_power_on_prefix_v1"


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Frontier(sh2e.SimulationStop):
    """An explicitly identified but unimplemented boundary, not a successful operation."""

    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class Scenario:
    name: str = "power_on_nmi_high_no_external_traffic"
    nmi_high: bool = True
    stack_low: int = 0xFFFF0000
    stack_high: int = 0xFFFFBFA0
    max_steps: int = 200000
    cycles_per_instruction: int = 16
    irq_at_step: int | None = None
    irq_priority: int = 1
    irq_is_nmi: bool = False
    reset_poison: int = 0xA5A50000
    sensor_profile: str = "unprovided"
    ram_power_on_byte: int | None = 0xA5
    can_idle_configuration: bool = True
    stop_on_timer_overflow: bool = False
    port_b_input_word: int = 0xFFFF

    def validate(self):
        if self.max_steps < 1 or not 1 <= self.cycles_per_instruction <= 1000000:
            raise ValueError("Positive bounded instruction and synthetic clock budgets required")
        if self.irq_at_step is not None and self.irq_at_step < 0:
            raise ValueError("IRQ scheduling is by nonnegative retired instruction count")
        if not 1 <= self.irq_priority <= 15:
            raise ValueError("Maskable interrupt priority must be 1..15")
        if self.sensor_profile not in ("unprovided", "open_circuit", "short_circuit"):
            raise ValueError("Unknown sensor scenario; no fabricated ADC values")
        if self.ram_power_on_byte is not None and not 0 <= self.ram_power_on_byte <= 255:
            raise ValueError("Explicit power-on RAM fixture byte must be0..255")
        if not 0 <= self.port_b_input_word <= 65535:
            raise ValueError("Explicit port-B pin fixture must fit16bits")
        if not sh2e.RAM_START <= self.stack_low < self.stack_high <= sh2e.RAM_END:
            raise ValueError("Explicit stack bounds must be inside SH7058 RAM")


# Only word writes actually used by AF0 are admitted. Reads of pin/data registers
# are not replaced by written latch values: input/output direction matters.
PORT_WRITES = {
    0xF720: "PAIOR", 0xF722: "PACRH", 0xF724: "PACRL", 0xF726: "PADR",
    0xF728: "PHIOR", 0xF72A: "PHCR", 0xF72C: "PHDR",
    0xF730: "PBIOR", 0xF732: "PBCRH", 0xF734: "PBCRL", 0xF736: "PBIR", 0xF738: "PBDR",
    0xF73A: "PCIOR", 0xF73C: "PCCR", 0xF73E: "PCDR",
    0xF740: "PDIOR", 0xF742: "PDCRH", 0xF744: "PDCRL", 0xF746: "PDDR",
    0xF748: "PFIOR", 0xF74A: "PFCRH", 0xF74C: "PFCRL", 0xF74E: "PFDR",
    0xF750: "PEIOR", 0xF752: "PECR", 0xF754: "PEDR",
    0xF756: "PLIOR", 0xF758: "PLCRH", 0xF75A: "PLCRL", 0xF75C: "PLIR", 0xF75E: "PLDR",
    0xF760: "PGIOR", 0xF762: "PGCR", 0xF764: "PGDR",
    0xF766: "PJIOR", 0xF768: "PJCRH", 0xF76A: "PJCRL", 0xF76C: "PJDR",
    0xF770: "PKIOR", 0xF772: "PKCRH", 0xF774: "PKCRL", 0xF776: "PKIR", 0xF778: "PKDR",
}
PORT_WRITES = {0xFFFF0000 | a: n for a, n in PORT_WRITES.items()}


class BootMemory(sh2e.Memory):
    def __init__(self, rom, scenario):
        super().__init__(rom)
        self.scenario = scenario
        self.mmio = {0xFFFFEC20: 0xF, 0xFFFFEC22: 0xFFFF,
                     0xFFFFEC24: 0x7777, 0xFFFFEC26: 0,
                     0xFFFFED18: 0, 0xFFFFF70B: 1,
                     0xFFFFD000: 1, 0xFFFFD002: 0xC}
        self.wdt = dict(tcsr=0x18, tcnt=0, rstcsr=0x1F, elapsed_cycles=0,
                        clock_divisor=None, enabled=False, mode="interval", overflows=0)
        self.can = {}
        self.can_mail = {}
        for base in (0xFFFFD000, 0xFFFFD800):
            for offset, value in {0:1, 2:0xC, 4:0, 6:0, 8:1, 0xA:0,
                                 0x20:0,0x22:0,0x28:0,0x2A:0,0x30:0,0x32:0,0x38:0,0x3A:0,
                                 0x40:0,0x42:0,0x48:0,0x4A:0,0x50:0xFFFF,0x52:0xFFFF,0x58:0,0x5A:0}.items():
                self.can[base+offset] = value
        if scenario.ram_power_on_byte is not None:
            self.initialize(sh2e.RAM_START, bytes([scenario.ram_power_on_byte]) * len(self.ram))
        self.attempts = []
        self.watch(0xFFFFC000, 0x100000000, "peripheral", "rw")
        self.watch(sh2e.RAM_START, sh2e.RAM_END, "RAM", "rw")
        self.watch(0xFFFF6390, 0xFFFF64D0, "SSM_state", "rw")

    def _attempt(self, mode, address, size, value=None):
        self.attempts.append(dict(mode=mode, address=sh2e.hx(address), size=size,
                                 value=sh2e.hx(value) if value is not None else None,
                                 pc=sh2e.hx(self.pc) if self.pc is not None else None))

    def read(self, address, size, address_sources=(), fetch=False):
        if address < 0xFFFFC000 or fetch:
            return super().read(address, size, address_sources, fetch)
        self._check(address, size)
        self._attempt("r", address, size)
        if address == 0xFFFFED18 and size == 2:
            value = self.mmio[address] | (0x8000 if self.scenario.nmi_high else 0)
        elif address in self.can and size == 2:
            if address & 0x7FF not in (0,2,0x40,0x42,0x50,0x52,0x58,0x5A):
                raise Frontier("HCAN_REGISTER_READ_MODEL", f"Read of{address:08X} not in reached no-traffic contract")
            value = self.can[address]
        elif address == 0xFFFFEC10 and size == 1:
            value = self.wdt["tcsr"]
        elif address == 0xFFFFEC11 and size == 1:
            value = self.wdt["tcnt"]
        elif address == 0xFFFFEC13 and size == 1:
            value = self.wdt["rstcsr"]
        elif address == 0xFFFFF708 and size == 1 and address in self.mmio:
            value = self.mmio[address]
        elif address == 0xFFFFF738 and size == 2 and 0xFFFFF730 in self.mmio and address in self.mmio:
            if self.mmio.get(0xFFFFF732,0) or self.mmio.get(0xFFFFF734,0) or self.mmio.get(0xFFFFF736,0):
                raise Frontier("PORT_B_FUNCTION_MODEL", "PortB read supports only documented GPIO/no-inversion configuration")
            outputs = self.mmio[0xFFFFF730]
            value = (self.mmio[address] & outputs) | (self.scenario.port_b_input_word & ~outputs & 65535)
        elif 0xFFFFF800 <= address < 0xFFFFF860:
            raise Frontier("ADC_INPUT_MODEL_REQUIRED", self.scenario.sensor_profile)
        elif 0xFFFFF000 <= address < 0xFFFFF030:
            raise Frontier("SCI_STARTUP_MODEL_REQUIRED", f"read {address:08X}+{size}")
        else:
            raise sh2e.SimulationStop(f"Unknown MMIO read {address:08X}+{size}")
        origins = {f"model:{MODEL_ID}:{address:08X}"}
        self._event("r", address, size, value, origins, address_sources)
        return value, origins

    def write(self, address, size, value, sources=(), address_sources=()):
        if address < 0xFFFFC000:
            return super().write(address, size, value, sources, address_sources)
        self._check(address, size)
        value &= (1 << (8 * size)) - 1
        self._attempt("w", address, size, value)
        if any(x.startswith("reset:undefined") for x in sources):
            raise sh2e.SimulationStop("Undefined reset register affects peripheral write")
        if address in PORT_WRITES and size == 2:
            self.mmio[address] = value  # Write observation only; no electrical output model.
        elif address == 0xFFFFF708 and size == 1:
            if value != 1:
                raise Frontier("SYSCR1_RAM_CLOCK_CHANGE", f"SYSCR1={value:02X}")
            self.mmio[address] = value
        elif address in (0xFFFFEC20, 0xFFFFEC22, 0xFFFFEC24) and size == 2:
            self.mmio[address] = value
        elif address == 0xFFFFEC26 and size == 2:
            if value:
                raise Frontier("RAM_EMULATION_CONFIGURATION", f"RAMER={value:04X}")
            self.mmio[address] = value
        elif address == 0xFFFFF70A and size == 2:
            if value >> 8 != 0x3C:
                raise sh2e.SimulationStop("SYSCR2 write lacks 3C key")
            if (value & 0x80) or (value & 0x70):
                raise Frontier("CLOCK_OR_RESERVED_SYSCR2", f"SYSCR2={value:04X}")
            self.mmio[0xFFFFF70B] = value & 255
        elif address == 0xFFFFED18 and size == 2:
            if value & 0x7E00:
                raise sh2e.SimulationStop("ICR reserved bits set")
            self.mmio[address] = value & 0x1FF  # NMIL is read-only.
        elif address == 0xFFFFEC12 and size == 2:
            if value >> 8 == 0x5A:
                self.wdt["rstcsr"] = (self.wdt["rstcsr"] & 0x80) | (value & 0x60) | 0x1F
            elif value == 0xA500:
                self.wdt["rstcsr"] &= 0x7F
            else:
                raise sh2e.SimulationStop("Unsupported WDT RSTCSR write key")
        elif address == 0xFFFFEC10 and size == 2:
            if value >> 8 == 0x5A:
                self.wdt.update(tcnt=value & 255, elapsed_cycles=0)
            elif value >> 8 == 0xA5:
                old = self.wdt["tcsr"]
                if value & 0x18 != 0x18:
                    raise sh2e.SimulationStop("WDT reserved bits must be one")
                if old & 0x20 and ((old ^ value) & 0x47):
                    raise Frontier("WDT_LIVE_CLOCK_MODE_CHANGE", "Manual13.4.2/13.4.3 require stopping TME before changing mode/divisor")
                self.wdt.update(tcsr=(value & 0x7F) | (old & value & 0x80),
                                enabled=bool(value & 0x20),
                                mode="watchdog" if value & 0x40 else "interval",
                                clock_divisor=(2, 64, 128, 256, 512, 1024, 4096, 8192)[value & 7])
                if not self.wdt["enabled"]:
                    self.wdt.update(tcnt=0, elapsed_cycles=0)
            else:
                raise sh2e.SimulationStop("Unsupported WDT TCNT/TCSR write key")
        elif address in self.can and size == 2:
            offset = address & 0x7FF
            base = address - offset
            if offset == 0:
                if value not in (0, 1):
                    raise Frontier("HCAN_MODE_CONFIGURATION", f"MCR={value:04X}")
                if value == 0 and not self.scenario.can_idle_configuration:
                    raise Frontier("HCAN_RESET_RELEASE", "Explicit idle-CAN configuration scenario disabled")
                if value == 1 and self.can[address] == 0:
                    raise Frontier("HCAN_REPEATED_RESET", "Reset effects after configuration require additional model")
                self.can[address] = value
                self.can[base+2] = 0xC if value else 0x4
            elif offset in (0x30,0x32,0x38,0x3A,0x40,0x42,0x48,0x4A,0x58,0x5A,8):
                self.can[address] &= ~value  # W1C flags, no external traffic in this model.
            elif offset in (0x20,0x22,0x28,0x2A):
                raise Frontier("HCAN_TRANSMISSION_REQUEST", "Actual bus transfer/cancel execution not modeled")
            elif offset == 2:
                raise sh2e.SimulationStop("Write to read-only HCAN GSR")
            else:
                self.can[address] = value
        elif self.mailbox_write(address, size, value):
            pass
        elif 0xFFFFF000 <= address < 0xFFFFF030:
            raise Frontier("SCI_STARTUP_MODEL_REQUIRED", f"write {address:08X}+{size}")
        else:
            raise sh2e.SimulationStop(f"Unknown MMIO write {address:08X}+{size}")
        self._event("w", address, size, value, sources, address_sources)

    def mailbox_write(self, address, size, value):
        # Table16.2: each32-byte slot has exactly20defined bytes; holes rejected.
        for base in (0xFFFFD100, 0xFFFFD900):
            if base <= address < base + 32 * 32:
                offset = (address - base) % 32
                if offset + size > 20 or size not in (1, 2) or (size == 1 and not 4 <= offset < 16):
                    raise sh2e.SimulationStop("Unsupported/reserved HCAN mailbox access")
                if offset == 4 and value & (0x1000 if size == 2 else 0x10):
                    raise Frontier("HCAN_AUTOTRANSMIT_REQUEST", "Mailbox ATX behavior not modeled")
                for i,b in enumerate(value.to_bytes(size,'big')):
                    self.can_mail[address+i] = b
                return True
        return False

    def advance(self, cycles):
        if not self.wdt["enabled"]:
            return
        self.wdt["elapsed_cycles"] += cycles
        divisor = self.wdt["clock_divisor"]
        ticks, self.wdt["elapsed_cycles"] = divmod(self.wdt["elapsed_cycles"], divisor)
        if self.wdt["tcnt"] + ticks >= 256:
            self.wdt["overflows"] += (self.wdt["tcnt"] + ticks) // 256
            if self.scenario.stop_on_timer_overflow or self.wdt["mode"] == "watchdog":
                raise Frontier("WDT_OVERFLOW_ENVELOPE", "Synthetic clock budget reaches interval interrupt/reset boundary; no invented interrupt service")
            self.wdt["tcsr"] |= 0x80
        self.wdt["tcnt"] = (self.wdt["tcnt"] + ticks) & 255


class BootCPU(sh2e.CPU):
    """Frozen ISA with reset setup and explicit interrupt admission observation."""
    def __init__(self, memory, scenario):
        super().__init__(memory, ((0, sh2e.ROM_SIZE),), (scenario.stack_low, scenario.stack_high))
        self.scenario = scenario
        self.vbr = 0
        self.fpscr = 0x00040001
        self.irq_inhibit_next = False
        self.irq_events = []
        self.irq_finished = False
        self.control = []

    def step(self):
        s = self.scenario
        if s.irq_at_step is not None and len(self.trace) >= s.irq_at_step and not self.irq_finished:
            if self.irq_inhibit_next:
                self.irq_events.append(dict(pc=sh2e.hx(self.pc), decision="deferred_after_LDC"))
            elif self.pending:
                if not self.irq_events or self.irq_events[-1]["decision"] != "deferred_delay_slot":
                    self.irq_events.append(dict(pc=sh2e.hx(self.pc), decision="deferred_delay_slot"))
            elif s.irq_is_nmi or s.irq_priority > ((self.sr >> 4) & 15):
                self.irq_events.append(dict(pc=sh2e.hx(self.pc), decision="admissible_unmodeled_exception"))
                raise Frontier("IRQ_EXCEPTION_CONTEXT_REQUIRED", "Admissible exception needs actual entry/return and peripheral arbitration model")
            elif not self.irq_events or self.irq_events[-1]["decision"] != "masked_pending":
                self.irq_events.append(dict(pc=sh2e.hx(self.pc), decision="masked_pending"))
        pc, pending, before_t = self.pc, self.pending, self.t
        previous_vbr, previous_fpscr = self.vbr, self.fpscr
        opcode, _ = self.memory.read(pc, 2, fetch=True)
        if not any(opcode & o.mask == o.value for o in sh2e.OPCODES) and self.extended_step(opcode):
            pass
        else:
            super().step()
        tr = self.trace[-1]
        self.irq_inhibit_next = tr['instruction'].startswith('ldc_') or tr['instruction'] in ('bf_s','bt_s')
        tr['system_before'].update(vbr=sh2e.hx(previous_vbr),fpscr=sh2e.hx(previous_fpscr))
        tr['system_after'].update(vbr=sh2e.hx(self.vbr),fpscr=sh2e.hx(self.fpscr))
        if tr["instruction"] in ("bt", "bf", "bt_s", "bf_s", "bra", "bsr", "jmp", "jsr", "rts") or pending:
            self.control.append(dict(pc=sh2e.hx(pc), next_pc=sh2e.hx(self.pc),
                                     delayed_target=sh2e.hx(self.pending[0]) if self.pending else None,
                                     instruction=tr["instruction"], prior_t=before_t, delay_slot=bool(pending)))
        self.memory.advance(s.cycles_per_instruction)

    def extended_step(self, op):
        # Only forms reached by the actual reset prefix. No FPU arithmetic.
        n, m = (op >> 8) & 15, (op >> 4) & 15
        name = None
        if op & 0xF00F == 0x6007: name = "not"
        elif op & 0xF00F == 0x200E: name = "mulu_w"
        elif op & 0xF0FF == 0x001A: name = "sts_macl_reg"
        elif op & 0xF0FF == 0x4029: name = "shlr16"
        elif op & 0xFF00 == 0x8100: name = "movw_disp_store"
        elif op & 0xF0FF == 0x4015: name = "cmppl"
        elif op & 0xF0FF == 0x4011: name = "cmppz"
        elif op & 0xF00F == 0x200A: name = "xor"
        elif op & 0xF0FF == 0x402E: name = "ldc_vbr"
        elif op & 0xF0FF == 0x406A: name = "lds_fpscr"
        if name is None: return False
        pc, slot = self.pc, self.pending
        if not any(a <= pc and pc+2 <= b for a,b in self.execution_ranges):
            raise sh2e.SimulationStop("Extended opcode escaped execution range")
        self._reg(15,self.r[15],self.sources[15])
        self.memory.pc, self.memory.in_delay_slot = pc, bool(slot)
        self.memory.call_context = list(self.call_context)
        self.memory.control_sources = set(self.control_sources)
        before, before_t, before_pr = list(self.r), self.t, self.pr
        bs = {key:sh2e.hx(getattr(self,key)) for key in ('sr','mach','macl')}
        if name == "not": self._reg(n,~self.r[m],self.sources[m])
        elif name == "mulu_w": self._set_system('macl',(self.r[n]&65535)*(self.r[m]&65535),self.sources[n]|self.sources[m])
        elif name == "sts_macl_reg": self._reg(n,self.macl,self.system_sources['macl'])
        elif name == "shlr16": self._reg(n,self.r[n]>>16,self.sources[n])
        elif name == "movw_disp_store": self.memory.write((self.r[m]+2*(op&15))&0xFFFFFFFF,2,self.r[0],self.sources[0],self.sources[m])
        elif name == "cmppl": self._t(sh2e.sx(self.r[n],32)>0,self.sources[n])
        elif name == "cmppz": self._t(sh2e.sx(self.r[n],32)>=0,self.sources[n])
        elif name == "xor": self._reg(n,self.r[n]^self.r[m],self.sources[n]|self.sources[m])
        elif name == "ldc_vbr": self.vbr=self.r[n]
        elif name == "lds_fpscr": self.fpscr=(self.r[n]&0x18C60)|0x40001
        self.opcodes_seen.add(name)
        self.trace.append(dict(pc=sh2e.hx(pc),opcode=f'{op:04X}',instruction=name,delay_slot=bool(slot),
                               call_context=list(self.call_context),registers={f'r{i}':sh2e.hx(v) for i,v in enumerate(self.r) if v!=before[i]},
                               t_before=before_t,t_after=self.t,system_before=bs,
                               system_after={key:sh2e.hx(getattr(self,key)) for key in ('sr','mach','macl')},pr_before=sh2e.hx(before_pr),pr_after=sh2e.hx(self.pr)))
        self.pending=None
        self.pc=pc+2
        if slot:
            self.pc,action=slot
            if action=='call':self.call_context.append(sh2e.hx(self.pc))
            elif action=='return':
                if not self.call_context:raise sh2e.SimulationStop('Return without context')
                self.call_context.pop();self.returned=not self.call_context
        return True


MILESTONES = {0xAAC: "power_on_entry", 0xAB0: "bus_configuration_returned",
              0xAB4: "port_initialization_returned", 0x66C: "boot_selector_entered",
              0x67A: "interval_timer_initialization_returned", 0x1B4: "HCAN_initialization_entered",
              0xC16: "HCAN_reset_status_observed", 0x680: "HCAN_initialization_returned",
              0x68C: "boot_communication_RAM_initialized", 0x6F8: "application_jump_selected", 0x1150: "application_reset_entry",
              0xF928: "OEM_RAM_initialization_entry", 0x47E24: "SSM_receive_driver_entry"}


def dependencies():
    paths = [SIM / "sh2e.py", HERE / "boot.py", HERE / "manual_evidence.json"]
    return [{"path": str(p), "sha256": sha256(p.read_bytes()).hexdigest()} for p in paths]


def run_image(path, expected_sha256=None, scenario=None, evidence_dir=None):
    scenario = scenario or Scenario()
    result = dict(schema=1, status="FAIL", model_id=MODEL_ID, image={}, milestones=[], unsupported=[],
                  ssm_readiness={"status": "CONDITIONAL", "reached": False,
                                 "reason": "Reset-to-SCI/SSM readiness not established"},
                  physical_operations=False, scenario=asdict(scenario))
    cpu = memory = None
    try:
        scenario.validate()
        if sha256((SIM / "sh2e.py").read_bytes()).hexdigest() != CORE_SHA256:
            raise sh2e.SimulationStop("Frozen core SHA256 changed")
        raw = Path(path).read_bytes()
        actual_sha = sha256(raw).hexdigest()
        result["image"] = dict(path=str(Path(path).resolve()), sha256=actual_sha, size=len(raw))
        if len(raw) != sh2e.ROM_SIZE:
            raise sh2e.SimulationStop("Image must be exactly 1 MiB")
        if expected_sha256 is not None and actual_sha != expected_sha256.lower():
            raise sh2e.SimulationStop("Image SHA256 mismatch")
        rom = sh2e.ROM(raw, str(Path(path).resolve()), actual_sha)
        memory, cpu = BootMemory(rom, scenario), None
        cpu = BootCPU(memory, scenario)
        for i in range(15):
            cpu._reg(i, (scenario.reset_poison + i * 0x101) & 0xFFFFFFFF, {f"reset:undefined:r{i}"})
        cpu.pc = int.from_bytes(raw[:4], "big")
        result["reset"] = dict(pc=sh2e.hx(cpu.pc), sp=sh2e.hx(int.from_bytes(raw[4:8], "big")), vbr=0, sr="000000F0")
        cpu._reg(15, int.from_bytes(raw[4:8], "big"), {"reset:ROM_SP_vector"})
        cpu._set_system("sr", 0xF0, {"reset:SR_I=15_other_bits_fixture_zero"})
        cpu.call_context = ["power_on"]
        result["reset"] = dict(pc=sh2e.hx(cpu.pc), sp=sh2e.hx(cpu.r[15]), vbr=0, sr=sh2e.hx(cpu.sr))
        seen = set()
        for _ in range(scenario.max_steps):
            if cpu.pc in MILESTONES and cpu.pc not in seen:
                result["milestones"].append(dict(name=MILESTONES[cpu.pc], pc=sh2e.hx(cpu.pc), retired=len(cpu.trace)))
                seen.add(cpu.pc)
            if cpu.pc & 1:
                raise sh2e.SimulationStop("Unexpected odd instruction target")
            cpu.step()
        raise Frontier("INSTRUCTION_BUDGET", f"Stopped at declared {scenario.max_steps} retired instructions")
    except Frontier as exc:
        result.update(status="CONDITIONAL", stop=dict(kind="known_model_frontier", code=exc.code, detail=exc.detail))
        result["unsupported"].append(dict(code=exc.code, detail=exc.detail))
    except (sh2e.SimulationStop, ValueError, OSError) as exc:
        result.update(status="FAIL", stop=dict(kind="execution_or_input_failure", code=type(exc).__name__, detail=str(exc)))
        result["unsupported"].append(dict(code=type(exc).__name__, detail=str(exc)))
    if cpu is not None:
        result["stop"].update(pc=sh2e.hx(cpu.pc), retired_instructions=len(cpu.trace), sp=sh2e.hx(cpu.r[15]))
        result["irq"] = cpu.irq_events
        result["watchdog"] = memory.wdt
        stack_values = [int(result['reset']['sp'],16)] + [int(t['registers']['r15'],16) for t in cpu.trace if 'r15' in t['registers']]
        result['stack'] = dict(declared_low=sh2e.hx(scenario.stack_low),declared_high=sh2e.hx(scenario.stack_high),
                               observed_min=sh2e.hx(min(stack_values)),observed_max=sh2e.hx(max(stack_values)),
                               scope='Address/alignment bound only; no whole-RAM ownership or complete ISR depth proof')
        result['final_system'] = dict(sr=sh2e.hx(cpu.sr),pr=sh2e.hx(cpu.pr),vbr=sh2e.hx(cpu.vbr),fpscr=sh2e.hx(cpu.fpscr))
        result['terminal_state'] = dict(registers=[sh2e.hx(v) for v in cpu.r],pc=sh2e.hx(cpu.pc),
            sr=sh2e.hx(cpu.sr),pr=sh2e.hx(cpu.pr),vbr=sh2e.hx(cpu.vbr),fpscr=sh2e.hx(cpu.fpscr),
            mach=sh2e.hx(cpu.mach),macl=sh2e.hx(cpu.macl),pending=cpu.pending,call_context=list(cpu.call_context))
        result["cycles"] = dict(kind="SCENARIO_ASSUMPTION_NOT_SILICON_TIMING", per_instruction=scenario.cycles_per_instruction,
                                modeled_total=len(cpu.trace) * scenario.cycles_per_instruction)
        traces = dict(instructions=cpu.trace, memory=memory.events, mmio_attempts=memory.attempts, control=cpu.control)
        # Include ALL writes, including transient stack, so no silent equivalence exception exists.
        result["observable_trace"] = [{k:e[k] for k in ('mode','address','size','value','pc')} for e in memory.events if e["mode"] == "w"]
        result["control_trace"] = cpu.control
        result["trace_hashes"] = {k: digest(v) for k, v in traces.items()}
        written_ram={a for e in memory.events if e['mode']=='w' and sh2e.RAM_START <= int(e['address'],16) < sh2e.RAM_END
                     for a in range(int(e['address'],16),int(e['address'],16)+e['size'])}
        result["coverage"] = dict(unique_pcs=len({t["pc"] for t in cpu.trace}), opcodes=sorted(cpu.opcodes_seen),
                                  peripheral_accesses=len(memory.attempts), readable_RAM_bytes=sum(memory.initialized),
                                  fixture_initialized_RAM_bytes=len(memory.ram) if scenario.ram_power_on_byte is not None else 0,
                                  actual_OEM_unique_RAM_written_bytes=len(written_ram),
                                  sensor_profile_consumed=False, SCI_access_reached=any(0xFFFFF000 <= int(e["address"], 16) < 0xFFFFF030 for e in memory.attempts))
        if evidence_dir:
            directory = Path(evidence_dir)
            directory.mkdir(parents=True, exist_ok=True)
            result["evidence"] = []
            for label, data in traces.items():
                target = directory / f"{label}.json.gz"
                target.write_bytes(gzip.compress(json.dumps(data, sort_keys=True, separators=(',',':')).encode(), mtime=0))
                result["evidence"].append(dict(path=str(target.resolve()), sha256=sha256(target.read_bytes()).hexdigest()))
    result["dependencies"] = dependencies()
    result["assumptions"] = ["User-mode power-on ROM mapping, VBR zero; no boot/programmer pin mode emulation",
        "NMI and portB input levels explicit; no external CAN/SCI frames; no blanket peripheral zero defaults",
        "RAM A5 power-on fixture is declared by scenario, not physical reset state; strict uninitialized option available",
        "Idle CAN configuration admits MCR/GSR transitions and no-traffic flags; no frame/bit timing, arbitration or bus synchronization success claim",
        "Unknown reset GPR values carry fixture origins; no claim covering every initial register value",
        "PFC writes recorded; electrical pin/output effects are unmodeled; reads fail",
        "Clock cost is synthetic scenario input, not measured silicon or a universal upper bound",
        "Interrupt admission is observed, accepted exception execution stops; no interrupt silently discarded",
        "No PASS until boot/application/SSM and fault contracts are actually closed"]
    result["semantic_sha256"] = digest({k: v for k, v in result.items() if k not in ("evidence", "semantic_sha256")})
    return result


def compare_images(stock_path, candidate_path, expected_stock_sha256=None, expected_candidate_sha256=None,
                   scenario=None, allowlist=(), evidence_dir=None):
    """Allowlist consists of exact before/after write-event pairs, never address-wide masks."""
    base = Path(evidence_dir) if evidence_dir else None
    stock = run_image(stock_path, expected_stock_sha256, scenario, base / "stock" if base else None)
    candidate = run_image(candidate_path, expected_candidate_sha256, scenario, base / "candidate" if base else None)
    differences = []
    allowed = list(allowlist)
    for kind in ("observable_trace", "control_trace"):
        a, b = stock.get(kind, []), candidate.get(kind, [])
        for i in range(max(len(a), len(b))):
            av = a[i] if i < len(a) else None
            bv = b[i] if i < len(b) else None
            if av != bv:
                entry = dict(kind=kind, index=i, stock=av, candidate=bv)
                entry["allowed"] = kind == "observable_trace" and any(x == {"stock": av, "candidate": bv} for x in allowed)
                differences.append(entry)
    equal_frontier = stock.get("stop") == candidate.get("stop")
    terminal_equal = stock.get('terminal_state') == candidate.get('terminal_state')
    if not terminal_equal:
        differences.append(dict(kind='terminal_state',stock=stock.get('terminal_state'),candidate=candidate.get('terminal_state'),allowed=False))
    fail = stock["status"] == "FAIL" or candidate["status"] == "FAIL" or any(not x["allowed"] for x in differences) or not equal_frontier
    return dict(schema=1, status="FAIL" if fail else "CONDITIONAL",
                classification="RESET_PREFIX_DIFFERENTIAL_NOT_COMPLETE_BOOT_EQUIVALENCE", stock=stock, candidate=candidate,
                explicit_allowlist=allowed, differences=differences, equal_frontier=equal_frontier,terminal_state_equal=terminal_equal,
                ssm_readiness={"status": "CONDITIONAL", "reached": False},
                reason="Equal modeled prefix does not prove later patched code, residency, SSM startup or physical operation")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True)
    ap.add_argument("--expected-sha256")
    ap.add_argument("--stock")
    ap.add_argument("--expected-stock-sha256")
    ap.add_argument("--scenario-json")
    ap.add_argument("--max-steps", type=int)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    values = json.loads(Path(args.scenario_json).read_text()) if args.scenario_json else {}
    if args.max_steps is not None:
        values["max_steps"] = args.max_steps
    scenario = Scenario(**values)
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Refusing to overwrite an existing run result; use a new output path")
    evidence_dir = output.parent / (output.stem + "_traces")
    result = (compare_images(args.stock, args.image, args.expected_stock_sha256, args.expected_sha256,
                             scenario, evidence_dir=evidence_dir) if args.stock else
              run_image(args.image, args.expected_sha256, scenario, evidence_dir))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=result["status"], output=str(output.resolve()), sha256=sha256(output.read_bytes()).hexdigest())))
    return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
