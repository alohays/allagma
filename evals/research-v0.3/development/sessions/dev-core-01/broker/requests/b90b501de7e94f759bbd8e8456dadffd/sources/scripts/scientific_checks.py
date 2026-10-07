"""Independent graph-score and partition audit from retained evidence, without fitting."""
import ast
import json
import math
from pathlib import Path


def checks(root, raw):
    import numpy as np
    findings = []
    # RandomState permutation is sklearn's fixed shuffle split implementation;
    # this does not call train_test_split, nearest neighbors, CULP or fit.
    for name, item in raw["datasets"].items():
        n = len(item["data"])
        n_test = math.ceil(n * .2)
        order = np.random.RandomState(42).permutation(n).tolist()
        assert item["test_indices"] == order[:n_test]
        assert item["train_indices"] == order[n_test:]
        assert not set(item["train_indices"]) & set(item["test_indices"])
        x = np.array(item["data"], dtype=float)
        y = np.array(item["labels"])
        assert np.array_equal(y[item["train_indices"]], item["y_train"])
        assert np.array_equal(y[item["test_indices"]], item["y_test"])
        train, test = x[item["train_indices"]], x[item["test_indices"]]
        assert np.array_equal(train, item["split_X_train"])
        assert np.array_equal(test, item["split_X_test"])
        if name == "wine":
            mean, sd = train.mean(axis=0), train.std(axis=0)
            sd[sd == 0] = mean[sd == 0] + 10e-10
            train, test = (train - mean) / sd, (test - mean) / sd
        for call in item["calls"]:
            assert np.array_equal(train, call["X_train"])
            assert np.array_equal(test, call["X_test"])
            graph = call["graph"]
            neighbours = {int(node): set() for node in graph["nodes"]}
            for u, v in graph["edges"]:
                neighbours[int(u)].add(int(v))
                neighbours[int(v)].add(int(u))
            degree = {u: len(v) + int(u in v) for u, v in neighbours.items()}
            n_train = len(train)
            classes = sorted(set(item["y_train"]))
            assert classes == list(range(len(classes)))
            for class_label in classes:
                expected = {i for i, label in enumerate(item["y_train"]) if label == class_label}
                assert neighbours[n + class_label] == expected
            def common(u, v):
                return (neighbours[u] & neighbours[v]) - {u, v}
            reproduced = []
            ties = 0
            for u in range(n_train, n):
                scores = []
                for v in range(n, n + len(classes)):
                    shared = sorted(common(u, v))
                    method = call["actual_predictor"]
                    if method == "CN":
                        score = len(shared)
                    elif method == "AA":
                        score = sum(1 / (math.log(degree[w]) + 10e-10) for w in shared)
                    elif method == "RA":
                        score = sum(1 / degree[w] for w in shared)
                    else:
                        score = sum(1 / (degree[w] - len(common(w, v))) +
                                    1 / (degree[w] - len(common(w, u))) for w in shared)
                    scores.append(score)
                winner = max(range(len(scores)), key=scores.__getitem__)
                ties += int(scores.count(scores[winner]) > 1)
                reproduced.append(winner)
            assert reproduced == call["prediction"], (name, call["actual_predictor"])
            call_check = {"dataset": name, "predictor": call["actual_predictor"],
                          "predictions_verified": len(reproduced), "tied_top_scores": ties,
                          "self_loops": sum(u == v for u, v in graph["edges"])}
            findings.append(call_check)
    changes = []
    for path in sorted((root / "source/original").rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root / "source/original")
        adapted = root / "source/adapted" / rel
        if path.read_bytes() != adapted.read_bytes():
            assert str(rel) in ["code/zoo_sample.py", "code/wine_sample.py"]
            old = ast.parse(path.read_text())
            new = ast.parse(adapted.read_text())
            new.body = [stmt for stmt in new.body if not (isinstance(stmt, ast.ImportFrom) and stmt.module == "pathlib")]
            class RestorePath(ast.NodeTransformer):
                def visit_Call(self, node):
                    self.generic_visit(node)
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "read_csv":
                        node.args[0] = ast.Constant('/data/' + path.stem.replace('_sample', '') + '.txt')
                    return node
            assert ast.dump(old) == ast.dump(RestorePath().visit(new))
            changes.append(str(rel))
    assert changes == ["code/wine_sample.py", "code/zoo_sample.py"]
    return {"passed": True, "coverage": [
        "Retained partitions equal RandomState(42) permutation and ceil(20% N) test size; train/test disjoint",
        "Labels match retained full inputs; Wine mean and population SD use only training rows",
        "Class vertices connect exactly to labelled training nodes, with no test-label edges",
        "Independent set-based CN/AA/RA/CS scoring of retained graph reproduces all 12 prediction vectors",
        "Only Zoo/Wine path adapters differ; AST after restoring those paths equals original"],
        "graph_checks": findings,
        "limits": ["No independent validation of upstream data authenticity", "Graph construction is inspected and frozen but nearest-neighbour selection is not independently reimplemented", "No new splits or true CN/AA runs for Iris/Zoo"]}
