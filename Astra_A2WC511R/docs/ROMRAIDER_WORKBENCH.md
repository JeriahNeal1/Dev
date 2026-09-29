# RomRaider native model workbench

## Purpose and scope
The goal is direct, reproducible access to the **same table objects and values that the ECU Editor uses**, rather than a hard-coded MAF/timing list, screenshot OCR or clipboard typing. Native definition inheritance/scalings remain RomRaider's responsibility. The integration does not pretend its own XML parser can reproduce every editor feature.

There are two layers:
```
Codex --stdio MCP--> Python history/evidence/proposals
                         |
                   authenticated loopback
                         |
Java agent inside existing RomRaider --Swing EDT--> Rom / Table / DataCell
```
The Java agent does not transform bytecode, replace the installed JAR, expose arbitrary reflection calls, connect J2534 or add an ECU flash endpoint. It uses the inspected native model methods. This is custom candidate tooling, not an official RomRaider-supported API. Local acceptance is required for the installed release.

## Catalog and coverage
Read all tables and stored axes accessible in the loaded native model. Capture table name/key, dimensions, storage address/index, endian, signedness, bitmask, native scales/inverse, units, raw and real values, original/revert raw values, native preset states and locking. Axes use explicit keys such as `Base Timing::x`, `Base Timing::y`, or `MAF Sensor Scaling::axis`. Coordinates are always `row=y,column=x`, zero-based; native 3D arrays use [x][y] and are transposed explicitly for this interface.

Supported design scope: native numeric scalars/vectors/2D/3D tables, numeric stored axes, switch/preset definitions and bitmasked numeric cells through native setters. Static text/axis labels are readable but not ROM-backed editable values. Checksum Fix and locked tables are read-only. There is no guarantee that every unusual future table class, unpopulated table, inherited schema or beta behavior is supported without adaptation; errors are reported as coverage gaps, not silently discarded. A transactional preview refuses incomplete native model coverage until resolved, to avoid unsafe rollback assumptions. Newly added MerpMod tables are accessible only when the editor has correct matching definitions.

A vector without a defined numeric axis can be compared/edited by explicit cell but cannot be mapped automatically to a driving timeline. An enum has named states, not a meaningful interpolated optimum.

## Workflow, with durable history
1. `rr_status`: identify the open ROM and session. Open historical baseline/current/candidate copies in the normal editor. Do not assume `rom_1` persists after restarting.
2. `rr_capture_snapshot`: archive a complete native model snapshot labeled, for example, `verified baseline`, `current file - ECU match unverified`, or `candidate before change`. Records include full ROM-buffer SHA256, model fingerprint, loaded definition-document fingerprint, active scales and timestamps. The original ROM bytes can separately be exported by `rr_export_model` under a content-addressed NOT_FLASH_READY name.
3. `rr_compare_snapshots`: compare all matching tables or one chosen key. Raw and real deltas are reported; axis/shape/scaling changes are flagged. Equal row numbers with different axes do not represent equal operating points. No automatic resampling hides that difference.
4. `rr_ingest_log`: archive an unchanged CSV and associate it explicitly with a snapshot. Choose `user_attested_applied_rom` only with operator evidence that the snapshot matches the vehicle during that run; otherwise choose `unverified_candidate_association`. File dates, CALID and filenames alone are inadequate. Record flash/readback hashes and time windows separately when known.
5. `rr_table_timeline`: bind exact CSV columns and units to table axes, choose filters and metric, declare time units and sensor lag, and state evidence for the active table. It produces a full timeline CSV, weighted cell statistics and an offline HTML report. A growing logger CSV can be ingested repeatedly as immutable versions; this is file-based observation, not a live logger connection or guaranteed sample-by-sample stream.
6. `rr_calculate_proposal` or `rr_preset_proposal`: create an explicit bounded candidate changeset. No editor changes yet. Unselected/rejected cells remain unchanged. Save the formula, input constants, evidence identifiers, constraints and rationale.
7. `rr_preview_proposal`: execute native scaling/quantization reversibly, calculate exact modified byte ranges and achieved values, and restore the entire editor ROM buffer before returning. This temporarily mutates the model internally, so it is not a pure read operation. Use offline disposable copies during acceptance. Review quantization/clamp failures, linked/overlapping regions and checksum status.
8. `rr_commit_preview`: after -EnableEdits and local confirmation, reapply exactly the previewed changeset to the open editor. Old ROM/model hashes, cell values and session must still match. A preview expires, a timed-out approval cannot apply late, and a repeated successful preview ID is idempotent within the session. No disk save or ECU write occurs. Review the table visually and capture the after snapshot.
9. Saving/checksum handling is a separate reviewed operation. The native Rom.saveFile path can change checksum/edit-stamp bytes. Our export only copies the current buffer, marks it NOT_FLASH_READY, and never claims checksums are fixed. Preserve a before/after-native-save diff and manifest before any later installation.

