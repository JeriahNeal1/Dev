"""Host-only RAW4 facade over two fixed OEM A8 reads; no ECU BE service.

No physical transport is included. The injected callable sees only the native
A8 requests below. FE framing and reason bits are produced locally, and every
result retains that origin instead of presenting it as an ECU response.
"""
from dataclasses import dataclass
from threading import Lock
from typing import Callable

from m06_protocol import (Observation, Page, ProtocolError, SessionError,
                          decode_exchange, observation_reason, request_frame)


# Native RomRaider SSMProtocol.constructReadAddressRequest, STATE_0/fastPoll false.
# Addresses are fixed; no caller-supplied address or control byte is accepted.
A8_REQUESTS = (
    bytes.fromhex("8010F00EA800FF4C75FF4C8DFF4CA1FF4C5055"),
    bytes.fromhex("8010F00BA800FF4BC1FF4BC2FF4C8D22"),
)
ADDRESS_PAGES = (
    (0xFFFF4C75, 0xFFFF4C8D, 0xFFFF4CA1, 0xFFFF4C50),
    (0xFFFF4BC1, 0xFFFF4BC2, 0xFFFF4C8D),
)
MODE = "HOST_FACADE_NO_ECU_EXTENSION"


@dataclass(frozen=True)
class FacadeResult:
    mode: str
    page: Page
    project_request: bytes
    native_request: bytes
    native_wire: bytes
    local_response: bytes
    observation: Observation


class HostFacade:
    """Serialize exact project requests over an independently isolated backend.

    The backend must enforce its own deadline, return the exact native request
    echo plus one E8 response, and must not cache replies or enable fast polling.
    Any backend/framing failure is terminal for this instance. Any malformed
    project request is rejected before the backend is called. A fresh instance
    alone does not re-establish transport isolation after a fault.
    """

    def __init__(self, native_exchange: Callable[[bytes], bytes]):
        if not callable(native_exchange):
            raise TypeError("An isolated native exchange callable is required")
        self._exchange = native_exchange
        self._lock = Lock()
        self._faulted = False

    @property
    def faulted(self):
        return self._faulted

    def exchange_project(self, project_request: bytes) -> FacadeResult:
        if not isinstance(project_request, bytes):
            raise ProtocolError("Project request must be immutable bytes")
        if project_request == request_frame(Page.RAW):
            page = Page.RAW
        elif project_request == request_frame(Page.OEM_DECODED):
            page = Page.OEM_DECODED
        else:
            raise ProtocolError("Only canonical RAW4 project requests are admitted")
        if not self._lock.acquire(blocking=False):
            raise SessionError("A native request is already outstanding")
        try:
            if self._faulted:
                raise SessionError("Facade session is faulted; isolate the backend again")
            try:
                request = A8_REQUESTS[page]
                wire = self._exchange(request)
                payload_bytes = len(ADDRESS_PAGES[page])
                expected_length = len(request) + payload_bytes + 6
                if not isinstance(wire, bytes) or len(wire) != expected_length:
                    raise ProtocolError("Expected exactly one native echo and one E8 response")
                if wire[:len(request)] != request:
                    raise ProtocolError("Native A8 echo differs from the outstanding request")
                reply = wire[len(request):]
                if reply[:5] != bytes((0x80, 0xF0, 0x10, payload_bytes + 1, 0xE8)):
                    raise ProtocolError("Native E8 header, direction, length, or command differs")
                if reply[-1] != sum(reply[:-1]) & 255:
                    raise ProtocolError("Native E8 checksum differs")
                payload = reply[5:-1]
                if page == Page.OEM_DECODED:
                    payload += bytes((observation_reason(*payload),))
                local_prefix = bytes((0x80, 0xF0, 0x10, 5, 0xFE)) + payload
                local_response = local_prefix + bytes((sum(local_prefix) & 255,))
                observation = decode_exchange(page, project_request, project_request + local_response)
                return FacadeResult(MODE, page, project_request, request, wire, local_response, observation)
            except BaseException:
                self._faulted = True
                raise
        finally:
            self._lock.release()
