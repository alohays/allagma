"""Render an evidence-linked English report from verified machine results."""
import argparse
import json
from pathlib import Path
from common import write_json,ref

def main():
    p=argparse.ArgumentParser();p.add_argument('--analysis',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();directory=Path(args.analysis)
    s=json.loads((directory/'summary.json').read_text()); rows=json.loads((directory/'per-seed.json').read_text())
    def event(e):return str(e['time']) if e['event'] else f">{e['censor_at']} (censored)"
    lines=['| Seed | Decay | Train accuracy | Held-out accuracy | Train CE | Held-out CE | Memorization | Generalization | Lag | Grokking observed |',
           '|---|---:|---:|---:|---:|---:|---:|---|---|---|']
    for r in rows:
        m=r['metrics']; t=r['transition']
        lines.append(f"| {r['seed']} | {r['weight_decay']} | {m['train_accuracy']:.6f} | {m['test_accuracy']:.6f} | {m['train_loss']:.6g} | {m['test_loss']:.6g} | {event(t['memorization'])} | {event(t['generalization'])} | {t['lag'] if t['lag'] is not None else 'unobserved'} | {t['delayed_grokking_observed']} |")
    table='\n'.join(lines)
    paired=['| Seed | Δ held-out accuracy | Δ held-out CE (nats) |','|---|---:|---:|']
    for r in s['per_seed']:paired.append(f"| {r['seed']} | {r['test_accuracy']:.9f} | {r['test_loss']:.9f} |")
    estimates=[]
    for name,u in s['uncertainty'].items():
        estimates.append(f"- {name}: mean {u['mean']:.9f}; SD {u['sd']:.9f}; SE {u['standard_error']:.9f}; 95% paired t interval [{u['ci95_student_t'][0]:.9f}, {u['ci95_student_t'][1]:.9f}]; exact sign-flip p={u['paired_sign_flip_two_sided_p']:.3f}.")
    outcomes=f"{s['memorized_count']}/{s['n_runs']} runs memorized, {s['generalized_count']}/{s['n_runs']} reached the generalization threshold, and {s['delayed_grokking_count']}/{s['n_runs']} met the frozen delayed-grokking criterion."
    q=json.loads(Path('evidence/qualification-a004/qualification.json').read_text())
    text=f'''# Weight decay, memorization and finite-horizon generalization in modular addition

Execution status: **{s['execution_status']}**. This is a local research draft, not an external submission. {s['n_runs']} of eight confirmation cells and {s['n_paired_seeds']} of four paired seeds have verified full-horizon endpoints.

## Question and scope

Does weight decay 1 versus 0 change held-out generalization after memorization in the prescribed MLP, and does a delayed threshold transition occur within 100,000 updates? {outcomes} Endpoint improvement and grokking are assessed separately below. This bounded MLP adaptation is not an exact replication of Power et al.'s transformer experiments and does not establish a general law about regularization.

## Protocol and controls

The immutable [protocol](campaigns/c001/protocol.json), [readable design](campaigns/c001/PROTOCOL.md), [workflow lock](campaigns/c001/lock.yaml), and [code manifest](campaigns/c001/code-manifest.json) precede confirmation. The installed Allagma research recipe was resolved through bundle `b-9a39b70665ba909edb8abc13`, with sequential artifact handoffs and broker-supervised study code.

We enumerate all 97²=9,409 ordered pairs and set targets to `(a+b)%97`. A seed-specific uniform NumPy permutation assigns its first 2,822 indices to training and 6,587 to held-out evaluation. Each seed (1001, 1002, 1003, 1004) shares exactly the same partition and initial weights across weight decay 0 and 1. The bias-free MLP has 194 concatenated one-hot inputs, 128 ReLU hidden units, and 97 outputs (37,248 parameters). Training uses float32 full-batch cross-entropy and PyTorch AdamW: learning rate .001, betas (.9,.98), epsilon 1e-8. All training ran on CPU with one thread. Held-out labels were used only for measurement, never optimization, stopping or tuning.

Both conditions run exactly 100,000 updates. Loss and accuracy are recorded at step zero and every 100 updates. Memorization means train accuracy ≥.99 for three consecutive evaluations; generalization means held-out accuracy ≥.95 for three. Event time is the first point in a qualifying triple; confirmation time is the third. Delayed grokking requires both events, lag ≥1,000 updates, and generalization time ≥2×memorization time. The absolute margin spans ten sampling intervals and the ratio requires a substantial relative delay; these are transparent descriptive conventions, not a universal definition. Unobserved event times and lags remain null. Right-censoring is recorded at 100,000; it does not predict an eventual event. Accuracy is always a fraction, and cross-entropy is in nats.

The independent unit is the seed, n=4. Primary effects are paired decay1-minus-decay0 endpoint differences. Two-sided 95% Student t intervals use three degrees of freedom; an exact enumeration of the 16 paired sign flips is a sensitivity calculation. Four seeds give weak tail estimation and coarse sign-flip evidence (the smallest two-sided p is .125). No pilot or repeated execution is counted as another seed.

## Implementation qualification and recovery

The pilot uses seed 61 only. The first marked scientific request was deliberately interrupted during import; its start record and the broker's `injected_interruption: true` receipt remain retained. A fresh request recovered the pilot. CPU timing succeeded, but that benchmark's later MPS initialization failed because of an allocator ratio configuration; the failed attempt remains excluded. A separate CPU-only 3,000-update pilot and control suite passed before confirmation. No MPS result supports any scientific conclusion.

The [qualification evidence](evidence/qualification-a004/qualification.json) verifies known-answer labels, all class counts, exhaustive/disjoint and repeatable splits, float32 architecture, a closed-form first AdamW update (maximum discrepancy {q['adamw_first_step_max_abs_error']:.3g}), bitwise uninterrupted-versus-resumed training, an independent NumPy cross-entropy formula, uniform/perfect prediction controls, and pilot checkpoint reload. End-to-end pilot timing projected {q['projected_training_seconds']:.1f} seconds for training with evaluations; with a 25% margin and verification reserve, {q['margin_and_verification_seconds']:.1f} seconds fit the 1,800-second computation ceiling. Setup has its separate 300-second ceiling. Source, commands and receipts are retained in the manifest and attempt ledger.

## Results

{table}

The complete values, confirmation times, censor indicators, lags and definition sensitivity are in [{directory}/per-seed.json]({directory}/per-seed.json). Figures show all individual trajectories; no seed is hidden by an aggregate curve.

![Individual learning curves]({directory}/learning-curves.png)

Positive accuracy differences and negative cross-entropy differences favor decay 1:

{chr(10).join(paired)}

{chr(10).join(estimates) if estimates else 'Full-horizon paired uncertainty is unavailable because confirmation is incomplete.'}

These are finite-horizon effects for the sampled seeds. A favorable endpoint difference below the held-out generalization threshold is an improvement in that metric, not threshold-level generalization or grokking. High training accuracy alone establishes neither. The t intervals are parametric descriptions with only four independent observations; the sign-flip calculation is assumption-dependent and cannot resolve conventional two-sided .05 significance at this seed count.

## Sensitivity and verification

The frozen primary analysis remains unchanged. The machine-readable per-seed file varies one component at a time: held-out threshold .90/.99, persistence 1/5, minimum lag 500/5,000, and time ratio 1/5 around the primary .95, 3, 1,000, 2. This checks whether a descriptive classification depends on the definition; it is not model tuning.

All reported endpoints were recomputed in float64 from the retained final logits and labels. The analysis checks every pair, partition, prediction argmax, initialization and curve schedule; it independently instantiates and reloads both the saved PyTorch checkpoint and NPZ weights for **every completed cell**. It also compares a NumPy forward pass using the one-hot identity and checks the optimizer's final update count. Exact coverage and tolerances are in [{directory}/validation.json]({directory}/validation.json). A second output directory reanalysis and the final digest audit are recorded in [verification.json](verification.json). These checks establish deterministic agreement within stated coverage; they do not supply independent peer review.

## Limitations and critique

Four seeds limit population inference and reliability of t intervals. Shared ordered-pair structure means held-out examples are not new algebraic tasks; swapped pairs can lie on different sides of the split. There are only two weight-decay values, one architecture and optimizer configuration, one 30% split fraction, and one finite horizon. Absence of a threshold event by 100,000 does not show it can never occur. Three-point persistence resolves only the first observed qualifying window; it need not imply permanent generalization. Evaluations every 100 updates discretize event times, and first-of-triple timing requires up to 200 later updates to confirm. Numerical reproducibility is qualified for the recorded CPU/software environment, not asserted bitwise across arbitrary hardware or libraries.

The protocol fixed a lag convention before confirmation, but alternative definitions of grokking exist. We do not infer the internal representation or mechanism from these curves. The supplied source README and code establish provenance and transformer context; no network search or full-paper verification was performed. The offline Allagma checklist audits schemas and evidence digests only. The substantive [critique](review.json) is the same agent's review, not an independent scientific review. A second complete fresh-environment training campaign is supplied as a command but is not redundantly executed within this finite budget; retained-data reanalysis is actually executed.

## Reproduction and evidence

[REPRODUCE.md](REPRODUCE.md) gives fresh-environment full-training and retained-data recomputation commands, artifact formats and exact verification coverage. [measurements.json](measurements.json) implements the supplied interchange; [artifact-manifest.json](artifact-manifest.json) identifies retained files by SHA-256. Immutable failed attempts are retained alongside successful evidence. [submission.json](submission.json) records machine-readable execution status and command arrays.

## Reference

Power, A., Burda, Y., Edwards, H., Babuschkin, I., and Misra, V. (2022). *Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets*. arXiv:2201.02177. https://arxiv.org/abs/2201.02177. Supplied MIT-licensed code revision `3d64b1d8c1d595dd8ebdb7771998823f1b14c7b3`; see [literature evidence map](literature.json). Bibliographic metadata verification is distinct from verification of scientific support.
'''
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(text)
    claims=[]
    for name,claim in [('memorization',f"{s['memorized_count']} of {s['n_runs']} confirmation runs met the frozen training memorization criterion."),
                       ('generalization',f"{s['generalized_count']} of {s['n_runs']} confirmation runs met the frozen held-out generalization criterion."),
                       ('grokking',f"{s['delayed_grokking_count']} of {s['n_runs']} confirmation runs met the frozen delayed-grokking criterion.")]:
        claims.append({'schema_version':'0.2','record_type':'ClaimRecord','claim_id':name,'text':claim,
                       'supporting':[ref(directory/'summary.json'),ref(directory/'per-seed.json')],
                       'contradicting':[],'dependencies':[ref(directory/'raw-manifest.json'),ref('campaigns/c001/protocol.json')],
                       'scope':'Prescribed MLP, four paired seeds, 100000-update horizon',
                       'limitations':s['limitations'],'status':'supported' if s['execution_status']=='complete' else 'inconclusive','supersedes':None})
    if s['uncertainty']:
        claims.append({'schema_version':'0.2','record_type':'ClaimRecord','claim_id':'paired-endpoints',
            'text':'Endpoint paired effects are reported with seed-level differences and fragile small-n uncertainty: '+json.dumps(s['uncertainty']),
            'supporting':[ref(directory/'summary.json')],'contradicting':[],
            'dependencies':[ref(directory/'raw-manifest.json'),ref('campaigns/c001/protocol.json')],
            'scope':'Metric differences at exactly 100000 updates; not a mechanism or universal effect',
            'limitations':s['limitations'],'status':'supported','supersedes':None})
    write_json(directory/'claims.json',claims)

if __name__=='__main__':main()
