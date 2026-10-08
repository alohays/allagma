"""Known-answer qualification uses only synthetic data, never capsule datasets."""
import math
import sys
import numpy as np
import networkx as nx
from common import ROOT, write
from analyze import accuracy, independent_scores, LINE, questions
sys.path.insert(0, str(ROOT / "work/capsule/code"))
from culp import link_predictors
from culp.classifier import culp

edges = np.asarray([(0, 6), (1, 6), (2, 7), (3, 7), (4, 0), (4, 1), (5, 2), (5, 3)])
graph = nx.Graph()
graph.add_nodes_from(range(8))
graph.add_edges_from(edges)
checks = []
methods = {"CN": link_predictors.common_neighbors, "AA": link_predictors.adamic_adar,
           "RA": link_predictors.resource_allocation_index, "CS": link_predictors.compatibility_score}
for name, fn in methods.items():
    expected = np.asarray([0, 1])
    assert np.array_equal(fn(graph, (4, 6), (6, 8)), expected)
    scores = independent_scores(edges, 4, 2, 2, name)
    diagonal = {"CN": 2, "AA": 2 / (math.log(2) + 1e-9), "RA": 1, "CS": 2}[name]
    assert np.allclose(scores, np.diag([diagonal, diagonal]), rtol=1e-12, atol=1e-12)
    checks.append(f"{name}: analytical two-class graph scores and upstream predictions agree")
empty = nx.empty_graph(8)
for name, fn in methods.items():
    assert np.array_equal(fn(empty, (4, 6), (6, 8)), [0, 0])
checks.append("All four algorithms select first class under all-zero score ties")
for name in methods:
    result = culp(np.asarray([[0.], [1.], [10.], [11.]]), np.asarray([0, 0, 1, 1]),
                  np.asarray([[0.1], [10.1]]), name, "manhattan", 1)
    assert np.array_equal(result, [0, 1])
checks.append("Complete upstream CULP pipeline predicts two separated synthetic classes")
assert accuracy(np.asarray([0, 0, 0]), np.asarray([0, 1, 0])) == (2, 3, 66.67)
assert len(LINE.findall("Prediction Accuracy for Iris Dataset (λ=CN) = 66.67%")) == 1
assert len(questions()) == 6
checks.append("Independent accuracy, source-output parser and exact task key extraction known answers pass")
write(ROOT / "evidence/pilot/qualification.json", {
    "status": "pass", "seed": 314159, "data": "Analytically constructed synthetic graphs and points; no randomness",
    "checks": checks, "independent_of_confirmation": True,
    "scope": "Basic algorithm and scoring controls; does not establish correctness on all graphs or paper claims"})
print("Pilot qualification passed:")
print("\n".join(checks))
