"""Seal this run after independent offline continuation review. No provider use."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess

A = Path(__file__).resolve().parent
R = Path(r"C:\Dev\A2WC511R_RK03_PostTransitionOffline")
C = R / "continuation"
OUT = A / "run_completion_20260930_01"
pins = {}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def need(ok, why):
    if not ok: raise RuntimeError(why)
def pin(p):
    p = Path(p).resolve()
    data = p.read_bytes()
    row = {"path": str(p), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if str(p) in pins: need(pins[str(p)] == row, "Changed during seal: " + str(p))
    pins[str(p)] = row
    return row
def verify(v):
    if isinstance(v, dict):
        if isinstance(v.get("path"), str) and isinstance(v.get("sha256"), str):
            actual = pin(v["path"])
            need(actual["sha256"] == v["sha256"].lower(), "Hash mismatch: " + v["path"])
            for key in ("bytes", "size"):
                if isinstance(v.get(key), int): need(actual["bytes"] == v[key], "Size mismatch: " + v["path"])
        for x in v.values(): verify(x)
    elif isinstance(v, list):
        for x in v: verify(x)
def git(*args):
    return subprocess.check_output(["git", "-C", str(R), *args], text=True).strip()
def write(p, obj):
    with p.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")

parser = argparse.ArgumentParser()
parser.add_argument("--native-review", type=Path, required=True)
args = parser.parse_args()
native = read(args.native_review)
need(native["status"].startswith("PASS"), "Native independent review incomplete")
need(not native.get("open_findings", []) and not native.get("errors", []), "Open native review finding")
verify(native)
pin(args.native_review)
if args.native_review.with_suffix(".md").exists(): pin(args.native_review.with_suffix(".md"))
root_review = A / "offline_continuation_review/ROOT_REVIEW.json"
need(read(root_review)["status"] == "PASS_ROOT_INDEPENDENT_RUNNER_REVIEW", "Root review incomplete")
verify(read(root_review)); pin(root_review)

latest = read(C / "reports/LATEST_QUALIFICATION.json")
need(latest["status"] == "PASS", "Continuation tests failed")
verify(latest)
test_path = Path(latest["report"]["path"])
tests = read(test_path)
need(tests["status"] == "PASS" and tests["passed_cases"] == tests["test_cases"] == 127, "Native cases incomplete")
need(tests["physical_operations"] == tests["real_provider_loads"] == 0, "Offline boundary mismatch")
verify(tests)
for p in (C / "build_a/BUILD.json", C / "build_b/BUILD.json", C / "INPUT_PINS.json", C / "reports/REUSE_PROOF.json"):
    verify(read(p)); pin(p)
need(tests["inputs"]["offline_executable"]["sha256"] == "e16d47a1d7fda7058016cf0f392aca1b64d1a6077353185eda8d3bb33ed68c86", "Unexpected final native bytes")
need(git("branch", "--show-current") == "rk03/post-transition-offline", "Wrong development branch")
need(git("status", "--porcelain", "--untracked-files=no") == "", "Uncommitted development edits")
head = git("rev-parse", "HEAD")
need(head != "00664cbe83c35eee0faffd4161c76fc70888984f", "Continuation not committed")
need(git("rev-parse", "rk03/explicit-serial-init") == "00664cbe83c35eee0faffd4161c76fc70888984f", "Original branch changed")
need(git("rev-parse", "rk03/transition-probe") == "6d2a076cc8cf90f023211c1e71ad5571e7b0ee8d", "Probe branch changed")

rom = read(A / "CURRENT_ROM_STATUS.json")
need(rom["CURRENT_ROM_SIZE"] == 1048576 and rom["CURRENT_CAL_ID"] == "A2WC511R" and rom["CURRENT_ECU_ID"] == "2F12515306", "Current-ROM identity mismatch")
need(rom["CURRENT_SUBARU_CHECKSUM"] == "PASS" and rom["EXECUTABLE_BYTES_IDENTICAL_TO_STOCK"] is True, "Current-ROM result differs")
need(pin(Path(r"C:\Dev\SubaruRoms\current.bin"))["sha256"] == rom["CURRENT_ROM_SHA256"], "Original current.bin changed")
need(pin(A / "current.preserved.bin")["sha256"] == rom["CURRENT_ROM_SHA256"], "Preserved current.bin changed")
for relative in ["OBJECTIVES_A_COMPLETE.json", "probe_qualification/QUALIFICATION.json",
                 "physical_probe_result/MANIFEST.json", "physical_probe_comparison/COMPARISON_MANIFEST.json",
                 "physical_probe_review/AUDIT.json", "oem_return_after_probe_01/MANIFEST.json",
                 "post83_oem_review/MANIFEST.json"]:
    p = A / relative
    verify(read(p)); pin(p)
old = Path(r"C:\Dev\A2WC511R_Final\analysis\rk02_vehicle_03_transition\FAILED_EVIDENCE_BEFORE.json")
old_manifest = read(old)
for row in old_manifest["files"]:
    actual = pin(Path(old_manifest["root"]) / row["path"])
    need(actual["sha256"] == row["sha256"] and actual["bytes"] == row["bytes"], "RK02 failed evidence changed")
pin(old)
physical = read(A / "physical_probe_result/PHYSICAL_RESULT.json")
oem = read(A / "oem_return_after_probe_01/OEM_RETURN_RESULT.json")
gates = read(A / "PROBE_GATE_STATE.json")
need(physical["RK03_TRANSITION_PHYSICAL"] == "PASS" and physical["physical_invocations"] == 1, "Physical result differs")
need(physical["C3_response"] == "80f01007c30000ff00ff0048" and physical["process_exited"], "Physical C3/exit differs")
need(oem["OEM_RETURN_AFTER_TRANSITION_PROBE"] == "PASS" and oem["samples"] == 120, "OEM return incomplete")
need(gates["probe_invocation_count"] == 1 and gates["passive_oem_return_invocations"] == 1, "Unexpected physical invocation count")
need(gates["OEM_RETURN_AFTER_TRANSITION_PROBE"] == "PASS" and gates["further_physical_activity_allowed"] is False, "Wrong final physical scope")
verify(gates["active_human_gate_policy"])
for p in [A / "CURRENT_ROM_STATUS.json", A / "CURRENT_ROM_STATUS.md", A / "physical_probe_result/PHYSICAL_RESULT.json",
          A / "physical_probe_result/PHYSICAL_RESULT.md", A / "oem_return_after_probe_01/OEM_RETURN_RESULT.json",
          A / "oem_return_after_probe_01/OEM_RETURN_RESULT.md", C / "README.md", C / "reports/SOURCE_PATCH.diff", Path(__file__)]: pin(p)
for p in (C / "tools").iterdir():
    if p.is_file(): pin(p)

OUT.mkdir(exist_ok=False)
with (OUT / "GATE_STATE_AT_COMPLETION.json").open("xb") as f:
    f.write((A / "PROBE_GATE_STATE.json").read_bytes())
pin(OUT / "GATE_STATE_AT_COMPLETION.json")
now = datetime.now(timezone.utc).isoformat()
qualification = {
    "schema": 1, "created_utc": now, "status": "PASS_OFFLINE_CONTINUATION_THROUGH_FIRST_ACKNOWLEDGED_RAM_CHUNK",
    "branch": "rk03/post-transition-offline", "commit": head,
    "executable": tests["inputs"]["offline_executable"], "cases_passed": 127,
    "test_report": pin(test_path), "independent_native_review": pin(args.native_review), "independent_runner_review": pin(root_review),
    "stock_instruction_review": pin(A / "post83_oem_review/OEM_POST83_REVIEW.json"),
    "scope": "Static in-process fake provider only; eight requests through first128-byte36 ACK and cleanup",
    "physical_authorization": False, "full_acquisition_qualified": False,
    "intentional_differences": [
        "One34 retained: actual stock/current instruction replay shows single and identical double declaration reach the same tested loader state.",
        "Owned RK02 kernel1808bytes differs from ECUFlash DUAL1.07 kernel4660bytes; only the first128-byte encrypted chunk is exercised here.",
        "Strict full reply/metadata validation and terminal nonzero-status/no-retry policy retained.",
        "200/100/200ms requested waits and post-baud TX/RX clears follow reviewed ECUFlash host evidence; virtual time does not establish physical minimum delays.",
        "15625 baud SET status/output checked; no baud GET or measured physical baud is claimed.",
        "Provider discovery/reopen/pin9 operations remain omitted; initial tested transport is reused; full upload/start/read/finalizer are outside this scope."
    ],
    "files": list(pins.values())
}
write(OUT / "CONTINUATION_QUALIFICATION.json", qualification)
summary = {
    "schema": 1, "created_utc": now, "status": "REQUESTED_SCOPE_COMPLETE",
    "RK03_TRANSITION_PHYSICAL": "PASS", "physical_probe_invocations": 1,
    "physical_C3_response": "80f01007c30000ff00ff0048",
    "OEM_RETURN_AFTER_TRANSITION_PROBE": "PASS", "passive_samples": 120, "observer_broker_provider_cleanup": "PASS",
    "OFFLINE_CONTINUATION_FIRST_CHUNK": "PASS_127_OF_127", "offline_executable_sha256": tests["inputs"]["offline_executable"]["sha256"],
    "continuation_qualification": pin(OUT / "CONTINUATION_QUALIFICATION.json"), "development_commit": head,
    "current_rom_designation": "CURRENT_PHYSICAL_CAPTURE", "current_rom_sha256": rom["CURRENT_ROM_SHA256"],
    "current_rom_size": rom["CURRENT_ROM_SIZE"], "current_cal_id": rom["CURRENT_CAL_ID"], "current_subaru_checksum": "PASS",
    "total_differing_bytes": rom["TOTAL_DIFFERING_BYTES"], "differing_ranges": len(rom["EXACT_DIFFERING_RANGES"]),
    "executable_bytes_identical_to_stock": True, "changed_executable_functions": [], "unknown_changed_ranges": [],
    "closest_historical_tune": r"C:\Users\Jeriah Neal\Desktop\AdjustedBaseTimingANDNOCLOLD.bin", "historical_match": "EXACT",
    "current_rom_report": pin(A / "CURRENT_ROM_STATUS.json"), "physical_result": pin(A / "physical_probe_result/PHYSICAL_RESULT.json"),
    "oem_return_result": pin(A / "oem_return_after_probe_01/OEM_RETURN_RESULT.json"),
    "transport_comparison": pin(A / "physical_probe_comparison/PHYSICAL_TRANSITION_COMPARISON.json"),
    "causality": "Combined corrected transport crossed83 in one physical session; no individual change identified as uniquely causal.",
    "physical_programming_after_probe": False, "physical_RAM_upload_in_this_run": False, "physical_kernel_start_in_this_run": False,
    "physical_ROM_read_by_custom_host_in_this_run": False, "flash_operation_in_this_run": False,
    "gate_policy": gates["active_human_gate_policy"], "measured_vehicle_power_loss_claimed": False,
    "future_physical_work_authorized": False, "full_RK03_acquisition_performed": False
}
write(OUT / "RUN_RESULT.json", summary)
markdown = f"""# Current ROM and RK03 transition run

