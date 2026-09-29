"""Open real Diaphora result choosers on a disposable native IDB; never import."""
from pathlib import Path
import hashlib
import json
import os
import sys
import traceback
import ida_bytes
import ida_funcs
import ida_kernwin
import ida_pro
import idautils
import idc
from export_native import bootstrap

WORK = Path(r"C:\Dev\Astra_A2WC511R\work\diaphora").resolve()


def snapshot():
    return {"bytes": ida_bytes.get_bytes(0, 0x30).hex(),
        "functions": [{"address": ea, "name": idc.get_func_name(ea),
                       "comment": ida_funcs.get_func_cmt(ida_funcs.get_func(ea), False),
                       "repeatable_comment": ida_funcs.get_func_cmt(ida_funcs.get_func(ea), True)}
                      for ea in idautils.Functions()]}


def run(job):
    idb = Path(idc.get_idb_path()).resolve()
    assert idb.is_relative_to(WORK), "Only a disposable work/diaphora IDB is permitted"
    results = Path(job["results"]).resolve()
    assert results.is_relative_to(WORK)
    before = snapshot()
    assert [row["address"] for row in before["functions"]] == [0, 16, 32]
    bootstrap()
    import diaphora_ida
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    assert app is not None, "Native GUI application is required for real chooser acceptance"
    diff = diaphora_ida.CIDABinDiff(":memory:")
    assert diff.load_results(str(results)) is True
    app.processEvents()
    counts = {name: len(getattr(diff, name + "_chooser").items)
              for name in ("best", "partial", "unreliable", "multimatch")}
    expected = job.get("expected_match_counts", {"best": 3, "partial": 0, "unreliable": 0, "multimatch": 0})
    assert counts == expected, counts
    titles = []
    for chooser in (diff.best_chooser, diff.unmatched_primary, diff.unmatched_second):
        if chooser.items:
            widget = chooser.GetWidget()
            assert widget is not None, "Actual native chooser widget was not created"
            title = ida_kernwin.get_widget_title(widget)
            assert title == chooser.title, title
            titles.append(title)
    unmatched = {"primary": {"addresses": [int(row[1], 16) for row in diff.unmatched_primary.items],
                              "is_primary": diff.unmatched_primary.primary, "title": diff.unmatched_primary.title},
                 "secondary": {"addresses": [int(row[1], 16) for row in diff.unmatched_second.items],
                                "is_primary": diff.unmatched_second.primary, "title": diff.unmatched_second.title}}
    assert unmatched["primary"]["is_primary"] is True
    assert unmatched["secondary"]["is_primary"] is False
    if "expected_unmatched" in job:
        for side, addresses in job["expected_unmatched"].items():
            assert unmatched[side]["addresses"] == addresses, unmatched
    after = snapshot()
    assert before == after, "Displaying results changed analysis metadata or bytes"
    report = {"status": "PASS", "IDB": str(idb), "result_database": str(results),
              "result_sha256": hashlib.sha256(results.read_bytes()).hexdigest(),
              "chooser_counts": counts, "actual_widget_titles": titles, "unmatched": unmatched,
              "QApplication_class": type(app).__name__, "show_choosers_monkeypatched": False,
              "bytes_and_function_metadata_unchanged": True, "snapshot": before,
              "IDA_version": ida_kernwin.get_kernel_version(), "python": sys.version,
              "IDAPython_version": str(getattr(sys.modules.get("__main__"), "IDAPYTHON_VERSION", None)),
              "import_APIs_called": False, "authoritative_IDB_opened": False}
    for name in ("best", "partial", "unreliable", "multimatch"):
        getattr(diff, name + "_chooser").Close()
    diff.unmatched_primary.Close()
    diff.unmatched_second.Close()
    diff.db_close()
    diff.db = None
    return report


if __name__ == "__main__":
    job = json.loads(Path(os.environ["A2WC_DIAPHORA_JOB"]).read_text())
    report_path = Path(job["report"])
    code = 0
    try:
        result = run(job)
    except BaseException as error:
        result = {"status": "FAIL", "error_type": type(error).__name__, "traceback": traceback.format_exc(),
                  "sys_version": sys.version, "sys_path": sys.path}
        traceback.print_exc()
        code = 1
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    ida_pro.qexit(code)
