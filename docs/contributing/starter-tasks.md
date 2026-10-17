# Contributor tasks

These are actual **maintainer-proposed** tasks in the
[first contributor milestone](https://github.com/alohays/allagma/milestone/1).
They do not imply external demand or prior contributors. The
[pinned overview](https://github.com/alohays/allagma/issues/9) is the current work
queue; read the [claim and review process](workflow.md) before starting.

## Available work

No unclaimed implementation or qualification task is currently listed.
Issues #7, #19, #22 and #23 are completed on main; their merged work is listed
below. The accessibility task #6 remains claimed. Check the pinned overview
before proposing a new bounded contribution.

Comment on the issue with your scope and environment. A maintainer confirms the
claim and assignment before overlapping implementation. No paid model access,
GPU, response-time guarantee or release deadline is involved. Submit concise
sanitized evidence with its exact tested commit. A documentation change needs a
rendered review and link check, not a test that merely repeats its prose.

The [dated triage](post-pr20-triage.md) explains why only #22 and #23 were added.
Claimed #6 has no newcomer-discovery labels. Completed tasks are not advertised
as available work.

## Claimed work

[#6: Describe the EMA figure accessibly](https://github.com/alohays/allagma/issues/6)
is in progress, assigned to `codedbypraneetha`. Start with
`studies/ema-schedule/RESULTS.md` and its figure. The existing claim is confirmed;
coordinate with the assignee and preserve the figure and results. The stated
Windows/Node environment is suitable for this documentation task.

## Merged contributor improvements

[#7: Linux/Python 3.13 onboarding](https://github.com/alohays/allagma/issues/7)
is complete through [#28](https://github.com/alohays/allagma/pull/28). The
[qualification record](linux-python313.md) retains actual Debian 12/aarch64,
CPython 3.13.16 execution, the missing-`ps` failure, and 217 passing tests on
the integrated feature main. This does not qualify all Linux/Python combinations.

Issues [#19](https://github.com/alohays/allagma/issues/19),
[#22](https://github.com/alohays/allagma/issues/22) and
[#23](https://github.com/alohays/allagma/issues/23) are complete through
PRs [#25](https://github.com/alohays/allagma/pull/25),
[#26](https://github.com/alohays/allagma/pull/26) and
[#27](https://github.com/alohays/allagma/pull/27). Use the
[toy-to-paper walkthrough](../guides/toy-to-paper.md),
[paper-source guide](../arxiv-papers.md) and
[standalone diagnostics](../cli.md#exit-status-and-costs) on main. The
[integration record](open-pr-integration.md) includes audit-binding regressions,
bounded-copy and exported-helper checks, the complete workflow and TeX rebuild.

[#18: required adapter regressions](https://github.com/alohays/allagma/issues/18)
is complete through [#20](https://github.com/alohays/allagma/pull/20). The
[three-iteration review](pr20-review-loops.md) records 192 conformance tests,
19 tooling tests and the actual selected-failure proof. No duplicate repair or
owner-review wait remains for that issue.

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
