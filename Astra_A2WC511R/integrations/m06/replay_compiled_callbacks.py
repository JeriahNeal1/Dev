"""Replay actual compiled callback bytes; framing and echo remain host-modeled."""
import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

from m06_protocol import Session, request_frame


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(fixture_path):
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture["status"] != "PASS" or fixture["classification"] != "VIRTUAL_COMPILED_HANDLER_PAYLOAD_NOT_PHYSICAL_TELEMETRY":
        raise ValueError("Compiled virtual fixture status/classification differs")
    build = pathlib.Path(fixture["build"])
    inputs = {
        "ROM_sha256": build / "A2WC511R_M06.EXPERIMENTAL_NOT_FLASH_READY.raw.bin",
        "ELF_sha256": build / "A2WC511R_M06.EXPERIMENTAL.elf",
        "payload_sha256": build / "m06.EXPERIMENTAL.code.bin",
    }
    for key, path in inputs.items():
        if digest(path) != fixture[key]:
            raise ValueError("Compiled input hash differs: " + key)
    if not fixture["cases"]:
        raise ValueError("No compiled callback cases")
    results = []
    event_ids = set()
    case_ids = set()
    read_addresses = ((0xFFFF4C75, 0xFFFF4C8D, 0xFFFF4CA1, 0xFFFF4C50),
                      (0xFFFF4BC1, 0xFFFF4BC2, 0xFFFF4C8D))
    for case in fixture["cases"]:
        page = case["page"]
        request = bytes.fromhex(case["request_hex"])
        response = bytes.fromhex(case["response_hex"])
        payload = bytes.fromhex(case["payload_hex"])
        if request != request_frame(page) or len(payload) != 4:
            raise ValueError("Compiled case does not match RAW4 request/payload shape")
        if case["event_id"] in event_ids or case["case_id"] in case_ids:
            raise ValueError("Repeated callback identity")
        event_ids.add(case["event_id"])
        case_ids.add(case["case_id"])
        reads = case["source_reads"]
        if tuple(int(read["address"], 16) for read in reads) != read_addresses[page]:
            raise ValueError("Observed source-read address sequence differs")
        if any(read["mode"] != "r" or read["size"] != 1 for read in reads):
            raise ValueError("Observed source-read type differs")
        if bytes(int(read["value"], 16) for read in reads) != payload[:len(reads)]:
            raise ValueError("Observed source bytes differ from returned payload")
        writes = case["tx_writes"]
        if tuple(int(write["address"], 16) for write in writes) != tuple(range(0xFFFF6492, 0xFFFF6496)):
            raise ValueError("Observed TX write extents differ")
        if any(write["mode"] != "w" or write["size"] != 1 for write in writes):
            raise ValueError("Observed TX write type differs")
        if bytes(int(write["value"], 16) for write in writes) != payload:
            raise ValueError("Observed TX writes differ from returned payload")
        calls = []
        def virtual_exchange(actual_request):
            if actual_request != request:
                raise ValueError("Replay request differs from compiled callback input")
            calls.append(actual_request)
            return actual_request + response  # Explicit modeled exact echo.
        observation = Session(virtual_exchange).read_page(page)
        if observation.payload != payload or len(calls) != 1:
            raise ValueError("Host interpretation differs from compiled payload")
        results.append({
            "case_id": case["case_id"], "event_id": case["event_id"],
            "page": page, "payload_hex": payload.hex(), "status": "PASS",
            "source_read_addresses": [read["address"] for read in reads],
            "tx_write_addresses": [write["address"] for write in writes],
            "fixture_execution_provenance": case["provenance"],
            "fixture_framing_provenance": case["framing_provenance"],
            "fixture_trace_sha256": case["trace_sha256"],
        })
    return {
        "status": "PASS_COMPILED_CALLBACK_PAYLOAD_HOST_REPLAY",
        "utc": datetime.now(timezone.utc).isoformat(),
        "fixture_path": str(fixture_path), "fixture_sha256": digest(fixture_path),
        "compiled_inputs": [{"path": str(path), "sha256": digest(path)} for path in inputs.values()],
        "cases_passed": len(results), "cases": results,
        "host_codec_sha256": digest(pathlib.Path(__file__).with_name("m06_protocol.py")),
        "replay_source_sha256": digest(pathlib.Path(__file__)),
        "echo_provenance": "Host-modeled exact request echo; no serial device",
        "wire_frame_provenance": "Host-assembled framing/checksum around actual compiled four-byte callback payload",
        "limits": ["No physical transport or telemetry", "No atomic page pair or freshness claim", "Actual OEM full RX/TX framing is separate root harness evidence", "Trace hashes retained from simulator fixture, not a new full-instruction-trace reproduction"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = replay(args.fixture.resolve())
    result["command"] = [sys.executable, *sys.argv]
    output = args.output or pathlib.Path(__file__).resolve().parents[2] / "reports/local/m06_architecture/protocol/compiled_callback_host_replay.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "cases": result["cases_passed"], "output": str(output)}))


if __name__ == "__main__":
    main()
