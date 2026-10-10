# Contributor tasks

These are actual **maintainer-proposed** tasks in the
[first contributor milestone](https://github.com/alohays/allagma/milestone/1).
They do not imply external demand or prior contributors. The
[pinned overview](https://github.com/alohays/allagma/issues/9) is the current work
queue; read the [claim and review process](workflow.md) before starting.

| Task and current state | Starting files | Finish line and prerequisites |
| --- | --- | --- |
| [#6: Describe the EMA figure accessibly](https://github.com/alohays/allagma/issues/6) — claim requested; maintainer confirmation pending | `studies/ema-schedule/RESULTS.md` and its figure | Describe axes, panels, paired seeds and uncertainty without changing numerical claims. Read the existing claim before starting overlapping work. No archive restoration or training; optional Node toolchain for site rendering. |
| [#7: Qualify Linux/Python 3.13 onboarding](https://github.com/alohays/allagma/issues/7) — available and unassigned; help wanted | `docs/guides/first-study.md`, `conformance/` | Record a literal clean-checkout offline tutorial with a distinct interpreter and paths with spaces. Requires local Linux/Python 3.13, not a native model or GPU. |

Comment on the issue with your scope and environment. A maintainer confirms the
claim and assignment before overlapping implementation. No paid model access,
GPU, response-time guarantee or release deadline is involved. Submit concise
sanitized evidence with its exact tested commit. A documentation change needs a
rendered review and link check, not a test that merely repeats its prose.

## Merged contributor improvements

The initial agent-assisted improvements are merged and available on main:
[#10: adapted toy/report repair](https://github.com/alohays/allagma/pull/10),
[#11: prerequisite diagnostics](https://github.com/alohays/allagma/pull/11), and
[#12: read-only evidence inspection](https://github.com/alohays/allagma/pull/12).
Use the current command guide and first-study tutorial for these features.
The [review record](pr-review.md) documents findings and fixes; the
[merge record](merged-prs.md) records successful CI between the sequential merges.

[#5: duplicate-key recovery](https://github.com/alohays/allagma/issues/5) is also
complete through [#15](https://github.com/alohays/allagma/pull/15). Its verified
[recovery recipe](../guides/troubleshooting.md#duplicate-json-keys) is available
on main. The [final audit](final-open-pr-merges.md) records this merge alongside
the reference-research/paper feature and repository-protection documentation.

The [historical-audio rights issue](https://github.com/alohays/allagma/issues/8)
is maintainer-owned and is not a newcomer task. See the complete
[contribution guide](../../CONTRIBUTING.md) for targeted checks.
