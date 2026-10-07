"""Recompute all numbers using only immutable raw evidence; no experiment imports."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def questions(root):
    return ast.literal_eval(re.search(r"dict_keys\((\[.*?\])\)", (root / "inputs/task.txt").read_text()).group(1))


def wilson(correct, total):
    z = 1.959963984540054
    p = correct / total
    denominator = 1 + z*z / total
    centre = (p + z*z / (2*total)) / denominator
    width = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    return [100*(centre-width), 100*(centre+width)]


def derive(root, manifest):
    for ref in manifest["raw"]:
        assert sha(root / ref["path"]) == ref["sha256"], ref["path"]
    assert len(manifest["raw"]) == 1, "One fixed split is the target; repeated labels are not replicates."
    raw = json.loads((root / manifest["raw"][0]["path"]).read_text())
    rows = []
    for name in ["iris", "zoo", "wine"]:
        item = raw["datasets"][name]
        printed = re.findall(r"\(λ=(\w+)\) = ([0-9.]+)%", item["stdout"])
        assert [x[0] for x in printed] == ["CN", "AA", "RA", "CS"]
        assert len(item["calls"]) == 4
        for (label, value), call in zip(printed, item["calls"]):
            assert len(call["prediction"]) == len(item["y_test"])
            correct = sum(p == y for p, y in zip(call["prediction"], item["y_test"]))
            total = len(item["y_test"])
            score = round(100 * correct / total, 2)
            assert score == float(value)
            rows.append({"dataset": name.title(), "printed_label": label,
                         "actual_predictor": call["actual_predictor"], "correct": correct,
                         "n_test": total, "accuracy_percent": score,
                         "wilson_95_percent": wilson(correct, total)})
    answers = {}
    for question in questions(root):
        name = next(n for n in ["Iris", "Zoo", "Wine"] if n in question)
        label = "CN" if " CN " in question else "AA"
        answers[question] = next(row["accuracy_percent"] for row in rows
                                 if row["dataset"] == name and row["printed_label"] == label)
    return {"rows": rows, "answers": answers,
            "units": "percent accuracy (0 to 100)",
            "interpretation": "Answers follow original printed labels. Iris and Zoo CN/AA labels actually execute CS.",
            "uncertainty": "Wilson 95% binomial intervals are descriptive conditional on this single split. Transductive predictions are dependent; these intervals are not validated coverage estimates, split variability or evidence of algorithm superiority."}


def write_analysis(root, manifest_path, output):
    output.mkdir(parents=True, exist_ok=False)
    result = derive(root, json.loads(manifest_path.read_text()))
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (output / "report.json").write_text(json.dumps(result["answers"], indent=2) + "\n")
    lines = ["| Dataset | Printed label | Executed predictor | Correct / test | Accuracy | Descriptive Wilson 95% |",
             "|---|---|---|---|---|---|"]
    for row in result["rows"]:
        low, high = row["wilson_95_percent"]
        lines.append(f"| {row['dataset']} | {row['printed_label']} | {row['actual_predictor']} | {row['correct']} / {row['n_test']} | {row['accuracy_percent']:.2f}% | {low:.2f}–{high:.2f}% |")
    (output / "table.md").write_text("\n".join(lines) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_analysis(args.root.resolve(), args.manifest.resolve(), args.output.resolve())
