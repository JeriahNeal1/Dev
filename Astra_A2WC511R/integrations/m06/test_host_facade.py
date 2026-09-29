"""Host facade synthetic tests; values are fixtures, not ECU telemetry."""
import unittest

from host_facade import ADDRESS_PAGES, A8_REQUESTS, MODE, HostFacade
from m06_protocol import ProtocolError, SessionError, request_frame


def native_reply(payload):
    prefix = bytes((0x80, 0xF0, 0x10, len(payload) + 1, 0xE8)) + bytes(payload)
    return prefix + bytes((sum(prefix) & 255,))


class FacadeTests(unittest.TestCase):
    def test_native_whitelist_and_local_origin(self):
        calls = []
        def native(request):
            calls.append(request)
            payload = (17, 17, 1, 2) if request == A8_REQUESTS[0] else (1, 1, 17)
            return request + native_reply(payload)
        facade = HostFacade(native)
        page0 = facade.exchange_project(request_frame(0))
        page1 = facade.exchange_project(request_frame(1))
        self.assertEqual(calls, list(A8_REQUESTS))
        for page, result in enumerate((page0, page1)):
            self.assertEqual(result.mode, MODE)
            self.assertEqual(result.page, page)
            self.assertEqual(result.project_request[4], 0xBE)
            self.assertEqual(result.native_request[4], 0xA8)
            self.assertEqual(result.native_request[5], 0)
            self.assertEqual(result.native_wire[len(result.native_request) + 4], 0xE8)
            self.assertEqual(result.local_response[4], 0xFE)
            addresses = tuple(int.from_bytes(result.native_request[i:i+3], 'big') | 0xFF000000 for i in range(6, len(result.native_request)-1, 3))
            self.assertEqual(addresses, ADDRESS_PAGES[page])
        self.assertEqual(page0.local_response.hex().upper(), "80F01005FE11110102A8")
        self.assertEqual(page1.local_response.hex().upper(), "80F01005FE0101118016")

    def test_every_project_byte_mutation_rejected_before_native_call(self):
        calls = []
        facade = HostFacade(lambda request: calls.append(request))
        canonical = (request_frame(0), request_frame(1))
        for request in canonical:
            for offset in range(len(request)):
                for value in range(256):
                    modified = bytearray(request)
                    modified[offset] = value
                    if offset != len(request)-1:
                        modified[-1] = sum(modified[:-1]) & 255
                    modified = bytes(modified)
                    if modified not in canonical:
                        with self.assertRaises(ProtocolError):
                            facade.exchange_project(modified)
        for invalid in (b"", canonical[0][:-1], canonical[0] + b"\0", bytearray(canonical[0])):
            with self.assertRaises(ProtocolError):
                facade.exchange_project(invalid)
        self.assertEqual(calls, [])
        self.assertFalse(facade.faulted)

    def test_local_reason_all_snapshots_and_actual_oem_values(self):
        for snapshot in range(256):
            # Actual decoded bytes deliberately differ from packed nibbles.
            # Facade must report them unchanged, including held-value cases.
            target, current = 3, 4
            facade = HostFacade(lambda request: request + native_reply((target, current, snapshot)))
            result = facade.exchange_project(request_frame(1))
            expected = 0x82 | (snapshot != 17) | (4 if max(divmod(snapshot, 16)) > 8 else 0)
            self.assertEqual(result.observation.payload, bytes((target, current, snapshot, expected)))

    def test_native_malformed_frames_fault_without_retry(self):
        request = A8_REQUESTS[0]
        good = request + native_reply((17, 17, 1, 2))
        cases = [b"", good[:-1], good + b"\0", good[len(request):]]
        for offset in list(range(len(request))) + list(range(len(request), len(request)+5)):
            bad = bytearray(good)
            bad[offset] ^= 1
            if offset >= len(request):
                bad[-1] = sum(bad[len(request):-1]) & 255
            cases.append(bytes(bad))
        cases.append(good[:-1] + bytes((good[-1] ^ 1,)))
        for bad in cases:
            calls = []
            def native(request):
                calls.append(request)
                return bad
            facade = HostFacade(native)
            with self.assertRaises(ProtocolError):
                facade.exchange_project(request_frame(0))
            self.assertTrue(facade.faulted)
            with self.assertRaises(SessionError):
                facade.exchange_project(request_frame(1))
            self.assertEqual(calls, [request])

    def test_native_FE_response_is_not_accepted_as_E8(self):
        def native(request):
            reply = bytearray(native_reply((17, 17, 1, 2)))
            reply[4] = 0xFE
            reply[-1] = sum(reply[:-1]) & 255
            return request + bytes(reply)
        facade = HostFacade(native)
        with self.assertRaises(ProtocolError):
            facade.exchange_project(request_frame(0))

    def test_reentrant_native_request_is_rejected(self):
        calls = []
        def native(request):
            calls.append(request)
            with self.assertRaises(SessionError):
                facade.exchange_project(request_frame(1))
            return request + native_reply((17, 17, 1, 2))
        facade = HostFacade(native)
        facade.exchange_project(request_frame(0))
        self.assertEqual(calls, [A8_REQUESTS[0]])
        self.assertFalse(facade.faulted)

    def test_native_exception_faults_and_never_retries(self):
        calls = []
        def native(request):
            calls.append(request)
            raise TimeoutError("Synthetic timeout")
        facade = HostFacade(native)
        with self.assertRaises(TimeoutError):
            facade.exchange_project(request_frame(0))
        with self.assertRaises(SessionError):
            facade.exchange_project(request_frame(0))
        self.assertEqual(calls, [A8_REQUESTS[0]])


if __name__ == '__main__':
    unittest.main(verbosity=2)
