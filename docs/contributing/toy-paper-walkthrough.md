# Toy-to-paper walkthrough validation

Issue [#19](https://github.com/alohays/allagma/issues/19) is the first available
task in the contributor overview inspected on 10 October 2026. The implementation
starts from main `174e200b508b07f022ba36233db54ca0b60e48e1`, independently of the
documentation-only queue refresh in #24. It adds a study-owned example and a
[literal walkthrough](../guides/toy-to-paper.md), without changing the toy
experiment, framework paper contract, frozen studies or existing publications.

The helper tests use a real completed offline toy and exercise preparation,
explicit review input, result locators, missing/stale reviews, altered evidence,
revision preservation and refusal of adapted/partial studies. Their review
inputs are labeled structural fixtures, not scientific judgments. The literal
walkthrough additionally requires reading the generated evidence and prose;
its review records identify the executor's self-review, not an independent peer.

## Measured scope

The complete walkthrough was executed at
`d4391da6664ec20c05c7fac91765fdbc4ba5cd1b` on macOS 26.6.2 arm64 with Python 3.11.6.
A fresh shallow, filtered, sparse clone used the directory `small checkout` and
the study path `work/toy paper study`. The standard first-study sparse set was
used, with `docs` added to read the guide. The exact shell blocks, exit codes,
environment, guide digest and numerical result are in
[walkthrough.json](evidence/toy-paper-walkthrough/walkthrough.json). The
[source manifest](evidence/toy-paper-walkthrough/source-files.json) binds the
helpers, editable inputs, guide and existing paper implementation to this run.

| Issue acceptance | Observed evidence |
| --- | --- |
| Literal small-checkout commands and paths with spaces | All eight shell blocks produced their expected exits: 0, 0, 2, 0, 0, 2, 0, 0. The guide lists every additional example input. |
| Actual values and limited claims | The summary digest is `cf60fe8211bf355c9a8f29b731119dbbf207d3943df9c936214b336b6f8bd8da`. The configured JSON pointers resolve the paired increase 0.06510417 and interval [0.03985104, 0.09035729]; the average claim uses the generated claim ledger's text. |
| Honest reference coverage and explicit authors | `reference check --require-review` passes with zero external records and explicit limited categories. The invocation explicitly supplies anonymous attribution; the PDF says “Anonymous draft.” |
| Scientific/prose review and freshness | The unreviewed check fails as intended. The executor read the derivation, sections, original report and claims, then recomputed the paired mean/interval from raw samples. Scoped judgments produce a passing r1 check. A new discussion file/config makes that review stale; rereading and retaining r2 judgments restores a pass. |
| Offline base and separate actual TeX route | The base Python commands use only the standard library. Optional `paper build` passes with installed TeX Live 2024, including its internal archive rebuild. The literal recipient invocation of the extracted `anc/build.py` also passes. Both rendered PDF pages were inspected. |
| Immutable prior science and finite budget | All 755 pre-publication study files retain bytes and nanosecond mtimes. All 17 first-publication/review files survive r2 unchanged. The toy has 26 successes, one failed attempt, one interruption and a passing 521-reference audit, under the unchanged 28-attempt/60-second limits. |
| Discoverable guide and documentation rendering | First-study and paper guides link the walkthrough; site navigation includes it. Canonical link, production-site and desktop/mobile browser checks pass. |

[Preservation evidence](evidence/toy-paper-walkthrough/preservation.json) records
the before/after comparisons. The original report configuration still says
`output: report`; only a new publication subtree is added. The implementation
does not change frozen study/publication data, framework runtime, adapters,
contracts, methods, resource limits or model configuration.

## Review and visual evidence

The [retained judgments](evidence/toy-paper-walkthrough/reviews.json) are the
Codex executor's self-review. The r1 fingerprint is
`4c4a6656bfb2234bbfa443b040ec59a29a66597e767448f85b1acb19e1aaa1e8`;
r2 is `eedec30208d0d39090c00b0c9b96a37f4204cdf2487d2e50863568ac0782d34b`.
The reviews preserve the normal-approximation limit, 24-seed unit, excluded
pilots/unsuccessful attempts and counterexamples 104, 108, 118 and 121.
They are distinct from fixture reviews and independent scientific peer review.

The [build/visual receipt](evidence/toy-paper-walkthrough/build.json) records
the two-page PDF, verified packaged entrypoint, network-denied Seatbelt builds
and explicit recipient rebuild. The source set is 121,476 bytes; this small
example does not exercise or resolve #22's 25 MiB admission boundary. The PDF's
SHA-256 is `fb3e4488c53067a702a37c913b2b4f36f90cfd23cae0e8370b086232a470c178`.
In this environment all three builds produced matching PDF bytes; that is an
observation, not a cross-platform reproducibility promise.

Inspect [paper page 1](evidence/toy-paper-walkthrough/paper-page-1.png) and
[page 2](evidence/toy-paper-walkthrough/paper-page-2.png). Both have legible text,
values and table cells, intact page numbering and no clipping/overlap. The
References section explains the absent external bibliography. The
[desktop guide](evidence/toy-paper-walkthrough/guide-desktop.png),
[review instructions](evidence/toy-paper-walkthrough/guide-review.png) and
[mobile guide](evidence/toy-paper-walkthrough/guide-mobile.png) retain the
rendered documentation views.

## Validation and boundaries

Local `python3 -B -m unittest discover -s conformance -v` passes all 198 tests,
including six new real-toy helper tests. `npm run build` generates 44 pages;
`npm test` passes 18 desktop/mobile browser tests, including the new page in
the all-pages viewport/script check. The branch's
[Linux CI](https://github.com/alohays/allagma/actions/runs/38035281153) passes
the required selector and full I1–I5/toy acceptance on the same implementation
commit. [Check receipts](evidence/toy-paper-walkthrough/checks.json) record
the exact commands and current documentation counts.

No external bibliography, online acquisition, native model session, scientific
budget expansion, GPU, arXiv submission or release is part of this change. This
macOS receipt does not close #7's Linux/Python 3.13 qualification or #23's
standalone diagnostics enhancement. The new draft PR links #19 for closure
after review and merge; opening the draft does not itself close the issue.
