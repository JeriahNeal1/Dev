# ROM/RAM and patch validation gates

## Identity and baseline
Confirm CALID, ECU ID, actual ECM/engine/transmission hardware, baseline SHA-256, read provenance and definition inheritance. Compare IDB bytes with the intended input file and current vehicle calibration, accounting for known IDB patches. Keep OEM reference, as-read, working calibration and patched candidate separate. Do not erase existing tuning changes by reflashing a supposedly stock file merely to simplify research.

## ROM allocation
Use FF scans to discover candidate regions, then audit the complete linked footprint and all possible references, base-plus-offset readers, checksum coverage, branch reach, alignment, vectors and metadata. `0xE1000` is only a family-based candidate. Reject any section outside the proved interval. Absence of IDA-generated references is not ownership proof.

## RAM allocation
`0xFFFF7400` is not allocated. Establish an end-exclusive interval and examine ROM, interrupt, DMA, VBR, base-register and stack use, as well as reset/clear/test routines. Prove structure layout, padding and conditional-field sizes. Ensure logger addresses agree with actual linked layout and account for asynchronous access. Do not write probe patterns into an unproven live RAM region.

## Hook and ABI
For each enabled hook record original bytes, width/alignment, the source instruction or pointer, callee target, arguments/returns, integer/FPU register preservation, PR/stack, delay slots, continuation and execution frequency. Validate the emitted instructions against the exact SH-2E toolchain configuration. A similar CALID's header is a hypothesis source, not verification. No byte-patch endpoint exists in the included IDA bridge.

## Diagnostic-only stage
Host-test a simple observer that records candidate eligibility and rejection reasons but has no actuator outputs. Unknown, invalid, stale or inconsistent inputs must not imply eligibility. A constant gear code is not a heartbeat. Do not introduce physical thresholds until units, polarity and provenance are established. Explain observer cost and preserve OEM calls. Omit unrelated features at the source and hook-generation levels, not only by setting their gains to zero.

## Offline delivery
Produce a manifest with source commits, dirty diffs, compiler hash/flags, tool versions, input/output hashes, section map, expected patch regions, definition files and all checks. Apply/remove patches on copies; perform a full diff under an explicit checksum policy. Resolve post-build exceptions. Keep the manifest explicitly NONFLASHABLE while gates remain open.

## Installation
Installation approval is not included in this handoff. A later review must identify the exact binary hash, power/connection conditions and recovery prerequisites. Physical flashing remains operator-controlled. Do not disable fault/protection logic or request hazardous road tests to make a patch appear functional.
