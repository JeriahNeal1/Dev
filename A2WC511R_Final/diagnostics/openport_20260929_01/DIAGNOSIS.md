# ECUFlash/OpenPort diagnostic read, 2026-09-29

One ECUFlash Read attempt was initiated and reached the error dialog. The adapter returned ECU identity `2F12515306`; the operation stopped after the seed/key step and before any logged kernel upload. No ROM was acquired. RK02 was not launched.

## Authorization and physical state

The user explicitly requested one installed ECUFlash ROM Read attempt to diagnose the OpenPort, superseding the earlier prohibition on using ECUFlash for this diagnostic task. The user confirmed engine OFF, ignition ON, green Test Mode connectors disconnected, Schumacher showing 10 A, and approximately 12.6 V. These are user reports, not software measurements. The earlier G18 power-loss gate was never satisfied, and the user subsequently changed the physical state. The original physical session is not complete.

## Observed execution

- Installed ECUFlash was launched as PID 13176. Executable SHA256: `5e1b1729446d306487bb7ed358b1ee050b11e440902bb23a05663d8575346115`.
- Provider SHA256: `f432084801762d919a3c31974616e097562424470003edc4f4fb843df34103cf`, matching the prior pinned provider.
- At 15:33:43 local time the exact enabled `sti05: Read from ECU` button was clicked once through its inspected UI control. `READ_CLICK_ONCE.json` prevents another click through this helper.
- The Connecting to ECU dialog was observed. It advanced before the subsequent automation action; the actor that dismissed it was not observed. The guarded continuation action found the error dialog and did not click or retry anything.
- At 15:33:52.565 the log records `SSM2 ECU ID is 2F12515306`.
- At 15:33:52.646 it records `Requesting Seed...`; at 15:33:52.690, `Sending Key [1]...`.
- At 15:33:53.308 and .309 it records `interface close`. The error dialog says to consult the log.
- There is no kernel upload, successful kernel-version response, ROM-block read, or ROM save in this attempt's log.
- The application was closed gracefully at 22:36:19 UTC. Process exit and absence of known diagnostic clients were verified in `CLEANUP.json`.

The final log is `ecuflash_log_20260929t153243.final.txt`, SHA256 `4b3bafa0853e0d42cacc094167da3581541de3f872e3b23b087e128f48629c62`. Original and earlier logs were copied before starting ECUFlash; UI snapshots and screenshots are retained in this folder. The after-attempt and final copies match.

## Adapter and driver observations

Windows reports the Tactrix Openport 2.0 J2534 Vehicle Interface present, status OK, ConfigManagerErrorCode 0, service `openport`. The associated provider is Tactrix Inc., driver version `1.0.0.4227`, INF `oem34.inf`. ECUFlash reports J2534 API 04.04, DLL 1.02.4870 and device firmware 1.17.4877. Enumeration alone is not a full adapter test; the received ECU identity additionally demonstrates bidirectional ECU communication during this attempt. Intermittent faults remain possible.

## Comparison and conclusion

Preserved successful July and August logs also include the preliminary `kernel get version`, interface closes, and `VIN read not supported`. Those messages alone do not identify a failure. The successful August log proceeds after Sending Key to `writing kernel area addr: FFFF3000 len:1234`, then kernel upload and DUAL1.07 response. Today's new attempt closes instead. A July unsuccessful attempt also stopped at this same visible stage before a later successful read.

The leading failure area is the programming-session/security transition before kernel upload. Test Mode being disconnected is a relevant admission condition to investigate, not a proved cause. The log does not record the raw security reply or a specific error code, so it cannot distinguish ECU rejection, a missing admission condition, and a timeout. It does not justify driver replacement or declaring the adapter faulty.

COBB's documentation confirms green Test Mode connectors are required for programming on the listed contemporary Subaru models; this contextual evidence is not an exact RK02 contract: https://www.cobbtuning.com/subaru-ecu-tuning-realtime-vs-reflash/

The earlier passive BF/A8 failure is separately explained by its broker rejecting a zero-length J2534 START_OF_MESSAGE indication before parsing identity. ECUFlash successfully obtaining identity strengthens the conclusion that the passive receiver needs its own offline compatibility correction. No sealed receiver or qualification artifact was modified here.

No second read, Write, Test Write, erase, or RK02 launch was initiated by the assistant. A future acquisition still needs its own qualified software and physical admission conditions; this diagnostic result is not a current-ROM capture.
