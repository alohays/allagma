# Start a study with a coding agent

The offline example supplies finished scientific programs. In a native study,
you supply a question, source materials and finite resource limits; the agent
develops the protocol, scientific code, analysis and report. Allagma supplies
portable methods, exact campaign locks, retained attempts and evidence contracts.
The researcher remains responsible for the question and scientific judgment.

## Prepare without starting a model session

The small [example inputs](../../examples/first-research/README.md) ask a native
agent to study the bias–variance trade-off for an estimator using only Python's
standard library. From the source checkout:

```sh
python3 -m allagma research prepare \
  --study work/agent-study --control work/agent-control --id estimator-study \
  --brief examples/first-research/BRIEF.md \
  --materials examples/first-research/materials \
  --profile examples/first-research/resources.json
python3 -m allagma research status --study work/agent-study --control work/agent-control
```

Read `work/agent-study/RESEARCH.md`, `inputs/BRIEF.md`, `inputs/RESOURCES.json`
and `ALLAGMA.md`. Preparation copies materials and pins methods. It does not
launch a model, train anything, or promise an answer. Study and controller
directories must be separate and new. Keep secrets out of supplied materials.

New studies also include `references/INDEX.md` and `references/map.json`. Build
the critical literature map during scoping and consult its notes throughout the
study. See [reference research](../reference-research.md) for offline/provided-only
coverage, bounded acquisition and immutable prepared assets. An
[optional paper request](../arxiv-papers.md) adds a PDF and portable source package
with the researcher's own author metadata.

## Launch explicitly on macOS

The supervised native runner currently targets **macOS and a compatible Codex
CLI**. It uses existing authentication and temporary runtime configuration;
it does not pin a project model. See the exact
[qualified host and version](../host-support.md). Compatibility of every future
CLI or model is not established by the recorded experiment.

Find your installed compatible executable and confirm its version. Then run,
replacing the executable path with your real absolute path:

```sh
python3 -m allagma research run \
  --study work/agent-study --control work/agent-control \
  --session session-001 --codex /absolute/path/to/codex --timeout 900
```

This is an authenticated model session and consumes your account's usage.
The 900-second session limit is separate from the example's 120-second science
budget, 30-second setup budget and 1 GiB study storage ceiling. The broker
disables network access for computation. Include any required dependencies in
materials before preparing a different study; the example needs none.

**Budget is a stopping rule, not a completion promise.** In the launch-onboarding
probe with the inherited model/settings, a 900-second session completed the
science, a full replay and deterministic audits, but timed out before its final
package index. A separate 300-second continuation also ended at its limit.
The [recorded observation](../launch/evidence/native-onboarding-initial.json) and
[controller arithmetic check](../launch/evidence/native-arithmetic.json) preserve
both facts. This extra probe is separate from the twelve-session release
evaluation and is not advertised as a completed native handoff.
The owner [chose to keep the current model-usage limit](../launch/evidence/native-budget-decision.json)
and retain that incomplete handoff as a measured limitation.

For a verified complete first result, use the [offline tutorial](first-study.md).
For a native session, choose a finite model-work budget appropriate to your
question and account; scientific execution may take seconds while planning,
review and packaging take much longer. The published
[native study packages](../showcase/index.md) retain their actual usage and limits.

## Ask for an inspectable result

Write the research brief in terms of a scientific question, comparisons,
independent units, available inputs, feasibility limits and required outputs.
Permit negative or inconclusive findings. Ask for failed attempts to remain and
for claims to link to actual measurements. Avoid dictating a favorable answer.

A useful handoff includes a protocol, exact source and environment, attempt
records, raw results, figures, an evidence-linked report, revision-bound critique,
full execution instructions and retained-data recomputation instructions.
Reviewing a report without naming its exact revision leaves a provenance gap.

## Inspect and recover

```sh
python3 -m allagma research status --study work/agent-study --control work/agent-control
```

A normally exited native session is not a scientific pass. Inspect the output,
resource ledger and critique. On interruption, check existing live processes and
receipts before launching a new session ID. Never replace an attempt or assume
that a missing client response means a job did not run.

For alternative hosts, use the canonical method text through their adapter.
Claude Code packaging is contract-tested; native qualification is not claimed.
For the full interfaces and limits, see [research workspaces](../research-workspaces.md),
[resource supervision](../resource-supervision.md) and [host support](../host-support.md).
