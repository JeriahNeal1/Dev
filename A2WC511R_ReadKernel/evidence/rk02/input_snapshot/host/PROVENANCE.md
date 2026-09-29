# Host protocol evidence

This new tree uses prior artifacts as read-only evidence. It does not execute installed ECUFlash or load a physical provider.

- `Astra_A2WC511R/reports/local/ecuflash_dynamic/protocol_reference/protocol_reference.py`, SHA256 `9e8061a9ba08c8d9adb0e908282bbd6ee9b072bd7a0f0e645db171d086fb26fe`, records the public seed/key and upload-word transform with independent fixed vectors.
- `api_boundary/DOWNLOAD_ACK_CONTRACT.json` records the observed 34/36/31 payload shapes: fixed FFFF3000, mode04, BE24 size/address, 128-byte data chunks and explicit310101.
- `read_audit/ENTRY_CHECKSUM_ADDENDUM.json` records actual stock handler0000194C: complete BE32 sum low16 equals5AA5; conditional post-ACK path reachesFFFF3004. It does not prove physical ACK/upload timing.
- `api_boundary/SEED_KEY_CONTRACT.json` records four key bytes and normal positive response670234.

The public algorithm reference is `Astra_A2WC511R/work/M07_reference/subaru-ecu-flashing/encryption.py` (repository GPLv3). The new pure implementation retains that provenance; constants, byte order and output vectors must agree. The new kernel itself does not contain the security/upload transforms.

SSM framing uses80/target/source/one-byte payload length/payload/additive8 checksum. Upload data consists of encrypted complete big-endian32-bit words; the outer SSM checksum covers encrypted wire bytes. Entry checksum applies to decrypted plaintext, not ciphertext. No checksum insertion or binary alteration is performed by the host: the build-owned kernel must already meet the stock entry checksum and exact SHA pin.

Kernel replies are provided only by the new simulator executing the exact uploaded project-owned binary. The fake server's boot negotiation remains an explicit software model. Separate `evidence/contracts/KWP_WIRE_CONTRACT.json` executes the actual stock KWP parser and serializer, and `UPLOAD_WIRE_CONTRACT.json` executes all 16 fixed 34/36/31 frames through the actual stock loader to the exact uploaded bytes and jump to FFFF3004. Those scoped executable contracts strengthen the model; they do not turn fake server negotiation into OEM execution or establish physical UART, adapter or power-cycle behavior.

The stock 36 handler can write decrypted RAM before rejecting a trailing frame checksum. Any ambiguous upload failure therefore means temporary RAM may already have changed. The host aborts without retry or further protocol requests; partial evidence is retained. Neither error exit nor normal provider close is described as ECU restoration.

The future physical target uses the same fixed installed provider previously pinned by the BF/A8 backend: `C:\Windows\SysWOW64\op20pt32.dll`, SHA256 `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`. `PHYSICAL_BINDING_PLAN.json` links the prior broker, transport configuration and fresh read-only snapshot. The differing OpenPort driver-package copy is not selected. The physical target is compiled only after an eligible offline certificate and is never executed during this run.
