"""Independent calculations on retained graphs, scores, labels and inputs only."""
import argparse
import json
import math
import numpy as np
from common import ROOT, check_ref, write_json

def audit(manifest_path):
    manifest = json.loads(manifest_path.read_text())
    results = []
    for run in manifest["runs"]:
        raw = json.loads(check_ref(run["raw"]).read_text())
        with np.load(check_ref(raw["dataset_arrays"]), allow_pickle=False) as data:
            n = len(data["y_train"])
            m = len(data["y_test"])
            c = len(set(data["y_train"].tolist()))
            # Independently generate sklearn's ShuffleSplit permutation via NumPy.
            perm = np.random.RandomState(42).permutation(n + m)
            assert np.array_equal(data["test_indices"], perm[:m])
            assert np.array_equal(data["train_indices"], perm[m:])
            for call in raw["calls"]:
                with np.load(check_ref(call["arrays"]), allow_pickle=False) as a:
                    neighbors = {int(node): set() for node in a["nodes"]}
                    for left, right in a["edges"].tolist():
                        neighbors[left].add(right)
                        neighbors[right].add(left)
                    assert set(neighbors) == set(range(n + m + c))
                    # Class nodes must connect to exactly the correctly labelled training nodes.
                    for cls in range(c):
                        assert neighbors[n+m+cls] == {i for i,y in enumerate(a["y_train"].tolist()) if y == cls}
                    assert all(not neighbors[i].intersection(range(n+m,n+m+c)) for i in range(n,n+m))
                    scores = []
                    for i in range(n, n+m):
                        row = []
                        for j in range(n+m, n+m+c):
                            common = neighbors[i] & neighbors[j]
                            method = call["actual_predictor"]
                            if method == "CN":
                                score = float(len(common))
                            elif method == "AA":
                                score = sum(1/(math.log(len(neighbors[v])) + 1e-9) for v in sorted(common))
                            elif method == "RA":
                                score = sum(1/len(neighbors[v]) for v in sorted(common))
                            else:
                                score = sum(1/(len(neighbors[v])-len(neighbors[v]&neighbors[j]))
                                            + 1/(len(neighbors[v])-len(neighbors[v]&neighbors[i])) for v in sorted(common))
                            row.append(score)
                        scores.append(row)
                    scores = np.array(scores)
                    error = float(np.max(np.abs(scores - a["scores"])))
                    assert np.allclose(scores, a["scores"], rtol=1e-12, atol=1e-12)
                    assert np.array_equal(np.argmax(scores, axis=1), a["prediction"])
                    margins = np.sort(scores, axis=1)[:, -1] - np.sort(scores, axis=1)[:, -2]
                    results.append({"dataset": run["dataset"], "printed_label": call["printed_label"],
                                    "actual_predictor": call["actual_predictor"], "max_score_error": error,
                                    "tied_maximum_test_cases": int(np.sum(margins == 0)),
                                    "predictions_match": True})
    return {"passed": True, "checks": [
        "Exact source seed-42 permutation and all retained train/test indices",
        "Every class edge comes from an appropriate training label; no test-label class edges",
        "All 12 score matrices independently reconstructed from retained graph edges using Python sets and math.log",
        "Independent score argmax agrees with every saved prediction"],
        "limitations": ["Does not prove nearest-neighbor graph construction for every possible input",
                        "Does not compare with unavailable original capsule outputs or establish generalization"],
        "results": results}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="evidence/raw-manifest.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    value = audit(ROOT / args.manifest)
    write_json(ROOT / args.out, value)
    print(json.dumps(value, indent=2))
