# Essential test coverage audit — 10 October 2026

Audited `main` at `f235f1868eec7f6cc9518e5d59053a236b876358`.
The existing 184 conformance tests passed. They already exercise complete toy
studies, interrupted attempts, resource ceilings, immutable evidence, updates,
rollback, references and paper assembly. The additions address three missing
boundaries with direct consequences for contributors and retained studies.

| Boundary | Missing evidence and resulting change |
| --- | --- |
| [Record admission](../../conformance/test_record_validation.py) | Non-object JSON and list/object `record_type` values raised uncaught exceptions. They now produce `AllagmaError`; the CLI exits 2 with a diagnostic and preserves bytes and mtimes. Positive cases and negative attempt/claim invariants guard against accepting incomplete evidence or rejecting every record. |
| [Study mutation lock](../../conformance/test_study_locking.py) | Existing crash tests did not prove exclusion between live processes. New subprocess tests cover refused campaign start/run and update/migration planning, progress in another study, release after normal exit, and kernel release after a killed owner without deleting its lock file. No locking implementation change was needed. |
| [Required CI selection](../../tools/tests/test_check_changed.py) | Adapter-only changes omitted their own regression suites; profile/policy changes and evaluation fixtures also missed relevant behavior checks. Runtime and workflow changes now run all offline conformance suites. Context/evaluation changes retain comparison checks, mixed changes retain both scopes, an unreadable base includes tooling checks, and selected-test failures propagate. |

The initial record tests failed before the type checks were added: seven CLI cases
returned tracebacks, and eight API cases raised the wrong exception type. The
initial eight CI-selection tests produce twelve failing subcases against the
original selector. Both suites pass after their fixes. Removing `flock` only
in a disposable source copy makes the new contention test fail; the unmodified
implementation passes. This checks that the concurrency test detects loss of
exclusion instead of relying on scheduling delays.

`main` advanced to `14c2fba` during the work. Its documentation-only changes
were merged with both goal records preserved; runtime and test contents were
unchanged by that integration.

## Validation

On macOS with Python 3.11.6, the full acceptance command passed all **191
conformance tests without skips** and I1–I5. The generic toy retained 26
successful attempts, one deliberate failure and one interruption, with all 24
confirmation replicates and a passing evidence audit. The catalog check passed
all 23 entries; all 15 tooling tests passed (eight selection tests plus seven
existing release-boundary tests).

```sh
python3 -m allagma check
python3 -m unittest conformance.test_record_validation conformance.test_study_locking -v
python3 -m unittest discover -s tools/tests -v
python3 -m allagma acceptance --output work/essential-coverage-acceptance
python3 tools/check_docs.py
```

Use a fresh acceptance destination. The command retains per-test outcomes,
source inventories, complete toy artifacts and an acceptance report. The PR's
Conformance workflow retains the equivalent Linux acceptance artifact, and its
`targeted` job exercises the actual change selector against the Git diff.

These checks add no dependencies, schema fields, scientific workloads or native
model qualification. Valid records keep their existing behavior. Malformed
records receive a controlled validation error; no data migration is required.
The selector tests intercept Git/test commands to inspect routing and exit
codes; actual conformance execution is verified separately by acceptance and CI.

## Subsequent review iterations

The [three-iteration review](pr20-review-loops.md) adds real-Git path/base tests,
a nested invalid-type API regression, and an actual failing selected test in a
disposable checkout. It repairs quoted-path, rename-removal and base-argument
selection gaps, and prevents invalid record-type diagnostics from raising a
secondary recursion error. The final local totals are 192 conformance tests and
19 tooling tests, with I1–I5 and the complete toy workflow passing. Earlier
counts above describe the initial implementation.
