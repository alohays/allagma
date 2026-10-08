# Allagma implementation goals

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

## Allagma v0.3 reusable workflow and evaluation — 8 October 2026

Deliver Allagma v0.3 as a reusable research workflow that lets a fresh Codex
session turn a research brief, source materials, and resource profile into an
executed, critically reviewed, reproducible research package.

Build on the current specifications and completed EMA study. Validate three
tasks: an EMA follow-up separating training-duration and learning-rate-schedule
effects; modular-addition grokking investigating regularization and
generalization; and an external computational-reproduction task. Prefer a
locally compatible CORE-Bench task. If none passes preflight, select a comparable
open reproduction task and clearly label it a custom evaluation. Preserve the
source task's scientific requirements and scoring criteria.

Run scientific workloads entirely on this M4 Pro Mac: 14 CPU cores, 20 GPU cores,
and 48 GB unified memory. Use CPU or PyTorch/MPS and isolated study environments.
Use existing Codex authentication for agent sessions. Select workloads that fit
local hardware without requiring CUDA, remote compute, or paid experiment
services. Use bounded pilots to choose conservative, finite compute, timeout,
attempt, memory, and storage limits. Track Codex usage separately and respect
existing account limits.

Extract reusable support from demonstrated needs. Evaluated agents should
perform planning, implementation, recovery, critique, and reporting from the
initial brief without task-specific coordinator handholding. Record all
subsequent assistance. Keep research logic study-owned and the default
conformance kit offline and standard-library-only.

Compare plain Codex with Codex plus Allagma across three tasks, two conditions,
and two isolated fresh sessions per condition: 12 evaluation runs. Match the
underlying model, settings, tools, inputs, and resource ceilings. Freeze the
workflow and evaluation criteria after development, separate pilot material
from final evaluation, and protect scorers and reference answers from candidate
changes. Measure correctness, evidence completeness, completion, interventions,
and resource use; report failures, regressions, and uncertainty honestly.

Continue through implementation, execution, and fixes until all three task
packages, the comparison report, and a release candidate are complete. Include
clean-checkout reproduction of at least one full study from environment setup
through training or execution, plus recomputation of its reported results.
Resolve reproduced critical defects, preserve historical evidence and bundles,
and document the exact validated scope in English with applicable migration
notes. Follow the existing commit-and-push instructions and preserve the GUI
model selection.

Make routine decisions autonomously. Use the user-input tool for consequential
unresolved choices or resource expansion. Negative scientific results and an
inconclusive baseline comparison are valid outcomes; unfinished or unverified
work is not completion. The [v0.3 requirement ledger](docs/v0.3/requirements.md)
tracks evidence against this full scope.

## Public open-source launch preparation — 8 October 2026

Make the completed Allagma v0.3 release ready for a world-class public open-source launch. A new researcher should understand its value at a glance, see a real study in action, reach a useful first result, and know how to contribute. Ground every claim in the final implementation and evaluation evidence. Write all public material in English.

Create an exceptional README with precise positioning, a compelling opening visual, concrete use cases, representative outputs, and a verified quickstart. Explain the value Allagma adds to a coding agent in plain language. Keep architecture details progressively discoverable. Clearly distinguish the offline example, native agent workflow, supported hosts, experimental features, and measured limitations. Take editorial and demonstration quality cues from uv and marimo while developing an original Allagma identity.

Deliver a cohesive visual system across the README and docs: a workflow illustration, real result and artifact previews, and a polished 60-120 second flagship video showing a research brief becoming an executed study, figures, an evidence-linked report, and reproducible outputs. Capture actual working software; label edits, accelerated time, and reused results accurately. Provide captions, a transcript, a GitHub-compatible preview linking to the full video, editable asset sources, and repeatable capture instructions. Make the key idea legible on mobile and in light and dark themes.

