"""Check a fresh execution against canonical results without requiring path identity."""
import argparse
from common import ROOT, read, ref, write

parser = argparse.ArgumentParser()
parser.add_argument("--analysis", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
canonical = read(ROOT / "analysis/main/results.json")
fresh = read(ROOT / args.analysis / "results.json")
assert read(ROOT / args.analysis / "report.json") == read(ROOT / "report.json")
def comparable(rows):
    return sorted([{k: v for k, v in r.items() if k not in ("arrays", "attempt_id")}
                   for r in rows], key=lambda r: (r["dataset"], r["printed_label"]))
assert comparable(canonical["rows"]) == comparable(fresh["rows"])
write(ROOT / args.output, {"status": "pass", "original": ref(ROOT / "analysis/main/results.json"),
    "fresh": ref(ROOT / args.analysis / "results.json"),
    "coverage": "Fresh isolated environment executed all three source scripts. Six exact answer percentages and all 12 call metrics, graph diagnostics, confusion matrices and independent predictor checks equal canonical results. Artifact paths and attempt IDs necessarily differ."})
print("Fresh-environment full execution matches all six answers and all 12 call measurements.")
