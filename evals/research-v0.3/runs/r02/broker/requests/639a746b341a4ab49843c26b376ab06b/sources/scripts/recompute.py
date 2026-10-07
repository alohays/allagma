"""Audit and recompute CULP results from retained evidence; never run experiments."""
import argparse
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("iris", "zoo", "wine")
LABELS = ("CN", "AA", "RA", "CS")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def relative(path):
    return path.relative_to(ROOT).as_posix()


def find_receipt(run):
    matches = []
    for path in sorted((ROOT / "evidence/broker").glob("*/request.json")):
        request = json.loads(path.read_text())
        argv = request["argv"]
        if "--output" in argv and argv[argv.index("--output") + 1] == relative(run) and "scripts/run_experiments.py" in argv:
            response = json.loads((path.parent / "response.json").read_text())
            assert response["result"]["status"] == "completed", response
            matches.append((request["request_id"], relative(path.parent / "response.json")))
    assert len(matches) == 1, (relative(run), matches)
    return matches[0]


def check_source(provenance):
    rows = provenance["files"]
    revision = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    assert revision == provenance["source_revision"]
    for entry in rows:
        assert digest(ROOT / "source/original" / entry["path"]) == entry["original_sha256"]
        assert digest(ROOT / "source/adapted" / entry["path"]) == entry["adapted_sha256"]
        assert digest(ROOT / "inputs/materials/capsule-6460826" / entry["path"]) == entry["original_sha256"]
    changed = [r["path"] for r in rows if r["original_sha256"] != r["adapted_sha256"]]
    assert changed == ["code/wine_sample.py", "code/zoo_sample.py"], changed
    for dataset in ("wine", "zoo"):
        before = (ROOT / "source/original/code" / (dataset + "_sample.py")).read_bytes()
        expected = b"from pathlib import Path\n" + before.replace(
            ("'/data/" + dataset + ".txt'").encode(),
            ("Path(__file__).resolve().parents[1] / 'data' / '" + dataset + ".txt'").encode())
        assert expected == (ROOT / "source/adapted/code" / (dataset + "_sample.py")).read_bytes()
    return changed


