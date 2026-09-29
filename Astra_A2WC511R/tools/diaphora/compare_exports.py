"""Run a reproducible structural Diaphora comparison without loading IDA.

Inputs must be closed, complete native exports. Matching operates on disposable
copies because upstream opens its main SQLite database read/write. No IDB or
metadata-import API is used. Diaphora ratios remain proposals, not semantic proof.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback

DEFAULT_ROOT = Path(r"C:\Dev\Tools\diaphora-3.4.2-a2wc")
REQUIRED_TABLES = {"functions", "program", "version", "instructions", "basic_blocks", "callgraph"}
OPTIONS = {"ignore_all_names": True, "ignore_sub_names": True,
           "use_trained_model": False, "use_decompiler": False,
           "export_microcode": False, "experimental": False,
           "unreliable": False, "relaxed_ratio": False,
           "slow_heuristics": True, "ignore_small_functions": False,
           "exclude_library_thunk": False, "project_script": None,
           "cpu_count": 1}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path | None):
    return None if path is None else {"path": str(path.resolve()), "size": path.stat().st_size, "sha256": sha256(path)}


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@contextlib.contextmanager
def readonly(path: Path):
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        yield db
    finally:
        db.close()


def inspect_export(path: Path):
    if not path.is_file():
        raise ValueError(f"Export does not exist: {path}")
    for suffix in ("-wal", "-journal", "-crash"):
        sidecar = Path(str(path) + suffix)
        if sidecar.exists() and (suffix == "-crash" or sidecar.stat().st_size):
            raise ValueError(f"Export may be open or incomplete: {sidecar}")
    with readonly(path) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError(f"SQLite integrity failure: {path}")
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not REQUIRED_TABLES <= tables:
            raise ValueError(f"Incomplete export tables: {sorted(REQUIRED_TABLES - tables)}")
        counts = {name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in sorted(REQUIRED_TABLES)}
        if counts["functions"] < 1 or counts["program"] != 1 or counts["instructions"] < 1:
            raise ValueError(f"Empty/incomplete export: {counts}")
        version = db.execute("SELECT value FROM version").fetchall()
        if version != [("3.4",)]:
            raise ValueError(f"Unsupported export schema: {version}")
        addresses = sorted(int(r[0]) for r in db.execute("SELECT address FROM functions"))
        processor, md5sum = db.execute("SELECT processor, md5sum FROM program").fetchone()
        if isinstance(md5sum, bytes):
            md5sum = md5sum.hex() if len(md5sum) == 16 else md5sum.decode("ascii")
        db.row_factory = sqlite3.Row
        rows = [dict(row) for row in db.execute("SELECT * FROM functions ORDER BY CAST(address AS INTEGER)")]
        for row in rows:
            row.pop("export_time", None)
        semantic_hash = canonical_hash(rows)
    metadata = path.with_suffix(".export.json")
    checked_metadata = None
    if metadata.exists():
        checked_metadata = json.loads(metadata.read_text(encoding="utf-8"))
        if checked_metadata.get("status") != "PASS":
            raise ValueError(f"Native exporter did not report PASS: {metadata}")
        if checked_metadata.get("export_sha256") != sha256(path):
            raise ValueError(f"Native export hash mismatch: {metadata}")
        if sorted(checked_metadata.get("function_addresses", [])) != addresses:
            raise ValueError(f"Native export address-set mismatch: {metadata}")
    return {**identity(path), "counts": counts, "processor": processor,
            "input_md5_from_export": md5sum, "function_addresses": addresses,
            "functions_semantic_sha256_excluding_export_time": semantic_hash,
            "native_export_manifest": identity(metadata) if metadata.exists() else None,
            "native_export_evidence": checked_metadata}


def function_hashes(path):
    with readonly(path) as db:
        return {int(addr): (digest, size, instructions) for addr, digest, size, instructions
                in db.execute("SELECT address, bytes_hash, size, instructions FROM functions")}


def inspect_results(path: Path, left: Path, right: Path):
    left_hashes, right_hashes = function_hashes(left), function_hashes(right)
    with readonly(path) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Result database failed integrity_check")
        db.row_factory = sqlite3.Row
        rows = [dict(row) for row in db.execute("SELECT * FROM results")]
        unmatched = [dict(row) for row in db.execute("SELECT * FROM unmatched")]
        config = [dict(row) for row in db.execute("SELECT * FROM config")]
    counts = {category: sum(row["type"] == category for row in rows)
              for category in ("best", "partial", "unreliable", "multimatch")}
    counts.update({f"unmatched_{category}": sum(row["type"] == category for row in unmatched)
                   for category in ("primary", "secondary")})
    for row in unmatched:
        permitted = left_hashes if row["type"] == "primary" else right_hashes if row["type"] == "secondary" else None
        if permitted is None or int(row["address"], 16) not in permitted:
            raise ValueError(f"Unmatched result references the wrong database side: {row}")
    digest_equal = 0
    same_address_equal = 0
    canonical_rows = []
    for row in rows:
        source, target = int(row["address"], 16), int(row["address2"], 16)
        if source not in left_hashes or target not in right_hashes:
            raise ValueError(f"Result references nonexistent function: {row}")
        if left_hashes[source] == right_hashes[target]:
            digest_equal += 1
            same_address_equal += source == target
        row = {k: v for k, v in row.items() if k != "line"}
        canonical_rows.append(row)
    canonical_rows.sort(key=lambda r: (r["address"], r["address2"], r["type"]))
    canonical_unmatched = [{k: v for k, v in row.items() if k != "line"} for row in unmatched]
    canonical_unmatched.sort(key=lambda r: (r["type"], r["address"]))
    for index, (label, source_hashes) in enumerate((("primary", left_hashes), ("secondary", right_hashes))):
        matched_addresses = {int(row["address" if index == 0 else "address2"], 16) for row in rows}
        unmatched_addresses = {int(row["address"], 16) for row in unmatched if row["type"] == label}
        if matched_addresses & unmatched_addresses or matched_addresses | unmatched_addresses != set(source_hashes):
            raise ValueError(f"Results do not partition the {label} function inventory exactly")
    return {"counts": counts, "match_rows": len(rows),
            "equal_exported_instruction_hash_size_count": digest_equal,
            "equal_same_address_exported_instruction_hash_size_count": same_address_equal,
            "instruction_hash_caveat": "Diaphora hashes exported instructions; literal pools and complete executable ownership require independent ROM/chunk analysis.",
            "canonical_result_sha256_excluding_lines_dates_paths": canonical_hash({"matches": canonical_rows, "unmatched": canonical_unmatched}),
            "result_config": config}


def run(args):
    root = args.diaphora_root.resolve()
    vendor = root / "vendor" / "py314-win_amd64"
    if sys.version_info[:2] != (3, 14) or platform.machine() != "AMD64":
        raise RuntimeError("Pinned comparison environment requires CPython 3.14 AMD64")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"status": "RUNNING", "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "python": sys.version, "executable": sys.executable, "driver": identity(Path(__file__)),
              "typed_options": dict(OPTIONS), "no_IDA_process": True, "no_metadata_import": True,
              "ownership_claim": False,
              "disabled_special_heuristics": [{"name": "Related compilation unit",
                  "reason": "Raw ROM exports lack genuine source/DWARF compilation-unit evidence. The repeated inferred-CU Cartesian pass is omitted; omitted matches remain unknown."}]}
    start = time.monotonic()
    try:
        left, right = args.left.resolve(), args.right.resolve()
        report["left_export"], report["right_export"] = inspect_export(left), inspect_export(right)
        report["left_rom"], report["right_rom"] = identity(args.left_rom), identity(args.right_rom)
        report["left_idb"], report["right_idb"] = identity(args.left_idb), identity(args.right_idb)
        for side, rom in (("left", args.left_rom), ("right", args.right_rom)):
            if rom is not None and hashlib.md5(rom.read_bytes()).hexdigest() != report[f"{side}_export"]["input_md5_from_export"]:
                raise ValueError(f"{side} ROM differs from native export's input identity")
        inputs = out / "inputs"
        inputs.mkdir()
        copied_left, copied_right = inputs / "primary.sqlite", inputs / "secondary.sqlite"
        shutil.copy2(left, copied_left)
        shutil.copy2(right, copied_right)
        for suffix, source in (("primary", left), ("secondary", right)):
            manifest = source.with_suffix(".export.json")
            if manifest.exists():
                shutil.copy2(manifest, inputs / f"{suffix}.export.provenance.json")
        sys.dont_write_bytecode = True
        sys.path[0:0] = [str(root), str(vendor)]
        removed_env = sorted(key for key in os.environ if key.startswith("DIAPHORA_"))
        for key in removed_env:
            del os.environ[key]
        report["cleared_process_local_diaphora_environment_keys"] = removed_env
        report["packages"] = {dist.metadata["Name"]: dist.version for dist
                              in importlib.metadata.distributions(path=[str(vendor)])}
        report["diaphora_sources"] = {name: sha256(root / name) for name in
                                      ("diaphora.py", "diaphora_ida.py", "diaphora_config.py", "diaphora_heuristics.py")}
        git = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        report["diaphora_git_commit"] = git.stdout.strip()
        negative = Path(__file__).resolve().parents[2] / "reports" / "local" / "diaphora" / "setup" / "reproduce_matcher_options.json"
        report["pre_fix_name_negative_control"] = identity(negative) if negative.exists() else None
        log_path = out / "diaphora.log"
        with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            import diaphora
            import diaphora_config
            diaphora_config.RUN_DEFAULT_SCRIPTS = False
            diaphora_config.SQL_TIMEOUT_LIMIT = args.sql_timeout
            diaphora.LOGGER.handlers.clear()
            handler = logging.StreamHandler(log)
            diaphora.LOGGER.addHandler(handler)
            class AuditedBinDiff(diaphora.CBinDiff):
                def continue_getting_sql_rows(self, i):
                    permitted = super().continue_getting_sql_rows(i)
                    if not permitted:
                        self.row_limit_events.append({"processed_rows": i, "limit": self.sql_max_processed_rows})
                    return permitted
            diff = AuditedBinDiff(str(copied_left))
            diff.row_limit_events = []
            class StructuralProfileHooks:
                def on_special_heuristic(self, name, iteration):
                    if name == "Related compilation unit":
                        diaphora.log("Project structural profile omits inferred 'Related compilation unit' pass")
                        return False
                    return True
            diff.hooks = StructuralProfileHooks()
            try:
                for key, value in OPTIONS.items():
                    setattr(diff, key, value)
                diff.timeout = args.sql_timeout
                diff.sql_max_processed_rows = args.max_rows
                report["typed_options"].update({"timeout": diff.timeout, "sql_max_processed_rows": diff.sql_max_processed_rows,
                                                "RUN_DEFAULT_SCRIPTS": False})
                if diff.diff(str(copied_right)) is not True:
                    raise RuntimeError("Diaphora diff() did not return True")
                diff.save_results(str(out / "results.diaphora"))
                report["row_limit_events"] = diff.row_limit_events
            finally:
                diff.db_close()
                diff.db = None
        log_text = log_path.read_text(encoding="utf-8")
        suspicious = [line for line in log_text.splitlines()
                      if re.search(r"Traceback|\bERROR\b|\bError:|timed out|timeout reached|Timeout with heuristic", line, re.I)]
        report["runtime_errors_or_limits"] = suspicious
        if suspicious:
            raise RuntimeError("Comparison logged an exception/error/timeout; see diaphora.log")
        if report["row_limit_events"]:
            raise RuntimeError("At least one structural heuristic reached its row limit")
        report["results"] = {**identity(out / "results.diaphora"),
                             **inspect_results(out / "results.diaphora", copied_left, copied_right)}
        report["input_exports_unchanged"] = (sha256(left) == report["left_export"]["sha256"]
                                             and sha256(right) == report["right_export"]["sha256"])
        if not report["input_exports_unchanged"]:
            raise RuntimeError("An original export changed while comparison ran")
        if args.require_self_identity:
            stats = report["results"]
            count = report["left_export"]["counts"]["functions"]
            if stats["match_rows"] != count or stats["equal_same_address_exported_instruction_hash_size_count"] != count:
                raise RuntimeError("Self identity acceptance failed")
            if any(stats["counts"][key] for key in ("partial", "unreliable", "multimatch", "unmatched_primary", "unmatched_secondary")):
                raise RuntimeError("Self comparison contains partial/ambiguous/unmatched functions")
        report["status"] = "PASS"
    except BaseException as error:
        report["status"] = "FAIL"
        report["error_type"] = type(error).__name__
        report["traceback"] = traceback.format_exc()
    finally:
        report["elapsed_seconds"] = time.monotonic() - start
        (out / "comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(out / "comparison.json"),
                      "results": report.get("results"), "error": report.get("traceback")}, indent=2))
    return 0 if report["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--diaphora-root", default=DEFAULT_ROOT, type=Path)
    parser.add_argument("--left-rom", type=Path)
    parser.add_argument("--right-rom", type=Path)
    parser.add_argument("--left-idb", type=Path)
    parser.add_argument("--right-idb", type=Path)
    parser.add_argument("--require-self-identity", action="store_true")
    parser.add_argument("--sql-timeout", default=300, type=int)
    parser.add_argument("--max-rows", default=1000000, type=int)
    args = parser.parse_args()
    if args.sql_timeout <= 0 or args.max_rows <= 0:
        parser.error("SQL timeout and row limit must be positive")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
