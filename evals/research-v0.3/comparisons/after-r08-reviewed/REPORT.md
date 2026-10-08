# Frozen local research-workflow comparison

Status: **partial**. Verified complete original packages: 6/12.

This report is generated from retained scoring, review and resource receipts.
A native process exit, numerical correctness and package completion are distinct.
Missing evidence is shown as NA; it is not converted to zero or removed from the assigned cohort.

Pending runs/reviews: r09, r10, r11, r12. This is an interim report, not a completed evaluation.

## Assigned outcomes

| Run | Task | Condition | Replicate | Native | Numerical | Evidence /8 | Required execution verified | Package complete |
| --- | --- | --- | ---: | --- | ---: | ---: | --- | --- |
| r01 | core-culp | allagma | 2 | completed | 6/6 | 8 | yes | yes |
| r02 | core-culp | plain | 2 | completed | 6/6 | 8 | yes | yes |
| r03 | modular-addition | plain | 2 | completed | 40/40 | 7 | yes | no |
| r04 | modular-addition | allagma | 2 | completed | 40/40 | 8 | yes | yes |
| r05 | modular-addition | allagma | 1 | completed | 40/40 | 8 | yes | yes |
| r06 | modular-addition | plain | 1 | completed | 40/40 | 7 | yes | no |
| r07 | ema-schedule | allagma | 2 | completed | 240/240 | 8 | yes | yes |
| r08 | ema-schedule | plain | 2 | completed | 240/240 | 8 | yes | yes |
| r09 | core-culp | plain | 1 | completed | 6/6 | NA | pending | pending |
| r10 | core-culp | allagma | 1 | running | NA | NA | pending | pending |
| r11 | ema-schedule | plain | 1 | not_started | NA | NA | pending | pending |
| r12 | ema-schedule | allagma | 1 | not_started | NA | NA | pending | pending |

## Per-run evidence gaps and process outcomes

- r01: all eight evidence items pass. Process outcomes: completed=24, failed=1, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
- r02: all eight evidence items pass. Process outcomes: completed=15, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
- r03: Substantive findings and resolutions are present, but review.json does not identify an exact reviewed source/artifact revision. The separate manifest seals files, but does not explicitly bind this review to its material revision as required by item 8. Process outcomes: completed=17, failed=2, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
  Original scorer: unscorable; Evidence paths must be confined relative paths. Compatibility-corrected evidence is reported separately.
- r04: all eight evidence items pass. Process outcomes: completed=27, failed=2, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
- r05: all eight evidence items pass. Process outcomes: completed=32, failed=4, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
  Original scorer: unscorable; Evidence paths must be confined relative paths. Compatibility-corrected evidence is reported separately.
- r06: Critique is substantive, but review.json does not name an exact reviewed manuscript or material revision. A generic file manifest seals files without explicitly binding this review to the material it assessed. This is the same required-evidence gap applied to r03. Process outcomes: completed=22, failed=2, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
  Original scorer: unscorable; Evidence paths must be confined relative paths. Compatibility-corrected evidence is reported separately.
- r07: all eight evidence items pass. Process outcomes: completed=36, failed=1, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
- r08: all eight evidence items pass. Process outcomes: completed=40, failed=1, timed_out=1. Subsequent recorded interventions: 0.
  Planned interruption: observed status timed_out; actual timeout observed=True. Recorded coordinator messages: 0.
- r09: review pending; no completion determination.
- r10: review pending; no completion determination.
- r11: review pending; no completion determination.
- r12: review pending; no completion determination.

## Resource use

The companion JSON retains observed model/settings/input/session matches for every run. Unknown observations remain null.

Seconds are measured/charged by the retained supervisors. RSS and storage are sampled observations,
not proofs of a strict instantaneous bound; RSS omits some GPU allocations.

