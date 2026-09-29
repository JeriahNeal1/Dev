"""Pure, explicitly hypothetical sti05 virtual ECU; no device or process APIs.

API: VirtualECU.handle_tx(protocol_id, wire) records one complete transmitted
frame and returns its audit event. drain_replies() returns queued Reply objects
with protocol_id, data and provenance. Echo/transport timing belong to the
caller; this model queues only ECU replies. Unknown requests are recorded and
receive no positive reply. No uploaded code is executed.
"""
import sys
sys.dont_write_bytecode = True
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT/'reports/local/ecuflash_dynamic/protocol_reference/protocol_reference.py'
REFERENCE_SHA256 = '9e8061a9ba08c8d9adb0e908282bbd6ee9b072bd7a0f0e645db171d086fb26fe'
if hashlib.sha256(REFERENCE.read_bytes()).hexdigest() != REFERENCE_SHA256:
    raise RuntimeError('Protocol reference changed; virtual model requires review')
_spec = importlib.util.spec_from_file_location('a2wc_virtual_protocol_reference', REFERENCE)
_reference = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reference)

FLASH_SIZE = 0x100000
HISTORICAL_GAPS = ((0x86000,0xC0000),(0xCF000,0xFF000))
UPLOAD_START = 0xFFFF3000
KERNEL_VERSION = b'OpenECU Subaru SH7058 DUAL  Kernel V1.07'
BF_RESPONSE = bytes.fromhex(
    '80f01039ffa210112f1251530673facba62b81fea800000060ce54f9b1e4000c200000000000'
    'dc00005d1f3080f226000043fb00e1000000000000c1f0c2')
FORBIDDEN_KERNEL = {0x07:'EEPROM read outside model',0x08:'EEPROM write',
                    0x20:'flash enable',0x21:'flash disable outside Read model',
                    0x22:'flash-buffer write',0x23:'flash-buffer validation/Test Write',
                    0x24:'flash commit',0x25:'flash erase'}
FORBIDDEN_SSM = {0x11:'ECU reset',0xB0:'ordinary RAM block write',
                 0xB8:'ordinary RAM byte write',0x2F:'IO control',0x30:'IO control'}


@lru_cache(maxsize=4)
def make_synthetic_flash(variant='baseline'):
    """Return a deterministic synthetic 1MiB, never a flashable OEM image.

    baseline: every block patterned; gaps_ff: only historical gaps replaced
    by FF; gap_sentinels: those FF gaps have unique first/last block markers.
    Variants change no bytes outside the two historical gaps.
    """
    if variant not in ('baseline','gaps_ff','gap_sentinels','crc_collision'):
        raise ValueError('Unknown synthetic flash variant')
    data = bytearray(((i*73)^(i>>8)^(i>>16)^0xA5)&255 for i in range(FLASH_SIZE))
    for address in range(0,FLASH_SIZE,512):
        data[address:address+8] = b'VECU'+address.to_bytes(4,'big')
        data[address+504:address+512] = b'END!'+address.to_bytes(4,'big')
    if variant in ('gaps_ff','gap_sentinels'):
        for start,end in HISTORICAL_GAPS:
            data[start:end] = b'\xff'*(end-start)
            if variant == 'gap_sentinels':
                for address in range(start,end,512):
                    data[address:address+8] = b'GAP!'+address.to_bytes(4,'big')
                    data[address+504:address+512] = b'GEND'+address.to_bytes(4,'big')
    if variant=='crc_collision':
        fixture=ROOT/'reports/local/ecuflash_dynamic/coverage_contract/nonblank_crc_equal_ff_4096.bin'
        page=fixture.read_bytes()
        if hashlib.sha256(page).hexdigest()!='16847923994211cacbfad93badfd78df74e5bfa5b3493581f9ed99eafd195877':
            raise ValueError('Collision negative control changed')
        if page==b'\xff'*4096 or zlib.crc32(page)!=zlib.crc32(b'\xff'*4096):raise ValueError('Invalid collision control')
        data[0x86000:0x87000]=page
    return bytes(data)


@dataclass(frozen=True)
class Reply:
    protocol_id: int
    data: bytes
    provenance: dict


class ModelReject(Exception):
    def __init__(self, classification, reason):
        super().__init__(reason)
        self.classification = classification


