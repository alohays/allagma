"""Independent arithmetic checks of retained arrays; never runs source experiments."""
import csv
import math
from pathlib import Path
import numpy as np


def check_arrays(a, call, dataset, root):
    train, test = a["train"], a["test"]
    ytrain, ytest = a["train_labels"], a["test_labels"]
    raw, labels, pred = a["raw_data"], a["raw_labels"], a["prediction"]
    n, m, total = len(train), len(test), len(raw)
    classes = np.unique(ytrain)
    c = len(classes)
    assert (total, raw.shape[1]) == {"iris": (150, 4), "zoo": (101, 16), "wine": (178, 13)}[dataset]
    assert n + m == total and m == math.ceil(0.2 * total)
    assert np.array_equal(classes, np.arange(c)), "Source assumes contiguous training classes"
    assert set(np.unique(labels)) == set(classes), "A source class is absent from training"
    assert all(np.all(np.isfinite(a[name])) for name in a.files)
    assert pred.shape == (m,) and ytest.shape == (m,)
    assert np.all((0 <= pred) & (pred < c))
    order = np.random.RandomState(42).permutation(total)
    test_indices, train_indices = order[:m], order[m:]
    np.testing.assert_array_equal(ytest, labels[test_indices])
    np.testing.assert_array_equal(ytrain, labels[train_indices])
    expected_train, expected_test = raw[train_indices], raw[test_indices]
    norm = None
    if dataset == "wine":
        mean, scale = expected_train.mean(axis=0), expected_train.std(axis=0, ddof=0)
        zero = scale == 0
        scale[zero] = mean[zero] + 10e-10
        expected_train, expected_test = (expected_train - mean) / scale, (expected_test - mean) / scale
        norm = {"training_mean": mean.tolist(), "training_population_std": scale.tolist(),
                "zero_variance_features": np.flatnonzero(zero).tolist()}
    np.testing.assert_allclose(train, expected_train, rtol=0, atol=1e-13)
    np.testing.assert_allclose(test, expected_test, rtol=0, atol=1e-13)
    if dataset in ("wine", "zoo"):
        with (root / f"source/original/data/{dataset}.txt").open() as stream:
            rows = list(csv.reader(stream))
        if dataset == "wine":
            source_data = np.array([[float(v) for v in row[1:]] for row in rows])
            source_labels = np.array([int(row[0]) - 1 for row in rows])
        else:
            source_data = np.array([[float(v) for v in row[1:17]] for row in rows])
            source_labels = np.array([int(row[17]) - 1 for row in rows])
        np.testing.assert_array_equal(raw, source_data)
        np.testing.assert_array_equal(labels, source_labels)

    edges = a["graph_edges"]
    assert edges.ndim == 2 and edges.shape[1] == 2
    assert np.all((edges >= 0) & (edges < total + c))
    canonical = {tuple(sorted(map(int, edge))) for edge in edges}
    assert len(canonical) == len(edges), "Duplicate undirected edges"
    adjacency = [set() for _ in range(total + c)]
    for u, v in edges:
        adjacency[u].add(int(v))
        adjacency[v].add(int(u))
    class_edges = {(u, v) for u, v in canonical if v >= total}
    expected_class_edges = {(i, total + int(label)) for i, label in enumerate(ytrain)}
    assert class_edges == expected_class_edges, "Class links must use training labels only"
    assert call["graph_nodes"] == total + c and call["graph_edges"] == len(edges)
    data = np.concatenate([train, test])
    distances = np.abs(data[:, None] - data[None, :]).sum(axis=2)
    k = call["k"]
    sorted_distances = np.sort(distances, axis=1)
    radii = sorted_distances[:, k]
    invalid_edges, missing_mandatory, insufficient_neighbors = [], [], []
    boundary_ties = []
    for i in range(total):
        row = distances[i]
        candidate = {j for j in adjacency[i] if j < total and row[j] <= radii[i] + 1e-12}
        if len(candidate) < k:
            insufficient_neighbors.append(i)
        # The source discards the first zero-distance item, which need not be self.
        mandatory = set(np.flatnonzero((row > 1e-12) & (row < radii[i] - 1e-12)))
        if not mandatory.issubset(adjacency[i]):
            missing_mandatory.append(i)
        if math.isclose(sorted_distances[i, k + 1], radii[i], rel_tol=0, abs_tol=1e-12):
            boundary_ties.append(i)
    for u, v in canonical:
        if v < total and distances[u, v] > max(radii[u], radii[v]) + 1e-12:
            invalid_edges.append([u, v])
    assert not invalid_edges and not missing_mandatory and not insufficient_neighbors
    self_loops = sorted(u for u, v in canonical if u == v)
    zero_distance_duplicate_rows = np.flatnonzero((distances < 1e-12).sum(axis=1) > 1).tolist()
    assert set(self_loops).issubset(zero_distance_duplicate_rows)
    exact_unique_graph = None
    if not boundary_ties and not zero_distance_duplicate_rows:
        expected_edges = set(expected_class_edges)
        for i in range(total):
            for j in np.argsort(distances[i])[1:k + 1]:
                expected_edges.add(tuple(sorted([i, int(j)])))
        assert expected_edges == canonical
        exact_unique_graph = True

    # An undirected self-loop contributes twice to NetworkX degree.
    degree = [len(a) + (i in a) for i, a in enumerate(adjacency)]

    def common(u, v):
        return (adjacency[u] & adjacency[v]) - {u, v}

    scores = np.zeros((m, c), dtype=float)
    method = call["actual_predictor"]
    for ti, i in enumerate(range(n, total)):
        for ci, j in enumerate(range(total, total + c)):
            neighbors = sorted(common(i, j))
            if method == "CN":
                score = len(neighbors)
            elif method == "AA":
                score = math.fsum(1 / (math.log(degree[v]) + 10e-10) for v in neighbors)
            elif method == "RA":
                score = math.fsum(1 / degree[v] for v in neighbors)
            elif method == "CS":
                terms = []
                for v in neighbors:
                    deg1, deg2 = degree[v] - len(common(v, j)), degree[v] - len(common(v, i))
                    assert deg1 > 0 and deg2 > 0
                    terms.append(1 / deg1 + 1 / deg2)
                score = math.fsum(terms)
            else:
                raise AssertionError(method)
            scores[ti, ci] = score
    independent_pred = scores.argmax(axis=1)
    exact_match = np.array_equal(independent_pred, pred)
    close_to_max = np.isclose(scores, scores.max(axis=1, keepdims=True), rtol=0, atol=1e-12)
    assert np.all(close_to_max[np.arange(m), pred]), "Saved prediction not a maximizing class"
    # Permit only summation-order ties; expose any exact argmax differences.
    mismatches = np.flatnonzero(independent_pred != pred).tolist()
    tie_rows = np.flatnonzero(close_to_max.sum(axis=1) > 1).tolist()
    assert set(mismatches).issubset(tie_rows)
    correct = int(np.count_nonzero(pred == ytest))
    confusion = np.zeros((c, c), dtype=np.int64)
    for truth, prediction in zip(ytest, pred):
        confusion[truth, prediction] += 1
    return {"correct": correct, "n_test": m, "n_train": n, "n_features": raw.shape[1],
            "accuracy_percent": round(100 * correct / m, 2), "accuracy_fraction": correct / m,
            "train_class_counts": np.bincount(ytrain, minlength=c).tolist(),
            "test_class_counts": np.bincount(ytest, minlength=c).tolist(),
            "confusion_matrix": confusion.tolist(), "error_test_positions": np.flatnonzero(pred != ytest).tolist(),
            "error_source_rows": test_indices[pred != ytest].tolist(),
            "split_matches_random_state_42": True, "normalization": norm,
            "input_data_match": "supplied text verified" if dataset != "iris" else "archived sklearn 1.5.2 built-in arrays",
            "graph": {"nodes": total + c, "edges": len(edges), "class_edges": len(class_edges),
                      "self_loop_nodes": self_loops, "self_loop_count": len(self_loops),
                      "duplicate_feature_rows": zero_distance_duplicate_rows,
                      "duplicate_feature_row_count": len(zero_distance_duplicate_rows),
                      "k_boundary_tie_nodes": boundary_ties, "k_boundary_tie_count": len(boundary_ties),
                      "exact_brute_graph_match_when_no_ties": exact_unique_graph,
                      "distance_and_class_edge_constraints_passed": True,
                      "audit_scope": "necessary kNN union constraints; tied directed neighbor choices not uniquely reconstructed"},
            "independent_predictor": {"exact_argmax_match": bool(exact_match), "argmax_mismatch_rows": mismatches,
                                      "near_tie_rows": tie_rows, "all_zero_score_rows": np.flatnonzero(np.all(scores == 0, axis=1)).tolist(),
                                      "maximizer_tolerance": 1e-12}}, scores, train_indices, test_indices
