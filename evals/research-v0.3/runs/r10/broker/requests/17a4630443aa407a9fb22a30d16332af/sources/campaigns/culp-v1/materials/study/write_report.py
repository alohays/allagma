"""Generate answer file, manuscript and CULP-specific measurement references."""
import argparse
import shutil
from common import ROOT, read, ref, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", default="analysis/main")
    parser.add_argument("--output", default=".")
    args = parser.parse_args()
    analysis = ROOT / args.analysis
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    result = read(analysis / "results.json")
    rows = result["rows"]
    write(output / "report.json", read(analysis / "report.json"))
    table = (analysis / "results-table.md").read_text()
    selected = [r for r in rows if r["printed_label"] in ("CN", "AA")]
    measured = []
    for dataset in ("iris", "zoo", "wine"):
        rr = [r for r in rows if r["dataset"] == dataset]
        measured.append({"dataset": dataset, "seed": 42, "phase": "confirmation", "device": "cpu",
            "attempt_id": rr[0]["attempt_id"], "source_revision": ref(ROOT / "provenance/source-manifest.json")["sha256"],
            "calls": [{"printed_label": r["printed_label"], "executed_predictor": r["executed_predictor"],
                       "arrays": r["arrays"]["path"], "metrics": {"accuracy": r["accuracy"],
                       "accuracy_percent": r["accuracy_percent"], "correct": r["correct"], "test_n": r["test_n"]}}
                      for r in rr]})
    write(output / "measurements.json", {"format": "research-measurements-v1", "task_id": "core-culp",
        "protocol": "campaigns/culp-v1/protocol.json", "runs": measured,
        "schema_note": "MEASUREMENTS.md defines EMA and modular-addition fields only. This CULP extension retains its generic envelope and uses per-call predictions, labels, source data and graph edges; there are no trained weights."})
    selfloops = ", ".join(f"{d.capitalize()}: {next(r['self_loops'] for r in rows if r['dataset'] == d)}"
                          for d in ("iris", "zoo", "wine"))
    text = f'''# Computational reproduction of CULP

This package executes the three supplied scripts and answers the six original task questions using their original printed labels and scoring. The results below describe this supplied capsule with the documented local environment. No original output, reference answer, original environment, or paper PDF was available for numerical comparison.

## Task answers and their interpretation

{table}
The six keys in [report.json](report.json) are copied exactly from [task.txt](inputs/materials/task.txt), including the original spelling “acccuracy”. Values are numeric percentages, rounded to two decimal places exactly as the scripts do. The table includes RA and CS as additional execution evidence because each required script prints all four labels.

**Iris and Zoo do not run CN or AA.** Their loops print CN, AA, RA and CS while passing the literal `link_predictor='CS'` on every call. Thus their requested CN/AA answers are the scores printed under those labels, and establish only CS performance for those fixed splits. Wine passes `link_predictor=lp`, so its printed CN and AA labels identify the algorithms actually used. This upstream limitation is preserved, not repaired to change the task answers. Runtime call records corroborate the source inspection.

## Materials and method

The supplied source is CORE-Bench training capsule 6460826, benchmark commit `e32a2980e72fe6eb04ee04eb749458f570625663`, capsule DOI [10.24433/CO.0609cc4f-8b95-4d94-8fd0-9456d262b3a5](https://doi.org/10.24433/CO.0609cc4f-8b95-4d94-8fd0-9456d262b3a5). The read-only inputs were copied to [work/capsule](work/capsule). [Source hashes](provenance/source-manifest.json) and the exact [patch](provenance/platform.patch) retain original and adapted provenance. Only Wine and Zoo absolute `/data/` paths were changed to file-relative paths; Iris and all CULP library files retain their original bytes.

The README does not contain a dependency list or version pins, and the referenced `run.sh` is absent. Imports require NumPy, scikit-learn, pandas and NetworkX, with SciPy, joblib, threadpoolctl, python-dateutil, six, pytz and tzdata as dependencies. They were installed offline in an isolated Python environment from the supplied wheelhouse. [Environment metadata](provenance/environment.json) records the actual Python/platform and package versions; [requirements-lock.txt](requirements-lock.txt) pins installed scientific dependencies. This establishes local executability in the supplied modern environment, not equivalence to an unavailable original environment.

All scripts use `train_test_split(test_size=0.2, random_state=42)` without stratification, Manhattan distance and one nearest-neighbor worker. Iris uses k=11, Zoo k=2 and Wine k=12. Iris and Zoo features are unchanged; Wine normalization uses only training feature means and population standard deviations, with its original zero-variance branch preserved. The original labels, partitions, metric, algorithms and rounding are fixed by [protocol v1](campaigns/culp-v1/protocol.json), frozen before confirmation. The known-answer pilot uses synthetic points and graphs, with no confirmation dataset or seed used for tuning.

CULP builds an undirected label-embedded graph from both train and test features. Training vertices connect to class vertices; test labels are used only for evaluation. The procedure is transductive: test feature geometry affects the graph. Calling it a strictly inductive hold-out classifier would overstate what was evaluated. The nearest-neighbor implementation drops the first neighbor under a self-neighbor assumption; tied duplicate points may violate that assumption. Retained graphs contain these self-loop counts: {selfloops}. The original graph construction is preserved. `argmax` resolves equal class scores to the first class, which is another source-defined choice.

## Execution and recovery

All setup, experiments, pilot checks, numerical analysis and verification used [the common local broker](inputs/COMPUTE.md), within the supplied [resource profile](inputs/RESOURCES.json). Sequential workers used the CPU. Each command and authoritative broker response is retained in [evidence/broker](evidence/broker), with a [history index](evidence/broker-history.json). The first marked substantive script attempt received the configured controlled interruption. Its request, response and any partial artifacts are retained and excluded from the successful raw manifest. Recovery used a new attempt identity after the authoritative interruption response; no observation timeout was treated as completion or cancellation. [Recovery details](evidence/recovery.json) identify the interrupted request and successor.

The study applies the pinned Allagma bundle `b-9a39b70665ba909edb8abc13` through the [campaign lock](campaigns/culp-v1/lock.yaml). [Workflow records](campaigns/culp-v1) preserve scope, protocol, qualification, attempts, analysis and claims. The installed deterministic checklist is used within its stated evidence-checking scope.

## Verification and uncertainty

The [pilot](evidence/pilot/qualification.json) checks analytically soluble graphs for all four link predictors, a complete synthetic CULP call, tie handling, accuracy rounding and output parsing. It does not prove every graph case correct. The [raw manifest](evidence/raw-manifest.json) selects only successful confirmation outputs, and hashes every source-linked call artifact. Each NPZ stores full input features and labels, actual transformed train/test arrays, predictions and graph edges and is loadable with `allow_pickle=False`.

[Analysis](analysis/main/results.json) recomputes each original accuracy from saved prediction/label pairs and checks its agreement with raw stdout. A separate implementation computes link scores directly from retained graph adjacency using the recorded actual algorithm; it checks all predictions without importing or rerunning the capsule. Recomputing the same raw evidence in [a separate directory](analysis/recomputed/comparison.json) checks numerical reproducibility. The [technical audit](evidence/verification.json) states the checks actually run, including original partitions, normalization, source edits, evidence hashes and exact task keys. A process exit code alone establishes none of these scientific connections.

There is one prescribed split per dataset. The independent observational unit for this reproduction is that fixed execution configuration; deterministic repeated loops and reruns are not independent replicates. We report exact correct/test counts and descriptive accuracy, without a confidence interval. Test cases share a graph, so a simple independent-binomial interval would require assumptions not established here. No split-to-split uncertainty, population accuracy, statistical ranking, or Iris/Zoo CN-versus-AA comparison is estimated. Rounded equality of two accuracies also need not imply identical predictions.

## Critical assessment and completion scope

The supplied script-execution task is complete when all three required scripts have terminal successful evidence, all six scores have been regenerated from retained data, and the documented artifact and review checks pass. The [submission](submission.json), [review](review.json) and [artifact manifest](artifact-manifest.json) record the final status and exact revisions. The review combines deterministic checks with author critique. It is not independent peer review, and its verdict is limited to the material digest it records.

The capsule's broader abstract claims novelty and competitiveness against other classifiers. Neither claim is verified here: the supplied three demonstrations contain no external baselines or multi-split study, and external literature access was unavailable. The source-label bug blocks interpreting four requested values as actual CN/AA measurements, but does not prevent reproducing the original printed task outputs. No additional algorithm-corrected experiment is substituted for the required scripts. [REPRODUCE.md](REPRODUCE.md) provides separate commands for fresh-environment execution and retained-data recomputation.

## Bibliography and support

1. Fadaee, Seyed Amin, and Maryam Amir Haeri. *CULP: Classification Using Link Prediction*. Supplied capsule metadata, [metadata.yml](inputs/materials/capsule-6460826/metadata/metadata.yml), and capsule DOI above. Names and title are supported by the local metadata; the paper's full bibliographic record and scientific claims were not independently retrieved.
2. Supplied [README](inputs/materials/capsule-6460826/code/README.md), algorithm source, dataset files, [SOURCES.md](inputs/materials/SOURCES.md) and original [task.txt](inputs/materials/task.txt). These support the reproduced code and task definition; they do not supply original reference answers.
3. [Evidence map](evidence/literature-map.json) separates local source support from unavailable external verification.
'''
    (output / "REPORT.md").write_text(text)
    print("Wrote report.json, REPORT.md and measurements.json from verified analysis.")


if __name__ == "__main__":
    main()
