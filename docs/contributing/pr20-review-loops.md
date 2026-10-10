# PR #20: three review and implementation iterations

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

## Remaining iteration

Iteration 3 will review the combined change against current main and run the
complete required validation. This record is incomplete until that iteration
and the final pushed-head checks are recorded.
