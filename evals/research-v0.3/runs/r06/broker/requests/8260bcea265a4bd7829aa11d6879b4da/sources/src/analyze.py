"""Recompute every reported numerical analysis from retained evidence; no training."""
import argparse
import csv
import itertools
import json
import math
import os
from pathlib import Path

import study as s


def transition(curve, metric, threshold, sustain):
    for i in range(len(curve) - sustain + 1):
        if all(curve[j][metric] >= threshold for j in range(i, i + sustain)):
            return {'observed': True, 'event_step': curve[i]['step'],
                    'confirmation_step': curve[i + sustain - 1]['step'],
                    'censor_step': None, 'index': i}
    return {'observed': False, 'event_step': None, 'confirmation_step': None,
            'censor_step': curve[-1]['step'], 'index': None}


def outcomes(curve, threshold=.95, sustain=3, lag_min=1000, gate=.5):
    mem = transition(curve, 'train_accuracy', .99, sustain)
    gen = transition(curve, 'test_accuracy', threshold, sustain)
    lag = gen['event_step'] - mem['event_step'] if mem['observed'] and gen['observed'] else None
    at_mem = curve[mem['index']]['test_accuracy'] if mem['observed'] else None
    persists = (all(curve[j]['train_accuracy'] >= .99
                    for j in range(gen['index'], gen['index'] + sustain)) if gen['observed'] else None)
    delayed = bool(lag is not None and lag >= lag_min and (gate is None or at_mem <= gate) and persists)
    return {'memorization': mem, 'generalization': gen, 'lag_updates': lag,
            'lag_censored_lower_bound_updates': curve[-1]['step'] - mem['event_step']
            if mem['observed'] and not gen['observed'] else None,
            'test_accuracy_at_memorization': at_mem, 'training_persists_at_generalization': persists,
            'delayed_grokking': delayed, 'complete_horizon': curve[-1]['step'] == 100000}


def metrics_from_arrays(a):
    np = s.np
    metrics = {}
    for prefix, key in [('train', 'train_indices'), ('test', 'test_indices')]:
        idx = a[key]
        z = a['logits'][idx].astype(np.float64)
        y = a['labels'][idx]
        max_z = z.max(1)
        logsum = max_z + np.log(np.exp(z - max_z[:, None]).sum(1))
        metrics[prefix + '_loss'] = float(np.mean(logsum - z[np.arange(len(idx)), y]))
        metrics[prefix + '_accuracy'] = float(np.mean(a['predictions'][idx] == y))
    return metrics


