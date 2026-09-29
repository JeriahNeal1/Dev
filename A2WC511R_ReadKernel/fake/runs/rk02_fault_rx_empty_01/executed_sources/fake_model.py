"""Modeled stock upload followed by actual project-kernel SH-2E execution.

No kernel reply is constructed here. CPU SCI writes are the sole source of all
kernel version and raw-read replies. OEM boot negotiation is explicitly modeled.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
from host.protocol import (ECU_ID,LOAD_ADDRESS,ENTRY_ADDRESS,require,sha256,ssm,
                           parse_ssm,decrypt_upload,seed_key,stock_entry_checksum)

BF_PAYLOAD = bytes.fromhex('ffa210112f1251530673facba62b81fea800000060ce54f9b1e4000c200000000000dc00005d1f3080f226000043fb00e1000000000000c1f0')

class OwnedKernelECU:
    def __init__(self,manifest_path,rom_path,rom_sha256,kernel,expected_kernel_sha256,trace_dir):
        require(type(kernel) is bytes and sha256(kernel)==expected_kernel_sha256,'Pinned owned plaintext')
        require(8<=len(kernel)<=8192 and len(kernel)%4==0,'Fixed RAM download span')
        require(stock_entry_checksum(kernel)==0x5AA5,'Stock entry checksum must hold')
        self.kernel=kernel;self.expected_kernel_sha256=expected_kernel_sha256
        self.manifest_path=Path(manifest_path);self.rom_path=Path(rom_path)
        self.rom_sha256=rom_sha256;self.trace_dir=Path(trace_dir)
        self.state='IDENTITY';self.cipher=bytearray();self.cpu=None
        self.seed=bytes.fromhex('12345678');self.events=[];self.failure=None

    def exchange(self,wire,baud):
        require(self.state!='FAIL','Terminal fake ECU cannot resume after failure')
        event={'sequence':len(self.events),'state_before':self.state,'tx_hex':wire.hex(),
               'baud':baud,'physical':False,'kernel_executed':self.cpu is not None}
        self.events.append(event)
        try:
            if self.state=='KERNEL':
                require(baud==62500,'Kernel baud contract')
                result=self.cpu.exchange(wire)
                status=result['status'] if isinstance(result,dict) else result.status
                require(status=='PASS','Kernel execution failed: '+str(result))
                reply=result['tx_bytes'] if isinstance(result,dict) else result.tx_bytes
                require(type(reply) is bytes and len(reply)>0,'No kernel reply; terminal failure, no retry')
                event['provenance']='EXECUTED_OWNED_KERNEL_SCI_TX'
            else:
                payload=parse_ssm(wire)
                expected_baud=15625 if self.state in ('DECLARE','UPLOAD','ENTRY') else 4800
                require(baud==expected_baud,'Boot state baud contract')
                event['provenance']='MODELED_OEM_BOOT_NEGOTIATION_NOT_OEM_EXECUTION'
                if self.state=='IDENTITY':
                    require(payload==b'\xBF','Identity must be first');reply=ssm(BF_PAYLOAD,True);self.state='COMMUNICATION'
                elif self.state=='COMMUNICATION':
                    require(payload==b'\x81','Communication start sequence');reply=ssm(bytes.fromhex('C1EF8F'),True);self.state='TIMINGS'
                elif self.state=='TIMINGS':
                    require(payload==b'\x83\x00','Fixed timing query');reply=ssm(bytes.fromhex('C30000FF00FF00'),True);self.state='SEED'
                elif self.state=='SEED':
                    require(payload==b'\x27\x01','Fixed seed query');reply=ssm(b'\x67\x01'+self.seed,True);self.state='KEY'
                elif self.state=='KEY':
                    require(payload==b'\x27\x02'+seed_key(self.seed),'Exact derived key');reply=ssm(bytes.fromhex('670234'),True);self.state='SESSION'
                elif self.state=='SESSION':
                    require(payload==bytes.fromhex('108502'),'Fixed diagnostic session');reply=ssm(bytes.fromhex('5085'),True);self.state='DECLARE'
                elif self.state=='DECLARE':
                    require(payload==b'\x34\xFF\x30\x00\x04'+len(self.kernel).to_bytes(3,'big'),'Exact single fixed RAM declaration')
                    reply=ssm(bytes.fromhex('7484'),True);self.state='UPLOAD'
                elif self.state=='UPLOAD':
                    amount=min(128,len(self.kernel)-len(self.cipher))
                    require(len(payload)==amount+4 and payload[:1]==b'\x36','Exact transfer size/opcode')
                    require(int.from_bytes(payload[1:4],'big')==(LOAD_ADDRESS+len(self.cipher))&0xFFFFFF,'Contiguous addressed upload')
                    self.cipher.extend(payload[4:]);reply=ssm(b'\x76',True)
                    if len(self.cipher)==len(self.kernel):
                        plaintext=decrypt_upload(bytes(self.cipher))
                        require(plaintext==self.kernel and sha256(plaintext)==self.expected_kernel_sha256,'Decrypted bytes differ from pinned compiled kernel')
                        require(stock_entry_checksum(plaintext)==0x5AA5,'Rejected entry checksum')
                        self.trace_dir.mkdir(parents=True,exist_ok=False)
                        (self.trace_dir/'uploaded_ciphertext.bin').write_bytes(self.cipher)
                        (self.trace_dir/'uploaded_plaintext.bin').write_bytes(plaintext)
                        self.state='ENTRY'
                elif self.state=='ENTRY':
                    require(payload==bytes.fromhex('310101'),'Only fixed entry request')
                    from sim.harness import KernelSession
                    self.cpu=KernelSession(self.manifest_path,self.rom_path,self.rom_sha256,trace_dir=self.trace_dir/'execution_cpu',kernel_bytes=bytes(self.kernel),receiver_self_echo=True)
                    result=self.cpu.start(entry=ENTRY_ADDRESS)
                    status=result['status'] if isinstance(result,dict) else result.status
                    require(status=='PASS','Kernel startup failed: '+str(result))
                    tx=result['tx_bytes'] if isinstance(result,dict) else result.tx_bytes
                    require(tx==b'','Unexpected unsolicited kernel TX at startup')
                    self.state='KERNEL';reply=ssm(bytes.fromhex('710101'),True)
                    event['kernel_start_executed']=True
                else:
                    raise ValueError('Unsupported modeled state')
            event.update(rx_hex=reply.hex(),state_after=self.state,status='PASS')
            return reply
        except Exception as error:
            self.failure=type(error).__name__+': '+str(error);self.state='FAIL'
            event.update(state_after=self.state,status='FAIL',failure=self.failure)
            raise
