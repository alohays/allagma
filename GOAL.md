# Allagma v0.2 implementation goal

Fully implement Allagma v0.2 in this repository following the adopted
[framework design](docs/specification/framework-design.md) and its relevant
linked specifications. Continue implementing, running and fixing until every
I1–I5 acceptance criterion has concrete passing evidence, including the complete
toy-study workflow. Maintain English technical documentation. Make routine
engineering decisions autonomously; use the user-input tool for unresolved
choices that materially affect scope, cost or correctness.

## Additional user instruction — 6 October 2026

Commit the work in appropriate, coherent Git increments as progress is made.
Once all tasks and acceptance checks are complete, push the completed work to
the Git remote named `origin`.

## Follow-up goal — 7 October 2026

Perform a thorough self-audit of the delivered implementation against the
original specifications. Independently inspect requirement coverage, reproduce
defects beyond the original tests, correct confirmed problems, retain the
before/after evidence, and qualify the resulting source again. The commit-and-
push instruction above also applies to this follow-up.

## Tracking and completion

## Native Codex diffusion study — 8 October 2026

Qualify Allagma for real native Codex use by completing **When Does Weight EMA
Help Tiny 2D Diffusion?** Keep science and dependencies in a separate study,
using SakanaAI/AI-Scientist's `templates/2d_diffusion` at commit
`1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb` as the reference. Target this Mac's
M4 Pro and 48 GB memory with an isolated Python/PyTorch environment and MPS.
Start with approximately 300,000 parameters, batch size 256 and 100 diffusion
steps. On two moons and an eight-component Gaussian mixture, compare raw
weights with EMA decays 0.99 and 0.999 from the same training trajectories at
5,000 and 10,000 updates. Complete two pilot seeds per dataset, then freeze the
confirmation protocol for five new seeds per dataset. Evaluate held-out Sliced
Wasserstein distance and mixture mode coverage with paired comparisons and
seed-level uncertainty.

Enforce a 30-minute total study-computation ceiling including retries, with
explicit attempt and timeout limits. The prior 15.3-second probe is only a
feasibility estimate. Ask before expanding the budget or changing the research
question. Retain real native skill activation, campaign-lock routing and fresh
session continuation after interruption. Finish with recomputable results,
figures, an evidence-linked English manuscript and an accurately scoped host
qualification report. Negative or inconclusive findings are valid. Fix
demonstrated framework defects and run affected checks. Commit coherent
increments and push to `origin` at completion. Preserve the GUI model choice.
Use the user-input tool for consequential unresolved choices.

## Implementation acceptance

See [implementation status](docs/implementation-status.md) for the acceptance
map. The final evidence must include portable delivery, independent module and
adapter replacement, an offline contributor path, version/update/migration and
rollback scenarios, and actual toy raw data, analysis, claims and manuscript.
Do not mark the goal complete until implementation, passing evidence, technical
documentation, commits and the authorized push are complete.
