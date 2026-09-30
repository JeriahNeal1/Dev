"""Side-by-side M07 transports; the frozen protocol/client remain unchanged."""
from pathlib import Path
import json
import os
from queue import Queue, Empty
import subprocess
import sys
sys.dont_write_bytecode = True  # Imported frozen M07 modules must never regenerate caches.
from threading import Lock, Thread
from time import monotonic_ns

HERE = Path(__file__).resolve().parent
M07 = HERE.parent / 'm07'
sys.path.append(str(M07))
from protocol import Exchange, ProtocolError, REQUEST, SnapshotClient, validate_request as m07_validate_request, parse_wire, utc_now
from backends import load_profile, ReplayTransport, NativeVirtualTransport, digest

IDENTITY_REQUEST = bytes.fromhex('8010f001bf40')
ECU_ID = '2f12515306'

def validate_request(request):
    if type(request) is not bytes:
        raise ProtocolError('An exact immutable bytes request is required')
    m07_validate_request(request)

def validate_operation(name):
    if type(name) is not str or name not in ('IDENTITY', 'SNAPSHOT', 'CLOSE'):
        raise ProtocolError('Only fixed IDENTITY, SNAPSHOT, CLOSE operations exist')

def parse_identity(wire):
    if type(wire) is not bytes or len(wire) != 68 or wire[:6] != IDENTITY_REQUEST:
        raise ProtocolError('Expected exact BF echo and 62-byte stock-layout identity response')
    r = wire[6:]
    if r[:5] != bytes.fromhex('80f01039ff') or sum(r[:-1]) & 255 != r[-1]:
        raise ProtocolError('BF framing/checksum differs')
    if r[8:13].hex() != ECU_ID:
        raise ProtocolError('Unexpected ECU identity; no A8 request permitted')
    return {'ecu_id': r[8:13].hex().upper(), 'request_hex': IDENTITY_REQUEST.hex(),
            'response_hex': r.hex(), 'identity_payload_hex': r[5:-1].hex(),
            'current_calibration_identified': False, 'cal_id': None,
            'cal_id_status': 'NOT_READ_BY_THIS_RESTRICTED_TRANSPORT'}

