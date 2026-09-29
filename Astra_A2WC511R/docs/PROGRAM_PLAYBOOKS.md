# v3 precedence note

Current host authorization and run order are in `../AGENTS.md`, `../state/RUN_CONTRACT.md` and `CLI_SETUP.md`. Actual uploaded source/binary identities superseding older unknowns are in `DEV_SNAPSHOT_AUDIT.md`. Keep the technical details below, but do not reimpose historical per-action host permission requests or stop after the first milestone. Physical actions remain human-controlled.

---

# Program operating procedures

## IDA Pro 9.4 Beta
Continue the existing IDB. Check CALID at 0x2000, ECU ID at 0xCDAD8, database/input paths and ROM hash. Prefer the existing official Hex-Rays MCP structured tools or tools/ida_checkpoint_export.py; the old custom server is removed. A delayed JSR executes its next instruction before the callee. PC-relative MOV.L literals are aligned to four bytes. Forced decoding remains a hypothesis even when it prints a plausible opcode.

Names, comments, code heads and functions are distinct. Inspect flags and overlapping chunks before creating a function. Persist a verified entry instruction, let analysis finish, then compare exact bounds. No indiscriminate undefining or whole-ROM conversion. Xrefs include data references; preserve their type and distinguish literal loads from calls. Do not assume a decompiler is available for this processor or change the architecture/endian preset silently. Save metadata manually in the editor. [IDA-PY, IDA-UA, RENESAS.]

## RomRaider Logger
Back up the configured XML, then select a separate copy of the latest full validity-test definition. Restart/reconnect as necessary and verify ECU ID `2F12515306` and exact channel names. All custom entries use uint8, `expr=x`, ECU target1 and SSM addresses `FFxxxx`. They are existing RAM reads, not a reason to flash.

The Tactrix/J2534 interface and the Innovate serial COM port are different resources; do not assume the previously reported COM3 belongs to ECU logging. Only one Tactrix client should own the interface. Use the normal logger GUI for connection/recording; no undocumented live API is asserted here. Preserve CSVs unchanged and record selector/event timing separately. Do not edit data to correct a hypothesis. The offline MCP analyzes files after recording.

## RomRaider ECU Editor
Use the per-process native Java model bridge and RomRaider MCP described in ROMRAIDER_WORKBENCH.md, after ROMRAIDER_ACCEPTANCE.md passes locally. Read/edit through native Table/DataCell interfaces, capture immutable snapshots and require exact reviewed batch transactions; do not use screenshots or per-cell pastes as the primary interface. Native Save/checksum changes are separate from model edits.

Editor XMLs define ROM tables; logger XMLs define runtime reads. Preserve the exact target's base inheritance and scalings. Edit copies only. Retain axes, dimensions, units and quantization. A valid `[Table3D]` clipboard format does not validate the numbers in a historical tune. Newly inserted MerpMod tables need appropriate generated editor definitions; the inspected MerpMod README does not promise RomRaider editor support for them. [RR-SOURCE, SUBARUDEFS, MM-README.]

## ECUFlash and Tactrix OpenPort2
A file open in an editor is not necessarily the image on the vehicle. Record read provenance and hashes. Inventory driver, USB interface, serial identity and relevant bitness on the host. Do not open concurrent ECUFlash/RomRaider/custom J2534 clients.

No supplied MCP exposes Write, Test Write, erase or recovery. Any later installation needs an exact-hash review and operator-controlled physical procedure. Preserve both sides of checksum corrections; do not automatically correct a baseline warning and describe it as unchanged. The historical ChecksumFix error must be investigated, not bypassed. [TACTRIX.]

## HEW and GNUSH
Keep the installed working environment. A newer e2 studio is not automatically a drop-in replacement. Capture the exact compiler/assembler/linker versions and flags referenced by the HEW project. Do not target SH-4 merely because IDA used SH4B. Separate compiler, linker, metadata, patch and definition phase success. Verify CALID in every phase and isolate output directories before cleaning them.

The official HEW page documents custom build steps, recorded command macros and a TargetServer COM extension. These are useful possible native automation routes. This package does not invent a COM ProgID or undocumented method signature. Use the supplied read-only `tools/Inspect-HewAutomation.ps1` to discover candidate COM registrations in both registry views. Inspect actual type libraries/manuals or record a build-only macro, then validate its contents before automation. Prefer reproducible compiler/batch commands once recovered. Never automate debugger download or vehicle actions as part of a build macro. [HEW, MM-README.]

## SharpTune and MSBuild
Match the executable banner/hash to the actual source, then inspect its CLI parser. The upstream README describes its editor as alpha; use the known offline map/patch commands on copies rather than broad GUI edits. Back up `.SharpTune` settings before changing the definition repository. Read the local .csproj for framework/toolset and resource requirements instead of converting to a modern framework merely to suppress errors. MSBuild builds the C# tool; GNUSH builds SuperH firmware. [SHARPTUNE.]

## Innovate ECB-1
This controller is not the focus of the status test. Keep present wiring and OEM sensors. Do not alter calibrations while collecting TCU data. Before later engine tuning, verify firmware, COM assignments, ground offsets, sensor installation and AFR/lambda conversion against the manufacturer's actual manual. A chosen AFR display factor is not proof of tank fuel composition. [INNOVATE.]

## GUI fallback
Use desktop interaction only for operations without an established API/file interface or for manual review. Probe elevated-window/UAC visibility instead of assuming it. No public RDP/VNC/port forwarding is needed. Keep offline development and physical vehicle operations separate; the driver must not operate the laptop while moving.
