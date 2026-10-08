"""Recompute original printed answers and independently check retained predictions.

Does not import the capsule, sklearn, pandas or networkx; never reconstructs kNN
or trains a model. Independent link scores use only retained graph edges.
"""
import argparse
import ast
import math
import re
import numpy as np
from common import ROOT, read, ref, verify_refs, write

LINE = re.compile(r"^Prediction Accuracy for (Iris|Zoo|Wine) Dataset \(λ=(CN|AA|RA|CS)\) = ([0-9.]+)%$", re.M)


def questions():
    text = (ROOT / "inputs/materials/task.txt").read_text()
    return ast.literal_eval(text.split("dict_keys(", 1)[1].split(").", 1)[0])


def independent_scores(edges, n, m, c, predictor):
    neighbors = [set() for _ in range(n + m + c)]
    for left, right in edges.tolist():
        neighbors[left].add(right)
        neighbors[right].add(left)
    # Match NetworkX degree for the rare self-loop; a self-loop contributes two.
    degrees = [len(adj) + int(i in adj) for i, adj in enumerate(neighbors)]
    scores = np.zeros((m, c))
    for row, test in enumerate(range(n, n + m)):
        for col, cls in enumerate(range(n + m, n + m + c)):
            common = (neighbors[test] & neighbors[cls]) - {test, cls}
            if predictor == "CN":
                score = len(common)
            elif predictor == "AA":
                score = sum(1 / (math.log(degrees[node]) + 1e-9) for node in sorted(common))
            elif predictor == "RA":
                score = sum(1 / degrees[node] for node in sorted(common))
            elif predictor == "CS":
                score = 0.0
                for node in sorted(common):
                    d1 = degrees[node] - len((neighbors[node] & neighbors[cls]) - {node, cls})
                    d2 = degrees[node] - len((neighbors[node] & neighbors[test]) - {node, test})
                    assert d1 > 0 and d2 > 0
                    score += 1 / d1 + 1 / d2
            else:
                raise ValueError(predictor)
            scores[row, col] = score
    return scores


def accuracy(prediction, target):
    correct = int(np.count_nonzero(prediction == target))
    total = len(target)
    return correct, total, round(100 * float(np.mean(prediction == target)), 2)


def evaluate_raw(manifest):
    verify_refs(manifest["files"])
    rows = []
    seen = set()
    for run in manifest["runs"]:
        dataset = run["dataset"]
        assert dataset not in seen
        seen.add(dataset)
        folder = ROOT / run["directory"]
        completion = read(folder / "completion.json")
        assert completion["status"] == "completed"
        verify_refs([completion[k] for k in ("stdout", "stderr", "call_manifest")])
        lines = LINE.findall((folder / "stdout.txt").read_text())
        assert len(lines) == 4
        calls = read(folder / "calls.json")
        assert len(calls) == 4
        for call, (printed_dataset, label, printed) in zip(calls, lines):
            assert printed_dataset.lower() == dataset and label == call["printed_label"]
            verify_refs([call["arrays"], call["source"]])
            with np.load(ROOT / call["arrays"]["path"], allow_pickle=False) as a:
                n, m, c = map(int, a["node_counts"])
                assert n + m == len(a["full_data"])
                assert len(a["prediction"]) == len(a["y_test"]) == m
                correct, total, percent = accuracy(a["prediction"], a["y_test"])
                assert float(printed) == percent
                scores = independent_scores(a["graph_edges"], n, m, c, call["executed_predictor"])
                alternative = np.argmax(scores, axis=1)
                assert np.array_equal(alternative, a["prediction"]), (dataset, label, "independent predictions")
                confusion = np.zeros((c, c), dtype=np.int64)
                for actual, predicted in zip(a["y_test"], a["prediction"]):
                    confusion[actual, predicted] += 1
                rows.append({"dataset": dataset, "printed_label": label,
                    "executed_predictor": call["executed_predictor"], "correct": correct,
                    "test_n": total, "train_n": n, "classes": c,
                    "accuracy_percent": percent, "accuracy": correct / total,
                    "k": call["k"], "metric": call["similarity"],
                    "graph_edges": len(a["graph_edges"]),
                    "self_loops": int(np.count_nonzero(a["graph_edges"][:, 0] == a["graph_edges"][:, 1])),
                    "confusion_matrix": confusion.tolist(),
                    "prediction_ties": int(np.count_nonzero((scores == scores.max(axis=1, keepdims=True)).sum(axis=1) > 1)),
                    "independent_graph_predictions_match": True,
                    "attempt_id": run["attempt_id"], "arrays": call["arrays"]})
    assert seen == {"iris", "zoo", "wine"}
    report = {}
    for q in questions():
        dataset = next(d for d in ("iris", "zoo", "wine") if d.capitalize() in q)
        label = "CN" if " CN " in q else "AA"
        matches = [r for r in rows if r["dataset"] == dataset and r["printed_label"] == label]
        assert len(matches) == 1
        report[q] = matches[0]["accuracy_percent"]
    assert len(report) == 6
    return rows, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="evidence/raw-manifest.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--compare")
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=False)
    manifest = read(ROOT / args.manifest)
    rows, report = evaluate_raw(manifest)
    write(out / "report.json", report)
    write(out / "results.json", {"rows": rows, "uncertainty": {
        "unit": "One prescribed deterministic split per dataset, seed 42",
        "method": "Exact held-out counts and original two-decimal percentages; no inferential interval",
        "reason": "Repeated loop labels, deterministic reruns and different datasets are not independent replicates.",
        "scope": "No population accuracy, random-split variability or CN/AA comparison for Iris/Zoo is established."},
        "checks": {"raw_hashes": "pass", "stdout_vs_saved_counts": "pass",
                   "independent_graph_predictor": "pass", "exact_question_keys": "pass"}})
    table = ["| Dataset | Printed label | Executed predictor | Correct / test | Accuracy |", "|---|---|---|---:|---:|"]
    table += [f"| {r['dataset'].capitalize()} | {r['printed_label']} | {r['executed_predictor']} | {r['correct']} / {r['test_n']} | {r['accuracy_percent']:.2f}% |" for r in rows]
    (out / "results-table.md").write_text("\n".join(table) + "\n")
    if args.compare:
        reference = ROOT / args.compare
        for filename in ("report.json", "results.json"):
            assert read(reference / filename) == read(out / filename), filename
        write(out / "comparison.json", {"status": "pass", "compared": args.compare,
              "coverage": "Exact JSON equality for all reported answers, counts, metadata and independent graph checks."})
    print(__import__("json").dumps({"status": "pass", "report": report, "checked_calls": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
