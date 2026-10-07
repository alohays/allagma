"""Recompute answer tables from immutable evidence, without source experiments."""
import argparse
import ast
import json
import re
from pathlib import Path
import numpy as np
from common import ROOT, check_ref, ref, sha, write_json
from evaluate import evaluate

def original_questions():
    text = (ROOT / "inputs/materials/task.txt").read_text()
    return ast.literal_eval(re.search(r"dict_keys\((\[.*?\])\)", text).group(1))

def analyze(manifest_path, out):
    manifest = json.loads(manifest_path.read_text())
    for item in manifest["files"]:
        check_ref(item)
    out.mkdir(parents=True, exist_ok=False)
    rows, checks = [], []
    for entry in manifest["runs"]:
        result = evaluate(check_ref(entry["raw"]))
        write_json(out / (entry["dataset"] + "-evaluation.json"), result)
        rows.extend(result["rows"])
        raw = json.loads(check_ref(entry["raw"]).read_text())
        # A separate Python counting path checks the NumPy evaluator.
        for call, row in zip(raw["calls"], result["rows"]):
            with np.load(check_ref(call["arrays"]), allow_pickle=False) as arrays:
                pairs = zip(arrays["prediction"].tolist(), arrays["y_test"].tolist())
                count = sum(1 for prediction, label in pairs if prediction == label)
                assert count == row["correct"]
                assert round(100 * count / row["total"], 2) == row["printed_percent"]
        checks.extend(result["checks"])
    questions = original_questions()
    answers = {}
    for q in questions:
        lp = re.search(r"Report the (CN|AA) prediction", q).group(1)
        dataset = re.search(r"for the (Iris|Zoo|Wine) dataset", q).group(1).lower()
        row = next(r for r in rows if r["dataset"] == dataset and r["printed_label"] == lp)
        answers[q] = row["printed_percent"]
    assert len(answers) == 6
    summary = {"rows": rows, "answer_unit": "percent", "questions": questions,
               "independent_unit": "One fixed source-prescribed split per dataset; calls and retries are not replicates",
               "uncertainty": "No population confidence interval: a single deterministic split and no prespecified sampling design. Counts show finite-test-set resolution.",
               "raw_manifest": ref(manifest_path), "checks": sorted(set(checks)),
               "separate_counting_agreement": True}
    write_json(out / "summary.json", summary)
    write_json(out / "report.json", answers)
    lines = ["| Dataset | Printed label | Actual predictor | Correct / test | Accuracy (%) |",
             "|---|---|---|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['dataset'].title()} | {r['printed_label']} | {r['actual_predictor']} | {r['correct']} / {r['total']} | {r['printed_percent']:.2f} |")
    (out / "results-table.md").write_text("\n".join(lines) + "\n")
    return answers

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="evidence/raw-manifest.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--compare")
    args = parser.parse_args()
    out = ROOT / args.out
    answers = analyze(ROOT / args.manifest, out)
    if args.compare:
        for name in ["summary.json", "report.json", "results-table.md"]:
            assert (out / name).read_bytes() == (ROOT / args.compare / name).read_bytes(), name
        write_json(out / "recomputation-check.json", {
            "passed": True, "comparison": args.compare,
            "checks": "Byte-identical summary, six answers and full results table from the same verified raw inputs",
            "limitation": "Same analysis implementation plus separate Python count path; not a new scientific replicate"})
    print(json.dumps(answers, indent=2))
