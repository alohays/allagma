"""Evidence-linked English report, claims, revision-bound critique and package."""
from __future__ import annotations
import json
from pathlib import Path
import platform
import subprocess
import sys
from common import ROOT,CAMPAIGN,write,ref,sha,now
from workflow import account

def interval(e):
    return f"{e['mean']:.6f} [{e['ci95'][0]:.6f}, {e['ci95'][1]:.6f}]"

def main():
    ledger=account()
    summary=json.loads((ROOT/'analysis/summary.json').read_text())
    measurements=json.loads((ROOT/'analysis/measurements.json').read_text())
    verification=json.loads((ROOT/'verification/verification.json').read_text())
    assert summary['complete'] and len(measurements['runs'])==32 and verification['passed']
    assert verification['states_regenerated']==96
    effects=summary['effects']
    primary=[e for e in effects if e['contrast']=='cell']
    sc=[e for e in effects if e['contrast']=='schedule_cosine_minus_constant']
    interactions=[e for e in effects if e['contrast']=='interaction']
    favor=sum(e['mean']<0 for e in primary)
    positive_schedule=sum(e['mean']>0 for e in sc)
    unadjusted_below=sum(e['ci95'][1]<0 for e in primary)
    within_interaction=sum(e['ci95'][0]<=0<=e['ci95'][1] for e in interactions)
    gmm=[(c,v) for c in measurements['runs'] if c['dataset']=='gmm8' for v in ('raw','ema099','ema0999')]
    counts=[c['metrics'][v]['covered_modes'] for c,v in gmm]
    inliers=[c['metrics'][v]['inlier_fraction'] for c,v in gmm]
    resource_text=f"{ledger['charged_seconds']['compute']:.2f} s compute and {ledger['charged_seconds']['setup']:.2f} s setup across {ledger['compute_requests']} completed compute requests before this packaging request"
    tables=[]
    tables.append('| Dataset | Policy | Updates | Weight | Mean SW1 |\n|---|---|---:|---|---:|')
    for e in summary['absolute_sw1']:
        if e['contrast']=='cell':tables.append(f"| {e['dataset']} | {e['schedule']} | {e['updates']} | {e['variant']} | {e['mean']:.6f} |")
    absolute_table='\n'.join(tables)
    lines=['| Dataset | Policy | Updates | EMA | Mean Δ [95% t interval] | Seeds with Δ < 0 | Sign-flip p |',
           '|---|---|---:|---|---|---:|---:|']
    for e in primary:
        lines.append(f"| {e['dataset']} | {e['schedule']} | {e['updates']} | {e['variant']} | {interval(e)} | {sum(v<0 for v in e['values'])}/4 | {e['sign_flip_p']:.3f} |")
    primary_table='\n'.join(lines)
    lines=['| Dataset | EMA | Contrast in Δ | Mean [95% t interval] |','|---|---|---|---|']
    for e in effects:
        if e['contrast']=='cell':continue
        description={'schedule_cosine_minus_constant':f"Cosine − constant at {e.get('updates','')} updates",
                     'duration_10000_minus_5000':f"10k − 5k under {e.get('schedule','')}",
                     'interaction':'(Cosine − constant) at 10k − at 5k'}[e['contrast']]
        lines.append(f"| {e['dataset']} | {e['variant']} | {description} | {interval(e)} |")
    contrast_table='\n'.join(lines)
    lines=['| Policy | Updates | Weight | Covered modes range | Mean inlier fraction |','|---|---:|---|---|---:|']
    for e in summary['coverage']:
        if e['metric']!='inlier_fraction':continue
        mode=next(m for m in summary['coverage'] if m['metric']=='covered_modes' and all(m[k]==e[k] for k in ('schedule','updates','variant')))
        lines.append(f"| {e['schedule']} | {e['updates']} | {e['variant']} | {min(mode['values'])}–{max(mode['values'])} | {e['mean']:.6f} |")
    coverage_table='\n'.join(lines)
    interpretation=(ROOT/'INTERPRETATION.md').read_text()
    report=f'''# Weight EMA after separating duration from learning-rate policy

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
EMA-minus-raw Sliced W1 was negative in {favor}/16 cell-level mean comparisons;
{unadjusted_below}/16 unadjusted 95% seed-level intervals lay below zero. The
cosine-minus-constant contrast in that paired difference was positive in
{positive_schedule}/8 comparisons. All findings are conditional on this small
design; no EMA improvement was required for completion.

{interpretation}

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

{primary_table}

**Table 2. Prespecified schedule, duration and interaction contrasts in Δ.**
Positive schedule contrasts mean that EMA's relative advantage is smaller
(or its disadvantage larger) under cosine. Of four interaction intervals,
{within_interaction} include zero; uncertainty must be considered alongside the estimates.

{contrast_table}

**Table 3. Absolute distribution quality.** Means over the same four seeds;
state-level intervals and per-seed values are retained in the analysis.

{absolute_table}

**Table 4. GMM8 diagnostics.** Coverage spans {min(counts)}–{max(counts)} modes
over all 48 GMM8 model states; individual-state inlier fractions span
{min(inliers):.6f}–{max(inliers):.6f}. Saturated coverage is a ceiling effect,
not evidence of equivalent distributions or correct mixture masses.

{coverage_table}

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
The receipt ledger records {resource_text}. Setup and computation used the
common local broker, one worker at a time. No resource ceiling was expanded.

[Separate reanalysis](reanalysis/summary.json) reproduces all numerical outputs
and the main figure byte-for-byte from retained raw evidence. The
[verification record](verification/verification.json) independently recomputes
SW1 and coverage arithmetic, checks seed-level intervals and generates all 96
states' samples from saved weights and recorded noise. Maximum independent SW1
disagreement was {verification['max_metric_abs_error']:.3g}; maximum regenerated
coordinate disagreement was {verification['max_sample_abs_error']:.3g}
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
'''
    (ROOT/'REPORT.md').write_text(report)
    claims=[]
    descriptions=[('design-completion','All 32 specified confirmation cells and 96 model states were executed with fixed matched-seed controls.','supported',['analysis/measurements.json','verification/verification.json']),
        ('paired-quality',f'EMA-minus-raw mean SW1 is negative in {favor}/16 cells; {unadjusted_below}/16 unadjusted intervals lie below zero.','supported',['analysis/summary.json']),
        ('schedule-policy',f'Cosine-minus-constant contrasts in EMA-minus-raw SW1 are positive in {positive_schedule}/8 comparisons; Table 2 retains all estimates and uncertainty.','supported',['analysis/contrasts.json']),
        ('interaction',f'{within_interaction}/4 unadjusted interaction intervals include zero; the dataset/decay-specific interactions are reported without a universal mechanism claim.','supported',['analysis/contrasts.json']),
        ('gmm-coverage',f'GMM8 coverage spans {min(counts)}–{max(counts)} modes and inlier fractions span {min(inliers):.6f}–{max(inliers):.6f}; saturated counts do not establish equivalence.','supported',['analysis/measurements.json','analysis/summary.json']),
        ('verification','All 96 model states regenerate retained samples and separate analysis reproduces numerical outputs and figures.','supported',['verification/verification.json'])]
    for name,text,status,support in descriptions:
        claims.append({'schema_version':'0.2','record_type':'ClaimRecord','claim_id':name,'text':text,
            'supporting':[ref(ROOT/p) for p in support],'contradicting':[],
            'dependencies':[ref(ROOT/'analysis/record.json'),ref(ROOT/'analysis/raw-manifest.json'),ref(ROOT/'PROTOCOL.md')],
            'scope':'Prespecified synthetic datasets, four matched seeds per dataset, two schedule policies and durations.',
            'limitations':['Small n; unadjusted multiplicity; no endpoint mechanism attribution','Same-assistant critique and deterministic checks are not independent scientific peer review'],
            'status':status,'supersedes':None})
    write(ROOT/'claims.json',claims)
    findings=[
        'The factorial design addresses the original duration/schedule confounding: cosine-5k is trained independently to its endpoint, and constant-5k is a valid checkpoint of the same constant policy. Matched input hashes support paired comparisons.',
        'Uncertainty remains weak at four seeds. Student t intervals rely on a seed-level approximation, and exact two-sided sign-flip p-values cannot be below 0.125. The report labels intervals descriptive and avoids declaring universal statistical significance.',
        'Multiplicity is substantial: 16 primary effects and 20 policy/duration/interaction contrasts are examined without simultaneous correction. The report discloses this; selecting a best decay would require new seeds.',
        'The treatment is an entire optimizer policy. Endpoint rates, cumulative step size, optimization noise and effective averaging lag change together. A terminal-learning-rate mechanism is not identified by this design, and the report does not claim one.',
        f'GMM8 coverage ranges {min(counts)}–{max(counts)}. If saturated, this statistic cannot establish equal sample quality; the retained mode counts and inlier fractions are necessary diagnostics. SW1 and mass allocation remain scientifically distinct.',
        'Saved-weight regeneration and byte-identical reanalysis establish internal reproducibility on this environment. They do not independently validate the scientific assumptions or demonstrate cross-platform identical training. The second full retraining command is provided but not conflated with the performed sample-regeneration check.',
        'The first interrupted attempt and MPS initialization failure were excluded with receipts retained, not erased. The memory repair lowered a watermark and did not relax the broker cap. No confirmation seed was used for implementation decisions.',
        'The final cosine update applies a rate infinitesimally above zero under the supplied indexing rule. This is frozen and disclosed; readers should distinguish it from a protocol using exactly zero during the last optimizer step.',
        'The source map is offline and some historical upstream provenance files are absent from supplied materials. The report limits attribution to the supplied adaptation and does not imply independent upstream verification.',
        'Reviewer independence is absent: this is a same-assistant substantive critique plus a deterministic locked checklist. Assurance is provisional for scientific judgment, not independent peer review.'
    ]
    digest=sha(ROOT/'REPORT.md')
    critique='# Substantive critique of report-r1\n\nMaterial: `REPORT.md`, SHA-256 `'+digest+'`.\n\nReviewer: the same Codex assistant, with the locked deterministic reviewer/checklist adapter. Scientific assurance is provisional, not independent.\n\n'
    critique+='\n\n'.join(f'{i+1}. {finding}' for i,finding in enumerate(findings))
    critique+='\n\nDisposition: pass for the bounded requested package, with the stated inferential and review limitations. No required scientific cell is omitted. This is not approval for a universal EMA claim or external publication.\n'
    (ROOT/'CRITIQUE.md').write_text(critique)
    lock=json.loads((CAMPAIGN/'lock.yaml').read_text());bundle=ROOT/'.allagma/bundles'/lock['bundle_id']
    sys.path.insert(0,str(bundle))
    from allagma.contracts import validate_record
    from allagma.campaigns import audit_evidence
    for claim in claims:validate_record(claim)
    checked=audit_evidence(ROOT,claims)
    for record_path in [CAMPAIGN/'study.json',CAMPAIGN/'context.json',ROOT/'analysis/record.json',*CAMPAIGN.glob('specs/*.json'),*(ROOT/'artifacts').glob('*/*/*/attempts/*/record.json')]:
        validate_record(json.loads(record_path.read_text()))
    reviewdir=ROOT/'evidence/review-r1';reviewdir.mkdir(exist_ok=False)
    review_input={'study':str(ROOT),'material':ref(ROOT/'REPORT.md'),'claims':claims,
        'criteria':['Scientific validity within specified scope','Factorial and seed controls','Uncertainty and multiplicity','Evidence and numerical reproduction','Disclosure and limitations']}
    write(reviewdir/'input.json',review_input)
    command=[sys.executable,str(bundle/'adapters/reviewer-checklist/review.py'),str(reviewdir/'input.json'),str(reviewdir/'adapter-result.json')]
    run=subprocess.run(command,capture_output=True,text=True)
    write(reviewdir/'execution.json',{'argv':command,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
    assert run.returncode==0
    adapter=json.loads((reviewdir/'adapter-result.json').read_text());assert adapter['verdict']=='pass'
    write(reviewdir/'transitive-audit.json',{'references_verified':len(checked),'passed':True})
    review={'schema_version':'0.2','record_type':'ReviewRecord','review_id':'report-r1-review',
        'reviewer':'Same Codex assistant plus reviewer/checklist from campaign lock','backend':'Codex scientific self-critique and deterministic local Python adapter',
        'backend_version':platform.python_version(),'material':ref(ROOT/'REPORT.md'),'criteria':review_input['criteria'],
        'verdict':'pass','findings':findings,'trace':[ref(ROOT/'CRITIQUE.md'),ref(ROOT/'verification/verification.json'),*[ref(p) for p in sorted(reviewdir.iterdir())]],
        'assurance':'provisional','coverage':adapter['coverage']+f' Also {len(checked)} transitive evidence references, raw-data reanalysis, all-state sample regeneration and same-assistant methodological critique. No independent scientific peer review.'}
    validate_record(review);write(ROOT/'review.json',review)
    submission={'task_id':'ema-schedule','execution_status':'complete','manuscript':'REPORT.md','review':'review.json',
        'artifact_manifest':'artifact-manifest.json','measurements':'analysis/measurements.json',
        'reproduce':{'argv':['python3','study/dispatch.py','--fresh','--environment','.venv-reproduce','--base','reproduction/artifacts','--analyze-out','reproduction/analysis'],'cwd':'.'},
        'recompute':{'argv':['python3','inputs/compute.py','--category','compute','--label','recompute-retained','--timeout','60','--','.venv/bin/python','study/analyze.py','--base','artifacts','--out','recomputed-analysis'],'cwd':'.'},
        'sample_regeneration':{'argv':['python3','inputs/compute.py','--category','compute','--label','verify-saved-weights','--timeout','60','--','.venv/bin/python','study/verify.py','--out','regenerated-check'],'cwd':'.'},
        'completion_assessment':'All 32 cells, raw evidence, checkpoints, paired uncertainty, figure, retained-data reanalysis and all-state sample regeneration completed. Scientific critique is provisional and self-authored; no independent peer review or universal mechanism claim.',
        'report_revision':'report-r1'}
    write(ROOT/'submission.json',submission)
    write(CAMPAIGN/'state.json',{'phase':'audit','execution_status':'completed','assurance':'provisional','protocol_revision':'v1','material':ref(ROOT/'REPORT.md'),'review':ref(ROOT/'review.json')})
    manifest()
    print(json.dumps({'execution_status':'complete','material_sha256':digest,'transitive_references_checked':len(checked),'resource_accounting':resource_text},indent=2))

def manifest():
    files=[]
    for folder in ('study','artifacts','campaigns','analysis','reanalysis','verification','evidence','dispatch-logs','.compute/requests','.compute/responses','inputs/materials'):
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                files.append(path)
    files += [ROOT/name for name in ('REPORT.md','PROTOCOL.md','INTERPRETATION.md','CRITIQUE.md','REPRODUCE.md','review.json','claims.json','submission.json','LICENSE-AI-SCIENTIST','inputs/BRIEF.md','inputs/COMPUTE.md','inputs/RESOURCES.json','inputs/compute.py')]
    inventory=[{**ref(p),'bytes':p.stat().st_size} for p in sorted(set(files))]
    write(ROOT/'artifact-manifest.json',{'format':'ema-artifact-manifest-v1','created_at':now(),'files':inventory,
        'exclusions':['Virtual environments and caches','This manifest itself','Broker responses produced after manifest creation; authoritative controller receipts remain permanent'],
        'total_retained_bytes':sum(f['bytes'] for f in inventory)})

if __name__=='__main__':main()
