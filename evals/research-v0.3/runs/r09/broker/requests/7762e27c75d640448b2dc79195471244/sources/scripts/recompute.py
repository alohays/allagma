"""Derive answers and scientific checks from retained evidence only, through the broker."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from audit_arrays import check_arrays

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="evidence/run-index.json")
    parser.add_argument("--output", default="analysis")
    parser.add_argument("--compare-report")
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    index = read_json(ROOT / args.index)
    revision = read_json(ROOT / "evidence/source-revision.json")
    for variant in ("original", "adapted"):
        for path, digest in revision[variant].items():
            assert sha(ROOT / "source" / variant / path) == digest, f"Changed source: {variant}/{path}"
    assert sha(ROOT / "PROTOCOL.md") == revision["protocol_sha256"]
    task = (ROOT / "inputs/materials/task.txt").read_text()
    keys = ast.literal_eval(re.search(r"dict_keys\((\[.*?\])\)", task).group(1))
    expected_datasets, expected_predictors = ["iris", "zoo", "wine"], ["CN", "AA", "RA", "CS"]
    assert [entry["dataset"] for entry in index["runs"]] == expected_datasets
    report, results, measurements = {}, [], []
    for entry in index["runs"]:
        dataset = entry["dataset"]
        directory = ROOT / entry["directory"]
        run = read_json(directory / "run.json")
        receipt = read_json(ROOT / entry["receipt"])
        assert receipt["request_id"] == entry["attempt_id"]
        assert receipt["result"]["status"] == "completed" and receipt["result"]["exit_code"] == 0
        assert run["status"] == "completed" and len(run["calls"]) == 4
        assert run["source_revision"] == revision["adapted_tree_sha256"]
        assert run["protocol_sha256"] == revision["protocol_sha256"]
        assert sha(ROOT / run["script"]) == run["script_sha256"]
        printed = (directory / "stdout.txt").read_text()
        lines = re.findall(r"^Prediction Accuracy for (Iris|Zoo|Wine) Dataset \(λ=(CN|AA|RA|CS)\) = ([0-9.]+)%$", printed, re.M)
        assert len(lines) == 4 and [x[1] for x in lines] == expected_predictors
        assert (directory / "stderr.txt").read_text() == ""
        assert (ROOT / entry["receipt"]).parent.joinpath("stdout.txt").read_text() == printed
        direct = ROOT / index["direct"]["directory"]
        assert (direct / f"{dataset}-stdout.txt").read_text() == printed
        assert (direct / f"{dataset}-stderr.txt").read_text() == ""
        for i, call in enumerate(run["calls"]):
            assert call["call"] == i + 1 and call["display_predictor"] == expected_predictors[i]
            assert call["actual_predictor"] == (expected_predictors[i] if dataset == "wine" else "CS")
            assert call["similarity"] == "manhattan" and call["k"] == {"iris": 11, "zoo": 2, "wine": 12}[dataset]
            assert call["n_jobs"] == 1
            arrays = ROOT / call["arrays"]
            assert sha(arrays) == call["arrays_sha256"]
            with np.load(arrays, allow_pickle=False) as saved:
                checked, scores, train_indices, test_indices = check_arrays(saved, call, dataset, ROOT)
            assert lines[i][0].lower() == dataset and float(lines[i][2]) == checked["accuracy_percent"]
            artifact = out / f"{dataset}-{call['display_predictor']}-audit.npz"
            np.savez_compressed(artifact, independent_scores=scores, train_indices=train_indices, test_indices=test_indices)
            result = {"dataset": dataset, "display_predictor": call["display_predictor"],
                      "actual_predictor": call["actual_predictor"], "call": call["call"],
                      "arrays": call["arrays"], "audit_arrays": str(artifact.relative_to(ROOT)),
                      "attempt_id": entry["attempt_id"], "source_revision": revision["adapted_tree_sha256"], **checked}
            results.append(result)
            measurements.append({"dataset": dataset, "display_predictor": call["display_predictor"],
                                 "actual_predictor": call["actual_predictor"], "phase": "reproduction", "device": "cpu",
                                 "seed": 42, "test_size": 0.2, "similarity": "manhattan", "k": call["k"],
                                 "arrays": call["arrays"], "metrics": {k: checked[k] for k in ["correct", "n_test", "accuracy_percent", "accuracy_fraction"]},
                                 "source_revision": revision["adapted_tree_sha256"], "attempt_id": entry["attempt_id"],
                                 "trace": str((directory / "events.jsonl").relative_to(ROOT))})
            if i < 2:
                matching = [key for key in keys if f"the {call['display_predictor']} prediction" in key and f"the {dataset.title()} dataset" in key]
                assert len(matching) == 1
                report[matching[0]] = checked["accuracy_percent"]
    assert set(report) == set(keys)
    report = {key: report[key] for key in keys}
    direct_receipt = read_json(ROOT / index["direct"]["receipt"])
    assert direct_receipt["result"]["status"] == "completed"
    if index.get("interrupted"):
        interrupted = read_json(ROOT / index["interrupted"]["receipt"])
        assert interrupted["injected_interruption"] is True and interrupted["result"]["status"] != "completed"
        assert (ROOT / index["interrupted"]["directory"] / "events.jsonl").is_file()
    envelope = {"format": "research-measurements-v1", "task_id": "core-culp", "protocol": "PROTOCOL.md",
                "schema_note": "CULP extension: supplied MEASUREMENTS.md defines no CULP-specific fields. Arrays contain raw_data, raw_labels, train, test, train_labels, test_labels, prediction, graph_edges; all are numeric and load with allow_pickle=False.",
                "runs": measurements}
    verification = {"status": "passed", "source_revision": revision["adapted_tree_sha256"],
                    "protocol_sha256": revision["protocol_sha256"], "checked_calls": len(results),
                    "verified_script_outputs": expected_datasets,
                    "checks": {"source_and_protocol_hashes": True, "broker_completion": True,
                               "controlled_interruption_preserved": True if index.get("interrupted") else "not injected in this rerun",
                               "printed_values_match_raw_predictions": True,
                               "exact_question_keys": True, "direct_stdout_equals_instrumented": True,
                               "fixed_split_and_preprocessing": True, "graph_necessary_constraints": True,
                               "independent_predictor_maximizers": True},
                    "limitations": ["No source experiment is rerun here; these checks are conditional on retained evidence.",
                                    "Graph audit allows boundary-distance ties; exact tied directed neighbor selection is not independently established.",
                                    "The Iris/Zoo CN and AA labels refer to CS calls in the supplied scripts."]}
    if args.compare_report:
        assert read_json(ROOT / args.compare_report) == report, "Submitted answers differ from raw evidence"
        verification["checks"]["submitted_report_matches"] = True
    for name, data in [("report.json", report), ("results.json", results), ("measurements.json", envelope), ("verification.json", verification)]:
        (out / name).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": report, "verification": verification}, indent=2))


if __name__ == "__main__":
    main()
