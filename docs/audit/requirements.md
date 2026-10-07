# Requirement-by-requirement audit map

The source requirements are the four owner-supplied specifications in
`docs/specification/`. [Digest checks](specification-provenance.json) confirm
that the retained copies still match the originals in the vault. The following
map preserves the original scope. It does not infer native host qualification,
scientific novelty or independent review from a passing fixture.

The [fresh acceptance receipt](evidence/acceptance.json),
[test receipt](evidence/conformance.json), and
[complete artifact inventory](evidence/archive-manifest.json) identify the
qualified bytes and the retained files. Paths under an acceptance tree below
refer to that archive. Test names refer to the committed `conformance/` sources.

## I1–I5 and the six version-protocol scenarios

| Requirement | Authoritative evidence and inspected behavior |
| --- | --- |
| I1: canonical methods, default recipe, three delivery paths | Catalog checks, external skill/YAML validation, `generic`, `codex`, and `claude-code` walkthroughs resolve one bundle and equal numerical output. Native wrappers are inspected routing instructions; the actual process execution is generic. |
| I2: replace context, reviewer and recipe independently | Three distinct replacement walkthroughs finish; common module revisions remain equal. Context and reviewer examples execute from their selected paths; replication performs two reanalyses. A07 additionally removes unused defaults from the closure. |
| I3: change one module offline | `test_a_contributor_can_add_and_check_one_module` creates and checks a single contribution. `CONTRIBUTING.md`, module-authoring examples, ownership, governance, issue/PR templates and targeted CI are retained and hashed. |
| I4: versioned study, overrides, update, migration and rollback | `versioning/scenario.json` and version conformance tests exercise every update stage, explicit conflicts, old resume, configuration rollback, migration and inverse. A01/A04/A06/A09/A12 close defects in those guarantees. |
| I5: actual toy evidence, analysis, claims and manuscript | Generic walkthrough has 26 successes, one failure, one interruption and separate retry IDs. Analysis has raw manifest, summary, per-seed/sensitivity tables, SVG, C1/C2/C3 and manuscript. Independent arithmetic verifies eligibility and every reported numerical result. |
| Version scenario 1: identical selection across hosts | Equal bundle IDs and summaries; generated wrapper checks; no native hooks/subagents/model pins. |
| Version scenario 2: central edits do not leak | Central/profile isolation tests plus campaign CLI dispatch and the selected-source sentinel regression. Source-copy mutation is rejected before export can be accepted. |
| Version scenario 3: upgrades preserve study code/overrides | Domain inventory and overrides are compared before/after actual updates; local variants retain base/scope and their bytes. |
| Version scenario 4: expose generated edits and contract mismatches | Bundle/entrypoint edits block planning, late input edits invalidate plans, and unsupported contract versions fail before adoption. |
| Version scenario 5: historical resume after replacement/retirement | Synthetic deprecation/coexistence/retirement releases retain old bundles and resume an earlier campaign using its recorded entrypoint. These are fixtures, not published release claims. |
| Version scenario 6: migration differs from update and rollback | Migration/inverse leaves bundle lock unchanged; update rollback restores complete configuration. A12 checks actual scaffold origin and invalidates an update plan after a scaffold change. |

## Foundation, modules, configuration and contribution

| Specification obligation | Evidence and boundary |
| --- | --- |
| Vendor-neutral method instructions; host controls in adapters | Every shared skill has name/description frontmatter, adjacent manifest and declared resources. Catalog rejects provider syntax in shared methods. Official Codex/Claude paths were rechecked; external YAML/skill checks validate generated wrappers. |
| Generic reading/injection and sequential handoffs | `ALLAGMA.md` routes to the selected catalog; recipe steps connect shared contracts. Native tools/hooks/subagents are optional. This is an instruction workflow with small helpers, not a universal executable workflow engine. |
| Required capabilities and explicit missing connections | Resolution checks dependency capabilities and effective authorization; absent capabilities fail without omitting a scientific check. No equivalent external runner is claimed. |
| Study-local installation, preserve existing instructions/skills | Namespace-conflict conformance retains user `AGENTS.md`, `CLAUDE.md`, `ALLAGMA.md` and preexisting skills. Ownership checks block later overwrites. |
| Host support scope and versions | Acceptance records platform, Python, installed-host probes and capabilities. `docs/host-support.md` separates format/contract checks from unperformed native activation and model-quality evaluation. |
| Manifest identity, contracts, capabilities, settings, dependencies, resources, lineage, lifecycle, owner and examples | `Catalog.check` inspects all required fields and referenced files. Dependency, retirement, resource, role-compatibility and recipe-handoff negative tests are included. |
| Recipe ordering, branches, termination and roles | Shared recipe instructions and `recipe.json` declare the control flow. Catalog checks handoffs, outputs, dependency closure and positive reanalysis repetitions. Budget/failure/interruption paths execute in the walkthrough. |
| Separate methods, recipes, adapters, contracts, evaluations, policy/profile and distribution | Registry and directories preserve each ownership boundary. Study science is under `examples/toy-study/domain`; provider integration remains under adapters. A coherent release is selected; arbitrary independent module-version resolution is not claimed. |
| Research and improvement are distinct | Research artifacts differ from retained proposal/candidate/comparison/ImprovementRecord packages. Adopt/reject/not-evaluated examples do not automatically change defaults. |
| Brief reconstructs the question, resources, constraints, output and stops | StudySpec is schema-checked and compared with the frozen brief, lock, resources and protocol. A11 tests conflicting metadata. |
| Configuration precedence and provenance | Module → recipe → profile → study → override → current request is tested, with leaf provenance and frozen configuration input hashes. Profile edits cannot change an existing campaign. |
| Unset resources are not unlimited | A03 blocks launches until explicit attempt, time and monetary ceilings exist. Timeouts, attempt ceilings, repeated failures and conservative recovery charges are tested. Partial packages remain possible. |
| Preserve GUI model selection and private configuration | No project model/review-model pins are generated. Configuration rejects model pins and common credential keys; public profiles contain no personal secrets. Programs still run with host permissions, as documented. |
| Lifecycle and defaults are separate | Stable public defaults, explicit experimental opt-in, deprecated replacement metadata and retired-module exclusion are checked. Governance defines maintainer review and coexistence commitments; automatic upstream release governance is not claimed. |
| Contributor materials and English documentation | Contributor asset digests, link validation, minimal module example, Code of Conduct, CODEOWNERS, governance and release/migration guidance. Public prose is English; source snapshots retain their owner-supplied provenance. |
| License and attribution before publication | MIT license is retained; third-party notices distinguish design inspiration from code reuse and optional validators. No public release/tag publication was performed. |