The requested scope is complete. **RK03_TRANSITION_PHYSICAL = PASS** and **OEM_RETURN_AFTER_TRANSITION_PROBE = PASS**. The transition probe ran exactly once, returned `80 F0 10 07 C3 00 00 FF 00 FF 00 48` after `83 00`, and completed explicit filter/channel/provider cleanup. The subsequent normal-mode passive observer confirmed BF identity `2F12515306` and 120 samples of six variables with PASS_CAPTURE_ONLY and clean observer/broker/provider exit.

Reproducing the reviewed ECUFlash-style explicit serial initialization and broad filtering restored successful progression through `83 00` in this session. No individual change is claimed uniquely causal. Both requested and effective initial values were `PARITY=0`, `P1_MAX=1`, `P3_MIN=0`, `P4_MIN=0` and `LOOPBACK=0`. The broad PASS filter used four zero bytes in mask, pattern and a nonnull flow object. Full arguments and timing are preserved in the physical journal.

The separate offline continuation passed **127/127** cases and two identical clean builds. Executable SHA256: `{tests['inputs']['offline_executable']['sha256']}`. Branch `rk03/post-transition-offline`, commit `{head}`. Independent native and runner reviews passed. It has only a static fake backend and stops after the first 128-byte `36` acknowledgment; no full physical acquisition was performed or qualified.

