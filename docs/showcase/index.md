# Completed studies and their outputs

These studies show what a coding agent returned after working from a research
brief with Allagma. Each package includes its protocol, code, raw results,
report and critique. Start with a result below, then follow the links to the
full record and reproduction instructions.

For a small example you can run without a model account, use the
[offline toy tutorial](../guides/first-study.md) or
[preview its figure and report](https://alohays.github.io/allagma/explore/).
That example supplies the scientific code; the native studies below were
developed and executed by coding agents.

## Weight EMA: a figure and a qualified finding

The agent investigated how training duration and learning-rate policy affect
the benefit of averaging tiny diffusion model weights. It completed 32 cells
and retained 96 raw/EMA model states.

![Retained EMA r07 figure, with paired effects across duration and learning-rate policy](../../media/evidence/ema-r07.png)

The relative benefit of EMA was larger under constant learning rate than at
completed cosine endpoints. With four independent seeds per dataset, duration
and interaction estimates remain inconclusive. A smaller relative benefit does
not imply worse absolute EMA quality.

[Read the result and its limits](../../studies/ema-schedule/RESULTS.md) ·
[Open the full-size figure](https://alohays.github.io/allagma/generated/media/evidence/ema-r07.png) ·
[Read the agent's report](../../media/evidence/ema-r07-report.md)

This preview is retained r07 work. Raw-data reanalysis and saved-state checks
passed; a second full training replay is not claimed. The
[AI Scientist source attribution and license](../../studies/ema-schedule/REFERENCE.md)
apply to the adapted study materials.

## CORE CULP: reproduced answers and an explained source defect

The agent reproduced a graph-classification capsule. All six requested
answers matched the original scorer. Inspection also found that the Iris and
Zoo outputs printed CN/AA labels while actually calling the CS predictor.
The result table makes that distinction explicit.

| Output | What a reader can inspect |
| --- | --- |
| Six numerical answers | Printed label, actual predictor and accuracy for each dataset |
| Source and graph checks | The upstream label defect and the agent's own corrected checker |
| Reproduction instructions | A full run in a fresh environment and a separate raw-result recomputation |

[Read the CORE CULP result and full replay evidence](../../studies/core-culp/RESULTS.md).

The fixed transductive splits do not provide a cross-split or population
uncertainty estimate. A clean-checkout replay of this r01 package passed,
including environment setup and full execution.

## Modular addition: improved accuracy without observed grokking

The agent compared weight decay 0 and 1 in four paired seeds of a small MLP.
All eight training trajectories completed 100,000 updates and memorized the
training set. Final held-out accuracy improved with weight decay, but no
trajectory met the sustained 95% accuracy threshold for grokking.

The package retains training curves, checkpoints, paired estimates and a
report that distinguishes the endpoint result from the unobserved transition.
The mean paired accuracy difference was 67.46 percentage points, with a
95% t interval of 50.31 to 84.61 points. Four seeds make those small-sample
assumptions fragile.

[Read the paired results and qualifications](../../studies/modular-addition/RESULTS.md).

The r04 package passed retained-data reanalysis and checkpoint verification.
A second full training replay is not claimed, and this MLP study does not
replicate the source paper's transformer experiments.

## How these examples were selected

Each native example is the first complete Allagma package for its task in
frozen run order. Selection did not depend on favorable scientific outcomes.
These are workflow examples, not evidence of general research superiority.

The [twelve-session comparison](../v0.3/COMPARISON.md) includes every assigned
run. All twelve completed the required science. Allagma produced six complete
packages out of six; plain Codex produced four out of six. The two baseline
packages contain critiques but lack explicit binding to the reviewed revision.
This small local comparison does not establish a general time, token or quality
advantage. Model critique and controller checks do not replace independent
scientific peer review.

Full archives are optional. [Artifact distribution](../launch/artifact-distribution.md)
explains the downloads, and [third-party notices](../../THIRD_PARTY_NOTICES.md)
identify the licenses. Allagma's core is MIT licensed; study materials retain
their own terms.
