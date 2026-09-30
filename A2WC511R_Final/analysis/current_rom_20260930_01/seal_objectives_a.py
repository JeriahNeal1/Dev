"""Validate completed offline ingest outputs and preserve the A-A4 milestone."""
from pathlib import Path
import collections
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "rk02_vehicle_03_transition"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def pin(path):
    p = Path(path)
    b = p.read_bytes()
    return {"path": str(p), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


checks = []


def verify(row, base=None):
    p = Path(row["path"])
    if not p.is_absolute():
        p = base / p
    actual = pin(p)
    assert actual["sha256"].lower() == row["sha256"].lower(), str(p)
    if "bytes" in row:
        assert actual["bytes"] == row["bytes"], str(p)
    checks.append(actual)


classification = read(ROOT / "rom_classification/CLASSIFICATION_SUMMARY.json")
identity = read(ROOT / "rom_classification/IDENTITY.json")
checksum = read(ROOT / "rom_classification/CHECKSUMS.json")
code = read(ROOT / "rom_classification/EXECUTABLE_COMPARISON.json")
ranges = read(ROOT / "rom_classification/CHANGED_RANGES.json")
history = read(ROOT / "historical_comparison/HISTORICAL_COMPARISON.json")
session = read(ROOT / "ecuflash_current_session/SESSION_EVIDENCE.json")
assert identity["identity_and_size_valid"] and identity["current_size"] == 1048576
assert identity["calid_at_2000"] == "A2WC511R" and identity["ecuid_at_CDAD8"] == "2F12515306"
assert checksum["geometry_equal"] and checksum["all_14_records_valid"] and checksum["first_record_enabled"]
assert classification["changed_bytes"] == 1856 and classification["changed_ranges"] == 517
assert code["executable_code_identical"] and code["all_bytes_outside_exact_known_data_changes_identical"]
assert not code["changed_executable_functions"]
assert classification["unclassified_changed_bytes"] == 0
current = Path(identity["current"]["path"]).read_bytes()
stock = Path(identity["stock"]["path"]).read_bytes()
assert hashlib.sha256(stock).hexdigest() == "22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218"
actual_changed = {i for i in range(len(current)) if current[i] != stock[i]}
classified = set()
counts = collections.Counter()
for row in ranges["ranges"]:
    lo, hi = row["start"], row["end_exclusive"]
    assert current[lo:hi].hex() == row["current_hex"] and stock[lo:hi].hex() == row["stock_hex"]
    assert all(i in actual_changed for i in range(lo, hi))
    owned = set()
    for seg in row["segments"]:
        a, b = seg["start"], seg["end_exclusive"]
        assert lo <= a < b <= hi
        span = set(range(a, b))
        assert not owned.intersection(span)
        owned.update(span)
        counts[seg["classification"]] += b-a
    assert owned == set(range(lo, hi))
    assert not classified.intersection(owned)
    classified.update(owned)
assert classified == actual_changed
for key, count in classification["classification_byte_counts"].items():
    assert counts[key] == count
for name in ("current", "source", "stock"):
    verify(identity[name])
for row in classification["evidence"]:
    verify(row)
for folder, manifest in (("rom_classification", "OUTPUT_MANIFEST.json"), ("historical_comparison", "MANIFEST.json"), ("ecuflash_current_session", "EVIDENCE_MANIFEST.json")):
    obj = read(ROOT / folder / manifest)
    for row in obj.get("outputs", obj.get("files", [])):
        verify(row, ROOT / folder)
    checks.append(pin(ROOT / folder / manifest))
verify(session["current_session"]["source"])
assert session["saved_image_association"]["source_image"]["sha256"] == identity["current"]["sha256"]
assert session["saved_image_association"]["save_events"]
before = read(OLD / "FAILED_EVIDENCE_BEFORE.json")
failed = Path(before["root"])
assert {str(p.relative_to(failed)) for p in failed.rglob("*") if p.is_file()} == {str(Path(x["path"])) for x in before["files"]}
for row in before["files"]:
    verify(row, failed)
for row in read(OLD / "ANALYSIS_BEFORE_DEVELOPMENT_MANIFEST.json")["files"]:
    verify(row)
for row in read(Path(r"C:\Dev\A2WC511R_ReadKernel\evidence\rk02\RELEASE_FREEZE.json"))["files"]:
    verify(row)

now = datetime.now(timezone.utc).isoformat()
status = {
    "schema": 1, "created_utc": now, "designation": "CURRENT_PHYSICAL_CAPTURE",
    "CURRENT_ROM_SHA256": identity["current"]["sha256"], "CURRENT_ROM_SIZE": identity["current_size"],
    "CURRENT_CAL_ID": identity["calid_at_2000"], "CURRENT_ECU_ID": identity["ecuid_at_CDAD8"],
    "CURRENT_SUBARU_CHECKSUM": "PASS", "EXECUTABLE_BYTES_IDENTICAL_TO_STOCK": True,
    "EXECUTABLE_FUNCTIONS_CHANGED": [], "UNKNOWN_CHANGED_RANGES": [],
    "EXACT_STOCK_BASELINE": identity["stock"], "TOTAL_DIFFERING_BYTES": len(actual_changed),
    "EXACT_DIFFERING_RANGES": ranges["ranges"], "CLASSIFICATION_BYTE_COUNTS": dict(counts),
    "ROMRAIDER_DEFINITION_OVERLAP": pin(ROOT / "rom_classification/CHANGED_OBJECTS.json"),
    "EXECUTABLE_DIFFERENCE_COUNT": 0, "FUNCTION_CONTAINED_DATA_CHANGES": code["function_contained_data_changes"],
    "CLOSEST_HISTORICAL_TUNE": {"path": r"C:\Users\Jeriah Neal\Desktop\AdjustedBaseTimingANDNOCLOLD.bin", "byte_identical": True, "differing_bytes": 0},
    "ACQUISITION_ASSOCIATION": session["saved_image_association"],
    "final_statement": "CURRENT PHYSICAL ECU IMAGE: calibration differs from stock; executable code identical to stock",
    "interpretation_limits": code["limits"],
    "physical_probe_result": "NOT_RUN",
    "factory_stock": False,
}
with (ROOT / "CURRENT_ROM_STATUS.json").open("x", encoding="utf-8") as f:
    json.dump(status, f, indent=2)
    f.write("\n")
text = f"""# Current physical ECU ROM status

CURRENT_ROM_SHA256 = {status['CURRENT_ROM_SHA256']}
CURRENT_ROM_SIZE = 1048576 bytes (1 MiB)
CURRENT_CAL_ID = A2WC511R (0x2000; also present at 0xC0000)
CURRENT_ECU_ID = 2F12515306 (0xCDAD8)
CURRENT_SUBARU_CHECKSUM = PASS
EXECUTABLE_BYTES_IDENTICAL_TO_STOCK = true
EXECUTABLE_FUNCTIONS_CHANGED = []
UNKNOWN_CHANGED_RANGES = []

The original `C:\\Dev\\SubaruRoms\\current.bin` is unchanged. Its read-only preserved copy is `current.preserved.bin`; initial filesystem timestamps and hashes are in `INGEST_MANIFEST.json`. The latest successful ECUFlash log records this exact saved path, 1 MiB size and 2026-09-30 00:29:13.123 UTC save time, matching the file timestamp. This direct acquisition is the authoritative current-image input.

The exact stock baseline is `C:\\Dev\\SubaruRoms\\OEM\\A2WC511R.bin`, SHA256 `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`. Complete comparison finds **1,856 differing bytes in 517 contiguous ranges**. Every changed byte has an exact definition/object or checksum/stamp classification; proximity to a table was not used.

| Classification | Changed bytes |
|---|---:|
| Calibration table | {counts['table']} |
| Axis | {counts['axis']} |
| Scalar | {counts['scalar']} |
| Checksum correction | {counts['checksum']} |
| RomRaider metadata stamp | {counts['metadata']} |
| Executable code / padding / unknown | 0 / 0 / 0 |

`CURRENT_ROM_STATUS.json` and `rom_classification/CHANGED_RANGES.json` contain all exact ranges and old/new bytes. `CHANGED_OBJECTS.json` records the 53 changed native definition objects. Both retained instruction inventories match; the broader Diaphora export covers 68,739 unique instruction words in 1,147 functions. These inventories are partial static discovery, but every changed byte outside them is also accounted for as exact data. All bytes outside the identified data changes match stock.

One function extent, `sub_151DC`, contains the changed float at 0x155FC (90.0 to 65.0), named Max Wastegate Duty Limit Post-Compensation. Only byte 0x155FD changes. The unchanged MOVA at 0x15474 and FMOV.S load at 0x15478 establish that this is embedded calibration data, not a changed instruction. No new Diaphora structural matching was needed. Unchanged instructions do not imply unchanged calibration behavior.

The closest historical tune is an **exact byte match**: `C:\\Users\\Jeriah Neal\\Desktop\\AdjustedBaseTimingANDNOCLOLD.bin`. It also matches all 16 retained historical page CRC values. Historical files provide provenance only; they do not override current.bin. Exact comparisons against all 18 historical inventory images are preserved in `historical_comparison/HISTORICAL_COMPARISON.json`.

The latest successful ECUFlash read is the primary physical comparator. `ecuflash_current_session/SESSION_COMPARISON.md` compares it with RK02_VEHICLE_03 and the August success. It records API 04.04, DLL 1.02.4870, firmware 1.17.4877, serial TAPoN7at, successful seed/key labels, DUAL 1.07 upload/start, ROM reading and save. Its application log does not expose raw 81/83 bytes, exact bus timing, provider defaults or that session's actual Test Mode observation. The saved file association is strong; the log alone does not prove every saved byte was transmitted from the ECU.

The current file provides strong evidence against changed executable instructions as the explanation for RK02's failure. Electrical cadence, provider behavior and receive/filter/queue behavior remain unresolved; no individual configuration change is claimed causal. The original transition analysis remains sealed, and this report is a supplement.

**CURRENT PHYSICAL ECU IMAGE: calibration differs from stock; executable code identical to stock.**

This is not factory stock. Physical transition-probe status at this milestone: NOT RUN.
"""
with (ROOT / "CURRENT_ROM_STATUS.md").open("x", encoding="utf-8") as f:
    f.write(text)
milestone = {"schema": 1, "created_utc": now, "status": "OBJECTIVES_A_THROUGH_A4_COMPLETE", "checks": checks,
             "status_report": pin(ROOT / "CURRENT_ROM_STATUS.json"), "status_markdown": pin(ROOT / "CURRENT_ROM_STATUS.md"),
             "probe_review_contract": pin(ROOT / "PROBE_REVIEW_CONTRACT.json"), "probe_build_allowed": True,
             "physical_authorization_received": False, "physical_invocations": 0, "full_acquisition_allowed": False}
with (ROOT / "OBJECTIVES_A_COMPLETE.json").open("x", encoding="utf-8") as f:
    json.dump(milestone, f, indent=2)
    f.write("\n")
state_path = Path(r"C:\Dev\A2WC511R_Final\state\CURRENT.json")
state = read(state_path)
state.update(phase="RK03_TRANSITION_PROBE_DEVELOPMENT_AFTER_COMPLETED_CURRENT_ROM_INGEST", updated_utc=now,
             current_vehicle_ROM="CURRENT_PHYSICAL_CAPTURE_VALIDATED_ECUFLASH_SAVED_IMAGE", current_rom_executable_identical_to_stock=True,
             current_rom_status_report=str(ROOT / "CURRENT_ROM_STATUS.json"), objectives_a_complete=str(ROOT / "OBJECTIVES_A_COMPLETE.json"),
             probe_build_allowed=True, probe_physical_authorization_received=False, probe_physical_invocations=0,
             next_action="Build and offline-qualify three-request transition probe; no physical operation until one-action gates and exact final authorization")
state_path.write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status":milestone["status"],"checks":len(checks),"classified_bytes":len(classified),"classification":dict(counts),"physical_probe":"NOT_RUN"}))
