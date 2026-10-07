"""Evaluate retained evidence only; no CULP imports or experiments."""
import argparse
import json
import re
import numpy as np
from common import ROOT, check_ref, ref, write_json

PATTERN = re.compile(r"Prediction Accuracy for (Iris|Zoo|Wine) Dataset \(λ=(CN|AA|RA|CS)\) = ([0-9.]+)%")

def accuracy(prediction, target):
    p, y = np.asarray(prediction), np.asarray(target)
    if p.ndim != 1 or y.ndim != 1 or p.shape != y.shape or len(y) == 0:
        raise ValueError("Predictions and labels must be matching nonempty vectors")
    correct = int(np.count_nonzero(p == y))
    return {"correct": correct, "total": len(y), "accuracy": correct / len(y),
            "printed_percent": round(100 * float(np.mean(p == y)), 2)}

def evaluate(raw_path):
    raw = json.loads(raw_path.read_text())
    check_ref(raw["script"])
    printed = PATTERN.findall(check_ref(raw["stdout"]).read_text())
    assert len(printed) == len(raw["calls"]) == 4
    check_ref(raw["stderr"])
    result = []
    with np.load(check_ref(raw["dataset_arrays"]), allow_pickle=False) as data:
        ti, vi = data["train_indices"], data["test_indices"]
        assert len(set(ti.tolist()) & set(vi.tolist())) == 0
        assert sorted(np.r_[ti, vi].tolist()) == list(range(len(data["labels"])))
        assert np.array_equal(data["labels"][ti], data["y_train"])
        assert np.array_equal(data["labels"][vi], data["y_test"])
        train, test = data["data"][ti], data["data"][vi]
        if raw["dataset"] == "wine":
            mean, sd = train.mean(0), train.std(0)
            sd[sd == 0] = mean[sd == 0] + 10e-10
            train, test = (train - mean) / sd, (test - mean) / sd
        assert np.array_equal(train, data["X_train"])
        assert np.array_equal(test, data["X_test"])
        for call, line in zip(raw["calls"], printed):
            with np.load(check_ref(call["arrays"]), allow_pickle=False) as a:
                for key in ["X_train", "X_test", "y_train", "y_test"]:
                    assert np.array_equal(a[key], data[key]), key
                m = accuracy(a["prediction"], a["y_test"])
                assert np.array_equal(a["scores"].argmax(1), a["prediction"])
                assert line[0].lower() == raw["dataset"] and line[1] == call["printed_label"]
                assert float(line[2]) == m["printed_percent"]
                expected_lp = line[1] if raw["dataset"] == "wine" else "CS"
                assert call["actual_predictor"] == expected_lp
                assert call["k"] == {"iris": 11, "zoo": 2, "wine": 12}[raw["dataset"]]
                assert call["similarity"] == "manhattan" and call["n_jobs"] == 1
                result.append({"dataset": raw["dataset"], "printed_label": line[1],
                               "actual_predictor": call["actual_predictor"], **m})
    return {"raw": ref(raw_path), "rows": result, "checks": [
        "All printed percentages exactly equal scores from retained predictions/labels",
        "All saved scores select saved predictions via source argmax",
        "Split indices partition input rows and recover every saved train/test label",
        "Inputs equal indexed raw features, with train-only Wine normalization",
        "All observed predictor, k, distance and n_jobs settings match original source"]}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("raw")
    p.add_argument("output")
    a = p.parse_args()
    result = evaluate(ROOT / a.raw)
    write_json(ROOT / a.output, result)
    print(json.dumps(result, indent=2))
