"""Run isolated synthetic host tests and retain exact inputs and full output."""
import hashlib
import argparse
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("codec", "facade"), default="codec")
    suite = parser.parse_args().suite
    here = pathlib.Path(__file__).resolve().parent
    report_dir = here.parents[1] / "reports/local/m06_architecture/protocol"
    report_dir.mkdir(parents=True, exist_ok=True)
    module = "test_m06_protocol" if suite == "codec" else "test_host_facade"
    prefix = "host_codec_tests" if suite == "codec" else "host_facade_tests"
    passed = "PASS_SYNTHETIC_HOST_TESTS_ONLY" if suite == "codec" else "PASS_SYNTHETIC_HOST_FACADE_ONLY"
    command = [sys.executable, "-m", "unittest", "-v", module]
    result = subprocess.run(command, cwd=here, capture_output=True, text=True)
    log = result.stdout + result.stderr
    (report_dir / (prefix + ".log")).write_text(log, encoding="utf-8")
    artifacts = [here / name for name in ("m06_protocol.py", "test_m06_protocol.py", "run_validation.py")]
    if suite == "facade":
        artifacts += [here / name for name in ("host_facade.py", "test_host_facade.py")]
    artifacts.append(report_dir / (prefix + ".log"))
    manifest = {
        "status": passed if result.returncode == 0 else "FAIL",
        "suite": suite,
        "utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "cwd": str(here),
        "returncode": result.returncode,
        "python": sys.version,
        "artifacts": [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in artifacts],
        "physical_transport_created": False,
        "firmware_executed": False,
        "boundary": "These synthetic vectors test host logic. Compiled ECU response fixtures are separate evidence.",
    }
    (report_dir / (prefix + ".json")).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "report": str(report_dir / (prefix + ".json"))}))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
