# v2 — 2026-09-25

Removed the custom IDA MCP implementation and its registration/startup instructions. Use official Hex-Rays IDA MCP with one active GUI database connection. The optional one-shot checkpoint script is independent of any server.

Added custom native RomRaider Java agent, source plus Java-8-target JAR, and 13-tool stdio MCP. Features: native tables/axes/scales/presets, immutable snapshots, raw/real historical differences, explicit-ROM logger association, analysis-side interpolation timelines, declared sensor delay and filters, weighted cell evidence, bounded formula/named-preset proposals, reversible quantization/byte-diff previews, stale/expiry checks, locally approved batch editor transactions, and NOT_FLASH_READY buffer export.

Revised persistent Codex instructions, local Windows launchers, migration guide and configuration generator. Added real-host acceptance gates, native source contract, security limits and calibration-versus-firmware explanation. Original definitions/evidence remain unchanged; no new ECU calibration or executable firmware was applied.

Full replacement archive: extract into a fresh v2 folder. Do not overwrite newer local state or leave the old server behind by merging blindly.