def verify(run, curve, protocol):
    np, torch = s.np, s.torch
    with np.load(run['arrays'], allow_pickle=False) as archive:
        a = {k: archive[k] for k in archive.files}
    expected_pairs = np.array([(i, j) for i in range(97) for j in range(97)], dtype=np.int64)
    assert np.array_equal(a['pairs'], expected_pairs)
    expected_labels = np.array([(int(i) + int(j)) % 97 for i, j in a['pairs']], dtype=np.int64)
    assert np.array_equal(a['labels'], expected_labels)
    assert a['pairs'].shape == (9409, 2) and a['labels'].shape == (9409,)
    assert a['logits'].shape == (9409, 97) and a['logits'].dtype == np.float32
    assert np.isfinite(a['logits']).all()
    assert a['predictions'].shape == (9409,) and np.issubdtype(a['predictions'].dtype, np.integer)
    assert np.array_equal(a['predictions'], a['logits'].argmax(1))
    tri, tei = a['train_indices'], a['test_indices']
    assert len(tri) == 2822 and len(tei) == 6587
    assert np.array_equal(np.sort(np.r_[tri, tei]), np.arange(9409))
    partition = np.random.Generator(np.random.PCG64(run['seed'])).permutation(9409)
    assert np.array_equal(tri, partition[:2822]) and np.array_equal(tei, partition[2822:])
    with np.load(run['partition'], allow_pickle=False) as p:
        for key in ['pairs', 'labels', 'train_indices', 'test_indices']:
            assert np.array_equal(a[key], p[key])
    assert s.sha(run['initial_weights']) == run['initial_weights_sha256']
    assert run['source_revision'] == protocol['source_revision']
    config = json.loads(Path(run['config']).read_text())
    for key in ['horizon', 'evaluation_interval', 'optimizer', 'dtype', 'device']:
        assert config[key] == protocol[key]
    assert config['seed'] == run['seed'] and config['weight_decay'] == run['weight_decay']
    assert [row['step'] for row in curve] == list(range(0, run['updates'] + 1, 100))
    assert len(curve) == run['updates'] // 100 + 1
    recomputed = metrics_from_arrays(a)
    metric_errors = {key: abs(recomputed[key] - run['metrics'][key]) for key in recomputed}
    curve_errors = {key: abs(recomputed[key] - curve[-1][key]) for key in recomputed}
    assert all(np.isclose(recomputed[k], run['metrics'][k], rtol=1e-10, atol=1e-10) for k in recomputed)
    assert all(np.isclose(recomputed[k], curve[-1][k], rtol=3e-6, atol=3e-6) for k in recomputed)
    # Fresh torch model loaded from the complete checkpoint; all saved pairs evaluated.
    net = s.model(run['seed'], 'cpu')
    checkpoint = torch.load(run['checkpoint'], map_location='cpu', weights_only=True)
    assert checkpoint['step'] == run['updates']
    net.load_state_dict(checkpoint['model'])
    assert checkpoint['curve'] == curve
    opt_group = checkpoint['optimizer']['param_groups'][0]
    assert opt_group['lr'] == .001 and opt_group['betas'] == (.9, .98)
    assert opt_group['eps'] == 1e-8 and opt_group['weight_decay'] == run['weight_decay']
    assert all(int(v['step'].item()) == run['updates'] for v in checkpoint['optimizer']['state'].values())
    x, y, tr, te = s.tensors(run['seed'], 'cpu')
    with torch.no_grad():
        reloaded = net(x).numpy()
    torch_error = float(np.max(np.abs(reloaded - a['logits'])))
    assert np.array_equal(reloaded, a['logits'])
    with np.load(run['weights'], allow_pickle=False) as w:
        assert set(w.files) == {'input_weight', 'output_weight'}
        wi, wo = w['input_weight'], w['output_weight']
    assert wi.shape == (128, 194) and wo.shape == (97, 128)
    assert wi.dtype == wo.dtype == np.float32
    assert np.array_equal(wi, net[0].weight.detach().numpy())
    assert np.array_equal(wo, net[2].weight.detach().numpy())
    # Independent NumPy float64 implementation exploits exactly two active inputs.
    hidden = np.maximum(wi[:, a['pairs'][:, 0]].T.astype(np.float64) +
                        wi[:, 97 + a['pairs'][:, 1]].T.astype(np.float64), 0)
    independent = hidden @ wo.astype(np.float64).T
    numpy_error = float(np.max(np.abs(independent - a['logits'])))
    assert np.allclose(independent, a['logits'], rtol=3e-5, atol=3e-4)
    numpy_prediction_disagreements = int(np.count_nonzero(independent.argmax(1) != a['predictions']))
    assert numpy_prediction_disagreements == 0
    independent_metrics = metrics_from_arrays({**a, 'logits': independent,
                                               'predictions': independent.argmax(1)})
    centered_error = float(np.max(np.abs((independent - independent.mean(1, keepdims=True)) -
                                         (a['logits'].astype(np.float64) - a['logits'].astype(np.float64).mean(1, keepdims=True)))))
    with np.load(run['initial_weights'], allow_pickle=False) as init:
        fresh = s.model(run['seed'], 'cpu')
        assert np.array_equal(init['input_weight'], fresh[0].weight.detach().numpy())
        assert np.array_equal(init['output_weight'], fresh[2].weight.detach().numpy())
    # Count structural overlap: reverse ordered pair observed in training, among held-out pairs.
    train_set = set(map(int, tri))
    reverse_in_training = sum(int(a['pairs'][i, 1]) * 97 + int(a['pairs'][i, 0]) in train_set for i in tei)
    return {'seed': run['seed'], 'weight_decay': run['weight_decay'], 'updates': run['updates'],
            'passed': True, 'metrics': recomputed, 'summary_metric_absolute_errors': metric_errors,
            'curve_metric_absolute_errors': curve_errors, 'torch_reload_max_logit_error': torch_error,
            'numpy_float64_max_logit_error': numpy_error,
            'numpy_float64_max_centered_logit_error': centered_error,
            'numpy_float64_forward_metrics': independent_metrics,
            'numpy_float64_forward_metric_differences': {k: independent_metrics[k] - recomputed[k] for k in recomputed},
            'numpy_prediction_disagreements': numpy_prediction_disagreements,
            'diagnostics_posthoc': {'input_weight_l2': float(np.linalg.norm(wi.astype(np.float64))),
                                   'output_weight_l2': float(np.linalg.norm(wo.astype(np.float64))),
                                   'min_logit': float(a['logits'].min()), 'max_logit': float(a['logits'].max()),
                                   'max_abs_row_mean_logit': float(np.abs(a['logits'].astype(np.float64).mean(1)).max())},
            'heldout_reverse_pair_in_training_count': reverse_in_training,
            'train_label_counts': np.bincount(a['labels'][tri], minlength=97).tolist(),
            'test_label_counts': np.bincount(a['labels'][tei], minlength=97).tolist()}


