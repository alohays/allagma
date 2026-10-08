# Allagma v0.2 implementation and audit

The current [0.3.0rc2 release](releases/0.3.0rc2.md) requalifies I1–I5 against
the corrected source: [113 conformance tests and all five scenarios pass](v0.3/evidence/rc2/acceptance/acceptance.json),
including the complete toy and 521-reference audit. Its
[5,944-file archive](v0.3/evidence/rc2/acceptance/archive-manifest.json),
[relocated replay](v0.3/evidence/rc2/archive-reproduction.json) and
[independent toy calculation](v0.3/evidence/rc2/independent-toy.json) pass.
The accepted distributable source is
`sha256:a7a67e09548e40442f2ff72ba63898f66e02368046132a183588ebebdbc1a196`.
The [v0.3 ledger](v0.3/requirements.md) and [comparison](v0.3/COMPARISON.md)
cover the subsequent three-task native scope. The evidence below is the retained
7 October v0.2 audit, not a claim that old receipts describe the new source.

Target: the four adopted specifications in `docs/specification/`, originally
dated 6 October 2026. Noemetric's scientific experiments are a separate study.

The [post-delivery self-audit](audit/README.md) found and corrected 13 groups of
defects or missing requirements. The [requirement map](audit/requirements.md)
identifies the evidence and limits for each obligation. Earlier passing tests
did not cover all of these cases; their original evidence remains preserved.

| Milestone | Required demonstration | Audited status |
| --- | --- | --- |
| I1 | Same contracts and artifacts through generic, Codex and Claude Code entrypoints; no native hooks or subagents | Passed within the declared packaging scope |
| I2 | Swap context method, reviewer adapter and recipe without rewriting other modules | Passed |
| I3 | One-module contribution, targeted offline conformance, lifecycle and ownership | Passed |
| I4 | Exact bundles, configuration provenance, update reconciliation, migration, rollback and historical resume | Passed |
| I5 | Actual toy raw data, recomputation, sensitivity, figure, claims, manuscript, success/failure/interruption | Passed |

Validated on 7 October 2026 (Asia/Seoul). The
[fresh acceptance receipt](audit/evidence/acceptance.json) records **75 passing
conformance tests with no skips** and all five executable acceptance scenarios.
The generic toy retains 26 successes, one failure and one interruption. Its
deterministic audit verifies **521 distinct evidence references**. A separate
limited-budget study produces an explicitly partial manuscript.

[Independent schema/packaging validation](audit/evidence/external-validation.json)
checks eight schemas, 643 record occurrences and 290 skill files. RFC 3339
timestamp validation is installed. A separate
[1,557-case differential check](audit/evidence/contract-differential.json) agrees
with the independent JSON Schema implementation.

The [independent scientific calculation](audit/evidence/independent-science.json)
uses rational arithmetic without importing the study implementation. It verifies
eligibility, primary/sensitivity tables, figure data, claims and manuscript
numbers. The original mean MSE difference remains `25/384`. All 24
leave-one-seed-out means are positive, ranging from `0.06182065` to `0.07269022`.
The [SVG figure](audit/paired-differences.svg) was also visually inspected.

The [complete evidence archive](audit/evidence/acceptance.tar.gz) contains
**5,839 files**. Its [inventory and digest](audit/evidence/archive-manifest.json)
cover the exact bundles, raw attempts, comparisons and update/migration cases.
[Archive reproduction](audit/evidence/archive-reproduction.json) passed after
extraction elsewhere using the pinned helper, with the new review retained.
The [original evidence](evidence/README.md) describes the earlier source only.

Accepted distributable source revision:
`sha256:fe61419ac78231ab0fcc0d70f77714f6946cbdb1bd72ce3a360313850855e100`.
Study examples and conformance sources have separate captured inventories.
English technical documentation, contribution materials and the
[commit-and-push instruction](../GOAL.md) remain in the repository.

The default kit uses Python 3.11+ on POSIX, without paid APIs, GPU or third-party
Python runtime dependencies. Historical
bundles keep their old helpers; adopt the corrected source explicitly for new
campaigns. Native Codex/Claude activation, model quality and independent
scientific peer review were unperformed at that audit checkpoint.

## Subsequent native Codex qualification

The [weight EMA diffusion study](../studies/ema-2d-diffusion/README.md) adds real
native Codex evidence on 8 October 2026. Six distinct CLI 0.160.1 sessions
cover interruption, fresh-session recovery, pilots, confirmation, analysis and
reporting revision. The inherited model was `gpt-6-astra` with no project model
pin. The exact audited framework source above remains the study's frozen
source; PyTorch and scientific dependencies belong only to the separate study.

Four pilot and ten confirmation trajectories completed on MPS. Every trajectory
retains raw and EMA0.99/EMA0.999 checkpoints at 5,000 and 10,000 updates. One
100-update pilot interruption remains excluded. The deterministic audit and
independent scientific verifiers recompute results and reproduce selected
saved-weight samples. A global 1,800-second ceiling counts scientific checks,
retries, execution, analysis and recomputation. See the
[host qualification report](../studies/ema-2d-diffusion/HOST-QUALIFICATION.md)
and [machine-checkable receipt](../studies/ema-2d-diffusion/evidence/host-qualification.json)
for actual cost, tested methods and limits. Claude activation, general model
research quality and independent scientific peer review remain unqualified.
