# First contributor workflow: delivery ledger

This is an active implementation ledger, not a completed contributor launch.
The source baseline is `5c9a7651d5f627da8e7ed5992fe869cedb43e8f5`.
The [goal](../../GOAL.md#first-contributor-workflow--9-october-2026) defines the
complete outcome; actual GitHub objects and pushed-head checks are required.

## Current state

GitHub inspection on 9 October 2026 found **no issues**, one open
[Dependabot PR](https://github.com/alohays/allagma/pull/1), no milestone,
disabled Pages and Discussions, and **public** visibility. Public visibility
conflicts with the active goal's private-visibility instruction. A user-input
question is pending: restore private visibility or retain the current public
setting. No visibility change, GitHub backlog write or implementation-branch
push has been made while that consequential choice is unresolved. The
[historical-audio blocker](../launch/owner-actions.md) remains uncleared.

## Implemented locally

| Improvement | Branch and commit | Passing local evidence |
| --- | --- | --- |
| Read-only prerequisite diagnostics | `codex/contributor-doctor`, `9027823` | 6 targeted tests, all 119 conformance tests, 38-page docs build and 2,172 internal links |
| Adapted toy preparation and correct bias reporting | `codex/contributor-study-adaptation`, `1692652` | 3 targeted tests, all 116 conformance tests, complete documented CLI workflow and audit, 38-page docs build and 2,176 internal links |
| Read-only transitive evidence inspection | `codex/contributor-evidence-verifier`, `ab3b724` | 7 targeted tests, all 120 conformance tests, existing evidence inspection, 38-page docs build and 2,175 internal links |

The three changes apply together without conflicts; the combined checkout
passed all **129 conformance tests**; the earlier integration also passed the catalog check. This temporary
integration test did not merge any changes into `main`. Results are from local
Python 3.11.6 on macOS and Node 22.20.0 for documentation; no native model
session, GPU workload or additional paid service was used. These changes do
not retroactively qualify or alter existing frozen bundles.

The confirmed defect was reproduced before repair: a new toy with bias 0.5
completed 26 successful runs and a 504-reference deterministic audit, but its
claim scope still said bias 0.25. The repaired workflow reports bias 0.5 and
passes independently recomputed paired arithmetic and the audit. This illustrates
why reproducing a report does not establish that its wording matches the science.

The evidence inspector checks all 521 references of the default fault-injected
toy without changing study contents or mtimes. It collects independent missing,
changed, unsafe-path and malformed-record failures and fails on file/byte limits.
Its pass does not establish scientific correctness, package completeness or
host qualification. Diagnostics similarly inspect prerequisites without invoking
hosts, reading model/authentication settings or repairing studies.

A follow-up review reproduced a false rejection of ordinary transport metadata
containing `path`, `sha256` and `size_bytes`. Commit `ab3b724` distinguishes it
from a declared four-field ArtifactRef. The regression checks both acceptance
of untyped transport metadata outside graph coverage and rejection of an
incomplete reference in a typed record field. Before/after receipts are retained
locally; no original evidence file was repaired to make verification pass.

## Remaining delivery work

Seven evidence-grounded issue bodies are prepared locally: the three
implementation tasks; duplicate-key recovery documentation; an accessible EMA
figure description; Python 3.13/Linux offline qualification; and the
maintainer-owned audio blocker. The three small tasks are intended to remain
unassigned, with `good first issue` only on the two bounded documentation tasks.

After visibility is resolved, recheck GitHub for duplicates, publish the label
set/milestone/issues and pin the contributor overview. Push each implementation
branch, open its linked draft PR, verify exact pushed-head CI and repair any
failures. Publish the separate Dependabot recommendation. Connect the actual
URLs and states from `CONTRIBUTING.md`, `ROADMAP.md`, starter tasks and the
community plan, then verify all relationships and render the changed docs.
The lightweight claim/triage/review/evidence/credit guide is prepared locally
and will link the real overview rather than placeholder URLs.
The three PR descriptions, overview, label/milestone payloads and separate
Dependabot comment are also prepared. Every pinned-source issue link resolves
in the baseline Git tree. Branch-diff inspection confirms that no frozen
evaluation/study evidence, media, contract schema, release metadata, project
model configuration or Dependabot-managed dependency version changed.

Dependabot review found no blocking issue in its two-file diff at
`0e612e14c139a5883ddb6fff6595247e15837a12`. Its retained
[exact-head documentation run](https://github.com/alohays/allagma/actions/runs/37775281206)
passed installation, npm audit (zero vulnerabilities), 38 pages, 2,167 internal
links and 14 browser tests; conformance is also green. The recommendation is
owner review followed by merge if the eventual current-head/base checks remain
green. No dependency bump is duplicated in these contributor branches.
