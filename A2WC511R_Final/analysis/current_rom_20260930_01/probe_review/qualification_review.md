# Offline probe qualification review

All 65 cases passed in the first qualification execution against the same PE intended for separately gated physical use. This is a software result for BF → 81 → 83 only, not physical authorization or proof that the vehicle failure is fixed.

The executable SHA256 is `1573fa0046a6c1ee6b0ca9d3b0873ce0b3536fb2cdc6888304fb1e7b1ff3513e`; both clean builds match byte for byte. The report SHA256 is `5c0c017258750b607b660c0f0e0ef8eb033428f020df1e5ee59d07863be82f0c`. Post-run audit verified 223 source, tool, build and output pins without mismatch, including all 195 fixture outputs.

I authored the qualification runner and README, independently reviewed the implementer's C++ core, and inspected results without rerunning the executable. The implementation agent executed the runner once. Root and oem_transition independently reviewed my runner; their final reports and the launcher qualification remain separate.

The suite verifies the three fixed requests and maximum three transmissions, five SET calls followed immediately by provider-returned GET_CONFIG, and the exact broad filter with a nonnull four-zero flow object. Each configuration failure prevents TX. Returned config count/pointer/parameter/value corruption is logged and rejected. Wrong BF, malformed 81 and malformed 83 stop at their respective stages.

The recorded failure replay compares all five original RX records, including SOM/BF/SOM/C1/status16 metadata and bytes. It remains terminal at status16 with no retry. Positive fragmented/status-indicated fixtures require the complete expected C3 frame. Error-return data, excessive count and oversized DataSize are retained in bounded journal records before rejection.

Cleanup proceeds in order after every allocated-resource failure. Individual and combined cleanup errors still allow remaining attempts and force overall failure. The journal-failure fixture deliberately omits one filter return record but preserves resource ownership, all three cleanup calls, zero TX and a failed terminal result. QPC source review confirms intent logging and output formatting are outside the API duration.

No blocking finding remains for this offline scope. Actual provider timing/defaults, ECU response, physical state and failure causation remain unproven. The tests do not qualify uploads, full ROM acquisition, reset or physical cleanup. No provider or probe executable was run by this review agent.

`qualification_review.json` contains requirement-level results and exact source, runner, README, executable and test-report pins. No further runner/source change was made after the successful run.
