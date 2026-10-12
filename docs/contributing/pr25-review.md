# PR #25 review — 12 October 2026

The owner requested resolution of reviews on every open PR, including drafts.
The GitHub inventory contained regular [#24](https://github.com/alohays/allagma/pull/24)
and draft [#25](https://github.com/alohays/allagma/pull/25), with no submitted
reviews, review threads, issue comments or pending review requests. The changes
were therefore reviewed directly by the implementing assistant. This is a
self-review, not an independent approval. Both PRs retain their existing states.

## Verified finding and repair

At `ac2086c551d4f0d98159c034746a7ffb7488135d`, `record_review.py` removed the
previous review references before validating the new configuration. Deleting
either the directly superseded r2 scientific record or its r1 ancestor still
allowed a new r3 review to return `pass`. The new record then pointed to an
unverifiable history. The reproduction used disposable copies of the completed
toy; no retained study or publication was changed.

The helper now verifies the path and digest of every superseded record before
creating an output directory. It also checks each record's kind and format.
It deliberately permits an old review's manuscript fingerprint to differ from
the current manuscript: changed prose is the reason to conduct a new review.
An intact history plus fresh supplied judgments still succeeds. Missing or
changed history fails before any new review file is written.

The regression covers deletion and byte changes at both r1 and r2, separately
for scientific and wording reviews. All eight cases failed against the original
implementation because the operation incorrectly succeeded. The repaired
helper rejects all eight and preserves the damaged fixture exactly as supplied.
Existing tests also verify successful prose revision, stale-input rejection,
new review creation and byte/mtime preservation of the first publication.

## Validation and scope

All 199 conformance tests pass, including the seven toy-paper tests. The
canonical documentation link check passes. The production build produces
44 pages with no broken local links, and all 18 desktop/mobile browser checks
pass, including the changed walkthrough. The original
[complete walkthrough receipt](toy-paper-walkthrough.md) remains a dated record
of its tested source commit; its manifests and rendered artifacts are unchanged.

The repair changes the study-owned review helper, its regression coverage and
the recovery instructions. It does not change manuscript content, toy science,
framework contracts, author attribution, resource ceilings or locked bundles.
No new TeX result, scientific review, native session or independent peer-review
claim is needed for this history-validation repair. The PR remains draft and
links #19 for closure only after owner review and merge.
