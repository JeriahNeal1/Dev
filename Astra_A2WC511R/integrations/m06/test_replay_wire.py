"""Integrity regressions over copies of the actual OEM wire fixtures."""
import copy
import hashlib
import json
import pathlib
import tempfile
import subprocess
import sys
import unittest

from replay_wire import replay


ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "reports/local/m06_architecture/wire/compiled_wire_fixtures.json"
STOCK = pathlib.Path("C:/Dev/SubaruRoms/OEM/A2WC511R.bin")
PATCH = ROOT / "work/builds/m06_04/A2WC511R_M06.EXPERIMENTAL_NOT_FLASH_READY.raw.bin"


class WireReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def reject_fixture(self, altered, mode="facade"):
        with tempfile.TemporaryDirectory(prefix="m06_wire_negative_") as temporary:
            path = pathlib.Path(temporary) / "fixture.json"
            path.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaises(ValueError):
                replay(path, STOCK if mode == "facade" else PATCH, mode)

    def test_both_actual_compiled_modes(self):
        for mode, rom in (("ecu", PATCH), ("facade", STOCK)):
            result = replay(FIXTURE, rom, mode)
            self.assertTrue(result["status"].startswith("PASS_"))
            self.assertEqual(len(result["pages"]), 2)
            self.assertFalse(result["physical_backend"])

    def test_wrong_image_and_physical_mode_rejected(self):
        with self.assertRaises(ValueError):
            replay(FIXTURE, STOCK, "ecu")
        with self.assertRaises(ValueError):
            replay(FIXTURE, STOCK, "physical")

    def test_acquisition_entry_fails_closed_without_transport(self):
        result = subprocess.run([sys.executable, str(ROOT / "integrations/m06/acquisition_status.py"),
                                 "--require-full-rom-attestation"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        status = json.loads(result.stdout)
        self.assertEqual(status["COLLECTOR_FULL_IMAGE_ATTESTATION"], "FAIL")
        self.assertEqual(status["physical_transport"], "NOT_IMPLEMENTED_OR_INVOKED")

    def test_event_integrity_and_transmit_bytes_rejected(self):
        altered = copy.deepcopy(self.fixture)
        altered["records"][0]["m06"]["events_sha256"] = "0" * 64
        self.reject_fixture(altered, "ecu")
        altered = copy.deepcopy(self.fixture)
        reply = bytearray.fromhex(altered["records"][0]["m06"]["response_hex"])
        reply[5] ^= 1
        altered["records"][0]["m06"]["response_hex"] = reply.hex()
        self.reject_fixture(altered, "ecu")

    def test_same_final_state_does_not_hide_changed_legacy_write(self):
        altered = copy.deepcopy(self.fixture)
        blob = next(r for r in altered["records"] if r["kind"] == "OEM_A8")["m06"]
        event = next(e for e in blob["events"] if e["mode"] == "w" and e["address"] != "FFFFF013")
        event["value"] = f'{int(event["value"], 16) ^ 1:08X}'
        blob["events_sha256"] = hashlib.sha256(json.dumps(blob["events"], sort_keys=True).encode()).hexdigest()
        self.reject_fixture(altered)

    def test_cross_scenario_parity_and_duplicate_pages_rejected(self):
        altered = copy.deepcopy(self.fixture)
        next(r for r in altered["records"] if r["kind"] == "OEM_A8")["stock"]["fixture_values"]["0xffff4c75"] ^= 1
        self.reject_fixture(altered)
        altered = copy.deepcopy(self.fixture)
        altered["records"].append(copy.deepcopy(altered["records"][0]))
        self.reject_fixture(altered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
