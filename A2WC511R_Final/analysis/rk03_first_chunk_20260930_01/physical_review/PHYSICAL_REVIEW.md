# Independent physical first-chunk audit

PASS_INDEPENDENT_PHYSICAL_FIRST_CHUNK_AUDIT. The one recorded invocation exited0 at2026-09-30T03:54:59.367746Z with PASS_FIRST_CHUNK_PROBE_ONLY. All40 J2534 calls and3 wait calls returned0. All9 raw session files remained byte-identical during this audit.

The exact qualified PE sent eight requests: BF,81,8300,2701,2702,108502, one34 and one36. ECU identity was2F12515306; seed a917a34f produced key4015f497 and the ECU returned full670234. Full5085,7484 and76 replies followed. The final reply was80f0100176f7. The only transfer carried the fixed128 cipher bytes toFFFF3000..FFFF307F. No second transfer, kernel-start, ROM-read or flash command followed.

Initial five SET/GET values and the broad four-zero filter matched the contract. Measured minimum waits were203.774ms,102.1152ms and200.4695ms. Baud15625 SET succeeded, then CLEAR_TX and CLEAR_RX succeeded. This establishes accepted configuration and subsequent communication; it is not a baud GET or waveform measurement.

After76, the only calls were StopMsgFilter, Disconnect and Close, all successful. The launcher recorded process exit and both client scans passed. This audit invoked no native program or provider.

BF/81/83 request and response bytes match the earlier successful transition exactly. This success does not isolate the historical RK02 failure cause or qualify a full upload/read. ACK acceptance is not independent RAM readback. OEM return requires the separate human-gated passive recovery check.
