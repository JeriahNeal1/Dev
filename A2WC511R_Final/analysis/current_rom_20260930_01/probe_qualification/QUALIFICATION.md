# Transition-only probe qualification

PASS_OFFLINE_QUALIFIED_TRANSITION_PROBE_ONLY

The same x86 executable intended for the single gated experiment passed 65 native in-process fake-provider cases. Two independent clean builds produced identical bytes. Independent source, build and test review passed; the parent launch controls passed 12 negative gates, one positive gate and two bookkeeping/child-wait cases without starting any process or provider.

Executable SHA256: `1573fa0046a6c1ee6b0ca9d3b0873ce0b3536fb2cdc6888304fb1e7b1ff3513e`

Qualification SHA256: `96d64646cdc9fa620d45afc7f2fc80e9c5b90a146a54b40c79324de85b9ee4d3`

Branch: `rk03/transition-probe`; commit `6d2a076cc8cf90f023211c1e71ad5571e7b0ee8d`. The original `rk03/explicit-serial-init` branch remains at `00664cbe83c35eee0faffd4161c76fc70888984f`.

The only request sequence is BF, 81, 83 00. The five explicit settings are read back and checked before the broad filter or first request. Filter mask, pattern and the observed nonnull flow object are four zero bytes, matching archived ECUFlash arguments. All API input/output records, configuration/filter state, message metadata and API-bracketing QPC times are journaled. Success and failure both attempt filter stop, disconnect and close; no retries occur.

The qualification includes status 16 replay with the original recorded SOM/BF/SOM/C1/empty-read records, the full expected C3 response, configuration failures and mismatches, filter/identity/reply failures, malformed messages and cleanup errors. Physical elapsed timing is not simulated.

No provider was loaded and no physical probe was run during qualification. Only the human preparation gates may now begin. The exact final authorization remains **PROCEED RK03 TRANSITION PROBE**. A full acquisition is excluded.