## Formula calculations are not automatic optimum discovery
The safe arithmetic evaluator accepts finite numeric constants/variables, + - * / ** (bounded), abs/min/max/sqrt/log/exp. No Python eval, attributes, imports, comprehensions or arbitrary functions. Standard variables are `old`, `row`, `column`, and when an evidence overlay is supplied, `count`, `mean`, `std`, `weight`, `metric_min`, `metric_max`. Constants cannot override reserved evidence fields.

Constraints are explicit: minimum, maximum, maximum absolute per-cell change, minimum sample count and allowed native quantization tolerance. There is no universal meaningful constraint for every ECU parameter; the user/tuner/model evidence must supply the correct one for each task. Out-of-bounds results are rejected rather than silently clamped into plausibility.

Synthetic example (not a tuning recommendation): with `old=10`, a supplied `correction=1.02`, formula `old*correction` requests 10.2. Whether that should be applied depends on the table's meaning, units, evidence and native representability. A switch/preset must use a named state instead. Never use one blanket percent change across all maps.

For engine work, instrumentation calibration may admit a well-defined relationship; ignition optimization needs torque/knock/thermal evidence, boost feedback needs its dynamic plant and operating context, and limits/diagnostics encode requirements rather than a power-maximization target. The correct result can be "leave unchanged; evidence missing".

## Logger association, filtering and interpretation
Bindings require `column`, exact axis `unit`, explicit linear conversion `factor` and `offset`. A positive `metric_delay_ms` aligns the metric at t+delay with the table operating point at t; alignment outside max gap is rejected. This compensates only a declared measured/modelled delay, not an invented universal sensor delay. Split logs across timestamp resets. Do not infer seconds versus milliseconds.

Table interpolation is analysis-side linear/bilinear with explicit adjacent-cell weights, numeric monotonic ascending/descending axes and no default extrapolation. This is useful for coverage and traceability but is NOT evidence the firmware selected that table, used that interpolation method, used unfiltered axes or applied no compensations. For example, base timing is not necessarily final commanded spark. Manual/automatic, alternate maps, warmup, closed/open-loop, corrections and failsafe selectors must be accounted for in the evidence.

Weighted sample counts are not independent dyno experiments. Closely spaced samples are correlated. Filter transients, suspect sensors and unsuitable operating conditions before interpreting errors. No filtering should silently erase inconvenient knock or misfire evidence; excluded counts/reasons remain in the report.

## Checkpoints
History is under `work/rr_history`: snapshots, unchanged CSV bytes, log association records, overlays with timeline reports, proposals, comparisons and events. Each JSON record is content-addressed and integrity-checked. Native bridge events are recorded separately under the editor work directory. Copy/save reports before clearing console output. Session/model IDs are transient; content hashes and the files persist.

See ROMRAIDER_API_CONTRACT.md for precise API and ROMRAIDER_ACCEPTANCE.md for the real-host test gate.

## Offline demonstration
Run `.venv\Scripts\python.exe tools\romraider_demo.py --out work\synthetic_demo` to generate a synthetic history, table comparison, logger timeline, HTML report and one bounded proposal. It never contacts an editor and contains no recommended vehicle values. The included reports/synthetic_timeline_demo.html shows the same report format.
