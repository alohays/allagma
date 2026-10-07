# Weight EMA: separate training duration from learning-rate policy

The supplied completed study compared raw and EMA weights at 5,000 and 10,000
updates along a single cosine learning-rate trajectory. Training duration and
position in the learning-rate schedule were confounded. Design, implement,
execute and critically review a follow-up that separates those factors and
reports how schedule policy changes the apparent benefit of weight EMA.

Use float32 training with the provided reference denoiser, datasets, DDPM noise schedule and evaluation
definitions. Cross terminal duration (5,000 and 10,000 optimizer updates) with
learning-rate policy (constant 0.0003 and cosine from 0.0003 to zero over the
selected duration). The intervention is a full schedule policy, not merely
terminal learning rate. Preserve batch size 256, AdamW weight decay 0.01,
gradient clipping 0.5, 100 diffusion steps, and raw/EMA0.99/EMA0.999 weights with
the reference EMA initialization/update rule. Use both moons and GMM8. Reusing
the constant-policy trajectory's 5,000-update checkpoint is valid; treating a
5,000-update intermediate checkpoint of the 10,000-update cosine schedule as
the completed 5,000-update cosine condition is not.

Before confirmation, define the protocol, qualify known-answer metrics and
runner behavior, and forecast the complete work within the resource ceiling.
Use pilot seeds 71 (moons) and 81 (GMM8) if calibration is needed. Confirmation
uses four untouched seeds per dataset: 4001–4004 (moons) and 5001–5004 (GMM8).
Within a dataset/seed, match initialization, training-data/noise prefixes,
held-out draws and generation noise across conditions. Use 100,000 training
draws, 2,048 held-out draws and 2,048 generated draws per model state. Keep
confirmation data out of implementation or tuning decisions.

Primary evaluation is the reference 128-direction Sliced Wasserstein-1 with
projection seed 7321, paired EMA-minus-raw differences and seed-level uncertainty.
Report schedule contrasts at fixed duration, duration contrasts under fixed
policy, and the interaction; do not infer a mechanism solely from endpoint
learning rate. Retain GMM8 coverage using the original within-0.45 and at-least-1%
of all generated draws rule, together with inlier counts/fractions. State any
ceiling effect or multiplicity limitation. Negative/inconclusive findings are
valid. Do not require an EMA benefit for success.

Retain initial-state hashes, exact run inputs and source hashes, every attempt,
training traces, raw held-out/generated samples, and loadable final raw/EMA
checkpoints for all required cells. Produce machine-readable seed-level
measurements and contrasts, a reproducible main figure, an evidence-linked
English report, and substantive critique at a named material revision. Verify
reported numbers from retained data; include a way to regenerate samples from
saved weights as a distinct check from retraining.

Read `COMPUTE.md` and `RESOURCES.json`. All setup and scientific computation must
use the common local client; preserve the controlled first-attempt interruption
and recover without coordinator guidance. Source inspection and editing may use
ordinary shell tools. Keep the research logic study-owned and all computation
on this Mac. Do not alter read-only inputs, raise ceilings or retrieve scorer
answers. Label partial work honestly when a stopping condition is reached.

Deliver `REPORT.md`, `review.json`, `REPRODUCE.md`, `artifact-manifest.json` and
`submission.json`. The submission must have `task_id: "ema-schedule"`,
`execution_status` (`complete`, `partial` or `blocked`), relative paths in
`manuscript`, `review`, `artifact_manifest` and `measurements`, and `reproduce`
and `recompute` objects with `argv` string arrays and relative `cwd`. Full
reproduction must set up a fresh environment and perform training/sampling;
recomputation must derive the reported analysis from retained raw evidence.
Use the common `MEASUREMENTS.md` interchange format and document other artifacts so an independent reviewer can
check the science without trusting narrative assertions. Separate pilot and
confirmation evidence and do not pool duplicate agent runs as new scientific
replicates. This is a bounded follow-up, not an exact upstream paper replication.
