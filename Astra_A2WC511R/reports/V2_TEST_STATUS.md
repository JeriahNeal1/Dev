# v2 tests and validation status
Prepared 2026-09-25.

## Executed in this build container
- **34 Python unittest cases passed**, including the actual full six-channel-test logger XML, the original 6,453-row packed gear CSV, immutable history integrity, explicit log associations, 2D interpolation weights, descending axes, unit/delay/reset guards, bounded calculations, unchanged-cell behavior and MCP schemas/handshakes.
- **22 Java model/transaction assertions passed**: source-contract test doubles for catalog/axes/native-setter behavior, multi-cell rollback, quantization/clamp rejection, stale hashes, 3D coordinates, editor-only commit, default edit blocking, local cancellation, approval deadline and JSON handling. These doubles are not the installed RomRaider binary.
- **11 Java-agent HTTP/EDT assertions passed** against a compiled test-double host: real agent startup, authenticated loopback roundtrip, model capture, reversible native-like preview, unchanged buffer, token/Origin/Host rejection, disabled-commit refusal and process/token cleanup. The host is explicitly not real RomRaider.
- Own Java agent compiled successfully targeting class-file major **52 (Java 8)**. Compiler emitted only obsolete target-8 warnings. The deployed JAR contains no test fixtures or upstream RomRaider class replacements.
- Synthetic offline workflow produced immutable snapshots, a historical difference, a 5-row timeline with weighted cell evidence, a constrained proposal and an HTML report. It is labelled synthetic, not vehicle tuning evidence.
- **138 original evidence files** verified byte-for-byte against the v1 archive, without alteration.

## Not executed here
- Actual Windows 10 PowerShell launcher/ACL behavior and the installed Java/RomRaider application.
- Official Hex-Rays MCP installation or connection to the real IDA Pro 9.4 Beta/idalib installation.
- Real RomRaider table-type coverage, GUI refresh/compare/undo behavior, or source-defined encoding parity on the user's JAR.
- ECU checksum completion, flash, live RAM writes, hardware I/O, engine or transmission tests. None were attempted.

See docs/ROMRAIDER_ACCEPTANCE.md. Passing source-contract doubles does not waive the real-host acceptance gate. No file is certified flash-ready.

## Build provenance
- Native RomRaider API source examined: dafe0c36c1a68efadbeedb2825f3855463fdbc35. Installed JAR revision remains to be checked; no forced update.
- Agent SHA256: `c1a63f9a0b0290934178fb7d0b0658de44c88e201b29199022d9d103546d46d6`
- Raw reports: v2_python_tests.txt, v2_java_tests.txt, v2_java_build.txt, v2_agent_transport_tests.txt.
- V1 TEST_REPORT.md and test_run.txt are historical; their custom IDA bridge was removed.

## Reproduce
Run Python unittest discovery in the workspace. Rebuild Java with tools/Build-RomRaiderBridge.ps1 -JdkBin <actual JDK bin> -RunModelTests. Then run tests/agent_transport_smoke.py with JAVA_EXE pointing to that java.exe. The transport script compiles against no installed RomRaider and does not touch a vehicle. See the documented local acceptance procedure afterward.
