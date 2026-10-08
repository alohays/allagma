"""Controller-owned adjacency-set CULP equations; no capsule imports."""
import math
import numpy as np


def predictions(data, predictor):
    n, m = len(data['X_train']), len(data['X_test'])
    classes = len(np.unique(data['y_train']))
    adjacent = [set() for _ in range(n + m + classes)]
    for a, b in data['graph_edges']:
        adjacent[int(a)].add(int(b)); adjacent[int(b)].add(int(a))
    degree = [len(neighbors) + int(i in neighbors) for i, neighbors in enumerate(adjacent)]
    def common(a, b):
        return (adjacent[a] & adjacent[b]) - {a, b}
    scores = np.zeros((m, classes))
    for row, node in enumerate(range(n, n + m)):
        for label, class_node in enumerate(range(n + m, n + m + classes)):
            shared = common(node, class_node)
            if predictor == 'CN':
                value = len(shared)
            elif predictor == 'AA':
                value = sum(1 / (math.log(degree[v]) + 1e-9) for v in sorted(shared))
            elif predictor == 'RA':
                value = sum(1 / degree[v] for v in sorted(shared))
            else:
                assert predictor == 'CS'
                value = sum(1 / (degree[v] - len(common(v, class_node)))
                            + 1 / (degree[v] - len(common(v, node))) for v in sorted(shared))
            scores[row, label] = value
    return scores.argmax(axis=1)
