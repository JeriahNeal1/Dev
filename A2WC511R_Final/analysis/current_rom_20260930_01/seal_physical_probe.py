"""Validate and preserve the completed single probe; never opens a provider."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

A = Path(__file__).resolve().parent
S = Path(r"C:\Dev\A2WC511R_RK03_TransitionProbe\physical_session\RK03_TRANSITION_PROBE_01")
D = A / "physical_probe_result"

def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))

def need(value, why):
    if not value:
        raise RuntimeError(why)

def pin(p):
    data = p.read_bytes()
    return {"path": str(p), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

rows = [json.loads(line) for line in (S / "native_api.jsonl").read_text().splitlines()]
ret = [r for r in rows if r["type"] == "api_return"]
intents = [r for r in rows if r["type"] == "api_intent"]
need(len(ret) == len(intents) == 22, "Unexpected API call count")
need([r["sequence"] for r in ret] == list(range(22)), "Nonsequential API returns")
for i, r in zip(intents, ret):
    need((i["sequence"], i["function"], i["input"]) == (r["sequence"], r["function"], r["input"]), "Intent/return mismatch")
    need(r["status"] == 0 and r["physical"] is True, "API did not succeed physically")
    need(i["host_event_counter"] <= r["qpc_before"] <= r["qpc_after"], "Invalid API timestamps")
    need(r["api_elapsed_ticks"] == r["qpc_after"] - r["qpc_before"], "Invalid duration")
tx = [r for r in ret if r["function"] == "PassThruWriteMsgs"]
expected_tx = ["8010f001bf40", "8010f0018102", "8010f002830005"]
need([r["input"]["message"]["data_hex"] for r in tx] == expected_tx, "TX sequence mismatch")
need(all(r["input"]["input_count"] == r["output"]["count"] == 1 for r in tx), "Write counts mismatch")
rx = [r for r in ret if r["function"] == "PassThruReadMsgs"]
need(len(rx) == 6 and all(r["output"]["count"] == 1 for r in rx), "Read counts mismatch")
frames = [r for r in rx if r["output"]["message"]["data_size"]]
need(len(frames) == 3, "Unexpected received frame count")
frame_hex = [r["output"]["message"]["data_hex"] for r in frames]
for h in expected_tx + frame_hex:
    b = bytes.fromhex(h)
    need(len(b) == b[3] + 5 and sum(b[:-1]) % 256 == b[-1], "SSM length/checksum failure")
need(bytes.fromhex(frame_hex[0])[8:13].hex() == "2f12515306", "BF identity mismatch")
need(frame_hex[1:] == ["80f01003c1ef8fc2", "80f01007c30000ff00ff0048"], "C1/C3 mismatch")
settings = [{"parameter": k, "value": v} for k, v in [(22,0),(7,1),(10,0),(12,0),(3,0)]]
need(all(r["function"] == "PassThruIoctl" and r["input"]["ioctl"] == 2 for r in ret[3:8]), "SET order mismatch")
need([r["input"]["config"]["owned_buffer_entries"][0] for r in ret[3:8]] == settings, "SET values mismatch")
get = ret[8]
need(get["function"] == "PassThruIoctl" and get["input"]["ioctl"] == 1, "Immediate GET missing")
need(get["output"]["config"]["owned_buffer_entries"] == settings and get["state"]["effective_configuration_valid"], "Readback mismatch")
flt = ret[9]
need(flt["function"] == "PassThruStartMsgFilter" and flt["input"]["filter_type"] == 1, "Broad filter missing")
for k in ["mask", "pattern", "flow"]:
    need(flt["input"][k + "_present"] and flt["input"][k]["data_hex"] == "00000000" and flt["input"][k]["protocol"] == 3, "Filter differs")
need([r["function"] for r in ret[-3:]] == ["PassThruStopMsgFilter", "PassThruDisconnect", "PassThruClose"], "Cleanup order mismatch")
terminal = rows[-1]
need(terminal["status"] == "PASS_TRANSITION_PROBE_ONLY" and terminal["protocol_complete"] and terminal["cleanup_confirmed"] and not terminal["log_failed"] and terminal["cleanup_error_mask"] == 0, "Terminal failed")
need(not terminal["state"]["opened"] and not terminal["state"]["connected"] and not terminal["state"]["filter"]["active"], "Resources remain active")
execution = read(S / "EXECUTION.json")
need(execution["exit_code"] == 0 and execution["process_exited"] and execution["bookkeeping_error"] is None, "Process exit failure")
need(read(S / "POSTEXIT_CLIENT_CHECK.json")["pass"] is True, "Provider process cleanup not established")
gates = read(A / "PROBE_GATE_STATE.json")
need(gates["probe_invocation_count"] == 1 and gates["process_exited"] and gates["commit_authorization"]["reply"] == "PROCEED RK03 TRANSITION PROBE", "Invocation/authorization mismatch")

D.mkdir(exist_ok=False)
saved = D / "evidence"
saved.mkdir()
evidence = []
sources = sorted(p for p in S.iterdir() if p.is_file()) + [A / "PROBE_GATE_STATE.json"]
for p in sources:
    target = saved / p.name
    shutil.copy2(p, target)
    need(pin(p)["sha256"] == pin(target)["sha256"], "Preservation copy mismatch")
    evidence.append({"source": pin(p), "preserved": pin(target)})
    target.chmod(0o444)
    if p.parent == S:
        p.chmod(0o444)
report = {
    "schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
    "session_id": "RK03_TRANSITION_PROBE_01", "RK03_TRANSITION_PHYSICAL": "PASS",
    "physical_invocations": 1, "retry_allowed": False, "full_acquisition_allowed": False,
    "BF_identity": "2F12515306", "transmitted_frames": expected_tx, "received_frames": frame_hex,
    "C3_response": frame_hex[-1], "all_api_calls": len(ret), "all_api_statuses_zero": True,
    "configuration_requested": settings, "configuration_reported_effective": get["output"]["config"]["owned_buffer_entries"],
    "connection": ret[2]["input"], "broad_filter": flt["input"], "ReadVersion": ret[1]["output"],
    "cleanup": [{"function": r["function"], "status": r["status"]} for r in ret[-3:]],
    "process_exited": True, "exit_code": 0, "postexit_client_check_pass": True,
    "C1_API_return_to_83_API_entry_ms": (tx[2]["qpc_before"] - frames[1]["qpc_after"]) / 10000,
    "C3_API_return_latency_from_83_write_return_ms": (frames[2]["qpc_after"] - tx[2]["qpc_after"]) / 10000,
    "timing_limit": "Host API boundaries are not measured physical K-line symbol timing.",
    "interpretation": "Reproducing the reviewed ECUFlash-style explicit serial initialization and broad filtering restored successful progression through 83 00 in this physical session. Individual-change causality was not isolated.",
    "remaining": "Human key-off/verified power-down/OEM-return recovery remains required, then only offline remaining-sequence qualification. No full RK03 acquisition in this run.",
    "evidence": evidence, "validator": pin(Path(__file__))
}
with (D / "PHYSICAL_RESULT.json").open("x", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
    f.write("\n")
md = """# Single physical transition probe