| Run | Compute s | Setup s | Compute requests | Native s | Input tokens | Cached input | Output tokens | Reasoning output |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| r01 | 76.26 | 15.43 | 20 | 1,921.48 | 2,456,774 | 2,330,112 | 40,977 | 9,368 |
| r02 | 77.43 | 15.14 | 11 | 1,065.67 | 1,266,718 | 1,164,288 | 38,837 | 13,311 |
| r03 | 1,215.97 | 14.30 | 18 | 2,012.26 | 3,153,372 | 2,925,440 | 62,222 | 30,813 |
| r04 | 1,186.59 | 14.73 | 28 | 1,942.91 | 5,885,533 | 5,732,608 | 58,533 | 22,150 |
| r05 | 1,403.91 | 35.26 | 32 | 2,442.58 | 5,572,883 | 5,406,976 | 72,526 | 31,065 |
| r06 | 1,320.09 | 16.53 | 23 | 2,663.10 | 4,925,283 | 4,772,736 | 72,118 | 30,876 |
| r07 | 362.39 | 20.43 | 35 | 1,511.68 | 2,998,321 | 2,860,800 | 44,300 | 10,598 |
| r08 | 422.01 | 22.27 | 38 | 1,451.36 | 2,633,449 | 2,532,096 | 49,207 | 12,454 |
| r09 | 71.92 | 17.10 | 16 | 1,487.42 | 2,002,601 | 1,913,856 | 43,908 | 12,860 |
| r10 | 43.12 | 8.90 | 1 | NA | NA | NA | NA | NA |
| r11 | 0.00 | 0.00 | 0 | NA | NA | NA | NA | NA |
| r12 | 0.00 | 0.00 | 0 | NA | NA | NA | NA | NA |

Cached-input and reasoning-output fields are reported separately and are never added again to other token fields.
Scientific requests, including failures, are counted separately from the planned interruption and any coordinator intervention.

## Six paired contrasts

Each contrast is Allagma minus plain Codex within the same task and replicate block.
Positive correctness/evidence/completion values favor Allagma; positive time/token differences indicate greater recorded use.

| Task | Replicate | Numerical fraction Δ | Evidence Δ | Required execution Δ | Package completion Δ | Compute s Δ | Native s Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| core-culp | 1 | NA | NA | NA | NA | NA | NA |
| core-culp | 2 | 0.0000 | 0 | 0 | 0 | -1.18 | 855.81 |
| modular-addition | 1 | 0.0000 | 1 | 0 | 1 | 83.82 | -220.52 |
| modular-addition | 2 | 0.0000 | 1 | 0 | 1 | -29.38 | -69.35 |
| ema-schedule | 1 | NA | NA | NA | NA | NA | NA |
| ema-schedule | 2 | 0.0000 | 0 | 0 | 0 | -59.61 | 60.32 |

The companion JSON retains all token contrasts and within-task means, ranges and observed/assigned denominators.
Pending runs may show accrued costs, but do not enter paired contrasts or within-task outcome averages.
Means with fewer observed values do not summarize unobserved outcomes; consult the full assigned-outcome table.

## Interpretation limits

Two fresh sessions per condition and three selected task families cannot establish broad research superiority.
The families were used during development; final sessions and confirmation seeds are separate, but the task families are not unseen.
Repeated agents executing the same seed plan do not increase a study’s independent scientific sample size.

CULP is a locally selected CORE-Bench training task with a curated wheelhouse and added evidence requirements, not a leaderboard result.
Both conditions receive the same broker, measurement contract and finite ceilings. Model/settings/input matches and any violations
remain per-run observations; a service-side model revision that is not exposed cannot be claimed controlled.

The frozen shared broker has a reproduced MPS allocator high/low-watermark mismatch. CPU fallback or other candidate recovery
is part of these frozen outcomes. These results do not measure the GPU performance of a later correction.
The inline-curve parser correction is applied uniformly in a separate scorer; original receipts and the exact correction are retained.
Post-evaluation package repairs and controller validation costs must be reported separately from these original agent outcomes.

Required execution and full package completion are shown separately. A missing review-revision binding can make an otherwise executed,
numerically correct study incomplete under the evidence rubric; it does not mean the experiments or substantive critique were absent.
Resource timings are descriptive observations on a shared local host, not a dedicated hardware benchmark.

No population confidence interval is presented for workflow effects: the two-session task-specific ranges are descriptive.
Same-model author critique and controller checks are provisional; neither is independent scientific peer review.
