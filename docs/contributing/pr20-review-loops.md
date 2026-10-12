# PR #20: three review and implementation iterations

The owner subsequently merged this work as `174e200` and closed #18. This
document retains the pre-merge review/implementation record; the
[current triage](post-pr20-triage.md) tracks subsequent issues and claims.

The owner requested review of every currently open PR followed by three
review/implementation iterations. On 10 October 2026, the open set contained
only [#20](https://github.com/alohays/allagma/pull/20), initially at
`b1674542b516b2c9c28ee5562c5a1cecbd926196`. This is an agent-assisted maintainer
review, not independent human approval. The PR author and authenticated reviewer
are the same account, so GitHub assessments use COMMENT reviews.

## Initial review

Read all nine changed files and their contracts, callers, Git workflow and lock
implementation. Seven record/locking tests and 15 tooling tests pass. The record
root/type guard preserves valid input and controlled errors. A separate deeply
nested JSON probe also exits 2 without a traceback or file writes. No blocking
record-admission or process-lock defect was reproduced.

Real Git histories exposed two CI-selection findings that mocked path lists
did not exercise. Quoted Unicode/control-character paths were not recognized,
and a detected rename into `docs/` hid the removal of its adapter source.
An invalid base such as `--base=--quiet` was interpreted as a Git option and
produced an empty successful diff. These cases returned success with no behavior
suite selected. The initial review was submitted against the exact starting head.

## Iteration 1: correct Git change admission

Reproduced the findings with three new tests using real temporary Git
repositories. All seven negative subcases fail on the initial selector: four
quoted-path variants, one rename and two invalid base values.

The selector now reads NUL-delimited paths, disables rename detection to retain
both source removal and destination addition, and ends option parsing before
the revisions. Real-Git tests preserve the actual path transport; only execution
of the selected Python suites is intercepted. Existing routing tests retain
their independent scope and failure assertions.

All 11 selector tests and seven record/locking tests pass after the change.
Runtime record semantics, schemas and the lock implementation are unchanged.

## Iteration 2: recheck regressions and bound invalid-type diagnostics

Reviewed `268761c266b86891fcaeb0599fb251faa7ac2732`. Independently removing each
of the three Git protections in memory makes its corresponding regression fail:
four path cases, one rename case and two base-argument cases. Repository source
remains unchanged by the mutation probes. The earlier selector findings are
resolved, including mixed changes and failure propagation.

A deeper API probe found a remaining malformed-record failure. Formatting an
invalid list/object `record_type` could raise `RecursionError` while producing
the rejection message. Both nested-container cases reproduce that failure.
The validator now rejects non-string types with a bounded diagnostic before
the known-string membership check. This does not change valid records, schemas
or scientific results. The new API regression fails before the fix and passes
after it, alongside the existing positive, malformed-file and lock cases.

## Iteration 3: integration and actual failure enforcement

Re-reviewed `6ccb408560c78b137bcac2050185434f30559e1f` and integrated current main
`cc667a5` in merge commit `205db50`, preserving both goal histories. No additional
production-code defect was found in the revised validator, selector or lock
path. The review checked the related [issue #18](https://github.com/alohays/allagma/issues/18)
against the implementation rather than relying only on the existing green tests.

One acceptance item needed stronger evidence: the original failure-propagation
test simulated a failed process. The new disposable-checkout regression invokes
the actual selector, Git diff and unittest process. An adapter-only change
selects a deliberately failing `conformance.test_reference_assets` fixture;
the selector exits 1 and retains the expected assertion in captured stderr.
Checking that assertion rules out a misleading pass caused by an unrelated
import or setup failure. The same enforcement test rejects the original main
selector. It adds no failure to the real conformance suite.

All 19 tooling tests pass. Fresh full acceptance passes **192 conformance tests
and I1–I5**, with 24 confirmation replicates, 26 successful attempts, one
deliberate failure, one interruption and a clean 521-reference toy audit. The
catalog check passes all 23 entries. The integrated documentation builds 43
pages with 2,851 local links/assets and passes all 18 desktop/mobile browser
tests. The scope remains offline contract, process and artifact behavior;
native model or scientific-quality qualification is not extended.

## Final evidence and scope

The [evidence manifest](evidence/pr20-review-loops/manifest.json) binds the
before/after reproductions, mutation results, actual failing-test output,
validation and preservation comparison. Detailed logs and the full acceptance
workspace remain in ignored `work/pr20-review-loops/`. Current-head hosted
results are available through [PR #20's checks](https://github.com/alohays/allagma/pull/20/checks),
including the actual required selector command and separate portable-paper job.

The fixes and evidence are committed in separate iteration increments and
pushed to the existing PR branch. Existing studies, frozen evaluations,
schemas, methods, adapters, media and project model settings are unchanged by
this review pass. No model session, new scientific training, resource expansion,
release or PR merge is part of this task. The earlier review findings and
original implementation history remain intact.
