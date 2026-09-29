"""Create a clearly synthetic asymmetric fixture for native chooser-role testing."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(r"C:\Dev\Tools\diaphora-3.4.2-a2wc")
sys.dont_write_bytecode = True
sys.path[0:0] = [str(ROOT), str(ROOT / "vendor" / "py314-win_amd64")]
import diaphora

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
left, right = args.output / "primary.sqlite", args.output / "secondary.sqlite"
for path, rows in ((left, [("synthetic_primary_zero", "0"), ("synthetic_primary_sixteen", "16")]),
                   (right, [("synthetic_secondary_thirtytwo", "32")])):
    diff = diaphora.CBinDiff(str(path))
    diff.db.executemany("INSERT INTO functions(name,address) VALUES (?,?)", rows)
    diff.db.commit()
    diff.db_close()
    diff.db = None
diff = diaphora.CBinDiff(str(left))
diff.attach_database(str(right))
diff.last_diff_db = str(right)
diff.find_unmatched()
assert [int(row[1], 16) for row in diff.unmatched_primary.items] == [0, 16]
assert [int(row[1], 16) for row in diff.unmatched_second.items] == [32]
diff.save_results(str(args.output / "results.diaphora"))
diff.db_close()
diff.db = None
(args.output / "SYNTHETIC_FIXTURE.json").write_text(json.dumps({"scope": "Only tests result labels and native chooser side semantics. This is not a ROM export or comparative reverse-engineering evidence.",
    "expected_primary": [0, 16], "expected_secondary": [32]}, indent=2) + "\n")
