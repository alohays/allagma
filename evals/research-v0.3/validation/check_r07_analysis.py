"""Independent r07 factorial statistics, paired inputs and execution provenance.

Reconstructs input arrays from the frozen trusted scientific reference and the
declared RNG plan. Does not import candidate code or retrain confirmation models.
"""
import datetime
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t
import torch

ROOT = Path(__file__).resolve().parents[3]
root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new verification receipt')
source = ROOT / 'evals/research-v0.3/frozen/source/studies/ema-2d-diffusion/domain/science.py'
spec = importlib.util.spec_from_file_location('trusted_ema_science_r07', source)
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)
torch.set_num_threads(1)
cells = json.loads((root / 'analysis/measurements.json').read_text())['runs']
summary = json.loads((root / 'analysis/summary.json').read_text())
freeze = json.loads((root / 'campaigns/ema-schedule-v1/confirmation-freeze.json').read_text())
freeze_time = datetime.datetime.fromisoformat(freeze['created_at'])
conditions = [('constant', 5000), ('cosine', 5000), ('constant', 10000), ('cosine', 10000)]
by_key = {(r['dataset'], r['seed'], r['schedule'], r['updates']): r for r in cells}
assert len(by_key) == len(cells) == 32
expected_keys = {(d, s, p, u) for d, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]
                 for s in seeds for p, u in conditions}
assert set(by_key) == expected_keys
for path, expected in freeze['scientific_sources'].items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected


def array_hash(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def named_hash(arrays):
    h = hashlib.sha256()
    for name in sorted(arrays):
        a = np.ascontiguousarray(arrays[name])
        h.update(json.dumps([name, str(a.dtype), list(a.shape)], separators=(',', ':')).encode() + b'\n')
        h.update(a.tobytes())
    return h.hexdigest()


groups = []
for dataset, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]:
    for seed in seeds:
        group = [by_key[dataset, seed, p, u] for p, u in conditions]
        assert len({r['input_metadata'] for r in group}) == 1
        folder = (root / group[0]['input_metadata']).parent
        meta = json.loads((folder / 'metadata.json').read_text())
        assert datetime.datetime.fromisoformat(meta['created_at']) > freeze_time
        torch.manual_seed(seed)
        model = science.Denoiser()
        assert sum(p.numel() for p in model.parameters()) == 296450
        initial = {k: v.detach().numpy() for k, v in model.state_dict().items()}
        with np.load(folder / 'initial.npz', allow_pickle=False) as saved:
            assert set(saved.files) == set(initial)
            assert all(np.array_equal(saved[k], initial[k]) for k in initial)
        train = science.dataset(dataset, 100000, seed + 1000000)
        generator = np.random.default_rng(seed + 100000)
        indices = generator.integers(0, len(train), (10000, 256)).astype(np.int32)
        noise = generator.normal(size=(10000, 256, 2)).astype(np.float32)
        timesteps = generator.integers(0, 100, (10000, 256)).astype(np.int16)
        coefficients = science.schedule()
        noisy = (coefficients['sqrt_abar'][timesteps, None] * train[indices]
                 + coefficients['sqrt_one_minus'][timesteps, None] * noise).astype(np.float32)
        expected = dict(train=train, indices=indices, noise=noise, timesteps=timesteps, noisy=noisy)
        with np.load(folder / 'training.npz', allow_pickle=False) as saved:
            assert set(saved.files) == set(expected)
            assert all(saved[k].dtype == expected[k].dtype and np.array_equal(saved[k], expected[k]) for k in expected)
        heldout = science.dataset(dataset, 2048, seed + 2000000)
        gen_noise = np.random.default_rng(seed + 3000000).normal(size=(100, 2048, 2)).astype(np.float32)
        with np.load(folder / 'evaluation.npz', allow_pickle=False) as saved:
            assert np.array_equal(saved['heldout'], heldout)
            assert np.array_equal(saved['generation_noise'], gen_noise)
        hashes = {'initial_weights_sha256': named_hash(initial),
                  'training_prefix_5000_sha256': named_hash({k: v if k == 'train' else v[:5000] for k, v in expected.items()}),
                  'heldout_sha256': array_hash(heldout), 'generation_noise_sha256': array_hash(gen_noise)}
        for row in group:
            assert all(row[k] == value for k, value in hashes.items())
            assert row['phase'] == 'confirmation' and row['device'] == 'mps'
            if row['schedule'] == 'cosine':
                assert row['updates'] == row['actual_schedule_duration']
        groups.append({'dataset': dataset, 'seed': seed, 'cells': 4, 'regenerated_inputs_exact': True, **hashes})

