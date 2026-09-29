"""Verify pinned compiled wire fixtures through the isolated research codecs."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from time import monotonic_ns
import json

from research_codec import MANIFESTS, encode_request, page_spec, parse_wire, validate_request, CodecError

ROOT = Path("C:/Dev/Astra_A2WC511R")
REPORTS = ROOT / "reports/local/m07_residency/protocol"
FIXTURE = REPORTS / "execution_01/compiled_protocol_fixtures.json"
FIXTURE_SHA = "8f1bf4e238e1b4e604d33ae16fcb14e76e8b969bd74ebc065600b9d061fd7868"
OVERLAYS = {"one_page": "005861f92771fc6b84e8e747faf5998130c12a528e3d73d2d35213d596de0513",
            "two_pages": "9dc63ee19afaef524755e00e1da3ca958b12f76ceeaf8e36c70cd3a9e3bf57a1"}


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def verify():
    for profile, (directory, expected_hash) in MANIFESTS.items():
        path = REPORTS / directory / "manifest.json"
        assert digest(path) == expected_hash
        manifest = json.loads(path.read_text())
        for name, expected in manifest["artifacts"].items():
            assert digest(path.parent / name) == expected
        pages = manifest["pages"] if profile == "two_pages" else [manifest]
        for index, record in enumerate(pages):
            spec = page_spec(profile, index)
            key = "request_without_checksum" if profile == "two_pages" else "request_without_checksum_hex"
            assert spec.prefix.hex() == record[key].lower()
            assert spec.opcode == record["response_opcode"] and record["version"] == 1 and record["page"] == index
            assert len(spec.fields) == record.get("data_bytes", record.get("raw_response_bytes"))
    assert digest(FIXTURE) == FIXTURE_SHA
    fixture = json.loads(FIXTURE.read_text())
    assert fixture["status"] == "PASS_SCOPED_SOFTWARE_TRANSPORT"
    assert fixture["physical"] is False and fixture["ROM_ownership_approved"] is False
    results = []
    for record in fixture["records"]:
        profile, page, executed = record["profile"], record["page"], record["m07"]
        spec = page_spec(profile, page)
        request = encode_request(profile, page)
        assert executed["request_hex"] == request.hex() and executed["accepted"] is True
        assert executed["rom_sha256"] == OVERLAYS[profile]
        assert record["stock"]["accepted"] is False and record["stock"]["response_hex"] == ""
        assert executed["raw_read_addresses"] == list(spec.addresses)
        events = executed["events"]
        assert sha256(json.dumps(events, sort_keys=True).encode()).hexdigest() == executed["events_sha256"]
        response = bytes.fromhex(executed["response_hex"])
        transmitted = bytes(int(e["value"], 16) for e in events if e["mode"] == "w" and e["address"] == "FFFFF013")
        assert transmitted == response[1:]
        decoded = parse_wire(profile, page, request, request + response)
        source = bytes.fromhex(executed["raw"])
        expected_raw = source if profile == "one_page" else (source[:4] if page == 0 else source[4:])
        assert decoded["raw_hex"] == expected_raw.hex()
        results.append({**decoded, "host_replay_utc": datetime.now(timezone.utc).isoformat(),
                        "host_replay_monotonic_ns": monotonic_ns(), "timestamp_is_ECU_age": False,
                        "request_hex": request.hex(), "response_hex": response.hex(),
                        "rom_sha256": executed["rom_sha256"], "fixture_sha256": FIXTURE_SHA,
                        "echo": "MODELED_HOST_ECHO", "physical_backend": False})
    assert {(x["profile"], x["page"]) for x in results} == {("one_page", 0), ("two_pages", 0), ("two_pages", 1)}
    for rejected in fixture["negative_ingress"]:
        assert rejected["status"] == "PASS_REJECTED"
        try:
            validate_request(rejected["profile"], rejected["page"], bytes.fromhex(rejected["request_hex"]))
        except CodecError:
            pass
        else:
            raise AssertionError("Host admitted a compiled negative request")
    return {"status": "PASS_OFFLINE_RESEARCH_CODEC", "valid_compiled_frames": len(results),
            "compiled_negative_requests": len(fixture["negative_ingress"]), "records": results,
            "physical_backend": False, "ROM_ownership_approved": False,
            "limitations": ["Research codecs are separate from supported native A8 host diagnostics", "No transport, electrical timing, timer, interrupt, or physical evidence", "No age proof or atomicity within/between pages", "No same-page nonce: outstanding request isolation and terminal faults belong to any future transport"]}


if __name__ == "__main__":
    result = verify()
    target = REPORTS / "codec_replay.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "valid_compiled_frames": result["valid_compiled_frames"], "compiled_negative_requests": result["compiled_negative_requests"], "output": str(target), "sha256": digest(target)}))
