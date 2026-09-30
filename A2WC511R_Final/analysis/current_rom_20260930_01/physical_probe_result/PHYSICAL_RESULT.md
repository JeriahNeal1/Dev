# Single physical transition probe

RK03_TRANSITION_PHYSICAL = PASS

The qualified probe ran exactly once and sent only BF, 81, and 83 00. ECU BF identity was 2F12515306. The complete response to 83 00 was `80 F0 10 07 C3 00 00 FF 00 FF 00 48`, with valid length and checksum. All five provider-reported configuration values matched their requests. All 22 API calls returned status zero.

Reproducing the reviewed ECUFlash-style explicit serial initialization and broad filtering restored successful progression through 83 00 in this physical session. The experiment does not isolate which individual change caused the improvement.

PassThruStopMsgFilter, PassThruDisconnect and PassThruClose all returned zero. The process exited zero, and a subsequent process/module scan found no competing diagnostic clients or provider users. No seed/key, programming-admission, RAM upload, kernel start, ROM read or flash command was transmitted. There is no retry and no full acquisition in this run.

The raw session files and authorization/gate snapshot are preserved as read-only copies with source and copy hashes in PHYSICAL_RESULT.json. Transport cleanup is confirmed; vehicle power-down and OEM-return verification remain pending human gates. The current-ROM report remains unchanged: calibration differs from stock; executable code is byte-identical to stock.
