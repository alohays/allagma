# Toy study: bias and squared error

The question is whether adding 0.25 to a sample mean increases expected squared
error for a zero-mean Rademacher distribution. The answer has a known analytical
derivation, so the study can check its runner/evaluator independently of an LLM.
This is a research-workflow demonstration with a short manuscript, not novel
science or a model benchmark.

```sh
python3 -m allagma toy --destination work/toy-run
```

## Prepare an adapted study before running it

The one-command walkthrough above runs the preset immediately. To inspect a
prospective change first, prepare a **new** study with a different additive bias:

```sh
python3 examples/toy-study/prepare.py --destination work/half-bias --id half-bias --bias 0.5
python3 -m allagma verify --study work/half-bias
```

Preparation uses only Python's standard library, makes no model calls, and
executes no experiments. Read `brief.json`, `protocol.json` and `adaptation.json`
in the new directory before continuing. The adaptation receipt retains source
digests and MIT lineage; `SOURCE-LICENSE.txt` carries the license. It copies
study-owned programs, never a previous study's attempts, results or bundles.

This bounded example accepts a finite bias between −1 and 1 and preserves the
two pilot seeds, 24 confirmation seeds, 64 observations per seed and original
60-second/28-attempt ceiling. Its expected MSE difference is b²; at b = 0.5 it
is 0.25, not a promise that the realized estimate or every seed equals that
value. The derivation's b = 0.25 calculation remains a labeled worked example.
The analyzer takes the actual common bias from the raw measurements, rejects
mixed bias/sample-count comparisons, and passes that value to the writer.
The question, protocol and report retain the accepted bias's full numeric
precision; rounding displayed result estimates does not change the setting
stated in the claim scope.

After reviewing the plan, run each lifecycle step explicitly:

```sh
python3 -m allagma campaign start --study work/half-bias --campaign half-bias-v1
python3 -m allagma campaign run --study work/half-bias --campaign half-bias-v1
python3 -m allagma campaign analyze --study work/half-bias --campaign half-bias-v1 --analysis-id a001
python3 -m allagma campaign audit --study work/half-bias --campaign half-bias-v1
```

Open `campaigns/half-bias-v1/analyses/a001/paper/manuscript.md` and its adjacent
`claims.json`. The scope must say **additive bias 0.5**. The ordinary adapted
run has 26 successful attempts; the tutorial does not inject failures. Any real
failure still retains its attempt and consumes the finite budget. The audit
reruns analysis and writing and appends a review; it is not independent science
review. A passing audit alone could not detect the older writer's hard-coded
0.25 wording, because it reproduced that same error.

Existing destinations, including empty directories and symlinks, are refused.
Invalid arguments are rejected before creation. If an unexpected filesystem or
setup failure occurs after creation, inspect the retained partial directory
and choose a new destination; preparation does not erase it. After campaign
start, the frozen materials are authoritative. Change a plan with an explicit
[amendment](../../docs/guides/reproduce.md#change-the-plan-deliberately), never by
editing campaign files. Existing studies keep their copied scientific programs;
this repair does not rewrite historical reports or qualify old bundles again.

## Default walkthrough and evidence

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
