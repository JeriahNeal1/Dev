"""Capture host-only OEM observations to JSONL, with offline backends only."""
import argparse
from pathlib import Path
import json
import sys
import time
import uuid

from backends import load_profile, ReplayTransport, NativeVirtualTransport, digest
from protocol import ADDRESSES, FIELDS, REQUEST, SnapshotClient, utc_now


def capture(output, profile_path, backend, count=None, interval_ms=0, timeout_ms=1000):
    if backend not in ("replay", "native-virtual"):
        raise ValueError("No physical backend is implemented")
    if not isinstance(interval_ms, int) or isinstance(interval_ms, bool) or not 0 <= interval_ms <= 60000:
        raise ValueError("Interval must be integer 0..60000 ms of host pacing")
    profile, fixture = load_profile(profile_path)
    count = len(fixture["samples"]) if count is None else count
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= len(fixture["samples"]):
        raise ValueError("Count must fit the finite recorded virtual fixture; no automatic repeat")
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or not 1 <= timeout_ms <= 60000:
        raise ValueError("Timeout must be integer 1..60000 ms")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    transport, client, failure, cleanup_failure = None, None, None, None
    written = 0
    started_ns = time.monotonic_ns()
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        def emit(row):
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")
            stream.flush()
        emit({"type": "capture_start", "schema": 1, "session_id": str(uuid.uuid4()), "host_utc": utc_now(),
              "host_monotonic_ns": started_ns, "mode": backend, "classification": fixture["classification"],
              "physical_backend": False, "ecu_patch": False, "profile_sha256": digest(profile_path),
              "fixture_sha256": profile["fixture"]["sha256"], "stock_rom_sha256": profile["stock_rom"]["sha256"],
              "fields": dict(zip(FIELDS, [f"{a:08X}" for a in ADDRESSES])), "request_hex": REQUEST.hex(),
              "samples_requested": count, "host_interval_ms": interval_ms, "host_timeout_ms": timeout_ms,
              "full_ROM_attestation": "WITHDRAWN_A0_MASKED_RANGES", "timestamps_are_ECU_data_age": False})
        try:
            transport = (ReplayTransport(profile, fixture) if backend == "replay" else
                         NativeVirtualTransport(profile, fixture, output.with_suffix(output.suffix + ".native.stderr.log")))
            client = SnapshotClient(transport, timeout_ms)
            for index in range(count):
                if index and interval_ms:
                    time.sleep(interval_ms / 1000)
                emit(client.capture())
                written += 1
        except BaseException as error:
            failure = {"type": type(error).__name__, "message": str(error)}
            emit({"type": "capture_failure", "host_utc": utc_now(), "host_monotonic_ns": time.monotonic_ns(),
                  "error": failure, "samples_written": written, "retry_attempted": False})
        finally:
            try:
                if client is not None:
                    client.close()
                elif transport is not None:
                    transport.close()
            except BaseException as error:
                cleanup_failure = {"type": type(error).__name__, "message": str(error)}
            summary = {"type": "capture_end", "status": "PASS_OFFLINE_CAPTURE" if failure is None and cleanup_failure is None else "FAILED_TERMINAL",
                       "samples_written": written, "samples_requested": count, "host_utc": utc_now(),
                       "host_monotonic_ns": time.monotonic_ns(), "error": failure, "cleanup_error": cleanup_failure,
                       "abort_errors": client.abort_errors if client is not None else [],
                       "physical_backend": False, "ecu_patch": False, "automatic_retry": False}
            emit(summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", required=True, choices=("replay", "native-virtual"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", type=Path, default=Path(__file__).with_name("profile.json"))
    parser.add_argument("--count", type=int)
    parser.add_argument("--interval-ms", type=int, default=0)
    parser.add_argument("--timeout-ms", type=int, default=1000)
    args = parser.parse_args()
    try:
        result = capture(args.output, args.profile, args.backend, args.count, args.interval_ms, args.timeout_ms)
    except Exception as error:
        print(json.dumps({"status": "CONFIGURATION_REJECTED", "error": str(error), "physical_backend": False}), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0 if result["status"] == "PASS_OFFLINE_CAPTURE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
