# Open pull request review — 10 October 2026

The owner requested a sequential, detailed review of every open PR. #14 and #15
were open at the initial inventory; #16 opened during the pass and was reviewed
next. Each assessment is a submitted GitHub review bound to the exact head.
Implementation fixes, conflict resolution and merges remain follow-up work.

| PR and reviewed head | Review conclusion | GitHub review |
| --- | --- | --- |
| #14, `72e88c39a6631dadb78d8162d8714baf324ab073` | Changes required: one P1 and three P2 findings | [Full assessment and inline threads](https://github.com/alohays/allagma/pull/14#pullrequestreview-5473294360) |
| #15, `32fd57e90348bd7ef6f8e14e0514c3a3b2e01fda` | Recovery recipe is sound; `GOAL.md` conflicts with current main | [Full assessment](https://github.com/alohays/allagma/pull/15#pullrequestreview-5473343534) |
| #16, `2dbbba76a218eaca4154d2d5314f302752484609` | No blocking findings | [Full assessment](https://github.com/alohays/allagma/pull/16#pullrequestreview-5473371952) |

The current main used for these comparisons was
`5f519e63e7fc50a2e7da887481444dd9b649eab8`. #14 is regular; #15 and #16 remain
draft. All three remain open, with their reviewed heads unchanged. This record
is a dated review snapshot, not a promise that later revisions have been checked.

## Findings in #14

1. **P1: generated ancillary-file replacement.** Reading notes share a namespace
   with generated package content and can overwrite it. A harmless fixture
   produced a successful delivery whose standalone build entrypoint no longer
   built the paper. Separate the namespaces, reject collisions and exercise the
   actual shipped entrypoint.
   [Inline finding](https://github.com/alohays/allagma/pull/14#discussion_r4232801295).
2. **P2: preparation omits dossier storage.** A 3,000,000-byte reference note
   passed preparation with a 2,000,000-byte workspace ceiling. The resulting
   study occupied 6,486,603 bytes because both dossier copies were omitted from
   admission. Account for the frozen and working copies before writing.
   [Inline finding](https://github.com/alohays/allagma/pull/14#discussion_r4232801582).
3. **P2: policy metadata bypasses cache limits.** Repeated successful policy
   adoptions grew a 10,000-byte cache from 863 to 10,955 bytes without an approved
   limit increase. Bound the complete history/policy write transaction.
   [Inline finding](https://github.com/alohays/allagma/pull/14#discussion_r4232801846).
4. **P2: manuscript section roles are absent from review identity.** Swapping
   abstract and limitations paths preserved the review fingerprint and passed
   validation despite changing the rendered manuscript. Bind section names,
   paths and content together.
   [Inline finding](https://github.com/alohays/allagma/pull/14#discussion_r4232802062).

All four findings remain unresolved. Green checks cover the tested behavior and
do not invalidate these independent reproductions. The full synthetic probes
remain in the ignored local review workspace; this public record contains no
executable ancillary-file replacement payload.

## Architecture and validation

#14 preserves the intended split between portable methods, offline evidence
helpers, acquisition/TeX adapters and study-owned science. The review covered all
120 changed paths, their relevant callers, resource accounting, source
distribution, versioned inputs, paper assembly and new documentation. Its
architecture is suitable once the four concrete boundary defects are corrected.

Fresh catalog checks and 45 reference/acquisition/paper/source-release tests
pass. Full acceptance passes 172 tests and I1–I5, including the complete toy
workflow. Six selected scientific inputs match the original r07 package index;
all 114 summaries and the publication-values file were reproduced in a temporary
copy. The paper rebuild, unpacked-source compilation and output verification
pass. Both the PDF and source archive match the retained artifacts byte-for-byte.
All eight rendered PDF pages were inspected without clipping, overlap, missing
glyphs or unresolved references. This does not constitute independent scientific
peer review or arXiv acceptance.

The #14 documentation build passes 43 pages and 2,828 internal links/assets;
all 18 browser tests pass. The current official
[arXiv source requirements](https://info.arxiv.org/help/submit_tex.html) and
[TeX support documentation](https://info.arxiv.org/help/faq/texlive.html) were
checked against the packaging claims.

#15 changes two documentation files and leaves parser/contract behavior intact.
Every shell block ran literally in one POSIX shell, including a temporary path
with spaces. The damaged record exits 2; the original exits 0. Bytes and mtimes
remain unchanged, and the damaged copy is retained. The commands also work on
current main. Catalog and 18 contract/module tests pass; documentation checks
cover 331 canonical links, 39 pages, 2,425 internal links/assets and 18 browser
tests. Desktop/mobile light/dark inspection confirms the anchor, error output,
successful JSON and code scrolling. GitHub and a local merge-tree check agree
that only `GOAL.md` conflicts with main. Preserve both goal-history additions when
resolving it; no passing combined merge tree is claimed.

#16 changes six configuration/documentation files. Fresh API readback matches
every specified field of both active rulesets and both payload hashes in the
application receipt. Main is protected, feature branches are outside the rules,
and both required check names report success from GitHub Actions app 15368.
The required jobs run on every PR. Zero required approvals is consistent with
the single-maintainer policy; maintainer review remains a separate obligation.
The documentation accurately distinguishes tag update/deletion protection from
tag creation, release authorization and release-asset immutability. These
conclusions were checked against GitHub's
[ruleset semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
and [required-check behavior](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

For #16, catalog checks, six compact-release tests, 348 canonical links and six
local ruleset-README links pass. The production build passes 39 pages and 2,437
internal links/assets; all 18 browser tests pass. Live settings were inspected
read-only. No destructive enforcement probe or settings change was performed.

## GitHub workflow and scope

The authenticated account is the author of all three PRs. GitHub therefore
prohibits formal self-approval and self-requested changes. Each assessment uses
a submitted COMMENT review and states its actual recommendation. #14's review
was created pending, received four diff-anchored comments, and was then submitted.
No pending review or invented inline finding was left behind. #15's conflict is
reported in its high-level review; #16 has no defect comments.

[Compact evidence](evidence/open-pr-review/manifest.json) records the tested
heads, review/comment identities, changed-file inventory, validation and live
settings readback. Detailed local logs, fixtures and rendered images remain in
`work/open-pr-review/`. Exact-head hosted CI links are retained with the review
receipts. Full histories, prior scientific evidence, PR heads, draft states,
resource limits and GUI model settings were preserved. No native model session,
new training, release or merge occurred.

The standing commit-and-push instruction is fulfilled on
`codex/open-pr-review-record`; this documentation branch does not change main,
the reviewed branches or deployed documentation.
