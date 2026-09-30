"""Read-only evidence audit, followed by offline result/state persistence."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

A = Path(__file__).resolve().parent
D = Path(r"C:\Dev\A2WC511R_RK03_TransitionDev")
S = Path(r"C:\Dev\A2WC511R_Final\state")
REPORT = D / "reports/run_20260930T000721019704Z/TEST_REPORT.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


checks = []


def check(item, base=None, category=""):
    path = Path(item["path"])
    if not path.is_absolute():
        path = base / path
    actual = pin(path)
    assert actual["sha256"] == item["sha256"], str(path)
    if "bytes" in item:
        assert actual["bytes"] == item["bytes"], str(path)
    checks.append({"category": category, **actual, "match": True})


def git(*args):
    return subprocess.check_output(["git", "-C", str(D), *args], text=True).strip()


before = read(A / "FAILED_EVIDENCE_BEFORE.json")
failed = Path(before["root"])
expected = {str(Path(x["path"])) for x in before["files"]}
observed = {str(p.relative_to(failed)) for p in failed.rglob("*") if p.is_file()}
assert observed == expected, "Failed session file set changed"
for item in before["files"]:
    check(item, failed, "failed_session")

analysis_manifest = read(A / "ANALYSIS_BEFORE_DEVELOPMENT_MANIFEST.json")
for item in analysis_manifest["files"]:
    check(item, category="analysis_precedes_development")
for item in read(A / "RK02_VEHICLE_03_SESSION_TRANSITION_EVENT_DIFF.json")["evidence_paths_hashes"]:
    check(item, category="analysis_evidence")
freeze_path = Path(r"C:\Dev\A2WC511R_ReadKernel\evidence\rk02\RELEASE_FREEZE.json")
for item in read(freeze_path)["files"]:
    check(item, category="qualified_release")
for item in read(D / "provenance/INPUT_PINS.json"):
    check(item, category="development_input")
check({"path": str(REPORT), "sha256": "e82c36175608a7d09748993948336acb896cd1e58e63b1bfdb5afd800296117d"}, category="test_report")
report = read(REPORT)
assert report["status"] == "PASS" and report["test_cases"] == 25 and report["test_groups"] == 7
assert report["physical_operations"] == report["real_provider_loads"] == 0
for item in report["artifacts"]:
    check(item, D, "tested_artifact")
for case in report["cases"]:
    assert case["status"] == "PASS"
    check({"path": case["journal"], "sha256": case["journal_sha256"]}, category="test_journal")
assert git("status", "--porcelain") == "", "Development repository has uncommitted changes"
assert git("branch", "--show-current") == "rk03/explicit-serial-init"
assert git("rev-parse", "HEAD") == "00664cbe83c35eee0faffd4161c76fc70888984f"

now = datetime.now(timezone.utc).isoformat()
audit = {
    "schema": 1, "created_at_utc": now, "status": "PASS",
    "scope": "File integrity and Git inspection only; no tests, executables, provider or hardware invoked",
    "failed_session_file_count": len(expected), "failed_session_file_set_unchanged": True,
    "checks": checks,
    "development_git_branch": git("branch", "--show-current"),
    "development_git_commit": git("rev-parse", "HEAD"),
    "development_git_clean": True,
}
with (A / "FINAL_INTEGRITY_AUDIT.json").open("x", encoding="utf-8") as f:
    json.dump(audit, f, indent=2)
    f.write("\n")

result = {
    "schema": 1, "created_at_utc": now,
    "status": "OFFLINE_ANALYSIS_AND_ISOLATED_CORRECTION_COMPLETE_WITH_CAUSAL_LIMITS",
    "physical_cause": "NOT_UNIQUELY_DETERMINED",
    "confirmed_host_failure": "ReadMsgs returned ERR_BUFFER_EMPTY (16), count 0 after 8300; RK02 terminated on its fatal nonzero-status guard",
    "confirmed_software_omission": "RK02 inherits unrecorded serial defaults instead of applying the five explicit settings present in the installed ECUFlash channel initialization",
    "configuration_correction": [{"parameter": p, "value": v} for p, v in [(22, 0), (7, 1), (10, 0), (12, 0), (3, 0)]],
    "first_divergence_scope": "Matched OEM-channel initialization segment after PassThruConnect; complete ECUFlash prefix also contains an earlier kernel-version probe",
    "development": {"directory": str(D), "branch": audit["development_git_branch"], "commit": audit["development_git_commit"], "git_clean": True,
                    "readme": pin(D / "README.md"), "candidate": pin(D / "build/rk03_transition_fake32.exe"),
                    "test_report": pin(REPORT), "test_cases_passed": 25, "test_groups_passed": 7},
    "independent_review": {
        "candidate_reviewer": "/root/passive_review",
        "result": "No blocking finding for stated offline scope; 20 artifact hashes and 25 journal hashes verified; native execution, config-before-TX, failure stopping and fake-only isolation reviewed",
        "provenance": "Root transcription of reviewer final message in this Codex run; reviewer performed read-only review",
        "oem_review": pin(A / "oem_transition_review.json")},
    "deliverables": [pin(Path(x["path"])) for x in analysis_manifest["files"]],
    "analysis_written_before_development": pin(A / "ANALYSIS_BEFORE_DEVELOPMENT_MANIFEST.json"),
    "integrity_audit": pin(A / "FINAL_INTEGRITY_AUDIT.json"),
    "physical_activity_during_analysis_and_development": False,
    "rk02_physical_invocations_this_run": 1,
    "qualified_rk02_and_failed_session_unchanged": True,
    "new_physical_attempt_qualified": False,
    "new_physical_attempt_requested": False,
    "current_vehicle_rom": "UNIDENTIFIED_NO_BYTES_ACQUIRED",
    "limitations": [
        "Historical successful physical application logs omit raw 81/83 traffic, provider defaults and exact bus timing; full physical transition equivalence cannot be established",
        "Fake replay combines independently labelled sources; its positive replies are not a successful historical physical transcript",
        "Synthetic incompatible defaults test configuration admission, not the cause of the actual 83 silence",
        "Recorded status 16 replay preserves API outcome and request order, not physical elapsed time",
        "Candidate stops after first acknowledged 36 chunk; no RAM start, two full reads, finalization or cleanup qualification",
        "Later ECUFlash delays, duplicate 34, queue clears, response parsing and kernel differences remain outside the correction and unresolved for full transition qualification",
        "Stock instruction replay does not establish executable equality with the edited, unacquired current ROM"
    ]
}
with (A / "DEVELOPMENT_RESULT.json").open("x", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
    f.write("\n")

addendum = """# Offline development result

