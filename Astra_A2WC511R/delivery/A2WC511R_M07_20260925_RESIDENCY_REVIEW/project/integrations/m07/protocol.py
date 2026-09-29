"""M0.7 host-only observations from one fixed native OEM A8 request."""
from dataclasses import dataclass
from datetime import datetime, timezone
from queue import Queue, Empty
from threading import Lock, Thread
from time import monotonic_ns

REQUEST = bytes.fromhex("8010F014A800FF4C75FF4C8DFF4CA1FF4C50FF4BC1FF4BC272")
FIELDS = ("source", "snapshot", "latch", "flags", "oem_target", "oem_current")
ADDRESSES = (0xFFFF4C75, 0xFFFF4C8D, 0xFFFF4CA1, 0xFFFF4C50, 0xFFFF4BC1, 0xFFFF4BC2)


class ProtocolError(ValueError):
    pass


class SessionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Exchange:
    wire: bytes
    provenance: dict


def validate_request(request):
    if not isinstance(request, bytes) or request != REQUEST:
        raise ProtocolError("Only the fixed one-shot A8 read of six reviewed OEM addresses is permitted")


def parse_wire(wire):
    if not isinstance(wire, bytes) or len(wire) != len(REQUEST) + 12:
        raise ProtocolError("Expected the exact A8 echo and one six-byte E8 reply")
    if wire[:len(REQUEST)] != REQUEST:
        raise ProtocolError("A8 request echo differs")
    response = wire[len(REQUEST):]
    if response[:5] != bytes((0x80, 0xF0, 0x10, 7, 0xE8)):
        raise ProtocolError("E8 header, direction, command, or length differs")
    if response[-1] != sum(response[:-1]) & 255:
        raise ProtocolError("E8 checksum differs")
    return response[5:11]


def observations(raw):
    if not isinstance(raw, bytes) or len(raw) != 6:
        raise ProtocolError("Exactly six raw bytes are required")
    source, snapshot, latch, flags, target, current = raw
    reason = (0x80 | (1 if snapshot != 0x11 else 0)
              | (2 if target != 1 or current != 1 else 0)
              | (4 if snapshot >> 4 > 8 or snapshot & 15 > 8 else 0))
    return {
        "raw": dict(zip(FIELDS, raw)),
        "raw_by_address": {f"{address:08X}": value for address, value in zip(ADDRESSES, raw)},
        "raw_hex": raw.hex(),
        "predicates": {"source_equals_snapshot": source == snapshot,
                       "latch_equals_one": latch == 1, "flags_bit02_set": bool(flags & 2),
                       "snapshot_equals_11": snapshot == 0x11,
                       "oem_target_equals_one": target == 1, "oem_current_equals_one": current == 1,
                       "snapshot_has_nibble_above_8": snapshot >> 4 > 8 or snapshot & 15 > 8},
        "reason_mask": reason, "reason_hex": f"{reason:02X}",
        "reason_origin": "HOST_COMPUTED_FROM_RETURNED_OEM_BYTES",
        "freshness": "UNKNOWN", "coherence": "UNPROVEN_SEQUENTIAL_OEM_READS",
        "physical_gear": "NOT_INFERRED", "control_eligibility": "NOT_EVALUATED",
    }


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class SnapshotClient:
    """One request at a time; bounded host wait, terminal fault, no retries.

    The transport implements exchange(request)->Exchange, abort(), and close().
    abort must interrupt owned I/O. Late worker results after timeout are ignored;
    this client never sends another request after any fault or closure.
    """
    def __init__(self, transport, timeout_ms=1000):
        if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or not 1 <= timeout_ms <= 60000:
            raise ValueError("Timeout must be an integer from 1 to 60000 ms")
        self.transport = transport
        self.timeout_ms = timeout_ms
        self._lock = Lock()
        self.state = "OPEN"
        self.count = 0
        self.abort_errors = []

    def _abort(self):
        try:
            self.transport.abort()
        except Exception as error:
            self.abort_errors.append({"type": type(error).__name__, "message": str(error)})

    def capture(self):
        if not self._lock.acquire(blocking=False):
            raise SessionError("An A8 request is already outstanding")
        try:
            if self.state != "OPEN":
                raise SessionError("Client is " + self.state + "; no retry is permitted")
            started_utc, started_ns = utc_now(), monotonic_ns()
            result = Queue(maxsize=1)
            def worker():
                try:
                    result.put((True, self.transport.exchange(REQUEST)))
                except BaseException as error:
                    result.put((False, error))
            thread = Thread(target=worker, name="m07-single-a8", daemon=True)
            try:
                thread.start()
                try:
                    success, value = result.get(timeout=self.timeout_ms / 1000)
                except Empty as error:
                    raise TimeoutError(f"A8 exchange exceeded host deadline {self.timeout_ms} ms") from error
                if not success:
                    raise value
                if not isinstance(value, Exchange):
                    raise ProtocolError("Transport returned an invalid exchange record")
                raw = parse_wire(value.wire)
                ended_ns, ended_utc = monotonic_ns(), utc_now()
                if ended_ns - started_ns > self.timeout_ms * 1_000_000:
                    raise TimeoutError("A8 response arrived after the host deadline")
                record = observations(raw)
                record.update({"type": "sample", "host_sample_index": self.count,
                               "host_request_utc": started_utc, "host_response_utc": ended_utc,
                               "host_request_monotonic_ns": started_ns, "host_response_monotonic_ns": ended_ns,
                               "host_exchange_elapsed_ns": ended_ns - started_ns,
                               "timestamp_meaning": "Host observation timing only; not ECU data age",
                               "request_hex": REQUEST.hex(), "response_hex": value.wire[len(REQUEST):].hex(),
                               "echo_response_wire_hex": value.wire.hex(), "provenance": value.provenance})
                self.count += 1
                return record
            except BaseException:
                self.state = "FAULTED"
                self._abort()
                raise
        finally:
            self._lock.release()

    def close(self):
        if not self._lock.acquire(blocking=False):
            raise SessionError("Cannot close while an A8 request is outstanding")
        try:
            if self.state == "OPEN":
                self.state = "CLOSED"
            self.transport.close()
        finally:
            self._lock.release()
