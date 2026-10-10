# Issue refresh after PR #20 — 10 October 2026

Inspected main `174e200b508b07f022ba36233db54ca0b60e48e1`, every issue's current
state, recent PRs, confirmed claims and the preceding triage. PR #20 is merged
and #18 is closed. Main's conformance, documentation, portable-paper and Pages
checks pass. The earlier [three-iteration review](pr20-review-loops.md) records
192 conformance tests, 19 tooling tests and I1–I5; those checks do not cover
every possible input boundary.

Exactly two new issues were opened. Both have probes on this main revision, need
no new model or scientific workload, and have bounded offline acceptance tests.

| New issue | Observed problem | Immediate value |
| --- | --- | --- |
| [#22: paper-source size admission](https://github.com/alohays/allagma/issues/22) | Assembly accepts 26,214,400 bytes before adding 3,829 bytes of provenance. Its own archive reader then rejects the 26,218,229-byte result. An oversized evidence file is copied in full before refusal. | Make the newly exposed portable-paper writer and reader agree on their source budget, with early admission and preserved failed revisions. |
| [#23: standalone bundle diagnostics](https://github.com/alohays/allagma/issues/23) | The bundled helper verifies a healthy study and runs a pilot, but `doctor` exits 1 solely because central toy examples are not inside the bundle. | Give recipients of a self-contained study an accurate read-only report and remedies that preserve immutable bundles. |

The [runnable boundary probe](evidence/post-pr20-triage/probe_boundaries.py)
uses temporary fixtures. From a checkout containing this record, run:

```sh
python3 -B docs/contributing/evidence/post-pr20-triage/probe_boundaries.py
```

The paper portion uses explicitly labeled conformance data and fixture-only
reviews; it neither compiles TeX nor establishes a scientific result. The
diagnostic control runs one bounded known-answer pilot, not a native session.
Neither probe alters existing studies, publication records or frozen bundles.
The [retained paper measurements](evidence/post-pr20-triage/paper-limit-probe.json)
and [diagnostic control](evidence/post-pr20-triage/bundle-doctor-control.json)
record the original observations. These are maintainer-observed gaps, not
invented external incidents or independent scientific review.

#22 is a confirmed packaging defect. #23 is a portability enhancement: the
current CLI documentation and original #2 acceptance cover source-checkout
diagnostics. Its probe establishes the need for a separate standalone scope;
it does not reopen or invalidate the completed source-checkout feature.

## Existing work and cleanup

- #18 remains closed through #20. Its stale `status: owner review` label was
  removed, its introduction now records completion, and its verified acceptance
  items are checked. The original reproduction remains below the new status.
- #2–#5 remain closed and correctly labeled. No completed work was reopened or
  assigned for duplicate implementation.
- #6 remains in progress with `codedbypraneetha`; its confirmed claim, comments,
  accessibility scope and existing labels are preserved.
- #7 remains available because the literal Linux/Python 3.13 tutorial receipt
  is still missing. Python 3.11/3.12 CI does not establish that qualification.
- #19 remains the first available onboarding task. Main still lacks the small
  runnable toy-to-paper walkthrough. It can proceed alongside the two repairs;
  its evidence, attribution and review requirements were retained.
- #8 remains blocked, assigned to the maintainer and outside the engineering
  milestone. Successful code checks and current licensed media do not clear
  historical audio rights. The full-history decision is preserved.
- The pinned overview #9 and milestone now show #19, #22, #23 and #7 as the
  available work. Only #22 and #23 are new; both are unassigned with
  `help wanted` and `status: available`, without a `good first issue` label.
  #22 has `bug`; #23 has `enhancement`.

The roadmap, starter list and community/owner guidance are updated in the
documentation cleanup branch. Historical review and triage records retain
their original evidence, with pointers to this current snapshot. The selected
issues are published; their implementation remains future contributor work.

## Selection and limits

The existing #19 onboarding work retains first priority. The two new issues
address a source-budget inconsistency and a missing standalone diagnostic scope
alongside features already on main. They do not duplicate the repaired #14 findings,
the completed #18 selector work, or the existing #7 qualification task.

No extra issue was added merely because there is no formal GitHub release.
The project remains a source release candidate with a separate owner release
decision. New providers, larger evaluations, hosting services and additional
test infrastructure were deferred. They would expand scope or require new
cost/owner decisions without resolving these immediate gaps.

The [evidence manifest](evidence/post-pr20-triage/manifest.json) binds the issue
snapshots, current-main checks, probes and preservation comparison. No framework,
adapter, method, schema, scientific source or model setting is changed by this
triage. Repository documentation follows the protected PR workflow; this task
does not merge feature work, rewrite history or publish a release.
