# Roadmap

Allagma 0.3.0rc2 has a working offline study, a qualified native Codex path on
the recorded macOS environment, and three local study packages. The roadmap
describes priorities, not promised delivery dates or existing community demand.

| Priority | Next useful outcome | Evidence needed before claiming it |
| --- | --- | --- |
| Launch | Make first use and contribution understandable, with a compact source download and browsable studies | Clean onboarding, working documentation/media and publication review |
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
| Available · documentation enhancement | [#5: validator recovery](https://github.com/alohays/allagma/issues/5), [#6: accessible figure description](https://github.com/alohays/allagma/issues/6) | Unassigned; good first issue and help wanted |
| Available · qualification | [#7: Linux/Python 3.13 tutorial](https://github.com/alohays/allagma/issues/7) | Unassigned; help wanted, local CPU only |
| Blocked · maintainer decision | [#8: retained historical-audio rights](https://github.com/alohays/allagma/issues/8) | Outside the engineering milestone; public activation does not resolve rights |

The three feature PRs were merged sequentially after final review and passing
CI after each merge. [Dependabot #1](https://github.com/alohays/allagma/pull/1)
was reviewed and merged separately. The [review record](docs/contributing/pr-review.md)
and [merge record](docs/contributing/merged-prs.md) link findings, fixes and
validation. Follow the [triage and review process](docs/contributing/workflow.md)
for transitions from available to in progress, blocked or owner review.
