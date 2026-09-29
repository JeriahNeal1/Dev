# HISTORICAL V1 TEST REPORT — superseded for current integrations
See V2_TEST_STATUS.md. The custom IDA MCP tested here was removed in v2.

# Test report

**Environment:** Linux container with Python, not the user's Windows desktop.

Fifteen automated tests passed; see `reports/test_run.txt`. They cover nibble decoding, traversal/runtime path exclusions, synthetic ROM identity and diffs, CSV parsing/timing, header-only files, the actual latest logger XML, the actual 6,453-row packed log, project MCP handshakes, IDA adapter URL restrictions, default read-only tools, mock identity rejection, real loopback authentication/Origin checks, metadata-denied behavior, and an external MCP adapter request to a mocked IDA server.

Actual artifact checks include the latest XML's well-formedness and four exact ECU-scoped addresses, the two historical ROM reads' hashes/identity/old pointer values, the supplied definition inheritance, and numerical packed-gear comparisons. Generated JSON reports are included. The active XML copy was not reformatted.

**Not tested:** genuine IDA Pro 9.4 Beta execution, long UI-thread/autoanalysis behavior, Windows PowerShell execution, the user's Codex client, HEW/GNUSH builds, SharpTune patch round trips, Tactrix communication, ECU flashing or vehicle behavior. Mock API tests are not a claim of live plugin compatibility. Run the documented host smoke test before relying on the integration.

Neither MCP exposes flashing or live vehicle-control tools. No generated firmware image is claimed flash-ready.
