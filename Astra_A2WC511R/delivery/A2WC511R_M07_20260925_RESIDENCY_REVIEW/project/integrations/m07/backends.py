"""Offline replay and isolated installed-RomRaider codec backends only."""
import hashlib
import json
import os
from pathlib import Path
from queue import Queue, Empty
import subprocess
from threading import Thread

from protocol import ADDRESSES, Exchange, ProtocolError, REQUEST, parse_wire, validate_request


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_profile(path):
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    if profile.get("mode") != "OFFLINE_ONLY_NO_PHYSICAL_BACKEND":
        raise ValueError("Only the offline profile is supported")
    for item in (profile["fixture"], profile["stock_rom"]):
        if digest(item["path"]) != item["sha256"]:
            raise ValueError("Profile input hash differs: " + item["path"])
    fixture = json.loads(Path(profile["fixture"]["path"]).read_text(encoding="utf-8"))
    if fixture.get("status") != "PASS" or fixture.get("classification") != "VIRTUAL_COMPILED_OEM_A8_READS_NOT_PHYSICAL_TELEMETRY":
        raise ValueError("Fixture is not the reviewed compiled OEM virtual data")
    if fixture["stock_rom"]["sha256"] != profile["stock_rom"]["sha256"] or fixture.get("ecu_patch") is not False:
        raise ValueError("Fixture is not bound to the unchanged stock ROM")
    samples = fixture["samples"]
    if not samples:
        raise ValueError("Fixture contains no samples")
    ids = set()
    for sample in samples:
        if sample["sample_id"] in ids:
            raise ValueError("Repeated fixture sample identity")
        ids.add(sample["sample_id"])
        validate_request(bytes.fromhex(sample["request_hex"]))
        raw = parse_wire(REQUEST + bytes.fromhex(sample["response_hex"]))
        if sample["raw_by_address"] != {f"{address:08X}": value for address, value in zip(ADDRESSES, raw)}:
            raise ValueError("Fixture raw values differ from executed reply")
        events = sample["events"]
        if hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest() != sample["events_sha256"]:
            raise ValueError("Fixture event digest differs")
        transmitted = bytes(int(e["value"], 16) for e in events if e["mode"] == "w" and e["address"] == "FFFFF013")
        if transmitted != bytes.fromhex(sample["response_hex"])[1:]:
            raise ValueError("Fixture differs from executed OEM transmit writes")
    return profile, fixture


class ReplayTransport:
    mode = "COMPILED_OEM_FIXTURE_REPLAY"

    def __init__(self, profile, fixture):
        self.profile, self.fixture, self.index, self.closed = profile, fixture, 0, False

    def exchange(self, request):
        validate_request(request)
        if self.closed:
            raise RuntimeError("Replay is closed")
        if self.index >= len(self.fixture["samples"]):
            raise EOFError("Virtual fixture exhausted; no cached repeat")
        index = self.index
        self.index += 1
        sample = self.fixture["samples"][index]
        return Exchange(request + bytes.fromhex(sample["response_hex"]),
                        {"mode": self.mode, "classification": self.fixture["classification"],
                         "sample_id": sample["sample_id"], "fixture_index": index,
                         "fixture_sha256": self.profile["fixture"]["sha256"],
                         "stock_rom_sha256": self.profile["stock_rom"]["sha256"],
                         "echo": "MODELED_HOST_REQUEST_ECHO", "physical_backend": False,
                         "ecu_patch": False, "native_RomRaider_parser": False})

    def abort(self):
        self.closed = True

    def close(self):
        self.closed = True


class NativeVirtualTransport:
    mode = "ISOLATED_NATIVE_ROMRAIDER_VIRTUAL"

    def __init__(self, profile, fixture, stderr_path, startup_timeout_ms=5000):
        self.profile, self.fixture, self.index, self.closed = profile, fixture, 0, False
        self.process = None
        self.stderr = None
        for item in [profile["java"], *profile["classpath"]]:
            if digest(item["path"]) != item["sha256"]:
                raise ValueError("Native runtime hash differs: " + item["path"])
        if len(profile["classpath"]) != 3:
            raise ValueError("Only the reviewed three-JAR native classpath is supported")
        self.command = [profile["java"]["path"], "-cp", ";".join(item["path"] for item in profile["classpath"]),
                        "NativeVirtualEndpoint", profile["fixture"]["path"], profile["fixture"]["sha256"],
                        profile["stock_rom"]["path"], profile["stock_rom"]["sha256"]]
        environment = dict(os.environ)
        for name in ("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "CLASSPATH"):
            environment.pop(name, None)  # Isolate this child only; no global setting change.
        try:
            self.stderr = open(stderr_path, "x", encoding="utf-8")
            self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                             stderr=self.stderr, text=True, encoding="utf-8", bufsize=1, env=environment,
                                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            queue = Queue(maxsize=1)
            def read_ready():
                try:
                    queue.put((True, self.process.stdout.readline()))
                except BaseException as error:
                    queue.put((False, error))
            Thread(target=read_ready, name="m07-native-startup", daemon=True).start()
            try:
                success, value = queue.get(timeout=startup_timeout_ms / 1000)
            except Empty as error:
                raise TimeoutError("Native virtual endpoint startup deadline exceeded") from error
            if not success:
                raise value
            ready = json.loads(value)
            if ready != {"type": "ready", "mode": self.mode, "native_request_hex": REQUEST.hex(),
                         "samples": len(fixture["samples"]), "physical_backend": False}:
                raise ProtocolError("Native endpoint handshake differs")
        except BaseException as error:
            try:
                self.close()
            except BaseException as cleanup:
                raise RuntimeError(f"Native startup failed: {error}; cleanup also failed: {cleanup}") from error
            raise

    def exchange(self, request):
        validate_request(request)
        if self.closed:
            raise RuntimeError("Native virtual endpoint closed")
        if self.index >= len(self.fixture["samples"]):
            raise EOFError("Native virtual fixture exhausted; no cached repeat")
        self.process.stdin.write(json.dumps({"op": "exchange", "request_hex": request.hex()}) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Native virtual endpoint ended without a response")
        record = json.loads(line)
        sample = self.fixture["samples"][self.index]
        if (record.get("type") != "exchange" or record.get("sample_id") != sample["sample_id"]
                or record.get("fixture_index") != self.index or record.get("native_parser_verified") is not True
                or record.get("physical_backend") is not False):
            raise ProtocolError("Native exchange identity or parser evidence differs")
        wire = bytes.fromhex(record["wire_hex"])
        raw = parse_wire(wire)
        if wire != request + bytes.fromhex(sample["response_hex"]) or raw.hex() != record["native_raw_hex"]:
            raise ProtocolError("Native codec response differs from the compiled fixture")
        self.index += 1
        return Exchange(wire, {"mode": self.mode, "classification": self.fixture["classification"],
                              "sample_id": sample["sample_id"], "fixture_index": self.index-1,
                              "fixture_sha256": self.profile["fixture"]["sha256"],
                              "stock_rom_sha256": self.profile["stock_rom"]["sha256"],
                              "echo": "MODELED_HOST_REQUEST_ECHO", "physical_backend": False,
                              "ecu_patch": False, "native_RomRaider_parser": True})

    def abort(self):
        self.closed = True
        if self.process is not None and self.process.poll() is None:
            self.process.kill()

    def close(self):
        self.abort()
        if self.process is not None:
            self.process.wait(timeout=3)
            for stream in (self.process.stdin, self.process.stdout):
                if stream is not None:
                    stream.close()
        if self.stderr is not None:
            self.stderr.close()
