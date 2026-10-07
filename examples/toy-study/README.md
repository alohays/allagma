# Toy study: bias and squared error

The question is whether adding 0.25 to a sample mean increases expected squared
error for a zero-mean Rademacher distribution. The answer has a known analytical
derivation, so the study can check its runner/evaluator independently of an LLM.
This is a research-workflow demonstration with a short manuscript, not novel
science or a model benchmark.

```sh
python3 -m allagma toy --destination work/toy-run
```

The workflow uses zero and balanced controls at pilot seeds 1 and 2, then 24
confirmation seeds 100–123 with 64 observations each. One runner invocation
actually raises an error; another reaches a checkpoint and is terminated. Each
retry has its own identity. Pilot and failed/interrupted data are excluded from
confirmation analysis. The default budget is 28 attempts, 60 seconds of recorded
execution time, zero money and a five-second per-attempt bound.

The primary statistic is the mean paired difference in squared error. The
reported interval is the mean ±1.96 standard errors across independent seeds,
an explicitly approximate uncertainty calculation. A separate overstrong claim
about every individual seed is tested against counterexamples.
Protocol revision `toy-v2` also prespecifies leave-one-seed-out sensitivity:
recalculate the mean after omitting each confirmation seed once. A separate
table and claim record the resulting range. A deterministic SVG figure shows
every paired difference, zero, and the overall mean. These artifacts are
recomputed by the audit without plotting-library dependencies. The first
walkthrough campaign is still named `toy-v1`; the campaign ID and protocol
revision are distinct.

| Generated location | Evidence |
| --- | --- |
| `brief.json`, `evidence-map.json`, `protocol.json` | Question, mathematical source/support map and frozen plan |
| `.allagma/lock.yaml`, `.allagma/bundles/` | Exact release, composition and source |
| `campaigns/toy-v1/study.json`, `lock.yaml`, `materials/` | Campaign identity and frozen scientific programs |
| `campaigns/toy-v1/runs/*/attempts/*/` | Inputs, raw data, evaluation, logs, started and terminal records |
| `campaigns/toy-v1/analyses/a001/raw-manifest.json` | Included and excluded observations and their identities |
| `campaigns/toy-v1/analyses/a001/outputs/` | Summary, per-seed and sensitivity tables, and SVG figure |
| `campaigns/toy-v1/analyses/a001/paper/` | Claims and manuscript |
| `campaigns/toy-v1/analyses/a001/reviews/` | Exact-revision deterministic reviews and reproduction reports |
| `walkthrough.json` | Host packaging route and final artifact handoff |

Run `campaign audit --study work/toy-run --campaign toy-v1` from the source
checkout, or use the exact `tools/allagma.py` inside the campaign's bundle. The
source CLI automatically dispatches campaign work to that pinned helper. A new
audit appends a review; it does not replace the prior review.

To see a limited package, create a toy study with a lower attempt ceiling before
campaign creation. The conformance and acceptance commands exercise this case,
along with corrupted evidence, stale claims, separate analysis revisions,
controller crashes and historical resume after updates.
