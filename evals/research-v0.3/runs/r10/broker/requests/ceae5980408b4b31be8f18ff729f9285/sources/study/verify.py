"""Broker-run technical audit of scientific evidence and locked artifact records."""
import argparse
import csv
import importlib.metadata
import math
import sys
import numpy as np
from common import ROOT, digest, read, ref, verify_refs, write
from analyze import evaluate_raw, questions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="evidence/verification.json")
    args = parser.parse_args()
    checks = []
    source = read(ROOT / "provenance/source-manifest.json")
    verify_refs(source["original"] + source["adapted"] + [source["patch"]])
    original = ROOT / "inputs/materials/capsule-6460826"
    adapted = ROOT / "work/capsule"
    changes = []
    for path in original.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(original)
        other = adapted / relative
        if path.read_bytes() == other.read_bytes():
            continue
        assert relative.as_posix() in ("code/wine_sample.py", "code/zoo_sample.py")
        dataset = relative.stem.split("_")[0]
        expected = "from pathlib import Path\n" + path.read_text().replace(
            f"'/data/{dataset}.txt'", f"Path(__file__).resolve().parents[1] / 'data/{dataset}.txt'")
        assert other.read_text() == expected
        changes.append(relative.as_posix())
    assert sorted(changes) == ["code/wine_sample.py", "code/zoo_sample.py"]
    checks.append({"id": "source-adaptation", "status": "pass", "establishes": "Only two exact data-path changes; all upstream algorithm bytes and Iris script unchanged", "changed": changes})
    code = read(ROOT / "campaigns/culp-v1/code-manifest.json")
    verify_refs(list(code.values()))
    for path, frozen in code.items():
        assert digest(ROOT / path) == frozen["sha256"], path
    checks.append({"id": "frozen-code", "status": "pass", "establishes": "Executed scientific source, analyzer and writer match pre-confirmation campaign snapshots"})
    manifest = read(ROOT / "evidence/raw-manifest.json")
    rows, report = evaluate_raw(manifest)
    assert report == read(ROOT / "report.json") == read(ROOT / "analysis/main/report.json")
    assert list(sorted(report)) == sorted(questions())
    checks.append({"id": "six-answer-evidence", "status": "pass", "establishes": "All six exact question keys and percentages match raw stdout and retained prediction counts; all 12 call predictions match independent graph scores", "calls": len(rows)})
    details = []
    for run in manifest["runs"]:
        calls = read(ROOT / run["directory"] / "calls.json")
        for call in calls:
            d = run["dataset"]
            with np.load(ROOT / call["arrays"]["path"], allow_pickle=False) as a:
                n, m, c = map(int, a["node_counts"])
                permutation = np.random.RandomState(42).permutation(n + m)
                test_indices, train_indices = permutation[:m], permutation[m:]
                assert m == math.ceil(0.2 * (n + m))
                assert np.array_equal(a["y_train"], a["full_labels"][train_indices])
                assert np.array_equal(a["y_test"], a["full_labels"][test_indices])
                xtrain, xtest = a["full_data"][train_indices], a["full_data"][test_indices]
                if d == "wine":
                    mean, std = xtrain.mean(axis=0), xtrain.std(axis=0)
                    std[std == 0] = mean[std == 0] + 1e-9
                    xtrain, xtest = (xtrain - mean) / std, (xtest - mean) / std
                assert np.array_equal(xtrain, a["X_train"])
                assert np.array_equal(xtest, a["X_test"])
                expected_predictor = call["printed_label"] if d == "wine" else "CS"
                assert call["executed_predictor"] == expected_predictor
                assert call["k"] == {"iris": 11, "zoo": 2, "wine": 12}[d]
                assert call["similarity"] == "manhattan" and call["n_jobs"] == 1
                if d in ("zoo", "wine"):
                    data = list(csv.reader((original / "data" / f"{d}.txt").open()))
                    raw_features = np.asarray([row[1:17] if d == "zoo" else row[1:] for row in data], dtype=float)
                    raw_labels = np.asarray([int(row[17] if d == "zoo" else row[0]) - 1 for row in data])
                else:
                    file = importlib.metadata.distribution("scikit-learn").locate_file("sklearn/datasets/data/iris.csv")
                    data = np.loadtxt(file, delimiter=",", skiprows=1)
                    raw_features, raw_labels = data[:, :4], data[:, 4].astype(int)
                assert np.array_equal(raw_features, a["full_data"])
                assert np.array_equal(raw_labels, a["full_labels"])
                edge_set = {tuple(edge) for edge in a["graph_edges"].tolist()}
                for train, label in enumerate(a["y_train"]):
                    assert (train, n + m + label) in edge_set
                for left, right in edge_set:
                    if right >= n + m:
                        assert left < n and right == n + m + a["y_train"][left]
                if call["call_index"] == 0:
                    details.append({"dataset": d, "train": n, "test": m, "classes": c, "partition_seed": 42,
                        "source_rows_match": True, "train_indices": train_indices.tolist(), "test_indices": test_indices.tolist()})
    checks.append({"id": "inputs-partitions-preprocessing", "status": "pass", "establishes": "Full rows match supplied files or installed Iris data, actual partitions match seed-42 permutation, Wine uses train-only population normalization, fixed parameters and class-label edges match", "datasets": details})
    assert read(ROOT / "analysis/main/report.json") == read(ROOT / "analysis/recomputed/report.json")
    assert read(ROOT / "analysis/main/results.json") == read(ROOT / "analysis/recomputed/results.json")
    checks.append({"id": "separate-recomputation", "status": "pass", "establishes": "Exact equality of report and full analysis JSON regenerated in a second directory from the same immutable raw inputs"})
    pilot = read(ROOT / "evidence/pilot/qualification.json")
    assert pilot["status"] == "pass" and pilot["independent_of_confirmation"]
    recovered = read(ROOT / "evidence/recovery.json")
    assert recovered["interrupted_request"]["injected_interruption"]
    assert recovered["successor"]["attempt_id"] != recovered["interrupted_request"]["label"]
    checks.append({"id": "qualification-recovery", "status": "pass", "establishes": "Synthetic pilot passed; controlled interrupted attempt retained and excluded; successor identity is distinct"})
    sys.path.insert(0, str(ROOT / ".allagma/bundles/b-9a39b70665ba909edb8abc13"))
    from allagma.contracts import validate_record
    from allagma.bundles import verify_lock
    verify_lock(ROOT, read(ROOT / "campaigns/culp-v1/lock.yaml"))
    validated = []
    for path in sorted((ROOT / "campaigns/culp-v1").rglob("*.json")):
        if "materials" in path.parts:
            continue
        value = read(path)
        if isinstance(value, dict) and "record_type" in value:
            validate_record(value)
            validated.append(path.relative_to(ROOT).as_posix())
    def recurse(value):
        if isinstance(value, dict):
            if {"path", "sha256"} <= value.keys():
                assert digest(ROOT / value["path"]) == value["sha256"], value["path"]
            for child in value.values():
                recurse(child)
        elif isinstance(value, list):
            for child in value:
                recurse(child)
    for path in sorted((ROOT / "campaigns/culp-v1").rglob("*.json")):
        if "materials" not in path.parts:
            recurse(read(path))
    checks.append({"id": "allagma-records-and-dependencies", "status": "pass", "establishes": "Exact bundle lock verified; all available typed campaign records satisfy their locked schemas; nested evidence references resolve to current hashes", "records": validated})
    table = (ROOT / "analysis/main/results-table.md").read_text()
    manuscript = (ROOT / "REPORT.md").read_text()
    assert table in manuscript and "do not run CN or AA" in manuscript
    checks.append({"id": "manuscript-numbers", "status": "pass", "establishes": "Complete generated empirical table occurs verbatim in manuscript with explicit Iris/Zoo interpretation caveat"})
    write(ROOT / args.output, {"status": "pass", "checks": checks,
        "reviewed_sources": [ref(ROOT / "study/verify.py"), ref(ROOT / "study/analyze.py"), ref(ROOT / "report.json"), ref(ROOT / "REPORT.md")],
        "limitations": ["Deterministic audit and author critique, not independent peer review", "No original reference answers or environment available", "No proof of population performance or all algorithm cases", "Source nearest-neighbor tie behavior is preserved"]})
    print(f"Technical audit passed {len(checks)} checks.")


if __name__ == "__main__":
    main()
