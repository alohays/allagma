# Weight EMA after separating duration from learning-rate policy

**Disclosure and status.** AI-generated/adapted code, analysis, figures, critique
and reporting were produced with OpenAI Codex using the installed, locked Allagma
research workflow. The supplied [AI Scientist Source Code License](LICENSE-AI-SCIENTIST)
applies to the adapted scientific mechanism. This is a completed bounded local
follow-up, not an exact upstream replication or independent scientific peer review.
The material revision is **report-r1**; its exact digest is in [review.json](review.json).

## Abstract

We crossed terminal training duration (5,000 or 10,000 optimizer updates) with
learning-rate policy (constant 0.0003 or cosine over the selected duration),
using the supplied denoiser, two synthetic datasets and four untouched seeds
per dataset. All 32 cells and 96 raw/EMA model states were executed and retained.
EMA-minus-raw Sliced W1 was negative in 14/16 cell-level mean comparisons;
2/16 unadjusted 95% seed-level intervals lay below zero. The
cosine-minus-constant contrast in that paired difference was positive in
8/8 comparisons. All findings are conditional on this small
design; no EMA improvement was required for completion.

The observed relative benefit of EMA depends on the full schedule policy. At
both durations and on both datasets, mean EMA-minus-raw differences favor EMA
more strongly under constant learning rate than at completed cosine endpoints.
Cosine also yields lower raw-weight mean SW1 in every dataset/duration comparison;
the absolute EMA means change less. Thus a smaller EMA-minus-raw difference at a
cosine endpoint does not by itself mean worse absolute EMA quality.

The fixed-duration schedule contrast is clearest descriptively for moons at
5,000 updates: both decays have unadjusted intervals above zero. The GMM8
schedule contrasts and all schedule contrasts at 10,000 updates include zero.
Every duration-contrast interval and every interaction interval includes zero.
The observed schedule gap is smaller at the longer duration in every
dataset/decay comparison, but its interaction uncertainty is too wide to
establish that pattern beyond these seeds. A zero-containing interval is not
evidence of equality, and no endpoint-learning-rate mechanism is identified.


## Question and prior evidence

The [supplied prior report](inputs/materials/prior-study/prior-report.md) compared
5k and 10k checkpoints along one 10k cosine path. It explicitly recognized that
duration and schedule position were confounded. Our factorial intervention
separates terminal duration from the **full learning-rate policy**. Within each
dataset/seed, the two completed cosine durations are separately initialized
trajectories with the same weights and training prefix. The constant trajectory
validly contributes both endpoints. No historical outputs were reused.

## Frozen methods

The [protocol](PROTOCOL.md), [qualification](evidence/qualification.json),
[forecast](evidence/forecast.json) and timestamped [confirmation freeze](campaigns/ema-schedule-v1/confirmation-freeze.json)
precede all confirmation inputs and attempts. Pilot seeds were moons 71 and GMM8
81. Confirmation seeds were moons 4001–4004 and GMM8 5001–5004. Scientific source
hashes remained fixed throughout confirmation. The campaign resolves canonical
methods through bundle `b-9a39b70665ba909edb8abc13` and its retained
[campaign lock](campaigns/ema-schedule-v1/lock.yaml).

Training used MPS float32, the reference 296,450-parameter residual denoiser
(128-dimensional embeddings, width 256, three residual blocks), batch 256,
AdamW weight decay 0.01 and gradient norm clipping 0.5. Both EMA copies start
at the initial raw weights and update every optimizer step with constant decay
0.99 or 0.999, without warmup or bias correction. The unchanged supplied
scientific module uses 100 cosine-scheduled DDPM diffusion steps and clips
predicted clean samples to [-6,6]. The diffusion noise schedule is distinct
from the optimizer learning-rate intervention.

For duration D, optimizer update k applies `0.0003*(1+cos(pi*(k-1)/D))/2` under
cosine, following the supplied reference discretization. The final applied
rate is just above zero; the scheduled rate after D updates is exactly zero.
The constant rate is 0.0003 throughout. These policies differ across the full
trajectory, so the design does not identify a mechanism caused solely by the
terminal learning rate.

Each seed uses 100,000 training draws, 2,048 independent held-out draws and
2,048 generated draws per state. Initialization, replacement minibatch indices,
noise targets, diffusion timesteps, held-out draws and all generation noise are
matched across conditions within seed. Actual training inputs and the canonical
first-5k prefix hash are retained, not just RNG seeds. The held-out and generation
streams are separate from training. Dataset generators and RNG offsets are fully
specified in the protocol and [runner](study/runner.py).

