"""Negative provenance tests on copies of the retained compiled fixture."""
import copy
import json
import pathlib
import tempfile
import unittest

from replay_compiled_callbacks import replay


FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "reports/local/m06_architecture/runtime/20260925T222344.398428Z/compiled_callback_fixtures.json"


class CompiledReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def assert_rejected(self, altered):
        with tempfile.TemporaryDirectory(prefix="m06_replay_negative_") as temporary:
            path = pathlib.Path(temporary) / "fixture.json"
            path.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaises(ValueError):
                replay(path)

    def test_changed_compiled_identity_rejected(self):
        for key in ("ROM_sha256", "ELF_sha256", "payload_sha256"):
            altered = copy.deepcopy(self.fixture)
            altered[key] = "0" * 64
            self.assert_rejected(altered)

    def test_invented_payload_or_wrong_source_read_rejected(self):
        for mutate in (
            lambda case: case.update(payload_hex="00000000"),
            lambda case: case["source_reads"][0].update(address="FFFF7400"),
            lambda case: case["tx_writes"][0].update(value="00000000"),
            lambda case: case["tx_writes"][0].update(address="FFFF7400"),
        ):
            altered = copy.deepcopy(self.fixture)
            mutate(altered["cases"][0])
            self.assert_rejected(altered)

    def test_repeated_callback_and_corrupt_response_rejected(self):
        altered = copy.deepcopy(self.fixture)
        altered["cases"].append(copy.deepcopy(altered["cases"][0]))
        self.assert_rejected(altered)
        altered = copy.deepcopy(self.fixture)
        reply = bytearray.fromhex(altered["cases"][0]["response_hex"])
        reply[-1] ^= 1
        altered["cases"][0]["response_hex"] = reply.hex()
        self.assert_rejected(altered)


if __name__ == '__main__':
    unittest.main(verbosity=2)
