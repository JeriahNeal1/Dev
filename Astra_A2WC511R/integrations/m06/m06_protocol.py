"""A2WC511R M0.6 RAW4 v1 codec; no hardware, provider, or background task.

This module deliberately has no physical transport. An injected exchange callable
must return exactly request echo + one response and enforce its own deadline.
Each page is a separate observation; a reply has no page or transaction ID.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from threading import Lock
from typing import Callable, Union


class ProtocolError(ValueError):
    """The exchange does not satisfy the fixed project protocol."""


class SessionError(RuntimeError):
    """An outstanding or faulted exchange prevents another request."""


class Page(IntEnum):
    RAW = 0
    OEM_DECODED = 1


def _page(value: int) -> Page:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProtocolError("Page must be integer 0 or 1")
    try:
        return Page(value)
    except ValueError as error:
        raise ProtocolError("Page must be integer 0 or 1") from error


def _checksum(data: bytes) -> int:
    return sum(data) & 0xFF


def request_frame(page: int) -> bytes:
    """Return the sole permitted request form for the selected RAW4 page."""
    prefix = bytes((0x80, 0x10, 0xF0, 0x07, 0xBE, 0x4D, 0x30, 0x36,
                    0x01, _page(page), 0x04))
    return prefix + bytes((_checksum(prefix),))


def observation_reason(target: int, current: int, snapshot: int) -> int:
    """Pure predicates only; bit 0x80 always marks unproven validity/coherence."""
    for value in (target, current, snapshot):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
            raise ProtocolError("Observed values must be unsigned bytes")
    return (0x80 | (0x01 if snapshot != 0x11 else 0)
            | (0x02 if target != 1 or current != 1 else 0)
            | (0x04 if snapshot >> 4 > 8 or snapshot & 15 > 8 else 0))


@dataclass(frozen=True)
class RawPage:
    source: int
    snapshot: int
    latch: int
    flags: int

    @property
    def payload(self) -> bytes:
        return bytes((self.source, self.snapshot, self.latch, self.flags))


@dataclass(frozen=True)
class DecodedPage:
    oem_target: int
    oem_current: int
    snapshot: int
    reason: int

    @property
    def payload(self) -> bytes:
        return bytes((self.oem_target, self.oem_current, self.snapshot, self.reason))


Observation = Union[RawPage, DecodedPage]


def decode_exchange(page: int, request: bytes, wire: bytes) -> Observation:
    """Validate exact echo and one FE response, then decode the expected page.

    Expected page comes from the outstanding request, not the response. This
    cannot detect a stale but valid FE frame or identify a wrong-page response
    whose bytes also satisfy the expected schema. Transport isolation remains
    required; checksum and magic are neither authentication nor freshness proof.
    """
    selected = _page(page)
    if not isinstance(request, bytes) or request != request_frame(selected):
        raise ProtocolError("Outstanding request is not canonical for its page")
    if not isinstance(wire, bytes) or len(wire) != 22:
        raise ProtocolError("Expected exactly 12 echo bytes and 10 response bytes")
    if wire[:12] != request:
        raise ProtocolError("Request echo does not match the outstanding request")
    response = wire[12:]
    if response[:5] != bytes((0x80, 0xF0, 0x10, 0x05, 0xFE)):
        raise ProtocolError("Response header, direction, length, or command differs")
    if response[-1] != _checksum(response[:-1]):
        raise ProtocolError("Response checksum differs")
    payload = response[5:9]
    if selected == Page.RAW:
        return RawPage(*payload)
    if payload[3] != observation_reason(*payload[:3]):
        raise ProtocolError("Reason byte differs from RAW4 v1 predicates")
    return DecodedPage(*payload)


class Session:
    """One outstanding exchange, with no retries or recovery after a fault.

    A successful exchange establishes framing only. Two returned observations
    are not a coherent sample. After a fault, dispose of this object; the caller
    must independently re-establish an isolated channel before making another.
    The exchange callable owns bounded I/O, transport echo handling, and cleanup.
    It must not silently serve cached replies, start fast polling, or add writes.
    """

    def __init__(self, exchange: Callable[[bytes], bytes]):
        if not callable(exchange):
            raise TypeError("An isolated exchange callable is required")
        self._exchange = exchange
        self._lock = Lock()
        self._faulted = False

    @property
    def faulted(self) -> bool:
        return self._faulted

    def read_page(self, page: int) -> Observation:
        selected = _page(page)
        if not self._lock.acquire(blocking=False):
            raise SessionError("A request is already outstanding")
        try:
            if self._faulted:
                raise SessionError("Session is faulted; isolated channel must be re-established")
            request = request_frame(selected)
            try:
                return decode_exchange(selected, request, self._exchange(request))
            except BaseException:
                self._faulted = True
                raise
        finally:
            self._lock.release()
