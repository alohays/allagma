# Your first study

Run a complete, inspectable research workflow on your own computer. In this
example you will compare two estimators, keep a failed and interrupted attempt,
inspect the resulting claims, and recompute the report from its evidence.
There is no model session, API bill, GPU, or Python package installation.

## Get the small source checkout

You need **Python 3.11 or newer**, Git, and macOS or Linux. Run `python3 --version`
first. This sparse checkout leaves the large historical research archives out
of your initial download:

```sh
git clone --depth 1 --filter=blob:none --sparse https://github.com/alohays/allagma.git
cd allagma
git sparse-checkout set allagma adapters contracts methods recipes policies profiles \
  templates tools conformance examples/toy-study examples/first-research evals/context-retention
python3 -m allagma check
```

The catalog command returns JSON with `"status": "pass"`. The public checkout
requires no GitHub authentication. If you already have a checkout, start with
that last command. The Python runtime is independent
of the documentation site's Node toolchain. A wheel or `pip install allagma`
is not the supported distribution in this release candidate.

## Run the experiment

```sh
python3 -m allagma toy --destination work/my-first-study
```

Use a new destination for each run. An existing study is never erased. The
command prints a JSON handoff when complete; it may be quiet while running.
The example has a 60-second recorded execution budget and 28-attempt ceiling;
those are bounds, not a runtime promise.

The question is deliberately small: **does adding 0.25 to a sample mean
increase its squared error?** Each observation is equally likely to be −1 or
+1. Two known-answer pilot seeds check the runner. Then 24 new seeds each
generate 64 observations for the paired comparison.

One attempt really fails and another is interrupted after a checkpoint. Both
are retained, and their retries receive new IDs. These are deliberate recovery
demonstrations. They do not count as extra independent observations. See the
[full toy specification](../../examples/toy-study/README.md).

## Read the result

Open this file in your editor or Markdown viewer:

```text
work/my-first-study/campaigns/toy-v1/analyses/a001/paper/manuscript.md
```

The representative result is:

| Quantity | Value |
| --- | ---: |
| Sample-mean MSE | 0.01529948 |
| Mean-plus-0.25 MSE | 0.08040365 |
| Paired increase in MSE | 0.06510417 |
| Approximate 95% interval | [0.03985104, 0.09035729] |
| Independent confirmation seeds | 24 |

These are generated results, not values typed into a report template. The
interval is the seed-level mean ±1.96 standard errors, a normal approximation.
The mathematical expected increase is 0.25² = 0.0625; the realized estimate
need not equal that expectation.

The adjacent `claims.json` marks the average comparison **supported**. It marks
“greater error on every seed” **contradicted**: seeds 104, 108, 118 and 121 are
counterexamples. A third claim records leave-one-seed-out sensitivity. An
average effect does not justify a claim about every observation.

## Follow a claim back to evidence

Within `campaigns/toy-v1/`, inspect these files in order:

| File or directory | What it lets you check |
| --- | --- |
| `analyses/a001/paper/claims.json` | Claim status, scope, limitations and references |
| `analyses/a001/outputs/summary.json` | Numerical values used in the report |
| `analyses/a001/raw-manifest.json` | Exactly which attempts were included or excluded |
| `runs/` | Individual attempts, raw measurements and failure records |
| `materials/` and `lock.yaml` | Frozen study programs and the exact Allagma bundle |

The figure is `analyses/a001/outputs/paired-differences.svg`. It shows individual
seed differences rather than only the favorable average. Files are ordinary
Markdown, JSON and SVG; no hosted dashboard is required to read them.

## Verify the package

```sh
python3 -m allagma campaign audit --study work/my-first-study --campaign toy-v1
```

Look for `"verdict": "pass"`, an empty findings list, and **521 checked
references** for the default full example. The audit checks content digests,
reruns the analysis and regenerates the manuscript. It appends a new review;
the original remains. This is deterministic verification, not independent
scientific peer review or evidence of a language model's research quality.

The campaign ID is `toy-v1`; its protocol revision is `toy-v2`. These identify
different things and are intentionally distinct. The state separates phase
(`audit`), execution (`completed`) and assurance (`deterministic`).

## Continue from here

Turn these retained results into an additional paper with the
[runnable toy-to-paper walkthrough](toy-to-paper.md). It covers explicit
attribution, provided-only references, scoped reviews and stale-review recovery.
The base walkthrough stays offline; TeX compilation is a separate optional step.

To change the offline question without a model session, follow
[prepare an adapted toy study](../../examples/toy-study/README.md#prepare-an-adapted-study-before-running-it).
It stops before execution so you can inspect the changed bias, source lineage
and finite plan, then start, run, analyze and audit the new campaign explicitly.

Use [your own question](native-study.md) with a native agent, learn to
[resume and reproduce](reproduce.md), or browse the
[real study showcase](../showcase/index.md). If a command fails, use
[troubleshooting](troubleshooting.md) before changing a lock or deleting evidence.
