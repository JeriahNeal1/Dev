# v1 -> v2 migration

## Files and registrations
Extract v2 into a fresh folder. Do not merge it over v1: extraction does not delete removed files and could leave the old IDA server executable. Preserve v1 as an archive and merge only newer operator-created state/work into v2 after comparing dates, hashes and content.

Removed: the entire custom `integrations/ida` implementation, its server configuration, custom IDA bridge tests and startup instructions. A standalone IDA checkpoint export was moved to `tools/ida_checkpoint_export.py`; it is not a server. Added: official IDA instructions and the RomRaider native model/history integration.

If the old bridge is running, save IDA through its editor and close/restart IDA to stop it. Inspect `codex mcp list`. Remove only the legacy custom server entry that points to the old `integrations/ida` path. Its previous name was `a2wc511r_ida`; use `codex mcp remove a2wc511r_ida` only after verifying this is the actual obsolete entry. Keep a config backup and preserve all unrelated entries. No automatic registry/global config cleanup is supplied.

Repoint or register the project MCP and RomRaider MCP using the snippets generated inside the new folder. Resolve duplicate entry names deliberately. The official IDA plugin is configured separately and must not be duplicated by another generic entry.

## Existing work
No IDB, tuning folder, ROM file, installed JAR, logger profile or source repository should be overwritten. The original evidence in this package is byte-identical to v1. The v2 source tools and current instructions supersede v1's integration instructions; original old console transcripts remain historical evidence, not active directions.

If Codex has already begun local firmware work, retain its newer CURRENT_STATE/NEXT_ACTIONS/SESSION_LOG and reconcile them with these integration changes. Do not mark the pending TCU log missing merely because it is absent from this archive—search the authorized local tuning folder.

## RR deployment order
Bootstrap/test -> inspect exact installed Java/JAR -> offline disposable ROM copy -> read-only agent -> catalog coverage and round-trip previews -> bounded commits with local confirmation -> immutable snapshots and log attribution -> separately reviewed checksum/export/installation. See ROMRAIDER_ACCEPTANCE.md.
