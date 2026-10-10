# Roadmap

Allagma 0.3.0rc2 has a working offline study, a qualified native Codex path on
the recorded macOS environment, and three local study packages. The roadmap
describes priorities, not promised delivery dates or existing community demand.

## Immediate work on public main

Main now includes [#20](https://github.com/alohays/allagma/pull/20); the required
adapter-regression checks and issue #18 are complete. The
[follow-up triage](docs/contributing/post-pr20-triage.md) adds exactly two
reproduced boundary issues, #22 and #23, while retaining the existing work:

1. [#19: make the toy-to-paper workflow runnable](https://github.com/alohays/allagma/issues/19).
   Teach contributors to turn actual toy results into a new, evidence-bound paper revision.
2. [#22: align paper-source size admission and extraction](https://github.com/alohays/allagma/issues/22).
   Include generated metadata in the limit and refuse oversized copies early.
3. [#23: diagnose self-contained exported studies](https://github.com/alohays/allagma/issues/23).
   Avoid a false missing-example failure from the bundled helper.

Existing work remains relevant: [#6](https://github.com/alohays/allagma/issues/6)
is assigned to `codedbypraneetha`, and [#7](https://github.com/alohays/allagma/issues/7)
still needs a literal Linux/Python 3.13 onboarding receipt. Historical-audio
rights stay with the maintainer in [#8](https://github.com/alohays/allagma/issues/8).
New provider integrations, larger studies and distribution services are later
directions, rather than additional issues in this small immediate queue.

## Longer-term directions

| Priority | Next useful outcome | Evidence needed before claiming it |
| --- | --- | --- |
| First use | Maintain the public tutorial, compact source distribution and browsable studies | Fresh onboarding evidence when behavior changes, working documentation/media and publication review |
| Host coverage | Qualify additional host versions and Claude Code with real sessions | Native activation, locked routing, execution and recovery receipts |
| Reproduction portability | Qualify a real study on another OS/hardware combination | Fresh environment, complete execution and independently recomputed outputs |
| Evaluation | Learn whether evidence-management benefits generalize | More tasks, independent runs/review, prospectively fixed scoring and uncertainty |
| Artifact distribution | Move optional large packages to durable hash-addressed storage when needed | Integrity-checked restore, retention policy, license/privacy review and sustainable costs |
| Study ergonomics | Reduce repeated setup and improve diagnostics where actual users struggle | Reproducible friction reports and scoped before/after checks |

The default remains a small, offline, standard-library Python core. Scientific
logic stays study-owned. No autonomous model optimization, broad agent-quality
claim or remote scheduler is implied by this roadmap.

Start with a [small contribution](docs/contributing/starter-tasks.md), or propose
a bounded change using the module proposal form. Changes to public contracts,
ownership or defaults follow [governance](GOVERNANCE.md).

## First contributor milestone

The [milestone](https://github.com/alohays/allagma/milestone/1) and
[pinned overview](https://github.com/alohays/allagma/issues/9) connect the actual
backlog. This is maintainer-proposed work; the initial implementations are
agent-assisted. The documentation site is [public](https://alohays.github.io/allagma/),
and the [welcome Discussion](https://github.com/alohays/allagma/discussions/13)
provides the community entry point.

| State and kind | Task | Review or contribution path |
| --- | --- | --- |
| Merged · confirmed defect | [#3: adapted toy reports hard-code bias](https://github.com/alohays/allagma/issues/3) | [#10](https://github.com/alohays/allagma/pull/10); available on main |
| Merged · enhancement | [#2: read-only prerequisite diagnostics](https://github.com/alohays/allagma/issues/2) | [#11](https://github.com/alohays/allagma/pull/11); available on main |
| Merged · enhancement | [#4: read-only evidence inspection](https://github.com/alohays/allagma/issues/4) | [#12](https://github.com/alohays/allagma/pull/12); available on main |
| Merged · documentation enhancement | [#5: validator recovery](https://github.com/alohays/allagma/issues/5) | [#15](https://github.com/alohays/allagma/pull/15); verified recovery recipe available on main |
| In progress · accessibility | [#6: accessible figure description](https://github.com/alohays/allagma/issues/6) | Claim confirmed and assigned to `codedbypraneetha`; coordinate before overlapping work |
| Available · qualification | [#7: Linux/Python 3.13 tutorial](https://github.com/alohays/allagma/issues/7) | Unassigned; help wanted, local CPU only |
| Merged · confirmed CI gap | [#18: adapter regression selection](https://github.com/alohays/allagma/issues/18) | [#20](https://github.com/alohays/allagma/pull/20); actual failure propagation and real-Git boundaries verified |
| Available · documentation enhancement | [#19: runnable toy-to-paper walkthrough](https://github.com/alohays/allagma/issues/19) | Unassigned; Python/research documentation; TeX only for optional compilation |
| Available · source-budget defect | [#22: paper-source size admission](https://github.com/alohays/allagma/issues/22) | Unassigned; offline packaging fixtures and the existing optional TeX check |
| Available · diagnostic defect | [#23: standalone bundle diagnostics](https://github.com/alohays/allagma/issues/23) | Unassigned; read-only CLI and exported-study coverage |
| Blocked · maintainer decision | [#8: retained historical-audio rights](https://github.com/alohays/allagma/issues/8) | Outside the engineering milestone; public activation does not resolve rights |

The three feature PRs were merged sequentially after final review and passing
CI after each merge. [Dependabot #1](https://github.com/alohays/allagma/pull/1)
was reviewed and merged separately. The [review record](docs/contributing/pr-review.md)
and [merge record](docs/contributing/merged-prs.md) link findings, fixes and
validation. Follow the [triage and review process](docs/contributing/workflow.md)
for transitions from available to in progress, blocked or owner review.

The subsequent [final audit](docs/contributing/final-open-pr-merges.md) records
the sequential merges of [#16](https://github.com/alohays/allagma/pull/16)
(repository rules), [#15](https://github.com/alohays/allagma/pull/15)
(duplicate-key recovery), and [#14](https://github.com/alohays/allagma/pull/14)
(critical reference research and optional portable papers). These capabilities
are available on main; native-host coverage and scientific scope retain their
documented limits.
