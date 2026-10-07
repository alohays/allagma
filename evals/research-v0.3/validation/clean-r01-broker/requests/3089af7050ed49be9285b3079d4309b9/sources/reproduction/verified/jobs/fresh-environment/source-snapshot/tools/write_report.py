"""Render empirical tables directly from verified retained-data analysis."""
import argparse
import json
from common import ROOT, write_json

def render(analysis):
    summary = json.loads((analysis / "summary.json").read_text())
    table = (analysis / "results-table.md").read_text()
    graph_audit = json.loads((ROOT / "analysis/graph-audit.json").read_text())
    loop_counts = {dataset: len(next(r for r in graph_audit['results'] if r['dataset'] == dataset)['self_loop_nodes'])
                   for dataset in ['iris', 'zoo', 'wine']}
    max_error = max(r['max_score_error'] for r in graph_audit['results'])
    return f"""# Computational reproduction of CULP

The three supplied scripts were executed locally with their original algorithms,
parameters, preprocessing and seed-42 80/20 partitions. The six requested values
are in [report.json](report.json), in percent with the original question strings.
The table below is generated from retained per-example predictions and labels,
and agrees with the captured script stdout.

## Results

{table}
**Iris and Zoo label limitation:** their CN, AA, RA and CS print lines all call
`link_predictor='CS'`. These entries reproduce the labeled script outputs; they
do not establish CN or AA performance for those datasets. Wine passes `lp` to
the classifier, so its CN and AA entries measure those predictors. This upstream
behavior was preserved. No corrected-algorithm experiment was substituted.

## Question and methods

The question is whether the supplied CULP capsule can execute in this offline
environment and yield traceable answers to its original six questions. This is
a computational reproduction, not a new benchmark or a claim of paper-level
replication. The frozen [protocol](campaigns/culp-reproduction/protocol.json)
and [StudySpec](campaigns/culp-reproduction/study.json) specify the controls,
completion conditions, fixed boundaries and resource stops before execution.
The Allagma methods come from bundle `b-9a39b70665ba909edb8abc13`, resolved through
the [campaign lock](campaigns/culp-reproduction/lock.yaml).

CULP builds an undirected label-embedded graph from training and test features.
Training nodes connect to their class nodes; test nodes receive no class-label
edges. A symmetrized k-nearest-neighbor graph uses Manhattan distance, with
k=11 for Iris, k=2 for Zoo and k=12 for Wine. The classifier takes the argmax of
the class-link scores, resolving exact ties toward the first class index. Iris
uses scikit-learn's built-in data; Wine and Zoo use the supplied text files.
Wine alone standardizes each feature using the training mean and population
standard deviation. No stratification, hyperparameter search, alternative split
or feature transformation was introduced. The graph includes test features:
this is transductive classification and should not be described as fitting only
on training features, even though class-label edges use training labels only.

The read-only capsule was copied to [source/original](source/original).
[source/adapted](source/adapted) changes only the absolute `/data` paths in Wine
and Zoo to paths relative to their copied capsule, with an added `Path` import.
The source diff and hashes are retained in [provenance](evidence/provenance.json).
The capsule README lists no installable requirements or versions; dependencies
were inferred from imports and installed from the supplied offline wheels in an
isolated Python 3.11 environment. [Environment metadata](evidence/setup/environment.json)
records actual versions. Their availability does not establish parity with the
unavailable original environment.

## Execution, recovery and verification

All setup, scientific execution, analysis and executable checks use the common
local broker. [Attempt history](evidence/attempt-history.json) links exact argv,
start/end times, broker responses, stdout/stderr, source digests and resource
charges. The deliberately interrupted first marked experiment is retained,
excluded from the answer set and recovered under a new attempt identity. A
synthetic pilot uses hand-defined graphs and separated 1D anchors with known
predictions for all four predictors, plus accuracy and invalid-shape controls.
It uses no confirmation dataset and must pass before confirmation.

A read-only Python profile hook captures actual classifier arguments, graphs,
score matrices, predictions and held-out labels during the required script
execution. It does not replace scientific functions or change their returns.
The [raw manifest](evidence/raw-manifest.json) hashes the eligible evidence.
The [analysis](analysis/primary/summary.json) recomputes every printed percentage,
checks row coverage, train/test disjointness, preprocessing and parameter use,
and counts correct predictions through a second Python counting path.
[Separate-directory recomputation](analysis/recomputed/recomputation-check.json)
checks byte-identical answers, summary and table. [Graph verification](analysis/graph-audit.json)
independently reconstructs every link-score matrix from saved edges and checks
predictions, label edges and the exact source split. These checks support the
recorded computations; a zero exit code alone would not establish them.
[Review](review.json) records the precise reviewed material revision and bounded
assurance. [REPRODUCE.md](REPRODUCE.md) provides fresh-environment execution and
retained-data recomputation commands.

The first independent graph checker failed because it used simple adjacency-set
sizes as degrees and did not exclude endpoints from common-neighbor sets. Those
rules are wrong for NetworkX self-loops. A documented checker-only correction
counts self-loops twice in degree and excludes the endpoints, matching the
library semantics. The recovered check's maximum absolute score discrepancy is
{max_error:.3g}. The failed attempt and its original code are retained alongside
the successful retry; source experiments and answer numbers did not change.
[Verification revision](evidence/verification-revision.json) records the scope.
[Fresh environment verification](reproduction/verified/agreement.json) establishes
agreement of all six answers after recreating dependencies and rerunning all
three scripts. It is a reproducibility check, not another statistical replicate.

## Uncertainty and limitations

{summary['uncertainty']} The independent unit is a fixed dataset/split, not an
individual link-predictor print line or a retry. The small test denominators in
the table show the granularity of the observed accuracies; they do not provide
cross-split variance. No new seeds or datasets were run to select better results.
Test-feature participation in the graph also prevents a simple independent
Bernoulli interpretation of all test predictions.

The Iris/Zoo predictor-label mismatch is unresolved upstream and limits the
meaning of four requested answers. The source discards the first neighbor under
the assumption that it is the query itself. With tied duplicate feature rows,
this can leave self-loops: the saved graphs contain {loop_counts['iris']} for Iris,
{loop_counts['zoo']} for Zoo and {loop_counts['wine']} for Wine. The original graph
and NetworkX semantics were preserved; no nearest-neighbor tie rule was repaired.
Tie ordering and library versions may therefore affect historical reproduction.
The requested original outputs, scorer,
reference answers, environment and reproduction instructions were not supplied;
exact historical numerical agreement therefore cannot be tested. The review is
an agent critique plus deterministic artifact checks, not independent peer
review. No general performance superiority, novelty, calibration, robustness,
or reproduction of the full paper's experiments is established.

## Sources and evidence scope

1. Fadaee, Seyed Amin, and Amir Haeri, Maryam. *CULP: Classification Using Link
   Prediction*. Supplied capsule metadata and implementation, capsule-6460826.
   DOI supplied by the materials: https://doi.org/10.24433/CO.0609cc4f-8b95-4d94-8fd0-9456d262b3a5.
   The local metadata attributes the work and describes its intended method;
   a DOI was not resolved because network access is unavailable.
2. CORE-Bench public training capsule selection, benchmark commit
   `e32a2980e72fe6eb04ee04eb749458f570625663`, as stated in
   [SOURCES.md](inputs/materials/SOURCES.md). This is a local selected-task study,
   not a leaderboard run.
3. [Original task](inputs/materials/task.txt), [source evidence map](evidence/literature-map.json),
   and [artifact manifest](artifact-manifest.json). Source metadata identifies
   provenance; the execution artifacts support the numerical claims.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", default="analysis/primary")
    parser.add_argument("--out", default="REPORT.md")
    args = parser.parse_args()
    (ROOT / args.out).write_text(render(ROOT / args.analysis))
