"""Independent r12 inputs, CPU execution, paired summaries and full-rerun arrays."""
import hashlib
import importlib.util
import itertools
import json
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
spec = importlib.util.spec_from_file_location('trusted_r12_science', source)
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)
torch.set_num_threads(1)
cells = json.loads((root / 'analysis/measurements.json').read_text())['runs']
summary = json.loads((root / 'analysis/summary.json').read_text())
freeze = json.loads((root / 'campaigns/ema-schedule-v1/confirmation-freeze.json').read_text())
conditions = [('constant', 5000), ('cosine', 5000), ('constant', 10000), ('cosine', 10000)]
key = lambda c: (c['dataset'], c['seed'], c['schedule'], c['updates'])
by_key = {key(c): c for c in cells}
expected_keys = {(d, s, p, u) for d, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]
                 for s in seeds for p, u in conditions}
assert len(cells) == len(by_key) == 32 and set(by_key) == expected_keys
assert freeze['device'] == 'cpu'
for name, expected in freeze['source_hashes'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected


def digest(*arrays):
    h = hashlib.sha256()
    for array in arrays:
        h.update(np.ascontiguousarray(array).tobytes())
    return h.hexdigest()


groups = []
for dataset, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]:
    for seed in seeds:
        group = [by_key[dataset, seed, p, u] for p, u in conditions]
        assert len({r['inputs'] for r in group}) == 1
        torch.manual_seed(seed)
        model = science.Denoiser()
        assert sum(p.numel() for p in model.parameters()) == 296450
        initial = {k: value.detach().numpy() for k, value in model.state_dict().items()}
        rng = np.random.default_rng(seed + 100000)
        expected = {'train': science.dataset(dataset, 100000, seed + 1000000),
                    'heldout': science.dataset(dataset, 2048, seed + 2000000),
                    'indices': rng.integers(0, 100000, (10000, 256)),
                    'noise': rng.normal(size=(10000, 256, 2)).astype(np.float32),
                    'timesteps': rng.integers(0, 100, (10000, 256)),
                    'generation_noise': np.random.default_rng(seed + 3000000).normal(size=(100, 2048, 2)).astype(np.float32)}
        with np.load(root / group[0]['inputs'], allow_pickle=False) as actual:
            assert set(actual.files) == set(expected)
            assert all(actual[k].dtype == value.dtype and np.array_equal(actual[k], value) for k, value in expected.items())
        with np.load(root / group[0]['initial_weights'], allow_pickle=False) as actual:
            assert set(actual.files) == set(initial)
            assert all(np.array_equal(actual[k], initial[k]) for k in initial)
        hashes = {'initial_weights_sha256': digest(*(initial[k] for k in sorted(initial))),
                  'training_prefix_5000_sha256': digest(expected['indices'][:5000], expected['noise'][:5000],
                      expected['timesteps'][:5000], expected['train'][expected['indices'][:5000]]),
                  'heldout_sha256': digest(expected['heldout']), 'generation_noise_sha256': digest(expected['generation_noise'])}
        for row in group:
            assert all(row[k] == value for k, value in hashes.items())
            assert row['source_revision'] == freeze['runner_revision'] and row['device'] == 'cpu'
        groups.append({'dataset': dataset, 'seed': seed, 'regenerated_inputs_exact': True, 'cells': 4})


def check_trajectories(base, rows):
    checked = {}
    for row in rows:
        folder = (base / row['training_trace']).parent
        if folder in checked:
            continue
        cfg = json.loads((folder / 'input.json').read_text())
        result = json.loads((folder / 'result.json').read_text())
        end = json.loads((folder / 'finished.json').read_text())
        horizon, policy = cfg['horizon'], cfg['policy']
        assert end['status'] == 'succeeded' and result['timing']['updates'] == horizon
        trace = [json.loads(line) for line in (folder / 'trace.jsonl').read_text().splitlines()]
        assert [r['step'] for r in trace] == [1, *range(250, horizon + 1, 250)]
        for point in trace:
            rate = .0003 if policy == 'constant' else .0003 * .5 * (1 + np.cos(np.pi * (point['step'] - 1) / horizon))
            assert abs(point['lr'] - rate) <= 1e-15
        checked[folder] = {'dataset': cfg['dataset'], 'seed': cfg['seed'], 'policy': policy, 'updates': horizon}
    assert len(checked) == 24 and sum(r['updates'] for r in checked.values()) == 200000
    return list(checked.values())


