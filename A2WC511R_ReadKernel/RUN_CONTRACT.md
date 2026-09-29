# Project-owned temporary RAM acquisition tool

Artifact class: TEMP_RAM_ACQUISITION_TOOL. Target SH-2E, SH7058, big endian. This tree is separate from MerpMod and must never produce or be flattened into a 1MiB flash candidate.

Preserve every prior sealed artifact, IDB, ECUFlash/OpenPort installation/registration and historical log. No physical provider loading, vehicle connection, physical upload or flash. No residency or active-control development. Existing installed ECUFlash exactness remains permanently FAIL.

Build a minimal independently inspected RAM kernel with explicit stack, private RAM/BSS, SR/interrupt, communication, watchdog and peripheral contracts. No inherited arbitrary RAM. Document every remaining clock/NMI/peripheral assumption. Use only documented SH7058 MMIO; no flash-controller stores, unlock, erase, program, commit, RAM-poke or arbitrary routine calls.

Fixed upload base FFFF3000 and stock loader entry FFFF3004 are the current supported contract. Root owns src/, linker/, tools/build.py and top-level manifests/validator. rom_inventory owns evidence/contracts and independent final binary review. simulator owns sim/ and execution/coverage tests. diaphora_setup owns host/, fake/, host/fake build/runner scripts and corresponding tests. Communicate before changing an interface. All old trees are read-only inputs.

Protocol proposal: BEEF framing/add8, version command01, raw command03 with BE32 address + BE16 length, exactly512 bytes, addresses ascending0..0FFE00 within1MiB. Version must identify this project uniquely. Reject all other opcodes/shapes; no CRC page substitution. A response should discriminate the requested block if changing response format provides stronger replay/out-of-order rejection; root/host/sim must agree before build.

Host pins exact ECU2F12515306, final kernel SHA, fixed upload/entry, custom identity, range and blocksize. No arbitrary kernel/address/opcode API. Enter reviewed BF/81/83/27/10/34/36/31 boot sequence, upload only compiled artifact, verify custom identity, read full1MiB twice, retain both raw outputs and hashes. Strict fake J2534 must execute actual uploaded instructions via sim, not synthesize kernel replies. Real provider remains unloaded.

Execution requirements: every instruction executed or justified unreachable; each admissible conditional edge; protocol states; every RAM write; all MMIO; exact stack bound; hard failure for unsupported instruction/MMIO, outside code/RAM, any flash write. Bounded suite first, deterministic seeded fuzz afterward. Fixtures: address-derived, all0/allFF pages, known FF-CRC collision, gap sentinels, random seeds and exact stock; two full reads each important fixture must agree byte-for-byte/hash.

Faults: beginning/middle/end upload timeout, start failure, bad identity, malformed/checksum requests, first/middle/final read failure, disconnect, duplicate/out-of-order packets, unknown opcode, host termination. Preserve incomplete results; never label current-ROM image or introduce generic retries/writes.

Exit is transport close -> ignition OFF and verified power loss -> ignition ON -> OEM reset/BF identity, not jumping into clobbered OEM RAM. Actual power-down interval, watchdog/electrical/ECU acceptance are PHYSICAL_REQUIRED. No human vehicle procedure is released unless software acquisition gates close.

One deterministic acquisition-tool validator checks pinned build/source/hash/entry/layout, static store/control closure, execution coverage, lossless fixtures, host allowlist, native fake integration and fault outcomes; PASS/CONDITIONAL/FAIL with hash-linked evidence. Preserve source/executed binary distinction. No new MerpMod image.
