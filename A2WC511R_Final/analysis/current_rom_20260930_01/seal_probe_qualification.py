"""Seal final reviewed offline qualification; does not authorize or launch hardware."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

A = Path(__file__).resolve().parent
R = Path(r"C:\Dev\A2WC511R_RK03_TransitionProbe")
P = R / "probe"
Q = A / "probe_qualification"
pins = {}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def require(value, why):
    if not value:
        raise RuntimeError(why)


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    row = {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if str(path) in pins:
        require(pins[str(path)] == row, "File changed during seal: " + str(path))
    pins[str(path)] = row
    return row


def verify_tree(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("path"), str) and isinstance(obj.get("sha256"), str):
            actual = pin(obj["path"])
            require(actual["sha256"].lower() == obj["sha256"].lower(), "Stale evidence pin: " + obj["path"])
            for key in ("bytes", "size"):
                if isinstance(obj.get(key), int):
                    require(actual["bytes"] == obj[key], "Stale evidence size: " + obj["path"])
        for value in obj.values():
            verify_tree(value)
    elif isinstance(obj, list):
        for item in obj:
            verify_tree(item)


def git(*args):
    return subprocess.check_output(["git", "-C", str(R), *args], text=True).strip()


latest = read(P / "reports/LATEST_QUALIFICATION.json")
require(latest["status"] == "PASS", "Latest native qualification failed")
verify_tree(latest)
report_path = Path(latest["report"]["path"])
report = read(report_path)
require(report["status"] == "PASS" and report["test_cases"] == report["passed_cases"] > 0, "Native cases did not all pass")
require(all(x["status"] == "PASS" for x in report["cases"]), "Failed native case")
require(report["physical_operations"] == report["real_provider_loads"] == 0, "Offline boundary violated")
verify_tree(report)
for path in (P / "build_a/BUILD.json", P / "build_b/BUILD.json", P / "INPUT_PINS.json"):
    verify_tree(read(path))
    pin(path)
exe = pin(P / "build_a/rk03_transition_probe32.exe")
repro = pin(P / "build_b/rk03_transition_probe32.exe")
require(exe["sha256"] == repro["sha256"], "Clean build bytes differ")
review_path = A / "probe_review/code_review.json"
review = read(review_path)
require(review["status"].startswith("PASS"), "Independent review incomplete")
for finding in review.get("findings", []):
    require(finding.get("status", "").startswith("RESOLVED"), "Unresolved independent finding")
verify_tree(review)
pin(review_path)
pin(A / "probe_review/code_review.md")
qualification_review = A / "probe_review/qualification_review.json"
require(read(qualification_review)["status"] == "PASS_OFFLINE_PROBE_TEST_QUALIFICATION_REVIEW", "Qualification review incomplete")
verify_tree(read(qualification_review))
pin(qualification_review)
pin(A / "probe_review/qualification_review.md")
launcher_tests = read(A / "LAUNCHER_FINAL_TESTS.json")
require(launcher_tests["status"] == "PASS_FINAL_OFFLINE_LAUNCHER_CONTROLS", "Launcher controls failed")
verify_tree(launcher_tests)
pin(A / "LAUNCHER_FINAL_TESTS.json")
verify_tree(read(A / "OBJECTIVES_A_COMPLETE.json"))
verify_tree(read(A / "OEM_RETURN_REUSE.json"))
for name in ("OBJECTIVES_A_COMPLETE.json", "CURRENT_ROM_STATUS.json", "CURRENT_ROM_STATUS.md", "OEM_RETURN_REUSE.json", "INGEST_MANIFEST.json", "TRANSITION_PROBE_HUMAN_PROTOCOL.json", "launch_probe_once.py", "check_clients.ps1"):
    pin(A / name)
contract = pin(A / "PROBE_REVIEW_CONTRACT.json")
pin(Path(__file__))
pin(P / "README.md")
pin(P / "reports/SOURCE_PATCH.diff")
require(git("branch", "--show-current") == "rk03/transition-probe", "Wrong development branch")
require(git("status", "--porcelain") == "", "Uncommitted development changes")
original_head = git("rev-parse", "rk03/explicit-serial-init")
require(original_head == "00664cbe83c35eee0faffd4161c76fc70888984f", "Original development history changed")
for name in ("AUTHORIZATION.txt", "launch.reserved", "invocation.once", "native_api.jsonl"):
    require(not (R / "physical_session/RK03_TRANSITION_PROBE_01" / name).exists(), "Unexpected physical authorization or invocation evidence")

now = datetime.now(timezone.utc).isoformat()
Q.mkdir(exist_ok=False)
certificate = {
    "schema": 1, "created_utc": now, "status": "PASS_OFFLINE_QUALIFIED_TRANSITION_PROBE_ONLY",
    "physical_executable": exe, "reproducible_build_executable": repro, "review_contract": contract,
    "native_test_report": pin(report_path), "native_cases_passed": report["passed_cases"],
    "independent_review": pin(review_path), "launcher_control_tests": pin(A / "LAUNCHER_FINAL_TESTS.json"),
    "branch": git("branch", "--show-current"), "commit": git("rev-parse", "HEAD"), "original_branch_head_unchanged": original_head,
    "physical_authorization_received": False, "physical_probe_invocations": 0, "maximum_physical_probe_invocations": 1,
    "full_rk03_acquisition_allowed": False, "allowed_wire_requests": ["8010f001bf40", "8010f0018102", "8010f002830005"],
    "expected_C3_response": "80f01007c30000ff00ff0048",
    "files": list(pins.values()),
    "limits": ["Offline qualification permits presentation of human gates only; exact final authorization is still required.",
               "No physical provider path has been executed for this candidate. Fake cases do not establish electrical timing or real provider behavior.",
               "No seed/key, programming session, upload, kernel start, ROM read or flash path is in the probe build.",
               "Physical result remains NOT_RUN. No full RAM acquisition is permitted in this run."]
}
with (Q / "QUALIFICATION.json").open("x", encoding="utf-8") as f:
    json.dump(certificate, f, indent=2)
    f.write("\n")
cert_sha = hashlib.sha256((Q / "QUALIFICATION.json").read_bytes()).hexdigest()
summary = f"""# Transition-only probe qualification

