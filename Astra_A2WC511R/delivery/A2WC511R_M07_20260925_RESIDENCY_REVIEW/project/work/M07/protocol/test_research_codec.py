import unittest
from research_codec import CodecError, encode_request, page_spec, parse_wire, validate_request
from replay_codec import verify

CASES = (("one_page", 0), ("two_pages", 0), ("two_pages", 1))


def synthetic_response(profile, page):
    spec = page_spec(profile, page)
    data = bytes((0x80, 0xF0, 0x10, len(spec.fields) + 1, spec.opcode)) + bytes(range(len(spec.fields)))
    return data + bytes((sum(data) & 255,))


class ResearchCodecTests(unittest.TestCase):
    def test_pinned_actual_compiled_fixtures(self):
        result = verify()
        self.assertEqual(result["valid_compiled_frames"], 3)
        self.assertEqual(result["compiled_negative_requests"], 15)

    def test_exact_profile_page_version(self):
        for profile in ("one_page", "two_pages"):
            for bad in (-1, 2, 255, None, True, "0"):
                with self.assertRaises(CodecError):encode_request(profile, bad)
            for version in range(256):
                if version != 1:
                    with self.assertRaises(CodecError):encode_request(profile, 0, version)
            with self.assertRaises(CodecError):encode_request(profile, 0, True)
        with self.assertRaises(CodecError):encode_request("one_page", 1)
        with self.assertRaises(CodecError):encode_request("native_A8", 0)

    def test_every_request_byte_mutation_even_correct_checksum(self):
        for profile, page in CASES:
            request = encode_request(profile, page)
            for offset in range(len(request)):
                for value in range(256):
                    if value == request[offset]:continue
                    bad = bytearray(request);bad[offset] = value
                    if offset < len(bad)-1:bad[-1] = sum(bad[:-1]) & 255
                    with self.assertRaises(CodecError):validate_request(profile, page, bytes(bad))

    def test_echo_response_header_and_checksum(self):
        for profile, page in CASES:
            request = encode_request(profile, page);response = synthetic_response(profile, page)
            wire = request + response
            result = parse_wire(profile, page, request, wire)
            self.assertEqual(len(result["raw"]), len(page_spec(profile, page).fields))
            self.assertEqual(result["freshness"], "UNKNOWN")
            self.assertFalse(result["ECU_reason_computation"])
            for offset in range(len(request)):
                bad = bytearray(wire);bad[offset] ^= 1
                with self.assertRaises(CodecError):parse_wire(profile, page, request, bytes(bad))
            for offset in range(5):
                for value in range(256):
                    if value == response[offset]:continue
                    bad = bytearray(response);bad[offset] = value;bad[-1] = sum(bad[:-1]) & 255
                    with self.assertRaises(CodecError):parse_wire(profile, page, request, request + bytes(bad))
            for bad in (wire[:-1], wire + b"\0", wire[:-1] + bytes((wire[-1]^1,)), response, b""):
                with self.assertRaises(CodecError):parse_wire(profile, page, request, bad)

    def test_wrong_profile_page_and_command_rejected(self):
        for profile, page in CASES:
            request = encode_request(profile, page)
            for other_profile, other_page in CASES:
                if (profile, page) == (other_profile, other_page):continue
                response = synthetic_response(other_profile, other_page)
                with self.assertRaises(CodecError):parse_wire(profile, page, request, request + response)
                with self.assertRaises(CodecError):validate_request(profile, page, encode_request(other_profile, other_page))

    def test_raw_values_do_not_claim_gear_or_freshness(self):
        for profile, page in CASES:
            request = encode_request(profile, page);spec = page_spec(profile, page)
            for value in range(256):
                response = bytes((0x80,0xF0,0x10,len(spec.fields)+1,spec.opcode)) + bytes((value,))*len(spec.fields)
                response += bytes((sum(response)&255,))
                result = parse_wire(profile,page,request,request+response)
                self.assertEqual(list(result["raw"].values()), [value]*len(spec.fields))
                self.assertEqual(result["physical_gear"], "NOT_INFERRED")
                self.assertEqual(result["freshness"], "UNKNOWN")


if __name__ == "__main__":unittest.main(verbosity=2)
