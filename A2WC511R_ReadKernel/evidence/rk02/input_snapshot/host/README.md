# Fixed read-kernel host

The supported executable contains one pinned 1776-byte project kernel. It identifies ECU `2F12515306`, uploads that exact encrypted temporary RAM image to `FFFF3000`, requests entry `FFFF3004`, checks the exact kernel version, then reads every 512-byte block of the 1 MiB ROM twice in order. It has no arbitrary kernel, provider, address, opcode, voltage or flash operation interface. Python `HostState` and protocol functions are internal, transport-free test and replay oracles.

The default qualified host is `build/native_04/owned_read32.exe`, SHA256 `9ca8941960f64a1cb2931c18889e77fb8c3a0cd42840bff5422e05e1a363addc`. It loads only the pinned new-project fake DLL. Kernel replies in the fake environment come from the compiled SH-2E kernel executing SCI accesses in the simulator. OEM negotiation is explicitly modeled, with separate scoped stock producer/decrypt regressions; this does not assert complete physical OEM execution.

Run a new complete offline fixture from any working directory in PowerShell (the label must be new):

```powershell
& 'C:\Program Files\Python314\python.exe' -B 'C:\Dev\A2WC511R_ReadKernel\host\run.py' native_04 composite review_new --transport fragmented_status
```

This creates a private loopback server and an owned native process tree, retains source snapshots and actual native/provider/CPU evidence, and stops both at completion. A named `--fault` from the CLI choices creates a separate terminal-failure experiment. Completed evidence is listed in `HOST_QUALIFICATION.json` and `HOST_FAULTS.json`. `composite_01` and `random_01` used native03; `build/native_04/SOURCE_TRANSITION.json` proves the native03-to04 change was logging only. The final `composite_native04` run exercised the exact final host with complete timestamps and message metadata.

The offline finalizer loads no DLL and makes no transport calls:

```powershell
& 'C:\Program Files\Python314\python.exe' -B 'C:\Dev\A2WC511R_ReadKernel\host\finalize.py' --fake-build native_04 'C:\Dev\A2WC511R_ReadKernel\fake\runs\review_new'
```

It replays the complete native journal independently, checks every API step, transmitted frame and received fragment, reconstructs both full images, requires equality, and retains new read-only raw copies plus a hash-linked report. Source input hashes are calculated from the exact validated buffers, and inputs are rechecked before publication. It never overwrites or renames incomplete raw data into a current ECU image. Its output does not establish physical session association or current-ROM identity.

Pure offline regression commands are `test_contracts.py`, `test_stream.py`, and `test_finalize.py`, each with the same explicit Python executable and `-B`. The finalizer tests use the retained final native04 fixture. `report.py` regenerates hash-linked host/fault qualification from completed evidence without transport operations.

`build_physical.py native_04 physical_01` is a **compile-only** derivation, permitted only after the root `OFFLINE_SOFTWARE_CERTIFICATE.json` marks the exact kernel and tested fake host eligible. It never runs the produced executable or loads a provider. The separate target fixes the previously pinned `C:\Windows\SysWOW64\op20pt32.dll` provider, requires an explicit acquisition flag and the embedded certificate hash before loading it, and accepts no provider/address/kernel selection. It remains unexecuted and requires human physical qualification. An eventual capture uses `finalize.py --physical-build physical_01 CAPTURE_DIRECTORY`; that validates raw capture integrity and retains the physical-session/current-ROM limitation.

Transport framing, fragment/status bounds and fault cleanup are specified in `TRANSPORT_CONTRACT.md`. Failure causes immediate terminal exit without more J2534 calls. Successful provider close is not ECU reset. Actual OpenPort behavior, electrical conditions, timing, execution on silicon and confirmed OEM restoration remain physical gates. No physical provider has been loaded by these tests.
