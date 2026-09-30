# Passive receiver START_OF_MESSAGE correction

Status: **PASS_OFFLINE_PASSIVE_RECEIVER_QUALIFICATION**. The corrected build has not yet been used with the vehicle. Its passing fake captures are not physical telemetry.

The two original physical attempts failed before BF identity parsing because the frozen passive broker rejected an empty J2534 `START_OF_MESSAGE` record (`RxStatus=2`). Test Mode did not change that failure. This separate build admits that exact bounded indication without adding any data bytes or changing the BF/A8 requests, echo, identity, checksums, deadlines, or cleanup policy. Full metadata is retained for diagnosis.

The sealed original project and all 20 RK02 release-freeze files remain unchanged. This observer correction neither changes nor requalifies RK02 and grants no RAM takeover authorization.

## Evidence

- `reports/qualification_01/QUALIFICATION.json`: source/build/dependency seal, original preservation checks and independent clean-directory binary reproduction.
- `reports/qualification_01/BROKER_SOURCE_DIFF.patch`: exact production source change.
- `reports/local/prehardware/READ_ONLY_BACKEND_TESTS.json`: all 16 existing groups pass.
- `reports/local/prehardware/START_OF_MESSAGE_TESTS.json`: all 6 new groups pass, including 120 fake samples, exact 1 BF/120 A8 requests, marker evidence, terminal negative cases and successful child exit/cleanup.
- The initial new-test assertion failure and source are preserved separately; only CRLF-safe line counting changed after that test failure.

Broker: `integrations/prehardware/build/broker.exe`

SHA256: `beab515c4fa68cb9ed1bea2f54f40a43bcc01769f1bac01e0f26d69412ad8424`

## Current physical session

`C:\Dev\A2WC511R_ReadKernel\acquisitions\RK02_VEHICLE_02` contains the preserved second failing physical attempt using the original broker. G13 (ignition OFF) and G14 (OpenPort disconnected from vehicle) were subsequently confirmed. G15 is pending. RK02 has never run. The user now manages voltage verification and has instructed the assistant not to request voltage readings; do not substitute older measurements as current values or infer that G18 passed.

Use this copied `integrations/prehardware/capture.py` only at an explicitly authorized passive software stage after the required physical state has been established. Never overwrite an existing capture. The prior failure exit continues with the user's gates and OEM-return check; a software correction does not itself advance a physical gate.

Successful physical acceptance still requires the actual `2F12515306` BF response, the requested sample count, `PASS_CAPTURE_ONLY`, null capture/cleanup errors, and confirmed observer/broker exit. Keep G11 `PROCEED RK02` mandatory before the single RK02 invocation. A passive capture made in Test Mode must be labeled as such, not normal-mode evidence.

The provider documentation describes the ISO9141 start indication preceding the received message: https://quantexlab.de/en/develop/j2534/pt_readmsg.html