def graph_check(arrays, graph, actual_predictor, k):
    train, test = arrays["train"], arrays["test"]
    n, m = len(train), len(test)
    labels = arrays["train_labels"]
    c = len(np.unique(labels))
    total = n + m
    assert np.array_equal(np.unique(labels), np.arange(c))
    assert np.array_equal(graph["nodes"], np.arange(total + c))
    edges = {tuple(sorted(map(int, edge))) for edge in graph["edges"]}
    assert len(edges) == len(graph["edges"])
    class_edges = {edge for edge in edges if edge[1] >= total}
    assert class_edges == {(i, total + int(labels[i])) for i in range(n)}
    adjacency = [set() for _ in range(total + c)]
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)
    # NetworkX counts a self-loop twice in degree, once in the neighbor set.
    degree = [len(neighbors) + int(i in neighbors) for i, neighbors in enumerate(adjacency)]

    def common(a, b):
        # NetworkX common_neighbors excludes the two queried vertices.
        return adjacency[a].intersection(adjacency[b]).difference((a, b))

    data = np.concatenate((train, test))
    distance = np.abs(data[:, None, :] - data[None, :, :]).sum(axis=2)
    boundary = np.sort(distance, axis=1)[:, k]
    for a, b in edges:
        if b < total:
            assert distance[a, b] <= boundary[a] + 1e-12 or distance[a, b] <= boundary[b] + 1e-12
    # All positive-distance neighbors strictly inside a directed k-NN boundary
    # must occur in the union graph. Boundary ties and duplicate zero distances
    # are checked for admissibility only, without imposing a new tie rule.
    required = np.argwhere((distance > 0) & (distance < boundary[:, None] - 1e-12))
    for a, b in required:
        assert tuple(sorted((int(a), int(b)))) in edges
    scores = np.zeros((m, c), dtype=float)
    minimum_cs_denominator = None
    for row, a in enumerate(range(n, total)):
        for col, b in enumerate(range(total, total + c)):
            neighbors = sorted(common(a, b))
            if actual_predictor == "CN":
                scores[row, col] = len(neighbors)
            elif actual_predictor == "AA":
                scores[row, col] = sum(1 / (math.log(degree[t]) + 1e-9) for t in neighbors)
            elif actual_predictor == "RA":
                scores[row, col] = sum(1 / degree[t] for t in neighbors)
            elif actual_predictor == "CS":
                for t in neighbors:
                    d1 = degree[t] - len(common(t, b))
                    d2 = degree[t] - len(common(t, a))
                    assert min(d1, d2) > 0
                    minimum_cs_denominator = min(d1, d2, minimum_cs_denominator or float("inf"))
                    scores[row, col] += 1 / d1 + 1 / d2
            else:
                raise AssertionError(actual_predictor)
    assert np.isfinite(scores).all()
    reconstructed = scores.argmax(axis=1)
    assert np.array_equal(reconstructed, arrays["predictions"])
    return scores, {
        "nodes": total + c, "edges": len(edges),
        "self_loops": [int(a) for a, b in sorted(edges) if a == b],
        "self_loop_count": sum(a == b for a, b in edges),
        "duplicate_feature_pairs": int(np.count_nonzero(np.triu(distance == 0, 1))),
        "top_score_ties": int(np.sum(np.sum(scores == scores.max(axis=1, keepdims=True), axis=1) > 1)),
        "all_zero_score_rows": int(np.sum(np.all(scores == 0, axis=1))),
        "minimum_cs_denominator": minimum_cs_denominator,
        "class_edges_exact": True, "knn_edges_admissible": True,
        "strict_positive_distance_knn_edges_present": True,
        "independent_score_predictions_equal": True,
        "limitation": "Boundary-tie neighbor choice is not independently reconstructed; its admissibility is checked."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--compare-run")
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected")
    args = parser.parse_args()
    run = ROOT / args.run
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    execution = json.loads((run / "execution.json").read_text())
    assert execution["state"] == "completed"
    assert execution["datasets_completed"] == list(DATASETS)
    assert execution["runner_sha256"] == digest(ROOT / "scripts/run_experiments.py")
    assert execution["protocol_sha256"] == digest(ROOT / "PROTOCOL.md")
    provenance = json.loads((ROOT / "source/provenance.json").read_text())
    changed = check_source(provenance)
    assert execution["source_revision"] == provenance["source_revision"]
    attempt_id, receipt = find_receipt(run)
    comparison = ROOT / args.compare_run if args.compare_run else None
    if comparison:
        repeat_execution = json.loads((comparison / "execution.json").read_text())
        assert repeat_execution["state"] == "completed"
        assert repeat_execution["source_revision"] == execution["source_revision"]
        assert repeat_execution["runner_sha256"] == execution["runner_sha256"]
        repeat_id, repeat_receipt = find_receipt(comparison)
    records = []
    measurements = []
    dataset_checks = {}
    evidence_hashes = {}
    for dataset in DATASETS:
        folder = run / dataset
        saved = load(folder / "dataset.npz")
        data, labels = saved["data"], saved["labels"]
        expected_shape = {"iris": (150, 4), "zoo": (101, 16), "wine": (178, 13)}[dataset]
        assert data.shape == expected_shape
        assert np.isfinite(data).all()
        n_test = math.ceil(len(data) * 0.2)
        permutation = np.random.RandomState(42).permutation(len(data))
        test_indices, train_indices = permutation[:n_test], permutation[n_test:]
        assert np.array_equal(saved["test_indices"], test_indices)
        assert np.array_equal(saved["train_indices"], train_indices)
        assert np.array_equal(saved["train_labels"], labels[train_indices])
        assert np.array_equal(saved["test_labels"], labels[test_indices])
        assert not set(train_indices).intersection(test_indices)
        assert set(train_indices).union(test_indices) == set(range(len(data)))
        if dataset == "wine":
            raw = np.loadtxt(ROOT / "source/original/data/wine.txt", delimiter=",")
            assert np.array_equal(data, raw[:, 1:])
            assert np.array_equal(labels, raw[:, 0].astype(int) - 1)
        elif dataset == "zoo":
            raw = np.loadtxt(ROOT / "source/original/data/zoo.txt", delimiter=",", usecols=range(1, 18))
            assert np.array_equal(data, raw[:, :16])
            assert np.array_equal(labels, raw[:, 16].astype(int) - 1)
        else:
            wheel = ROOT / "inputs/materials/wheels/scikit_learn-1.5.2-cp311-cp311-macosx_12_0_arm64.whl"
            with zipfile.ZipFile(wheel) as archive:
                with archive.open("sklearn/datasets/data/iris.csv") as handle:
                    raw = np.loadtxt(handle, delimiter=",", skiprows=1)
            assert np.array_equal(data, raw[:, :4])
            assert np.array_equal(labels, raw[:, 4].astype(int))
        raw_train, raw_test = data[train_indices], data[test_indices]
        if dataset == "wine":
            mean, std = raw_train.mean(axis=0), raw_train.std(axis=0)
            std[std == 0] = mean[std == 0] + 1e-9
            expected_train, expected_test = (raw_train - mean) / std, (raw_test - mean) / std
            np.savez_compressed(output / "wine_normalization.npz", mean=mean, std=std)
        else:
            expected_train, expected_test = raw_train, raw_test
        np.testing.assert_allclose(saved["train"], expected_train, rtol=0, atol=1e-14)
        np.testing.assert_allclose(saved["test"], expected_test, rtol=0, atol=1e-14)
        assert np.array_equal(np.unique(saved["train_labels"]), np.unique(labels))
        text = (folder / "stdout.txt").read_text()
        lines = re.findall(r"^Prediction Accuracy for (Iris|Zoo|Wine) Dataset \(λ=(CN|AA|RA|CS)\) = ([0-9.]+)%$", text, re.MULTILINE)
        assert len(lines) == 4 and tuple(row[1] for row in lines) == LABELS, text
        assert all(row[0].lower() == dataset for row in lines)
        assert len(text.splitlines()) == 4
        assert (folder / "stderr.txt").read_text() == ""
        calls = json.loads((folder / "calls.json").read_text())
        assert len(calls) == 4
        for index, call in enumerate(calls):
            label = LABELS[index]
            actual = label if dataset == "wine" else "CS"
            k = {"iris": 11, "zoo": 2, "wine": 12}[dataset]
            assert call["state"] == "completed"
            assert call["call_index"] == index and call["printed_label"] == label
            assert call["actual_predictor"] == actual
            assert (call["similarity"], call["k"], call["n_jobs"]) == ("manhattan", k, 1)
            assert digest(folder / call["arrays"]) == call["arrays_sha256"]
            assert digest(folder / call["graph"]) == call["graph_sha256"]
            arrays = load(folder / call["arrays"])
            graph = load(folder / call["graph"])
            for key in ("train", "test", "train_labels"):
                assert np.array_equal(arrays[key], saved[key])
            predictions = arrays["predictions"]
            truth = saved["test_labels"]
            assert predictions.shape == truth.shape
            assert np.isin(predictions, np.unique(labels)).all()
            correct = int(np.count_nonzero(predictions == truth))
            percentage = round(100 * float(np.mean(predictions == truth)), 2)
            assert percentage == float(lines[index][2])
            scores, graph_audit = graph_check(arrays, graph, actual, k)
            score_path = output / (dataset + "_" + label + "_scores.npz")
            np.savez_compressed(score_path, scores=scores)
            classes = len(np.unique(labels))
            confusion = np.zeros((classes, classes), dtype=int)
            np.add.at(confusion, (truth, predictions), 1)
            mismatches = np.flatnonzero(predictions != truth)
            record = {"dataset": dataset, "printed_label": label, "actual_predictor": actual,
                      "correct": correct, "total": len(truth), "accuracy": correct / len(truth),
                      "accuracy_percent": percentage, "k": k, "similarity": "manhattan",
                      "confusion_true_rows_predicted_columns": confusion.tolist(),
                      "misclassified_original_indices": test_indices[mismatches].tolist(),
                      "misclassified_true_labels": truth[mismatches].tolist(),
                      "misclassified_predictions": predictions[mismatches].tolist(),
                      "graph_audit": graph_audit, "independent_scores": relative(score_path)}
            records.append(record)
            measurements.append({"dataset": dataset, "phase": "confirmation", "device": "cpu",
                                 "printed_label": label, "actual_predictor": actual,
                                 "arrays": relative(folder / call["arrays"]),
                                 "dataset_arrays": relative(folder / "dataset.npz"),
                                 "graph_arrays": relative(folder / call["graph"]),
                                 "stdout": relative(folder / "stdout.txt"),
                                 "metrics": {key: record[key] for key in ("correct", "total", "accuracy", "accuracy_percent")},
                                 "source_revision": execution["source_revision"], "attempt_id": attempt_id,
                                 "broker_receipt": receipt})
        dataset_checks[dataset] = {"data_shape": list(data.shape), "train_count": len(train_indices),
                                   "test_count": len(test_indices),
                                   "train_class_counts": np.bincount(saved["train_labels"]).tolist(),
                                   "test_class_counts": np.bincount(saved["test_labels"], minlength=len(np.unique(labels))).tolist(),
                                   "seed42_split_exact": True, "input_label_alignment": True,
                                   "preprocessing_verified": True, "stdout_all_rows_verified": True,
                                   "test_rows_exact_feature_match_in_train": int(np.any(np.all(raw_test[:, None, :] == raw_train[None, :, :], axis=2), axis=1).sum()),
                                   "original_data_file_verified": True,
                                   "iris_provenance": "Saved sklearn 1.5.2 built-in Iris arrays; offline wheel retained." if dataset == "iris" else None}
        for path in sorted(folder.iterdir()):
            if path.is_file():
                evidence_hashes[relative(path)] = digest(path)
                if comparison:
                    other = comparison / dataset / path.name
                    if path.suffix == ".npz":
                        left, right = load(path), load(other)
                        assert left.keys() == right.keys()
                        assert all(np.array_equal(left[key], right[key]) for key in left)
                    else:
                        assert path.read_bytes() == other.read_bytes()
    task = (ROOT / "inputs/materials/task.txt").read_text()
    questions = ast.literal_eval(re.search(r"dict_keys\((\[.*?\])\)", task, re.DOTALL).group(1))
    answers = {}
    for question in questions:
        dataset = next(d for d in DATASETS if d.lower() + " dataset" in question.lower())
        label = next(label for label in ("CN", "AA") if "the " + label + " " in question)
        answers[question] = next(r["accuracy_percent"] for r in records if r["dataset"] == dataset and r["printed_label"] == label)
    assert len(answers) == 6
    if args.expected:
        assert answers == json.loads((ROOT / args.expected).read_text()), "Reported answers differ from raw evidence"
    save(output / "report.json", answers)
    save(output / "measurements.json", {"format": "research-measurements-v1", "task_id": "core-culp",
         "protocol": "PROTOCOL.md", "schema_extension": "CULP run schema documented in REPRODUCE.md; supplied task-specific schemas concern other tasks.",
         "runs": measurements})
    save(output / "metrics.json", records)
    save(output / "verification.json", {"status": "passed", "source_revision": execution["source_revision"],
         "protocol_sha256": digest(ROOT / "PROTOCOL.md"), "runner_sha256": digest(ROOT / "scripts/run_experiments.py"),
         "recompute_sha256": digest(Path(__file__)), "attempt_id": attempt_id, "receipt": receipt,
         "changed_sources": changed, "dataset_checks": dataset_checks,
         "same_environment_repeatability": {"checked": bool(comparison), "run": args.compare_run,
             "attempt_id": repeat_id if comparison else None, "receipt": repeat_receipt if comparison else None,
             "all_dataset_arrays_graphs_predictions_stdout_equal": bool(comparison)},
         "evidence_sha256": evidence_hashes,
         "scope": "Exact retained-output arithmetic, data/split/scaling checks, graph admissibility, independent predictor scores; no source experiment rerun.",
         "limits": ["No comparison to original capsule outputs, which were not supplied.",
                    "No uncertainty or cross-version generalization claim from one fixed partition.",
                    "Iris and Zoo printed CN/AA rows execute CS.",
                    "k-NN boundary-tie selection is checked for admissibility, not independently reconstructed."]})
    with (output / "results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "printed_label", "actual_predictor", "correct", "total", "accuracy", "accuracy_percent"])
        writer.writeheader()
        writer.writerows({key: record[key] for key in writer.fieldnames} for record in records)
    print(json.dumps({"status": "passed", "output": args.output, "report": answers,
                      "calls_verified": len(records), "repeatability_checked": bool(comparison)}, indent=2))


if __name__ == "__main__":
    main()
