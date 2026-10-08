"""Summarize scientific diagnostics and compare independent fresh-run arrays."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    results = json.loads((ROOT / "analysis/results.json").read_text())
    fresh_index = json.loads((ROOT / "reproduction/fresh-check/run-index.json").read_text())
    summary = []
    arrays_compared = 0
    predictions_compared = 0
    for dataset in ["iris", "zoo", "wine"]:
        rows = [r for r in results if r["dataset"] == dataset]
        fresh_entry = next(r for r in fresh_index["runs"] if r["dataset"] == dataset)
        fresh_run = json.loads((ROOT / fresh_entry["directory"] / "run.json").read_text())
        with np.load(ROOT / rows[0]["arrays"], allow_pickle=False) as original:
            duplicates = np.all(original["test"][:, None] == original["train"][None, :], axis=2)
            duplicate_test_positions = np.flatnonzero(duplicates.any(axis=1)).tolist()
        for row, new_call in zip(rows, fresh_run["calls"]):
            with np.load(ROOT / row["arrays"], allow_pickle=False) as old, np.load(ROOT / new_call["arrays"], allow_pickle=False) as new:
                assert set(old.files) == set(new.files)
                for key in old.files:
                    np.testing.assert_array_equal(old[key], new[key])
                    arrays_compared += 1
                predictions_compared += len(old["prediction"])
        first = rows[0]
        summary.append({"dataset": dataset, "train": first["n_train"], "test": first["n_test"],
                        "self_loops": first["graph"]["self_loop_count"],
                        "duplicate_feature_rows": first["graph"]["duplicate_feature_row_count"],
                        "test_rows_identical_to_at_least_one_training_row": len(duplicate_test_positions),
                        "duplicate_test_positions": duplicate_test_positions,
                        "k_boundary_tie_nodes": first["graph"]["k_boundary_tie_count"],
                        "class_counts_train": first["train_class_counts"], "class_counts_test": first["test_class_counts"],
                        "printed_predictor_accuracy_percent": {r["display_predictor"]: r["accuracy_percent"] for r in rows},
                        "actual_predictors": {r["display_predictor"]: r["actual_predictor"] for r in rows},
                        "all_independent_argmax_exact": all(r["independent_predictor"]["exact_argmax_match"] for r in rows)})
    output = {"status": "passed", "fresh_run_comparison": {"calls": 12, "arrays_compared": arrays_compared,
              "predictions_compared": predictions_compared, "all_arrays_exactly_equal": True}, "datasets": summary}
    (ROOT / "analysis/diagnostics.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
