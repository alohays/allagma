"""Generate a short manuscript and claim ledger from verified analysis files."""
import hashlib
import json
from pathlib import Path
import sys


def ref(study, path):
    return {"path": path.relative_to(study).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "media_type": "application/json", "retention": "retain-with-study"}


def write(study, analysis_path, output):
    analysis = json.loads(analysis_path.read_text())
    summary_ref = next(item for item in analysis["outputs"] if item["path"].endswith("summary.json"))
    summary_path = study / summary_ref["path"]
    if hashlib.sha256(summary_path.read_bytes()).hexdigest() != summary_ref["sha256"]:
        raise ValueError("Summary digest mismatch")
    values = json.loads(summary_path.read_text())
    lower, upper = values["ci95_normal"]
    supported = lower > 0
    interpretation = "The biased estimator had higher average squared error" if supported else "The direction of the average error difference was inconclusive"
    scope = f"{values['replicates']} prespecified seeds, {values['samples_per_replicate']} Rademacher observations per seed, target zero, additive bias 0.25"
    limits = ["This synthetic known-answer problem does not establish novelty or improve an LLM research agent.",
              "The 95% interval is a normal approximation over seed replicates, not an exact small-sample guarantee.",
              "Averages do not establish an ordering for every individual seed."]
    if analysis["configuration"]["partial"]:
        limits.append("The campaign stopped before the full prespecified run plan completed.")
    common = {"schema_version": "0.2", "record_type": "ClaimRecord", "supporting": [summary_ref],
              "contradicting": [], "dependencies": [ref(study, analysis_path), analysis["raw_manifest"], *analysis["dependencies"]],
              "scope": scope, "limitations": limits, "supersedes": None}
    claims = [{**common, "claim_id": "C1", "text": interpretation + f" (paired MSE difference {values['difference']:.8f}; approximate 95% CI [{lower:.8f}, {upper:.8f}]).",
               "status": "supported" if supported else "inconclusive"},
              {**common, "claim_id": "C2", "text": "The biased estimator has greater squared error on every individual confirmation seed.",
               "supporting": [], "contradicting": [summary_ref] if values["counterexample_seeds"] else [],
               "status": "contradicted" if values["counterexample_seeds"] else "inconclusive"}]
    output.mkdir(parents=True, exist_ok=False)
    (output / "claims.json").write_text(json.dumps(claims, sort_keys=True, indent=2, allow_nan=False) + "\n")
    paper = f'''# A reproducible toy comparison of two mean estimators

## Abstract

We compared the sample mean with the sample mean plus 0.25 for a zero-mean
synthetic distribution. {interpretation.lower()} across {values['replicates']}
confirmation seeds. This is a workflow demonstration with a known analytical
expectation, not a claim of scientific novelty or agent quality.

## Question and prior evidence

Does adding a constant bias increase expected squared error? For independent
Rademacher outcomes, E[X] = 0 and Var(X) = 1. The sample mean has MSE 1/n;
adding b gives MSE 1/n + b². This algebraic expectation is distinct from the
realized estimates below. The study-owned derivation is the only prior source
needed for this known-answer demonstration [1].

## Methods

The frozen protocol used {values['samples_per_replicate']} observations per seed,
Python's recorded pseudorandom generator, and separate pilot and confirmation
seeds. Balanced and zero-output controls qualified the runner and evaluator.
Failed and interrupted attempts were excluded; retries retained distinct IDs.
Confirmation differences are paired within each seed. The standard error is
the sample standard deviation of paired differences divided by the square root
of the number of seeds. The interval uses ±1.96 standard errors.

## Results

| Quantity | Recomputed value |
| --- | ---: |
| Confirmation replicates | {values['replicates']} |
| Sample-mean MSE | {values['mean_mse']:.8f} |
| Biased-estimator MSE | {values['biased_mse']:.8f} |
| Paired difference | {values['difference']:.8f} |
| Approximate 95% interval | [{lower:.8f}, {upper:.8f}] |

Claim C1 records the average comparison. Claim C2 tests an overstrong universal
ordering: counterexample seeds were {values['counterexample_seeds']}. A positive
average does not imply that every replicate favors the sample mean.

## Evidence and reproducibility

The [claim ledger](claims.json) links each statement to the
[analysis record](../record.json) through content-addressed study-relative
references. Run the bundled `audit` command to check the raw manifest, rerun
analysis and regenerate this manuscript. The analysis record and raw manifest
are also at `../record.json` and `../raw-manifest.json` relative to this directory.

## Limitations

{' '.join(limits)} Deterministic reproduction does not substitute for independent
scientific review. No paid API, language model or GPU was used in the study.

## Bibliography

[1] Toy study authors (2026). Bias–variance identity for a Rademacher mean.
Study-owned `domain/derivation.md`, frozen in the campaign's code manifest.
Metadata and support assessments are separately recorded in `evidence-map.json`.
'''
    (output / "manuscript.md").write_text(paper)


if __name__ == "__main__":
    write(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
