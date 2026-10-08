"""Controller checks of r04 retained curves, statistics and safe checkpoints.

This consumes only data. It neither imports candidate code nor retrains models.
"""
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t
import torch

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
measurements = json.loads((root / 'measurements.json').read_text())
summary = json.loads((root / 'analysis/primary/summary.json').read_text())
transitions = json.loads((root / 'analysis/primary/per-seed.json').read_text())
observations = []
for run in measurements['runs']:
    curve = json.loads((root / run['curve']).read_text())
    assert [r['step'] for r in curve] == list(range(0, 100001, 100))
    onset = next(curve[i]['step'] for i in range(len(curve) - 2)
                 if all(r['train_accuracy'] >= .99 for r in curve[i:i + 3]))
    maximum = max(r['test_accuracy'] for r in curve)
    assert maximum < .9
    row = next(r for r in transitions
               if r['seed'] == run['seed'] and r['weight_decay'] == run['weight_decay'])
    event = row['transition']
    assert event['memorization']['time'] == onset
    assert event['memorization']['confirmed_at'] == onset + 200
    assert event['generalization']['time'] is None
    assert event['generalization']['censor_at'] == 100000
    assert event['lag'] is None and not event['delayed_grokking_observed']
    for sensitivity in row['sensitivity']:
        outcome = sensitivity['outcome']
        assert not outcome['generalization']['event']
        assert not outcome['delayed_grokking_observed']
    checkpoint = torch.load(root / run['checkpoint'], map_location='cpu', weights_only=True)
    assert checkpoint['step'] == 100000
    assert all(int(value['step']) == 100000 for value in checkpoint['optimizer']['state'].values())
    with np.load(root / run['weights'], allow_pickle=False) as weights:
        assert np.array_equal(checkpoint['model']['0.weight'].numpy(), weights['input_weight'])
        assert np.array_equal(checkpoint['model']['2.weight'].numpy(), weights['output_weight'])
    observations.append({'seed': run['seed'], 'weight_decay': run['weight_decay'],
                         'memorization_onset': onset, 'maximum_heldout_accuracy': maximum,
                         'checkpoint_and_optimizer_updates': 100000})
effects = {}
for metric in ['test_accuracy', 'test_loss']:
    differences = []
    for seed in range(1001, 1005):
        rows = {r['weight_decay']: r for r in measurements['runs'] if r['seed'] == seed}
        differences.append(rows[1]['metrics'][metric] - rows[0]['metrics'][metric])
    values = np.asarray(differences, dtype=np.float64)
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    interval = [mean - float(t.ppf(.975, 3)) * sd / 2,
                mean + float(t.ppf(.975, 3)) * sd / 2]
    probability = sum(abs(float(np.mean(values * signs))) >= abs(mean) - 1e-14
                      for signs in itertools.product([-1, 1], repeat=4)) / 16
    expected = summary['uncertainty'][metric]
    # Candidate uses a rounded t critical value; tolerance is < 1e-8 nats.
    np.testing.assert_allclose(expected['ci95_student_t'], interval, rtol=1e-10, atol=1e-9)
    np.testing.assert_allclose([expected['mean'], expected['sd']], [mean, sd], rtol=1e-12, atol=1e-12)
    assert expected['paired_sign_flip_two_sided_p'] == probability
    assert expected['n_independent_seeds'] == 4 and expected['df'] == 3
    effects[metric] = {'mean': mean, 'ci95': interval,
                       'exact_sign_flip_p': probability, 'independent_units': 4}
result = {'status': 'pass', 'completed_cells': len(observations),
          'observations': observations, 'effects': effects,
          'scope': 'Independent endpoint effects/t intervals/sign flips, complete curve grid, memorization/censoring and sensitivity, all final optimizer counters and safe checkpoint-to-NPZ identity. No second training replay.'}
if output.exists():
    raise RuntimeError('Use a new validation receipt')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': 'pass', 'completed_cells': len(observations), 'effects': effects}))
