"""Synthetic known-answer controls, distinct from all confirmation datasets."""
import argparse
import json
import sys
from common import ROOT, write_json, ref

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    import networkx as nx
    import numpy as np
    sys.path.insert(0, str(ROOT / "source/adapted/code"))
    from culp import link_predictors
    from culp.classifier import culp
    from evaluate import accuracy, PATTERN
    # A test node 2 has its only common neighbor with class 3 (node 0).
    # Class 4 has none. Each method therefore must predict class index 0.
    graph = nx.Graph([(2, 0), (0, 3), (1, 4)])
    outcomes = {}
    for name in ["common_neighbors", "adamic_adar", "resource_allocation_index", "compatibility_score"]:
        p = getattr(link_predictors, name)(graph, (2, 3), (3, 5))
        assert p.tolist() == [0], (name, p)
        outcomes[name] = p.tolist()
    for lp in ["CN", "AA", "RA", "CS"]:
        # Two separated labelled anchors and a test point beside each.
        p = culp(np.array([[0.0], [10.0]]), np.array([0, 1]),
                 np.array([[0.1], [9.9]]), lp, "manhattan", 1)
        assert p.tolist() == [0, 1], (lp, p)
        outcomes["end_to_end_" + lp] = p.tolist()
    assert accuracy([0, 1, 1], [0, 1, 0]) == {
        "correct": 2, "total": 3, "accuracy": 2/3, "printed_percent": 66.67}
    try:
        accuracy([0], [0, 1])
    except ValueError:
        outcomes["reject_mismatched_vectors"] = True
    else:
        raise AssertionError("Evaluator accepted mismatched vectors")
    for pred, expected in [([1, 1], 0.0), ([0, 0], 100.0)]:
        assert accuracy(pred, [0, 0])["printed_percent"] == expected
    assert PATTERN.fullmatch("Prediction Accuracy for Iris Dataset (λ=CN) = 66.67%")
    write_json(out / "qualification.json", {"status": "passed", "seed": 123, "phase": "pilot",
        "inputs": "Hand-defined graph and 1D separated anchors; no supplied dataset used",
        "outcomes": outcomes, "known_accuracy_percent": 66.67,
        "scope": "Known predictions for all four predictors and evaluator boundary controls; not a proof for all graphs"})
    print(json.dumps({"qualification": "passed", "artifact": ref(out / "qualification.json")}, indent=2))

if __name__ == "__main__":
    main()