class VirtualECU:
    """An auditable protocol hypothesis, not a SH7058 execution model.

    response_mask=0x40 is the requested initial hypothesis; 0x80 selects the
    competing older OpenECU framing. Upload length defaults to the historically
    logged 4660 bytes. Changing either requires an explicit caller argument.
    All request failures preserve the current stage and queue no new reply.
    Existing queued replies remain visible; the transport owns their delivery.
    """
    def __init__(self, *, response_mask=0x40, flash=None,
                 sentinel_variant='baseline', seed=bytes.fromhex('12345678'),
                 expected_upload_length=0x1234):
        if type(response_mask) is not int or response_mask not in (0x40,0x80):
            raise ValueError('response_mask must explicitly be 0x40 or 0x80')
        if type(seed) is not bytes or len(seed)!=4:
            raise ValueError('Exactly four synthetic seed bytes required')
        if type(expected_upload_length) is not int or not 4<=expected_upload_length<=0x8000 or expected_upload_length%4:
            raise ValueError('Explicit upload length must be aligned and fit reviewed virtual RAM bound')
        if flash is None:
            flash = make_synthetic_flash(sentinel_variant)
            self.flash_origin = 'SYNTHETIC_'+sentinel_variant.upper()
        else:
            if type(flash) is not bytes or len(flash)!=FLASH_SIZE:
                raise ValueError('Caller flash must be exactly 1MiB immutable bytes')
            self.flash_origin = 'CALLER_SUPPLIED_BYTES_NOT_CURRENT_ROM_ATTESTATION'
        self._flash = flash
        self.flash_sha256 = hashlib.sha256(flash).hexdigest()
        self.response_mask = response_mask
        self.seed = seed
        self.expected_upload_length = expected_upload_length
        self.stage = 'OEM'
        self.events = []
        self.captured_upload_frames = []
        self.accepted_upload_frames = []
        self.uploaded_ciphertext = b''
        self.uploaded_plaintext = None
        self.download_declarations = 0
        self._replies = deque()

    @property
    def flash(self):
        return self._flash

    def drain_replies(self):
        replies = list(self._replies)
        self._replies.clear()
        return replies

    def pop_reply(self):
        return self._replies.popleft() if self._replies else None

    @property
    def pending_replies(self):
        return len(self._replies)

    def _reply(self, data, event, basis, **detail):
        provenance = {'classification':'VIRTUAL_RESPONSE_HYPOTHESIS',
                      'not_vehicle_telemetry':True,'kernel_executed':False,
                      'request_event_index':event['index'],'basis':basis,
                      'response_mask_hypothesis':f'{self.response_mask:02X}',
                      'reference_sha256':REFERENCE_SHA256,**detail}
        reply = Reply(3,data,provenance)
        self._replies.append(reply)
        event['replies'].append({'protocol_id':3,'wire_hex':data.hex(),'provenance':dict(provenance)})

    def _ssm_reply(self, payload, event, **detail):
        self._reply(_reference.ssm(payload,response=True),event,
                    'REFERENCE_MINIMAL_POSITIVE_RESPONSE_NOT_INSTALLED_ACCEPTANCE',**detail)

    def _require(self, valid, reason, classification='UNSUPPORTED_SEQUENCE'):
        if not valid:
            raise ModelReject(classification,reason)

    def handle_tx(self, protocol_id, wire, *, timestamp_us=None):
        """Accept one complete TX frame. Record errors instead of guessing ACKs."""
        event = {'index':len(self.events),'protocol_id':protocol_id if type(protocol_id) is int else None,
                 'wire_hex':wire.hex() if type(wire) is bytes else None,
                 'wire_type':type(wire).__name__,'timestamp_us':timestamp_us,
                 'stage_before':self.stage,'stage_after':self.stage,'replies':[],
                 'classification':'UNSUPPORTED','reason':None,'physical':False}
        self.events.append(event)
        if type(wire) is bytes and len(wire)>=5 and wire[:1]==b'\x80' and wire[4] in (0x34,0x36):
            self.captured_upload_frames.append(wire)  # Include rejected/malformed uploads.
        try:
            self._require(type(protocol_id) is int and protocol_id==3,
                          'Only ISO9141 protocol3 is modeled','UNSUPPORTED_PROTOCOL')
            self._require(type(wire) is bytes and 1<=len(wire)<=65540,
                          'An immutable bounded complete frame is required','MALFORMED')
            self._require(timestamp_us is None or (type(timestamp_us) is int and 0<=timestamp_us<=0xFFFFFFFF),
                          'Invalid provider timestamp','MALFORMED')
            if wire.startswith(b'\xBE\xEF'):
                self._kernel(wire,event)
            elif wire.startswith(b'\x80'):
                try:
                    payload = _reference.parse_ssm(wire)
                except ValueError as error:
                    raise ModelReject('MALFORMED',str(error)) from error
                self._ssm(payload,wire,event)
            else:
                raise ModelReject('UNSUPPORTED_FRAMING','No model for this raw frame; legacy raw53 is not silently accepted')
            if event['classification']=='UNSUPPORTED':
                event['classification']='HYPOTHETICAL_REPLY'
        except ModelReject as error:
            event['classification']=error.classification
            event['reason']=str(error)
        event['stage_after']=self.stage
        return event

    def _ssm(self, payload, wire, event):
        command = payload[0]
        if command in FORBIDDEN_SSM:
            raise ModelReject('FORBIDDEN',FORBIDDEN_SSM[command])
        self._require(self.stage!='KERNEL','OEM protocol after kernel entry has no established restoration contract')
        identity_stages = ('OEM','IDENTIFIED','COMM_STARTED','TIMINGS_ACCEPTED')
        if payload==b'\xBF':
            self._require(self.stage in identity_stages,'BF cannot reset a security/upload transaction')
            self.stage='IDENTIFIED'
            self._reply(BF_RESPONSE,event,'ACTUAL_STOCK_BF_PRODUCER_BYTES_REPLAYED_VIRTUALLY',
                        ecu_id='2F12515306',current_rom_identified=False)
        elif payload==b'\x81':
            self._require(self.stage in identity_stages[1:],'BF identity required before communication start')
            self.stage='COMM_STARTED'
            self._ssm_reply(b'\xC1',event,unmodeled='Additional installed keyword fields unknown')
        elif payload==b'\x83\x00':
            self._require(self.stage in identity_stages[1:],'BF identity required before timing query')
            self.stage='TIMINGS_ACCEPTED'
            self._ssm_reply(b'\xC3',event,unmodeled='Installed timing bytes unknown; opcode-only hypothesis')
        elif payload==b'\x27\x01':
            self._require(self.stage in identity_stages[1:],'Identity required; seed requests are not retried implicitly')
            self.stage='SEED_SENT'
            self._ssm_reply(b'\x67\x01'+self.seed,event,synthetic_seed_hex=self.seed.hex())
        elif command==0x27 and len(payload)==6 and payload[1]==2:
            self._require(self.stage=='SEED_SENT','No matching seed transaction')
            self._require(payload[2:]==_reference.seed_key(self.seed),'Key differs from reference transform','REJECTED_SECURITY')
            self.stage='AUTHENTICATED'
            self._ssm_reply(b'\x67\x02\x34',event,basis_detail='INSTALLED_RVA9B136_REQUIRES_POST_SID_LENGTH2_AND_BYTE1_34')
        elif payload==bytes.fromhex('108502'):
            self._require(self.stage=='AUTHENTICATED','Validated reference key required')
            self.stage='PROGRAMMING'
            self._ssm_reply(b'\x50',event,reference_next_baud=15625)
        elif command==0x34:
            self._require(self.stage=='PROGRAMMING' or (self.stage=='UPLOADING' and not self.uploaded_ciphertext and self.download_declarations==1),
                          'Only observed double declaration before any data is modeled')
            self._require(len(payload)==8 and payload[4]==4,'Unknown34 declaration layout','MALFORMED')
            address=0xFF000000|int.from_bytes(payload[1:4],'big')
            length=int.from_bytes(payload[5:8],'big')
            self._require(address==UPLOAD_START and length==self.expected_upload_length,
                          'Download differs from explicit RAM start/length contract','UNSUPPORTED_RANGE')
            self.download_declarations+=1
            self.accepted_upload_frames=[wire]
            self.stage='UPLOADING'
            self._ssm_reply(b'\x74',event,virtual_RAM_start=address,virtual_RAM_length=length,
                            declaration_number=self.download_declarations,
                            basis_detail='INSTALLED9C154_AND9C164_DOUBLE34_BEFORE_DATA; EXPLICIT_IDEMPOTENT_VIRTUAL_RAM_DECLARATION')
        elif command==0x36:
            self._require(self.stage=='UPLOADING','No incomplete declared upload')
            remaining=self.expected_upload_length-len(self.uploaded_ciphertext)
            amount=min(128,remaining)
            self._require(len(payload)==4+amount,'Transfer must match next128-byte block or exact final remainder','MALFORMED')
            address=0xFF000000|int.from_bytes(payload[1:4],'big')
            self._require(address==UPLOAD_START+len(self.uploaded_ciphertext),
                          'Out-of-order, overlapping, duplicate or gapped upload','UNSUPPORTED_RANGE')
            accepted=self.accepted_upload_frames+[wire]
            ciphertext=self.uploaded_ciphertext+payload[4:]
            if len(ciphertext)==self.expected_upload_length:
                # Revalidate the complete captured wire sequence before accepting entry.
                rebuilt=_reference.reassemble_transfer36(accepted)
                self.uploaded_plaintext=rebuilt['plaintext_reference_decryption']
                self.stage='UPLOADED'
                event['upload_ciphertext_sha256']=hashlib.sha256(ciphertext).hexdigest()
                event['reference_plaintext_sha256']=hashlib.sha256(self.uploaded_plaintext).hexdigest()
            self.accepted_upload_frames=accepted
            self.uploaded_ciphertext=ciphertext
            self._ssm_reply(b'\x76',event,accepted_upload_bytes=len(ciphertext),
                            installed_transfer_checksum_verified=False)
        elif payload==bytes.fromhex('310101'):
            self._require(self.stage=='UPLOADED' and self.uploaded_plaintext is not None,
                          'Complete validated frame coverage required before virtual kernel entry')
            self.stage='KERNEL'
            self._ssm_reply(b'\x71',event,reference_next_baud=62500,
                            installed_transfer_checksum_verified=False,
                            model_transition_only_uploaded_code_not_executed=True)
        elif command==0x31:
            raise ModelReject('FORBIDDEN','Unrecognized routine control; only explicit310101 is modeled')
        else:
            raise ModelReject('UNSUPPORTED_COMMAND',f'No SSM model for payload {payload.hex()}')

    def _kernel(self, wire, event):
        self._require(len(wire)>=6 and len(wire)==int.from_bytes(wire[2:4],'big')+5
                      and wire[-1]==sum(wire[:-1])&255,'Malformed BEEF length/checksum','MALFORMED')
        payload=wire[4:-1]
        self._require(bool(payload),'Empty BEEF payload','MALFORMED')
        command=payload[0]
        if command in FORBIDDEN_KERNEL:
            raise ModelReject('FORBIDDEN',FORBIDDEN_KERNEL[command])
        if self.stage!='KERNEL':
            if payload==b'\x01':
                event['classification']='EXPECTED_TIMEOUT'
                event['reason']='No virtual kernel before complete upload plus explicit entry'
                return
            raise ModelReject('UNSUPPORTED_SEQUENCE','No running virtual kernel')
        detail={}
        if payload==b'\x01':
            data=KERNEL_VERSION+b'\x00'
            detail['version_basis']='CAPTURED_B0989858_KERNEL_FFFF32F0_COPIES41_BYTES_FROM_FFFF41FC; LEAF_SIM_VALIDATED'
        elif payload==b'\x05':
            data=(0x208).to_bytes(4,'big')
            detail['capacity_basis']='PINNED_NAMED_RESOURCE_CANDIDATE_FFFF33D4_VALUE_0208'
        elif payload==b'\x06':
            data=(4096).to_bytes(4,'big')
        elif command in (2,3):
            required=9 if command==2 else 7
            self._require(len(payload)==required,'Unknown CRC/read request layout','MALFORMED')
            address=int.from_bytes(payload[1:5],'big')
            length=int.from_bytes(payload[5:],'big')
            self._require(length>0 and address<FLASH_SIZE and address+length<=FLASH_SIZE,
                          'Read/CRC outside immutable virtual flash','UNSUPPORTED_RANGE')
            self._require(command!=3 or length<=514,'Read exceeds candidate read-handler capacity','UNSUPPORTED_RANGE')
            raw=self.flash[address:address+length]
            data=(zlib.crc32(raw)&0xFFFFFFFF).to_bytes(4,'big') if command==2 else raw
            detail={'address':address,'length':length,'flash_sha256':self.flash_sha256,
                    'flash_origin':self.flash_origin,'backing_span_sha256':hashlib.sha256(raw).hexdigest()}
            if command==2:
                detail['CRC_hypothesis']='ISO_HDLC_HISTORICAL_HOST_VECTOR_EDB88320'
        elif command==4:
            raise ModelReject('UNSUPPORTED_COMMAND','Programming-voltage units/value are not invented')
        else:
            raise ModelReject('UNSUPPORTED_COMMAND',f'No BEEF model for payload {payload.hex()}')
        self._reply(_reference.kernel_reply(command,data,response_mask=self.response_mask),event,
                    'REFERENCE_BEEF_RESPONSE_UNEXECUTED_KERNEL',**detail)
