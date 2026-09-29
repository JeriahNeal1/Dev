"""Offline CLI for retained compiled OEM wire fixtures. No physical backend."""
import argparse
import hashlib
import json
import pathlib
import sys

from host_facade import A8_REQUESTS, HostFacade
from m06_protocol import Session, request_frame


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _checked_wire(blob, expected_hash):
    if blob["rom_sha256"] != expected_hash or not blob["accepted"]:
        raise ValueError("Fixture ROM identity or acceptance differs")
    if sha(json.dumps(blob["events"], sort_keys=True).encode()) != blob["events_sha256"]:
        raise ValueError("Fixture event digest differs")
    response = bytes.fromhex(blob["response_hex"])
    # The fixture releases the first header byte from OEM-built TX FIFO.
    # Every following response byte must be an actual executed TDR write.
    transmitted = bytes(int(event["value"], 16) for event in blob["events"]
                        if event["mode"] == "w" and event["address"] == "FFFFF013" and event["size"] == 1)
    if len(response) < 2 or transmitted != response[1:]:
        raise ValueError("Response bytes disagree with actual OEM TDR writes")
    return response


def replay(fixture_path, rom_path, mode):
    if mode not in ("ecu", "facade"):
        raise ValueError("Only offline ECU-prototype or host-facade replay is supported")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture["status"] != "PASS":
        raise ValueError("Fixture execution did not pass")
    image_hash = sha(rom_path.read_bytes())
    expected_hash = fixture["m06_sha256" if mode == "ecu" else "stock_sha256"]
    if image_hash != expected_hash:
        raise ValueError("Supplied ROM does not match the compiled fixture")
    records = {}
    for record in fixture["records"]:
        key = record["kind"], record["page"]
        if key in records:
            raise ValueError("Ambiguous repeated fixture page")
        records[key] = record
    if set(records) != {(kind, page) for kind in ("ECU_BE", "OEM_A8") for page in (0, 1)}:
        raise ValueError("Expected the four stable compiled OEM wire fixtures")
    output = []
    for page in (0, 1):
        project_request = request_frame(page)
        calls = []
        if mode == "ecu":
            record = records["ECU_BE", page]
            if record["stock"]["accepted"] or record["stock"]["response_hex"]:
                raise ValueError("Fixture unexpectedly claims stock BE support")
            blob = record["m06"]
            response = _checked_wire(blob, image_hash)
            if bytes.fromhex(blob["request_hex"]) != project_request:
                raise ValueError("Compiled BE request differs from the project request")
            def exchange(request):
                if request != project_request:
                    raise ValueError("Host emitted a different request")
                calls.append(request)
                return request + response  # Explicit modeled host echo.
            value = Session(exchange).read_page(page)
            if value.payload.hex() != record["decoded"]:
                raise ValueError("Decoded payload differs from compiled record")
            output.append({"page": page, "origin": "COMPILED_ECU_M06_SERVICE", "request_hex": project_request.hex(),
                           "response_hex": response.hex(), "payload_hex": value.payload.hex()})
        else:
            record = records["OEM_A8", page]
            blob = record["stock"]
            response = _checked_wire(blob, image_hash)
            patched_response = _checked_wire(record["m06"], fixture["m06_sha256"])
            if patched_response != response or blob["final_ssm_ram_hex"] != record["m06"]["final_ssm_ram_hex"]:
                raise ValueError("Stock/patched native A8 output differs")
            legacy_writes = lambda item: [(e["address"], e["size"], e["value"]) for e in item["events"] if e["mode"] == "w"]
            if legacy_writes(blob) != legacy_writes(record["m06"]):
                raise ValueError("Stock/patched native A8 write sequence differs")
            native_request = bytes.fromhex(blob["request_hex"])
            if native_request != A8_REQUESTS[page]:
                raise ValueError("Compiled native request differs from the fixed A8 whitelist")
            def exchange(request):
                if request != native_request:
                    raise ValueError("Facade emitted a request other than the actual compiled A8 input")
                calls.append(request)
                return request + response  # Explicit modeled host echo.
            result = HostFacade(exchange).exchange_project(project_request)
            ecu = records["ECU_BE", page]["m06"]
            if blob["fixture_values"] != ecu["fixture_values"]:
                raise ValueError("Cannot compare facade and ECU payloads from different virtual inputs")
            if result.local_response != bytes.fromhex(ecu["response_hex"]):
                raise ValueError("Local facade interpretation differs from actual compiled ECU service")
            output.append({"page": page, "origin": result.mode, "native_request_hex": native_request.hex(),
                           "native_response_hex": response.hex(), "local_response_hex": result.local_response.hex(),
                           "payload_hex": result.observation.payload.hex(), "native_A8_write_sequence_preserved": True})
        if len(calls) != 1:
            raise ValueError("Expected one outstanding exchange per page")
    return {
        "status": "PASS_ECU_PROTO_COMPILED_OEM_REPLAY" if mode == "ecu" else "PASS_STOCK_FACADE_COMPILED_OEM_REPLAY",
        "mode": mode, "pages": output, "rom_path": str(rom_path), "rom_sha256": image_hash,
        "fixture_path": str(fixture_path), "fixture_sha256": sha(fixture_path.read_bytes()),
        "fixture_scope": fixture["scope"], "physical_backend": False,
        "echo_provenance": "Modeled exact host echo; actual OEM RX echo-routing path was separately executed by fixture producer",
        "first_response_byte_provenance": "Fixture release from OEM-built FIFO; periodic first-byte timer release is not modeled",
        "limitations": ["Separate page observations", "No physical telemetry, response age, or atomic producer snapshot", "No electrical, timer or interrupt scheduling model"],
        "sources": [{"path": str(path), "sha256": sha(path.read_bytes())} for path in
                    (pathlib.Path(__file__), pathlib.Path(__file__).with_name("m06_protocol.py"), pathlib.Path(__file__).with_name("host_facade.py"))],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("ecu", "facade"))
    parser.add_argument("--fixture", required=True, type=pathlib.Path)
    parser.add_argument("--rom", required=True, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = replay(args.fixture.resolve(), args.rom.resolve(), args.mode)
    result["command"] = [sys.executable, *sys.argv]
    if args.output:
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result if not args.output else {"status": result["status"], "pages": 2, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
