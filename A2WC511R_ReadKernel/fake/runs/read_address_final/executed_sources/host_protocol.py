"""Pure byte contracts. No provider, device, process, socket or arbitrary-call API.

The seed/upload transforms reproduce the public Subaru reference and the prior
hash-bound A2WC audit. See PROVENANCE.md. They are not silicon qualification.
"""
import sys
sys.dont_write_bytecode = True
import hashlib

ECU_ID = bytes.fromhex('2f12515306')
LOAD_ADDRESS = 0xFFFF3000
ENTRY_ADDRESS = 0xFFFF3004
FLASH_SIZE = 0x100000
BLOCK_SIZE = 512
UPLOAD_BLOCK = 128
VERSION = b'A2WC511R-RK01\0'
TABLE = (5,6,7,1,9,12,13,8,10,13,2,11,15,4,0,3,
         11,4,6,0,15,2,13,9,5,12,1,10,3,13,14,8)
UPLOAD_KEYS = (0x7856,0xCE22,0xF513,0x6E86)
SEED_KEYS = (0x88F0,0x6E74,0x6B70,0x3563,0x9D34,0xDBA3,0x503D,0xAFB8,
             0x3608,0x834F,0x3382,0x7CA3,0x437D,0x72EB,0x33BC,0x53DA)

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def _transform(data, keys):
    require(type(data) is bytes and len(data) % 4 == 0, 'Complete BE32 groups required')
    result = bytearray()
    for offset in range(0, len(data), 4):
        left = int.from_bytes(data[offset:offset+2], 'big')
        right = int.from_bytes(data[offset+2:offset+4], 'big')
        for key in keys:
            expanded = (right ^ key) * 0x10001
            substitution = 0
            for shift in (0,4,8,12):
                substitution |= TABLE[(expanded >> shift) & 31] << shift
            rotated = ((substitution >> 3) | (substitution << 13)) & 0xFFFF
            left, right = right, left ^ rotated
        result.extend(right.to_bytes(2, 'big'))
        result.extend(left.to_bytes(2, 'big'))
    return bytes(result)

def seed_key(seed):
    require(type(seed) is bytes and len(seed) == 4, 'Exactly four seed bytes required')
    return _transform(seed, SEED_KEYS)

def encrypt_upload(kernel):
    return _transform(kernel, UPLOAD_KEYS)

def decrypt_upload(ciphertext):
    return _transform(ciphertext, tuple(reversed(UPLOAD_KEYS)))

def stock_entry_checksum(kernel):
    require(type(kernel) is bytes and len(kernel) % 4 == 0, 'Aligned complete upload required')
    return sum(int.from_bytes(kernel[i:i+4], 'big') for i in range(0,len(kernel),4)) & 0xFFFF

def ssm(payload, response=False):
    require(type(payload) is bytes and 1 <= len(payload) <= 255, 'Bounded SSM payload')
    frame = bytes((0x80,0xF0 if response else 0x10,0x10 if response else 0xF0,len(payload))) + payload
    return frame + bytes((sum(frame) & 255,))

def parse_ssm(frame, response=False):
    require(type(frame) is bytes and len(frame) >= 6, 'Complete SSM frame required')
    require(frame[:3] == bytes((0x80,0xF0 if response else 0x10,0x10 if response else 0xF0)), 'SSM direction/header')
    require(frame[3] >= 1 and len(frame) == frame[3] + 5, 'Exact SSM length')
    require(sum(frame[:-1]) & 255 == frame[-1], 'SSM additive checksum')
    return frame[4:-1]

def beef(payload):
    require(type(payload) is bytes and 1 <= len(payload) <= 518, 'Bounded kernel payload')
    frame = b'\xBE\xEF' + len(payload).to_bytes(2,'big') + payload
    return frame + bytes((sum(frame) & 255,))

def parse_beef(frame):
    require(type(frame) is bytes and 6 <= len(frame) <= 523, 'Bounded complete kernel frame')
    require(frame[:2] == b'\xBE\xEF', 'Kernel frame magic')
    require(len(frame) == int.from_bytes(frame[2:4],'big') + 5, 'Exact kernel length')
    require(sum(frame[:-1]) & 255 == frame[-1], 'Kernel additive checksum')
    return frame[4:-1]

def declaration(kernel_size):
    require(type(kernel_size) is int and 8 <= kernel_size <= 0x2000 and kernel_size % 4 == 0, 'Owned kernel upload bound')
    return ssm(b'\x34\xFF\x30\x00\x04' + kernel_size.to_bytes(3,'big'))

def upload_frames(kernel):
    encrypted = encrypt_upload(kernel)
    for offset in range(0,len(encrypted),UPLOAD_BLOCK):
        address = LOAD_ADDRESS + offset
        yield ssm(b'\x36' + (address & 0xFFFFFF).to_bytes(3,'big') + encrypted[offset:offset+UPLOAD_BLOCK])

def read_request(pass_number, address):
    require(type(pass_number) is int and pass_number in (0,1), 'Only two acquisition passes')
    require(type(address) is int and 0 <= address < FLASH_SIZE and address % BLOCK_SIZE == 0, 'Fixed ascending block range')
    return beef(b'\x03' + bytes((pass_number,)) + address.to_bytes(4,'big') + b'\x02\x00')

def read_response(frame, pass_number, address):
    expected = b'\x83' + bytes((pass_number,)) + address.to_bytes(4,'big')
    payload = parse_beef(frame)
    require(len(payload) == 518 and payload[:6] == expected, 'Wrong read length/opcode/pass/address')
    return payload[6:]
