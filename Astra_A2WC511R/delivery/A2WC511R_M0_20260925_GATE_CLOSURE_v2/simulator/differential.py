"""Exact compiled experimental observer versus stock, within explicit virtual bounds."""
from hashlib import sha256
import json
from pathlib import Path
import sys

from sh2e import ROM, Memory, FunctionHarness, SimulationStop, RAM_START, STOCK_SHA256

ROOT = Path(__file__).resolve().parent
BUILD = Path(r"C:\Dev\Astra_A2WC511R\work\builds\m0_final_05")
CODE_BASE, CODE_END, HOOK_ENTRY = 0xE1000, 0xE1364, 0xE12DC
DIAG_BASE, DIAG_END = 0xFFFF7400, 0xFFFF7420
CALL_ENTRY, CALL_CONTINUE, HOOK_POOL = 0x1193A, 0x11940, 0x11ADC
DECODER = (0x147AC, 0x14802)
ROM_PATH = Path(r"C:\Dev\SubaruRoms\OEM\A2WC511R.bin")
SOURCE, PACKED, LATCH, FLAGS = 0xFFFF4C75, 0xFFFF4C8D, 0xFFFF4CA1, 0xFFFF4C50
TARGET, CURRENT = 0xFFFF4BC1, 0xFFFF4BC2


def artifacts(build=BUILD):
    build = Path(build)
    manifest = json.loads((build / "manifest.json").read_text())
    name = "m0.EXPERIMENTAL_UNAPPROVED.code.bin"
    code = (build / name).read_bytes()
    if sha256(code).hexdigest() != manifest["artifacts"][name]:
        raise SimulationStop("Experimental code differs from build manifest")
    if (len(code), int(manifest["code_base"], 16), int(manifest["ram_base"], 16)) != (868, CODE_BASE, DIAG_BASE):
        raise SimulationStop("Changed experimental mapping; review before updating test")
    stock = ROM.load(ROM_PATH, STOCK_SHA256)
    if stock.data[HOOK_POOL:HOOK_POOL + 4] != bytes.fromhex("000147ac"):
        raise SimulationStop("Unexpected stock hook pointer")
    if stock.data[CALL_ENTRY:CALL_CONTINUE] != bytes.fromhex("d268420b0009"):
        raise SimulationStop("Unexpected stock caller bytes")
    patched = stock.with_overlay(CODE_BASE, code, "EXPERIMENTAL_UNAPPROVED compiled diagnostic closure")
    patched = patched.with_overlay(HOOK_POOL, HOOK_ENTRY.to_bytes(4, "big"),
                                   "EXPERIMENTAL_UNAPPROVED decoder pointer")
    return stock, patched, manifest


def initial_state(warm, packed):
    if not warm:
        return b"\xA5" * 32
    # Explicit virtual prior observation, including near-wrap publication counters.
    values = [0xFFFFFFFE if packed & 1 else 12, 0x4D304431,
              0xFFFFFFFF if packed & 1 else 20, 0xFFFF,
              0xFFFFFFFF if packed & 1 else 5]
    state = bytearray(b"".join(v.to_bytes(4, "big") for v in values) + b"\x00" * 12)
    state[26:28] = bytes([0xA7, 0xB8])
    state[29] = packed if packed & 2 else packed ^ 0x11
    state[30] = 1
    return bytes(state)


def reference_state(old, source, packed, latch, flags, changed=0):
    """Independent explicit expected observation; freshness remains UNKNOWN."""
    old = bytearray(old)
    read32 = lambda off: int.from_bytes(old[off:off + 4], "big")
    if read32(4) != 0x4D304431 or old[30] != 1:
        old = bytearray(32)
        old[0:4] = (2).to_bytes(4, "big")
        old[4:8] = bytes.fromhex("4d304431")
        old[30] = 1
    old32 = lambda off: int.from_bytes(old[off:off + 4], "big")
    sequence = ((old32(0) & ~1) + 2) & 0xFFFFFFFF
    samples = (old32(8) + 1) & 0xFFFFFFFF
    transitions = (old32(16) + int(old32(8) != 0 and old[29] != packed)) & 0xFFFFFFFF
    hi, lo = packed >> 4, packed & 15
    reasons = 512 | 8 | int(packed != 0x11) | (2 if latch != 1 else 0) | (4 if flags & 2 == 0 else 0)
    reasons |= (32 if source != packed else 0) | (128 if hi > 8 or lo > 8 else 0) | (256 if changed else 0)
    target = hi if hi < 8 else 0 if hi == 8 else old[26]
    current = lo if lo < 8 else 0 if lo == 8 else old[27]
    output = b"".join(v.to_bytes(4, "big") for v in (sequence, 0x4D304431, samples, reasons, transitions))
    return output + bytes([source, packed, latch, flags, hi, lo, target, current, 0, packed, 1, changed])


def validate_publication(events):
    """Every diagnostic field write must occur between odd/even sequence stores."""
    sequence = None
    commits = []
    for event in events:
        address = int(event["address"], 16)
        if event["mode"] != "w" or not DIAG_BASE <= address < DIAG_END:
            continue
        if address == DIAG_BASE:
            if event["size"] != 4:
                raise AssertionError("Sequence was not written as one aligned32-bit access")
            sequence = int(event["value"], 16)
            if sequence & 1 == 0:
                commits.append(sequence)
        elif sequence is None or sequence & 1 == 0:
            raise AssertionError("Diagnostic field write outside odd publication sequence")
    if sequence is None or sequence & 1:
        raise AssertionError("Diagnostic publication did not finish even")
    return commits


