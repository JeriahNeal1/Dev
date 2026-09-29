# Source index and acquisition notes

Reviewed for this handoff on 2026-09-25. These links are reference/navigation resources, not a claim that every page or program is bundled or installed. Supplied original artifacts remain the immediate authority for this project's observed state. Repository revisions are intentionally separated into observed and merely proposed pins.

The three pinned MerpMod/SharpTune README captures in `sources/upstream/` are available offline and match their upstream Git blob hashes exactly. See `CAPTURE_PROVENANCE.json`.

## MerpMod: the exact source generation

**MM-README** — Pinned source workflow, configurations, build phases and definition handling:
https://github.com/Merp/MerpMod/blob/8720d209df107a81fd171131cfba96d8cae1f118/README.md

The inspected README identifies Gratis as deprecated, Flash as its successor and Switch as alpha/untested. Default tables are not base maps. Use this source-generation workflow, not the old Release/Gratis compatibility list. The upstream current branch is not permission to overwrite a dirty local checkout.

**MM-PORT** — Pinned reverse-engineering/map instructions:
https://github.com/Merp/MerpMod/blob/8720d209df107a81fd171131cfba96d8cae1f118/README_PORTING.md

Its stated scope is Flash-build analysis and map creation. It is useful for locating functions/hooks, but does not document or certify every advanced-launch/Switch dependency. RAM allocation still requires indirect, VBR, DMA and stack analysis.

**MM-EH** — Feature coupling and generated target/config interfaces:
https://github.com/Merp/MerpMod/blob/8720d209df107a81fd171131cfba96d8cae1f118/MerpMod/EcuHacks.h

Read alongside Initializer.c, Metadata.c, Definition.c, RamVariables.h, RevLimiter.c, TimingHacks.c, FuelHacks.c and the actual HEW project. In particular, timing/POLF features can force switching features on.

**SHARPTUNE** — Observed binary-banner revision, resolved to an upstream commit:
https://github.com/Merp/SharpTune/tree/fcf9fdbafc2ba5bf04674fcad253fbda404aa171
https://github.com/Merp/SharpTune/blob/fcf9fdbafc2ba5bf04674fcad253fbda404aa171/README.md

The old starter proposed a different revision:
https://github.com/Merp/SharpTune/tree/ecabea89615132dac2de37c05f72adae16d966d1

Do not confuse these. Hash the actual executable and inspect local modifications before rebuilding or selecting a revision.

**SUBARUDEFS** — Starter's proposed definition-repository pin:
https://github.com/Merp/SubaruDefs/tree/9b2992eba8133fe5338b89aa77b22c1bb14d6507

The current host HEAD/branch is not established. Compare it with the local MerpMod/SharpTune conventions. Ordinary logger XML alone is not a complete inserted-patch editor definition.

**Related disassembly repository lead:**
https://github.com/Merp/SubaruDisassembly

Find any existing local `SubaruDisassembly/Maps` work too. Related CALIDs generate hypotheses, not proof of exact A2WC511R addresses. No complete copy of this repository is claimed in the archive.

## Subaru EJ255, USDM 2005 Outback XT, 5EAT and wiring

**SUBARU-STIS** — Official factory service information:
https://techinfo.subaru.com/stis/

Select the correct USDM model/year, 2.5L DOHC turbo and 5AT. Obtain engine fuel-injection/diagnostics, automatic transmission 5AT/5AT diagnostics, engine-control wiring, automatic-transmission wiring and ECM/TCM terminal/connector views. Record publication number, revision, market and pages. Use lawful local copies; diagram pages need visual inspection, not just text extraction.

**Owner resources:**
https://www.subaru.com/owners/vehicle-resources.html

Owner manuals help with selector/SportShift operation, but are not firmware maps or PCB schematics.

There is no single verified “EJ255 five-speed ECU source package” in this handoff. Engine ECM, transmission TCM, vehicle wiring and reverse-engineered calibration definitions are different layers. No exact ECM PCB schematic or complete OEM source code was obtained. Do not derive connector pinouts from a CPU hardware manual. Public 2005 Legacy manual mirrors may cover other markets/publication families; verify applicability rather than silently substituting them for USDM documentation.

## Renesas hardware and legacy tools

**RENESAS** — SH7058S product/hardware-manual landing page:
https://www.renesas.com/en/products/sh7058s

The official page identifies the SH-2E core. Verify the actual CPU marking and SH7058/SH7058S differences. The combined SH7059/SH7058S manual covers multiple parts; SH7059 memory sizes are not those of this 1MiB target.

**HEW** — Official IDE, archive downloads, macro/COM integration information:
https://www.renesas.com/en/software-tool/high-performance-embedded-workshop

This page lists version 4.09.01 resources and integration facilities. The user already has HEW; first inspect that installation rather than reinstalling it. TargetServer COM, Tcl/Tk and recorded macros are documented extension options, but exact installed API signatures must be verified before scripting them.

**GNUSH archive lead from MerpMod's README:**
https://gcc-renesas.com/

Record actual installed gcc/assembler/linker versions and flags. GNUSH bundle 13.01 is not automatically a gcc major-version number. IDA's SH4B selection is not a compiler target specification.

## RomRaider, ECU definitions, ECUFlash and OpenPort2

**RR-SOURCE** — Official project source:
https://github.com/RomRaider/RomRaider

Inspect the version-matched XML parser and logger code when diagnosing definition behavior.

**RR-FAQ / RR-DOWNLOAD** — Legacy project documentation:
https://www.romraider.com/RomRaider/FAQ
https://www.romraider.com/RomRaider/Download

