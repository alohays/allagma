"""Independent r09 source, split, graph-score and fresh-array comparisons."""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new validation receipt')


def inventory(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


original = root / 'source/original'
adapted = root / 'source/adapted'
supplied = root / 'inputs/materials/capsule-6460826'
assert inventory(original) == inventory(supplied)
assert set(inventory(original)) == set(inventory(adapted))
changes = []
for name in inventory(original):
    before, after = (original / name).read_bytes(), (adapted / name).read_bytes()
    if before == after:
        continue
    assert name in ('code/wine_sample.py', 'code/zoo_sample.py')
    dataset = 'wine' if 'wine' in name else 'zoo'
    expected = before.replace(b'import pandas\n', b'import pandas\nfrom pathlib import Path\n', 1)
    expected = expected.replace(("'/data/" + dataset + ".txt'").encode(),
                                ("Path(__file__).resolve().parents[1] / 'data' / '" + dataset + ".txt'").encode(), 1)
    assert after == expected
    changes.append(name)
assert len(changes) == 2


def independent_predictions(data, predictor):
    train, test = len(data['train']), len(data['test'])
    classes = len(np.unique(data['train_labels']))
    adjacent = [set() for _ in range(train + test + classes)]
    for a, b in data['graph_edges']:
        adjacent[int(a)].add(int(b)); adjacent[int(b)].add(int(a))
    degree = [len(a) + int(i in a) for i, a in enumerate(adjacent)]
    def common(a, b):
        return (adjacent[a] & adjacent[b]) - {a, b}
    scores = np.zeros((test, classes))
    for row, node in enumerate(range(train, train + test)):
        for label, class_node in enumerate(range(train + test, len(adjacent))):
            shared = common(node, class_node)
            if predictor == 'CN':
                value = len(shared)
            elif predictor == 'AA':
                value = sum(1 / (math.log(degree[v]) + 1e-9) for v in sorted(shared))
            elif predictor == 'RA':
                value = sum(1 / degree[v] for v in sorted(shared))
            else:
                assert predictor == 'CS'
                value = sum(1 / (degree[v] - len(common(v, class_node)))
                            + 1 / (degree[v] - len(common(v, node))) for v in sorted(shared))
            scores[row, label] = value
    return scores.argmax(axis=1)


index = json.loads((root / 'evidence/run-index.json').read_text())
fresh = json.loads((root / 'reproduction/fresh-check/run-index.json').read_text())
fresh_by_dataset = {r['dataset']: r for r in fresh['runs']}
observations = []
arrays_compared = 0
predictions_compared = 0
for run in index['runs']:
    folder = root / run['directory']
    record = json.loads((folder / 'run.json').read_text())
    assert record['status'] == 'completed' and len(record['calls']) == 4
    fresh_record = json.loads((root / fresh_by_dataset[run['dataset']]['directory'] / 'run.json').read_text())
    for call, replay in zip(record['calls'], fresh_record['calls']):
        with np.load(root / call['arrays'], allow_pickle=False) as saved, np.load(root / replay['arrays'], allow_pickle=False) as repeated:
            data = {k: saved[k] for k in saved.files}
            assert set(saved.files) == set(repeated.files)
            for key in saved.files:
                assert np.array_equal(saved[key], repeated[key]); arrays_compared += 1
        n = len(data['raw_data'])
        permutation = np.random.RandomState(42).permutation(n)
        ntest = int(math.ceil(.2 * n))
        test_indices, train_indices = permutation[:ntest], permutation[ntest:]
        assert np.array_equal(data['train_labels'], data['raw_labels'][train_indices])
        assert np.array_equal(data['test_labels'], data['raw_labels'][test_indices])
        train, test = data['raw_data'][train_indices], data['raw_data'][test_indices]
        if run['dataset'] == 'wine':
            mean, scale = train.mean(0), train.std(0)
            train, test = (train - mean) / scale, (test - mean) / scale
        np.testing.assert_allclose(data['train'], train, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(data['test'], test, rtol=1e-12, atol=1e-12)
        predictor = 'CS' if run['dataset'] in ('iris', 'zoo') else call['display_predictor']
        assert call['actual_predictor'] == predictor
        assert np.array_equal(independent_predictions(data, predictor), data['prediction'])
        percent = round(100 * float(np.mean(data['prediction'] == data['test_labels'])), 2)
        expected = 100.0 if run['dataset'] != 'wine' or predictor == 'CS' else 97.22
        assert percent == expected
        predictions_compared += len(data['prediction'])
        observations.append({'dataset': run['dataset'], 'printed': call['display_predictor'],
                             'actual': predictor, 'accuracy_percent': percent,
                             'independent_predictions_match': True})
assert len(observations) == 12 and arrays_compared == 96 and predictions_compared == 348
result = {'status': 'pass', 'only_portability_edits': sorted(changes),
          'observations': observations, 'fresh_numeric_arrays_equal': arrays_compared,
          'fresh_predictions_equal': predictions_compared,
          'scope': 'Exact source/data preservation except two documented paths/imports; independent fixed splits, Wine normalization, adjacency-set predictor equations including self-loop degrees and endpoint exclusions; fresh-run arrays. No population-performance or unique tied-neighbor graph reconstruction claim.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': 'pass', 'calls_checked': len(observations),
                  'fresh_numeric_arrays_equal': arrays_compared, 'fresh_predictions_equal': predictions_compared}))
