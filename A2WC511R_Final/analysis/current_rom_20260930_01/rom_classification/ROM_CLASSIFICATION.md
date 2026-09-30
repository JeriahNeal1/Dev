# Current ROM byte classification

`current.preserved.bin` is a valid 1 MiB A2WC511R / 2F12515306 image, SHA256 `bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2`. Its original `C:\Dev\SubaruRoms\current.bin` and the preserved copy have identical bytes. Designate the supplied image **CURRENT_PHYSICAL_CAPTURE**, not factory stock. Acquisition provenance/exactness is assessed separately; this analysis does not turn an ECUFlash file into an independently verified double read.

Against verified stock SHA256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`, it differs at exactly **1,856 bytes in 517 contiguous ranges**. Every changed byte is classified using exact native RomRaider object extents, checksum descriptors, or the documented editor stamp. No proximity-to-table attribution was used.

| Classification | Changed bytes |
|---|---:|
| Table data | 1,765 |
| Axis data | 62 |
| Scalars | 21 |
| Checksum correction | 4 |
| Editor metadata | 4 |
| Executable instructions | 0 |
| Padding | 0 |
| Unknown | 0 |

The changes touch 53 native objects, including the checksum object. `CHANGED_OBJECTS.json` identifies each parent table/axis by its unique native key and records exact extent, storage type, scaling expression, changed cell indices, original/current raw values, and object hashes. `CHANGED_RANGES.json` contains complete original/current bytes for all 517 ranges; `CHANGED_BYTES.csv` assigns all 1,856 bytes individually.

## Executable code

**Executable code is identical to stock in the supplied image.** The retained IDA export's 63,588 instruction words were checked against actual stock bytes, then compared with the capture. The broader retained Diaphora stock inventory covers 1,147 functions and 68,739 unique instruction addresses; every corresponding instruction word is unchanged. All retained stock function-chunk hashes also match the actual stock file before comparison. Independently, the exhaustive whole-image difference contains only exact known data/checksum/stamp bytes, closing the otherwise incomplete static-inventory coverage for this comparison.

`changed_executable_functions` is empty. One function's enclosing byte extent changes: stock `sub_151DC` (named `sWgdc_loc` in the earlier IDA export), `[0x151DC,0x15748)`. The sole changed byte is `0x155FD`, inside the defined float scalar `[0x155FC,0x15600)` **Max Wastegate Duty Limit Post-Compensation**, changed from **90.0 to 65.0**. The unchanged instruction at `0x15474` (`C761`) computes `0x155FC` with MOVA; the unchanged instruction at `0x15478` (`F608`) loads that address with `FMOV.S @R0,FR6`. This is embedded calibration data, not a changed opcode. It is explicitly recorded under `function_contained_data_changes` rather than a code-change list.

Unchanged opcodes do not imply unchanged engine behavior: the calibration changes include boost/wastegate, fueling/transitions, ignition/knock adaptation, AVCS, and MAF data. This report classifies bytes; it does not approve the tune.

Fresh Diaphora structural matching is unnecessary because there are no changed executable instructions or unknown changed regions. The existing export is reused read-only, with its SHA256 checked against the retained export index. The inventory remains seeded static discovery, not a claim of complete firmware reachability or general executable ownership.

## Identity, checksums and preservation

CALID at `0x2000` is A2WC511R, ECU ID at `0xCDAD8` is 2F12515306, and reset words match stock (`00000AAC FFFFBFA0` repeated). All 14 checksum records validate with unchanged descriptor geometry. The first record remains enabled; the other 13 disabled placeholders match stock. The changed correction word is `[0xFFB88,0xFFB8C)`. The edit stamp `[0xFFC4C,0xFFC50)` changes from `FFFFFFFF` to `26081816`; an editor stamp is not evidence of acquisition freshness.

`PRESERVED_HOOKS.json` checks the previously reviewed MAF, WGDC, rev-limit, reset and other hook words and selected M0/M0.6/M0.7 review spans directly against stock. All are unchanged. The full byte diff additionally establishes that no changes exist in the stock KWP/session/boot routines: the only changed byte below `0xC0000` is the separately proven calibration literal at `0x155FD`.

The current source, preserved copy and stock were hashed again after analysis. No ROM, definition, existing IDA/Diaphora database, qualified build, or failed acquisition evidence was changed. Only this new analysis directory was written.

## Reproduction and artifacts

Run `py -3.14 -B classify_current.py` from this directory. It stops before classification if size, current hash, stock hash, CALID, or ECU ID differs. It performs no hardware operation and invokes no editor or IDA process.

- `CLASSIFICATION_SUMMARY.json`: result, counts, scope, input hashes.
- `IDENTITY.json`: source/copy/baseline identities and reset words.
- `CHANGED_RANGES.json`, `CHANGED_BYTES.csv`: complete byte difference and classification.
- `CHANGED_OBJECTS.json`: all changed data objects/cells, including axes and embedded scalar.
- `EXECUTABLE_COMPARISON.json`: instruction and function comparison, coverage limits, literal proof.
- `CHECKSUMS.json`: all stored and computed checksum records plus metadata.
- `PRESERVED_HOOKS.json`: reviewed hook words and stock-span equality.
- `OUTPUT_MANIFEST.json`: final output hashes.

During development, the first run's raw-XML check incorrectly compared the native snapshot's serialized-DOM hash to the raw XML file hash. Inspection of `RomAccess.java` showed these are distinct representations. The check now uses the retained raw-XML inheritance hash; the native snapshot remains separately hash-bound to the reviewed exact extents. A final review also classified the explicit `::axis` native keys as axes, alongside `::x`/`::y`. These corrections affect analysis bookkeeping only. Final classification passes with zero unclassified bytes.
