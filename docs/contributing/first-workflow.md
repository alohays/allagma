# First contributor workflow: delivery ledger

Historical delivery record: the draft states and original heads below describe
the initial contributor setup. The subsequent [PR review](pr-review.md) fixed
three findings, made #10/#11/#12 regular and ready, and merged #1 with owner
authorization. The later [merge records](final-open-pr-merges.md) include
#10–#12 and #14–#16; those features are now on main. Use the
[current triage](post-pr20-triage.md) for issue status and claims, including the
completed #20 merge and closed #18. The original
evidence receipts and the dated setup narrative below remain unchanged.

The contributor backlog and draft PRs are published, the public site and community
entry points are operational, and anonymous onboarding/live checks pass. All
implementation PRs remain unmerged for owner review.
The source baseline is `5c9a7651d5f627da8e7ed5992fe869cedb43e8f5`.
The [goal](../../GOAL.md#first-contributor-workflow--9-october-2026) defines the
complete outcome; actual GitHub objects and pushed-head checks are required.

## State at initial public activation

The owner resolved the original visibility conflict on 9 October 2026: public
visibility is intentional and must remain. The [updated goal](../../GOAL.md#public-contributor-workflow-and-documentation-activation--9-october-2026)
authorizes contributor publication, public documentation and community entry
points. Earlier private-only decisions remain historical evidence, not current
gates. [Historical-audio rights](https://github.com/alohays/allagma/issues/8)
remain unresolved and maintainer-owned.

- [Documentation](https://alohays.github.io/allagma/) is live. The first actual [Pages deployment](https://github.com/alohays/allagma/actions/runs/37813656778) succeeded at `bd4c2a98d0cf37155e65053d601422a114956c23` with the existing scoped permissions.
- [Overview #9](https://github.com/alohays/allagma/issues/9) is pinned and links [milestone 1](https://github.com/alohays/allagma/milestone/1).
- Task issues [#2](https://github.com/alohays/allagma/issues/2), [#3](https://github.com/alohays/allagma/issues/3), [#4](https://github.com/alohays/allagma/issues/4) await owner review through draft [#11](https://github.com/alohays/allagma/pull/11), [#10](https://github.com/alohays/allagma/pull/10), [#12](https://github.com/alohays/allagma/pull/12), respectively.
- [#5](https://github.com/alohays/allagma/issues/5), [#6](https://github.com/alohays/allagma/issues/6), [#7](https://github.com/alohays/allagma/issues/7) are available and unassigned. Only #5/#6 carry `good first issue`; all three carry `help wanted`.
- [Welcome #13](https://github.com/alohays/allagma/discussions/13) is published and pinned. Q&A, Show and tell, and Ideas are available; no outside outreach was performed.
- The repository website is the working docs URL; the prepared social preview is uploaded, and private vulnerability reporting is enabled.

The PRs are independent and unmerged. Main's documentation describes main's
commands and clearly labels these draft features as proposed. New releases and
PR merges remain owner decisions; no new native session or model usage was added.

## Published draft improvements and local evidence

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

## Pushed-head validation and delivery checks

The [PR validation receipt](evidence/pr-validation.json) binds each published
head and linked issue. All applicable documentation, targeted conformance and
push-time full offline acceptance jobs passed. Duplicate acceptance is skipped
on PR events by the existing workflow; a skipped job is not claimed as a pass.
Every pinned-source issue link resolves in the baseline Git tree. Branch diffs
leave frozen evaluation/study evidence, media, contract schemas, release
metadata, model configuration and Dependabot-managed versions unchanged.

The [workflow guide](workflow.md) defines claim, triage, evidence, review and
credit practices. [Starter tasks](starter-tasks.md), [roadmap](../../ROADMAP.md),
[contribution guide](../../CONTRIBUTING.md) and [community entry points](../launch/community-plan.md)
link the actual GitHub objects. Recommended review order is #10, #11, #12;
there are no stacked dependencies. Keep all drafts unmerged for owner review.

## Public activation verification

The [completion audit](evidence/public-activation/completion-audit.json) binds the
settings, open/unassigned issues, linked draft heads, category metadata and
successful main CI to `a57ba0a2889cc6516be6685a2153e64541e5abf8`.
Its [actual Pages deployment](https://github.com/alohays/allagma/actions/runs/37817332243),
[documentation checks](https://github.com/alohays/allagma/actions/runs/37817332178)
and [conformance/acceptance](https://github.com/alohays/allagma/actions/runs/37817331906)
all passed. The public `build-info.json` matched that commit and the cleared
movie digest. A later documentation/receipt commit is checked separately before handoff.

| Required check | Concrete evidence and scope |
| --- | --- |
| Anonymous source onboarding | [Receipt](evidence/public-activation/anonymous-onboarding.json): source `0a5f41c`, minimal environment with no tokens/cookies, Git config/helper/auth headers disabled, prompts disabled; sparse clone, catalog, full offline toy and second audit pass. 26 successful attempts, 1 failure, 1 interruption, 521 verified references and realized difference 25/384. Python 3.11.6/macOS only; Linux/Python 3.13 task remains open. |
| Live paths and assets | [HTTP receipt](evidence/public-activation/public-http.json): 38 content routes (plus the build's separate 404 page), 1,848 internal links/fragments, no failures; anonymous movie/caption/provenance/figure-preview assets match committed bytes. These full-route checks used `0a5f41c`; the subsequent site change only repairs download links. |
| Desktop/mobile interaction | [Browser receipt](evidence/public-activation/live-browser-final.json): 1440×1000 and 390×844 layouts in both themes, no horizontal overflow on inspected views; search, deep links, mobile menu, skip link, keyboard artifact tabs, actual EMA figure, transcript and captioned playback. This is responsive browser inspection, not qualification of every physical device. |
| Media and seeking | 100.433-second 1600×900 movie decodes without errors; English captions visibly render, with 22 cues in the hash-verified VTT. Keyboard seeking while paused advances from 44.090711 to 45.095033 seconds. README playback advances from 0.054824 to 94.534625 seconds while signed out. The browser bridge does not expose cue arrays; cue count is checked from the downloaded VTT, not inferred from the bridge. |
| Actual downloads and repair | The original caption link opened VTT text. Commit `a57ba0a` adds real download attributes and an MP4 download link. Both actual browser downloads complete without leaving the demo page: movie 2,875,851 bytes, SHA-256 `6435ccbd6ba55757fd512e3b631478227831b9d77a80b300776bbe8164841cc3`; caption 2,242 bytes, SHA-256 `8f8bfd94926a2179891c47cd1f3d4ff9a1b73fea8ebf63d7b2fa05c42853e6ad`. |
| Public README links | [31-link receipt](evidence/public-activation/readme-links.json): anonymous HTTP checks pass; private security submission intentionally redirects to GitHub sign-in. The inline video is expanded near the top and its anonymous bytes match the cleared MP4. |
| Community and repository settings | Pinned overview #9 and welcome #13; Q&A is answerable; Show and tell/Ideas exist; custom social preview and private vulnerability reporting enabled; website is the live docs URL. No new release/tag, PR merge or external outreach. |

The [evidence manifest](evidence/public-activation/manifest.json) lists hashes and
sizes. Retained views show the [desktop](evidence/public-activation/live-desktop-light.png),
[mobile](evidence/public-activation/live-mobile-light.png),
[visible captions](evidence/public-activation/live-video-captions.png),
[signed-out README](evidence/public-activation/readme-anonymous-playback.png),
[pinned welcome](evidence/public-activation/welcome-pinned.jpg), and
[uploaded social preview](evidence/public-activation/social-preview.jpg).

Public main's Python core, study programs, contracts, frozen evidence, release
metadata and project model configuration remain unchanged from the qualified
baseline used here. The three improvements stay on their separate draft branches.
Only current cleared media is built from main into Pages. The exact unresolved
owner decisions are review/merge of #10/#11/#12 and Dependabot #1; historical
audio clearance or a separately authorized strategy in #8; and any later
release/version or external-outreach decision.

Dependabot review found no blocking issue in its two-file diff at
`0e612e14c139a5883ddb6fff6595247e15837a12`. Its retained
[exact-head documentation run](https://github.com/alohays/allagma/actions/runs/37775281206)
passed installation, npm audit (zero vulnerabilities), 38 pages, 2,167 internal
links and 14 browser tests; conformance is also green. The [posted recommendation](https://github.com/alohays/allagma/pull/1#issuecomment-6065003786) is
owner review followed by merge if the eventual current-head/base checks remain
green. No dependency bump is duplicated in these contributor branches.
