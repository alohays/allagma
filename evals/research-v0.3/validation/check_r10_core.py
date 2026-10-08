"""Independent r10 source, graph, partition and fresh-execution checks."""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from core_graph import predictions

root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new validation receipt')
original = root / 'inputs/materials/capsule-6460826'
adapted = root / 'work/capsule'
def files(folder):
    return {str(p.relative_to(folder)): p for p in folder.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}
before, after = files(original), files(adapted)
assert set(before) == set(after)
changes = []
for name in before:
    old, new = before[name].read_bytes(), after[name].read_bytes()
    if old == new:
        continue
    assert name in ('code/wine_sample.py', 'code/zoo_sample.py')
    dataset = 'wine' if 'wine' in name else 'zoo'
    expected = b'from pathlib import Path\n' + old.replace(
        ("'/data/" + dataset + ".txt'").encode(),
        ("Path(__file__).resolve().parents[1] / 'data/" + dataset + ".txt'").encode(), 1)
    assert new == expected
    changes.append(name)
assert len(changes) == 2
measurements = json.loads((root / 'measurements.json').read_text())['runs']
observations = []
array_count = 0
prediction_count = 0
for run in measurements:
    fresh_dirs = list((root / 'reproductions/verification/raw').glob(run['dataset'] + '*'))
    assert len(fresh_dirs) == 1
    for call in run['calls']:
        path = root / call['arrays']
        with np.load(path, allow_pickle=False) as saved, np.load(fresh_dirs[0] / path.name, allow_pickle=False) as fresh:
            data = {k: saved[k] for k in saved.files}
            assert set(saved.files) == set(fresh.files)
            for name in saved.files:
                assert np.array_equal(saved[name], fresh[name]); array_count += 1
        full = data['full_data']
        order = np.random.RandomState(42).permutation(len(full))
        ntest = math.ceil(.2 * len(full))
        test_indices, train_indices = order[:ntest], order[ntest:]
        assert np.array_equal(data['y_train'], data['full_labels'][train_indices])
        assert np.array_equal(data['y_test'], data['full_labels'][test_indices])
        train, test = full[train_indices], full[test_indices]
        if run['dataset'] == 'wine':
            mean, sd = train.mean(0), train.std(0)
            assert (sd > 0).all()
            train, test = (train - mean) / sd, (test - mean) / sd
        np.testing.assert_allclose(data['X_train'], train, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(data['X_test'], test, rtol=1e-12, atol=1e-12)
        predictor = 'CS' if run['dataset'] != 'wine' else call['printed_label']
        assert call['executed_predictor'] == predictor
        assert np.array_equal(predictions(data, predictor), data['prediction'])
        percent = round(100 * float(np.mean(data['prediction'] == data['y_test'])), 2)
        assert call['metrics']['accuracy_percent'] == percent
        assert percent == (100. if run['dataset'] != 'wine' or predictor == 'CS' else 97.22)
        prediction_count += len(data['prediction'])
        observations.append({'dataset': run['dataset'], 'printed': call['printed_label'],
                             'actual': predictor, 'accuracy_percent': percent})
assert len(observations) == 12 and array_count == 108 and prediction_count == 348
result = {'status': 'pass', 'only_portability_edits': sorted(changes), 'observations': observations,
          'fresh_arrays_exactly_equal': array_count, 'fresh_predictions_exactly_equal': prediction_count,
          'scope': 'Exact input/source preservation except the two documented path edits/imports; independent splits, normalization and adjacency-set predictors; equality of all saved original/fresh arrays. No population-performance or unique tied-neighbor reconstruction claim.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': 'pass', 'calls_checked': len(observations), 'fresh_arrays': array_count}))