PASS_OFFLINE_QUALIFIED_TRANSITION_PROBE_ONLY

The same x86 executable intended for the single gated experiment passed {report['passed_cases']} native in-process fake-provider cases. Two independent clean builds produced identical bytes. Independent source, build and test review passed; the parent launch controls passed 12 negative gates, one positive gate and two bookkeeping/child-wait cases without starting any process or provider.

Executable SHA256: `{exe['sha256']}`

Qualification SHA256: `{cert_sha}`

Branch: `rk03/transition-probe`; commit `{certificate['commit']}`. The original `rk03/explicit-serial-init` branch remains at `{original_head}`.

The only request sequence is BF, 81, 83 00. The five explicit settings are read back and checked before the broad filter or first request. Filter mask, pattern and the observed nonnull flow object are four zero bytes, matching archived ECUFlash arguments. All API input/output records, configuration/filter state, message metadata and API-bracketing QPC times are journaled. Success and failure both attempt filter stop, disconnect and close; no retries occur.

The qualification includes status 16 replay with the original recorded SOM/BF/SOM/C1/empty-read records, the full expected C3 response, configuration failures and mismatches, filter/identity/reply failures, malformed messages and cleanup errors. Physical elapsed timing is not simulated.

No provider was loaded and no physical probe was run during qualification. Only the human preparation gates may now begin. The exact final authorization remains **PROCEED RK03 TRANSITION PROBE**. A full acquisition is excluded.
"""
(Q / "QUALIFICATION.md").write_text(summary, encoding="utf-8")
gate_state = {
    "schema": 1, "session_id": "RK03_TRANSITION_PROBE_01", "status": "QUALIFIED_WAITING_G06", "next_gate": "G06",
    "qualification_sha256": cert_sha, "executable_sha256": exe["sha256"], "completed_pre_probe_gates": [],
    "commit_authorization": None, "probe_invocation_count": 0, "launch_reserved": False,
    "engine": "OFF", "stationary": True, "charger": "SCHUMACHER_SE_5212A_10A_CHARGING", "adapter": "GENUINE_OPENPORT_2_0",
    "operator_monitors_voltage": True, "context_source": "Latest user physical-context directive; actual fresh Test Mode indications required at G09",
    "full_acquisition_allowed": False, "physical_authorization_received": False,
    "protocol": str(A / "TRANSITION_PROBE_HUMAN_PROTOCOL.json"), "updated_utc": now,
}
with (A / "PROBE_GATE_STATE.json").open("x", encoding="utf-8") as f:
    json.dump(gate_state, f, indent=2)
    f.write("\n")
state_path = Path(r"C:\Dev\A2WC511R_Final\state\CURRENT.json")
state = read(state_path)
state.update(phase="RK03_TRANSITION_PROBE_OFFLINE_QUALIFIED_WAITING_G06", updated_utc=now,
             calibration_base="Authoritative current physical ECUFlash saved image current.bin, SHA256 bf10be6d7c75b4f2ae663b0d57a912e6e9ef7654ccfc985195954596e50427b2; identity/checksum/diff validated, acquisition limits retained in current session evidence; not factory stock",
             probe_qualification=str(Q / "QUALIFICATION.json"), probe_qualification_sha256=cert_sha,
             probe_executable_sha256=exe["sha256"], probe_gate_state=str(A / "PROBE_GATE_STATE.json"),
             probe_physical_authorization_received=False, probe_physical_invocations=0,
             next_action="G06: user turns ignition OFF; wait for exactly DONE G06", human_required=["G06"])
state_path.write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
global_gates_path = Path(r"C:\Dev\A2WC511R_Final\state\PHYSICAL_SESSION_GATES.json")
global_gates = read(global_gates_path)
global_gates.update(current_gate_state=str(A / "PROBE_GATE_STATE.json"),
                    current_gate_state_scope="New separately identified transition-only probe; all RK02 fields remain historical and failed-session files remain immutable",
                    transition_probe_allowed_after_human_authorization=True, full_rk03_acquisition_allowed=False,
                    latest_user_direction="One qualified BF81/83-only probe after fresh preparation gates and exact PROCEED RK03 TRANSITION PROBE; no full acquisition, no automatic retry",
                    updated_utc=now)
global_gates_path.write_text(json.dumps(global_gates, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status": certificate["status"], "cases": report["passed_cases"], "pinned_files": len(certificate['files']), "executable_sha256": exe['sha256'], "qualification_sha256": cert_sha, "next_gate": "G06", "physical_invocations": 0}))
