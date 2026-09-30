"""Offline evidence validation and sealing for the completed passive OEM return."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

A = Path(__file__).resolve().parent
O = A / "oem_return_after_probe_01"

def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def require(ok, why):
    if not ok: raise RuntimeError(why)
def pin(p):
    data = p.read_bytes()
    return {"path": str(p), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

rows = [json.loads(x) for x in (O / "capture.jsonl").read_text().splitlines()]
identity = [r for r in rows if r.get("type") == "identity"]
samples = [r for r in rows if r.get("type") == "sample"]
end = rows[-1]
execution = read(O / "EXECUTION.json")
require(len(identity) == 1 and identity[0]["ecu_id"] == "2F12515306", "OEM identity mismatch")
require(len(samples) == end["samples_written"] == 120, "Sample count mismatch")
require(end["status"] == "PASS_CAPTURE_ONLY" and end["error"] is None and end["cleanup_error"] is None, "Capture or cleanup failure")
require(execution["process_exited"] and execution["exit_code"] == 0, "Observer exit failure")
require(read(O / "POSTEXIT_CLIENT_CHECK.json")["pass"] is True, "Process/provider absence check failed")
expected_addresses = {"FFFF4C75", "FFFF4C8D", "FFFF4CA1", "FFFF4C50", "FFFF4BC1", "FFFF4BC2"}
for r in samples:
    require(set(r["raw_by_address"]) == expected_addresses, "Six-variable acquisition mismatch")
    require(r["provenance"]["identity_ecu_id"] == "2F12515306" and r["provenance"]["physical_backend"] is True, "Physical identity provenance mismatch")
stderr = (O / "capture.jsonl.provider.stderr.log").read_text()
tx = re.findall(r"^TX .* raw=([0-9a-fA-F]+)$", stderr, re.M)
expected_snapshot = "8010f014a800ff4c75ff4c8dff4ca1ff4c50ff4bc1ff4bc272"
require(tx == ["8010f001bf40"] + [expected_snapshot] * 120, "Unexpected passive wire requests")
gates = read(A / "PROBE_GATE_STATE.json")
require(gates["normal_mode_confirmation"]["reply"] == "NORMAL MODE ON" and gates["probe_invocation_count"] == 1, "Gate/invocation mismatch")
policy = gates["active_human_gate_policy"]
require(pin(Path(policy["path"]))["sha256"] == policy["sha256"], "Operator policy hash mismatch")
for name, data in [("GATE_STATE_AT_OEM_RETURN.json", (A / "PROBE_GATE_STATE.json").read_bytes())]:
    with (O / name).open("xb") as f: f.write(data)
evidence = [pin(p) for p in sorted(O.iterdir()) if p.is_file()]
result = {
    "schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
    "OEM_RETURN_AFTER_TRANSITION_PROBE": "PASS", "session_id": "RK03_TRANSITION_PROBE_01",
    "BF_identity": "2F12515306", "capture_status": "PASS_CAPTURE_ONLY", "samples": 120,
    "variables_per_sample": 6, "observer_exit_code": 0, "broker_cleanup_confirmed": True,
    "cleanup_basis": "Capture ended with no cleanup error; pinned transport close requires the broker CLOSE response and exit zero, then waits for worker termination. Post-exit process/module check also passed.",
    "provider_cleanup_confirmed": True, "postexit_provider_module_users": [],
    "wire_requests": {"BF": 1, "A8": 120, "other": 0}, "programming_session_requests": 0,
    "transition_probe_invocations": 1, "transition_probe_rerun_allowed": False,
    "full_acquisition_allowed": False, "current_rom_attestation_from_passive_capture": False,
    "physical_state_basis": "NORMAL MODE ON confirmed by operator; battery/charger/OpenPort/connector details operator-managed under explicit simplified policy. Measured vehicle-side power loss was not established and is not claimed.",
    "active_human_gate_policy": policy, "evidence": evidence,
    "next_scope": "OFFLINE_ONLY_REMAINING_RK03_SEQUENCE_THROUGH_FIRST_ACKNOWLEDGED_UPLOAD_CHUNK",
    "validator": pin(Path(__file__))
}
rp = O / "OEM_RETURN_RESULT.json"
with rp.open("x", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
    f.write("\n")
md = """# OEM return after the single transition probe

OEM_RETURN_AFTER_TRANSITION_PROBE = PASS

The operator confirmed NORMAL MODE ON under the simplified ignition-state policy. The unchanged qualified observer read BF identity 2F12515306 and completed 120 six-variable A8 samples with PASS_CAPTURE_ONLY. Its wire log contains one BF request and 120 fixed A8 requests, with no programming/session probe.

Observer exit was zero. Capture and cleanup errors were null. The pinned transport requires a successful broker CLOSE response and worker exit zero; a subsequent process/module scan also found no remaining diagnostic client or provider module user. Observer, broker and provider cleanup passed.

The transition probe invocation count remains exactly one. No further physical testing or full acquisition is authorized in this run. Work continues offline through the first acknowledged RAM-upload chunk using simulated providers only.

Earlier component gates are retained as history or explicitly waived, never relabeled PASS. Measured vehicle-side power loss was not established; the operator assumed physical preparation responsibility and confirmed normal mode. This passive capture does not attest a whole ROM image; current.bin remains the separately preserved ECUFlash acquisition.
"""
(O / "OEM_RETURN_RESULT.md").write_text(md, encoding="utf-8")
manifest = {"status": "SEALED_OEM_RETURN_PASS", "files": [pin(p) for p in sorted(O.iterdir()) if p.is_file()]}
with (O / "MANIFEST.json").open("x", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
for p in O.iterdir():
    if p.is_file(): p.chmod(0o444)
now = datetime.now(timezone.utc).isoformat()
gates.update(status="OEM_RETURN_PASS_OFFLINE_ONLY", next_gate=None, expected_manual_reply=None,
             OEM_RETURN_AFTER_TRANSITION_PROBE="PASS", oem_return_result=pin(rp),
             passive_oem_return_invocations=1, further_physical_activity_allowed=False, updated_utc=now)
(A / "PROBE_GATE_STATE.json").write_text(json.dumps(gates, indent=2)+"\n", encoding="utf-8")
sp = Path(r"C:\Dev\A2WC511R_Final\state\CURRENT.json")
state = read(sp)
state.update(phase="RK03_TRANSITION_AND_OEM_RETURN_PASS_OFFLINE_REMAINING_SEQUENCE", OEM_RETURN_AFTER_TRANSITION_PROBE="PASS",
             oem_return_result=str(rp), human_required=[], next_action="Offline qualification of remaining RK03 sequence through first acknowledged RAM-upload chunk; no physical acquisition",
             further_physical_activity_allowed=False, updated_utc=now)
sp.write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status": "OEM_RETURN_AFTER_TRANSITION_PROBE_PASS", "samples": 120, "wire_requests": result["wire_requests"], "result": pin(rp), "next_scope": "OFFLINE_ONLY"}))