The requested analysis and event diff were sealed before development and remain unchanged. The physical reason for the missing reply remains unproven. Decimal 16 is ERR_BUFFER_EMPTY in the matching installed SDK definitions; it is not ERR_TIMEOUT.

The isolated `rk03/explicit-serial-init` branch applies the five explicit serial settings identified in the installed ECUFlash initialization. Commit: `00664cbe83c35eee0faffd4161c76fc70888984f`. The executable binds only to its in-process fake provider. Both native builds compiled with warnings treated as errors; 25 cases across seven groups passed, and independent review found no blocking issue for that scope.

Tests preserve the native parser and seed logic, verify configuration failures stop before transmission, and replay the recorded status 16 termination in both baseline and candidate. The positive path ends after the first acknowledged upload chunk. This is not full ECUFlash transcript equivalence or physical qualification. The deliberately incompatible synthetic defaults are not measured OpenPort defaults and do not reproduce a proved physical cause.

For precision, the analysis's first configuration divergence refers to the matched OEM-channel initialization segment after Connect. The complete archived ECUFlash prefix also contains an earlier kernel-version probe. Historical successful physical logs do not record raw 81/83 bytes or exact provider timing. Later delays, queue clears, duplicate 34 declarations, response parsing and kernel differences still require resolution or independent justification before full transition qualification.

`FINAL_INTEGRITY_AUDIT.json` verifies the unchanged failed-session file set and all 17 file hashes, the qualified release, the original analysis evidence, and tested development artifacts. `DEVELOPMENT_RESULT.json` binds the report, branch, commit, test results and review. RK02 invocation count remains one. No additional physical attempt was performed, requested or qualified. Current vehicle ROM remains unidentified because no ROM bytes were acquired.
"""
with (A / "DEVELOPMENT_RESULT.md").open("x", encoding="utf-8") as f:
    f.write(addendum)

state = read(S / "CURRENT.json")
state.update({
    "phase": "OFFLINE_RK02_VEHICLE_03_ANALYSIS_AND_DEVELOPMENT_COMPLETE_CAUSAL_LIMITS_REMAIN",
    "updated_utc": now,
    "offline_scope_status": result["status"],
    "physical_causal_root_status": result["physical_cause"],
    "development_commit": result["development"]["commit"],
    "development_test_report": str(REPORT),
    "development_test_report_sha256": result["development"]["test_report"]["sha256"],
    "development_result": str(A / "DEVELOPMENT_RESULT.json"),
    "final_integrity_audit": str(A / "FINAL_INTEGRITY_AUDIT.json"),
    "new_physical_attempt_qualified": False,
    "next_action": "No further physical activity in this run. Remaining full-transition differences require offline resolution or independent justification before any future qualification.",
    "human_required": [],
    "further_physical_programming_attempts_allowed": False,
})
(S / "CURRENT.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
gates = read(S / "PHYSICAL_SESSION_GATES.json")
gates.update({"offline_analysis_status": result["status"], "offline_analysis_result": str(A / "DEVELOPMENT_RESULT.json"), "updated_utc": now})
(S / "PHYSICAL_SESSION_GATES.json").write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "hash_checks": len(checks), "failed_files_unchanged": len(expected), "development_result": str(A / "DEVELOPMENT_RESULT.json"), "physical_activity": False}))
