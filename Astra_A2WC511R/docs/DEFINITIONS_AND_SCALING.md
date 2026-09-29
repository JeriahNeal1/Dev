# Findings in the provided definitions

Programmatic inspection of the archived `ecu_defs.xml` finds this inheritance chain:

```text
A2WC511R -> A2WC510C -> 32BITBASE
```

A2WC511R supplies identity metadata and no direct table overrides. A2WC510C has 297 direct table entries; 32BITBASE has 807. These are document counts, not a claim that every base entry is applicable or corresponds to a separate physical table. Preserve inheritance rather than copying another CALID's entire ROM. See `reports/definition_inheritance.json`.

The target metadata says USDM, model year 05, Subaru Outback XT, AT, SH7058, `sti05` flash method, 1024kb, ECU ID `2F12515306`, and internal ID address `2000`. The `sti05` method name does not make the car an STI or authorize another vehicle's firmware.

The exact-ECUID logger entry E38 maps `FF4FC0` to **Throttle Plate Opening Angle (4-byte)**, described as actual plate opening, with:

```text
percent = raw float / 0.84
```

Consequently, a direct raw-float comparison against 60 is not automatically a 60-percent threshold. Confirm behavior and units before activation logic. This specific definition finding is stronger than speculation that this entry might be a target-throttle signal; it still needs operational cross-checking.

The MAP entries use `FF4F30` as a native float in **mmHg absolute**, including conversions such as `psi absolute = x * 0.01933677`. Relative-sea-level entries subtract 760mmHg, which is not the same as subtracting local barometric pressure in Redmond. Do not compare absolute, local-relative and sea-level-relative channels interchangeably. Exact entries are in `reports/exact_ecuid_scaling_checks.json`.

The narrow scan found no exact-ECUID extended entry for `FF51D8` or `FF51E8`. That does not invalidate prior reverse engineering; it means this scan alone does not establish their direct units. Cross-check their producers and standard SSM speed/RPM signals.

Custom validity channels remain raw uint8. Logger XML uses shortened 24-bit SSM addresses such as `FF4C8D`; IDA and C pointers use physical addresses such as `FFFF4C8D`. Do not apply that shortening rule blindly to other architectures/protocols.
