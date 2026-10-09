# Pull request review — 9 October 2026

The owner requested review of every open PR, authorized merging #1 if ready,
and asked for the other PRs to be fixed and made regular. Four PRs were open.
All changed files, their callers/contracts, issue acceptance criteria and tests
were inspected. Three reproducible findings were posted as inline GitHub
reviews, fixed in separate commits, retested and resolved with linked replies.

## Decisions and evidence

| PR | Reviewed implementation | Decision | Validation |
| --- | --- | --- | --- |
| [#1: docs dependencies](https://github.com/alohays/allagma/pull/1) | `0e612e14c139a5883ddb6fff6595247e15837a12` | [Approved](https://github.com/alohays/allagma/pull/1#pullrequestreview-5470551485) and merged as `5cf169035228b93327c8a76070a5a90b90f95935` | Fresh install/audit (0 vulnerabilities), 39-page/2,418-link build, 18 browser tests; merged-tree CI passes |
| [#10: adapted toy](https://github.com/alohays/allagma/pull/10) | `a8dfa9042ffc10714b64b0a0cba8759471bcfa40` | Regular PR, ready for a merge decision | 118 tests; complete literal CLI workflow; 39 pages/2,426 links; [docs](https://github.com/alohays/allagma/actions/runs/37936446355) and [conformance/acceptance](https://github.com/alohays/allagma/actions/runs/37936439323) pass |
| [#11: prerequisites](https://github.com/alohays/allagma/pull/11) | `726bb4e0dae0c919f38085b07bbb0c3c3e459352` | Regular PR, ready for a merge decision | 121 tests; malformed-data CLI and no-write/no-execution checks; 39 pages/2,422 links; [docs](https://github.com/alohays/allagma/actions/runs/37936671940) and [conformance/acceptance](https://github.com/alohays/allagma/actions/runs/37936662020) pass |
| [#12: evidence inspector](https://github.com/alohays/allagma/pull/12) | `2ea69f1753d4ecb945d2ab880f11639574110e6f` | Regular PR, ready for a merge decision | 121 tests; full 521-reference toy graph; 39 pages/2,425 links; [docs](https://github.com/alohays/allagma/actions/runs/37936973182) and [conformance/acceptance](https://github.com/alohays/allagma/actions/runs/37936965571) pass |

Every feature branch includes main after the dependency merge. Feature code
remains outside main; the three PRs have no dependency on one another. Hosted
Documentation checks include all 18 desktop/mobile browser tests. The duplicate
acceptance job is intentionally skipped for pull-request events; the push job
performs full acceptance.

## Findings and repairs

- **#10, P2 — scientific setting precision.** Preparing bias `0.123456789`
  produced that raw/summary value but described `0.123457` in the question,
  protocol, claim scope and manuscript. All 26 runs and the deterministic audit
  still passed. Scientific setting text now preserves the accepted numeric
  value. The new full-workflow test checks every reporting stage; boundary
  preparation covers -1, 0 and 1 with the unchanged finite plan.
  [Finding and fix](https://github.com/alohays/allagma/pull/10#discussion_r4230537178).
- **#11, P2 — malformed prerequisite crash.** A lock containing `[]` raised
  `AttributeError`, suppressing JSON and later checks. Wrong shapes and excessive
  nesting now produce individual failed checks with remedies. An actual CLI
  test corrupts catalog metadata, lock and ownership together and verifies
  exit 1, complete independent diagnostics, sanitized output, and unchanged
  content/mtimes. [Finding and fix](https://github.com/alohays/allagma/pull/11#discussion_r4230557439).
- **#12, P2 — lost sibling diagnostics.** One malformed member in a nonempty
  record list caused an immediate entry failure, hiding missing evidence in
  valid siblings. The verifier now reports each bad member at its location
  and continues valid siblings. An actual CLI test verifies all findings,
  successful-record coverage, shared-reference deduplication and no writes.
  [Finding and fix](https://github.com/alohays/allagma/pull/12#discussion_r4230574714).

## Architecture and file review

The dependency diff changes only the docs manifest/lockfile. Pins, registry
URLs, integrity hashes and the matching axe-core version agree. The upstream
MDX escaping correction works with the current page components. Accessibility
checks pass without removing rules. The Python runtime remains dependency-free.

For #10, `prepare.py` owns scientific configuration and prospective setup in the
example; `analyze.py` rejects mixed settings; `write.py` carries measured settings
into claims and manuscript. The adaptation tests and both guides cover the
prepare/inspect/execute boundary, input refusal, source lineage and finite plan.
No framework record schema or existing campaign is rewritten.

For #11, CLI dispatch and exit handling remain additive. `diagnostics.py` reuses
the existing catalog, lock and ownership checks instead of defining competing
freshness rules. The tests exercise both read-only inspection and failure
isolation; CLI/troubleshooting docs distinguish prerequisites from qualification.
Native checks inspect availability without invoking a runner or reading account
or model configuration.

For #12, CLI dispatch avoids campaign/helper execution. `evidence.py` uses path
confinement, regular-file checks, bounded reads, digests and explicit JSON graph
traversal. The `files.py` decoder extraction preserves duplicate/non-finite
rejection for existing readers. Tests cover missing/changed data, path traversal,
symlinks, malformed records, ceilings and graph deduplication; CLI/reproduction
docs state the pass's exact scope. An entry digest is not an authenticated root;
quiescent input is required, and inspection is not an atomic snapshot.

## Combined validation

The three reviewed implementations merge without conflicts in local integration
commit `413c184240072468e1b7156a6ddd43181c6154b9`. Its runtime/source inventory is
`sha256:b43430691203946e041ab4815af4118828b6e4cbb3cc5643ae3a80cc9f08a9b9`.

`python3 -m allagma acceptance --output work/pr-review/integration-acceptance`
passes all **134 conformance tests and I1–I5**. The default toy retains 26
successful attempts, one deliberate failure, one interruption and a passing
521-reference audit. The combined docs build has 39 pages and 2,437 valid local
links/assets; all 18 browser tests pass.

A separate actual CLI workflow prepares bias `0.123456789`, runs `doctor`,
starts and executes the 26-run campaign, analyzes/audits it, then invokes
`verify-evidence`. The final inspector passes 504 references in 505 reads and
leaves all study bytes/mtimes unchanged. The original 521-reference default toy
includes additional deliberate failure/interruption/context records.

Compact receipts and logs are retained in [review evidence](evidence/pr-review/manifest.json).
Full generated acceptance/study directories remain in ignored `work/pr-review/`;
they are fresh fixtures, not edits to previously frozen evidence. GitHub CI
artifacts provide the independently hosted branch runs.

## Limits and ownership

These are agent-assisted maintainer reviews, not independent human approvals.
GitHub permits formal approval of Dependabot #1 but prohibits approving or
requesting changes on the same account's own PRs. The feature findings and final
assessments therefore use submitted COMMENT reviews with inline threads and
resolution replies. No unresolved blocking finding remains in the reviewed
implementation. Merge and release decisions for #10–#12 remain with the owner.

No native model session, GPU training, resource increase, model override,
history rewrite, frozen-bundle edit or release publication occurred. Inspection
tests establish their stated contract/digest/prerequisite coverage; they do not
establish scientific truth or additional host qualification. Historical audio
clearance remains tracked separately in [#8](https://github.com/alohays/allagma/issues/8).