trajectories = {}
for row in cells:
    folder = (root / row['arrays']).parent
    if folder in trajectories:
        continue
    result = json.loads((folder / 'result.json').read_text())
    config = result['inputs']
    duration, policy = config['duration'], config['policy']
    assert result['status'] == 'succeeded' and result['completed_updates'] == duration
    assert datetime.datetime.fromisoformat(result['started_at']) > freeze_time
    trace = [json.loads(line) for line in (folder / 'trace.jsonl').read_text().splitlines()]
    assert trace[-1]['step'] == duration
    for point in trace:
        rate = .0003 if policy == 'constant' else .0003 * (1 + math.cos(math.pi * (point['step'] - 1) / duration)) / 2
        assert math.isclose(point['lr'], rate, rel_tol=1e-12, abs_tol=1e-15)
    with np.load(folder / 'recovery.npz', allow_pickle=False) as state:
        assert int(state['completed_updates']) == duration
        steps = [name for name in state.files if name.startswith('optimizer__') and name.endswith('__step')]
        assert steps and all(int(state[name]) == duration for name in steps)
        with np.load(folder / f'step-{duration}-weights.npz', allow_pickle=False) as weights:
            assert all(np.array_equal(state[name], weights[name]) for name in weights.files)
    trajectories[folder] = {'dataset': config['dataset'], 'seed': config['seed'], 'policy': policy,
                             'updates': duration, 'optimizer_states': len(steps), 'trace_points': len(trace)}
assert len(trajectories) == 24 and sum(v['updates'] for v in trajectories.values()) == 200000


def check_statistics(row, values):
    values = np.asarray(values, dtype=np.float64)
    mean, sd = float(values.mean()), float(values.std(ddof=1))
    radius = float(t.ppf(.975, 3)) * sd / 2
    p = sum(abs(float(np.mean(values * signs))) >= abs(mean) - 1e-15
            for signs in itertools.product([-1, 1], repeat=4)) / 16
    np.testing.assert_allclose(row['values'], values, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose([row['mean'], row['sd'], row['se']], [mean, sd, sd / 2], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['ci95'], [mean - radius, mean + radius], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['leave_one_out_means'], [(float(values.sum()) - value) / 3 for value in values], rtol=1e-12, atol=1e-12)
    assert row['sign_flip_p'] == p and row['n'] == 4


for family in ('effects', 'absolute_sw1', 'coverage'):
    for row in summary[family]:
        seeds = list(range(4001, 4005) if row['dataset'] == 'moons' else range(5001, 5005))
        assert row['seeds'] == seeds
        if family == 'coverage':
            values = [by_key[row['dataset'], seed, row['schedule'], row['updates']]['metrics'][row['variant']][row['metric']] for seed in seeds]
        else:
            matrix = np.array([[by_key[row['dataset'], seed, policy, updates]['metrics'][row['variant']]['sw1']
                                for policy, updates in conditions] for seed in seeds])
            if family == 'effects':
                matrix -= np.array([[by_key[row['dataset'], seed, policy, updates]['metrics']['raw']['sw1']
                                     for policy, updates in conditions] for seed in seeds])
            kind = row['contrast']
            if kind == 'cell':
                coefficients = np.eye(4)[conditions.index((row['schedule'], row['updates']))]
            elif kind == 'schedule_cosine_minus_constant':
                coefficients = [-1, 1, 0, 0] if row['updates'] == 5000 else [0, 0, -1, 1]
            elif kind == 'duration_10000_minus_5000':
                coefficients = [-1, 0, 1, 0] if row['schedule'] == 'constant' else [0, -1, 0, 1]
            else:
                assert kind == 'interaction'
                coefficients = [1, -1, -1, 1]
            values = matrix @ coefficients
        check_statistics(row, values)
assert [len(summary[k]) for k in ('effects', 'absolute_sw1', 'coverage')] == [36, 54, 24]
effects = [row for row in summary['effects'] if row['contrast'] == 'cell']
schedules = [row for row in summary['effects'] if row['contrast'] == 'schedule_cosine_minus_constant']
interactions = [row for row in summary['effects'] if row['contrast'] == 'interaction']
result = {'status': 'pass', 'required_cells': 32, 'input_groups': groups,
          'actual_trajectories': list(trajectories.values()), 'actual_training_updates': 200000,
          'statistical_rows_checked': 114,
          'findings': {'negative_cell_mean_effects': sum(row['mean'] < 0 for row in effects),
                       'cell_intervals_below_zero': sum(row['ci95'][1] < 0 for row in effects),
                       'positive_schedule_contrast_means': sum(row['mean'] > 0 for row in schedules),
                       'interaction_intervals_include_zero': sum(row['ci95'][0] <= 0 <= row['ci95'][1] for row in interactions)},
          'scope': 'Exact reference-based input/initialization regeneration and paired prefix hashes; all 24 terminal optimizer counters and learning-rate traces; 114 cell/contrast summaries with paired t intervals, sign flips and leave-one-out means. The separate frozen scorer verifies all metrics and 96 saved-state samples. No second training replay.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'required_cells', 'actual_training_updates', 'statistical_rows_checked', 'findings')}))
