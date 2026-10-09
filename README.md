# Allagma

**A research workflow for coding agents.** Give the agent a question, source
materials and resource limits. It develops the protocol, writes and runs the
experiments, analyzes the results, and prepares a report for you to review.

Allagma is for researchers working with code. You receive the figures and
findings, along with the code, data and attempt history needed to check them.

[Read a completed study](https://alohays.github.io/allagma/studies/ema-schedule/) ·
[Try the offline example](#run-your-first-study) ·
[Documentation](https://alohays.github.io/allagma/)

https://github.com/user-attachments/assets/df7c556b-9251-4514-9fb2-ecacc2de9162

The 100-second demo runs the supplied **offline example**, producing a figure,
report and reproducible results. At 1:23 it shows **retained native-agent EMA
results**. The recording uses a local demonstration workbench; it does not show
a live model session or accelerate computation.

[Watch with captions](https://alohays.github.io/allagma/demo/) ·
[Transcript](media/demo/transcript.md) · [Download MP4](media/demo/allagma-workflow.mp4) ·
[Media sources and licenses](media/CAPTURE.md)

<picture>
  <source media="(prefers-color-scheme: dark) and (max-width: 600px)" srcset="media/workflow-dark-mobile.svg">
  <source media="(max-width: 600px)" srcset="media/workflow-light-mobile.svg">
  <source media="(prefers-color-scheme: dark)" srcset="media/workflow-dark.svg">
  <img src="media/workflow-light.svg" alt="You supply the question, sources and resource limits. The agent develops a protocol and code, runs experiments and analysis. You review figures, a report, critique and reproducible code." width="1000">
</picture>

Allagma gives the agent reusable methods for planning, execution, analysis and
critique. It keeps the agreed protocol, failed attempts and the data behind
each claim with the report, so you can see which runs informed a finding and
recompute the numbers. You choose the question and judge the science.

## What a completed study looks like

A native Codex session used Allagma to investigate **when averaging model
weights helps tiny diffusion models**. It returned scientific code, saved
weights, paired estimates, this figure, a report and a critique.

[![Retained EMA study figure: paired effects across learning-rate policy and training duration](media/evidence/ema-r07.png)](https://alohays.github.io/allagma/studies/ema-schedule/)

The observed relative benefit of EMA was larger under constant learning rate
than at completed cosine endpoints. With four seeds per dataset, duration and
interaction estimates remain inconclusive. A smaller relative benefit does
not imply worse absolute EMA quality. The figure shows retained r07 results;
no new training was run for this preview.

[Read the result and its limits](https://alohays.github.io/allagma/studies/ema-schedule/) ·
[Open the full-size figure](media/evidence/ema-r07.png) ·
[Agent's full report (Markdown)](https://alohays.github.io/allagma/generated/media/evidence/ema-r07-report.md) ·
[Source attribution and study license](studies/ema-schedule/REFERENCE.md)

Other completed native studies include a [CORE CULP reproduction](https://alohays.github.io/allagma/studies/core-culp/)
with all six requested answers and a disclosed predictor-label defect, and a
[modular-addition experiment](https://alohays.github.io/allagma/studies/modular-addition/)
where weight decay improved endpoint accuracy without an observed grokking
transition. [Browse their outputs and reproduction scope](https://alohays.github.io/allagma/studies/).

## Run your first study

The offline toy supplies finished scientific programs. It is the easiest way
to try the workflow: Python 3.11+ on macOS or Linux, with no model account, paid
API, GPU or Python package installation. This small checkout leaves the large
historical study archives out of the first download:

```sh
git clone --depth 1 --filter=blob:none --sparse https://github.com/alohays/allagma.git
cd allagma
git sparse-checkout set allagma adapters contracts methods recipes policies profiles \
  templates tools conformance examples/toy-study examples/first-research evals/context-retention
python3 -m allagma check
python3 -m allagma toy --destination work/my-first-study
```

Use a new destination for each study. If you already have a checkout, start
with `python3 -m allagma check`.

The example asks whether adding 0.25 to a sample mean increases squared error.
It runs two known-answer pilots and 24 confirmation seeds, retains a deliberate
failure and interruption, and generates a figure, manuscript and claim ledger.
The average error increases, but four seeds contradict the claim that it
increases on every seed. This is a known-answer workflow demonstration.

[Preview the actual outputs](https://alohays.github.io/allagma/explore/), or open
`work/my-first-study/campaigns/toy-v1/analyses/a001/paper/manuscript.md` in your
editor. Then recompute and check the evidence:

```sh
python3 -m allagma campaign audit --study work/my-first-study --campaign toy-v1
```

The [full tutorial](https://alohays.github.io/allagma/guides/first-study/) explains
the outputs, uncertainty estimates, retained attempts and audit coverage.

## Work on your own research question

<a id="use-it-for-research-you-want-to-check-later"></a>

[Prepare a native study](https://alohays.github.io/allagma/guides/native-study/)
from a brief, materials and finite resource profile. The agent develops the
scientific code and report through Allagma's methods. Preparation is offline;
explicit native execution consumes your account's model usage.

New studies include a [critical reference map](docs/reference-research.md) for
prior papers, implementations, competing findings and study decisions. Selected
source assets use a bounded local cache. An optional [arXiv paper output](docs/arxiv-papers.md)
adds a compiled PDF and portable sources with researcher-configured attribution.
See the [EMA paper and reference demonstration](studies/ema-schedule/publications/reference-r2/README.md)
for a revision of completed research with unchanged scientific evidence.

<a id="what-has-actually-been-tested"></a>

**0.3.0rc2 is a source release candidate.** The supervised native runner is
qualified on the recorded macOS/Codex setup. Claude Code packaging is tested,
but native qualification is not claimed. A session budget is a stopping limit,
not a promise of completion: an additional onboarding probe completed its
science and replay but ran out of session time before the final package index.

The [host report](docs/host-support.md), [twelve-session comparison](docs/v0.3/COMPARISON.md)
and [release notes](docs/releases/0.3.0rc2.md) describe the measured scope.
The small comparison does not establish general research superiority or
consistent cost savings. Deterministic checks and model critique do not replace
independent scientific review.

## Understand and extend it

The [concept guide](https://alohays.github.io/allagma/reference/concepts/) explains
the research record. Methods are portable Agent Skills, recipes compose them,
and adapters connect them to a host. A campaign pins its exact bundle, so later
central changes cannot silently rewrite an existing study. See
[architecture](docs/architecture.md), [contracts](docs/contracts.md),
[study-owned programs](docs/study-adapters.md), [versioning](docs/versioning.md)
and [acceptance evidence](docs/acceptance.md) for engineering details.

For a contribution, start with the [pinned overview](https://github.com/alohays/allagma/issues/9),
[available tasks](docs/contributing/starter-tasks.md) or
[welcome Discussion](https://github.com/alohays/allagma/discussions/13).
The three contributor feature PRs remain drafts; their commands and adaptation
helper are not yet available on main. [Contributing](CONTRIBUTING.md),
[roadmap](ROADMAP.md), [support](SUPPORT.md) and
[private security reporting](https://github.com/alohays/allagma/security/advisories/new)
provide the next steps.

Allagma core is MIT licensed. Scientific adaptations and archived dependencies
retain their own terms, including the AI Scientist license on EMA-derived
materials. See [third-party notices](THIRD_PARTY_NOTICES.md). Cite the exact
software version using [CITATION.cff](CITATION.cff), and identify a study's
bundle separately.
