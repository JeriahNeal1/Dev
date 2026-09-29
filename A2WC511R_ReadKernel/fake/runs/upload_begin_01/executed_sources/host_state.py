"""Deterministic fixed acquisition plan and fail-closed reply verifier.

This module has no transport. The native fake-only host follows the same plan;
its recorded TX/RX is replayed here independently after completion.
"""
import sys
sys.dont_write_bytecode = True
from dataclasses import dataclass
from .protocol import (ECU_ID,VERSION,FLASH_SIZE,BLOCK_SIZE,require,sha256,
                       stock_entry_checksum,ssm,parse_ssm,beef,parse_beef,
                       declaration,upload_frames,seed_key,read_request,read_response)

@dataclass(frozen=True)
class Step:
    kind: str
    wire: bytes
    baud: int
    pass_number: int = -1
    address: int = -1

class HostState:
    def __init__(self, kernel, expected_sha256):
        require(type(kernel) is bytes and sha256(kernel) == expected_sha256, 'Exact owned kernel hash required')
        declaration(len(kernel))
        require(stock_entry_checksum(kernel) == 0x5AA5, 'Owned kernel stock entry checksum')
        self.kernel = kernel
        self.expected_sha256 = expected_sha256
        self.status = 'ACTIVE'
        self.failure = None
        self.step_count = 0
        self.images = [bytearray(),bytearray()]
        self._plan = self._steps()
        self.pending = next(self._plan)

    def _steps(self):
        yield Step('identity',ssm(b'\xBF'),4800)
        yield Step('communication',ssm(b'\x81'),4800)
        yield Step('timings',ssm(b'\x83\x00'),4800)
        seed_reply = yield Step('seed',ssm(b'\x27\x01'),4800)
        seed = parse_ssm(seed_reply,True)[2:]
        yield Step('key',ssm(b'\x27\x02'+seed_key(seed)),4800)
        yield Step('session',ssm(bytes.fromhex('108502')),4800)
        yield Step('declaration',declaration(len(self.kernel)),15625)
        for wire in upload_frames(self.kernel):
            yield Step('upload',wire,15625)
        yield Step('entry',ssm(bytes.fromhex('310101')),15625)
        yield Step('version',beef(b'\x01'),62500)
        for pass_number in (0,1):
            for address in range(0,FLASH_SIZE,BLOCK_SIZE):
                yield Step('read',read_request(pass_number,address),62500,pass_number,address)

    def accept(self, wire):
        require(self.status == 'ACTIVE' and self.pending is not None, 'Terminal host cannot accept/retry')
        step = self.pending
        try:
            if step.kind == 'version':
                require(parse_beef(wire) == b'\x81'+VERSION, 'Exact project kernel identity')
            elif step.kind == 'read':
                data = read_response(wire,step.pass_number,step.address)
                require(len(self.images[step.pass_number]) == step.address, 'Exact contiguous image coverage')
                self.images[step.pass_number].extend(data)
            else:
                payload = parse_ssm(wire,True)
                if step.kind == 'identity':
                    require(len(payload) == 57 and payload[:4] == bytes.fromhex('ffa21011') and payload[4:9] == ECU_ID, 'Exact A2WC511R ECU identity')
                elif step.kind == 'seed':
                    require(len(payload) == 6 and payload[:2] == b'\x67\x01', 'Exact seed response')
                else:
                    expected = {'communication':b'\xC1','timings':b'\xC3','key':bytes.fromhex('670234'),
                                'session':b'\x50','declaration':bytes.fromhex('7484'),'upload':b'\x76',
                                'entry':bytes.fromhex('710101')}[step.kind]
                    require(payload == expected, 'Exact positive '+step.kind+' reply')
            self.step_count += 1
            try:
                self.pending = self._plan.send(wire)
            except StopIteration:
                require(len(self.images[0]) == len(self.images[1]) == FLASH_SIZE, 'Two complete images required')
                require(self.images[0] == self.images[1], 'Read passes differ')
                self.status = 'PASS';self.pending = None
        except Exception as error:
            self.fail(type(error).__name__+': '+str(error))
            raise

    def fail(self, reason):
        self.status = 'FAIL';self.failure = str(reason);self.pending = None

    def summary(self):
        return {'status':self.status,'failure':self.failure,'steps':self.step_count,
                'kernel_sha256':self.expected_sha256,'physical':False,
                'passes':[{'bytes':len(data),'sha256':sha256(data),'complete':len(data)==FLASH_SIZE} for data in self.images]}
