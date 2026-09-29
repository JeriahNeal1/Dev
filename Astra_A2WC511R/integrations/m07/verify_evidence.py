"""Verify final offline captures and write their bounded evidence manifest."""
from pathlib import Path
from datetime import datetime, timezone
import json

from backends import digest, load_profile
from protocol import REQUEST, observations, parse_wire

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "reports/local/m07_residency/host"


def main():
    profile, fixture = load_profile(HERE / "profile.json")
    for source in fixture["sources"]:
        assert digest(source["path"]) == source["sha256"], source["path"]
    captures = []
    for mode, name in (("replay", "capture_replay_final.jsonl"), ("native-virtual", "capture_native_final.jsonl")):
        path = OUT / name
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        assert rows[0]["type"] == "capture_start" and rows[0]["mode"] == mode
        assert rows[0]["profile_sha256"] == digest(HERE / "profile.json")
        assert rows[0]["fixture_sha256"] == profile["fixture"]["sha256"]
        assert rows[0]["full_ROM_attestation"] == "WITHDRAWN_A0_MASKED_RANGES"
        samples = rows[1:-1]
        assert len(samples) == len(fixture["samples"]) == 8
        previous = rows[0]["host_monotonic_ns"]
        for index, (row, expected) in enumerate(zip(samples, fixture["samples"])):
            assert row["type"] == "sample" and row["host_sample_index"] == index
            assert row["response_hex"] == expected["response_hex"]
            assert row["request_hex"] == REQUEST.hex()
            expected_observations = observations(parse_wire(bytes.fromhex(row["echo_response_wire_hex"])))
            assert all(row[key] == value for key, value in expected_observations.items())
            assert previous <= row["host_request_monotonic_ns"] <= row["host_response_monotonic_ns"]
            assert row["host_exchange_elapsed_ns"] == row["host_response_monotonic_ns"] - row["host_request_monotonic_ns"]
            previous = row["host_response_monotonic_ns"]
            for key in ("host_request_utc", "host_response_utc"):
                assert datetime.fromisoformat(row[key]).utcoffset().total_seconds() == 0
            assert row["provenance"]["native_RomRaider_parser"] == (mode == "native-virtual")
            assert row["provenance"]["physical_backend"] is False
        assert rows[-1]["type"] == "capture_end" and rows[-1]["status"] == "PASS_OFFLINE_CAPTURE"
        assert rows[-1]["samples_written"] == 8 and previous <= rows[-1]["host_monotonic_ns"]
        assert rows[-1]["error"] is None and rows[-1]["cleanup_error"] is None and rows[-1]["abort_errors"] == []
        captures.append({"mode": mode, "path": str(path.relative_to(ROOT)), "sha256": digest(path), "samples": 8})
    log = (OUT / "host_service_tests.log").read_text(encoding="utf-8-sig")
    assert "Ran 15 tests" in log and "\nOK" in log and "FAILED" not in log
    artifacts = set(HERE.glob("*.*"))
    artifacts.update(OUT / name for name in ("stock_six_a8_fixtures.json", "host_service_tests.log", "capture_replay_final.jsonl", "capture_native_final.jsonl", "capture_native_final.jsonl.native.stderr.log", "HOST_SERVICE_REVIEW.md", "host_gate_status.json"))
    artifacts.update(Path(item["path"]) for item in profile["classpath"])
    artifacts.update((Path(profile["java"]["path"]), Path(profile["build_log"]["path"]), Path(profile["stock_rom"]["path"])))
    result = {"schema": 1, "status": "PASS_OFFLINE_HOST_SERVICE", "utc": datetime.now(timezone.utc).isoformat(),
              "regression_groups": 15, "compiled_OEM_scenarios": 8, "captures": captures,
              "physical_backend": False, "ecu_patch": False, "full_ROM_attestation": "WITHDRAWN_A0_MASKED_RANGES",
              "artifacts": [{"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)} for path in sorted(artifacts)]}
    target = OUT / "host_evidence_manifest.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "manifest": str(target), "sha256": digest(target), "artifacts": len(artifacts)}))


if __name__ == "__main__":
    main()