primary_trajectories = check_trajectories(root, cells)
replay_root = root / 'reproduction/full-r1'
replay = json.loads((replay_root / 'analysis/measurements.json').read_text())['runs']
replay_by_key = {key(r): r for r in replay}
assert set(replay_by_key) == expected_keys
replay_trajectories = check_trajectories(replay_root, replay)
compared_arrays = 0
for row in cells:
    repeated = replay_by_key[key(row)]
    for name in ('initial_weights_sha256', 'training_prefix_5000_sha256', 'heldout_sha256', 'generation_noise_sha256', 'source_revision'):
        assert row[name] == repeated[name]
    for field in ('arrays', 'weights'):
        with np.load(root / row[field], allow_pickle=False) as first, np.load(replay_root / repeated[field], allow_pickle=False) as second:
            assert set(first.files) == set(second.files)
            for name in first.files:
                assert np.array_equal(first[name], second[name]); compared_arrays += 1


def statistics(row, values):
    values = np.array(values, dtype=float)
    mean = float(values.mean()); half = float(t.ppf(.975, 3)) * float(values.std(ddof=1)) / 2
    p = sum(abs(float(np.mean(values * signs))) >= abs(mean) - 1e-14
            for signs in itertools.product([-1, 1], repeat=4)) / 16
    np.testing.assert_allclose(row['values'], values, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose([row['mean'], *row['ci95']], [mean, mean - half, mean + half], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['leave_one_out'], [(float(values.sum()) - x) / 3 for x in values], rtol=1e-12, atol=1e-12)
    assert row['n'] == 4 and row['signflip_p'] == p


for family in ('effects', 'contrasts', 'absolute_sw1_contrasts'):
    for row in summary[family]:
        seeds = list(range(4001, 4005) if row['dataset'] == 'moons' else range(5001, 5005))
        assert row['seeds'] == seeds
        matrix = np.array([[by_key[row['dataset'], s, p, u]['metrics'][row['variant']]['sw1'] for p, u in conditions] for s in seeds])
        if family != 'absolute_sw1_contrasts':
            matrix -= np.array([[by_key[row['dataset'], s, p, u]['metrics']['raw']['sw1'] for p, u in conditions] for s in seeds])
        if family == 'effects':
            coefficients = np.eye(4)[conditions.index((row['schedule'], row['updates']))]
        elif row['contrast'] == 'schedule':
            coefficients = [-1, 1, 0, 0] if row['at'] == '5000' else [0, 0, -1, 1]
        elif row['contrast'] == 'duration':
            coefficients = [-1, 0, 1, 0] if row['at'] == 'constant' else [0, -1, 0, 1]
        else:
            assert row['contrast'] == 'interaction'; coefficients = [1, -1, -1, 1]
        statistics(row, matrix @ coefficients)
for row in summary['coverage']:
    values = [by_key['gmm8', seed, row['schedule'], row['updates']]['metrics'][row['variant']] for seed in range(5001, 5005)]
    assert row['counts'] == [r['mode_counts'] for r in values]
    statistics(row['covered_modes'], [r['covered_modes'] for r in values])
    statistics(row['inlier_fraction'], [r['inlier_fraction'] for r in values])
assert [len(summary[k]) for k in ('effects', 'contrasts', 'absolute_sw1_contrasts', 'coverage')] == [16, 20, 30, 12]
result = {'status': 'pass', 'required_cells': 32, 'input_groups': groups,
          'primary_trajectories': primary_trajectories, 'fresh_replay_trajectories': replay_trajectories,
          'primary_updates': 200000, 'fresh_replay_updates': 200000,
          'replayed_numeric_arrays_bitwise_equal': compared_arrays, 'statistical_summaries_checked': 90,
          'backend': 'cpu', 'scope': 'Exact declared input/initialization regeneration, paired hashes, all primary and fresh-rerun LR/update traces, independent factorial statistics and every fresh weight/sample array. No optimizer-state checkpoint or extra independent seed claim; original frozen scoring covers all 96 final model states.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'required_cells', 'primary_updates', 'fresh_replay_updates', 'replayed_numeric_arrays_bitwise_equal', 'statistical_summaries_checked')}))
