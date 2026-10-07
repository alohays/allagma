# Post-delivery self-audit

Audit baseline: Git commit `43ca353e9dfc12094fe2b0f89971fbeed3f31cea`.
The original 51 tests passed again before this audit. They did not establish
all of the claimed failure, recovery and resource invariants.

This is a self-audit by the implementing agent, not an independent human review.
The audit uses separate adversarial regressions, current-state inspection,
independent numerical calculations and a fresh acceptance run. Native host
activation and model quality remain separate, unperformed qualifications.

## Reproduced findings

| ID | Severity | Defect and consequence | Regression evidence |
| --- | --- | --- | --- |
| A01 | High | Update recovery overwrote files edited after interruption, risking loss of user work. | `test_recovery_preserves_post_interruption_user_edits` |
| A02 | High | Worker cleanup stopped checking a process group after its leader exited. Analysis/review helper timeouts killed only the parent. Descendants could continue executing and writing after return. | `test_worker_cleans_descendants_after_leader_exits`, `test_helper_timeout_cleans_descendants` |
| A03 | High | Unset resource ceilings allowed execution despite the explicit resource policy. | `test_unset_resources_do_not_authorize_execution` |
| A04 | Medium | Failed campaign creation and interrupted attempt preparation published incomplete directories that prevented retry. | `test_failed_campaign_creation_does_not_publish_partial_campaign`, `test_interrupted_attempt_preparation_can_resume` |
| A05 | Medium | Partial analysis omitted a controller-interrupted attempt; a new analysis inherited an earlier review's assurance. Incomplete review directories could prevent retry. | `test_partial_analysis_recovers_interrupted_attempt_before_manifest`, `test_new_analysis_does_not_inherit_review_assurance`, `test_review_retry_preserves_incomplete_review_directory` |
| A06 | Medium | A source edit during export could associate copied helper bytes with a different source revision. | `test_export_rejects_source_changes_during_copy` |
| A07 | Medium | Replacement resolution also selected the unused default, importing its settings and capability requirements. Recipe metadata could disable the claimed reproduction check with zero repetitions. | `test_replacement_does_not_resolve_unused_default`, `test_recipe_cannot_disable_reproduction` |
| A08 | Medium | Exponent overflow bypassed JSON's finite-number guard; budget validation disagreed with the record schema; permissive timestamp parsing and symlink resolution hid invalid inputs. | `test_json_exponent_overflow_is_rejected`, `test_configuration_matches_budget_schema`, `test_timestamp_requires_rfc3339_time_and_zone`, `test_reference_rejects_symlink_alias` |
| A09 | High | `toy --source` exported the selected source but executed campaign helpers from the calling checkout, so the claimed pinned runtime could differ from the runtime used. | `test_toy_executes_the_selected_source_helper` |
| A10 | Medium | A changed protocol could reuse its revision or omit the reason and affected-run lineage. | `test_protocol_changes_require_revision_and_amendment_lineage` |
| A11 | Medium | Frozen material inventories could silently omit files; StudySpec configuration could disagree with its frozen lock. | `test_omitted_frozen_material_is_rejected`, `test_study_metadata_cannot_disagree_with_frozen_lock` |
| A12 | Medium | Initialization hardcoded scaffold version 1, while method updates could claim a target scaffold version without migrating user files. | `test_scaffold_baseline_uses_selected_release`, `test_method_update_does_not_claim_scaffold_migration` |
| A13 | Medium | The toy omitted the default lifecycle's sensitivity analysis and figure, while the acceptance source inventory did not separately track study examples. | `test_analysis_includes_seed_sensitivity_and_reproducible_figure`; retained example inventory and independent numerical audit |

The first [failing log](baseline-regressions.log) contains 11 regression tests
against the original implementation (14 failed subcases and one error). The
[second-pass log](second-pass-regressions.log) records three further failures
and one error after the initial corrections. A positive-repetition guard was
also added from direct inspection of recipe validation and audit control flow.
All regressions live in `conformance/test_audit.py` and run in the default kit.
The [routing regression](helper-routing-regression.log) separately demonstrates
the ignored helper in a selected source. The walkthrough now dispatches through
the same pinned command-line entrypoint used by ordinary campaign operations.
The [specification-level log](specification-regressions.log) records five
additional failures for amendment lineage, frozen metadata and scaffold origin.
The [analysis-scope regression](analysis-scope-regression.log) demonstrates the
missing sensitivity result. The new toy protocol revision `toy-v2` declares
leave-one-seed-out analysis and a figure before execution; C3 records its result.
The walkthrough campaign ID remains `toy-v1` (campaign ID and protocol revision
are separate fields). Original archived studies retain protocol `toy-v1`.

A stress test caught a regression in the initial cleanup fix: a vanished
process group sometimes returned a permission error in this macOS environment,
preventing the worker receipt from being saved. Cleanup now checks whether live
group members remain and always records cleanup failures. Worker diagnostics
are retained. Thirty successive controller-kill checks passed after correction.

The independent schema comparison found an invalid timezone offset accepted by
the standard library's permissive ISO parser. After correction, all
[1,557 differential cases](contract-differential-after.json) agree with
jsonschema and its installed RFC 3339 validator. The
[earlier differential receipt](contract-differential-before.json) retains the
counterexample; the optional validation environment now includes timestamp
format validation.

The [independent calculation](baseline-science.json) verified the original toy's
numerical conclusion using rational arithmetic and a complete binomial
enumeration, without importing its implementation. The observed MSE difference
is exactly `25/384`; the population expectation is `1/16`. Differences in the
last floating-point digit of the standard error are within the stated tolerance.

The fixes preserve historical bundles. Updating central source does not repair
an already pinned old helper; new campaigns must explicitly adopt the corrected
source. Existing campaigns retain their original source and evidence.

## Audit status

The reproduced cases are corrected. Requirement mapping, independent scientific
verification and refreshed final acceptance evidence are still in progress.
The original archive remains historical evidence for the baseline, not proof
that the corrections have been qualified.
