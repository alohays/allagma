# Contributor tasks

These are actual **maintainer-proposed** tasks in the
[first contributor milestone](https://github.com/alohays/allagma/milestone/1).
They do not imply external demand or prior contributors. The
[pinned overview](https://github.com/alohays/allagma/issues/9) is the current work
queue; read the [claim and review process](workflow.md) before starting.

## Available work

1. [#7: Qualify Linux/Python 3.13 onboarding](https://github.com/alohays/allagma/issues/7).
   Start with `docs/guides/first-study.md` and `conformance/`. Record the literal
   clean-checkout tutorial with a distinct interpreter and paths with spaces.
   Requires local Linux/Python 3.13, not a native model or GPU.

This qualification remains unassigned. Check the pinned overview for the latest
queue; its separate post-merge refresh is tracked in PR #24.

Comment on the issue with your scope and environment. A maintainer confirms the
claim and assignment before overlapping implementation. No paid model access,
GPU, response-time guarantee or release deadline is involved. Submit concise
sanitized evidence with its exact tested commit. A documentation change needs a
rendered review and link check, not a test that merely repeats its prose.

The [triage record](issue-triage.md) explains why only #18 and #19 were added.
These available tasks carry `help wanted`; their prerequisites make them more
involved than a good first issue. Claimed #6 has no newcomer-discovery labels.

## Awaiting owner review

[#19: runnable toy-to-paper workflow](https://github.com/alohays/allagma/issues/19)
is implemented in [draft PR #25](https://github.com/alohays/allagma/pull/25),
assigned to `alohays`. The [walkthrough](../guides/toy-to-paper.md) and
[acceptance record](toy-paper-walkthrough.md) cover actual retained values,
explicit attribution, review freshness, preservation and the optional TeX
rebuild. It remains open pending owner review/merge; do not duplicate the work.

[#18: Run adapter regressions in the required check](https://github.com/alohays/allagma/issues/18)
is assigned to `alohays`. [PR #20](https://github.com/alohays/allagma/pull/20)
appeared during triage and proposes the repair. Review its acceptance criteria
before closure; do not begin a duplicate implementation. This issue has no
`help wanted` label while it awaits review.

## Claimed work

[#6: Describe the EMA figure accessibly](https://github.com/alohays/allagma/issues/6)
is in progress, assigned to `codedbypraneetha`. Start with
`studies/ema-schedule/RESULTS.md` and its figure. The existing claim is confirmed;
coordinate with the assignee and preserve the figure and results. The stated
Windows/Node environment is suitable for this documentation task.

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
