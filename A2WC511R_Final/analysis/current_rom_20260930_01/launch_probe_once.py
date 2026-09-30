"""Gated one-shot launcher. Never invoke --run-once before the human commit gate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path(r"C:\Dev\A2WC511R_RK03_TransitionProbe")
SESSION_ID = "RK03_TRANSITION_PROBE_01"
SESSION = REPO / "physical_session" / SESSION_ID
EXE = REPO / "probe/build_a/rk03_transition_probe32.exe"
CONTRACT = HERE / "PROBE_REVIEW_CONTRACT.json"
CERT = HERE / "probe_qualification/QUALIFICATION.json"
GATES = HERE / "PROBE_GATE_STATE.json"
STATE = Path(r"C:\Dev\A2WC511R_Final\state\CURRENT.json")
TOKEN = "PROCEED RK03 TRANSITION PROBE"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, detail="Physical launch precondition failed"):
    if not condition:
        raise RuntimeError(detail)


def write_new(path, obj):
    with Path(path).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def validate_gate(gates, cert_sha):
    require(gates["qualification_sha256"] == cert_sha)
    require(gates["probe_invocation_count"] == 0 and not gates.get("launch_reserved", False))
    rows = gates["completed_pre_probe_gates"]
    require([x["gate"] for x in rows] == ["G06", "G07", "G08", "G09"])
    for row in rows[:3]:
        require(row["reply"] == "DONE " + row["gate"] and row["source"] == "user")
    require(rows[3]["reply"].startswith("TESTMODE G09 ") and rows[3]["source"] == "user")
    require(rows[3]["test_mode_confirmed"] is True)
    auth = gates["commit_authorization"]
    require(auth["reply"] == TOKEN and auth["source"] == "user" and auth["received_utc"])
    require(gates["engine"] == "OFF" and gates["stationary"] is True)
    require(gates["charger"] == "SCHUMACHER_SE_5212A_10A_CHARGING")
    require(gates["adapter"] == "GENUINE_OPENPORT_2_0")
    require(gates["operator_monitors_voltage"] is True)
    require(gates["full_acquisition_allowed"] is False)


def preflight():
    cert_bytes = CERT.read_bytes()
    cert_sha = hashlib.sha256(cert_bytes).hexdigest()
    cert = json.loads(cert_bytes.decode("utf-8-sig"))
    require(cert["status"] == "PASS_OFFLINE_QUALIFIED_TRANSITION_PROBE_ONLY")
    require(Path(cert["physical_executable"]["path"]).resolve() == EXE.resolve())
    require(cert["physical_executable"]["sha256"] == digest(EXE))
    require(cert["review_contract"]["sha256"] == digest(CONTRACT))
    required_pins = {Path(__file__).resolve(), (HERE / "check_clients.ps1").resolve(), EXE.resolve(), CONTRACT.resolve()}
    require(required_pins.issubset({Path(x["path"]).resolve() for x in cert["files"]}), "Required launch controls are absent from qualification pins")
    for row in cert["files"]:
        require(digest(row["path"]) == row["sha256"], row["path"])
    gates = read(GATES)
    validate_gate(gates, cert_sha)
    require(not any((SESSION / n).exists() for n in ["launch.reserved", "invocation.once", "AUTHORIZATION.txt", "native_api.jsonl", "EXECUTION.json", "console.log"]))
    return cert, gates, cert_sha


def wait_for_child(process, record_started):
    """A bookkeeping failure must not orphan an already-started physical child."""
    error = None
    try:
        record_started()
    except BaseException as exc:
        error = repr(exc)
    finally:
        exit_code = process.wait()
    return exit_code, error


def run_once():
    cert, gates, cert_sha = preflight()
    SESSION.mkdir(parents=True, exist_ok=True)
    check_path = SESSION / "PRELAUNCH_CLIENT_CHECK.json"
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "check_clients.ps1"), "-OutputPath", str(check_path)], check=True)
    require(read(check_path)["pass"] is True)
    # Recheck native bytes after the client scan and before reserving launch.
    exe_sha, contract_sha = digest(EXE), digest(CONTRACT)
    require(exe_sha == cert["physical_executable"]["sha256"])
    require(contract_sha == cert["review_contract"]["sha256"])
    require(digest(CERT) == cert_sha, "Qualification changed during prelaunch checks")
    auth = f"{TOKEN}\nSESSION_ID={SESSION_ID}\nEXE_SHA256={exe_sha}\nCONTRACT_SHA256={contract_sha}\n"
    with (SESSION / "AUTHORIZATION.txt").open("x", encoding="ascii", newline="\n") as f:
        f.write(auth)
    with (SESSION / "launch.reserved").open("x", encoding="ascii", newline="\n") as f:
        f.write(f"{SESSION_ID}\n{exe_sha}\n{contract_sha}\n")
    gates.update(launch_reserved=True, launch_reserved_utc=now(), status="SINGLE_LAUNCH_RESERVED_NO_RETRY")
    GATES.write_text(json.dumps(gates, indent=2)+"\n", encoding="utf-8")
    argv = [str(EXE), "--physical-transition-probe", "--session", str(SESSION), "--authorization-file", str(SESSION / "AUTHORIZATION.txt")]
    started = {"session_id": SESSION_ID, "command_argv": argv, "started_utc": now(), "executable_sha256": exe_sha,
               "contract_sha256": contract_sha, "qualification_sha256": cert_sha, "authorization_source": "Exact user commit reply recorded after all four human preparation gates", "retry_allowed": False}
    write_new(SESSION / "EXECUTION_BEGIN.json", started)
    try:
        with (SESSION / "console.log").open("xb") as console:
            process = subprocess.Popen(argv, stdout=console, stderr=subprocess.STDOUT)
            def record_started():
                gates.update(probe_invocation_count=1, process_id=process.pid, status="PROBE_RUNNING_NO_PHYSICAL_STATE_CHANGES")
                GATES.write_text(json.dumps(gates, indent=2)+"\n", encoding="utf-8")
                state = read(STATE)
                state.update(phase="RK03_TRANSITION_PROBE_RUNNING", probe_physical_invocations=1, probe_process_id=process.pid, probe_session=str(SESSION), updated_utc=now())
                STATE.write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
            # The native code has bounded calls and always attempts resource cleanup.
            # Do not automatically terminate or restart a provider-backed process.
            exit_code, bookkeeping_error = wait_for_child(process, record_started)
        result = {**started, "pid": process.pid, "exit_code": exit_code, "exited_utc": now(), "process_exited": True, "bookkeeping_error": bookkeeping_error}
    except Exception as exc:
        result = {**started, "launcher_error": repr(exc), "retry_allowed": False}
        write_new(SESSION / "EXECUTION_LAUNCHER_ERROR.json", result)
        raise
    write_new(SESSION / "EXECUTION.json", result)
    gates.update(status="PROBE_EXITED_RECOVERY_G13_REQUIRED", process_exited=True, exit_code=exit_code, next_gate="G13")
    GATES.write_text(json.dumps(gates, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    if sys.argv[1:] != ["--run-once"]:
        raise SystemExit("Only --run-once is accepted; requires sealed qualification, completed gates and exact user authorization")
    run_once()
