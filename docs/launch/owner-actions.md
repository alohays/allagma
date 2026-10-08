# Public entry points and remaining owner decisions

On 9 October 2026 the owner confirmed that public visibility was intentional and
authorized keeping the repository public, activating Pages/community settings,
publishing the contributor backlog and draft PRs, and posting one pinned welcome.
That instruction supersedes the previous private-only activation gate for these
actions. The earlier decisions and audit receipts remain preserved in Git.

## Activated surfaces

- [Public documentation](https://alohays.github.io/allagma/), deployed with GitHub Actions and `ALLAGMA_PUBLIC_LAUNCH=true`.
- [Contributor overview](https://github.com/alohays/allagma/issues/9), pinned above the issue queue, and the [first milestone](https://github.com/alohays/allagma/milestone/1).
- [Welcome Discussion](https://github.com/alohays/allagma/discussions/13), pinned, with Q&A, Show and tell, and Ideas categories available.
- Prepared social preview uploaded; the repository website points to the live docs.
- [Private vulnerability reporting](https://github.com/alohays/allagma/security/advisories/new) enabled.

The [contributor delivery ledger](../contributing/first-workflow.md) records
verification and exact current objects. Public documentation describes main's
available behavior. Diagnostics, evidence-inspection and study-preparation
features remain proposed in draft PRs, not silently included in main.

## Unresolved historical-audio rights

[Maintainer issue #8](https://github.com/alohays/allagma/issues/8) tracks two older
Apple system-voice recordings retained in Git/PR history. The current movie uses
Kokoro with the recorded Apache-2.0/MIT notices. Replacing it did not clear the
older recordings; public visibility and documentation activation also do not
clear them. The owner chose to retain history unchanged. Obtain and document
clearance or separately authorize an alternative publication/history strategy.
Do not rewrite history or frozen evidence under the contributor task.

Serve only the current cleared media on Pages. The earlier accepted exposure of
author email, local paths and native session IDs is a separate metadata decision,
not an audio-rights grant. See the [publication review](publication-review.md)
and [dated final audit](final-audit.md) for the source evidence.

## Review and release decisions

Review the independent draft changes in this order:
[PR #10](https://github.com/alohays/allagma/pull/10) (confirmed toy reporting
 defect and preparation), [PR #11](https://github.com/alohays/allagma/pull/11)
(prerequisite diagnostics), then [PR #12](https://github.com/alohays/allagma/pull/12)
(read-only evidence inspection). They are validated but unmerged. The owner
decides whether/when to merge and include them in a release. Review
[Dependabot #1](https://github.com/alohays/allagma/pull/1#issuecomment-6065003786)
separately; the contributor changes do not duplicate its dependency updates.

The software remains **0.3.0rc2**, not an asserted stable 0.3.0 release. No new
release, tag, PR merge or external outreach is authorized by this activation.
Release publication needs a separate version decision, current acceptance and
matching immutable source assets. The release-preparation workflow only creates
reviewable assets. Keep large scientific packages opt-in with their hashes and
licenses; not all retained scientific code is MIT.

The extra native-onboarding probe remains incomplete at its existing 15-minute
plus 5-minute model-session limit. No additional continuation, project model
override, or new scientific campaign is part of this public activation.
