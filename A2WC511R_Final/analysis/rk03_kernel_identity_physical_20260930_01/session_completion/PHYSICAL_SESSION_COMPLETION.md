# Completed RK03 kernel-start/identity physical session

RK03_KERNEL_START_IDENTITY_PHYSICAL = PASS
OEM_RETURN_AFTER_KERNEL_START_IDENTITY = PASS

Session RK03_KERNEL_START_IDENTITY_01 ran exactly once, after the fresh simplified ignition states and exact authorization. All15 fixed chunks received their76 ACK. One fixed start atFFFF3004 and one fixed identity query returned exactly A2WC511R-RK02 followed byNUL. The host emitted24 requests total and cleaned up both filters, channel and provider. There were zero ROM-read requests and zero flash operations.

Exact start frame: 8010f003310101b6.
Exact start ACK: 80f01003710101f6.
Exact identity query: beef000101af.
Exact identity reply: beef000f8141325743353131522d524b3032005f.

After operator-confirmed IGNITION OFF then NORMAL MODE ON, the qualified passive observer received BF2F12515306 and120/120 samples of the fixed six variables: PASS_CAPTURE_ONLY. Observer, broker and provider cleanup passed. The passive wire contains only oneBF and120A8 requests. No physical operation after that return is authorized in this run.

Independent raw physical review passed. The fixed executable remains SHA256623dc766ca69a97b16f7beabc9acb909a1225eabb8a21c40fe8379b4f72b593f; certificate SHA25619dc92d085a5721d7af280fc8fabf32a22919a9a370ec19e8052c8d6f8cf9cf8. The unchanged1808-byte kernel remains SHA2563a65d6f0700bae394a24ba9f552d03500b7f66e6344ec57613f10bfd360d8581.

Earlier reports that say physical kernel start/identity NOT RUN are historical checkpoints, superseded by this preserved physical PASS. They have not been edited.

The subsequent RK03_BOUNDED_ROM_READ scope is offline only and has a separate report/certificate. No bounded or full physical ROM acquisition occurred here. The preserved direct ECUFlash current.bin remains authoritative; this identity/passive return is not a new image acquisition or whole-ROM attestation.
