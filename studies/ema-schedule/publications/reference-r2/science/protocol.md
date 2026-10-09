# EMA schedule follow-up: protocol v1

AI-generated/adapted code and reporting; the supplied AI Scientist Source Code
License is retained. This is a bounded follow-up, not an upstream replication.

The question is whether the apparent advantage of EMA changes with the full
learning-rate policy after separating that policy from terminal training duration.
The prior report is contextual evidence only. No historical trajectories or
confirmation outputs will be reused. No directional result is required.

The confirmation design crosses dataset (moons, GMM8), duration (5,000, 10,000
optimizer updates), and policy (constant 0.0003, or cosine from 0.0003 toward
zero over that duration). Cosine uses the reference discretization at update
k: 0.0003 * (1 + cos(pi*(k-1)/D))/2. Its final applied rate is just above zero;
the schedule reaches exactly zero after D updates. The intervention includes
the entire path. We will not attribute effects solely to the endpoint rate.
The constant trajectory supplies both endpoints. Cosine-5k and cosine-10k are
separate trajectories from identical initial weights, not relabeled checkpoints.

Fixed science: supplied float32 reference Denoiser (296,450 parameters),
100-step cosine DDPM noise schedule, clean prediction clipping [-6,6], AdamW
weight decay 0.01, batch 256, gradient norm clipping 0.5. EMA0.99 and EMA0.999
start as copies of the initial raw model and update after every optimizer step,
without warmup, sparse updates or bias correction. All state-dictionary entries,
including embedding buffers, will be saved in non-pickle NPZ files.

Pilot seeds: moons 71, GMM8 81. Confirmation: moons 4001–4004 and GMM8 5001–5004.
The independent unit is the training seed within dataset. Each seed uses
100,000 training draws, 2,048 independent held-out draws and 2,048 generated
draws for each state. Data seeds are seed+1,000,000 (training), seed+2,000,000
(held-out), seed+3,000,000 (generation). Initialization uses torch.manual_seed(seed).
A NumPy generator seed+100,000 draws 10,000x256 replacement indices, then
10,000x256x2 standard normal targets, then 10,000x256 timesteps, for every policy
and duration. Precomputation follows the reference float64 coefficient arithmetic
then float32 cast. Actual arrays and canonical prefix hashes will be retained.
Generation noise, held-out draws, initialization and all 5,000-step training
prefix inputs are shared exactly across cells of a dataset/seed. Evaluation
never consumes training randomness. Confirmation inputs are created only after
pilot qualification and the confirmation freeze, and never used for tuning.

Primary metric: reference 128-direction Sliced Wasserstein-1, projection seed
7321, float64 metric arithmetic, paired delta = EMA minus raw (negative favors
EMA). For each dataset/decay report all four deltas; schedule contrasts
delta(cosine,D)-delta(constant,D); duration contrasts delta(policy,10k)-
delta(policy,5k); interaction = [delta(cosine,10k)-delta(constant,10k)] -
[delta(cosine,5k)-delta(constant,5k)]. Also report state-level SW1 and analogous
contrasts in absolute SW1 so the EMA contrast is interpretable.

Uncertainty: two-sided 95% Student t intervals across the four paired seed
contrasts (3 df), unadjusted and descriptive. Retain individual values, SD, SE,
leave-one-seed-out means, and two-sided exact sign-flip p-values (16 assignments;
minimum attainable 0.125). Do not treat generated draws, projections, repeated
executions, or shared trajectory endpoints as independent replicates. Small n
and multiple datasets/decays/contrasts preclude strong significance or generality
claims. No decay selection or multiplicity-adjusted confirmatory claim is made.

GMM8 coverage uses nearest-center distance <=0.45, and at least ceil(0.01*2048)
=21 inliers out of all generated draws per covered mode. Retain eight counts,
total inliers, inlier fraction and covered modes; report ceiling effects. Coverage
alone cannot establish correct masses or equivalence. Finite-sample SW1 is not
debiased by subtracting a reference floor.

Qualification before confirmation: SW1 identity, analytically known translation
and custom-axis answers; mode threshold/outlier-denominator checks; EMA update
answer; reference architecture and schedule checks; shared-input identity;
save/load and resumed-versus-continuous optimizer/EMA behavior; reference sampling
equivalence and measured training/sampling cost. Pilot numerical quality does
not choose any scientific hyperparameter. A complete-work forecast includes
200,000 confirmation updates, 96 state samplings, data/I/O, analysis, sample
regeneration and retained-data recomputation. Device is selected from qualified
pilot behavior and cost, with no implicit fallback.

All setup and computation use the common broker, one worker at a time. Ceilings:
setup 300 s, compute 1,800 s, 64 compute requests, 180 s per request, 8 GiB RSS,
6 GiB storage, 512 MiB per file; native session 3,600 s. Reserve at least 100 s
of compute for analysis and verification. Chunk/resume only with full model,
EMA and AdamW state and actual step numbers. Preserve every failed/interrupted
attempt under a distinct ID. The controlled first substantive pilot interruption
is excluded from confirmation. Resume from a verified state or restart with the
same fixed seed, without counting a retry as another seed.

Complete means all 32 cells, all artifacts, preconfirmation qualification/freeze,
recomputed numerical agreement, saved-weight regeneration check, report and
revision-bound critique. Otherwise report partial or blocked honestly. Stop on
resource insufficiency, repeated uncorrectable failures, or failed scientific
qualification. Exclude only failed/incomplete/nonfinite outputs and pilots;
never exclude a finite result based on the sign or size of the EMA effect.
Freeze this protocol and scientific source hashes before confirmation. Later
scientific changes require a new campaign or explicit amendment; reporting fixes
retain prior versions. Sequential artifact handoffs implement the locked Allagma
scope → protocol → pilot → campaign → analysis → writing → audit workflow.