The primary metric is reference empirical Sliced Wasserstein-1 over 128 fixed
directions (projection seed 7321), computed in float64. Lower is better. We define
Δ = SW1(EMA) − SW1(raw), so negative favors EMA. Schedule contrasts are
Δ(cosine,D) − Δ(constant,D); duration contrasts are Δ(policy,10k) − Δ(policy,5k);
the interaction is the 10k schedule contrast minus its 5k counterpart. Analogous
absolute-SW1 contrasts for every state are retained in [contrasts.json](analysis/contrasts.json).

The independent unit is the seed within dataset, n=4. We report paired means,
two-sided 95% Student t intervals (3 df), all per-seed values, leave-one-seed-out
means and exact two-sided sign-flip p-values. Intervals are unadjusted and
descriptive, with limited reliability at n=4. With 16 sign assignments, the
minimum p-value is 0.125. Generated points, projection directions, retries and
shared trajectory checkpoints are not additional independent replicates.

GMM8 coverage counts a mode only when at least 21 of all 2,048 generated draws
are within distance 0.45 of their nearest mixture center. Eight mode counts,
total inlier count and inlier fraction are retained for every state.

## Results

![EMA-minus-raw differences](analysis/main-figure.png)

**Figure 1.** Dots show the four paired seed differences, black diamonds their
means, and bars unadjusted 95% Student t intervals. Blue is constant and orange
is cosine. The complete figure source is [paired-differences.csv](analysis/paired-differences.csv);
the [PDF](analysis/main-figure.pdf) is also retained. Each panel retains its own
vertical scale to show within-panel effects; inspect axis labels when comparing panels.

**Table 1. All primary paired effects.** Values are EMA minus raw.

| Dataset | Policy | Updates | EMA | Mean Δ [95% t interval] | Seeds with Δ < 0 | Sign-flip p |
|---|---|---:|---|---|---:|---:|
| moons | constant | 5000 | ema099 | -0.062730 [-0.101586, -0.023874] | 4/4 | 0.125 |
| moons | cosine | 5000 | ema099 | 0.000576 [-0.000852, 0.002004] | 0/4 | 0.125 |
| moons | constant | 10000 | ema099 | -0.039576 [-0.095603, 0.016451] | 4/4 | 0.125 |
| moons | cosine | 10000 | ema099 | -0.000041 [-0.000232, 0.000150] | 2/4 | 0.750 |
| moons | constant | 5000 | ema0999 | -0.059242 [-0.094880, -0.023604] | 4/4 | 0.125 |
| moons | cosine | 5000 | ema0999 | -0.003576 [-0.009083, 0.001932] | 4/4 | 0.125 |
| moons | constant | 10000 | ema0999 | -0.041781 [-0.092162, 0.008599] | 4/4 | 0.125 |
| moons | cosine | 10000 | ema0999 | 0.000156 [-0.001190, 0.001501] | 2/4 | 0.875 |
| gmm8 | constant | 5000 | ema099 | -0.053400 [-0.169414, 0.062615] | 3/4 | 0.250 |
| gmm8 | cosine | 5000 | ema099 | -0.000242 [-0.000763, 0.000279] | 3/4 | 0.375 |
| gmm8 | constant | 10000 | ema099 | -0.028151 [-0.057218, 0.000915] | 4/4 | 0.125 |
| gmm8 | cosine | 10000 | ema099 | -0.000147 [-0.000531, 0.000237] | 2/4 | 0.500 |
| gmm8 | constant | 5000 | ema0999 | -0.055769 [-0.182917, 0.071380] | 3/4 | 0.250 |
| gmm8 | cosine | 5000 | ema0999 | -0.004116 [-0.011615, 0.003382] | 3/4 | 0.250 |
| gmm8 | constant | 10000 | ema0999 | -0.029281 [-0.066649, 0.008087] | 4/4 | 0.125 |
| gmm8 | cosine | 10000 | ema0999 | -0.000401 [-0.003890, 0.003088] | 2/4 | 0.750 |

**Table 2. Prespecified schedule, duration and interaction contrasts in Δ.**
Positive schedule contrasts mean that EMA's relative advantage is smaller
(or its disadvantage larger) under cosine. Of four interaction intervals,
4 include zero; uncertainty must be considered alongside the estimates.

