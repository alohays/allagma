"""Independent r08 input reconstruction, execution traces and factorial summaries."""
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
    raise RuntimeError('Use a new validation receipt')
source = ROOT / 'evals/research-v0.3/frozen/source/studies/ema-2d-diffusion/domain/science.py'
spec = importlib.util.spec_from_file_location('trusted_r08_science', source)
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)
torch.set_num_threads(1)
cells = json.loads((root / 'measurements.json').read_text())['runs']
summary = json.loads((root / 'analysis/summary.json').read_text())
freeze = json.loads((root / 'protocols/freeze.json').read_text())
conditions = [('constant', 5000), ('cosine', 5000), ('constant', 10000), ('cosine', 10000)]
by_key = {(r['dataset'], r['seed'], r['schedule'], r['updates']): r for r in cells}
expected_keys = {(d, s, p, u) for d, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]
                 for s in seeds for p, u in conditions}
assert len(cells) == len(by_key) == 32 and set(by_key) == expected_keys
for name, digest in freeze['source_hashes'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest


def digest(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


groups = []
for dataset, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]:
    for seed in seeds:
        group = [by_key[dataset, seed, p, u] for p, u in conditions]
        assert len({r['shared_inputs'] for r in group}) == 1
        generator = np.random.default_rng(seed + 100000)
        expected = {'train': science.dataset(dataset, 100000, seed + 1000000),
                    'heldout': science.dataset(dataset, 2048, seed + 2000000),
                    'indices': generator.integers(0, 100000, (10000, 256)),
                    'noise': generator.normal(size=(10000, 256, 2)).astype(np.float32),
                    'timesteps': generator.integers(0, 100, (10000, 256)),
                    'generation_noise': np.random.default_rng(seed + 3000000).normal(size=(100, 2048, 2)).astype(np.float32)}
        with np.load(root / group[0]['shared_inputs'], allow_pickle=False) as actual:
            assert set(actual.files) == set(expected)
            assert all(actual[k].dtype == value.dtype and np.array_equal(actual[k], value) for k, value in expected.items())
        torch.manual_seed(seed)
        model = science.Denoiser()
        assert sum(p.numel() for p in model.parameters()) == 296450
        initial = {k: value.detach().numpy() for k, value in model.state_dict().items()}
        initial_hash = hashlib.sha256()
        for name in sorted(initial):
            initial_hash.update(name.encode() + b'\0')
            initial_hash.update(np.ascontiguousarray(initial[name]).tobytes())
        prefix = hashlib.sha256()
        for name, values in [('clean', expected['train'][expected['indices'][:5000]]),
                             ('noise', expected['noise'][:5000]), ('timesteps', expected['timesteps'][:5000])]:
            prefix.update(name.encode() + b'\0')
            prefix.update(np.ascontiguousarray(values).tobytes())
        for row in group:
            with np.load(root / row['initial_weights'], allow_pickle=False) as saved:
                assert all(np.array_equal(saved[k], initial[k]) for k in initial)
            assert row['initial_weights_sha256'] == initial_hash.hexdigest()
            assert row['training_prefix_5000_sha256'] == prefix.hexdigest()
            assert row['heldout_sha256'] == digest(expected['heldout'])
            assert row['generation_noise_sha256'] == digest(expected['generation_noise'])
            assert row['phase'] == 'confirmation' and row['device'] == 'mps'
            assert row['source_revision'] == freeze['source_revision']
            if row['schedule'] == 'cosine':
                assert row['updates'] == row['schedule_duration']
        groups.append({'dataset': dataset, 'seed': seed, 'cells': 4, 'regenerated_inputs_exact': True,
                       'initial_hash': initial_hash.hexdigest(), 'training_prefix_hash': prefix.hexdigest()})

trajectories = {}
for row in cells:
    folder = (root / row['arrays']).parent
    if folder in trajectories:
        continue
    config = json.loads((folder / 'config.json').read_text())
    status = json.loads((folder / 'status.json').read_text())
    duration, policy = config['duration'], config['policy']
    assert status['status'] == 'completed' and status['timing']['updates'] == duration
    trace = [json.loads(line) for line in (folder / 'trace.jsonl').read_text().splitlines()]
    assert [x['step'] for x in trace] == [1, *range(100, duration + 1, 100)]
    for point in trace:
        rate = .0003 if policy == 'constant' else .0003 * (1 + math.cos(math.pi * (point['step'] - 1) / duration)) / 2
        assert math.isclose(point['lr'], rate, rel_tol=1e-12, abs_tol=1e-15)
        assert point['ema_updates'] == point['step']
    trajectories[folder] = {'dataset': config['dataset'], 'seed': config['seed'], 'policy': policy,
                             'updates': duration, 'trace_points': len(trace)}
assert len(trajectories) == 24 and sum(r['updates'] for r in trajectories.values()) == 200000


def check_statistics(row, values):
    values = np.asarray(values, dtype=np.float64)
    mean, sd = float(values.mean()), float(values.std(ddof=1))
    radius = float(t.ppf(.975, 3)) * sd / 2
    p = sum(abs(float(np.mean(values * signs))) >= abs(mean) - 1e-15
            for signs in itertools.product([-1, 1], repeat=4)) / 16
    np.testing.assert_allclose(row['values'], values, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose([row['mean'], row['sd'], row['se']], [mean, sd, sd / 2], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['ci95'], [mean - radius, mean + radius], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['leave_one_seed_out_means'], [(float(values.sum()) - value) / 3 for value in values], rtol=1e-12, atol=1e-12)
    assert row['sign_flip_p'] == p and row['n'] == 4 and row['negative_count'] == int((values < 0).sum())


for family in ('paired_ema_minus_raw', 'ema_effect_contrasts', 'absolute_sw1_contrasts'):
    for row in summary[family]:
        seeds = list(range(4001, 4005) if row['dataset'] == 'moons' else range(5001, 5005))
        assert row['seeds'] == seeds
        matrix = np.array([[by_key[row['dataset'], seed, policy, updates]['metrics'][row['variant']]['sw1']
                            for policy, updates in conditions] for seed in seeds])
        if family != 'absolute_sw1_contrasts':
            matrix -= np.array([[by_key[row['dataset'], seed, policy, updates]['metrics']['raw']['sw1']
                                 for policy, updates in conditions] for seed in seeds])
        if family == 'paired_ema_minus_raw':
            coefficients = np.eye(4)[conditions.index((row['schedule'], row['updates']))]
        elif row['contrast'] == 'schedule_cosine_minus_constant':
            coefficients = [-1, 1, 0, 0] if row['condition'] == 5000 else [0, 0, -1, 1]
        elif row['contrast'] == 'duration_10000_minus_5000':
            coefficients = [-1, 0, 1, 0] if row['condition'] == 'constant' else [0, -1, 0, 1]
        else:
            assert row['contrast'] == 'interaction'
            coefficients = [1, -1, -1, 1]
        check_statistics(row, matrix @ coefficients)
for row in summary['absolute_cell_quality']:
    for variant, value in row['mean_sw1'].items():
        expected = np.mean([by_key[row['dataset'], seed, row['schedule'], row['updates']]['metrics'][variant]['sw1'] for seed in row['seeds']])
        assert abs(value - expected) < 1e-12
for row in summary['gmm8_coverage']:
    values = [by_key['gmm8', seed, row['schedule'], row['updates']]['metrics'][row['variant']] for seed in row['seeds']]
    assert row['covered_modes'] == [v['covered_modes'] for v in values]
    assert row['inlier_counts'] == [v['inlier_count'] for v in values]
    assert row['inlier_fractions'] == [v['inlier_fraction'] for v in values]
    assert row['mean_inlier_fraction'] == np.mean(row['inlier_fractions'])
assert [len(summary[k]) for k in ('paired_ema_minus_raw', 'ema_effect_contrasts', 'absolute_sw1_contrasts', 'absolute_cell_quality', 'gmm8_coverage')] == [16, 20, 30, 8, 12]
result = {'status': 'pass', 'required_cells': 32, 'input_groups': groups,
          'actual_trajectories': list(trajectories.values()), 'actual_training_updates': 200000,
          'paired_statistical_rows_checked': 66, 'absolute_quality_rows_checked': 8, 'coverage_rows_checked': 12,
          'scope': 'Exact trusted-reference input and initial-state regeneration, within-seed prefix matching, 24 complete source/trace trajectories and all reported paired contrasts/uncertainty. No optimizer-state replay or second training execution is claimed; the separate frozen scorer verifies all 96 saved model states.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'required_cells', 'actual_training_updates', 'paired_statistical_rows_checked', 'absolute_quality_rows_checked', 'coverage_rows_checked')}))
