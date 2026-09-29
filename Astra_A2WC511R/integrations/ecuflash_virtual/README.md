# Isolated installed ECUFlash Read harness

This tool executes the installed1.44.4870 sti05 Read against a separately named fake J2534 provider and an address-derived virtual1MiB ECU. It never loads a real provider. It is a reverse-engineering harness, not a physical acquisition command.

From `C:\Dev`, use a new, unused session name:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\run_read.py offline_read_001 --variant baseline
```

The command creates private registry/AppData state, starts the loopback ECU, launches the hash-pinned installed executable through the guard, verifies fourteen native entry points, redirects only those API calls, invokes Read, and saves the actual native raw output. It uses only Read, operation confirmation, unknown-ROM save-only setup and Raw ROM Save As UI actions. The host closes normally after the result. An existing session is never overwritten.

Accepted variants are `baseline`, `gaps_ff`, `gap_sentinels` and `crc_collision`. The last is an intentional **exactness failure**: successful ECUFlash UI is not the qualification result. `--fault` selects a named one-shot fault from `faults.py`. Batch commands are:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\batch_read.py repeat --prefix new_repeat
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\batch_read.py coverage --prefix new_coverage
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\batch_read.py faults --prefix new_fault
```

Capture-only independent checks require no running application:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\audit_read.py --self-test
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\audit_read.py --run C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\offline_read_001 --expected C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\offline_read_001\synthetic_flash.bin --saved C:\Dev\Astra_A2WC511R\work\ecuflash_dynamic\offline_read_001\ECUFLASH_READ_OUTPUT.bin
```

After any supplementary virtual checks finish, remove the closed session's private registry subtree and stop its exact owned RPC job:

```powershell
py -3.14 -B C:\Dev\Astra_A2WC511R\tools\ecuflash_dynamic\cleanup.py offline_read_001
```

Cleanup retains all evidence files. It refuses an active host and mismatched process identity; it never alters real PassThru registration. `--all-closed` applies the same checks to recorded virtual sessions. `session_private.json` contains a private environment/token and must not be printed or published. Registry backups may contain existing adapter/license information; their values are also private.

Native source/build inputs live here. `py -3.14 -B C:\Dev\Astra_A2WC511R\integrations\ecuflash_virtual\build.py` rebuilds the isolated x86 tools using the already installed MSVC, scoped Detours and nlohmann headers. Do not rebuild accepted inputs without a source change. GUI support packages are scoped to `C:\Dev\Tools\ecuflash-virtual-python`; no HCLI, decompiler or ML path is involved.

Normal generic fake-provider enumeration is not available in this installed ECUFlash build. The accepted fallback is a hash-pinned process-local cdecl-to-stdcall adapter; this limitation is visible in the qualification report. All real provider/device access is blocked by the guard. Unsupported APIs, protocol commands, memory ranges and response shapes fail explicitly. The virtual protocol state machine does not claim physical ECU or kernel execution.

See [qualification decision](../../reports/local/ecuflash_dynamic/READ_QUALIFICATION.md), [repair journal](../../reports/local/ecuflash_dynamic/SETUP_REPAIR_LOG.md) and [engineering gates](../../reports/local/ecuflash_dynamic/ENGINEERING_GATES.json). No vehicle connection is currently qualified.
