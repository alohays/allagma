# Contributor tasks

These are actual **maintainer-proposed** tasks in the
[first contributor milestone](https://github.com/alohays/allagma/milestone/1).
They do not imply external demand or prior contributors. The
[pinned overview](https://github.com/alohays/allagma/issues/9) is the current work
queue; read the [claim and review process](workflow.md) before starting.

## Available work

1. [#19: Document a runnable toy-to-paper workflow](https://github.com/alohays/allagma/issues/19).
   Start with `examples/toy-study/` and the first-study and paper guides. Bind
   actual toy values and claims to a new paper revision, with explicit coverage
   and scoped reviews. Python/research-documentation familiarity is useful;
   TeX is only needed for the separate optional build.
2. [#22: Align paper-source size admission with extraction](https://github.com/alohays/allagma/issues/22).
   Start with `adapters/arxiv/package.py` and the paper conformance fixtures.
   Count generated source files and bound copies before accepting an archive.
   The boundary tests need no TeX, model or scientific rerun.
3. [#23: Diagnose exported studies accurately](https://github.com/alohays/allagma/issues/23).
   Start with `allagma/diagnostics.py` and the bundled CLI. A healthy standalone
   study should not fail because source-only toy examples are absent. Preserve
   read-only behavior and meaningful missing-resource, lock and ownership checks.
4. [#7: Qualify Linux/Python 3.13 onboarding](https://github.com/alohays/allagma/issues/7).
   Start with `docs/guides/first-study.md` and `conformance/`. Record the literal
   clean-checkout tutorial with a distinct interpreter and paths with spaces.
   Requires local Linux/Python 3.13, not a native model or GPU.

All four are unassigned. The order reflects the available implementation work;
the small #19 walkthrough can proceed alongside the two follow-ups.

Comment on the issue with your scope and environment. A maintainer confirms the
claim and assignment before overlapping implementation. No paid model access,
GPU, response-time guarantee or release deadline is involved. Submit concise
sanitized evidence with its exact tested commit. A documentation change needs a
rendered review and link check, not a test that merely repeats its prose.

The [latest triage](post-pr20-triage.md) explains why only #22 and #23 were added.
These available tasks carry `help wanted`; their prerequisites make them more
involved than a good first issue. Claimed #6 has no newcomer-discovery labels.

## Claimed work

[#6: Describe the EMA figure accessibly](https://github.com/alohays/allagma/issues/6)
is in progress, assigned to `codedbypraneetha`. Start with
`studies/ema-schedule/RESULTS.md` and its figure. The existing claim is confirmed;
coordinate with the assignee and preserve the figure and results. The stated
Windows/Node environment is suitable for this documentation task.

## Merged contributor improvements

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