class ReadOnlyJ2534Transport:
    """One worker, one fixed identity, then fixed A8. Terminal errors, no fallback.

    A process boundary limits normal API callers. This is not a sandbox against
    a same-user attacker who replaces binaries or opens another J2534 client.
    """
    def __init__(self, stderr_path, *, fake=False, authorize_physical_read_only=False, timeout_ms=2500):
        if type(fake) is not bool or type(authorize_physical_read_only) is not bool:
            raise ValueError('Boolean mode selectors required')
        if not fake and not authorize_physical_read_only:
            raise ValueError('Physical mode requires explicit future human invocation')
        if type(timeout_ms) is not int or not 2000 <= timeout_ms <= 10000:
            raise ValueError('Worker deadline must be 2000..10000 ms')
        self.fake, self.timeout_ms, self.closed = fake, timeout_ms, False
        self._lock, self._process, self._stderr = Lock(), None, None
        self._abort_lock = Lock()
        self.cleanup_status = 'NOT_STARTED'
        self.identity = None
        manifest = json.loads((HERE/'build/BUILD_MANIFEST.json').read_text())
        for path, expected in manifest['files'].items():
            if digest(path) != expected:
                raise ValueError('Worker source/build integrity mismatch: '+path)
        self.worker_sha256 = digest(HERE/'build/broker.exe')
        self.provider_sha256 = (digest(HERE/'build/fake_j2534.dll') if fake else
                                digest(Path(r'C:\Windows\SysWOW64\op20pt32.dll')))
        if not fake and self.provider_sha256 != manifest['installed_provider_read_only_hash']:
            raise ValueError('Installed provider hash differs')
        environment = dict(os.environ)
        environment.pop('A2WC_FAKE_FAULT', None)
        try:
            self._stderr = Path(stderr_path).open('x', encoding='utf-8')
            self._process = subprocess.Popen([str(HERE/'build/broker.exe'), '--fake' if fake else '--physical-read-only'],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._stderr,
                    env=environment, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if self._receive() != {'type':'ready','fake':fake,'provider_loaded':False}:
                raise ProtocolError('Worker startup differs')
            start_utc, start_ns = utc_now(), monotonic_ns()
            self.cleanup_status = 'UNCONFIRMED'
            reply = self._command('IDENTITY')
            self.identity = parse_identity(bytes.fromhex(reply['wire_hex']))
            self.identity.update({'type':'identity', 'host_request_utc':start_utc,
                'host_response_utc':utc_now(), 'host_request_monotonic_ns':start_ns,
                'host_response_monotonic_ns':monotonic_ns(), 'provider_frames':reply['provider_frames'],
                'physical_backend':not fake, 'worker_sha256':self.worker_sha256,
                'provider_sha256':self.provider_sha256})
        except BaseException:
            self.abort()
            self.close()
            raise

    def _receive(self):
        result = Queue(maxsize=1)
        def read():
            try:
                value = self._process.stdout.readline(16385)
                result.put((True,value))
            except BaseException as error:
                result.put((False,error))
        Thread(target=read, daemon=True).start()
        try:
            success, value = result.get(timeout=self.timeout_ms/1000)
        except Empty as error:
            raise TimeoutError('Fixed-read worker exceeded deadline') from error
        if not success:
            raise value
        if not value.endswith(b'\n') or len(value)>16384:
            raise ProtocolError('Malformed/oversized worker response')
        return json.loads(value)

    def _command(self, operation):
        validate_operation(operation)
        if self.closed:
            raise RuntimeError('Worker transport terminally closed')
        self._process.stdin.write((operation+'\n').encode('ascii'))
        self._process.stdin.flush()
        row = self._receive()
        if row.get('type') == 'terminal_failure' and row.get('cleanup_ok') is True:
            self.cleanup_status = 'CONFIRMED'
        if row.get('type') != ('closed' if operation=='CLOSE' else 'exchange'):
            raise ProtocolError('Worker reported terminal failure')
        if operation != 'CLOSE' and row.get('operation') != operation:
            raise ProtocolError('Wrong worker operation response')
        if operation == 'CLOSE':
            self.cleanup_status = 'CONFIRMED'
        return row

    def exchange(self, request):
        # Validate before even looking at the process. The worker never receives caller bytes.
        validate_request(request)
        if not self._lock.acquire(blocking=False):
            raise RuntimeError('Read already outstanding')
        try:
            reply = self._command('SNAPSHOT')
            wire = bytes.fromhex(reply['wire_hex'])
            parse_wire(wire)
            return Exchange(wire, {'mode':'INSTRUMENTED_FAKE_J2534' if self.fake else 'PHYSICAL_J2534_READ_ONLY',
                'physical_backend':not self.fake, 'ecu_patch':False,
                'classification':'FABRICATED_PROVIDER_TEST_NOT_TELEMETRY' if self.fake else 'PHYSICAL_PASSIVE_OBSERVATION',
                'worker_sha256':self.worker_sha256, 'provider_sha256':self.provider_sha256,
                'provider_frames':reply['provider_frames'], 'native_RomRaider_parser':False,
                'echo':'EXACT_PROVIDER_ECHO_REQUIRED', 'identity_ecu_id':self.identity['ecu_id']})
        except BaseException:
            self.abort()
            raise
        finally:
            self._lock.release()

    def abort(self):
        self.closed=True
        with self._abort_lock:
            if self._process is None:
                return
            if self._process.poll() is None:
                try:
                    self._process.stdin.write(b'CLOSE\n')
                    self._process.stdin.flush()
                except (BrokenPipeError, OSError, ValueError):
                    pass
                try:
                    self._process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=3)
                    self.cleanup_status='FORCED_TERMINATION_CLEANUP_UNCONFIRMED'
            if self._process.returncode == 0:
                self.cleanup_status='CONFIRMED'

    def close(self):
        error = None
        try:
            if self._process is not None and self._process.poll() is None and not self.closed:
                self._command('CLOSE')
                if self._process.wait(timeout=3) != 0:
                    raise RuntimeError('Worker cleanup failed')
        except BaseException as failure:
            error=failure
        finally:
            self.abort()
            if self._process is not None:
                self._process.wait(timeout=3)
                self._process.stdin.close()
                self._process.stdout.close()
            if self._stderr is not None:
                self._stderr.close()
        if self.cleanup_status not in ('NOT_STARTED','CONFIRMED') and error is None:
            error=RuntimeError('Provider cleanup not confirmed: '+self.cleanup_status)
        if error:
            raise error

def create_transport(backend, output, *, profile=M07/'profile.json', authorize_physical_read_only=False):
    if backend in ('replay','native-virtual'):
        config, fixture = load_profile(profile)
        return (ReplayTransport(config,fixture) if backend=='replay' else
                NativeVirtualTransport(config,fixture,Path(str(output)+'.native.stderr.log')))
    if backend not in ('fake-j2534','physical-j2534'):
        raise ValueError('Unknown backend')
    return ReadOnlyJ2534Transport(Path(str(output)+'.provider.stderr.log'), fake=backend=='fake-j2534',
                                 authorize_physical_read_only=authorize_physical_read_only)
