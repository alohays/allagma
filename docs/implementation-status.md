# Allagma v0.2 implementation

Target: the four adopted specifications in `docs/specification/`, originally
dated 6 October 2026. Noemetric's scientific experiments are a separate study.

The [post-delivery self-audit](audit/README.md) found gaps beyond the original
tests. Corrections are undergoing fresh qualification. The receipts below
describe the original delivered source until replaced by the completed audit.

| Milestone | Required demonstration | Implementation status |
| --- | --- | --- |
| I1 | Same contracts and artifacts through generic, Codex and Claude Code entrypoints; no native hooks or subagents | Passed |
| I2 | Swap context method, reviewer adapter and recipe without rewriting other modules | Passed |
| I3 | One-module contribution, targeted offline conformance, lifecycle and ownership | Passed |
| I4 | Exact bundles, configuration provenance, update reconciliation, migration, rollback and historical resume | Passed |
| I5 | Actual toy raw data, recomputation, claims, manuscript, success/failure/interruption | Passed |

Validated on 7 October 2026 (Asia/Seoul). The
[acceptance receipt](evidence/acceptance.json) reports **51 passing conformance
tests with no skips** and all five executable acceptance scenarios passing.
The generic toy campaign retained 26 successes, one failure and one interruption;
its deterministic audit verified **411 distinct evidence references**. The
replacement, partial-budget, lifecycle and migration cases have their own
retained artifacts.

[Independent validation](evidence/external-validation.json) checked eight JSON
schemas, 629 record occurrences and 293 skill files using jsonschema, PyYAML and
the Skill Creator validator. This is structural/packaging assurance. The
[archive reproduction receipt](evidence/archive-reproduction.json) confirms that
the retained evidence was extracted elsewhere and re-audited successfully.

The [complete evidence archive](evidence/acceptance.tar.gz) contains 5,169 files;
its inventory and digest are in [archive-manifest.json](evidence/archive-manifest.json).
See [the acceptance guide](acceptance.md) for reproduction commands and scope.

The accepted distributable source revision is
`sha256:8a7d9cac866cf864f02446cb56a83cd40469629d7698cdefb443122a2ce8270b`.
English contributor guides, governance, ownership, release/migration notes,
issue/PR templates and targeted CI are present. The requested commit-and-push
instruction is recorded in [GOAL.md](../GOAL.md); the delivery target is
`origin/main`.

The default kit uses Python 3.11+ without paid APIs, GPU or third-party runtime
dependencies. JSON-compatible YAML is the on-disk configuration encoding.
Content-addressed local source snapshots identify unpublished releases; no
public release, publication, or real-model quality claim is implied.

Native Codex and Claude Code packaging is format/contract checked. Real native
activation, hosted-model behavior and independent scientific review remain
separate qualifications, as required by the support-scope distinction in the
specification. Noemetric experiments remain outside this implementation goal.
