# A2WC511R M0.7 review bundle

**ECU residency FAIL. No image is approved for flashing or physical testing.**
The supported deliverable is the offline stock-A8 host observation tool. ECU
research payloads are 100/148 bytes; 162 bytes of conditional executable savings
remain 0 proven owned bytes. No active-control feature is enabled.

Start with [the complete review](project/reports/local/m07_residency/M07_REVIEW.md),
[engineering gates](ENGINEERING_GATES.json), [exact fragment ownership](project/reports/local/m07_residency/OWNERSHIP_FRAGMENTS.json)
and [host tool usage](project/integrations/m07/README.md).

This is a source/evidence review snapshot of the existing C:\Dev workspace, not
a portable installer or a flashing procedure. Scripts intentionally retain
their reviewed workspace and installed-tool paths. Licensed GNUSH/RomRaider,
official IDA, Python/Java and local analysis-tool inputs are identified in logs,
profiles and manifests; installed proprietary tools are not redistributed here.
The simulator source/test snapshot is in simulator/. Use its README for scoped
semantic/ownership checks. Do not regenerate outputs into frozen original trees.

Current M0.6 comparison binaries and both old manifests are included. The full
M0 and 211-file M0.6 sets remain in their original verified workspace locations;
this package does not claim to duplicate every historical file. Frozen files
were verified before packaging. The current IDB copy contains comments only;
its mapped bytes retain the original four-byte-stamp variant, distinct from the
stock build input. All images are offline research artifacts.

The A0 exact-image acquisition procedure is withdrawn. ECUFlash Read/kernel
coverage, flash-exclusion and cleanup are unresolved; the audit offers only
conditional future ordering. No physical action is requested by this bundle.

SHA256SUMS.json covers every other file, including this notice. Verification is
read-only with verify_package.py; its manifest is integrity evidence, not an
ownership or physical-safety certificate.
