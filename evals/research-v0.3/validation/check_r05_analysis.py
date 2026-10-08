"""Independent r05 statistics, censoring, curve and optimizer-state checks."""
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t

root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new verification receipt')
measurements = json.loads((root / 'measurements.json').read_text())
analysis = json.loads((root / 'analysis/results.json').read_text())
observations = []
for run in measurements['runs']:
    curve = run['curve']
    assert [r['step'] for r in curve] == list(range(0, 100001, 100))
    onset = next(curve[i]['step'] for i in range(len(curve) - 2)
                 if all(r['train_accuracy'] >= .99 for r in curve[i:i + 3]))
    maximum = max(r['test_accuracy'] for r in curve)
    assert maximum < .9
    row = next(r for r in analysis['runs'] if r['seed'] == run['seed'] and r['weight_decay'] == run['weight_decay'])
    event = row['transition']
    assert event['memorization']['time'] == onset
    assert event['memorization']['confirmation_time'] == onset + 200
    assert event['generalization']['time'] is None and event['generalization']['censor_time'] == 100000
    assert event['lag'] is None and not event['delayed_grokking']
    assert event['lag_lower_bound_exclusive'] == 100000 - 200 - onset
    for sensitivity in row['sensitivity'].values():
        assert not sensitivity['generalization']['observed'] and not sensitivity['delayed_grokking']
    with np.load(root / run['checkpoint'], allow_pickle=False) as checkpoint, np.load(root / run['weights'], allow_pickle=False) as weights:
        assert int(checkpoint['step']) == 100000
        assert np.array_equal(checkpoint['u'].T, weights['input_weight'])
        assert np.array_equal(checkpoint['v'], weights['output_weight'])
        for key in ('m1', 'm2', 'q1', 'q2'):
            assert np.isfinite(checkpoint[key]).all()
        assert (checkpoint['q1'] >= 0).all() and (checkpoint['q2'] >= 0).all()
    assert len(run['attempt_chain']) == 2
    for attempt, expected_start, expected_end in zip(run['attempt_chain'], (0, 50000), (50000, 100000)):
        completed = json.loads((root / 'evidence/confirmation/attempts' / attempt / 'completed.json').read_text())
        assert completed['status'] == 'succeeded'
        assert (completed['started_step'], completed['ended_step']) == (expected_start, expected_end)
    observations.append({'seed': run['seed'], 'weight_decay': run['weight_decay'],
                         'memorization_onset': onset, 'maximum_heldout_accuracy': maximum,
                         'checkpoint_updates': 100000, 'segments': 2})
effects = {}
for metric in ('test_accuracy', 'test_loss'):
    differences = []
    for seed in (1001, 1002, 1003, 1004):
        rows = {r['weight_decay']: r for r in measurements['runs'] if r['seed'] == seed}
        differences.append(rows[1]['metrics'][metric] - rows[0]['metrics'][metric])
    values = np.array(differences, dtype=np.float64)
    mean, sd = float(values.mean()), float(values.std(ddof=1))
    interval = [mean - float(t.ppf(.975, 3)) * sd / 2, mean + float(t.ppf(.975, 3)) * sd / 2]
    probability = sum(abs(float(np.mean(values * signs))) >= abs(mean) - 1e-14
                      for signs in itertools.product([-1, 1], repeat=4)) / 16
    expected = analysis['paired_uncertainty'][metric + '_difference']
    np.testing.assert_allclose(expected['ci95'], interval, rtol=1e-10, atol=1e-9)
    np.testing.assert_allclose([expected['mean'], expected['sample_sd']], [mean, sd], rtol=1e-12, atol=1e-12)
    assert expected['exact_signflip_two_sided_p'] == probability and expected['n'] == 4 and expected['t_df'] == 3
    effects[metric] = {'mean': mean, 'ci95': interval, 'exact_signflip_two_sided_p': probability, 'independent_seeds': 4}
result = {'status': 'pass', 'completed_cells': len(observations), 'observations': observations,
          'effects': effects, 'scope': 'Independent paired statistics, primary/sensitivity censoring, dense curve grid, final native optimizer state and two-segment coverage. No long-horizon cross-backend identity or second training replay.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': 'pass', 'completed_cells': len(observations), 'effects': effects}))