These legacy endpoints were intermittent during research. The supplied XML and local version are the immediate authority; do not guess a replacement download. The original editor XML's inheritance is recorded in reports.

**Additional definition-repository lead:**
https://github.com/dschultzca/ECU-Definitions

Treat this as a discovery lead, not a pinned dependency of the user's MerpMod build. Confirm availability and applicable release before use.

**TACTRIX** — Official OpenPort2 and ECUFlash site:
https://www.tactrix.com/

Use its software/support/download links and the documentation/samples installed with the user's exact ECUFlash/OpenPort version. Inspect SSMK logcfg, serial MTS and J2534 documentation where relevant. Avoid unverified flashing binaries and cloned-cable firmware.

**Legacy OpenECU documentation lead:**
https://www.openecu.org/

Availability varies. It is not asserted to be a maintained replacement for current Tactrix instructions.

**INNOVATE** — ECB-1 product and manual resources:
https://www.innovatemotorsports.com/ecb-1-boost-ethanol-advanced-gauge-complete-kit.html

Verify exact controller/sensor installation and scaling before later engine tuning. The wideband-only primary-feedback idea is deferred.

## Forums requested by the user — supplemental leads

RomRaider's 32-bit Speed Density forum, linked by the MerpMod README:
https://www.romraider.com/forum/viewforum.php?f=37

General research:
https://www.romraider.com/forum/
https://forums.nasioc.com/forums/
https://www.legacygt.com/

Search by exact CALID, 5EAT, SH7058 and MerpMod, noting publication dates and hardware. Forum claims and other ROMs remain hypotheses until checked against this binary. Do not run arbitrary attachments or adopt an aggressive posted map as a baseline. These are requested research links, not manufacturer verification.

## IDA and integration APIs

**IDA-PY:** https://python.docs.hex-rays.com/
**IDA-UI:** https://python.docs.hex-rays.com/ida_kernwin/index.html
**IDA-UA:** https://python.docs.hex-rays.com/ida_ua/index.html
**IDA-BYTES:** https://python.docs.hex-rays.com/ida_bytes/index.html
**IDA-FUNCS:** https://python.docs.hex-rays.com/ida_funcs/index.html
**IDA-XREF:** https://python.docs.hex-rays.com/ida_xref/index.html
**IDA-LOADER:** https://python.docs.hex-rays.com/ida_loader/index.html
**IDA-SDK:** https://github.com/HexRaysSA/ida-sdk

These document execute_sync, code creation/decoding, byte reads and typed references. Stable web documentation is useful but not a guarantee about 9.4 Beta signatures. No broken `ida_kernwin.save_database()` call is used in this package.

**Optional existing third-party IDA MCP:**
https://github.com/mrexodia/ida-pro-mcp

Not installed or pinned here. Audit its requirements, exposed operations and permissions before choosing it. The included custom bridge is deliberately narrower and has no arbitrary IDAPython evaluation endpoint.

## Codex and MCP: official documentation

**OAI-MCP:** https://developers.openai.com/codex/mcp
Current redirect: https://learn.chatgpt.com/docs/extend/mcp?surface=cli

Covers local stdio servers, config and `codex mcp add`.

**OAI-WIN:** https://developers.openai.com/codex/windows
Current redirect: https://learn.chatgpt.com/docs/windows/windows-sandbox

Windows11 is recommended; fully updated Windows10 is described as best-effort, with 1809 or later needed for ConPTY. Verify the installed client, permissions and actual GUI capabilities.

**OAI-AGENTS:** https://developers.openai.com/codex/guides/agents-md
Current redirect: https://learn.chatgpt.com/docs/agent-configuration/agents-md

Use a concise root AGENTS.md and read detailed evidence on demand. Durable state files remain necessary even when continuing one chat.

**OAI-DOCS-MCP:** https://developers.openai.com/learn/docs-mcp
Optional official documentation-only endpoint: https://developers.openai.com/mcp

It supplies documentation, not local desktop or vehicle access. The package does not automatically register it.

**MCP-TRANSPORT:** https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
**MCP-LIFECYCLE:** https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle

The custom servers implement this dated protocol generation and negotiate selected older versions. They do not claim every future extension.

## Licensing and acquisition limits

Original user files are included for private continuity; no public redistribution license is asserted. MerpMod/SharpTune have their own GPL terms. Proprietary manuals, licenses and installers are not bundled. Complete third-party repositories were not downloaded into this container; use the pinned reference-fetch script or the existing local source after reconciliation. Never reset a dirty host checkout to a proposed pin merely to match a handoff note.


## v2 direct integrations — checked 2026-09-25
- Official IDA MCP: https://github.com/HexRaysSA/ida-mcp ; current requirements/commands summarized in docs/IDA_OFFICIAL_MCP.md. This supersedes the custom IDA server.
- Community alternative: https://github.com/mrexodia/ida-pro-mcp (alternative, not simultaneous or vendor-supported).
- Codex MCP registration: https://developers.openai.com/codex/mcp
- RomRaider native API reference: commit dafe0c36c1a68efadbeedb2825f3855463fdbc35; exact inspected source file URLs and method contract in docs/ROMRAIDER_API_CONTRACT.md. This is not a pin forcing the installed program to update.
- Java agent mechanism: https://docs.oracle.com/javase/8/docs/api/java/lang/instrument/package-summary.html . Our agent uses premain without class retransformation.

The latest official IDA README was fetched via the GitHub connector. RomRaider source was inspected through the same connector. Full current RR source/JAR execution was not available in the build container; the adapter is compiled against reflection and verified with explicit source-contract doubles. Local acceptance is not waived.
