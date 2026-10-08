# Twelve-session research workflow comparison

All twelve assigned sessions completed the required scientific execution and
passed their numerical checks. Allagma produced six complete evidence packages
out of six; plain Codex produced four out of six. The two incomplete packages
contain substantive critiques but do not explicitly bind them to a reviewed
material revision. This is a narrow evidence-management difference in two
modular-addition runs, not evidence that the baseline failed to do the science.
The experiment does not establish broad research superiority or a consistent
time or token saving.

The [generated report](../../evals/research-v0.3/comparisons/final/REPORT.md)
contains every run, all eight evidence items, process outcomes, resource fields
and six paired contrasts. Its [JSON](../../evals/research-v0.3/comparisons/final/comparison.json)
also retains task-specific means and ranges. Both derive from the
[final outcome ledger](../../evals/research-v0.3/outcomes-final.json); no assigned
run was discarded, repaired in place or replaced by a more favorable result.

## Design and observed controls

The frozen design is three tasks × two conditions × two isolated fresh sessions.
The baseline is plain Codex with the same computation broker, measurement
interface, inputs, wheelhouse and limits. The treatment adds the pinned Allagma
workflow and an explicit invocation instruction. Task/replicate blocks and
within-block order were frozen before execution. Sessions ran serially on the
same M4 Pro Mac with 14 CPU cores, 20 GPU cores and 48 GB unified memory.

The [freeze](../../evals/research-v0.3/frozen/freeze.json) binds workflow source
`c369fe7aabb5bd5575f967b3e3704cf463a97eb0`, scorers, criteria, inputs, resource
profiles and order. All sessions used CLI 0.160.1 and the user's inherited
`gpt-6-astra` / `max` settings, with the same one-million-token context setting.
No project model pins, personal skills, prior chat history, nested model agents
or task-specific follow-up messages were supplied. The service does not expose
a fixed backend model revision, so that is not a controlled variable.

The [final control audit](../../evals/research-v0.3/postprocess-checks/cohort-controls-final.json)
passes for twelve distinct native threads, actual model/settings/CLI/adapter
observations, unchanged common inputs, protected profile/source hashes,
resolved reservations, charged ceilings, zero coordinator follow-ups and current
terminal footprints. The [treatment audit](../../evals/research-v0.3/postprocess-checks/treatment-compliance-final.json)
finds successful real command events returning the exact frozen recipe and all
seven methods in every Allagma session. This establishes explicit reading and
locked delivery; it does not establish implicit skill triggering.

Every run received one planned timeout on its first marked scientific attempt.
All twelve actual timeouts and subsequent recovery requests remain retained.
These planned interruptions are separate from the zero subsequent interventions
and from each agent's autonomous corrections. Scientific computation stayed
local; native inference used the existing Codex account. No limits were expanded.

## Outcomes

| Outcome | Codex + Allagma | Plain Codex |
| --- | ---: | ---: |
| Assigned fresh sessions | 6 | 6 |
| Required scientific execution verified | 6/6 | 6/6 |
| Numerical checks pass in every run | 6/6 | 6/6 |
| Complete evidence package | 6/6 | 4/6 |
| Verified evidence items | 48/48 | 46/48 |
| Subsequent coordinator interventions | 0 | 0 |

Each of the four CORE runs passed the unchanged original six-question scoring
rule. Each modular-addition run passed 40 checks. Each EMA run passed 240 checks,
including all 96 saved-state sample replays. Source, execution, input pairing,
scientific inference, artifact hashes and review revisions were inspected
separately; numerical success alone did not determine completion.

Plain runs [r03](../../evals/research-v0.3/runs/r03/substantive-review.json) and
[r06](../../evals/research-v0.3/runs/r06/substantive-review.json) received 7/8 for
the same frozen item-8 requirement. Their generic manifests seal files but do
not explicitly identify the material assessed by the critique. All other runs
received 8/8. The underlying review content was not treated as absent, and the
controller did not retroactively add a revision binding to their submissions.

The first fully verified Allagma package for each task was selected by the
prespecified rule: [CORE r01](../../studies/core-culp/RESULTS.md),
[modular addition r04](../../studies/modular-addition/RESULTS.md), and
[EMA r07](../../studies/ema-schedule/RESULTS.md). Their findings remain bounded:
CORE preserves the original Iris/Zoo predictor-label bug; the modular study
finds improved held-out accuracy with regularization but no prespecified 95%
grokking event; EMA shows a schedule-dependent descriptive pattern with
inconclusive duration/interaction intervals. Repeated agents using the same
confirmation seeds do not increase the studies' independent sample sizes.

## Resources and variability

Each native session had 3,600 seconds. CORE allowed 600 compute seconds and
32 compute requests; the two training tasks allowed 1,800 seconds and 64
requests. All allowed 300 setup seconds, a 180-second command timeout, 8 GiB
polled RSS, 6 GiB logical workspace storage and 512 MiB per file. Failed jobs
count toward their ceilings. Setup, scientific computation and native usage
remain separate accounting dimensions.

