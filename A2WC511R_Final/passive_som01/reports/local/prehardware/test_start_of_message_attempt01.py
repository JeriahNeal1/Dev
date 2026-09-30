"""Offline copied-broker START_OF_MESSAGE regression tests; fake provider only."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from capture import capture
from test_read_only import run_worker
from transport import HERE, IDENTITY_REQUEST, REQUEST, parse_identity, parse_wire

RESULTS = {}
ROOT = HERE.parents[1]


class StartOfMessageTests(unittest.TestCase):
    def assert_clean_failure(self, fault):
        run, frames = run_worker(b'IDENTITY\nSNAPSHOT\nCLOSE\n', fault)
        self.assertNotEqual(run.returncode, 0, fault)
        self.assertEqual(frames, [IDENTITY_REQUEST.hex()], fault)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(rows[-1], {'type': 'terminal_failure', 'cleanup_ok': True}, fault)
        for operation in ('StopFilter', 'Disconnect', 'Close'):
            self.assertEqual(run.stderr.count(('FAKE '+operation+'\n').encode()), 1, fault)
        return run

    def test_valid_markers_and_fragmentation_preserve_wire(self):
        expected_counts = {None: 0, 'som': 2, 'som_before_echo': 1,
                           'som_before_response': 1, 'som_split': 2, 'som_four': 4}
        baseline = None
        for fault, count in expected_counts.items():
            with self.subTest(fault=fault):
                run, frames = run_worker(b'IDENTITY\nSNAPSHOT\nCLOSE\n', fault)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(frames, [IDENTITY_REQUEST.hex(), REQUEST.hex()])
                rows = [json.loads(line) for line in run.stdout.splitlines()]
                self.assertEqual(rows[-1], {'type': 'closed'})
                exchanges = rows[1:3]
                self.assertEqual(parse_identity(bytes.fromhex(exchanges[0]['wire_hex']))['ecu_id'], '2F12515306')
                self.assertEqual(parse_wire(bytes.fromhex(exchanges[1]['wire_hex'])), bytes.fromhex('111101020101'))
                wires = [row['wire_hex'] for row in exchanges]
                if baseline is None:
                    baseline = wires
                self.assertEqual(wires, baseline)
                for exchange in exchanges:
                    events = exchange['provider_frames']
                    markers = [e for e in events if e['rx_status'] == 2]
                    self.assertEqual(len(markers), count)
                    self.assertEqual(''.join(e['raw_hex'] for e in events), exchange['wire_hex'])
                    for marker in markers:
                        self.assertEqual({k: marker[k] for k in ('protocol', 'tx_flags', 'data_size', 'extra_data_index', 'message_count', 'raw_hex')},
                                         {'protocol': 3, 'tx_flags': 0, 'data_size': 0, 'extra_data_index': 0, 'message_count': 1, 'raw_hex': ''})
        RESULTS['positive_fixtures'] = [name or 'original_no_marker' for name in expected_counts]

    def test_invalid_marker_metadata_rejected(self):
        faults = ['som_nonempty', 'som_oversized', 'som_unknown', 'som_mixed',
                  'som_wrong_protocol', 'som_tx_flags', 'som_extra', 'som_zero_status',
                  'som_count_zero', 'som_count_many']
        for fault in faults:
            with self.subTest(fault=fault):
                self.assert_clean_failure(fault)
        RESULTS['invalid_marker_fixtures'] = faults

    def test_indicator_bound_and_partial_message_boundary(self):
        for fault in ('som_flood', 'som_late'):
            with self.subTest(fault=fault):
                run = self.assert_clean_failure(fault)
                self.assertIn(b'unsupported START_OF_MESSAGE indication', run.stderr)
        RESULTS['bounded_marker_count'] = 4
        RESULTS['flood_and_partial_message_rejection'] = 'PASS'

    def test_marker_does_not_extend_deadline_or_supply_missing_data(self):
        start = time.monotonic()
        run = self.assert_clean_failure('som_no_payload')
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 4)
        self.assertIn(b'RX deadline', run.stderr)
        RESULTS['marker_without_data'] = {'status': 'PASS_TERMINAL_TIMEOUT', 'elapsed_seconds': elapsed}

    def test_existing_echo_checksum_identity_guards_survive_markers(self):
        for fault in ('som_missing_echo', 'som_echo_mismatch', 'som_bad_checksum', 'som_wrong_identity'):
            with self.subTest(fault=fault):
                self.assert_clean_failure(fault)
        RESULTS['unchanged_wire_guards'] = ['missing_echo', 'echo_mismatch', 'checksum', 'identity']

    def test_120_sample_capture_retains_markers_and_reaps_fake_worker(self):
        original_popen = subprocess.Popen
        children = []

        def fake_markers(*args, **kwargs):
            self.assertEqual(args[0], [str(HERE/'build/broker.exe'), '--fake'])
            kwargs['env']['A2WC_FAKE_FAULT'] = 'som_split'
            child = original_popen(*args, **kwargs)
            children.append(child)
            return child

        with tempfile.TemporaryDirectory(prefix='som120-', dir=ROOT/'reports/local/prehardware') as temporary:
            output = Path(temporary)/'capture.jsonl'
            with patch('subprocess.Popen', fake_markers):
                result = capture(output, 'fake-j2534', 120, 0)
            self.assertEqual(result['status'], 'PASS_CAPTURE_ONLY', result)
            self.assertEqual(result['samples_written'], 120)
            self.assertIsNone(result['error'])
            self.assertIsNone(result['cleanup_error'])
            rows = [json.loads(line) for line in output.read_text().splitlines()]
            identities = [row for row in rows if row['type'] == 'identity']
            samples = [row for row in rows if row['type'] == 'sample']
            self.assertEqual(len(identities), 1)
            self.assertEqual(identities[0]['ecu_id'], '2F12515306')
            self.assertEqual(len(samples), 120)
            self.assertEqual([row['host_sample_index'] for row in samples], list(range(120)))
            for row in samples:
                events = row['provenance']['provider_frames']
                self.assertEqual(sum(event['rx_status'] == 2 for event in events), 2)
                self.assertEqual(''.join(event['raw_hex'] for event in events), row['echo_response_wire_hex'])
            stderr = Path(str(output)+'.provider.stderr.log').read_text()
            self.assertNotIn('FORBIDDEN_', stderr)
            wires = [line.removeprefix('FAKE WIRE ') for line in stderr.splitlines() if line.startswith('FAKE WIRE ')]
            self.assertEqual(wires, [IDENTITY_REQUEST.hex()]+[REQUEST.hex()]*120)
            for operation in ('StopFilter', 'Disconnect', 'Close'):
                self.assertEqual(stderr.splitlines().count('FAKE '+operation), 1)
            self.assertEqual(len(children), 1)
            self.assertEqual(children[0].poll(), 0)
        RESULTS['full_capture'] = {'status': 'PASS_CAPTURE_ONLY', 'samples': 120,
                                   'BF_transmits': 1, 'A8_transmits': 120,
                                   'markers_per_exchange': 2, 'worker_exit': 0,
                                   'cleanup_error': None}


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StartOfMessageTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    RESULTS.update(status='PASS' if result.wasSuccessful() else 'FAIL',
                   test_groups=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   real_provider_loaded=False,
                   source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   build_manifest_sha256=hashlib.sha256((HERE/'build/BUILD_MANIFEST.json').read_bytes()).hexdigest())
    report = ROOT/'reports/local/prehardware/START_OF_MESSAGE_TESTS.json'
    with report.open('x', encoding='utf-8') as stream:
        json.dump(RESULTS, stream, indent=2)
        stream.write('\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
