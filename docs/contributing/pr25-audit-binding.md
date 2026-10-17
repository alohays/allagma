# Toy-paper audit binding

The owner authorized repairing all open PRs, making ready drafts regular, and
merging changes that pass final review and the repository gates. PR #25's earlier
review-history repair remains intact. This follow-up addresses preparation's
separate obligation to use the selected analysis's retained audited evidence.

## Reproductions and repair

At `38b37a1e0bf6b9af2f3fcdbecba7192b7b580754`, changing a claim's text or status
after a passing audit still allowed publication preparation. A passing stub
without a review reference, a missing or inconsistent immutable audit receipt,
and an actual passing audit of another analysis also passed. The
[regression log](evidence/pr25-audit-binding/before.log) records six failing
assertions against that implementation. Separately, a changed frozen derivation
was accepted; its [reproduction](evidence/pr25-audit-binding/derivation-before.log)
is retained as a seventh failure. Only disposable fixture copies were changed.

Preparation now verifies the selected `a001` review's path, digest, record
contract, passing verdict, manuscript and original input. The current claim
content must equal that input, and the latest audit must agree with the retained
receipt. Existing campaign material checks cover the complete frozen inventory,
including the derivation. Transitive references remain verified. All checks
precede publication creation and do not execute a campaign, regenerate a report,
or write an audit. Relocated studies remain supported: historical absolute
paths in review input are not treated as the current study location.

These checks bind retained content; they do not authenticate an independently
trusted root or establish scientific truth. The publication still starts
unreviewed and requires the reader's scoped scientific and wording judgments.

## Verification

Implementation commit `cefd166ba51bf4f5ee8d9d1f90e607a211af272f` passes all
11 toy-paper tests and all 203 offline conformance tests without skips. Full
I1–I5 acceptance passes, including the complete default toy with 26 successful
attempts, one failure, one interruption and 521 audited references. Rejection
tests verify unchanged input bytes and modification times and no publication
creation. The normal preparation, stale-review recovery and full superseded
review history tests remain passing.

The production documentation build and all 18 desktop/mobile browser tests
also pass. [Validation details](evidence/pr25-audit-binding/validation.json)
bind the commands and implementation digests; the
[focused test log](evidence/pr25-audit-binding/after.log) records each case.
The original walkthrough evidence remains a dated record of its own source.
This is agent-assisted engineering review, not independent scientific or native
host qualification. Final integration and GitHub checks are separate merge gates.
