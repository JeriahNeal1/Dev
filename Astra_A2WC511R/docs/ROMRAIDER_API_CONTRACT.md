# Native editor API contract and implementation
Source examined at RomRaider commit **dafe0c36c1a68efadbeedb2825f3855463fdbc35**. This is a source reference, not a claim that the installed JAR equals that revision. Inspect and hash the user's JAR/version before deployment. The historical executable version in the existing inventory must be reconciled locally.

## Actual APIs used
| Layer | Native interface | Purpose |
|---|---|---|
| Editor manager | ECUEditorManager.getECUEditorWithoutCreation() | Attach to existing editor, never create one implicitly |
| Editor | ECUEditor.getImages() | Enumerate open ROM objects |
| ROM | getTables(), getBinary(), getRomIDString(), getDefinitionPath(), getDocument(), getFaultyTables() | Native resolved model and identity |
| Table | getData(), getCurrentScale(), getScales(), getStorageAddress(), getStorageType(), getRamOffset(), getEndian(), isLocked() and metadata getters | No duplicate ECU-definition parser |
| 3D | get3dData(), getXAxis(), getYAxis(), getSwapXY(), getFlipX/Y(), getSkipCells() | Correct logical orientation and address metadata |
| 2D | getAxis() | Explicit axis capture |
| Cell | getRealValue(), getBinValue(), getOriginalValue(), getIndexInTable(), getBitMask() | Exact native values |
| Writes | DataCell.setRealValue(String), DataCell.setBinValue(double) | Native encoding, inverse scales, integer quantization, permissions and shared-cell updates |
| Rollback/refresh | getBinary() buffer restore, updateBinValueFromMemory(), calcCellRanges(), view.drawTable() | Restore model and visible values |
| Presets | Table.presetManager read-only reflection, getPresets(), isPresetActive() | Capture native named states; apply as explicit native raw-cell changes |

No endpoint lets a caller provide a class, method, arbitrary memory address, Java expression, shell command or Python expression for execution. Internal reflection is limited by implemented operations, not exported as a generic tool. getData is NOT used as the 3D matrix: the source's get3dData returns [x][y].

## Important source behaviors
DataCell.setRealValue uses the current scale's inverse or approximation and rounds integer storage. setBinValue can reject locked/checksum-special values, enforce user level and clamp numeric range. The adapter verifies the achieved value against the explicit tolerance, then verifies the resulting full binary SHA rather than assuming a setter call succeeded.

DataCell.saveBinValueInFile modifies the ROM's in-memory byte buffer and refreshes shared cells; its name is not evidence of an OS-level save. The native code supports special layouts, masks, floating-point and other storage formats. The adapter relies on that model and reports resulting byte ranges; it does not blindly write floats or assume row-major file storage.

Rom.saveFile is not a pure buffer getter: in the inspected source it can modify a Subaru edit stamp and checksum state. We deliberately do not invoke it. `rr_export_model` emits the existing buffer under a SHA256 `.NOT_FLASH_READY.bin` name, explicitly without checksum recomputation. Any editor Save As / ECUFlash correction must be audited separately.

## Hashes, transactions and trust
All model operations run on the Swing event-dispatch thread. A single HTTP worker serializes requests. A preview checks expected full-ROM SHA and model/scaling fingerprint, applies explicit native cell changes, captures quantized results and byte diffs, then restores original bytes in finally. Multi-cell failure rolls back the whole buffer. If rollback itself fails, stop the session and restore the saved disposable copy—never report success.

Each commit requires launch-time enablement and one local YES/NO dialog. It checks freshness before and after the dialog and refuses after the request deadline. It checks the final SHA against the cached preview. Preview IDs expire after ten minutes. An uncertain timeout is a reason to inspect state, not blindly retry. The in-memory model may have native save/compare/revert semantics beyond these getters, which must be checked on the real program during acceptance.

Read snapshots report unsupported tables rather than pretending complete coverage. Transactional writes require the complete model to be refreshable; no silent skipping during rollback. A missing method on a different installed version is an explicit compatibility gap. The deployment code does not automatically download or replace RomRaider.

## Transport and payload limits
Java 8 class-file target; no third-party runtime dependencies. Launcher can use a known-working full Java 8+ runtime. HTTP server binds random port on 127.0.0.1 only, checks exact Host, rejects Origin, requires per-session random bearer token and accepts only POST /rpc. Config/token beneath ACL-restricted .runtime. No network proxy/redirect use by client. Maximum request 4MiB, result/file 64MiB, changeset 65,536 cells. These are transport bounds, not approved calibration sizes.

Python stdio MCP implements initialize, ping, tools/list and tools/call with structured schemas. Tools and record definitions are in integrations/romraider_mcp/server.py and core.py. No live Logger/serial ownership or flash protocol is included.

## Source references
- https://github.com/RomRaider/RomRaider/blob/dafe0c36c1a68efadbeedb2825f3855463fdbc35/src/main/java/com/romraider/maps/Table.java
- https://github.com/RomRaider/RomRaider/blob/dafe0c36c1a68efadbeedb2825f3855463fdbc35/src/main/java/com/romraider/maps/DataCell.java
- https://github.com/RomRaider/RomRaider/blob/dafe0c36c1a68efadbeedb2825f3855463fdbc35/src/main/java/com/romraider/maps/Rom.java
- https://github.com/RomRaider/RomRaider/blob/dafe0c36c1a68efadbeedb2825f3855463fdbc35/src/main/java/com/romraider/maps/Table3D.java
- https://github.com/RomRaider/RomRaider/blob/dafe0c36c1a68efadbeedb2825f3855463fdbc35/src/main/java/com/romraider/maps/PresetManager.java
- https://github.com/RomRaider/RomRaider/blob/dafe0c36c1a68efadbeedb2825f3855463fdbc35/src/main/java/com/romraider/editor/ecu/ECUEditorManager.java
