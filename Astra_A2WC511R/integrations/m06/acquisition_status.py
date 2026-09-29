"""Fail-closed local status entry; never connects or loads a provider."""
import argparse
import json
import pathlib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-full-rom-attestation", action="store_true")
    args = parser.parse_args()
    advisory = pathlib.Path(__file__).resolve().parents[2] / "reports/local/m06_architecture/protocol/ACQUISITION_COVERAGE_ADVISORY.md"
    result = {
        "COLLECTOR_FULL_IMAGE_ATTESTATION": "FAIL",
        "reason": "OEM A0 substitutes FF in required ROM spans; equal reads and CALID do not prove full physical-byte coverage",
        "additional_RAW4_channels_required": False,
        "physical_transport": "NOT_IMPLEMENTED_OR_INVOKED",
        "old_full_rom_procedure": "ATTESTATION_WITHDRAWN; do not start the 80-minute masked-image acquisition",
        "advisory": str(advisory),
        "offline_replay_remains_available": True,
    }
    print(json.dumps(result, indent=2))
    return 2 if args.require_full_rom_attestation else 0


if __name__ == "__main__":
    raise SystemExit(main())
