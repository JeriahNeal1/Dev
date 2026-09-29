# v3 preparation tests

Executed in this preparation environment, not inside the user's Windows programs:

- **64 Python unittest cases passed.** Includes original file/log/XML tests plus exact uploaded ROM comparison, source-state audit expectations, real newline-JSON metadata protocol against a fake server, model/effort rejection, no thread/turn operations, backed-up idempotent setup, initial package acceptance / immutable evidence with resumable working-file edits, staged command/artifact failures, release-envelope checks, and launch/resume argument construction.
- **66,566 C host assertions passed**, compiled with GCC C99 -Wall -Wextra -Werror -pedantic -O2. This is the pure observation scaffold, NOT an ECU firmware or SH build.
- **22 Java model/transaction assertions passed** against test substitutes.
- **11 actual Java-agent transport/Swing assertions passed** against a test application.
- Java agent rebuilt with --release 8; all Python modules compiled for syntax.

Read raw reports: v3_python_tests.txt, v3_diagnostic_host_tests.txt, v3_java_build.txt, v3_java_tests.txt, v3_agent_transport_tests.txt.

## Not executed here
Actual Windows PowerShell execution; GNUSH Windows compiler; IDA9.4 Beta/official MCP; installed RomRaider models; authenticated user Codex catalog/Ultra entitlement; ECU checksum program; any vehicle connection or test. The PowerShell files were reviewed but could not be runtime-tested here. Host preflight is supplied specifically to detect local failures before the main model task. Actual local CLI parser checks use --help without starting a model task.

## No new ECU firmware
No A2WC511R ECU firmware was compiled, patched or flashed by this archive preparation. Existing uploaded Gratis_Debug objects are the wrong target. Successful tests of tooling and the host observer do not complete the source port.

Passing release_check.py only checks identity/diff/evidence linkage; it is not a checksum implementation, memory proof or physical safety certificate.