| Task | Condition | Compute seconds, mean [range] | Native seconds, mean [range] |
| --- | --- | ---: | ---: |
| CORE | Plain | 74.68 [71.92, 77.43] | 1276.54 [1065.67, 1487.42] |
| CORE | Allagma | 92.76 [76.26, 109.27] | 1616.21 [1310.95, 1921.48] |
| Modular addition | Plain | 1268.03 [1215.97, 1320.09] | 2337.68 [2012.26, 2663.10] |
| Modular addition | Allagma | 1295.25 [1186.59, 1403.91] | 2192.75 [1942.91, 2442.58] |
| EMA | Plain | 411.06 [400.11, 422.01] | 1724.09 [1451.36, 1996.83] |
| EMA | Allagma | 599.02 [362.39, 835.64] | 1705.28 [1511.68, 1898.88] |

Each range contains only two sessions. Allagma-minus-plain native differences
range from −220.52 to +855.81 seconds across the six paired blocks. There is no
consistent saving. The two conditions also performed different optional
verification work: r12 selected CPU from its pilot and reran all 24 EMA training
trajectories in a fresh environment, whereas r07/r08/r11 used MPS and did not
perform a second complete training campaign. Their compute times are not a
fixed-workload CPU/GPU benchmark. Host cache and concurrent desktop activity
were not controlled as in a dedicated performance experiment.

The generated report lists cumulative input, cached-input, output and
reasoning-output token fields separately. Cache and reasoning fields are never
added again to other counts. Across these six-task mixtures, mean input tokens
were 3,959,214.5 for Allagma and 3,095,783.8 for plain; mean output tokens were
51,731.8 and 52,511.5. These are descriptive usage records, not billed-dollar
estimates or measures of scientific quality. Controller verification has its
own [ledger](../../evals/research-v0.3/validation/resources/policy.json) and is
excluded from original agent costs and outcomes.

## Failures, corrections and scientific conventions

The original broker supplied MPS high watermark 0.2 without lowering PyTorch's
incompatible default low watermark. Eight runs retain an actual failed MPS
initialization: r03–r08 and r11–r12. The four CORE runs use CPU.
The frozen outcome includes CPU fallback or a study-owned low-watermark repair.
The separately corrected rc2 broker passed actual GPU training/checkpoint and
access-denial tests; this cohort does not measure that corrected path.

All 18 non-timeout failed scientific jobs are retained. Beyond the eight MPS
failures, r01 corrected its independent graph check's self-loop treatment;
r03/r04 corrected overly strict auxiliary numerical tolerances; r05 retained
two C/PyTorch pilot discrepancies and a final package-check failure before
passing its amended, disclosed checks; r06 corrected an auxiliary float64
argmax comparison against its actual float32 checkpoint execution; r11 corrected
an exact-zero permutation assertion; and r12 corrected NumPy boolean
serialization and its permutation tolerance. No training result was silently
replaced. The original error logs, amendments and controller findings remain
linked by each run's substantive review and resource receipts.

The frozen modular scorer incorrectly expected a curve path where the interface
allowed an inline list. Original unscorable receipts for r03/r05/r06 remain
retained. A separately protected loader-only correction accepts both forms,
applies uniformly, and passes equivalence checks with the original scorer on
identical curve data. No scoring formula, tolerance or scientific criterion was
relaxed. Archive transport corrections likewise preserve the original packages.
See the [defect record](defects.md) for exact before/after evidence.

r05's modular implementation uses C/Accelerate after CPU/MPS pilots. Its declared
float32 equations passed independent black-box checks, but long-run bitwise
identity to PyTorch is not claimed. r11 prospectively defined cosine with
denominator D−1 and a zero final applied rate; r07/r08/r12 use denominator D and
a near-zero final rate. Both satisfy the brief's unspecified indexing choice.
These autonomous implementation choices are preserved rather than normalized
after observing results. Cross-run differences are not additional controlled
scientific interventions.

## Interpretation and release boundary

Three selected task families and two sessions per condition are insufficient
for a population effect estimate. The task families were used during development;
final sessions and confirmation seeds were separate, but the families are not
unseen. CULP is a locally adapted selected CORE-Bench training task with curated
dependencies and added evidence requirements, not a leaderboard evaluation.
Same-model author critique and controller inspection remain provisional rather
than independent scientific peer review.

Polled RSS omits some GPU allocations, and watchdogs permit sampling/termination
overshoot. The original supervisors also had a final-storage sampling race.
All twelve terminal footprints were independently below their caps; this is not
a continuous historical peak measurement. rc2 checks final persistent storage
after exit, with separate actual-worker and explicitly fake-CLI regressions.
It does not claim adversarial containment or instantaneous hard memory limits.

The scientific packages, comparison and historical freeze remain immutable.
Release repairs, acceptance and reproduction evidence are separately identified
in the [release notes](../releases/0.3.0rc2.md) and
[requirement ledger](requirements.md). The small observed review-binding benefit
is a result worth retaining; it does not justify a general superiority claim.
