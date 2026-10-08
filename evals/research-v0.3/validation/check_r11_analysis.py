"""Independent r11 input, optimizer, exact-terminal-cosine and statistic checks."""
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t, wasserstein_distance
import torch

ROOT = Path(__file__).resolve().parents[3]
root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new validation receipt')
source = ROOT / 'evals/research-v0.3/frozen/source/studies/ema-2d-diffusion/domain/science.py'
spec = importlib.util.spec_from_file_location('trusted_r11_science', source)
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)
torch.set_num_threads(1)
cells = json.loads((root / 'measurements.json').read_text())['runs']
summary = json.loads((root / 'analysis/summary.json').read_text())
freeze = json.loads((root / 'freeze.json').read_text())
conditions = [('constant', 5000), ('cosine', 5000), ('constant', 10000), ('cosine', 10000)]
by_key = {(c['dataset'], c['seed'], c['schedule'], c['updates']): c for c in cells}
assert len(cells) == len(by_key) == 32
assert set(by_key) == {(d, s, p, u) for d, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]
                       for s in seeds for p, u in conditions}
for path, expected in freeze['source_hashes'].items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected


def digest(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


groups = []
controls = []
angles = np.random.default_rng(7321).uniform(0, 2 * np.pi, 128)
for dataset, seeds in [('moons', range(4001, 4005)), ('gmm8', range(5001, 5005))]:
    for seed in seeds:
        group = [by_key[dataset, seed, p, u] for p, u in conditions]
        assert len({r['provenance'] for r in group}) == 1
        folder = (root / group[0]['provenance']).parent
        torch.manual_seed(seed)
        model = science.Denoiser()
        assert sum(p.numel() for p in model.parameters()) == 296450
        initial = {k: v.detach().numpy() for k, v in model.state_dict().items()}
        with np.load(folder / 'initial.npz', allow_pickle=False) as saved:
            assert set(saved.files) == set(initial)
            assert all(np.array_equal(saved[k], initial[k]) for k in initial)
        train = science.dataset(dataset, 100000, seed + 1000000)
        rng = np.random.default_rng(seed + 100000)
        indices = rng.integers(0, len(train), (10000, 256)).astype(np.int32)
        noise = rng.normal(size=(10000, 256, 2)).astype(np.float32)
        timesteps = rng.integers(0, 100, (10000, 256)).astype(np.int16)
        coeff = science.schedule()
        noisy = (coeff['sqrt_abar'][timesteps, None] * train[indices]
                 + coeff['sqrt_one_minus'][timesteps, None] * noise).astype(np.float32)
        expected = dict(train=train, indices=indices, noise=noise, timesteps=timesteps, noisy=noisy)
        with np.load(folder / 'training.npz', allow_pickle=False) as saved:
            assert all(saved[k].dtype == a.dtype and np.array_equal(saved[k], a) for k, a in expected.items())
        heldout = science.dataset(dataset, 2048, seed + 2000000)
        gen = np.random.default_rng(seed + 3000000).normal(size=(100, 2048, 2)).astype(np.float32)
        independent = science.dataset(dataset, 2048, seed + 4000000)
        with np.load(folder / 'evaluation.npz', allow_pickle=False) as saved:
            for k, a in [('heldout', heldout), ('generation_noise', gen), ('independent_heldout', independent)]:
                assert np.array_equal(saved[k], a)
        hashes = {'initial_weights_sha256': digest(*(initial[k] for k in sorted(initial))),
                  'training_prefix_5000_sha256': digest(noisy[:5000], noise[:5000], timesteps[:5000]),
                  'heldout_sha256': digest(heldout), 'generation_noise_sha256': digest(gen)}
        for row in group:
            assert all(row[k] == value for k, value in hashes.items())
            assert row['source_revision'] == freeze['source_revision'] and row['device'] == 'mps'
            if row['schedule'] == 'cosine':
                assert row['updates'] == row['trajectory_terminal_updates']
        # Independent SciPy implementation of the held-out reference diagnostic.
        diagnostic = float(np.mean([wasserstein_distance(
            heldout[:, 0].astype(float) * np.cos(a) + heldout[:, 1].astype(float) * np.sin(a),
            independent[:, 0].astype(float) * np.cos(a) + independent[:, 1].astype(float) * np.sin(a)) for a in angles]))
        reported = next(r for r in summary['finite_sample_controls'] if r['dataset'] == dataset and r['seed'] == seed)
        assert abs(reported['heldout_vs_independent_sw1'] - diagnostic) < 1e-12
        groups.append({'dataset': dataset, 'seed': seed, 'cells': 4, 'regenerated_inputs_exact': True})
        controls.append({'dataset': dataset, 'seed': seed, 'reference_sw1': diagnostic})

trajectories = {}
for row in cells:
    folder = (root / row['config']).parent
    if folder in trajectories:
        continue
    cfg = json.loads((folder / 'config.json').read_text())
    result = json.loads((folder / 'result.json').read_text())
    total = cfg['total']
    assert result['status'] == 'completed' and result['last_update'] == cfg['stop'] == total
    trace = [json.loads(line) for line in (folder / 'trace.jsonl').read_text().splitlines()]
    assert [x['step'] for x in trace] == [1, *range(100, total + 1, 100)]
    for point in trace:
        lr = .0003 if cfg['policy'] == 'constant' else .0003 * (1 + math.cos(math.pi * (point['step'] - 1) / (total - 1))) / 2
        assert math.isclose(point['lr'], lr, rel_tol=1e-12, abs_tol=1e-15)
    if cfg['policy'] == 'cosine':
        assert trace[-1]['lr'] == 0
    checkpoint = torch.load(folder / 'resume.pt', map_location='cpu', weights_only=True)
    assert checkpoint['step'] == total
    assert all(int(s['step']) == total for s in checkpoint['optimizer']['state'].values())
    final = next(c for c in cells if c['config'] == row['config'] and c['updates'] == total)
    with np.load(root / final['weights'], allow_pickle=False) as weights:
        for variant, state in checkpoint['models'].items():
            assert all(np.array_equal(value.numpy(), weights[variant + '__' + name]) for name, value in state.items())
    trajectories[folder] = {'dataset': cfg['dataset'], 'seed': cfg['seed'], 'policy': cfg['policy'], 'updates': total}
assert len(trajectories) == 24 and sum(r['updates'] for r in trajectories.values()) == 200000


def statistics(row, values):
    values = np.array(values, dtype=float)
    mean, se = float(values.mean()), float(values.std(ddof=1)) / 2
    half = float(t.ppf(.975, 3)) * se
    probability = sum(abs(float(np.mean(values * signs))) >= abs(mean) - 1e-14
                      for signs in itertools.product([-1, 1], repeat=4)) / 16
    np.testing.assert_allclose(row['values'], values, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose([row['mean'], row['se']], [mean, se], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['ci95'], [mean - half, mean + half], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['leave_one_out_means'], [(float(values.sum()) - x) / 3 for x in values], rtol=1e-12, atol=1e-12)
    assert row['exact_signflip_p'] == probability and row['n'] == 4 and row['seeds_negative'] == int((values < 0).sum())


vectors = {'schedule_at_5000': [-1, 1, 0, 0], 'schedule_at_10000': [0, 0, -1, 1],
           'duration_constant': [-1, 0, 1, 0], 'duration_cosine': [0, -1, 0, 1],
           'interaction': [1, -1, -1, 1]}
for family in ('absolute_sw1', 'conditions', 'contrasts'):
    for row in summary[family]:
        seeds = list(range(4001, 4005) if row['dataset'] == 'moons' else range(5001, 5005))
        assert row['seeds'] == seeds
        matrix = np.array([[by_key[row['dataset'], s, p, u]['metrics'][row['variant']]['sw1'] for p, u in conditions] for s in seeds])
        if family == 'conditions' or row.get('target') == 'delta_vs_raw':
            matrix -= np.array([[by_key[row['dataset'], s, p, u]['metrics']['raw']['sw1'] for p, u in conditions] for s in seeds])
        coefficients = vectors[row['contrast']] if family == 'contrasts' else np.eye(4)[conditions.index((row['schedule'], row['updates']))]
        statistics(row, matrix @ coefficients)
for row in summary['coverage']:
    values = [by_key['gmm8', s, row['schedule'], row['updates']]['metrics'][row['variant']] for s in row['seeds']]
    assert row['covered_modes'] == [v['covered_modes'] for v in values]
    assert row['inlier_counts'] == [v['inlier_count'] for v in values]
    statistics(row['inlier_fraction'], [v['inlier_fraction'] for v in values])
assert [len(summary[k]) for k in ('absolute_sw1', 'conditions', 'contrasts', 'coverage')] == [24, 16, 50, 12]
result = {'status': 'pass', 'required_cells': 32, 'input_groups': groups,
          'actual_trajectories': list(trajectories.values()), 'actual_training_updates': 200000,
          'statistical_rows_checked': 102, 'finite_sample_controls': controls,
          'cosine_convention': 'Frozen denominator D-1: first applied rate .0003, final applied rate exactly zero.',
          'scope': 'Exact reference-based input regeneration, paired hashes, full optimizer/checkpoint identity, traces and 102 statistic summaries plus eight independent held-out controls. Separate original scoring verifies all 96 saved-state samples. No second training replay.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('status', 'required_cells', 'actual_training_updates', 'statistical_rows_checked')}))