## Research and evidence integrity

| Specification obligation | Evidence and boundary |
| --- | --- |
| Scope and prior-work uncertainty | Toy brief and evidence map separately record mathematical-source metadata, support and novelty limits. The known-answer derivation is explicit; no broad literature-search completion is claimed. |
| Protocol, controls, data boundaries and stop rules | Frozen protocol declares two known-answer pilots, 24 disjoint confirmation seeds, metrics, uncertainty, sensitivity, figure and resource stops. Duplicate or overlapping seeds fail. |
| Actual pilots and qualification before confirmation | Runner and evaluator are distinct study programs. A failed pilot prevents confirmation; the evaluator checks seeded observations, estimator arithmetic and known-answer controls. |
| Every attempt retained, including failure and interruption | Separate started/terminal records, new retry IDs, retained raw/partial outputs, stdout/stderr, commands and worker diagnostics. Recovery does not infer success from leftover files. |
| Frozen materials and complete run inventory | Code and experiment manifests are checked against the protocol's complete declared inventory and paths. Their referenced bytes and successful outputs must match before use. A11 covers omission. |
| Protocol amendments preserve reason, affected runs and prior revision | A10 rejects revision reuse and absent lineage, stores an amendment receipt linking the previous protocol, and preserves earlier campaigns. Unchanged replication remains allowed. |
| Analysis recomputation, tables, figure, sensitivity and negative evidence | Paired MSE and normal-approximation uncertainty are recomputed from raw samples. A13 adds planned leave-one-seed-out analysis and the SVG; C2 preserves counterexamples to a universal ordering. Figure rendering was visually inspected. |
| Explicit partial or budget-limited package | Separate limited-budget study has two eligible confirmation observations, partial configuration and manuscript limitation, and terminal state `partial`. Insufficient evidence produces an execution report instead of invented statistics. |
| Phase, execution status and assurance remain distinct | Separate state fields; A05 resets assurance for new analysis and recovers interrupted attempts before forming manifests. New review material is not covered by an old verdict. |
| StudySpec / ExperimentSpec / RunRecord / AnalysisRecord / ClaimRecord / ReviewRecord | Versioned schemas, producer checks, transitive reference verification, data eligibility and recomputation. Independent structural validation and 1,557 differential mutations supplement behavioral tests; schemas alone are not scientific assurance. |
| ContextRecord / ImprovementRecord | Required-context preservation and controlled-comparison examples execute; producer identity, artifacts, lineage, cost, intervention, decisions and scope are retained. These records supplement the six core research contracts. |
| Claims connect supporting/contradicting evidence and become stale | Claims link analysis, raw manifest and run dependencies. Raw mutation yields stale C1/C2/C3; manuscript mutation gets a new revise verdict. Original ledgers and reviews are retained. |
| Bibliographic metadata and support are separate | `evidence-map.json` contains distinct fields for each; the manuscript cites the frozen study-owned derivation. No external citation claim is fabricated. |
| Same-family review is provisional; deterministic assurance is scoped | The delivered reviewer is deterministic with coverage text. No same-family or independent scientific peer-review result is claimed. |
| Append-only meaning, retention and material revision | Immutable writes, inventories, retained bundles and review material digests detect changes. Hashes are not signatures and do not prevent coordinated rewriting of the trusted history; that limit is documented. |

## Improvement and delivery

| Specification obligation | Evidence and boundary |
| --- | --- |
| Proposal → candidate → comparison → decision → release decision | Comparison packages retain proposal, candidate/baseline files, common runtime, fixtures, traces and ImprovementRecord. Release/default selection remains an explicit separate decision. |
| Controlled tasks/resources, quality/noise/cost/complexity/intervention | Fixed deterministic retention fixtures, zero sampling noise, serialized-character cost, measured wall time and stated complexity/intervention. This supports only the measured fixture decision. |
| Environmental failure is not a measured rejection | Separate failing candidate yields `not evaluated`; a costlier working candidate yields `reject`; the focused context candidate yields bounded `adopt`. |
| Retain exact bytes and reproduce after relocation | Full archive inventory and SHA-256, extraction elsewhere, invocation through the archived helper and retained new review trace. |
| Commit in coherent increments and push after completion | Audit fixes are committed separately from final qualification/reporting. Delivery is complete only after `origin/main` equals the final local commit and CI for that commit passes. |

## Explicit residual limits

The generic local POSIX workflow is executed; native Codex and Claude model
sessions are not. The implementation is not a security sandbox. Cleanup covers
the launched process group, not hostile code deliberately escaping that group.
The sensitivity result concerns individual confirmation seeds, not other
scientific questions or distributions. Closed-model reproducibility, remote
runners, external optimizers, arbitrary module-version solving, Noemetric and
manuscript submission remain outside the adopted v0.2 qualification scope.
