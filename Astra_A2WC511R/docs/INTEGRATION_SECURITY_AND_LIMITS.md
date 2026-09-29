# v3 precedence note

Current host authorization and run order are in `../AGENTS.md`, `../state/RUN_CONTRACT.md` and `CLI_SETUP.md`. Actual uploaded source/binary identities superseding older unknowns are in `DEV_SNAPSHOT_AUDIT.md`. Keep the technical details below, but do not reimpose historical per-action host permission requests or stop after the first milestone. Physical actions remain human-controlled.

---

# Integration trust and limits — v2

Official IDA MCP is a separately installed vendor tool, not our custom restricted server. This archive cannot enforce its tool permissions. Review its real capabilities, select the existing GUI database, keep saved backups, and constrain tasks under AGENTS.md. Do not run multiple IDA MCPs or expose remote listeners. Metadata-only work is not permission for debugger execution or firmware-byte changes.

The custom RomRaider integration has a fixed operation set: read model, capture history, propose, reversible preview, locally confirmed editor commit, and content-addressed NOT_FLASH_READY export. No arbitrary Java/Python eval, reflection endpoint, process launch, ECU/TCU hardware I/O, J2534, actuator operation, flash, erase or live RAM write is provided. The launcher is explicitly per-process and does not replace the installed editor JAR. The project analysis MCP remains read-only for its artifact inputs.

The Java bridge binds 127.0.0.1 on a random port with a per-session random bearer token, exact Host check, Origin rejection and POST-only dispatch. The client disables redirects/proxies. Launcher ACLs restrict .runtime to the current Windows user/SYSTEM. A same-user malicious process can still access that user's resources; this is not a sandbox protecting against a compromised desktop. Never publish the token, connection file or proprietary ROM/license data.

Reversible preview temporarily exercises the native mutable editor model, then restores full bytes and refreshes data. It must be tested on disposable offline copies first. Persistent commit is disabled unless the launcher receives -EnableEdits, and still requires a local changeset confirmation. Complete old-ROM/model/cell fingerprints, expiry, post-approval checks and final-byte equality guard against stale decisions. Do not auto-retry a commit when a timeout makes the result uncertain. Snapshot/history hashes are integrity/identity aids, not proof a calibration is appropriate or flashed.

Native encoded values can have quantization, aliasing, masks or coupled representations. Respect native locking/user levels; do not bypass them through raw writes. Unsupported models block writes. General formulas are bounded arithmetic proposals, not a vehicle performance optimizer. Sensor alignment/interpolation is explicitly assumed and logged; default normal-operation logs do not prove all fault behaviors.

Physical vehicle interfaces remain owned by the normal user-controlled logger/flasher, one client at a time. No remote/deployed service is needed. Existing desktop privileges are not extended automatically. All current integration tests and their mock-versus-real scope are listed in reports/V2_TEST_STATUS.md.
