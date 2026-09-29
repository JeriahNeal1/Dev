import copy
import gc
from datetime import datetime
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import capture as capture_module
from backends import load_profile, ReplayTransport, NativeVirtualTransport
from protocol import ADDRESSES, Exchange, ProtocolError, REQUEST, SessionError, SnapshotClient, observations, parse_wire, validate_request

HERE = Path(__file__).resolve().parent
PROFILE = HERE / "profile.json"


def wire(raw=bytes((17,17,1,2,1,1))):
    header = bytes((0x80,0xF0,0x10,7,0xE8)) + raw
    return REQUEST + header + bytes((sum(header)&255,))


class MemoryTransport:
    def __init__(self, reply=None):
        self.reply = wire() if reply is None else reply
        self.calls = 0
        self.closed = False
    def exchange(self, request):
        validate_request(request)
        self.calls += 1
        return Exchange(self.reply, {"classification":"SYNTHETIC_UNIT_VECTOR"})
    def abort(self):self.closed=True
    def close(self):self.closed=True


class ProtocolTests(unittest.TestCase):
    def test_request_whitelist_rejects_all_mutations_and_other_commands(self):
        validate_request(REQUEST)
        for offset in range(len(REQUEST)):
            for value in range(256):
                if value == REQUEST[offset]:continue
                bad=bytearray(REQUEST);bad[offset]=value
                if offset != len(REQUEST)-1:bad[-1]=sum(bad[:-1])&255
                with self.assertRaises(ProtocolError):validate_request(bytes(bad))
        for bad in (b"",REQUEST+b"\0",bytearray(REQUEST)):
            with self.assertRaises(ProtocolError):validate_request(bad)

    def test_exact_echo_header_length_checksum_and_no_stale_fallback(self):
        good=wire()
        self.assertEqual(parse_wire(good), bytes((17,17,1,2,1,1)))
        for offset in list(range(len(REQUEST)))+list(range(len(REQUEST),len(REQUEST)+5)):
            bad=bytearray(good);bad[offset]^=1
            if offset>=len(REQUEST):bad[-1]=sum(bad[len(REQUEST):-1])&255
            with self.assertRaises(ProtocolError):parse_wire(bytes(bad))
        for bad in (good[:-1],good+b"\0",good[len(REQUEST):],good[:-1]+bytes((good[-1]^1,))):
            with self.assertRaises(ProtocolError):parse_wire(bad)

    def test_reason_all_oem_pairs_and_all_snapshots(self):
        for target in range(256):
            for current in range(256):
                reason=observations(bytes((17,17,1,2,target,current)))["reason_mask"]
                self.assertEqual(reason,0x80 if (target,current)==(1,1) else 0x82)
        for snapshot in range(256):
            result=observations(bytes((snapshot,snapshot,0,0,3,4)))
            expected=0x82|(1 if snapshot!=17 else 0)|(4 if max(divmod(snapshot,16))>8 else 0)
            self.assertEqual(result["reason_mask"],expected)
            self.assertEqual(result["freshness"],"UNKNOWN")
            self.assertEqual(result["raw"]["oem_target"],3)
            self.assertEqual(result["raw"]["oem_current"],4)

    def test_timestamp_and_raw_record_contract(self):
        backend=MemoryTransport();client=SnapshotClient(backend)
        result=client.capture()
        self.assertEqual(result["host_sample_index"],0)
        self.assertGreaterEqual(result["host_response_monotonic_ns"],result["host_request_monotonic_ns"])
        self.assertEqual(result["host_exchange_elapsed_ns"],result["host_response_monotonic_ns"]-result["host_request_monotonic_ns"])
        self.assertIsNotNone(datetime.fromisoformat(result["host_request_utc"]).utcoffset())
        self.assertIsNotNone(datetime.fromisoformat(result["host_response_utc"]).utcoffset())
        self.assertEqual(set(result["raw_by_address"]),{f"{a:08X}" for a in ADDRESSES})
        self.assertEqual(backend.calls,1)
        client.close()
        with self.assertRaises(SessionError):client.capture()

    def test_parser_failure_terminal_no_retry(self):
        backend=MemoryTransport(b"");client=SnapshotClient(backend)
        with self.assertRaises(ProtocolError):client.capture()
        self.assertEqual(client.state,"FAULTED")
        self.assertTrue(backend.closed)
        with self.assertRaises(SessionError):client.capture()
        self.assertEqual(backend.calls,1)

    def test_timeout_aborts_and_late_result_never_becomes_sample(self):
        release=threading.Event()
        class Delayed(MemoryTransport):
            def exchange(self, request):
                self.calls+=1;release.wait(3);return Exchange(wire(),{})
            def abort(self):
                self.closed=True;release.set()
        backend=Delayed();client=SnapshotClient(backend,25)
        started=time.monotonic()
        with self.assertRaises(TimeoutError):client.capture()
        self.assertLess(time.monotonic()-started,1)
        self.assertEqual(client.count,0)
        self.assertEqual(client.state,"FAULTED")
        with self.assertRaises(SessionError):client.capture()
        self.assertEqual(backend.calls,1)

    def test_one_outstanding_request(self):
        entered,release=threading.Event(),threading.Event()
        class Paused(MemoryTransport):
            def exchange(self,request):
                self.calls+=1;entered.set();release.wait(3);return Exchange(wire(),{})
        backend=Paused();client=SnapshotClient(backend,2000);results=[]
        thread=threading.Thread(target=lambda:results.append(client.capture()))
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            with self.assertRaises(SessionError):client.capture()
            with self.assertRaises(SessionError):client.close()
        finally:
            release.set();thread.join(2)
        self.assertEqual(backend.calls,1)
        self.assertEqual(len(results),1)
        client.close()

    def test_abort_error_retained_with_original_fault(self):
        class FailedAbort(MemoryTransport):
            def abort(self):raise RuntimeError("synthetic abort failure")
        client=SnapshotClient(FailedAbort(b""))
        with self.assertRaises(ProtocolError):client.capture()
        self.assertEqual(client.abort_errors[0]["message"],"synthetic abort failure")


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.profile,cls.fixture=load_profile(PROFILE)

    def test_replay_is_finite_and_refuses_unknown_request(self):
        backend=ReplayTransport(self.profile,self.fixture)
        with self.assertRaises(ProtocolError):backend.exchange(b"")
        client=SnapshotClient(backend)
        for expected in self.fixture["samples"]:
            self.assertEqual(client.capture()["response_hex"],expected["response_hex"])
        with self.assertRaises(EOFError):client.capture()
        self.assertEqual(client.state,"FAULTED")

    def test_both_jsonl_backends_match_all_actual_oem_samples(self):
        captured=[]
        with tempfile.TemporaryDirectory(prefix="m07_capture_test_") as temporary:
            for backend in ("replay","native-virtual"):
                output=Path(temporary)/(backend+".jsonl")
                summary=capture_module.capture(output,PROFILE,backend)
                self.assertEqual(summary["status"],"PASS_OFFLINE_CAPTURE")
                rows=[json.loads(line) for line in output.read_text().splitlines()]
                samples=[row for row in rows if row["type"]=="sample"]
                self.assertEqual(len(samples),len(self.fixture["samples"]))
                self.assertEqual([sample["response_hex"] for sample in samples],[sample["response_hex"] for sample in self.fixture["samples"]])
                self.assertTrue(all(s["provenance"]["native_RomRaider_parser"]==(backend=="native-virtual") for s in samples))
                self.assertTrue(all(s["freshness"]=="UNKNOWN" and s["reason_mask"]&0x80 for s in samples))
                captured.append([(s["raw_hex"],s["reason_mask"],s["request_hex"]) for s in samples])
                self.assertEqual(rows[0]["type"],"capture_start")
                self.assertEqual(rows[-1]["type"],"capture_end")
            self.assertEqual(captured[0],captured[1])

    def test_native_runtime_hash_failure_before_process_creation(self):
        profile=copy.deepcopy(self.profile);profile["classpath"][0]["sha256"]="0"*64
        with tempfile.TemporaryDirectory(prefix="m07_hash_test_") as temporary:
            log=Path(temporary)/"stderr.log"
            with self.assertRaises(ValueError):NativeVirtualTransport(profile,self.fixture,log)
            self.assertFalse(log.exists())

    def test_native_owned_child_abort_and_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="m07_native_lifetime_test_") as temporary:
            backend=NativeVirtualTransport(self.profile,self.fixture,Path(temporary)/"stderr.log")
            process=backend.process
            self.assertIsNone(process.poll())
            backend.abort()
            backend.close()
            self.assertIsNotNone(process.poll())
            self.assertTrue(process.stdin.closed and process.stdout.closed and backend.stderr.closed)
            with self.assertRaises(RuntimeError):backend.exchange(REQUEST)
            # Windows retains the Popen process handle until object disposal.
            del backend, process
            gc.collect()

    def test_constructor_failure_still_records_terminal_capture(self):
        with tempfile.TemporaryDirectory(prefix="m07_constructor_test_") as temporary:
            output=Path(temporary)/"capture.jsonl"
            with patch.object(capture_module,"NativeVirtualTransport",side_effect=RuntimeError("synthetic startup failure")):
                summary=capture_module.capture(output,PROFILE,"native-virtual",count=1)
            rows=[json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(summary["status"],"FAILED_TERMINAL")
            self.assertEqual(summary["samples_written"],0)
            self.assertEqual([r["type"] for r in rows],["capture_start","capture_failure","capture_end"])

    def test_cleanup_failure_is_not_success(self):
        class CleanupFailure(MemoryTransport):
            def close(self):raise RuntimeError("synthetic cleanup failure")
        with tempfile.TemporaryDirectory(prefix="m07_cleanup_test_") as temporary:
            output=Path(temporary)/"capture.jsonl"
            with patch.object(capture_module,"ReplayTransport",return_value=CleanupFailure()):
                summary=capture_module.capture(output,PROFILE,"replay",count=1)
            self.assertEqual(summary["status"],"FAILED_TERMINAL")
            self.assertEqual(summary["cleanup_error"]["message"],"synthetic cleanup failure")

    def test_no_overwrite_no_physical_backend_no_repeat(self):
        with tempfile.TemporaryDirectory(prefix="m07_rejection_test_") as temporary:
            output=Path(temporary)/"capture.jsonl";output.write_text("preserve")
            with self.assertRaises(FileExistsError):capture_module.capture(output,PROFILE,"replay",count=1)
            self.assertEqual(output.read_text(),"preserve")
            with self.assertRaises(ValueError):capture_module.capture(output,PROFILE,"physical",count=1)
            with self.assertRaises(ValueError):capture_module.capture(output,PROFILE,"replay",count=len(self.fixture["samples"])+1)


if __name__=="__main__":unittest.main(verbosity=2)
