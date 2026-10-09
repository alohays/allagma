# Sequential PR merges — 10 October 2026

The owner authorized a final review and sequential merging of the previously
reviewed PRs. #10, #11 and #12 are now merged. No new blocking finding appeared
in the final diff, integration and regression review. Their reviewed heads were
unchanged, and each actual merge tree matched the locally tested tree.

## Merge gates

Times below are UTC (the task date is 10 October in Asia/Seoul). The next PR was
merged only after the preceding merge's conformance/full acceptance,
documentation/browser checks, and Pages build/deploy had all succeeded.
Job completion and gate-verification timestamps are retained in the receipts.

| PR | Merge commit | Merged at (UTC) | Conformance tests | Successful CI |
| --- | --- | --- | --- | --- |
| [#10](https://github.com/alohays/allagma/pull/10) | `5c17dedfaaff49a6bcb9619b4067b2acdb71cde2` | 2026-10-09T16:05:29Z | 118; I1–I5 pass | [Conformance](https://github.com/alohays/allagma/actions/runs/37956565752) · [Docs](https://github.com/alohays/allagma/actions/runs/37956565651) · [Pages](https://github.com/alohays/allagma/actions/runs/37956565746) |
| [#11](https://github.com/alohays/allagma/pull/11) | `b7bdf3411d046c5c9e94d4936e8bc4d64d48b9a8` | 2026-10-09T16:08:43Z | 126; I1–I5 pass | [Conformance](https://github.com/alohays/allagma/actions/runs/37956962919) · [Docs](https://github.com/alohays/allagma/actions/runs/37956962899) · [Pages](https://github.com/alohays/allagma/actions/runs/37956962826) |
| [#12](https://github.com/alohays/allagma/pull/12) | `657ea5d279235bffe384d96e3cc41fe7522b234f` | 2026-10-09T16:13:26Z | 134; I1–I5 pass | [Conformance](https://github.com/alohays/allagma/actions/runs/37957548406) · [Docs](https://github.com/alohays/allagma/actions/runs/37957548352) · [Pages](https://github.com/alohays/allagma/actions/runs/37957548726) |

All three hosted documentation runs include 18 desktop/mobile browser tests.
The required jobs were checked individually: `targeted` and `acceptance`,
`build-and-test`, and both Pages `build` and `deploy`. No later PR was merged
while any preceding required job was pending. The workflow receipts bind these
results to each actual main merge SHA.

## Final review and integration

- #10: re-read all six changed files; catalog validation and five adaptation
  tests pass. Full-precision bias, complete campaigns/audits, boundary inputs,
  mixed settings and preservation are covered.
- #11: re-read all five files on main after #10; catalog validation, eight
  diagnostics tests and the actual offline `doctor` command pass. Failure
  isolation, malformed JSON, no execution and unchanged study bytes/mtimes
  remain covered.
- #12: re-read all six files on main after #11; catalog validation and 26
  evidence, diagnostics and contract tests pass. The 521-reference default toy,
  mixed malformed lists, limits, strict JSON and path confinement are covered.

Final pre-merge COMMENT reviews were submitted on the exact feature heads
through GitHub's review workflow. This is agent-assisted maintainer review;
GitHub does not allow this account to approve its own PRs. The earlier inline
findings, fixes and resolved threads remain in the [original review record](pr-review.md).

A fresh actual CLI workflow on merged main `657ea5d279235bffe384d96e3cc41fe7522b234f`
prepares bias `0.123456789`, inspects prerequisites, starts and runs the full
26-run campaign, analyzes and audits it, then verifies declared evidence.
All commands exit 0. The final inspector checks 504 references in 505 reads
and leaves every study file's contents and modification time unchanged. This
normal adapted workflow has no injected failures; hosted I1–I5 acceptance also
runs the full default toy with its deliberate failure and interruption.

## Retained evidence and scope

[The evidence manifest](evidence/sequential-merges/manifest.json) binds merge
receipts, per-job CI results, focused test logs, the combined workflow and
preservation checks. Full CI logs and the new study remain in ignored
`work/final-merges/`; hosted Actions retain their normal artifacts.

Merge commits preserve the original feature history and authorship. Frozen
studies, evaluations, media, contracts, methods, adapters and project model
configuration are unchanged from the pre-merge main. There was no native model
session, GPU work, additional scientific budget, release publication or history
rewrite. Passing offline fixtures do not extend native-host qualification.

Linked issues #3, #2 and #4 closed through their PR merges, and their stale
owner-review labels were removed. The README, roadmap, contributor guidance,
changelog and goal now reflect the merged features. Historical review/evidence
records remain intact and are identified as pre-merge records.

Newer #14 had no submitted review and #15 was draft when this task started;
both were outside the previously reviewed merge set and remain open with their
heads and draft states unchanged.
