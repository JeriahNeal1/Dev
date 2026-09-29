"""Synthetic wire vectors only. Compiled ECU execution is separate evidence."""
import threading
import unittest

from m06_protocol import (DecodedPage, Page, ProtocolError, RawPage, Session,
                          SessionError, decode_exchange, observation_reason,
                          request_frame)


def response(payload):
    prefix = bytes((0x80, 0xF0, 0x10, 5, 0xFE)) + bytes(payload)
    return prefix + bytes((sum(prefix) & 255,))


class WireTests(unittest.TestCase):
    def test_exact_known_requests(self):
        self.assertEqual(request_frame(0).hex().upper(), "8010F007BE4D3036010004FD")
        self.assertEqual(request_frame(1).hex().upper(), "8010F007BE4D3036010104FE")
        for invalid in (-1, 2, 255, 256, 0.0, "0", None, True):
            with self.assertRaises(ProtocolError):
                request_frame(invalid)

    def test_raw_page_preserves_all_values(self):
        for value in range(256):
            raw = bytes((value, 255 - value, value, 255 - value))
            request = request_frame(0)
            observation = decode_exchange(0, request, request + response(raw))
            self.assertIsInstance(observation, RawPage)
            self.assertEqual(observation.payload, raw)

    def test_page1_all_snapshots_and_oem_predicates(self):
        for snapshot in range(256):
            for target, current in ((1, 1), (0, 1), (1, 0), (8, 9), (255, 255)):
                reason = 0x80
                if snapshot != 17:
                    reason |= 1
                if (target, current) != (1, 1):
                    reason |= 2
                if max(divmod(snapshot, 16)) >= 9:
                    reason |= 4
                self.assertEqual(observation_reason(target, current, snapshot), reason)
                request = request_frame(1)
                observation = decode_exchange(1, request, request + response((target, current, snapshot, reason)))
                self.assertIsInstance(observation, DecodedPage)
                self.assertEqual(observation.payload, bytes((target, current, snapshot, reason)))

    def test_all_oem_byte_combinations(self):
        for target in range(256):
            for current in range(256):
                expected = 0x80 if (target, current) == (1, 1) else 0x82
                self.assertEqual(observation_reason(target, current, 0x11), expected)

    def test_exact_echo_not_blindly_stripped(self):
        for page in Page:
            request = request_frame(page)
            payload = (17, 17, 1, 2) if page == 0 else (1, 1, 17, 128)
            reply = response(payload)
            for offset in range(len(request)):
                for value in range(256):
                    if value != request[offset]:
                        echo = bytearray(request)
                        echo[offset] = value
                        with self.assertRaises(ProtocolError):
                            decode_exchange(page, request, bytes(echo) + reply)

    def test_all_header_mutations_rejected_even_with_correct_checksum(self):
        request = request_frame(0)
        reply = response((17, 17, 1, 2))
        for offset in range(5):
            for value in range(256):
                if value != reply[offset]:
                    mutated = bytearray(reply)
                    mutated[offset] = value
                    mutated[-1] = sum(mutated[:-1]) & 255
                    with self.assertRaises(ProtocolError):
                        decode_exchange(0, request, request + bytes(mutated))

    def test_truncation_extra_response_and_checksum_rejected(self):
        request = request_frame(0)
        reply = response((17, 17, 1, 2))
        wire = request + reply
        for length in range(281):
            if length != len(wire):
                with self.assertRaises(ProtocolError):
                    decode_exchange(0, request, (wire + bytes(281))[:length])
        with self.assertRaises(ProtocolError):
            decode_exchange(0, request, request + reply + reply)
        for value in range(256):
            if value != reply[-1]:
                with self.assertRaises(ProtocolError):
                    decode_exchange(0, request, wire[:-1] + bytes((value,)))

    def test_reason_reserved_bits_unknown_and_predicate_mismatch_rejected(self):
        request = request_frame(1)
        for reason in range(256):
            if reason != 0x80:
                with self.assertRaises(ProtocolError):
                    decode_exchange(1, request, request + response((1, 1, 17, reason)))
        for invalid in (-1, 256, True, "1"):
            with self.assertRaises(ProtocolError):
                observation_reason(invalid, 1, 17)

    def test_noncanonical_request_context_rejected(self):
        request = request_frame(0)
        with self.assertRaises(ProtocolError):
            decode_exchange(1, request, request + response((1, 1, 17, 128)))
        with self.assertRaises(ProtocolError):
            decode_exchange(0, bytearray(request), request + response((17, 17, 1, 2)))

    def test_identifier_absence_is_an_explicit_limit(self):
        # A raw page can have exactly the bytes of a valid decoded page. No
        # parser can distinguish this swapped/stale payload under RAW4 v1.
        ambiguous = response((1, 1, 17, 128))
        self.assertIsInstance(decode_exchange(0, request_frame(0), request_frame(0) + ambiguous), RawPage)
        self.assertIsInstance(decode_exchange(1, request_frame(1), request_frame(1) + ambiguous), DecodedPage)


class SessionTests(unittest.TestCase):
    def test_successful_serial_pages_are_independent(self):
        calls = []
        def exchange(request):
            calls.append(request)
            # Synthetic values deliberately change across the two requests.
            return request + response((17, 17, 1, 2) if request[9] == 0 else (2, 3, 35, 131))
        session = Session(exchange)
        raw = session.read_page(0)
        decoded = session.read_page(1)
        self.assertNotEqual(raw.snapshot, decoded.snapshot)
        self.assertEqual(calls, [request_frame(0), request_frame(1)])
        self.assertFalse(session.faulted)

    def test_malformed_response_faults_session_without_retry(self):
        calls = []
        def exchange(request):
            calls.append(request)
            return b""
        session = Session(exchange)
        with self.assertRaises(ProtocolError):
            session.read_page(0)
        self.assertTrue(session.faulted)
        with self.assertRaises(SessionError):
            session.read_page(1)
        self.assertEqual(len(calls), 1)

    def test_transport_failure_and_interrupt_fault_session(self):
        for failure in (TimeoutError("Synthetic timeout"), KeyboardInterrupt()):
            def exchange(request):
                raise failure
            session = Session(exchange)
            with self.assertRaises(type(failure)):
                session.read_page(0)
            self.assertTrue(session.faulted)
            with self.assertRaises(SessionError):
                session.read_page(0)

    def test_reentrant_request_rejected_without_second_transport_call(self):
        calls = []
        def exchange(request):
            calls.append(request)
            with self.assertRaises(SessionError):
                session.read_page(1)
            return request + response((17, 17, 1, 2))
        session = Session(exchange)
        session.read_page(0)
        self.assertEqual(len(calls), 1)
        self.assertFalse(session.faulted)

    def test_concurrent_request_rejected(self):
        entered, release = threading.Event(), threading.Event()
        results, errors = [], []
        def exchange(request):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("Synthetic test synchronization timeout")
            return request + response((17, 17, 1, 2))
        session = Session(exchange)
        def worker():
            try:
                results.append(session.read_page(0))
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(entered.wait(3))
            with self.assertRaises(SessionError):
                session.read_page(1)
        finally:
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 1)
        self.assertFalse(session.faulted)

    def test_invalid_page_never_calls_transport_or_faults_session(self):
        calls = []
        session = Session(lambda request: calls.append(request))
        with self.assertRaises(ProtocolError):
            session.read_page(2)
        self.assertFalse(session.faulted)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
