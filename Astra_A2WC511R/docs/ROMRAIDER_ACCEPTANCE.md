# Required local acceptance — do not mistake mocks for the real program

## A. Offline identity and reads
Disconnect vehicle I/O for editor integration acceptance. Preserve the normal logger/hardware setup. Discover actual working Java/JAR version, hash, options and profile; launch the same editor with the per-process agent on a disposable copy of a known ROM. Confirm CALID, full buffer size/hash, table count, axes, existing definition path/document hash and any faulty/unsupported tables. Save the report.

Compare every exported native table/axis against a read of the same native model; additionally visually inspect representative scalar, 1D, 2D, 3D, integer, float, signed/masked cells, flipped/swapped maps, shared axes and named switches. Current-scale selection is part of the fingerprint. Record real coverage instead of asserting every table is editable.

## B. Reversible preview
Choose a harmless disposable numeric table cell; do not select an actual safety/diagnostic switch for a demonstration. Request one representable adjacent value, snapshot before, preview, and assert the entire ROM-buffer SHA is unchanged after preview. Check the returned achievable value and exact byte diff against native manual editing on a separate disposable copy. Test multi-cell transactions and stored axes with the same controls. Unsupported representations remain read-only until this agrees.

Check strict old-value and scale/axis/hash guards by changing a value manually between capture and preview. Verify rejection without other cells changing. Verify out-of-range/quantization failure rolls back earlier changes in the same batch. Verify source file hashes remain unchanged. Preview is not expected to trigger checksums or native disk saves.

## C. Approved persistent editor change
Only now restart with -EnableEdits. Capture a fresh session snapshot and make a new small disposable proposal. Confirm the local changeset dialog applies one batch and updates the editor display. Cancel another batch and verify no change. Verify a preview cannot commit after its deadline or after a model change. Check aliases/compare displays/undo behavior on the real release; any inconsistency blocks further use until fixed.

Export the in-memory buffer and reopen it offline in the editor; read all tables again and compare. It remains NOT_FLASH_READY. Separately test native Save As checksum/edit-stamp behavior on another disposable copy and classify every additional modified byte. Do not infer checksum support from the export filename.

## D. Historical and logger evidence
Open baseline and current copies and capture each with clear labels. Compare the full models. Ingest an existing CSV with an explicit snapshot association; do not attest ECU match without evidence. Test a known monotonic map's axis bindings, linear unit conversions, interpolation weights, filters, delay direction and timestamp-reset rejection. Confirm every plotted timeline row can be traced to raw CSV bytes and table snapshot hashes. Count excluded samples and avoid treating sequential samples as independent experiments.

## E. Gate for the real project
Record which table types and installed runtime passed, errors, exact software hashes and unresolved constraints in reports/ROMRAIDER_LOCAL_ACCEPTANCE.md. Before any later calibration change, require table-specific evidence/objective/bounds and preserve unsupported/unobserved cells. No valid data means no automatic optimization. Before vehicle installation, retain the existing independent exact-ROM, memory/hook, checksum and manual flashing gates.
