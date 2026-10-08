# Research workflow evaluation (v0.3)

This directory is the evaluation controller's material. Candidate workspaces
receive frozen task inputs, a common resource interface, and (only in the
Allagma condition) the frozen workflow. They must not receive development
outputs, reference answers, scorer code or another candidate's work.

The frozen design is three tasks, two conditions and two fresh sessions per
condition. Development decisions and evidence are in `development/`. The
`frozen/freeze.json` manifest enumerates exact inputs, scorers, workflow source,
resource ceilings, model/settings observations and run order. Current progress
is in `progress.json`; terminal outcomes and complete traces are in `runs/`.
Ten sessions are terminal and reviewed; eight original packages are fully
verified. Both incomplete deliveries have verified science but lack explicit
review/material revision binding. The final two EMA sessions and release audit
remain pending.
Native sessions use the existing Codex account; scientific processes run only
on the local Mac. Final evaluation results are preserved even if later repaired
packages are needed for release.

The selected CORE-Bench task is CULP capsule `capsule-6460826`, from the public
training split at commit `e32a2980e72fe6eb04ee04eb749458f570625663`. It retains
its original task prompt, questions and numerical scoring rule.
This is a local evaluation of a selected task, not a CORE-Bench leaderboard run
or an estimate for the full benchmark.

Keep the original scorer outcomes, any documented compatibility correction and
the substantive evidence review separate. `summarize.py` aggregates these
receipts without treating a native process exit as scientific completion.
See [defects found after freezing](../../docs/v0.3/defects.md) for the shared MPS
configuration problem and inline-curve parser correction. The comparison cannot
measure the performance of a subsequently repaired GPU path.

The [retention procedure](RETENTION.md) preserves original scientific artifacts,
terminal requests/receipts and exact dependency identities. Archive supplements
repair transport omissions; they do not change candidate outcomes. Package
restoration, deterministic checks, substantive controller review and full
scientific reproduction establish different kinds of evidence and remain
separately labeled.

## Generate the descriptive comparison

```sh
python3 evals/research-v0.3/summarize.py --output /path/to/new-summary.json
python3 evals/research-v0.3/comparison.py \
  --summary /path/to/new-summary.json --destination /path/to/new-comparison
```

The postprocessor requires all twelve terminal outcomes and evidence reviews.
For an explicitly interim snapshot, `--allow-partial` labels the report partial,
retains pending assignments and excludes their accrued costs from outcome
contrasts. Missing measurements remain missing. It produces the six prespecified
within-task/replicate contrasts, two-session descriptive ranges and separate raw
usage fields; it does not add scientific seeds or infer broad superiority.
The [latest reviewed snapshot](comparisons/after-r10-reviewed/REPORT.md) is an interim artifact. Required scientific execution and package completeness are reported separately.

`python3 evals/research-v0.3/test_comparison.py -v` checks assignment completeness,
contrast direction, pending/missing handling and separate usage accounting.

## Verify the retained historical cohort

`evaluate.py verify` is the original launch guard: it requires the current source,
CLI and selected settings to match the freeze. A later corrected release is
expected to differ. Verify the stored historical source and retained packages
without changing that original guard:

```sh
python3 evals/research-v0.3/verify_archive.py --output /path/to/new-archive-check.json
```

This checks all frozen source hashes, all twelve prepared input sets against
the frozen materials/common interface, identical task profiles, retained input
identities, archive parts and queue supplements. It requires every package by
default. `--allow-missing-packages` produces an explicitly partial check during
evaluation. Neither mode reruns experiments or establishes scientific completion.
