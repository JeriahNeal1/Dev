# Native fake-J2534 raw read supplement

This separate prototype closes the direct-RPC bypass in the earlier virtual supplement: a real32-bit C++ process loads the same pinned fake J2534 DLL used by the isolated ECUFlash session and calls its standard`__stdcall` exports. The DLL then uses its authenticated loopback connection to the virtual ECU. The client does not implement a physical-capable transport or accept a provider path.

Build and run against a fresh, already-completed isolated collision session:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\build_native_raw_supplement.py
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\run_native_raw_supplement.py SESSION_NAME
```

The runner accepts only a simple session name beneath the fixed project work root. It requires a normally closed installed ECUFlash Read, saved1MiB output, a closed fake provider, and live virtual`KERNEL` state. It verifies the installed executable, prior API attachment, original isolation records, exact native client binary, and native fake/guard/launcher hashes. It snapshots the original trace and supporting files before starting a separate client through the existing isolation launcher. Its guard and launcher logs have separate paths; the installed Read records remain unchanged.

The native executable accepts no transport, file, address, opcode or baud arguments. A validated session environment determines one exact fake-DLL path. Before loading it, the executable takes a file handle that denies write/delete sharing and verifies hardcoded SHA256`58be9aaad8e004eb5bd04a600e53394a1139752f1b698ca1832124dbbb4d5cc0`. The handle remains open through use. `LoadLibraryExW` uses that absolute path and restricted dependency search. The file hashing uses the documented Windows CNG SHA256 API; hash-object automatic allocation is supported on Windows7 and later. [Microsoft BCryptCreateHash documentation](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptcreatehash).

Only eight exports are resolved: Open, Connect, StartMsgFilter, WriteMsgs, ReadMsgs, StopMsgFilter, Disconnect and Close. The fixed wire sequence is version01, then command03 for2048 ascending512-byte blocks over`[0,0x100000)`. It uses protocol3, flags`0200`, baud62500 and a`BE EF` pass filter. It exposes no CRC shortcut, upload, reset, security, voltage, periodic or flash-control operation. The version response must equal`OpenECU Subaru SH7058 DUAL  Kernel V1.07` including its terminalNUL. Every response has exact size, length, opcode, checksum and message-boundary checks. Message structs have canaries on both sides, and every native call records the x86 ESP value before and after it.

The first API, frame, count, canary or stack failure terminates the process without further J2534 calls. This may leave the virtual provider's logical channel open after failure; success closes the filter, channel and provider. Neither case claims an ECU reset.

The current Python runner creates the isolation launcher suspended, assigns it to a private Windows Job Object with kill-on-close and no breakaway, then resumes it. At the 120-second bound it terminates the entire owned job and verifies that no active job processes remain before reporting failure. This closes a reviewer-found defect in the earlier runner, whose `subprocess.run` timeout could stop only the launcher and leave its native child running. The successful capture used the earlier runner and remains preserved with its exact executed source; it did not time out. The timeout fix was checked separately using a sleeping parent and a heartbeat child, without loading a provider or making RPC calls. [Microsoft Job Object limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information).

The completed`qualification_collision_native` demonstration passed:

- 4104 actual native calls, with all 4104 stack-pointer comparisons equal.
- 2048 strict raw-read replies reconstruct 1MiB, SHA256 `c777be6d9e0e3de2a1abc263a26c91ec2e1f421d09acb6fbe09c3ca81021180b`.
- All 37 bytes hidden by the native Read CRC substitution were recovered.
- Native TX/RX bytes match the appended fake-provider records, and the original 4753-event trace prefix remains unchanged.
- 27 native offline framing, metadata, version, opcode, address-order, path-name and canary controls pass.
- Three separate native processes reject a foreign provider path, a provider-path argument, and a changed fake-DLL hash before provider loading or RPC.

The original trace snapshot hash is`e222e1909a08b4b0a55ba565d08c2ef84ccb6bdeaa86f8b3fff9ef2641727738`. The saved native ECUFlash image remains SHA256`4019b72614f525025acbc3cb34d2aa731711373b90f329ec006f60cc5800dc0d`. New evidence is under`reports/local/ecuflash_dynamic/native_raw_supplement/qualification_collision_native/`. The earlier direct-RPC demonstration and its seal are preserved.

The separate `timeout_hardening_01/RESULT.json` records three active job members before timeout cleanup, zero afterward, and a stopped child heartbeat. A normal-exit control also leaves zero active members. `SOURCE_PROVENANCE.json` and `MANIFEST.json` at the native supplement report root distinguish the archived successful-run sources from the current runner and its offline hardening evidence. The completed session has been cleaned up; replay requires a new completed isolated virtual session created by the existing session tooling.

This proves the selected fake DLL's native ABI path and the fixed raw-read protocol against the model. It does not change installed ECUFlash Read's exactness, execute the kernel on silicon, qualify OpenPort/J2534 physical behavior, prove hardware timing, or close cleanup/reset gates.

One ordinary build defect was repaired: inline-assembly statements expanded inside a macro needed explicit braces. The failing log is retained as`work/ecuflash_dynamic_native_raw_build/build_failed_01.log`; the same `/W4 /WX` x86 build then passed without warnings. No existing provider, guard, launcher, installed executable or licensed binary was modified.