The continuation checks 16 OEM-derived seed vectors, exact later ACKs, 200/100/200 ms virtual waits, the 15625 baud SET, TX/RX queue clears, one `34` and the first fixed encrypted chunk. Actual stock/current instruction replay independently confirms that one `34` suffices at the tested admitted loader boundary and that the first chunk yields `76` and 32 correct decrypted stores. Virtual timing and supplied peripheral/admission inputs do not establish later physical behavior. A failed `36` may already have changed RAM; the host does not retry.

**CURRENT PHYSICAL ECU IMAGE: calibration differs from stock; executable code identical to stock.**

- Designation: CURRENT_PHYSICAL_CAPTURE, not factory stock.
- SHA256: `{rom['CURRENT_ROM_SHA256']}`
- Size: 1,048,576 bytes; CAL ID: A2WC511R; ECU ID: 2F12515306; Subaru checksum: PASS.
- Exact stock baseline SHA256: `22d52a5b3de7d86562eed2f85cca772db10e0949fcedc2d61b7540b45f760218`.
- 1,856 changed bytes in 517 ranges: 1765 table, 62 axis, 21 scalar, 4 checksum, 4 metadata; 0 changed executable instructions/functions and 0 unknown ranges.
- Exact historical match: `AdjustedBaseTimingANDNOCLOLD.bin`. Direct current.bin bytes remain authoritative.