def paired_summary(values):
    import scipy.stats
    np = s.np
    v = np.array(values, dtype=np.float64)
    n = len(v)
    if not n:
        return {'n': 0, 'mean': None, 'ci95': None, 'sd': None, 'sign_flip_p_two_sided': None}
    mean = float(v.mean())
    if n > 1:
        sd = float(v.std(ddof=1))
        margin = float(scipy.stats.t.ppf(.975, n - 1) * sd / math.sqrt(n))
        ci = [mean - margin, mean + margin]
    else:
        sd, ci = None, None
    reference = [abs(float(np.mean(v * sign))) for sign in itertools.product([-1, 1], repeat=n)]
    p = sum(x >= abs(mean) - 1e-14 for x in reference) / len(reference)
    return {'n': n, 'mean': mean, 'ci95': ci, 'sd': sd, 'degrees_of_freedom': n - 1,
            'sign_flip_p_two_sided': p, 'differences': values,
            'ci_method': 'two-sided Student-t interval on independent seed-level paired differences',
            'sign_flip_assumption': 'exchangeable signs under the null; reference test, not an assigned-treatment design'}


def make_figure(runs, curves, output):
    os.environ.setdefault('MPLCONFIGDIR', str(Path('.tmp/matplotlib').resolve()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors = {0: '#225ea8', 1: '#d95f0e'}
    fig, axes = plt.subplots(4, 2, figsize=(12, 12), sharex=True)
    for row, seed in enumerate([1001, 1002, 1003, 1004]):
        for run in runs:
            if run['seed'] != seed:
                continue
            curve = curves[(seed, run['weight_decay'])]
            steps = [x['step'] for x in curve]
            for col, metric in enumerate(['accuracy', 'loss']):
                ax = axes[row, col]
                for split, style in [('train', '--'), ('test', '-')]:
                    vals = [max(x[split + '_' + metric], 1e-10) if metric == 'loss'
                            else x[split + '_' + metric] for x in curve]
                    ax.plot(steps, vals, style, color=colors[run['weight_decay']], lw=1.25,
                            label='decay %d, %s' % (run['weight_decay'], 'held out' if split == 'test' else 'train'))
                ax.set_xscale('symlog', linthresh=1000)
                ax.set_xlim(0, 100000)
                ax.set_xticks([0, 1000, 10000, 100000], ['0', '1,000', '10,000', '100,000'])
                ax.grid(alpha=.2)
                ax.set_ylabel('Seed %d\n%s' % (seed, 'Accuracy' if metric == 'accuracy' else 'Cross-entropy'))
                if metric == 'accuracy':
                    ax.set_ylim(-.025, 1.025)
                    ax.axhline(.95, color='gray', lw=.6, alpha=.4)
                else:
                    ax.set_yscale('log')
    axes[0, 0].set_title('Individual accuracy curves')
    axes[0, 1].set_title('Individual loss curves (log scale)')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=9, loc='upper center', bbox_to_anchor=(.5, .97), ncol=4)
    for ax in axes[-1]:
        ax.set_xlabel('Optimizer updates (linear to 1,000; logarithmic thereafter)')
    fig.suptitle('Modular addition: matched seeds, full-batch float32 MLP', fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .935))
    fig.savefig(output / 'learning-curves.png', dpi=170)
    fig.savefig(output / 'learning-curves.pdf', metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)


