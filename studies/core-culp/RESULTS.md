# Verified local CULP reproduction

A native Codex session reproduced the graph-classification capsule and returned
all six requested answers. Its report also explains why four printed predictor
labels do not describe the predictors the source actually called.

| Dataset | Requested printed label | Actual predictor | Accuracy |
| --- | --- | --- | ---: |
| Iris | CN | CS | 100% |
| Iris | AA | CS | 100% |
| Zoo | CN | CS | 100% |
| Zoo | AA | CS | 100% |
| Wine | CN | CN | 97.22% |
| Wine | AA | AA | 97.22% |

The unchanged original CORE-Bench scorer accepts **6/6 answers**. The source's
Iris/Zoo label defect is preserved and explicitly interpreted; these rows do not
measure actual CN/AA calls. Only the two absolute data paths were adapted, with
their required `Path` imports. All other capsule source/data bytes were retained.
See the [protected scoring receipt](../../evals/research-v0.3/runs/r01/score.json)
and [controller review](../../evals/research-v0.3/runs/r01/substantive-review.json).

The agent completed the initial brief without subsequent coordinator messages.
It preserved a deliberately interrupted Iris attempt, recovered under a new ID,
and independently found and corrected a self-loop error in its own graph checker.
The source-generated graphs and numerical answers were unchanged by that repair.
Fresh-environment execution, raw-only reanalysis, and ordinary script execution
without the capture hook agree. The fixed transductive splits provide no
cross-split or population uncertainty estimate; no general superiority claim is
made. Review combines source inspection and deterministic checks with explicitly
provisional model critique, not independent scientific peer review.

## Execution and verification

The first fully verified Allagma package in the frozen run order is **r01**
(replicate 2). It is the illustrative package selected by the prespecified
criteria. The [12-run comparison is complete](../../docs/v0.3/COMPARISON.md);
this individual result does not establish a workflow advantage.

The run consumed 76.26 seconds of scientific computation and 15.43 seconds of
setup. Native wall time was 1,921.48 seconds. Exact token and measured resource
fields are retained with the [native receipt](../../evals/research-v0.3/runs/r01/sessions/evaluation/native/session.json)
and controller ledger.

## Restore the complete research package

The [package index](../../evals/research-v0.3/runs/r01/package/package-index.json)
identifies the unchanged report, source, protocol, arrays, attempts, claims,
review, reproduction commands and software wheels by hash. Restore into a new
directory, hydrating exact software dependencies:

```sh
python3 evals/research-v0.3/retention.py restore \
  --source evals/research-v0.3/runs/r01/package \
  --destination /path/to/new-culp-package --download-wheels
```

An exact local wheel cache may be supplied instead of downloading. After
restoration, read `REPORT.md`, `REPRODUCE.md` and `submission.json`. Use the
[standalone broker driver](../../docs/research-workspaces.md) to service the
delivered reproduction command under a new finite validation profile. Run the
full-study and raw-data recomputation commands separately and retain their
outcomes. The [clean-checkout release check](../../evals/research-v0.3/validation/clean-r01-results/verification.json) passed: a new Git clone restored all exact files and dependencies, created a fresh environment, reran the complete study, and recomputed the retained-data results. Both answer sets equal the original package.