The latest successful ECUFlash log is preserved and associated by exact saved path, size and timestamp. Its raw 81/83 bytes and session-time provider hash are not exposed. API 04.04 and firmware 1.17.4877 match the probe; full DLL build strings differ (:31 in ECUFlash logs, :05 from the probe). The saved 1 MiB file is authoritative for analysis, while the application log does not prove every saved byte crossed the bus.

Earlier component gates and voltage reports remain historical evidence. The operator explicitly replaced those gates with IGNITION OFF / TEST MODE ON / NORMAL MODE ON. OEM return followed the exact NORMAL MODE ON reply. No measured vehicle-side power-loss assertion is made. The software interlocks and one-shot limit remain in force, and no further physical operation is authorized here.

Reports:

- [Current ROM detail](../CURRENT_ROM_STATUS.md)
- [Current/August/RK02/physical-probe comparison](../physical_probe_comparison/PHYSICAL_TRANSITION_COMPARISON.md)
- [Physical probe result](../physical_probe_result/PHYSICAL_RESULT.md)
- [Passive OEM return](../oem_return_after_probe_01/OEM_RETURN_RESULT.md)
- [Stock/current first-chunk instruction review](../post83_oem_review/OEM_POST83_REVIEW.md)
- [Offline continuation qualification](CONTINUATION_QUALIFICATION.json)

RK02 artifacts, failed RK02_VEHICLE_03 evidence, the original development/probe branches, current.bin and successful ECUFlash evidence remain unchanged. PRESERVATION_MANIFEST.json pins all verified inputs and final outputs. Full kernel upload/start, complete custom ROM acquisition and physical behavior beyond `83 00` remain separate future work.
"""
with (OUT / "RUN_REPORT.md").open("x", encoding="utf-8") as f: f.write(markdown)
pin(OUT / "RUN_RESULT.json"); pin(OUT / "RUN_REPORT.md")
write(OUT / "PRESERVATION_MANIFEST.json", {"status": "PASS_FINAL_HASH_AUDIT", "created_utc": now, "failed_RK02_files_verified": len(old_manifest["files"]), "files": list(pins.values())})
for p in OUT.iterdir(): p.chmod(0o444)
for p in [C / "build_a/rk03_first_chunk_offline32.exe", C / "build_b/rk03_first_chunk_offline32.exe", test_path]: p.chmod(0o444)

gates.update(status="PHYSICAL_PROBE_OEM_RETURN_AND_REQUESTED_OFFLINE_SCOPE_COMPLETE", next_gate=None,
             completion_report=str(OUT / "RUN_RESULT.json"), offline_continuation_status="PASS_127_OF_127",
             further_physical_activity_allowed=False, updated_utc=now)
(A / "PROBE_GATE_STATE.json").write_text(json.dumps(gates, indent=2)+"\n", encoding="utf-8")
sp = Path(r"C:\Dev\A2WC511R_Final\state\CURRENT.json")
state = read(sp)
state.update(phase="RK03_TRANSITION_PROBE_CURRENT_ROM_AND_OFFLINE_FIRST_CHUNK_COMPLETE", completion_claimed=True,
             completion_scope="Current ROM ingest, one physical BF81/83 probe, passive OEM return, offline continuation through first chunk ACK only",
             completion_report=str(OUT / "RUN_RESULT.json"), completion_manifest=str(OUT / "PRESERVATION_MANIFEST.json"),
             continuation_development_directory=str(R), continuation_development_branch="rk03/post-transition-offline", continuation_development_commit=head,
             offline_continuation_status="PASS_127_OF_127", human_required=[], next_action="No further physical action authorized; retain sealed evidence for separately scoped future work",
             full_rk03_acquisition_allowed=False, further_physical_activity_allowed=False, updated_utc=now)
sp.write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status": "REQUESTED_SCOPE_COMPLETE", "report": pin(OUT / "RUN_REPORT.md"), "manifest": pin(OUT / "PRESERVATION_MANIFEST.json"), "verified_files": len(pins), "physical_probe_invocations": 1, "passive_samples": 120, "offline_cases": 127}))