def execute(rom, packed, warm=False, caller=False, patched=False, memory_class=Memory):
    source = packed if packed & 4 else packed ^ 0x21
    latch = (0, 1, 2, 255)[packed % 4]
    flags = (0, 2, 255, 128)[(packed // 4) % 4]
    memory = memory_class(rom)
    for address, value in ((SOURCE, source), (PACKED, packed), (LATCH, latch), (FLAGS, flags)):
        memory.initialize(address, bytes([value]))
        memory.watch(address, address + 1, f"virtual input {address:08X}")
    prior = (0xAA, 0xBB) if warm else (0, 7)
    memory.initialize(TARGET, bytes(prior))
    state = initial_state(warm, packed)
    memory.initialize(DIAG_BASE, state)
    memory.watch(TARGET, CURRENT + 1, "OEM decoded RAM")
    memory.watch(DIAG_BASE, DIAG_END, "experimental observer RAM")
    ranges = [DECODER]
    if patched:
        ranges += [(CODE_BASE, CODE_END)]
    if caller:
        ranges += [(CALL_ENTRY, CALL_CONTINUE)]
    harness = FunctionHarness(memory, ranges)
    seed = packed | (0x100 if warm else 0)
    regs = {i: ((0x9E3779B9 * (i + 1)) ^ (seed * 0x01010101)) & 0xFFFFFFFF for i in range(15)}
    system = dict(sr=(0x3F3 if warm else 0xF0), mach=(0x89ABCDEF ^ seed), macl=(0x76543210 ^ seed))
    entry = CALL_ENTRY if caller else HOOK_ENTRY if patched else DECODER[0]
    allowed = [(TARGET, CURRENT + 1)] + ([(DIAG_BASE, DIAG_END)] if patched else [])
    result = harness.run(entry, allowed_writes=allowed, registers=regs, system_registers=system,
                         stop_at=CALL_CONTINUE if caller else None, max_steps=2000)
    return harness, result, reference_state(state, source, packed, latch, flags)


def compare(stock_run, patched_run):
    stock, baseline_result, _ = stock_run
    patched, patched_result, expected_state = patched_run
    if stock.cpu.r != patched.cpu.r:
        raise AssertionError("General register divergence: " + str([
            (i, hex(a), hex(b)) for i, (a, b) in enumerate(zip(stock.cpu.r, patched.cpu.r)) if a != b]))
    if baseline_result["system_registers"] != patched_result["system_registers"]:
        raise AssertionError("SR/MACH/MACL/PR divergence")
    if stock.cpu.pc != patched.cpu.pc:
        raise AssertionError("Continuation/return PC divergence")
    excluded = [(DIAG_BASE - RAM_START, DIAG_END - RAM_START),
                (patched.stack[0] - RAM_START, patched.stack[1] - RAM_START)]
    for start, end in ((0, excluded[0][0]), (excluded[0][1], excluded[1][0]),
                       (excluded[1][1], len(stock.memory.ram))):
        if stock.memory.ram[start:end] != patched.memory.ram[start:end]:
            raise AssertionError("Undeclared final RAM divergence")
        if stock.memory.initialized[start:end] != patched.memory.initialized[start:end]:
            raise AssertionError("Undeclared initialized-RAM divergence")
    state = bytes(patched.memory.ram[DIAG_BASE - RAM_START:DIAG_END - RAM_START])
    if state != expected_state:
        raise AssertionError(f"Diagnostic reference mismatch: {state.hex()} != {expected_state.hex()}")
    publication_commits = validate_publication(patched.memory.events)
    # Same original decoder instruction sequence, branch outcomes and memory effects.
    def oem_trace(h):
        return [(row["pc"], row["opcode"], row["t_before"], row["t_after"], row["delay_slot"])
                for row in h.cpu.trace if DECODER[0] <= int(row["pc"], 16) < DECODER[1]]
    if oem_trace(stock) != oem_trace(patched):
        raise AssertionError("Original decoder instruction or T-bit behavior diverged")
    def oem_memory(h):
        return [(e["pc"], e["mode"], e["address"], e["size"], e["value"])
                for e in h.memory.events if e["pc"] is not None and DECODER[0] <= int(e["pc"], 16) < DECODER[1]]
    if oem_memory(stock) != oem_memory(patched):
        raise AssertionError("Original decoder memory access behavior diverged")
    for e in patched.memory.events:
        if e["mode"] != "w":
            continue
        address = int(e["address"], 16)
        if not (TARGET <= address < CURRENT + 1 or DIAG_BASE <= address < DIAG_END
                or patched.stack[0] <= address < patched.stack[1]):
            raise AssertionError("Write outside OEM/diagnostic/stack allowlist")
    stack_writes = [int(e["address"], 16) for e in patched.memory.events
                    if e["mode"] == "w" and patched.stack[0] <= int(e["address"], 16) < patched.stack[1]]
    stack_depth = patched.stack[1] - min(stack_writes) if stack_writes else 0
    if stack_depth > 124:
        raise AssertionError(f"Observed stack exceeds reviewed 124-byte bound: {stack_depth}")
    return dict(stock_steps=baseline_result["steps"], patched_steps=patched_result["steps"],
                extra_instructions=patched_result["steps"] - baseline_result["steps"],
                max_extra_stack_bytes=stack_depth, diagnostic_state=state.hex(),
                publication_commits=publication_commits,
                stock_trace_sha256=baseline_result["trace_sha256"],
                patched_trace_sha256=patched_result["trace_sha256"],
                stock_memory_trace_sha256=baseline_result["memory_trace_sha256"],
                patched_memory_trace_sha256=patched_result["memory_trace_sha256"])


if __name__ == "__main__":
    stock, patched, _ = artifacts()
    print(json.dumps(compare(execute(stock, 0x21, caller=True),
                             execute(patched, 0x21, caller=True, patched=True)), indent=2))
