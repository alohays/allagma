# Open PR integration

The owner authorized repairing every open PR, making ready drafts regular, and
merging changes after verification. The initial open set was #24–#27. The
three feature PRs were integrated sequentially with merge commits, preserving
their original authors and history. Required checks were enforced without
administrator bypasses. Documentation PR #24 reconciles the resulting queue
and retains this record; its final merge commit and checks are on
[the PR](https://github.com/alohays/allagma/pull/24).

## Review decisions

| PR | Verified change and decision | Merge commit |
| --- | --- | --- |
| [#26](https://github.com/alohays/allagma/pull/26) | Complete source-byte/file accounting, generated bibliography/provenance, bounded copies, validated digests and nonblocking regular-file reads. Current-head conformance, docs, actual TeX and acceptance passed before merge. | `dac1380278a3186ce14f6f9ce41248814fc08104` |
| [#27](https://github.com/alohays/allagma/pull/27) | Standalone/source/unknown diagnostic scopes, independent failures, immutable recovery and no execution. Updated against #26; the source tree matches the combined 36-test and real-TeX run. Fresh CI and acceptance passed before merge. | `da9ea45844c59d14ece28789f2707627e8af724f` |
| [#25](https://github.com/alohays/allagma/pull/25) | Repaired retained-audit binding, verified the complete walkthrough after integrating #26/#27, converted the draft to regular, and merged after fresh CI and I1–I5 acceptance. | `f7e32a70b43675444e9f88c07d227a8b762b9e56` |
| [#24](https://github.com/alohays/allagma/pull/24) | Reconciles the three documentation conflicts and changes #19/#22/#23 from owner review to completed. Preserves historical triage receipts, #6's assignee, #7's available qualification scope and #8's separate rights decision. | See the PR's final merge metadata. |

PR #25's earlier superseded-review-chain repair did not address preparation's
stale claim ledger. Seven new failing assertions covered changed claim text or
status, missing/inconsistent audit history, an audit of another analysis and a
changed frozen derivation. The [repair record](pr25-audit-binding.md) retains
the before/after tests. Preparation now rejects these inputs before publication
writes and keeps the original evidence intact. No other actionable finding
remained after reviewing the current #26/#27 implementations and their callers.

## Combined verification

The integrated feature head is `74e00f5ad7bba239e36467454f3a3b2b18f98db6`.
Its [required check](https://github.com/alohays/allagma/actions/runs/39049966079)
passes all **217 conformance tests**. The
[full acceptance run](https://github.com/alohays/allagma/actions/runs/39049961609)
passes I1–I5 and the complete toy. The local production site build generates
44 pages and 2,976 valid local links/assets; all 18 desktop/mobile browser
tests pass. The required [documentation CI](https://github.com/alohays/allagma/actions/runs/39049966081)
also passes. The final documentation PR has its own current-head checks.

All eight literal [toy-to-paper commands](../guides/toy-to-paper.md) were rerun
from a fresh sparse checkout with spaces in checkout and study paths. Their
exits were **0, 0, 2, 0, 0, 2, 0, 0**: missing reviews and stale reviews fail
as intended, and fresh supplied reviews restore a pass. The executor read the
frozen derivation, original report, claims and all seven sections, and
recomputed the paired mean and approximate interval from retained raw samples.
All **765** pre-publication files and **17** first-publication files retain
their bytes and modification times. The original report remains the default.

Actual TeX Live 2024 compilation, the internal archive rebuild and the separate
recipient invocation of `anc/build.py` all pass with network access denied.
Both rendered PDF pages were inspected for clipping, overlap, numeric values,
section flow, page numbering, anonymous attribution and the explicitly empty
external bibliography. The PDF hash is
`73d993274782c36dffb4fa854fc0a40d48766226071ae0ce3a5c0e73cce73f0d`.
The matching bytes across these local builds are an observation, not a
cross-platform reproducibility promise.

The [walkthrough receipt](evidence/open-pr-integration/walkthrough.json) retains the
literal blocks, expected/actual exits, environment, source digests, preservation
counts, measurements and delivery results. Inspect
[page 1](evidence/open-pr-integration/paper-page-1.png) and
[page 2](evidence/open-pr-integration/paper-page-2.png). The
[verification receipt](evidence/open-pr-integration/validation.json) records the
reviewed heads, merge metadata and CI gates; its timestamps identify the snapshot.

## Queue and scope

Issues #19, #22 and #23 are closed through their implementation PRs and their
stale `status: owner review` labels are removed. The roadmap, starter list,
community/owner guidance and pinned overview reflect completion. Issue #6
remains assigned to `codedbypraneetha`; #7 remains available; #8 remains blocked
on the maintainer's historical-audio decision. No completed implementation is
advertised as unclaimed work.

These are agent-assisted engineering and scoped executor reviews, not
independent scientific approvals. Tests do not extend native-host or
Linux/Python 3.13 qualification. Frozen studies, evaluations, existing bundles,
historical media, model selection and scientific resource ceilings are unchanged.
No new release, submission, native session or history rewrite is part of this
integration.
