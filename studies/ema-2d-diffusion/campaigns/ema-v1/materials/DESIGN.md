# Prespecified study design

The question is whether fixed weight EMA helps a tiny DDPM, and how its effect
depends on dataset, decay and update count. This is not a novelty test. The
reference architecture has **296,450** trainable parameters; a hand-calculated
296,962 assertion was corrected against the instantiated parameter count before
pilots. All failed setup checks remain in the compute ledger.

## Experimental unit and controls

One unit is a complete, independently seeded training trajectory, with paired
raw/EMA0.99/EMA0.999 measurements at updates 5,000 and 10,000. Both EMAs start
from the same initial parameters and update after every optimizer step. There
is no warmup or correction. Evaluation noise and held-out data are shared
within a trajectory; evaluation cannot advance training randomness. The 5k
checkpoint is observed in the 10k learning-rate schedule, not trained with a
separate shorter schedule. Optimizer settings and model are identical across
conditions. Constant EMA decays differ from the reference's warmup/sparse update
implementation.

Two moons use uniform independent angles, balanced mixture probabilities,
Gaussian coordinate noise of 0.03, and the reference's affine transformation.
The other distribution is eight equal-weight isotropic Gaussians at radius-two
circle centers, each with standard deviation 0.15. Each trajectory has 100,000
training draws and 2,048 independent held-out draws. RNG seeds are separated by
fixed offsets for training data, holdout data, optimization draws and sampling.
Minibatches sample with replacement. All seeds and offsets are recorded.

## Pilot and confirmation gate

Pilot seeds are 11/12 (moons) and 21/22 (mixture). Confirmation uses 1001–1005
and 2001–2005 respectively. The proposed numerical protocol and code are locked
before pilot execution. After all four pilots and known-answer checks pass,
`manage.py freeze` writes an immutable confirmation decision binding the exact
protocol, pilot records, code and cost forecast. No confirmation is allowed
before that receipt; the runner also enforces this. If no change is needed,
the same already locked numerical protocol becomes the confirmation protocol.
Any required scientific change needs an explicit new revision/campaign before
confirmation; old results remain intact.

Known-answer checks cover projected W1 identity/translation, all/single/zero
mixture-mode controls, data partitions, the diffusion inversion, exact EMA
updates and CPU/MPS forward agreement. Every complete attempt separately
verifies its held-out dataset, checkpoints, and projected W1 against SciPy.
One real 100-update pilot attempt is deliberately interrupted to qualify native
recovery. It is never counted as scientific data. A fresh native session must
reconstruct the state from the campaign, retaining the interrupted attempt and
using a new attempt ID.

## Metrics and analysis

The primary metric is mean empirical projected Wasserstein-1 over 128 fixed
unit directions (direction RNG seed 7321), evaluated on 2,048 generated and
2,048 held-out draws. The secondary mixture metric is the number of modes with
at least ceil(0.01 × 2048) samples assigned to that nearest center and within
three component standard deviations (0.45). Inlier fraction and half-L1
inlier-mass discrepancy from 1/8 per mode are supporting diagnostics. The
last quantity includes outlier/missing mass and is not normalized categorical
total variation. A second independent held-out sample estimates the metric's
finite-sample floor; it is not subtracted from scores.

Analyze the five confirmation seed differences separately for each of eight
dataset/checkpoint/EMA combinations. Report mean, standard error and unadjusted
two-sided 95% Student t interval (df=4), all individual differences, improved
seed count, exact two-sided sign-flip sensitivity and leave-one-seed-out mean
range. The sign-flip calculation assumes sign exchangeability, with minimum
two-sided p=0.0625. These eight comparisons are descriptive and do not
support a familywise superiority claim. Do not pool checkpoints, directions
or generated samples as additional replicates. No pilot data enter inference.

Plot the paired effects and uncertainty. The qualitative sample figure uses
the first 1,024 draws of the smallest prespecified confirmation seed in each
dataset at 10k updates, without selecting by visual quality. Retain raw draws,
checkpoint weights, actual commands, environment, timings, and failed attempts.
Recompute all metrics and figures from those raw artifacts with frozen code.

## Resource policy

The study-wide ceiling is 1,800 elapsed scientific-process seconds, serially
accounted by `compute.py`. It includes setup scientific checks, training,
sampling, evaluation, retries, plotting and recomputation, plus a conservative
15.3-second charge for the earlier user-reported feasibility estimate. That
estimate is never scientific evidence. Environment installation, code editing,
framework-only tests and native model deliberation are outside the study
computation clock. Native model usage is retained separately and no pay-as-you-go
API key is used. This is local GPU wall time, not a sum of CPU core seconds.

Allow at most 18 training attempts (14 planned successes, one interruption and
three additional retry slots), no more than two failures per planned run, and
150 seconds per attempt including evaluation. The Allagma campaign has an
additional 1,650-second attempt ceiling. The outer supervisor reserves 162
seconds before each attempt, including controller overhead, and conservatively
charges the reservation if interrupted without a completion receipt. It
reserves 122 seconds for each analysis/audit call; actual elapsed time is charged
on normal completion. An attempt is not launched without sufficient remaining
reserve. Before confirmation, the forecast must fit ten times the slowest
pilot × 1.15 plus 120 seconds for analysis/reproduction. Ask the user before
expanding budget or changing the research question.
