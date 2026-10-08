# A reproducible toy comparison of two mean estimators

## Abstract

We compared the sample mean with the sample mean plus 0.25 for a zero-mean
synthetic distribution. The biased estimator had higher average squared error across 24
confirmation seeds. This is a workflow demonstration with a known analytical
expectation, not a claim of scientific novelty or agent quality.

## Question and prior evidence

Does adding a constant bias increase expected squared error? For independent
Rademacher outcomes, E[X] = 0 and Var(X) = 1. The sample mean has MSE 1/n;
adding b gives MSE 1/n + b². This algebraic expectation is distinct from the
realized estimates below. The study-owned derivation is the only prior source
needed for this known-answer demonstration [1].

## Methods

The frozen protocol used 64 observations per seed,
Python's recorded pseudorandom generator, and separate pilot and confirmation
seeds. Balanced and zero-output controls qualified the runner and evaluator.
Failed and interrupted attempts were excluded; retries retained distinct IDs.
Confirmation differences are paired within each seed. The standard error is
the sample standard deviation of paired differences divided by the square root
of the number of seeds. The interval uses ±1.96 standard errors.
Sensitivity analysis recalculates the mean difference after omitting each
confirmation seed once. This measures sensitivity to individual seeds, not to
other distributions or estimator definitions.

## Results

| Quantity | Recomputed value |
| --- | ---: |
| Confirmation replicates | 24 |
| Sample-mean MSE | 0.01529948 |
| Biased-estimator MSE | 0.08040365 |
| Paired difference | 0.06510417 |
| Approximate 95% interval | [0.03985104, 0.09035729] |

Claim C1 records the average comparison. Claim C2 tests an overstrong universal
ordering: counterexample seeds were [104, 108, 118, 121]. A positive
average does not imply that every replicate favors the sample mean.

![Paired squared-error differences by confirmation seed](../outputs/paired-differences.svg)

Each dot is one confirmation seed. Positive values favor the sample mean;
the dashed line is the average difference. Claim C3 records the sensitivity
result: Leave-one-seed-out mean differences ranged from 0.06182065 to 0.07269022; 24 of 24 retained means were positive.

## Evidence and reproducibility

The [claim ledger](claims.json) links each statement to the
[analysis record](../record.json) through content-addressed study-relative
references. Run the bundled `audit` command to check the raw manifest, rerun
analysis and regenerate this manuscript. The analysis record and raw manifest
are also at `../record.json` and `../raw-manifest.json` relative to this directory.

## Limitations

This synthetic known-answer problem does not establish novelty or improve an LLM research agent. The 95% interval is a normal approximation over seed replicates, not an exact small-sample guarantee. Averages do not establish an ordering for every individual seed. Deterministic reproduction does not substitute for independent
scientific review. No paid API, language model or GPU was used in the study.

## Bibliography

[1] Toy study authors (2026). Bias–variance identity for a Rademacher mean.
Study-owned `domain/derivation.md`, frozen in the campaign's code manifest.
Metadata and support assessments are separately recorded in `evidence-map.json`.
