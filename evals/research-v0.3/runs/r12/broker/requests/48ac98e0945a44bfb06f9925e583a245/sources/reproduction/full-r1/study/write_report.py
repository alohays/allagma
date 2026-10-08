"""Generate manuscript tables and claim ledger from verified analysis only."""
import json
from pathlib import Path
from common import ROOT,CAMP,read,write,ref,sha

def fmt(x):return 'NA' if x is None else f'{x:.6f}'
def interval(x):return 'NA' if not x else f'[{x[0]:.6f}, {x[1]:.6f}]'

def main():
    s=read(ROOT/'analysis/summary.json');v=read(ROOT/'evidence/verification.json')
    assert s['complete'] and v['status']=='pass' and v['complete_cells']==32 and v['regenerated_states']==96
    assert read(ROOT/'recomputed-r1/comparison.json')['status']=='pass'
    replay_path=ROOT/'reproduction/full-r1/comparison.json'
    replay=read(replay_path) if replay_path.exists() else None
    effects=s['effects']; contrasts=s['contrasts'];measure=read(ROOT/'analysis/measurements.json')['runs']
    findings={'negative_mean_effects':sum(e['mean']<0 for e in effects),
      'negative_intervals':sum(e['ci95'][1]<0 for e in effects),'positive_intervals':sum(e['ci95'][0]>0 for e in effects),
      'positive_schedule_means':sum(e['mean']>0 for e in contrasts if e['contrast']=='schedule'),
      'schedule_intervals_above_zero':sum(e['ci95'][0]>0 for e in contrasts if e['contrast']=='schedule'),
      'interaction_intervals_excluding_zero':sum(e['ci95'][0]>0 or e['ci95'][1]<0 for e in contrasts if e['contrast']=='interaction')}
    cov=[r['metrics'][a]['covered_modes'] for r in measure if r['dataset']=='gmm8' for a in ['raw','ema099','ema0999']]
    findings['coverage_range']=[min(cov),max(cov)]
    findings['max_regeneration_error']=max(x['regeneration_max_abs_error'] for r in v['checks'] for x in r['variants'].values())
    write(ROOT/'analysis/report-numbers.json',findings)
    effectrows='\n'.join(f"| {e['dataset']} | {e['updates']} | {e['schedule']} | {e['variant']} | {fmt(e['mean'])} | {interval(e['ci95'])} | {sum(x<0 for x in e['values'])}/4 | {e['signflip_p']:.3f} |" for e in effects)
    contrastrows='\n'.join(f"| {e['dataset']} | {e['variant']} | {e['contrast']} | {e['at']} | {fmt(e['mean'])} | {interval(e['ci95'])} | {e['signflip_p']:.3f} |" for e in contrasts)
    covrows='\n'.join(f"| {e['updates']} | {e['schedule']} | {e['variant']} | {e['covered_modes']['mean']:.2f} | {e['inlier_fraction']['mean']:.4f} | {interval(e['inlier_fraction']['ci95'])} |" for e in s['coverage'])
    absolute=[]
    for d in ['moons','gmm8']:
        for T in [5000,10000]:
            for P in ['constant','cosine']:
                rr=[r for r in measure if (r['dataset'],r['updates'],r['schedule'])==(d,T,P)]
                means=[sum(r['metrics'][a]['sw1'] for r in rr)/4 for a in ['raw','ema099','ema0999']]
                absolute.append(f"| {d} | {T} | {P} | "+' | '.join(fmt(x) for x in means)+' |')
    absolute_rows='\n'.join(absolute)
    interpretation=(ROOT/'INTERPRETATION.md').read_text()
    replay_text=('Full reproduction in a fresh environment also completed all 24 training trajectories and 32 cells; '
       'the [comparison](reproduction/full-r1/comparison.json) checks every saved weight and sample array against the original. '
       'These duplicate runs are verification, not additional seeds.' if replay and replay['status']=='pass' else
       'A full fresh-environment reproduction command is supplied; no claim of a completed second full retraining is made.')
    text=f'''# Weight EMA under crossed training duration and learning-rate policy

**AI disclosure and scope.** Code adaptation, execution orchestration, analysis,
figures, manuscript and critique were generated with OpenAI Codex. Scientific
mechanisms derive from the supplied Allagma study and pinned SakanaAI/AI-Scientist
template. The [source license](LICENSE-AI-Scientist) is retained. This is a bounded
follow-up, without a novelty, universal EMA-benefit, or exact upstream replication
claim. The critique is by the same assistant, with deterministic artifact checks;
it is not independent scientific peer review. Material revision: **material-r1**.

## Question and result

The supplied study evaluated 5,000 and 10,000 updates along one cosine schedule,
confounding training duration with position in that schedule. We crossed terminal
duration with constant and duration-specific cosine policies on moons and GMM8.
All 32 required cells (four seeds per dataset) and all 96 raw/EMA model states
completed. EMA had a negative mean paired SW1 difference in
{findings['negative_mean_effects']} of 16 dataset/duration/policy/decay comparisons;
{findings['negative_intervals']} unadjusted intervals lay below zero and
{findings['positive_intervals']} lay above zero. These counts are descriptive,
not a multiplicity-adjusted discovery claim.

{interpretation}

## Frozen design and execution

The [protocol](campaigns/ema-schedule-v1/protocol.json),
[qualification](campaigns/ema-schedule-v1/attempts/pilot-a005/pilot.json),
[forecast](campaigns/ema-schedule-v1/forecast.json), and
[confirmation freeze](campaigns/ema-schedule-v1/confirmation-freeze.json) precede
any confirmation run. Pilot seeds were 71 (moons) and 81 (GMM8); confirmation
seeds were 4001–4004 and 5001–5004. Device selection used runtime alone under the
frozen rule and selected CPU. MPS also passed the final pilot. The CPU full-work
forecast was 469.88 seconds, including 15% headroom and a verification reserve,
against 1,778.53 computation seconds remaining before confirmation.

Every trajectory uses the supplied 296,450-parameter residual denoiser, float32,
batch size 256, AdamW (default betas 0.9/0.999 and epsilon 1e-8), weight decay
0.01, gradient clipping 0.5, and initial learning rate 0.0003. The constant
policy stays at that rate. Cosine uses lr(u)=0.0003[1+cos(pi*u/T)]/2 for update
indices u=0,...,T−1; its zero-rate boundary is u=T, and the last applied rate is
near zero. The T=5,000 and T=10,000 cosine runs start separately from the same
initial weights. Only the constant trajectory supplies both durations. This is
an intervention on the whole learning-rate path, not just its endpoint.

EMA0.99 and EMA0.999 start as copies of initial raw weights and update after
every optimizer step without warmup, sparse updates, or bias correction. The
supplied 100-step cosine DDPM noise schedule, beta cap 0.999 and clean-sample
clip [−6,6] are unchanged. Training uses 100,000 synthetic draws per seed; all
conditions share initialization and the actual batch-index, training-noise and
diffusion-time prefixes. Held-out draws and the generation-noise tensor are
also identical within dataset/seed across all conditions and states. Evaluation
uses 2,048 held-out and 2,048 generated points per model state. Evaluation never
consumes the training random stream.

The primary metric is the supplied empirical Sliced Wasserstein-1 with 128
directions and projection seed 7321, computed in float64. Define
D=SW1(EMA)−SW1(raw), so negative values favor EMA. At fixed duration the schedule
contrast is D(cosine)−D(constant). Under fixed policy the duration contrast is
D(10,000)−D(5,000). The interaction is the schedule contrast at 10,000 minus the
schedule contrast at 5,000. Positive schedule contrasts mean less apparent EMA
benefit under cosine. Contrasts of absolute SW1 for all three variants are also
retained in [contrasts.json](analysis/contrasts.json).

The independent unit is seed within dataset. Each interval is the paired mean
±t(0.975,3)·SD/√4. All 16 EMA-effect and 20 factorial-contrast intervals are
unadjusted and descriptive; secondary absolute-SW1 and coverage summaries add
further multiplicity. The exact two-sided sign-flip sensitivity has minimum
p=0.125 with four pairs, under sign exchangeability. Leave-one-seed-out means
are retained. Points, projection directions, checkpoints, and retries are not
independent replicates. No practical-equivalence threshold was specified.

## Absolute quality and paired EMA effects

| Dataset | Updates | Policy | Raw SW1 | EMA0.99 SW1 | EMA0.999 SW1 |
| --- | ---: | --- | ---: | ---: | ---: |
{absolute_rows}

These are four-seed means; all raw seed values are in
[seed-metrics.csv](analysis/seed-metrics.csv).

| Dataset | Updates | Policy | EMA | Mean D | 95% t interval | Seeds D<0 | Sign-flip p |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: |
{effectrows}

![Paired EMA effects](analysis/main-figure.png)

**Figure 1.** Dots show the four independent seed differences, diamonds their
mean, and bars the unadjusted 95% t interval. The PDF and figure source are
[retained](analysis/main-figure.pdf); the same analysis command recreates them.

## Schedule, duration and interaction contrasts

| Dataset | EMA | Contrast | Fixed level | Mean contrast | 95% t interval | Sign-flip p |
| --- | --- | --- | --- | ---: | --- | ---: |
{contrastrows}

Each entry is computed within seed before averaging. Missing adjustment for
multiple comparisons and the small seed count prohibit treating individual
interval exclusions as broad proof. The complete paired values are in
[seed-contrasts.csv](analysis/seed-contrasts.csv).

## GMM8 coverage and inliers

A draw is an inlier when it lies within 0.45 of its nearest original mixture
center. A mode is covered at 21 or more inlier draws, which is at least 1% of
all 2,048 generated draws. The denominator is never restricted to inliers.
Across retained GMM8 states, coverage ranged from {min(cov)} to {max(cov)} modes.
Coverage can saturate at eight and cannot establish accurate density, mixture
weights, or equivalence. Exact eight-mode counts and inlier counts are retained
for every state in [measurements](analysis/measurements.json).

| Updates | Policy | State | Mean covered modes | Mean inlier fraction | 95% t interval for inlier fraction |
| --- | --- | --- | ---: | ---: | --- |
{covrows}

## Recovery, verification and completion

The first marked attempt was interrupted by the broker during imports, before
training, and is retained unchanged. Three further pre-training pilot failures
concerned JSON boolean serialization, an exact-zero floating-point assertion,
and an incompatible MPS low watermark. These were repaired and qualification
rerun under new attempt IDs; the broker's high watermark cap was not increased.
All failures and the successful fifth pilot remain in the
[recovery record](campaigns/ema-schedule-v1/RECOVERY.md) and
[run manifest](campaigns/ema-schedule-v1/run-manifest.json). No failed or pilot
attempt enters confirmation analysis.

[Independent numerical checks](evidence/verification.json) recomputed SW1 and
coverage with a separate vectorized implementation, checked actual matched
inputs and all state keys/buffers, and regenerated samples from all 96 saved
states. Maximum sample discrepancy was {findings['max_regeneration_error']:.1e}.
[Separate-directory recomputation](recomputed-r1/comparison.json) reproduced
the numerical summary, measurements, and contrasts exactly from retained raw
evidence. {replay_text}

The main experiment performed 200,000 optimizer updates across 24 trajectories;
32 cells and 96 states are accounted for. Full command lines, environment,
source hashes, arrays and checkpoints are linked by the
[raw manifest](analysis/raw-manifest.json), [artifact manifest](artifact-manifest.json),
and [reproduction guide](REPRODUCE.md). All setup and scientific execution used
the supplied broker. Its ceilings were 1,800 computation seconds, 300 setup
seconds and 64 computation requests. [Resource usage](evidence/resource-usage.json)
records a named cutoff before final packaging checks; the final check's receipt
is retained separately in `.compute/responses/`.

## Limitations and critique

Four seeds produce fragile t intervals and coarse sign-flip sensitivity. The
intervals describe variation across the jointly seeded training and evaluation
process, not a decomposition of training randomness and finite-sample metric
noise. Shared held-out points and generation noise improve pairing but do not
remove measurement error. No independent evaluation-noise repetition or
sample-size sensitivity study was performed. The fixed 128 directions define
the measured estimand and do not establish equality in every projection.

Crossing policies and terminal duration resolves the prior design's missing
cells. It does not isolate a mechanism: changing cosine duration also changes
its full rate path, cumulative step size, and optimization history. Both cosine
conditions have a near-zero terminal learning rate, yet their trajectories
differ. Neither endpoint rate nor the interaction alone proves that smoothing,
EMA lag, convergence, or noise suppression caused the pattern. These would need
additional controlled interventions. No decay was selected as universally best.

Coverage saturation is a weak diagnostic of density quality. This synthetic
two-dimensional model, the chosen optimizer, two durations and two EMA decays
do not support claims about image diffusion or other training scales. The
supplied prior report is contextual evidence, not newly verified historical
data. Literature access was offline, and bibliographic metadata was inherited
from the supplied source. The named [review](review.json) states its same-author
and deterministic scope; it is not an independent scientific review.

## Sources

1. Supplied Allagma `ema-2d-diffusion` study at commit `6d2daf0`; source and
   support limitations mapped in [SCOPE.md](SCOPE.md).
2. SakanaAI, AI-Scientist 2D diffusion template, commit
   `1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb`; supplied
   [reference note](inputs/materials/prior-study/REFERENCE.md) and source license.
3. Ho, Jain and Abbeel (2020), *Denoising Diffusion Probabilistic Models*,
   arXiv:2006.11239 (context cited by the supplied source).
4. Nichol and Dhariwal (2021), *Improved Denoising Diffusion Probabilistic Models*,
   arXiv:2102.09672 (cosine diffusion schedule context).
5. PyTorch reproducibility and MPS documentation, as identified in the supplied
   reference note; local installed versions are recorded in the verification.
'''
    report=ROOT/'REPORT.md';assert not report.exists();report.write_text(text)
    summaryref=ref(ROOT/'analysis/summary.json');verificationref=ref(ROOT/'evidence/verification.json')
    claims=[]
    for cid,claim,support,status in [
       ('C1-design-completion','All 32 crossed confirmation cells and 96 states completed with matched within-seed inputs.', [ref(ROOT/'analysis/measurements.json'),verificationref],'supported'),
       ('C2-paired-effects',f"Negative observed mean EMA differences in {findings['negative_mean_effects']} of 16 comparisons; all effects and seed uncertainty reported.",[summaryref],'supported'),
       ('C3-factorial-contrasts','The schedule, duration and interaction tables report within-seed contrasts of EMA-minus-raw SW1, with uncertainty and no endpoint-only mechanism inference.',[summaryref,ref(ROOT/'analysis/contrasts.json')],'supported'),
       ('C4-coverage',f'GMM8 covered-mode counts range from {min(cov)} to {max(cov)} under the original threshold; counts do not establish density equivalence.',[summaryref,verificationref],'supported'),
       ('C5-verification','Retained-data recomputation agrees and all 96 saved states regenerate their sample arrays.',[verificationref,ref(ROOT/'recomputed-r1/comparison.json')],'supported')]:
        claims.append({'schema_version':'0.2','record_type':'ClaimRecord','claim_id':cid,'text':claim,'supporting':support,'contradicting':[],
          'dependencies':[ref(CAMP/'protocol.json'),ref(CAMP/'confirmation-freeze.json'),ref(ROOT/'analysis/raw-manifest.json')],
          'scope':'This frozen two-dataset, four-seed, two-duration, two-policy follow-up only.',
          'limitations':['Unadjusted multiplicity','Four independent seeds per dataset','Finite heldout/generated samples and fixed projection directions','No mechanistic or universal benefit inference','Same-author critique; no independent peer review'],
          'status':status,'supersedes':None})
    if replay and replay['status']=='pass':
        claims.append({'schema_version':'0.2','record_type':'ClaimRecord','claim_id':'C6-full-reproduction','text':'A fresh environment reran all 24 training trajectories and matched all 32 cells without adding scientific replicates.',
          'supporting':[ref(replay_path)],'contradicting':[],'dependencies':[ref(CAMP/'confirmation-freeze.json')],
          'scope':'Pinned local software and CPU backend on this Mac.','limitations':['Cross-platform equality not tested','Duplicate runs are verification only'],'status':'supported','supersedes':None})
    write(ROOT/'claims.json',claims)
    print(json.dumps(findings,indent=2))

if __name__=='__main__':main()