Build a polished documentation site with Astro Starlight, keeping its toolchain separate from the Python runtime. Provide a distinctive landing page, search, a complete first-study tutorial, practical guides, CLI and concept references, a browsable real-study showcase, evidence and support boundaries, troubleshooting, and contributor documentation. Reuse canonical content without maintaining contradictory copies. Configure the actual GitHub Pages project path, automated builds and link checks, and a deployment workflow ready for later public launch.

Complete the repository's public presentation and contribution experience: description, topics, social preview, citation metadata, roadmap, release notes, support and security reporting, contribution guidance, issue/PR forms, and a lightweight Discussions and starter-contribution plan. Improve existing files instead of duplicating them. Add useful, low-maintenance CI for docs, relevant examples, links, dependencies, and releases; ensure fork contributions work without privileged secrets. Prepare launch copy and concrete beginner-friendly tasks without inventing community activity or adoption.

Review tracked content and Git history for private data, secrets, and redistribution restrictions. Keep downloads and media practical, preserve frozen evidence and attempts, and document a maintainable artifact distribution strategy. Preserve the offline standard-library core, study-owned science, and my GUI model selection. Keep builds and scientific demos feasible on this M4 Pro Mac with 48GB RAM; use existing Codex authentication and bounded workloads.

Continue through implementation, rendering, actual demo capture, clean-checkout onboarding, browser inspection, and repairs until the complete launch package works. Verify desktop/mobile presentation, keyboard access, search, media playback, links, commands, and the production build under its Pages base path. Fix first-use friction within scope. Finish with runnable local previews, final assets, validation evidence, and exact remaining owner actions for publication. A storyboard, scaffold, or deployment configuration alone is not completion.

Make routine editorial, design, and engineering decisions autonomously; use the user-input tool for consequential unresolved choices. Follow existing commit-and-push instructions. Prepare publication fully while retaining private repository visibility; activating public Pages, publishing releases, and posting announcements belong to the later launch.

The [launch acceptance ledger](docs/launch/requirements.md) tracks the complete
scope. Commit coherent increments as work proceeds; push to `origin` after the
launch package is complete. Keep repository visibility private. Public Pages
activation, release publication, and announcements remain later owner actions.

Owner decisions for public-launch preparation on 8 October 2026: preserve the
full Git history, with author email, local home-directory paths and native
session IDs documented for launch review. Keep the additional native onboarding
probe at its existing 15-minute plus 5-minute model-session limits; do not run
another native continuation. Record the incomplete final handoff as a measured
limitation, separately from its verified science and the completed frozen
release qualification.

## Final audit before open-source publication — 8 October 2026

Audit the current worktree, complete reachable Git history and current GitHub
state before public release. Recheck the I1–I5 acceptance criteria and complete
toy workflow, clean-source onboarding, production documentation and media,
dependency advisories, redistribution notices, retained evidence, privacy
decisions and publication controls. Investigate confirmed defects, repair them
without changing frozen scientific records, and record fresh evidence and any
remaining owner actions in English. Commit coherent increments and push the
completed audit to `origin`.

This audit does not activate public visibility, Pages, releases or announcements.
The existing decisions to retain historical metadata and cap the additional
native onboarding probe remain in force. Do not run another native model
continuation or add project model overrides.

Final-audit owner decisions on 8 October 2026: replace the demo narration with
a voice that permits redistribution. The current movie now uses Kokoro's
Apache-2.0 model and MIT-licensed ONNX engine. **Keep all historical commits
unchanged and finish the audit with clearance of the older Apple-voice videos
listed as a public-launch blocker.** Do not rewrite history or change repository
visibility to resolve that blocker without a later owner instruction.

## Prior implementation acceptance

See [implementation status](docs/implementation-status.md) for the acceptance
map. The final evidence must include portable delivery, independent module and
adapter replacement, an offline contributor path, version/update/migration and
rollback scenarios, and actual toy raw data, analysis, claims and manuscript.
Do not mark the goal complete until implementation, passing evidence, technical
documentation, commits and the authorized push are complete.