| Dataset | EMA | Contrast in Δ | Mean [95% t interval] |
|---|---|---|---|
| moons | ema099 | Cosine − constant at 5000 updates | 0.063306 [0.023965, 0.102648] |
| moons | ema099 | Cosine − constant at 10000 updates | 0.039535 [-0.016330, 0.095401] |
| moons | ema099 | 10k − 5k under constant | 0.023154 [-0.037175, 0.083483] |
| moons | ema099 | 10k − 5k under cosine | -0.000617 [-0.002225, 0.000992] |
| moons | ema099 | (Cosine − constant) at 10k − at 5k | -0.023771 [-0.083068, 0.035526] |
| moons | ema0999 | Cosine − constant at 5000 updates | 0.055666 [0.019748, 0.091585] |
| moons | ema0999 | Cosine − constant at 10000 updates | 0.041937 [-0.007833, 0.091707] |
| moons | ema0999 | 10k − 5k under constant | 0.017461 [-0.037112, 0.072034] |
| moons | ema0999 | 10k − 5k under cosine | 0.003731 [-0.001185, 0.008647] |
| moons | ema0999 | (Cosine − constant) at 10k − at 5k | -0.013730 [-0.072011, 0.044551] |
| gmm8 | ema099 | Cosine − constant at 5000 updates | 0.053158 [-0.062767, 0.169083] |
| gmm8 | ema099 | Cosine − constant at 10000 updates | 0.028004 [-0.000909, 0.056917] |
| gmm8 | ema099 | 10k − 5k under constant | 0.025248 [-0.061895, 0.112391] |
| gmm8 | ema099 | 10k − 5k under cosine | 0.000095 [-0.000123, 0.000313] |
| gmm8 | ema099 | (Cosine − constant) at 10k − at 5k | -0.025153 [-0.112347, 0.062040] |
| gmm8 | ema0999 | Cosine − constant at 5000 updates | 0.051652 [-0.070912, 0.174216] |
| gmm8 | ema0999 | Cosine − constant at 10000 updates | 0.028880 [-0.007677, 0.065437] |
| gmm8 | ema0999 | 10k − 5k under constant | 0.026488 [-0.065668, 0.118644] |
| gmm8 | ema0999 | 10k − 5k under cosine | 0.003715 [-0.005093, 0.012524] |
| gmm8 | ema0999 | (Cosine − constant) at 10k − at 5k | -0.022772 [-0.110134, 0.064589] |

**Table 3. Absolute distribution quality.** Means over the same four seeds;
state-level intervals and per-seed values are retained in the analysis.

| Dataset | Policy | Updates | Weight | Mean SW1 |
|---|---|---:|---|---:|
| moons | constant | 5000 | raw | 0.096467 |
| moons | cosine | 5000 | raw | 0.039818 |
| moons | constant | 10000 | raw | 0.076944 |
| moons | cosine | 10000 | raw | 0.035707 |
| moons | constant | 5000 | ema099 | 0.033737 |
| moons | cosine | 5000 | ema099 | 0.040394 |
| moons | constant | 10000 | ema099 | 0.037368 |
| moons | cosine | 10000 | ema099 | 0.035666 |
| moons | constant | 5000 | ema0999 | 0.037225 |
| moons | cosine | 5000 | ema0999 | 0.036242 |
| moons | constant | 10000 | ema0999 | 0.035163 |
| moons | cosine | 10000 | ema0999 | 0.035862 |
| gmm8 | constant | 5000 | raw | 0.126985 |
| gmm8 | cosine | 5000 | raw | 0.070762 |
| gmm8 | constant | 10000 | raw | 0.100678 |
| gmm8 | cosine | 10000 | raw | 0.068164 |
| gmm8 | constant | 5000 | ema099 | 0.073585 |
| gmm8 | cosine | 5000 | ema099 | 0.070520 |
| gmm8 | constant | 10000 | ema099 | 0.072527 |
| gmm8 | cosine | 10000 | ema099 | 0.068017 |
| gmm8 | constant | 5000 | ema0999 | 0.071216 |
| gmm8 | cosine | 5000 | ema0999 | 0.066646 |
| gmm8 | constant | 10000 | ema0999 | 0.071397 |
| gmm8 | cosine | 10000 | ema0999 | 0.067763 |

**Table 4. GMM8 diagnostics.** Coverage spans 8–8 modes
over all 48 GMM8 model states; individual-state inlier fractions span
0.973145–0.994141. Saturated coverage is a ceiling effect,
not evidence of equivalent distributions or correct mixture masses.

