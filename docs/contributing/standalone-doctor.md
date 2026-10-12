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
mtimes. The [current reports](evidence/standalone-doctor/after.json) show source,
bundle and current-central-helper inspection routes all passing. The
[diagnostic tests](evidence/standalone-doctor/diagnostics.log) and
[validation receipt](evidence/standalone-doctor/validation.json) record the
11 focused tests, 195 passing full conformance tests, environment, commands and
implementation digests. Catalog and canonical documentation checks also pass.

This is agent-assisted implementation and self-review. Fixtures do not qualify
a native host or scientific result. Existing studies, bundles, evaluations,
media, history and model configuration are unchanged. This independent PR leaves
the paper-source repair to #26 and remains unmerged for review.
