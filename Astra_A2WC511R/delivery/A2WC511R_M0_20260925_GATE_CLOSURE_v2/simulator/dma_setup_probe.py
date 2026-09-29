"""Finite DMA register-storage fixture: configuration writes only, never DMA execution."""
from sh2e import ROM, Memory, CPU, RAM_START, STOCK_SHA256, SimulationStop
from differential import ROM_PATH


class DMAConfigurationMemory(Memory):
    def __init__(self, rom):
        super().__init__(rom)
        self.config = bytearray(32)
        self.config_initialized = bytearray(32)
        self.watch(0xFFFFECE0, 0xFFFFED00, "explicit DMA2/3 configuration-storage fixture")

    def write(self, address, size, value, sources=(), address_sources=()):
        if 0xFFFFECE0 <= address < address + size <= 0xFFFFED00:
            self._check(address, size)
            payload = (value & ((1 << (8 * size)) - 1)).to_bytes(size, "big")
            for byte_address in (0xFFFFECEF, 0xFFFFECFF):
                if address <= byte_address < address + size and payload[byte_address - address] & 1:
                    raise SimulationStop("DMA enable unsupported: fixture cannot execute a transfer")
            offset = address - 0xFFFFECE0
            self.config[offset:offset + size] = payload
            self.config_initialized[offset:offset + size] = b"\x01" * size
            self._event("w", address, size, value, sources, address_sources)
            return
        super().write(address, size, value, sources, address_sources)

    def read(self, address, size, address_sources=(), fetch=False):
        if 0xFFFFECE0 <= address < address + size <= 0xFFFFED00:
            raise SimulationStop("DMA status/peripheral reads unsupported in configuration-only fixture")
        return super().read(address, size, address_sources, fetch)


def run_setup(index_i, index_j):
    memory = DMAConfigurationMemory(ROM.load(ROM_PATH, STOCK_SHA256))
    memory.initialize(0xFFFF31AE, bytes([index_i]))
    memory.initialize(0xFFFF31AC, bytes([index_j]))
    cpu = CPU(memory, [(0xC31E, 0xC376)], (0xFFFF1F00, 0xFFFF2000))
    for register in range(15):
        cpu._reg(register, 0, {f"fixture:register:r{register}"})
    # R15 must be assigned a valid declared stack value directly before steps.
    cpu._reg(15, 0xFFFF2000, {"fixture:register:r15"})
    for register, value in ((9, 2), (14, 0xFFFF31AE), (12, 0xFFFF31AC)):
        cpu._reg(register, value, {f"fixture:register:r{register}"})
    cpu.pc, cpu.pr, cpu.call_context = 0xC31E, 0x11223344, ["0000C31E_SETUP_FRAGMENT"]
    while cpu.pc != 0xC376:
        cpu.step()
    if cpu.pr != 0x11223344 or cpu.r[15] != 0xFFFF2000 or cpu.pending:
        raise AssertionError("DMA setup fragment unexpectedly changed PR/SP/control flow")
    fields = {}
    for name, offset in (("tx_sar", 0), ("tx_dar", 4), ("tx_tcr", 8), ("tx_chcr", 12),
                         ("rx_sar", 16), ("rx_dar", 20), ("rx_tcr", 24), ("rx_chcr", 28)):
        if not all(memory.config_initialized[offset:offset + 4]):
            raise AssertionError("Configuration field was not fully written by the ROM fragment")
        fields[name] = int.from_bytes(memory.config[offset:offset + 4], "big")
    return dict(index_i=index_i, index_j=index_j, registers=fields, instruction_count=len(cpu.trace),
                trace=cpu.trace, accesses=memory.events,
                classification="ACTUAL_ROM_CONFIGURATION_STORES_IN_EXPLICIT_FINITE_FIXTURE_NO_DMA_EXECUTION")
