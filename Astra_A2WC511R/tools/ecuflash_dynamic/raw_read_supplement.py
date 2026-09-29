"""Fixed-loopback, virtual-only raw read supplement. No provider DLL or device APIs.

CLI accepts one existing isolated session name. There are no address, opcode,
transport-host, DLL, baud, image-upload, reset, or flash-operation arguments.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import hashlib
import json
import os
import re
import socket
import struct
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIZE, CHUNK = 0x100000, 512
VERSION = b'OpenECU Subaru SH7058 DUAL  Kernel V1.07\0'
EXE_SHA = '5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115'
MAP_SHA = '6b49cc2394f9f7a35c776b8c112cab03e983cfa84f8fcb3dd08443cf3e0cd63b'
NATIVE_PINS = {
    'a2wc_ecuflash_virtual32.dll': 'cfcb5cce34873101b25db64ecb7e1aa502ac00ebe264d501b6d9b6261c503ff4',
    'a2wc_guard32.dll': 'ce33218627c52238b737005935d78971e3f34c0a70c662850b04ab98dad24f4f',
    'guarded_launcher32.exe': '3d9d14b50c04870967c2fe0ddf5a4cf845fe2277d12b5b6dbfe7942fc18b0d8c',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _packet(payload):
    frame = b'\xbe\xef' + len(payload).to_bytes(2, 'big') + payload
    return frame + bytes([sum(frame) & 255])


def _message(data):
    return {'protocol': 3, 'rx_status': 0, 'tx_flags': 0, 'timestamp': 0,
            'extra': 0, 'data_hex': data.hex()}


def _reply(response, command, expected_length):
    require(type(response) is dict and type(response.get('status')) is int and response['status'] == 0,
            'RPC/provider did not succeed')
    messages = response.get('messages')
    require(type(messages) is list and len(messages) == 1, 'Exactly one response message required')
    message = messages[0]
    require(type(message) is dict and all(type(message.get(k)) is int for k in ('protocol','rx_status','tx_flags','extra'))
            and message.get('protocol') == 3 and message.get('rx_status') == 0
            and message.get('tx_flags') == 0, 'Non-raw/echo/wrong-protocol response')
    text = message.get('data_hex')
    require(type(text) is str and re.fullmatch('[0-9a-fA-F]+', text) is not None and len(text) % 2 == 0,
            'Malformed response hex')
    frame = bytes.fromhex(text)
    require(len(frame) == expected_length + 6 and frame[:2] == b'\xbe\xef', 'Response frame size/header')
    require(int.from_bytes(frame[2:4], 'big') == expected_length + 1, 'Response declared length')
    require(frame[4] == command + 0x80, 'Wrong response opcode')
    require(sum(frame[:-1]) & 255 == frame[-1], 'Response checksum')
    require(message.get('extra') == len(frame), 'Unexpected extra-data boundary')
    provenance = message.get('provenance')
    require(type(provenance) is dict and provenance.get('not_vehicle_telemetry') is True
            and provenance.get('kernel_executed') is False, 'Missing explicit synthetic model provenance')
    return frame[5:-1]


class _OutboundPolicy:
    """Fixed finite state machine independently rejects accidental broader RPCs."""
    def __init__(self):
        self.phase = 'open'
        self.device = self.channel = self.filter = None
        self.next_address = 0

    def check(self, request):
        q = {k: v for k, v in request.items() if k in ('function', 'device', 'channel', 'protocol', 'flags', 'baud',
              'filter_type', 'mask', 'pattern', 'flow', 'count', 'timeout', 'messages', 'id')}
        fn = q.get('function')
        expected = {
            'open': {'function': 'PassThruOpen'},
            'connect': {'function': 'PassThruConnect', 'device': self.device, 'protocol': 3, 'flags': 0x200, 'baud': 62500},
            'filter': {'function': 'PassThruStartMsgFilter', 'channel': self.channel, 'filter_type': 1,
                       'mask': _message(b'\xff\xff'), 'pattern': _message(b'\xbe\xef'), 'flow': None},
            'rx_version': {'function': 'PassThruReadMsgs', 'channel': self.channel, 'count': 1, 'timeout': 2000},
            'rx_data': {'function': 'PassThruReadMsgs', 'channel': self.channel, 'count': 1, 'timeout': 2000},
            'stop_filter': {'function': 'PassThruStopMsgFilter', 'channel': self.channel, 'id': self.filter},
            'disconnect': {'function': 'PassThruDisconnect', 'channel': self.channel},
            'close': {'function': 'PassThruClose', 'device': self.device},
        }
        if self.phase in ('tx_version', 'tx_data'):
            payload = b'\x01' if self.phase == 'tx_version' else b'\x03' + self.next_address.to_bytes(4, 'big') + CHUNK.to_bytes(2, 'big')
            expected[self.phase] = {'function': 'PassThruWriteMsgs', 'channel': self.channel, 'count': 1,
                                    'timeout': 2000, 'messages': [_message(_packet(payload))]}
        require(self.phase in expected and q == expected[self.phase], 'Outbound fixed-read allowlist violation')
        allowed_keys = set(q) | {'pid', 'thread', 'utc', 'monotonic_ns', 'client', 'physical'}
        require(set(request) <= allowed_keys and request.get('physical') is False,
                'Unexpected outbound argument or nonvirtual provenance')
        require(fn not in ('PassThruIoctl', 'PassThruSetProgrammingVoltage', 'PassThruStartPeriodicMsg'), 'Forbidden RPC')

    def accept(self, response):
        require(type(response) is dict and type(response.get('status')) is int and response['status'] == 0,
                'Nonzero provider status: terminal failure')
        if self.phase == 'open':
            require(response.get('device') == 1 and response.get('provenance') == 'VIRTUAL_DEVICE_ONLY', 'Wrong virtual device')
            self.device = 1; self.phase = 'connect'
        elif self.phase == 'connect':
            require(type(response.get('channel')) is int and response['channel'] >= 100, 'Invalid virtual channel')
            self.channel = response['channel']; self.phase = 'filter'
        elif self.phase == 'filter':
            require(type(response.get('id')) is int and response['id'] > 0, 'Invalid filter')
            self.filter = response['id']; self.phase = 'tx_version'
        elif self.phase in ('tx_version', 'tx_data'):
            require(response.get('count') == 1, 'Partial or empty TX acceptance')
            self.phase = 'rx_version' if self.phase == 'tx_version' else 'rx_data'
        elif self.phase == 'rx_version':
            require(_reply(response, 1, len(VERSION)) == VERSION, 'Exact DUAL1.07 version required')
            self.phase = 'tx_data'
        elif self.phase == 'rx_data':
            _reply(response, 3, CHUNK)
            self.next_address += CHUNK
            self.phase = 'tx_data' if self.next_address < SIZE else 'stop_filter'
        elif self.phase == 'stop_filter': self.phase = 'disconnect'
        elif self.phase == 'disconnect': self.phase = 'close'
        elif self.phase == 'close': self.phase = 'done'
        else: raise ValueError('RPC after terminal state')


class _LoopbackClient:
    def __init__(self, port, token, journal):
        require(type(port) is int and 1024 <= port <= 65535, 'Invalid loopback port')
        require(type(token) is str and len(token) >= 32, 'Invalid private token')
        self.sock = socket.create_connection(('127.0.0.1', port), timeout=5)
        require(self.sock.getpeername()[0] == '127.0.0.1', 'Non-loopback peer')
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.token, self.journal, self.policy, self.sequence = token, journal, _OutboundPolicy(), 0
        self.failed = False

    def _call(self, **request):
        require(not self.failed, 'Terminal client failure; no further RPC allowed')
        request.update(client='A2WC_VIRTUAL_ONLY_RAW_READ_SUPPLEMENT', pid=os.getpid(), thread=0,
                       utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), monotonic_ns=time.monotonic_ns(), physical=False)
        try:
            self.policy.check(request)
            self.journal.write(json.dumps({'sequence': self.sequence, 'phase': 'INTENT', 'request': request})+'\n')
            self.journal.flush()
            wire = json.dumps(dict(request, token=self.token), sort_keys=True).encode()
            self.sock.sendall(struct.pack('!I', len(wire))+wire)
            def receive(n):
                result = bytearray()
                deadline = time.monotonic()+5
                while len(result) < n:
                    remaining = deadline-time.monotonic()
                    require(remaining > 0, 'RPC frame deadline')
                    self.sock.settimeout(remaining)
                    part = self.sock.recv(n-len(result))
                    require(bool(part), 'Truncated RPC response')
                    result.extend(part)
                return bytes(result)
            n = struct.unpack('!I', receive(4))[0]
            require(0 < n <= 4*1024*1024, 'RPC response size')
            response = json.loads(receive(n))
            self.journal.write(json.dumps({'sequence': self.sequence, 'phase': 'RESULT', 'request': request, 'response': response})+'\n')
            self.journal.flush(); self.sequence += 1
            self.policy.accept(response)
            return response
        except Exception:
            self.failed = True
            self.sock.close()
            raise

    def collect(self):
        self._call(function='PassThruOpen')
        self._call(function='PassThruConnect', device=1, protocol=3, flags=0x200, baud=62500)
        channel = self.policy.channel
        self._call(function='PassThruStartMsgFilter', channel=channel, filter_type=1,
                   mask=_message(b'\xff\xff'), pattern=_message(b'\xbe\xef'), flow=None)
        self._call(function='PassThruWriteMsgs', channel=channel, count=1, timeout=2000, messages=[_message(_packet(b'\x01'))])
        self._call(function='PassThruReadMsgs', channel=channel, count=1, timeout=2000)
        data, blocks = bytearray(), []
        for address in range(0, SIZE, CHUNK):
            packet = _packet(b'\x03'+address.to_bytes(4, 'big')+CHUNK.to_bytes(2, 'big'))
            self._call(function='PassThruWriteMsgs', channel=channel, count=1, timeout=2000, messages=[_message(packet)])
            result = self._call(function='PassThruReadMsgs', channel=channel, count=1, timeout=2000)
            returned = _reply(result, 3, CHUNK)
            data.extend(returned)
            blocks.append({'address': address, 'length': CHUNK, 'sha256': sha(returned), 'response_sequence': self.sequence-1})
        self._call(function='PassThruStopMsgFilter', channel=channel, id=self.policy.filter)
        self._call(function='PassThruDisconnect', channel=channel)
        self._call(function='PassThruClose', device=1)
        self.sock.close()
        require(self.policy.phase == 'done' and len(data) == SIZE, 'Incomplete fixed collection')
        return bytes(data), blocks


def _verify_session(name):
    require(type(name) is str and re.fullmatch('[a-zA-Z0-9_-]+', name) is not None, 'Simple isolated session name required')
    folder = (ROOT/'work/ecuflash_dynamic'/name).resolve()
    require(folder.parent == (ROOT/'work/ecuflash_dynamic').resolve(), 'Session outside project')
    spec, attach, ready, live, run = [load(folder/n) for n in ('session_private.json','API_ATTACH.json','rpc_ready.json','live_state.json','RUN_RESULT.json')]
    require(Path(spec['directory']).resolve() == folder and spec['name'] == name and spec.get('probe') is False, 'Session identity')
    require(Path(spec['target']).resolve() == Path(r'C:\Program Files (x86)\OpenECU\EcuFlash\ecuflash.exe').resolve()
            and sha(Path(spec['target']).read_bytes()) == EXE_SHA, 'Installed executable identity')
    for filename, digest in NATIVE_PINS.items():
        path = folder/'native'/filename
        require(sha(path.read_bytes()) == digest and spec['native_hashes'].get(str(path)) == digest, 'Pinned fake/guard identity')
    require(attach.get('status') == 'PASS_INSTRUMENTATION_INSTALLED' and attach.get('api_mapping_sha256') == MAP_SHA
            and attach.get('pid') == spec['pid'] and len(attach['verified_entries']) == 14
            and attach.get('physical') is False and attach.get('modified_on_disk_executable') is False, 'API attachment evidence')
    require(run.get('application_closed_normally') is True and run.get('physical') is False
            and run.get('outcome') == 'SUCCESS', 'Completed isolated Read required')
    require(ready.get('physical') is False and live.get('stage') == 'KERNEL', 'Virtual kernel state required')
    require(str(ready['port']) == spec['environment'].get('A2WC_RPC_PORT'), 'RPC port association')
    guard = (folder/'guard.log').read_text()
    require('ISOLATION_READY Software\\A2WC511R_VirtualRead\\'+name in guard, 'Isolation record missing')
    require('DLL_LOADED '+str(folder/'native/a2wc_ecuflash_virtual32.dll') in guard, 'Fake DLL load record missing')
    require(not re.search(r'(?im)DLL_LOADED [^\r\n]*(?:op20pt32\.dll|ftd2xx\.dll)', guard), 'Real provider load detected')
    before = (folder/'j2534.jsonl').read_bytes()
    rows = [json.loads(line) for line in before.splitlines()]
    require(len(rows) == live['calls'] and all(row.get('sequence') == i and row.get('physical') is False for i,row in enumerate(rows)), 'Trace sequence/virtual identity')
    closure = [row for row in rows if row['request']['function'] in ('PassThruOpen','PassThruClose')]
    require(closure[-1]['request']['function'] == 'PassThruClose' and closure[-1]['response']['status'] == 0, 'Installed host did not close provider')
    require(len((folder/'ECUFLASH_READ_OUTPUT.bin').read_bytes()) == SIZE, 'Earlier saved1MiB image required')
    return folder, spec, ready, before


def _difference_ranges(a, b):
    ranges, start = [], None
    for i, (left, right) in enumerate(zip(a, b)):
        if left != right and start is None: start = i
        elif left == right and start is not None: ranges.append([start, i]); start = None
    if start is not None: ranges.append([start, len(a)])
    return ranges


def _require_trace_prefix(report, before, after):
    preserved = after.startswith(before)
    if not preserved:
        report['status'] = 'FAIL'
        report['trace_continuity_error'] = 'Original provider trace changed or was truncated during collection'
    return preserved


def run(name):
    folder, spec, ready, before = _verify_session(name)
    snapshot = folder/'post_read_snapshot'
    snapshot.mkdir(exist_ok=False)
    original = snapshot/'j2534.jsonl'
    original.write_bytes(before)
    for filename in ('guard.log','live_state.json','API_ATTACH.json','RUN_RESULT.json','MODEL_INPUTS.json','ECUFLASH_READ_OUTPUT.bin'):
        (snapshot/filename).write_bytes((folder/filename).read_bytes())
    require((folder/'j2534.jsonl').read_bytes() == before, 'Trace changed before supplement start')
    output = ROOT/'reports/local/ecuflash_dynamic/raw_read_supplement'/name
    output.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'session': name, 'status': 'FAIL', 'physical': False,
              'classification': 'VIRTUAL_ONLY_PROTOCOL_REMEDIATION_PROTOTYPE_NOT_PHYSICAL_BACKEND',
              'installed_Read_exactness_changed': False, 'kernel_executed': False,
              'original_trace': {'path': str(original), 'sha256': sha(before), 'bytes': len(before),
                                 'events': len(before.splitlines())},
              'script_sha256': sha(Path(__file__).read_bytes()), 'fixed_range': [0, SIZE], 'fixed_chunk': CHUNK,
              'session_metadata_sha256': sha((folder/'session_private.json').read_bytes()),
              'verified_native_pins': NATIVE_PINS, 'installed_exe_sha256': EXE_SHA, 'API_mapping_sha256': MAP_SHA,
              'loopback': '127.0.0.1', 'cleanup_means_ECU_reset': False}
    journal_path = output/'SUPPLEMENT_RPC.jsonl'
    try:
        with journal_path.open('x', encoding='utf8', buffering=1) as journal:
            client = _LoopbackClient(ready['port'], spec['environment']['A2WC_RPC_TOKEN'], journal)
            data, blocks = client.collect()
            journal.flush(); os.fsync(journal.fileno())
        saved = (snapshot/'ECUFLASH_READ_OUTPUT.bin').read_bytes()
        require(saved == (folder/'ECUFLASH_READ_OUTPUT.bin').read_bytes(), 'Original saved image changed during supplement')
        expected = (folder/'synthetic_flash.bin').read_bytes()
        destination = output/'RAW_MODEL_RETURNED_BYTES.bin'
        destination.write_bytes(data)
        report.update(status='PASS_VIRTUAL_RAW_READ_ONLY', image={'path':str(destination),'sha256':sha(data),'bytes':len(data)},
                      blocks=blocks, all_bytes_from_command03=True, earlier_saved_sha256=sha(saved),
                      differences_from_installed_saved=_difference_ranges(data,saved),
                      different_byte_count=sum(a!=b for a,b in zip(data,saved)),
                      synthetic_reference_sha256=sha(expected), exact_matches_synthetic_reference=data==expected,
                      provider_closed=True, calls=client.sequence)
        require(data == expected, 'Returned bytes disagree with separately stored synthetic input')
    except Exception as error:
        report.update(status='FAIL', error=type(error).__name__+': '+str(error),
                      failure_behavior='Socket closed; no further data/control RPCs after failure; virtual provider channel state may remain open.')
    finally:
        report['supplement_trace'] = {'path':str(journal_path),'sha256':sha(journal_path.read_bytes()) if journal_path.exists() else None}
        after = (folder/'j2534.jsonl').read_bytes()
        combined = output/'COMBINED_PROVIDER_TRACE.jsonl'
        combined.write_bytes(after)
        preserved = _require_trace_prefix(report, before, after)
        report['combined_provider_trace'] = {'path':str(combined),'sha256':sha(after),'bytes':len(after),
                                           'original_prefix_preserved':preserved}
        (output/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'blocks'},indent=2))
    return 0 if report['status']=='PASS_VIRTUAL_RAW_READ_ONLY' else 1


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', help='Existing completed isolated virtual session name only')
    raise SystemExit(run(parser.parse_args().session))