| Policy | Updates | Weight | Covered modes range | Mean inlier fraction |
|---|---:|---|---|---:|
| constant | 5000 | raw | 8–8 | 0.976440 |
| constant | 5000 | ema099 | 8–8 | 0.985229 |
| constant | 5000 | ema0999 | 8–8 | 0.982544 |
| cosine | 5000 | raw | 8–8 | 0.985474 |
| cosine | 5000 | ema099 | 8–8 | 0.985107 |
| cosine | 5000 | ema0999 | 8–8 | 0.982422 |
| constant | 10000 | raw | 8–8 | 0.984497 |
| constant | 10000 | ema099 | 8–8 | 0.989502 |
| constant | 10000 | ema0999 | 8–8 | 0.989746 |
| cosine | 10000 | raw | 8–8 | 0.989868 |
| cosine | 10000 | ema099 | 8–8 | 0.989746 |
| cosine | 10000 | ema0999 | 8–8 | 0.990356 |

## Execution, recovery and verification

The first marked scientific attempt was deliberately interrupted by the broker
after 1.53 seconds and is permanently retained. A second pilot attempt failed
before training because PyTorch's default low watermark (1.4) exceeded the
broker's high watermark cap (0.2). The repair lowered the low watermark to 0.1;
no allocation ceiling was raised. Pilot retry identities and the unsuccessful
source snapshots remain available. Neither attempt enters confirmation.

All 12 known-answer/behavior checks passed, including analytic SW1 cases,
coverage thresholds and denominator, EMA interpolation, schedule distinction,
loadable complete state, exact resumed-versus-continuous updates and reference
sample regeneration. Successful pilots ran 1,500 updates each. The frozen
full-work forecast was 818.35 compute seconds including previously charged work,
a safety factor, I/O and verification reserve, against 1,800 seconds allowed.
The receipt ledger records 357.49 s compute and 20.43 s setup across 33 completed compute requests before this packaging request. Setup and computation used the
common local broker, one worker at a time. No resource ceiling was expanded.

[Separate reanalysis](reanalysis/summary.json) reproduces all numerical outputs
and the main figure byte-for-byte from retained raw evidence. The
[verification record](verification/verification.json) independently recomputes
SW1 and coverage arithmetic, checks seed-level intervals and generates all 96
states' samples from saved weights and recorded noise. Maximum independent SW1
disagreement was 2.78e-17; maximum regenerated
coordinate disagreement was 0
(tolerance 1e-6). This saved-weight check does no retraining. A fresh-environment
full retraining command is separately provided in [REPRODUCE.md](REPRODUCE.md).

## Limitations and interpretation boundaries

Four seeds give imprecise uncertainty and no powerful exact two-sided test.
There are 16 primary cell means and 20 schedule/duration/interaction comparisons,
plus supporting absolute metrics; their intervals are not simultaneous guarantees.
Selecting the best EMA decay from these results would require fresh confirmation.
Pairing reduces noise but does not separate initialization, data and generation
variability into distinct population effects. Finite sample SW1 includes
sampling error and is not a debiased population distance.

These conclusions apply to two synthetic 2D distributions, one small denoiser,
one optimizer setup and two full policies. They do not establish universal EMA
benefit, behavior for image diffusion, or an endpoint-learning-rate mechanism.
The nearly zero applied final cosine rate follows the reference discretization,
not a separate terminal-rate intervention. High coverage cannot distinguish
fine distributional errors. Numerical reproducibility is not independent
scientific validation. Critique was generated by the same assistant; the locked
reviewer adapter provides deterministic schema/evidence checks only.

The study was offline. Bibliographic metadata is inherited from the supplied
materials, and historical upstream links/provenance not included in the input
package were not independently verified. The exact supplied scientific source
was preserved and hashed. No novelty claim or exact upstream replication claim
is made. See the [evidence map](evidence/literature-map.json) and
[revision-bound critique](CRITIQUE.md).

## Evidence and references

The [common measurements](analysis/measurements.json), [seed-level values](analysis/seed-level.json),
[full contrasts](analysis/contrasts.json), [raw manifest](analysis/raw-manifest.json),
[AnalysisRecord](analysis/record.json), [claim ledger](claims.json),
[resource receipts](evidence/resource-ledger.json) and [artifact manifest](artifact-manifest.json)
make the empirical statements inspectable. Failed attempts and pilots remain
separate. The [submission](submission.json) distinguishes full reproduction
from recomputation and records completion status.

1. Supplied Allagma EMA study, repository commit `6d2daf0`; local prior report and REFERENCE.md.
2. SakanaAI, AI-Scientist `templates/2d_diffusion`, commit `1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb`; supplied licensed adaptation.
3. Ho, Jain and Abbeel (2020), *Denoising Diffusion Probabilistic Models*, arXiv:2006.11239; contextual citation inherited from materials.
4. Nichol and Dhariwal (2021), *Improved Denoising Diffusion Probabilistic Models*, arXiv:2102.09672; contextual citation inherited from materials.
