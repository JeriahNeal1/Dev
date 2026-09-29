"""One-command native export and structural comparison acceptance, no HCLI."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform
import shutil
import sqlite3
import subprocess
import sys
import traceback
import uuid

TOOLS = Path(__file__).resolve().parent
PROJECT = TOOLS.parents[1]
WORK = PROJECT / "work" / "diaphora"
REPORTS = PROJECT / "reports" / "local" / "diaphora"
IDA = Path(r"C:\Program Files\IDA Professional 9.4\ida.exe")
TOOL_ROOT = Path(r"C:\Dev\Tools\diaphora-3.4.2-a2wc")


def identity(path):
    return {"path": str(path.resolve()), "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def run_command(command, log, cwd, expected=0):
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=240)
    log.write_text(done.stdout + done.stderr, encoding="utf-8")
    record = {"command": command, "cwd": str(cwd), "exit_code": done.returncode,
              "expected_exit_code": expected, "log": identity(log)}
    if done.returncode != expected:
        raise RuntimeError(f"Expected exit {expected}, got {done.returncode}: {log}")
    return record


def native(run_root, label, source, script, output=None, export=None, config=None):
    command = [sys.executable, str(TOOLS / "native_job.py"), "--input", str(source),
               "--script", str(TOOLS / script), "--label", label, "--wait"]
    if output is not None:
        command += ["--new-output", str(output)]
    if export is not None:
        command += ["--export", str(export), "--no-analysis"]
    if config is not None:
        command += ["--config", str(config), "--no-analysis"]
    result = run_command(command, run_root / f"{label}.launcher.log", run_root / "unrelated working directory")
    result["native_job"] = str(REPORTS / "jobs" / label)
    return result


def compare(run_root, label, left, right, rom=None, left_idb=None, right_idb=None, expected=0):
    output = run_root / label
    command = [sys.executable, str(TOOLS / "compare_exports.py"), str(left), str(right), "--output-dir", str(output)]
    if expected == 0:
        command += ["--require-self-identity"]
    if rom is not None:
        command += ["--left-rom", str(rom), "--right-rom", str(rom)]
    if left_idb is not None:
        command += ["--left-idb", str(left_idb), "--right-idb", str(right_idb)]
    launch = run_command(command, run_root / f"{label}.launcher.log", run_root / "unrelated working directory", expected)
    evidence = json.loads((output / "comparison.json").read_text())
    assert evidence["status"] == ("PASS" if expected == 0 else "FAIL"), evidence
    return {"launch": launch, "report": identity(output / "comparison.json"), "evidence": evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", help="Optional new alphanumeric/underscore label; otherwise a unique timestamp is used")
    args = parser.parse_args()
    label = args.label or (datetime.now(timezone.utc).strftime("smoke_%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:6])
    if not all(c.isalnum() or c in "_-" for c in label):
        parser.error("Label must contain only letters, digits, underscores or hyphens")
    run_root = WORK / "smoke runs" / label
    run_root.mkdir(parents=True, exist_ok=False)
    unrelated = run_root / "unrelated working directory"
    unrelated.mkdir()
    result = {"status": "RUNNING", "created_utc": datetime.now(timezone.utc).isoformat(),
              "caller_cwd": str(Path.cwd()), "run_directory": str(run_root),
              "scope": "Three synthetic SH leaf functions only; no ROM patch or metadata import.",
              "HCLI_used": False, "global_configuration_changed": False,
              "authoritative_IDB_opened": False, "hardware_used": False,
              "python": sys.version, "commands": []}
    try:
        assert sys.version_info[:2] == (3, 14) and platform.machine() == "AMD64"
        assert IDA.is_file() and (TOOL_ROOT / "vendor" / "py314-win_amd64").is_dir()
        isolated = WORK / "ida_user_isolated"
        assert (isolated / "plugins" / "diaphora_config.py").is_file()
        assert (isolated / "plugins" / "diaphora_plugin.py").is_file()
        result["scoped_IDAUSR"] = str(isolated)
        result["IDA_executable"] = identity(IDA)
        version = subprocess.run(["powershell", "-NoProfile", "-Command",
            "(Get-Item -LiteralPath 'C:\\Program Files\\IDA Professional 9.4\\ida.exe').VersionInfo.FileVersion"],
            capture_output=True, text=True, check=True)
        result["IDA_PE_file_version"] = version.stdout.strip()
        result["validated_native_profile"] = {"IDA_kernel": "9.4", "IDAPython": "9.4.0",
            "Python": "3.14.7 AMD64", "native_PE": "9.4.260610.6c3b13fe",
            "caveat": "This installed native profile is measured separately from the older authoritative IDB's producer and any other IDA process. Re-probe after runtime upgrades."}
        result["scripts"] = {name: identity(TOOLS / name) for name in
            ("smoke.py", "native_job.py", "prepare_tiny.py", "export_native.py", "compare_exports.py", "open_results_native.py", "make_unmatched_fixture.py")}
        rom = run_root / "tiny identical input.bin"
        data = bytearray(b"\xff" * 0x30)
        for address in (0, 0x10, 0x20):
            data[address:address + 6] = bytes.fromhex("E0" + f"{address // 16 + 1:02X}" + "000B0009")
        rom.write_bytes(data)
        result["synthetic_input"] = identity(rom)
        exports, idbs = [], []
        for index in (1, 2):
            idb = run_root / f"independent analysis {index}.i64"
            export = run_root / f"independent export {index}.sqlite"
            result["commands"].append(native(run_root, f"{label}_prepare_{index}", rom, "prepare_tiny.py", output=idb))
            result["commands"].append(native(run_root, f"{label}_export_{index}", idb, "export_native.py", export=export))
            evidence = json.loads(export.with_suffix(".export.json").read_text())
            assert evidence["status"] == "PASS" and evidence["function_addresses"] == [0, 16, 32]
            assert evidence["counts"]["functions"] == 3
            exports.append(export)
            idbs.append(idb)
        result["exports"] = [identity(path) for path in exports]
        result["IDBs"] = [identity(path) for path in idbs]
        result["self_compare"] = compare(run_root, "self_compare", exports[0], exports[0], rom, idbs[0], idbs[0])
        result["independent_analysis_compare"] = compare(run_root, "independent_analysis_compare", exports[0], exports[1], rom, idbs[0], idbs[1])
        result["clean_process_repeat"] = compare(run_root, "clean_process_repeat", exports[0], exports[0], rom, idbs[0], idbs[0])
        keys = ("self_compare", "independent_analysis_compare", "clean_process_repeat")
        canonical = [result[key]["evidence"]["results"]["canonical_result_sha256_excluding_lines_dates_paths"] for key in keys]
        assert len(set(canonical)) == 1, canonical
        result["reproducible_canonical_result_sha256"] = canonical[0]
        first = result["independent_analysis_compare"]["evidence"]
        result["analysis_function_rows_deterministic_except_export_time"] = (first["left_export"]["functions_semantic_sha256_excluding_export_time"]
            == first["right_export"]["functions_semantic_sha256_excluding_export_time"])
        assert result["analysis_function_rows_deterministic_except_export_time"]
        view = run_root / "native result view"
        view.mkdir()
        original_results = run_root / "self_compare" / "results.diaphora"
        preserved = {str(p): identity(p) for p in (original_results, exports[0], exports[1], idbs[0])}
        view_idb, view_results = view / "disposable view.i64", view / "results.diaphora"
        view_left, view_right = view / "primary.sqlite", view / "secondary.sqlite"
        for original, copied in ((idbs[0], view_idb), (original_results, view_results),
                                 (exports[0], view_left), (exports[0], view_right)):
            shutil.copy2(original, copied)
        db = sqlite3.connect(view_results)
        with db:
            db.execute("UPDATE config SET main_db=?, diff_db=?", (str(view_left), str(view_right)))
        db.close()
        job_config = view / "job.json"
        job_config.write_text(json.dumps({"results": str(view_results), "report": str(view / "NATIVE_RESULT_OPEN.json")}, indent=2))
        result["commands"].append(native(run_root, f"{label}_native_view", view_idb, "open_results_native.py", config=job_config))
        result["native_result_open"] = json.loads((view / "NATIVE_RESULT_OPEN.json").read_text())
        assert result["native_result_open"]["status"] == "PASS"
        assert all(identity(Path(p))["sha256"] == old["sha256"] for p, old in preserved.items())
        result["native_view_original_artifacts_unchanged"] = True
        asym = run_root / "synthetic unmatched view"
        result["commands"].append(run_command([sys.executable, str(TOOLS / "make_unmatched_fixture.py"), str(asym)],
            run_root / "make_unmatched_fixture.log", unrelated))
        asym_idb = asym / "disposable unmatched view.i64"
        shutil.copy2(idbs[0], asym_idb)
        asym_job = asym / "job.json"
        asym_job.write_text(json.dumps({"results": str(asym / "results.diaphora"),
            "report": str(asym / "NATIVE_UNMATCHED_OPEN.json"),
            "expected_match_counts": {"best": 0, "partial": 0, "unreliable": 0, "multimatch": 0},
            "expected_unmatched": {"primary": [0, 16], "secondary": [32]}}, indent=2))
        result["commands"].append(native(run_root, f"{label}_native_unmatched", asym_idb, "open_results_native.py", config=asym_job))
        result["native_unmatched_role_regression"] = json.loads((asym / "NATIVE_UNMATCHED_OPEN.json").read_text())
        assert result["native_unmatched_role_regression"]["status"] == "PASS"
        wrong = run_root / "wrong format.sqlite"
        wrong.write_bytes(b"not a SQLite export\n")
        empty = run_root / "empty export.sqlite"
        db = sqlite3.connect(empty)
        db.close()
        result["wrong_format_negative"] = compare(run_root, "wrong_format_negative", wrong, exports[0], expected=1)
        result["empty_export_negative"] = compare(run_root, "empty_export_negative", empty, exports[0], expected=1)
        for key in ("wrong_format_negative", "empty_export_negative"):
            assert result[key]["evidence"]["status"] == "FAIL"
        result["status"] = "PASS"
    except BaseException as error:
        result["status"] = "FAIL"
        result["error_type"] = type(error).__name__
        result["traceback"] = traceback.format_exc()
    path = run_root / "SMOKE_RESULT.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(path), "error": result.get("traceback")}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
