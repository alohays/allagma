"""Checks predictions against labels, printed scores, fixed configuration and toy controls."""
import json
from pathlib import Path
import re
import sys


def accuracy(prediction, truth):
    assert len(prediction) == len(truth) and truth
    return round(100 * sum(p == y for p, y in zip(prediction, truth)) / len(truth), 2)


def evaluate(raw):
    checks = []
    assert accuracy([0, 0, 1], [0, 1, 1]) == 66.67
    assert accuracy([0, 0], [1, 1]) == 0.0
    assert accuracy([0, 1], [0, 1]) == 100.0
    checks.append("Known-answer scoring controls: 0%, 2/3 -> 66.67%, 100%")
    if raw["mode"] == "pilot":
        assert raw["seed"] == 7
        assert raw["expected"] == [0, 1]
        assert set(raw["predictions"]) == {"CN", "AA", "RA", "CS"}
        assert all(value == [0, 1] for value in raw["predictions"].values())
        checks.append("All four original predictors classify the analytically specified two-class graph correctly")
    else:
        assert raw["seed"] == 42
        assert set(raw["datasets"]) == {"iris", "zoo", "wine"}
        for name, item in raw["datasets"].items():
            lines = re.findall(r"Prediction Accuracy for (\w+) Dataset \(λ=(\w+)\) = ([0-9.]+)%", item["stdout"])
            assert len(lines) == len(item["calls"]) == 4
            assert [line[1] for line in lines] == ["CN", "AA", "RA", "CS"]
            assert item["split_kwargs"] == {"test_size": 0.2, "random_state": 42}
            assert len(item["y_test"]) == {"iris": 30, "zoo": 21, "wine": 36}[name]
            for (title, label, printed), call in zip(lines, item["calls"]):
                assert title.lower() == name
                assert accuracy(call["prediction"], item["y_test"]) == float(printed)
                assert call["actual_predictor"] == (label if name == "wine" else "CS")
                assert call["k"] == {"iris": 11, "zoo": 2, "wine": 12}[name]
                assert call["similarity"] == "manhattan"
            checks.append(f"{name}: four complete outputs agree with retained labels/predictions and fixed source settings")
    return {"valid": True, "checks": checks,
            "coverage": "Known-answer pilot or retained predictions, source labels and configuration. No independent proof of classifier correctness or generalization."}


if __name__ == "__main__":
    parameters = json.loads(Path(sys.argv[1]).read_text())
    raw = json.loads(Path(sys.argv[2]).read_text())
    assert parameters["mode"] == raw["mode"]
    Path(sys.argv[3]).write_text(json.dumps(evaluate(raw), indent=2) + "\n")
