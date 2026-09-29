"""Focused offline tests; synthetic mutations never become physical evidence."""
import sys
sys.dont_write_bytecode = True
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ingest_acquisition', ROOT/'tools/ingest_acquisition.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class IngestionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = m.Inputs()
        cls.api, cls.checksum = m.load_apis(cls.inputs)
        cls.common = cls.inputs.json(m.OLD/'tools/prehardware/validator_registry.json')['common']
        cls.stock = cls.inputs.read(cls.common['baseline']['path'], m.STOCK_SHA)
        cls.scratch = ROOT/'tests/scratch'
        cls.scratch.mkdir(exist_ok=True)

    def statuses(self, raw):
        return {r['id']: r['status'] for r in m.image_checks(raw, self.common, self.checksum)}

    def test_valid_baseline_image_components(self):
        self.assertTrue(all(value == 'PASS' for value in self.statuses(self.stock).values()))
        m.validate_pair(self.stock, self.stock)

    def test_truncated_pair(self):
        with self.assertRaisesRegex(ValueError, '1MiB'):
            m.validate_pair(self.stock[:-1], self.stock[:-1])

    def test_unequal_pair(self):
        bad = bytearray(self.stock)
        bad[0x2222] ^= 1
        with self.assertRaisesRegex(ValueError, 'differ'):
            m.validate_pair(self.stock, bytes(bad))

    def test_wrong_calid(self):
        bad = bytearray(self.stock)
        bad[0x2000] ^= 1
        self.assertEqual(self.statuses(bad)['CALID'], 'FAIL')

    def test_wrong_ecuid(self):
        bad = bytearray(self.stock)
        bad[self.common['identity']['ecuid_offset']] ^= 1
        self.assertEqual(self.statuses(bad)['ECUID'], 'FAIL')

    def test_wrong_big_endian_vector(self):
        bad = bytearray(self.stock)
        bad[:4] = bad[:4][::-1]
        self.assertEqual(self.statuses(bad)['RESET_BIG_ENDIAN'], 'FAIL')

    def test_wrong_stack_pointer(self):
        bad = bytearray(self.stock)
        bad[7] ^= 1
        self.assertEqual(self.statuses(bad)['INITIAL_SP'], 'FAIL')

    def test_disabled_checksum_even_with_valid_arithmetic(self):
        bad = bytearray(self.stock)
        struct.pack_into('>III', bad, 0xFFB80, 0, 0, 0x5AA5A55A)
        self.assertEqual(self.statuses(bad)['CHECKSUM_VALIDITY'], 'PASS')
        self.assertEqual(self.statuses(bad)['CHECKSUM_GEOMETRY_ENABLED'], 'FAIL')

    def test_changed_checksum_geometry(self):
        bad = bytearray(self.stock)
        struct.pack_into('>I', bad, 0xFFB84, 0x100004)
        self.assertEqual(self.statuses(bad)['CHECKSUM_GEOMETRY_ENABLED'], 'FAIL')

    def test_invalid_checksum(self):
        bad = bytearray(self.stock)
        bad[0xFFB88] ^= 1
        self.assertEqual(self.statuses(bad)['CHECKSUM_VALIDITY'], 'FAIL')

    def test_missing_association_pending(self):
        result = m.association_review(None, m.Inputs(), m.STOCK_SHA, '0'*64)
        self.assertEqual(result['status'], 'PENDING')

    def fake_finalization(self, directory, physical=False, classification=None):
        finalized = directory/'finalized'
        finalized.mkdir()
        report = {'schema': 1, 'status': 'PASS_RAW_CAPTURE_INTEGRITY', 'capture_declared_physical': physical,
                  'classification': classification or 'VIRTUAL_FIXTURE_CAPTURE_NOT_CURRENT_ECU_ROM'}
        (finalized/'FINALIZATION.json').write_text(json.dumps(report))

    def test_false_physical_flag(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as scratch:
            path = Path(scratch)
            self.fake_finalization(path, classification='USER_PHYSICAL_CAPTURE_REQUIRES_SESSION_ASSOCIATION')
            with self.assertRaisesRegex(ValueError, 'Physical capture required'):
                m.validate_capture(path, m.Inputs(), self.api)

    def test_true_flag_does_not_promote_virtual_fixture(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as scratch:
            path = Path(scratch)
            self.fake_finalization(path, physical=True)
            with self.assertRaisesRegex(ValueError, 'virtual fixtures rejected'):
                m.validate_capture(path, m.Inputs(), self.api)

    def test_native_fake_event_rejected(self):
        kernel = (m.RK/'build/rk02_01/kernel.bin').read_bytes()
        with self.assertRaisesRegex(ValueError, 'provenance'):
            self.api.replay_native([{'sequence': 0, 'status': 0, 'physical': False}], kernel, m.KERNEL_SHA, True)

    def test_fake_host_identity_rejected_even_with_physical_labels(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as scratch:
            path = Path(scratch)
            self.fake_finalization(path, physical=True, classification='USER_PHYSICAL_CAPTURE_REQUIRES_SESSION_ASSOCIATION')
            report_path = path/'finalized/FINALIZATION.json'
            report = json.loads(report_path.read_text())
            report.update(current_ROM_identified=False, physical_session_association_proven=False,
                          kernel_sha256=m.KERNEL_SHA, client_sha256='4b681bcdb3c178b89382b37b207b4a7679f0a1e87ab13c7051e8cf8019c094ec')
            report_path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, 'Wrong RK02 kernel/host'):
                m.validate_capture(path, m.Inputs(), self.api)

    def test_failed_capture_publishes_no_raw_copies(self):
        # CLI-equivalent path: real pinned APIs, deliberately incomplete scratch capture.
        with tempfile.TemporaryDirectory(dir=self.scratch) as scratch:
            path = Path(scratch)
            capture = path/'capture'
            capture.mkdir()
            self.fake_finalization(capture)
            output = path/'output'
            result = m.ingest(capture, output)
            self.assertEqual(result['status'], 'FAIL')
            self.assertEqual(result['raw_copies'], [])
            self.assertFalse(result['current_ROM_identified'])
            self.assertFalse(list(output.glob('*.bin')))
            self.assertTrue((output/'INGESTION.json').exists())
            # Windows readonly file is restored only inside this test-owned scratch directory.
            (output/'INGESTION.json').chmod(0o666)

    def test_output_exclusivity(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as scratch:
            with self.assertRaises(FileExistsError):
                m.ingest(Path(scratch)/'absent', Path(scratch))

    def test_failed_image_quality_retains_evidence_without_promotion(self):
        # Publication unit only: replay is explicitly mocked, never physical acceptance.
        bad = bytearray(self.stock)
        bad[0xFFB88] ^= 1
        raw = bytes(bad)
        with tempfile.TemporaryDirectory(dir=self.scratch) as scratch:
            path = Path(scratch)
            evidence = path/'SYNTHETIC_TEST_ONLY.json'
            evidence.write_text('{"synthetic":true}')
            with patch.object(m, 'validate_capture', return_value=([raw, raw], evidence, {'synthetic_unit_stub': True})):
                result = m.ingest(path, path/'output')
            self.assertEqual(result['status'], 'FAIL_IMAGE_CHECKS_CAPTURE_PRESERVED')
            self.assertFalse(result['current_ROM_identified'])
            self.assertEqual(result['association']['status'], 'PENDING')
            self.assertEqual(len(result['stock_and_historical_differences']), 5)
            self.assertEqual(len(result['raw_copies']), 2)
            for row in result['raw_copies']:
                copy = Path(row['path'])
                self.assertEqual(copy.read_bytes(), raw)
                copy.chmod(0o666)
            (path/'output/INGESTION.json').chmod(0o666)

    def test_pinned_source_execution_ignores_existing_host_module(self):
        import types
        fake = types.ModuleType('host.finalize')
        fake.__file__ = str(m.RK/'host/finalize.py')
        fake.replay_native = 'not executable evidence'
        with patch.dict(sys.modules, {'host.finalize': fake}):
            api, unused = m.load_apis(m.Inputs())
            self.assertTrue(callable(api.replay_native))
            self.assertIs(sys.modules['host.finalize'], fake)

    def test_complete_diff_overlap_and_unknown(self):
        before = bytes(m.SIZE)
        after = bytearray(before)
        after[10:14] = bytes([1, 2, 3, 4])
        masks = [0]*m.SIZE
        masks[10] = (1 << m.CATEGORIES.index('calibration')) | (1 << m.CATEGORIES.index('executable'))
        masks[11] = 1 << m.CATEGORIES.index('checksum')
        diff = m.difference(before, after, masks)
        self.assertEqual(diff['changed_bytes'], 4)
        self.assertEqual(diff['category_counts_overlapping']['unknown'], 2)
        self.assertTrue(diff['ranges'][0]['overlap_or_uncertain'])
        self.assertTrue(diff['diaphora_review_trigger'])
        reconstructed = bytearray(before)
        for row in diff['ranges']:
            reconstructed[row['start']:row['end_exclusive']] = bytes.fromhex(row['after_hex'])
        self.assertEqual(reconstructed, after)

    def test_reuse_saved_catalog_and_complete_historical_diffs(self):
        report = m.compare_catalogs(self.stock, self.inputs, self.common)
        self.assertEqual(len(report['catalog_matches']), 37)
        self.assertEqual(len(report['stock_and_historical_differences']), 5)
        self.assertEqual(report['stock_and_historical_differences'][0]['changed_bytes'], 0)
        self.assertEqual(len(report['page_crc32']), 16)
        self.assertTrue(any(row['exact_sha256_match'] for row in report['catalog_matches']))
        for row in report['stock_and_historical_differences'][1:]:
            self.assertGreater(row['changed_bytes'], 1800)
            self.assertEqual(sum(r['end_exclusive']-r['start'] for r in row['ranges']), row['changed_bytes'])
        self.inputs.recheck()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IngestionTests))
    report = {'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'tests_run': result.testsRun,
              'failures': [{'test': str(test), 'error': error} for test, error in result.failures+result.errors],
              'scope': 'Offline component/integration negative tests and retained catalog reuse. No physical acquisition acceptance and no valid synthetic capture promotion.',
              'ingestion_source_sha256': m.sha((ROOT/'tools/ingest_acquisition.py').read_bytes()),
              'test_source_sha256': m.sha(Path(__file__).read_bytes()), 'provider_loaded': False}
    require_path = args.report.resolve()
    if not require_path.is_relative_to(ROOT):
        raise ValueError('Test report must remain under new Final tree')
    require_path.parent.mkdir(parents=True, exist_ok=True)
    with require_path.open('x') as output:
        json.dump(report, output, indent=2)
        output.write('\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