def analyze(args):
    s.imports()
    np = s.np
    root, output = Path(args.root), Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    protocol_path = root / 'frozen/protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for source, expected in protocol['source_hashes'].items():
        assert s.sha(root / 'frozen/source' / source) == expected
    runs, curves, checks, rows = [], {}, [], []
    missing = []
    for seed in protocol['seeds']:
        for wd in protocol['weight_decays']:
            path = root / 'runs' / ('seed-%d-wd-%d' % (seed, wd)) / 'summary.json'
            if not path.exists():
                missing.append({'seed': seed, 'weight_decay': wd})
                continue
            run = json.loads(path.read_text())
            curve = json.loads(Path(run['curve']).read_text())
            check = verify(run, curve, protocol)
            runs.append(run)
            curves[(seed, wd)] = curve
            checks.append(check)
            rows.append({'seed': seed, 'weight_decay': wd, 'updates': run['updates'],
                         **check['metrics'], **outcomes(curve)})
    # Pairing checks use exact files and step-zero metrics, not merely matching seed names.
    for seed in protocol['seeds']:
        pair = [r for r in runs if r['seed'] == seed]
        if len(pair) == 2:
            assert pair[0]['initial_weights_sha256'] == pair[1]['initial_weights_sha256']
            assert s.sha(pair[0]['partition']) == s.sha(pair[1]['partition'])
            assert curves[(seed, 0)][0] == curves[(seed, 1)][0]
    paired = []
    for seed in protocol['seeds']:
        pair = {r['weight_decay']: r for r in runs if r['seed'] == seed and r['updates'] == 100000}
        if len(pair) == 2:
            paired.append({'seed': seed,
                           'test_accuracy_difference_wd1_minus_wd0': pair[1]['metrics']['test_accuracy'] - pair[0]['metrics']['test_accuracy'],
                           'test_loss_difference_wd1_minus_wd0': pair[1]['metrics']['test_loss'] - pair[0]['metrics']['test_loss']})
    uncertainty = {metric: paired_summary([p[metric + '_difference_wd1_minus_wd0'] for p in paired])
                   for metric in ['test_accuracy', 'test_loss']}
    sensitivity = []
    for threshold, sustain, lag, gate in itertools.product([.9, .95, .99], [1, 3, 5], [500, 1000, 5000], [.5, None]):
        for wd in [0, 1]:
            selected = [r for r in runs if r['weight_decay'] == wd and r['updates'] == 100000]
            outcomes_here = [outcomes(curves[(r['seed'], wd)], threshold, sustain, lag, gate) for r in selected]
            sensitivity.append({'test_threshold': threshold, 'sustain': sustain, 'minimum_lag': lag,
                                'test_at_memorization_maximum': gate, 'weight_decay': wd,
                                'n_complete': len(selected),
                                'generalization_events': sum(o['generalization']['observed'] for o in outcomes_here),
                                'delayed_grokking_events': sum(o['delayed_grokking'] for o in outcomes_here),
                                'seed_outcomes': [{'seed': r['seed'], **o} for r, o in zip(selected, outcomes_here)]})
    complete = len(runs) == 8 and all(r['updates'] == 100000 for r in runs)
    summary = {'task_id': 'modular-addition', 'execution_status': 'complete' if complete else 'partial',
               'protocol': str(protocol_path), 'per_seed': rows, 'paired_differences': paired,
               'uncertainty': uncertainty, 'missing_cells': missing,
               'primary_grokking_counts': {str(wd): sum(r['delayed_grokking'] for r in rows if r['weight_decay'] == wd) for wd in [0, 1]},
               'analysis_source_sha256': s.sha(__file__)}
    s.write_json(output / 'results.json', summary)
    s.write_json(output / 'sensitivity.json', sensitivity)
    s.write_json(output / 'verification.json', {
        'passed': True, 'coverage': 'Every retained run; every pair; all final NPZ weights and PyTorch checkpoints; full curve cadence; paired state identities',
        'checks': checks, 'tolerances': {'summary_metrics_rtol_atol': [1e-10, 1e-10],
                                        'curve_metrics_rtol_atol': [3e-6, 3e-6],
                                        'torch_reload': 'bitwise equality',
                                        'numpy_forward_rtol_atol': [3e-5, 3e-4],
                                        'numpy_argmax': 'exact equality'},
        'not_checked': ['bitwise reproducibility across different hardware or package versions',
                        'every intermediate checkpoint reloaded', 'new full 800000-update independent rerun']})
    s.write_json(output / 'measurements.json', {'format': 'research-measurements-v1', 'task_id': 'modular-addition',
                                               'protocol': str(protocol_path),
                                               'runs': [r for r in runs if r['updates'] == 100000],
                                               'partial_runs': [r for r in runs if r['updates'] != 100000]})
    with (output / 'endpoints.csv').open('w', newline='') as f:
        keys = ['seed', 'weight_decay', 'updates', 'train_accuracy', 'test_accuracy', 'train_loss', 'test_loss']
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows({k: r[k] for k in keys} for r in rows)
    with (output / 'paired-differences.csv').open('w', newline='') as f:
        keys = ['seed', 'test_accuracy_difference_wd1_minus_wd0', 'test_loss_difference_wd1_minus_wd0']
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(paired)
    table = ['| Seed | Decay | Updates | Train accuracy | Held-out accuracy | Train loss | Held-out loss |',
             '|---|---|---:|---:|---:|---:|---:|']
    table += ['| %d | %d | %d | %.6f | %.6f | %.6g | %.6g |' %
              (r['seed'], r['weight_decay'], r['updates'], r['train_accuracy'], r['test_accuracy'], r['train_loss'], r['test_loss']) for r in rows]
    table += ['', '| Seed | Decay | Memorization onset | Generalization onset | Lag | Delayed grokking |',
              '|---|---|---:|---:|---:|---|']
    for row in rows:
        def event(key):
            value = row[key]
            return str(value['event_step']) if value['observed'] else 'censored at %d' % value['censor_step']
        table.append('| %d | %d | %s | %s | %s | %s |' % (row['seed'], row['weight_decay'], event('memorization'),
                     event('generalization'), str(row['lag_updates']) if row['lag_updates'] is not None else 'censored', row['delayed_grokking']))
    (output / 'report-tables.md').write_text('\n'.join(table) + '\n')
    make_figure(runs, curves, output)
    print(json.dumps({'execution_status': summary['execution_status'], 'runs_verified': len(checks),
                      'uncertainty': uncertainty, 'primary_grokking_counts': summary['primary_grokking_counts']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='artifacts')
    parser.add_argument('--output', default='analysis')
    analyze(parser.parse_args())
