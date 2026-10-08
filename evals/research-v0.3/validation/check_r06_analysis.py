"""Independent checks of r06's retained checkpoint, transition and paired evidence."""
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t
import torch

root, output = (Path(p).resolve() for p in sys.argv[1:3])
analysis_dir = root / (sys.argv[3] if len(sys.argv) > 3 else 'analysis')
if output.exists():
    raise RuntimeError('Use a new validation receipt')
submission = json.loads((root / 'submission.json').read_text())
measurements = json.loads((root / submission['measurements']).read_text())
results = json.loads((analysis_dir / 'results.json').read_text())
sensitivity = json.loads((analysis_dir / 'sensitivity.json').read_text())
assert len(measurements['runs']) == 8
curves = {}
observations = []


def event(curve, metric, threshold, sustain):
    mask = np.array([r[metric] >= threshold for r in curve], dtype=np.int64)
    starts = np.flatnonzero(np.convolve(mask, np.ones(sustain, dtype=np.int64), mode='valid') == sustain)
    start = int(starts[0]) if len(starts) else None
    return {'observed': start is not None,
            'event_step': curve[start]['step'] if start is not None else None,
            'confirmation_step': curve[start + sustain - 1]['step'] if start is not None else None,
            'censor_step': None if start is not None else curve[-1]['step']}, start


def check_outcome(curve, reported, threshold=.95, sustain=3, lag_min=1000, gate=.5):
    mem, mi = event(curve, 'train_accuracy', .99, sustain)
    gen, gi = event(curve, 'test_accuracy', threshold, sustain)
    for label, expected in [('memorization', mem), ('generalization', gen)]:
        assert {k: reported[label][k] for k in expected} == expected
    lag = gen['event_step'] - mem['event_step'] if mem['observed'] and gen['observed'] else None
    assert reported['lag_updates'] == lag
    persists = all(r['train_accuracy'] >= .99 for r in curve[gi:gi + sustain]) if gi is not None else None
    at_mem = curve[mi]['test_accuracy'] if mi is not None else None
    delayed = bool(lag is not None and lag >= lag_min and (gate is None or at_mem <= gate) and persists)
    assert reported['delayed_grokking'] == delayed
    assert reported['training_persists_at_generalization'] == persists
    assert reported['test_accuracy_at_memorization'] == at_mem
    if mi is not None and gi is None:
        # A trailing unconfirmed crossing can start an event before the horizon.
        trailing = 0
        for row in reversed(curve):
            if row['test_accuracy'] < threshold:
                break
            trailing += 1
        earliest_possible = curve[-trailing]['step'] if trailing else curve[-1]['step'] + 100
        assert reported['lag_censored_lower_bound_updates'] <= earliest_possible - mem['event_step']
    return gen['observed'], delayed


for run in measurements['runs']:
    curve = run['curve'] if isinstance(run['curve'], list) else json.loads((root / run['curve']).read_text())
    assert [r['step'] for r in curve] == list(range(0, 100001, 100))
    curves[(run['seed'], run['weight_decay'])] = curve
    reported = next(r for r in results['per_seed'] if r['seed'] == run['seed'] and r['weight_decay'] == run['weight_decay'])
    check_outcome(curve, reported)
    checkpoint = torch.load(root / run['checkpoint'], map_location='cpu', weights_only=True)
    assert checkpoint['step'] == 100000 and checkpoint['curve'] == curve
    assert all(int(v['step']) == 100000 for v in checkpoint['optimizer']['state'].values())
    group = checkpoint['optimizer']['param_groups'][0]
    assert group['lr'] == .001 and group['betas'] == (.9, .98)
    assert group['eps'] == 1e-8 and group['weight_decay'] == run['weight_decay']
    with np.load(root / run['weights'], allow_pickle=False) as weights:
        assert np.array_equal(checkpoint['model']['0.weight'].numpy(), weights['input_weight'])
        assert np.array_equal(checkpoint['model']['2.weight'].numpy(), weights['output_weight'])
    observations.append({'seed': run['seed'], 'weight_decay': run['weight_decay'], 'updates': 100000,
                         'memorization': reported['memorization'], 'generalization': reported['generalization'],
                         'maximum_heldout_accuracy': max(r['test_accuracy'] for r in curve)})
assert set(curves) == {(seed, wd) for seed in range(1001, 1005) for wd in (0, 1)}
assert len(sensitivity) == 108
for definition in sensitivity:
    outcomes = []
    assert definition['n_complete'] == 4
    for row in definition['seed_outcomes']:
        outcomes.append(check_outcome(curves[(row['seed'], definition['weight_decay'])], row,
                       definition['test_threshold'], definition['sustain'], definition['minimum_lag'],
                       definition['test_at_memorization_maximum']))
    assert definition['generalization_events'] == sum(x[0] for x in outcomes)
    assert definition['delayed_grokking_events'] == sum(x[1] for x in outcomes)
effects = {}
for metric in ('test_accuracy', 'test_loss'):
    differences = []
    for seed in range(1001, 1005):
        pair = {r['weight_decay']: r for r in measurements['runs'] if r['seed'] == seed}
        differences.append(pair[1]['metrics'][metric] - pair[0]['metrics'][metric])
    x = np.array(differences, dtype=np.float64)
    mean, sd = float(x.mean()), float(x.std(ddof=1))
    interval = [mean - float(t.ppf(.975, 3)) * sd / 2, mean + float(t.ppf(.975, 3)) * sd / 2]
    probability = sum(abs(float(np.mean(x * signs))) >= abs(mean) - 1e-14
                      for signs in itertools.product([-1, 1], repeat=4)) / 16
    reported = results['uncertainty'][metric]
    np.testing.assert_allclose(reported['ci95'], interval, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose([reported['mean'], reported['sd']], [mean, sd], rtol=1e-12, atol=1e-12)
    assert reported['sign_flip_p_two_sided'] == probability and reported['n'] == 4
    effects[metric] = {'mean': mean, 'ci95': interval, 'exact_signflip_two_sided_p': probability, 'independent_seeds': 4}
result = {'status': 'pass', 'completed_cells': len(observations), 'observations': observations,
          'sensitivity_rows_checked': len(sensitivity), 'effects': effects,
          'scope': 'Independent convolution-based sustained-event checks, primary and sensitivity rules, conservative censoring bounds, paired uncertainty, exact final checkpoint/NPZ identity and all optimizer counters/settings. No second training replay.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': 'pass', 'completed_cells': len(observations), 'effects': effects}))
