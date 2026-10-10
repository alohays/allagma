# Contributor workflow

The [pinned contributor overview](https://github.com/alohays/allagma/issues/9) is the entry point for the
[first contributor milestone](https://github.com/alohays/allagma/milestone/1). It links the actual issues and
PRs, shows what is available, and gives the review order. These are
maintainer-proposed tasks; agent-assisted implementations are identified in their
PRs. They are not evidence of external adoption or independent endorsement.

## Choose and claim a task

Start with the [available tasks](starter-tasks.md). Read the issue's problem,
source/reproduction, scope, acceptance criteria, validation and prerequisites.
Comment with the part you intend to take, your local environment and any open
scope question. A maintainer confirms the claim, assigns the issue and changes
its status before substantial overlapping work begins. A comment alone is not
an exclusive reservation. A small correction may still be submitted directly
as a PR with its concrete problem and evidence.

Keep the scope small enough to review. If circumstances change, leave a brief
handoff and ask to release the claim; the maintainer can remove the assignment
and return it to available. There is no promised response time, completion date
or automatic removal for inactivity. Do not post credentials, private research
inputs or account/session identifiers in comments or receipts.

## Triage and state

Use one task status label at a time. GitHub issues, labels, assignments and the
milestone are the work queue; no separate project board or bot is required.

| State | Meaning and next action |
| --- | --- |
| `status: available` | Scope is bounded and unclaimed. Read prerequisites, then propose a claim. |
| `status: in progress` | A confirmed assignee is implementing or gathering evidence; link the branch/draft PR when available. |
| `status: blocked` | Name the concrete missing prerequisite or owner decision in the issue. Keep the issue open and link what will unblock it. |
| `status: owner review` | A PR or qualification receipt awaits owner review or a merge decision; tests do not imply merge approval. |

Use `bug` for a reproduced defect, `enhancement` for a proposed behavior or
usability improvement, and `qualification` for a claim that needs new evidence.
`good first issue` applies only to a bounded, approachable task with a local
finish line. `help wanted` invites participation; remove newcomer labels when
claimed so searches continue to show available work. `maintainer-owned` marks
publication decisions that contributors cannot resolve by passing tests.

Triage checks for duplicates and existing PRs first, reproduces the problem or
states the evidence gap, and confirms scope, compatibility and prerequisites.
Retained failures are useful sources; already-fixed defects should not be
reopened without a current reproduction. Each task links its supporting source
and starts with the cheapest relevant validation. A new broad contract/default
change needs the proposal described in [governance](../../GOVERNANCE.md).

## Submit reviewable evidence

Open a draft PR against `main` and link its issue with `Closes #NUMBER` when it
fully addresses that issue. Describe the concrete before/after behavior, source
lineage, compatibility, remaining owner decisions, and dependencies on other
PRs. State which work was agent-assisted and distinguish fixtures from real
host or scientific qualification. Keep the original commit authors; do not
invent reviewers, users, co-authors or endorsements.

Include the tested commit, exact commands, exit/results and the limits of the
evidence. Use compact sanitized receipts or CI links. For docs/visual changes,
include a rendered view; for a behavior change, exercise the relevant failure
and recovery or before/after result. Preserve failed attempts and frozen
records. Default checks are offline and standard-library-only; an ordinary
contribution needs no model session, provider credentials or GPU. See the
[targeted-check table](../../CONTRIBUTING.md) before running a whole campaign.

A maintainer checks the reproduction and acceptance criteria, reads the diff
and source/license provenance, verifies relevant CI on the pushed head, and
checks that frozen evidence, study ownership and scope claims remain intact.
Ask for missing evidence or a smaller scope in the issue/PR rather than silently
changing acceptance. A failing check returns the task to in progress; a concrete
external prerequisite makes it blocked. The overview and starter list should
change when assignments, dependencies or status change.

Draft PRs stay draft until the owner chooses to proceed. The owner authorized this public contributor setup and documentation deployment.
Merge, default-selection changes and new release publication still require owner decisions.
On 9 October 2026 the owner requested a full PR review, authorized merging #1
if ready, and authorized making the three feature PRs regular after fixes.
That [review and validation](pr-review.md) is complete. On 10 October the owner
authorized a final review and sequential merges. #10, #11 and #12 are now
merged, with [successful CI after each merge](merged-prs.md); #1 was merged earlier.
After an owner-approved merge, close the linked task, remove stale status labels,
and update the overview. If the implementation is declined, record the reason
without deleting its tests or discussion. Dependency PRs, including
[Dependabot #1](https://github.com/alohays/allagma/pull/1), receive a separate
review; do not duplicate dependency bumps in feature work.

## Credit and publication boundaries

Git commits and linked PRs preserve attribution. Release notes can name the
contribution and link its PR with the contributor's preferred public attribution;
ask before adding a different name, affiliation or sensitive contact detail.
Code, documentation, reproductions, negative findings and review are all useful
contributions. Scientific authorship and release/default decisions follow
[governance](../../GOVERNANCE.md), not automatic issue completion.

The [historical-audio blocker](https://github.com/alohays/allagma/issues/8) remains maintainer-owned. Retaining
full history and documenting personal metadata did not clear the older audio.
The owner separately authorized the public Pages site and
[pinned welcome](https://github.com/alohays/allagma/discussions/13) on 9 October
2026. New releases, further PR merges, external outreach, history changes and
additional native-onboarding model usage remain separate owner decisions. Use the repository
support and code-of-conduct routes.
