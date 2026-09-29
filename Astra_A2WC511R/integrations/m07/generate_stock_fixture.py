"""Execute unchanged OEM six-address A8 software events. No ECU patch/device.

Adapted from the reviewed M0.6 event harness into an independent M0.7 file so
even failure output cannot change frozen M0.6 artifacts.
"""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SIM = Path("C:/Dev/A2WC511R_Sim")
sys.path.insert(0, str(SIM))
from sh2e import ROM, Memory, FunctionHarness, SimulationStop, RAM_START
from protocol import REQUEST, ADDRESSES, parse_wire

STOCK_PATH = Path("C:/Dev/SubaruRoms/OEM/A2WC511R.bin")
STOCK_SHA = "22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218"
OUT = ROOT / "reports/local/m07_residency/host"


class EventMemory(Memory):
    def __init__(self, rom):
        super().__init__(rom)
        self.scr, self.tx, self.rdr, self.status_reads = 0, [], None, []

    def read(self, address, size, address_sources=(), fetch=False):
        if address in (0xFFFFF012, 0xFFFFF014, 0xFFFFF015) and size == 1 and not fetch:
            if address == 0xFFFFF012:
                value = self.scr
            elif address == 0xFFFFF015:
                if self.rdr is None:
                    raise SimulationStop("RDR read without supplied event")
                value = self.rdr
            else:
                value = self.status_reads.pop(0) if self.status_reads else 0x80
            sources = {"fixture:SCI-ready-event"}
            self._event("r", address, size, value, sources, address_sources)
            return value, sources
        return super().read(address, size, address_sources, fetch)

    def write(self, address, size, value, sources=(), address_sources=()):
        if address in (0xFFFFF012, 0xFFFFF013, 0xFFFFF014) and size == 1:
            value &= 255
            if address == 0xFFFFF012:
                self.scr = value
            if address == 0xFFFFF013:
                self.tx.append(value)
            self._event("w", address, size, value, sources, address_sources)
            return
        return super().write(address, size, value, sources, address_sources)


def receive(memory, value):
    memory.rdr = value
    memory.status_reads = [0xC0, 0x80, 0x80]
    harness = FunctionHarness(memory, [(0x47000, 0x48B90), (0x2500, 0x2590), (0x4200, 0x4400)])
    harness.cpu.track_control_sources = False
    try:
        result = harness.run(0x47E24, allowed_writes=[(0xFFFF63E0, 0xFFFF64BC)], max_steps=10000)
    except BaseException:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "stock_fixture_failure.json").write_text(json.dumps({"pc": hex(harness.cpu.pc), "trace": harness.cpu.trace[-70:], "events": memory.events[-70:]}, indent=2))
        raise
    if memory.status_reads:
        raise AssertionError("RX did not consume its declared status event")
    memory.rdr = None
    return result


def execute(rom, sample_id, raw):
    memory = EventMemory(rom)
    memory.initialize(0xFFFF63E0, bytes(0xDC))
    for address, value in zip(ADDRESSES, raw):
        memory.initialize(address, bytes((value,)))
        memory.watch(address, address+1, f"raw:{address:08X}", "r")
    calls = [receive(memory, value) for value in REQUEST]
    if not memory.ram[0x649A] & 0x20:
        raise AssertionError("OEM six-address A8 was not accepted")
    memory.tx.append(memory.ram[0x6492])  # Fixture first-byte release from OEM FIFO.
    for _ in range(270):
        before = bytes(memory.ram[0x6408:0x6492])
        calls.append(receive(memory, memory.tx[-1]))
        if bytes(memory.ram[0x6408:0x6492]) != before:
            raise AssertionError("Active TX changed the retained request")
        if not memory.ram[0x649A] & 0x20:
            break
    else:
        raise AssertionError("OEM TX failed to complete")
    response = bytes(memory.tx)
    if parse_wire(REQUEST + response) != raw:
        raise AssertionError("Actual OEM response differs from initialized six bytes")
    events = [e for e in memory.events if not 0xFFFFBBA0 <= int(e["address"], 16) < 0xFFFFBFA0]
    transmitted = bytes(int(e["value"], 16) for e in events if e["mode"] == "w" and e["address"] == "FFFFF013")
    if transmitted != response[1:]:
        raise AssertionError("OEM TDR writes differ from reply")
    return {"sample_id": sample_id, "request_hex": REQUEST.hex(), "response_hex": response.hex(),
            "raw_by_address": {f"{address:08X}": value for address, value in zip(ADDRESSES, raw)},
            "events_sha256": sha256(json.dumps(events, sort_keys=True).encode()).hexdigest(),
            "events": events, "calls": calls, "steps": sum(c["steps"] for c in calls),
            "provenance": "Actual unchanged OEM47E24 RX/parser/A8 classifier/getter/TX execution; explicit virtual RAM and SCI-ready events",
            "first_byte": "Fixture release from OEM-built FIFO; no first-byte timer simulation"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rom = ROM.load(STOCK_PATH, STOCK_SHA)
    cases = [bytes(values) for values in ((17,17,1,2,1,1),(33,17,0,0,2,1),(136,136,255,128,0,0),
             (159,159,1,2,5,4),(255,255,255,255,255,255),(0,0,0,0,1,1),(17,17,40,130,1,1),(82,82,1,3,5,2))]
    samples = [execute(rom, f"virtual_{index:02d}", values) for index, values in enumerate(cases)]
    result = {"status": "PASS", "classification": "VIRTUAL_COMPILED_OEM_A8_READS_NOT_PHYSICAL_TELEMETRY",
              "utc": datetime.now(timezone.utc).isoformat(), "stock_rom": {"path": str(STOCK_PATH), "sha256": STOCK_SHA},
              "samples": samples, "ecu_patch": False,
              "limitations": ["Explicit virtual input scenarios, not telemetry", "No electrical/timer/interrupt model", "First response byte released by fixture from OEM FIFO", "Sequential RAM reads do not prove freshness or atomicity"],
              "sources": [{"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()} for path in (Path(__file__), SIM / "sh2e.py", Path(__file__).with_name("protocol.py"))]}
    path = OUT / "stock_six_a8_fixtures.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "samples": len(samples), "fixture": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