RK03_TRANSITION_PHYSICAL = PASS

The qualified probe ran exactly once and sent only BF, 81, and 83 00. ECU BF identity was 2F12515306. The complete response to 83 00 was `80 F0 10 07 C3 00 00 FF 00 FF 00 48`, with valid length and checksum. All five provider-reported configuration values matched their requests. All 22 API calls returned status zero.

Reproducing the reviewed ECUFlash-style explicit serial initialization and broad filtering restored successful progression through 83 00 in this physical session. The experiment does not isolate which individual change caused the improvement.

PassThruStopMsgFilter, PassThruDisconnect and PassThruClose all returned zero. The process exited zero, and a subsequent process/module scan found no competing diagnostic clients or provider users. No seed/key, programming-admission, RAM upload, kernel start, ROM read or flash command was transmitted. There is no retry and no full acquisition in this run.

The raw session files and authorization/gate snapshot are preserved as read-only copies with source and copy hashes in PHYSICAL_RESULT.json. Transport cleanup is confirmed; vehicle power-down and OEM-return verification remain pending human gates. The current-ROM report remains unchanged: calibration differs from stock; executable code is byte-identical to stock.
"""
(D / "PHYSICAL_RESULT.md").write_text(md, encoding="utf-8")
manifest = {"status": "SEALED_SINGLE_PHYSICAL_TRANSITION_PASS", "files": [pin(D / "PHYSICAL_RESULT.json"), pin(D / "PHYSICAL_RESULT.md")] + [r["preserved"] for r in evidence]}
with (D / "MANIFEST.json").open("x", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
for p in D.iterdir():
    if p.is_file(): p.chmod(0o444)
now = datetime.now(timezone.utc).isoformat()
gates.update(status="PROBE_PASS_RECOVERY_G13_REQUIRED", physical_result=pin(D / "PHYSICAL_RESULT.json"), next_gate="G13", updated_utc=now)
(A / "PROBE_GATE_STATE.json").write_text(json.dumps(gates, indent=2)+"\n", encoding="utf-8")
state_path = Path(r"C:\Dev\A2WC511R_Final\state\CURRENT.json")
state = read(state_path)
state.update(phase="RK03_TRANSITION_PHYSICAL_PASS_RECOVERY_G13_REQUIRED", probe_physical_result="PASS", probe_physical_invocations=1, probe_process_exited=True, probe_cleanup_confirmed=True, probe_physical_result_report=str(D / "PHYSICAL_RESULT.json"), next_action="G13: turn ignition OFF; wait for exactly DONE G13", human_required=["G13"], updated_utc=now)
state_path.write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status": "RK03_TRANSITION_PHYSICAL_PASS", "report": pin(D / "PHYSICAL_RESULT.json"), "manifest": pin(D / "MANIFEST.json"), "cleanup": report["cleanup"], "next_gate": "G13"}))
