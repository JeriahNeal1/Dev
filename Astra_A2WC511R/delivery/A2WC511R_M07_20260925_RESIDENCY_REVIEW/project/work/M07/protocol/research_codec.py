"""Strict offline codecs for two distinct, unapproved M0.7 ECU research builds.

This module has no transport. Preferred diagnostics remain integrations/m07 A8.
"""
from dataclasses import dataclass


class CodecError(ValueError):
    pass


@dataclass(frozen=True)
class Page:
    prefix: bytes
    opcode: int
    fields: tuple
    addresses: tuple

    @property
    def request(self):
        return self.prefix + bytes((sum(self.prefix) & 255,))


ALL_FIELDS = ("source", "snapshot", "latch", "flags", "oem_target", "oem_current")
ALL_ADDRESSES = ("FFFF4C75", "FFFF4C8D", "FFFF4CA1", "FFFF4C50", "FFFF4BC1", "FFFF4BC2")
ONE_PAGE = (Page(bytes.fromhex("8010F014BE10FF4C75FF4C8DFF4CA1FF4C50FF4BC1FF4BC2"), 0xFC, ALL_FIELDS, ALL_ADDRESSES),)
TWO_PAGES = (Page(bytes.fromhex("8010F00EBE10FF4C75FF4C8DFF4CA1FF4C50"), 0xFC, ALL_FIELDS[:4], ALL_ADDRESSES[:4]),
             Page(bytes.fromhex("8010F008BE11FF4BC1FF4BC2"), 0xFD, ALL_FIELDS[4:], ALL_ADDRESSES[4:]))
MANIFESTS = {
    "one_page": ("one_page_01", "a69589a230a9de0b75530cfa867feaef48ac1fd438f2029d20dd32695e5a8f21"),
    "two_pages": ("two_pages_01", "cd2f4267c0f4e09a43fe9e89785cce566917713d84dd65362b80e91211321a53"),
}


def page_spec(profile, page, version=1):
    if type(version) is not int or version != 1:
        raise CodecError("Only protocol version 1 is defined")
    if type(profile) is not str or profile not in MANIFESTS:
        raise CodecError("Choose the exact one_page or two_pages research profile")
    pages = ONE_PAGE if profile == "one_page" else TWO_PAGES
    if type(page) is not int or not 0 <= page < len(pages):
        raise CodecError("Page is not defined for this exact build profile")
    return pages[page]


def encode_request(profile, page, version=1):
    return page_spec(profile, page, version).request


def validate_request(profile, page, request, version=1):
    if type(request) is not bytes or request != encode_request(profile, page, version):
        raise CodecError("Request differs from the pinned command/version/page/length/address whitelist")


def parse_wire(profile, page, request, wire, version=1):
    validate_request(profile, page, request, version)
    spec = page_spec(profile, page, version)
    size = len(spec.fields)
    if type(wire) is not bytes or len(wire) != len(request) + size + 6:
        raise CodecError("Response size differs from this exact profile/page")
    if wire[:len(request)] != request:
        raise CodecError("Request echo differs")
    response = wire[len(request):]
    expected = bytes((0x80, 0xF0, 0x10, size + 1, spec.opcode))
    if response[:5] != expected:
        raise CodecError("Response header/version-page opcode/length differs")
    if response[-1] != sum(response[:-1]) & 255:
        raise CodecError("Response checksum differs")
    raw = response[5:-1]
    return {"architecture": "EXPERIMENTAL_ECU_PROTOCOL_NOT_OWNERSHIP_APPROVED",
            "profile": profile, "version": 1, "page": page, "raw_hex": raw.hex(),
            "raw": dict(zip(spec.fields, raw)), "raw_by_address": dict(zip(spec.addresses, raw)),
            "freshness": "UNKNOWN", "coherence": "UNPROVEN_SEQUENTIAL_READS_AND_SEPARATE_REQUESTS",
            "physical_gear": "NOT_INFERRED", "ECU_reason_computation": False}
