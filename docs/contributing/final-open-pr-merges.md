# Final audit and open-PR merges — 10 October 2026

All three pull requests open at the start of this audit are merged. The owner
authorized a final audit and sequential merges when ready. No blocking finding
remained after checking the current revisions, previous review findings,
integration, documented commands and applicable validation.

## Merge sequence

Merge commits preserve the feature history. Each merge used its verified head
SHA and the normal repository rules, without an administrative bypass. Before
each subsequent merge, the preceding main commit passed conformance/full
acceptance, documentation/browser checks and Pages deployment.

| Order | PR | Reviewed head | Merge commit | CI on the merge |
| --- | --- | --- | --- | --- |
| 1 | [#16: repository rules](https://github.com/alohays/allagma/pull/16) | `2dbbba76a218eaca4154d2d5314f302752484609` | `f9986a2e057791d7a2849c233c1fe0ca05992615` | [Conformance](https://github.com/alohays/allagma/actions/runs/38022073597) · [Docs](https://github.com/alohays/allagma/actions/runs/38022073578) · [Pages](https://github.com/alohays/allagma/actions/runs/38022073577) |
| 2 | [#15: duplicate-key recovery](https://github.com/alohays/allagma/pull/15) | `693b91e8fcf37483ebb6c9bea3c18ca80d5a8816` | `342ee4f23a754df1a1440e6506c215dd2560802c` | [Conformance](https://github.com/alohays/allagma/actions/runs/38022280547) · [Docs](https://github.com/alohays/allagma/actions/runs/38022280502) · [Pages](https://github.com/alohays/allagma/actions/runs/38022280498) |
| 3 | [#14: reference research and portable papers](https://github.com/alohays/allagma/pull/14) | `13cf79e1a8d68e8f2733ea8bb448d67ddf9dae59` | `f235f1868eec7f6cc9518e5d59053a236b876358` | [Conformance](https://github.com/alohays/allagma/actions/runs/38022458464) · [Docs](https://github.com/alohays/allagma/actions/runs/38022458478) · [Paper](https://github.com/alohays/allagma/actions/runs/38022458471) · [Pages](https://github.com/alohays/allagma/actions/runs/38022458484) |

#15 and #14 received ordinary merges from main before their final gates. Their
feature changes were preserved. The duplicate-key recipe was unchanged, and
#14's runtime, adapters, methods, contracts, tests, tools and scientific files
were identical to the independently checked `8ec5e5e` revision. All four #14
review threads are resolved; no pending review remains. The intentionally
skipped PR-event acceptance job was supplemented by successful branch-push and
main acceptance runs.

## Final review evidence

For #16, both committed ruleset payloads and their hashes match fresh GitHub
readback. Main is protected; the feature branch is outside those rules. The
required Actions checks are `targeted` and `build-and-test`, review conversations
must be resolved, and the bypass lists are empty. Zero required approval votes
remains the documented single-maintainer policy. Catalog validation, six
compact-source tests and 348 canonical documentation links pass. The merge
exercised the ordinary PR path; no destructive enforcement probe was used.

For #15, all three documented shell blocks ran literally in one POSIX shell,
with a temporary parent directory containing spaces. The duplicate copy exits
2 with the named-key error; the original exits 0 with the documented result.
Both files retain their bytes and modification times, the damaged copy remains
available, and the shipped fixture is unchanged. The recipe, goal-history
integration, catalog check, local links and hosted checks pass. Issue #5 closed
through the merge; its obsolete available/newcomer labels were removed.

For #14, the [four prior findings](pr14-revisions.md) were checked in code and
against fresh regressions:

- Reading notes have a separate namespace, copies refuse collisions, and the
  unpacked archive's own verified builder is executed. The real TeX collision
  regression passes, including a reading note named `build.py`.
- Preparation admits the protected dossier and working copy, including the
  snapshot receipt, before creating the workspace. Oversized and changed-source
  cases fail with bounded, retained output.
- Policy adoption admits the complete history/replacement transaction before
  either write. Capacity and free-space refusals preserve the prior records.
- Review fingerprints bind section roles, paths and hashes. Swapping abstract
  and limitations invalidates both reviews; JSON key order does not.

All 55 focused reference, acquisition, paper and preparation tests and seven
compact-source tests pass. Fresh full acceptance passes **184 tests and I1–I5**.
The complete toy retains 24 confirmation replicates, 26 successful attempts,
one deliberate failure and one interruption. Its 521-reference audit passes
without findings. The merged runtime's source digest matches this local
acceptance run.

The scientific check recomputes all 114 retained summaries in a temporary copy.
Six selected inputs match the original r07 package index, and regenerated
publication values match retained bytes. This repeats neither training nor
metric extraction from saved samples. The optional paper build and verification
pass, including the real standalone archive entrypoint. The freshly built
eight-page PDF and source archive match the retained revised delivery exactly:

- PDF: `7aea0bb5cac8bd0a108a977aaf48c70cdd23cbbde5a08b97b4eed9c34d0c98ce`.
- Sources: `d1d63141f243632fca1656b7d2a88e72aa53f81fa2ef60a10c64784e5e0c2559`.

All eight freshly rendered pages were inspected without clipping, overlapping
text, missing glyphs or unresolved references. Local TeX Live 2024 and hosted
TeX Live 2023 checks pass. These checks do not establish arXiv acceptance or
independent scientific peer review.

The integrated documentation passes 384 canonical links, a 43-page production
build, 2,835 internal links/assets and all 18 desktop/mobile browser tests.
Those checks cover search, keyboard access, figures, video playback/seeking,
English captions and page layout. Six additional checks against the live site
pass on desktop and mobile: search, video playback/seeking/captions, and every
canonical page's rendering. The live build receipt identifies `f235f18` and the
unchanged movie digest. Deployment evidence is retained with the merge receipts.

## Preservation and records

The [evidence manifest](evidence/final-open-pr-merges/manifest.json) binds the
merge receipts, actual CI job results, local checks, paper inspection and
preservation comparison. Detailed local outputs remain in ignored
`work/final-pr-merge/`; hosted Actions retain their normal artifacts.

Existing studies, frozen evaluations, contracts, media and project model
configuration are unchanged from pre-audit main `5f519e6`. #14 adds its separate
publication revision. No native model session, new scientific training, resource
expansion, release publication or history rewrite occurred. The current licensed
movie keeps its original digest. [Historical-audio rights](https://github.com/alohays/allagma/issues/8)
remain an unresolved maintainer issue.

This is an agent-assisted maintainer audit, not independent human approval.
The standing commit-and-push instruction applies to this record and the related
contributor-status corrections, which use the protected PR path as well.
