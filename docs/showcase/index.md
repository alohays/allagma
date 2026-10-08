# Studies you can inspect

These are executed local studies with retained protocols, attempts, raw data,
figures, reports and review. Each was selected as the first complete Allagma
package for its task in the frozen evaluation order, before comparing outcomes.
They illustrate the workflow; they do not establish general research superiority.

| Study | Question and observed result | Inspect |
| --- | --- | --- |
| Bias and squared error | A known-answer offline example with 24 confirmation seeds; a favorable average and four counterexamples to an overstrong claim | [Run it yourself](../guides/first-study.md) |
| CORE CULP · r01 | Can the original graph-classification capsule be reproduced? All six answers match, with a source label defect explicitly preserved | [Results and full replay](../../studies/core-culp/RESULTS.md) |
| Modular addition · r04 | Does weight decay change held-out generalization? Endpoint accuracy improves, but no trajectory reaches the prespecified sustained grokking threshold | [Curves, statistics and limits](../../studies/modular-addition/RESULTS.md) |
| Weight EMA · r07 | How do training duration and learning-rate policy affect EMA's benefit? Descriptive schedule differences; duration and interaction intervals remain inconclusive | [Figure, paired effects and limits](../../studies/ema-schedule/RESULTS.md) |

The CORE package passed full execution from a clean Git checkout and a fresh
environment, followed by a separate raw-result recomputation. Modular r04 and
EMA r07 passed retained-data checks and checkpoint verification; a second full
training replay is not claimed for those two illustrative packages.

The [twelve-session comparison](../v0.3/COMPARISON.md) includes all assigned
runs. All twelve completed the required science. Allagma produced six complete
packages out of six; plain Codex produced four out of six. The two baseline
packages contain critiques but lack explicit binding to the reviewed revision.
The small local comparison does not show a general time, token or quality advantage.

Full archives are optional downloads. See [artifact distribution](../launch/artifact-distribution.md)
and [third-party notices](../../THIRD_PARTY_NOTICES.md), especially the separate
AI Scientist license on EMA-derived scientific code. Allagma's core remains MIT.
