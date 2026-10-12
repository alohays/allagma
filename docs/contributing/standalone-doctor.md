# Standalone study diagnostics

Issue [#23](https://github.com/alohays/allagma/issues/23) was selected alongside
[#22](https://github.com/alohays/allagma/issues/22) as the next highest-priority
available engineering work on 12 October 2026. A correctly exported study could
verify and run, but its helper's `doctor` required central toy files that are
intentionally absent from the bundle.

Diagnostics now distinguish source checkouts from selected bundle catalogs.
The generated catalog's existing composition marker identifies a relocated
bundle; its normal `.allagma/bundles/` location also identifies one when the
registry is damaged. Absence of toy files alone never selects bundle scope.
Source-checkout toy checks remain unchanged.

The report retains version 1 and its pass/fail check statuses. The added
`distribution` and `excluded_checks` fields explicitly report the omitted
central-example check; omission is not described as a pass. Catalog failures
in bundles have recovery guidance that preserves frozen content. See the
[CLI commands](../cli.md#exit-status-and-costs) and
[troubleshooting guide](../guides/troubleshooting.md).

## Acceptance evidence

| Requirement | Passing evidence |
| --- | --- |
| Actual standalone helper outside the checkout | A regression creates an exported toy with spaces in its source and study paths, moves the original checkout away, and runs the actual bundled `tools/allagma.py` from a separate directory. It exits 0 with catalog, study-lock and generated-file checks passing and the central toy check explicitly excluded. |
| Source-checkout route | The same regression invokes the source helper before moving it. Its report includes a passing central toy check. Existing missing-toy and missing-catalog tests still fail independently. |
| Required failures preserved | Disposable copies separately remove a catalog resource, corrupt the registry, corrupt the lock and edit `ALLAGMA.md`. Each returns the expected failed checks without preventing unrelated checks; generated-file edits are preserved. |
| Recovery respects immutable content | Bundle catalog remedies say to recover an intact exported copy or use the update workflow from a source checkout, and explicitly forbid inserting files into or rewriting the bundle. Historical helpers remain unchanged; the current central helper can inspect their source directory. |
| Read-only behavior | Actual helper invocations preserve every study file's bytes and all descendant modification times, including on failure. A supplied native executable is found without running its sentinel. The relocated-catalog test rejects subprocess/network/host lookup and any file read outside the bundle, including ambient credential files. |
| Scope and portability | A relocated catalog works without a study argument. Native prerequisite checks remain independent and retain their qualification disclaimer. No study protocol is executed or scientifically validated. |

The [baseline reproduction](evidence/standalone-doctor/before.json) uses the
original diagnostics at main `174e200` in a newly exported helper: `verify`
exits 0 but `doctor` exits 1 solely for `toy-resources`, preserving bytes and
mtimes. The [initial implementation reports](evidence/standalone-doctor/after.json) show source,
bundle and current-central-helper inspection routes all passing. The
[diagnostic tests](evidence/standalone-doctor/diagnostics.log) and
[validation receipt](evidence/standalone-doctor/validation.json) record the
initial 11 focused tests and 195 passing full conformance tests, environment, commands and
implementation digests. Catalog and canonical documentation checks also pass.

This is agent-assisted implementation and self-review. Fixtures do not qualify
a native host or scientific result. Existing studies, bundles, evaluations,
media, history and model configuration are unchanged. This independent PR leaves
the paper-source repair to #26 and remains unmerged for review.

## Self-audit before handoff — 12 October 2026

A second audit of PR #27 at `9a21fce` found two untested faults. A relocated
bundle with a missing, malformed or wrong-shape registry was treated as a
source checkout, producing an inappropriate central-toy recovery hint. A
selected catalog with an empty module mapping passed after checking zero
modules. Both are reproduced by actual helper invocations in disposable exports.

The repaired diagnostic reports unknown distribution when a relocated catalog
cannot identify it, fails the catalog check, and explicitly leaves the central
toy check unassessed. Its recovery hint forbids adding files to a frozen bundle.
Empty module mappings fail admission. Normal source-checkout and bundle scopes
retain their checks and read-only guarantees.

The [before log](evidence/standalone-doctor/self-audit/before.log) records four
expected failing assertions across two tests on the reviewed head. The
[after log](evidence/standalone-doctor/self-audit/after.log) passes all 13
diagnostic tests, including bytes/mtime preservation for the new faults. Full
offline conformance passes 197 tests. The
[audit receipt](evidence/standalone-doctor/self-audit/validation.json) records
commands, environment and repaired code digests. Earlier receipts above remain
historical evidence rather than being overwritten. GitHub had no external
reviews or unresolved conversations at this audit; this is same-assistant
self-review, not independent approval. The PR remains regular and unmerged.
