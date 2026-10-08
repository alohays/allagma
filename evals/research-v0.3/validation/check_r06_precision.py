"""Independent float64-forward diagnostic for r06's reported class near ties."""
import json
from pathlib import Path
import sys

import numpy as np

root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new verification receipt')
measurements = json.loads((root / 'analysis/measurements.json').read_text())
unit = 2 ** -24
gamma_first = 194 * unit / (1 - 194 * unit)
gamma_second = 128 * unit / (1 - 128 * unit)
observations = []
total_disagreements = 0
for run in measurements['runs']:
    with np.load(root / run['arrays'], allow_pickle=False) as data, np.load(root / run['weights'], allow_pickle=False) as weights:
        pairs, labels = data['pairs'], data['labels']
        retained, pred32 = data['logits'].astype(np.float64), data['predictions']
        wi, wo = weights['input_weight'].astype(np.float64), weights['output_weight'].astype(np.float64)
        hidden = np.maximum(wi[:, pairs[:, 0]].T + wi[:, 97 + pairs[:, 1]].T, 0)
        forward = hidden @ wo.T
        first_bound = gamma_first * (np.abs(wi[:, pairs[:, 0]].T) + np.abs(wi[:, 97 + pairs[:, 1]].T))
        bound = first_bound @ np.abs(wo).T + gamma_second * ((np.abs(hidden) + first_bound) @ np.abs(wo).T)
        errors = np.abs(forward - retained)
        assert (errors <= bound + 1e-10).all()
        pred64 = forward.argmax(1)
        changes = np.flatnonzero(pred64 != pred32)
        assert np.array_equal(pred32 == labels, pred64 == labels)
        assert not np.isin(changes, data['train_indices']).any()
        for i in changes:
            margin = forward[i, pred64[i]] - forward[i, pred32[i]]
            assert margin <= bound[i, pred64[i]] + bound[i, pred32[i]] + 1e-10
        total_disagreements += len(changes)
        observations.append({'seed': run['seed'], 'weight_decay': run['weight_decay'],
                             'changed_example_indices': changes.tolist(),
                             'classification_correctness_unchanged': True,
                             'maximum_logit_error': float(errors.max()),
                             'maximum_error_bound_ratio': float(np.max(errors / np.maximum(bound, 1e-30)))})
assert total_disagreements == 5
result = {'status': 'pass', 'total_changed_argmax': total_disagreements,
          'all_changes_between_wrong_heldout_classes': True, 'observations': observations,
          'scope': 'Independent double-precision forward and propagated float32 dot-product error bound on every endpoint. Confirms the reported five auxiliary class-choice changes without changing float32 endpoints or inferring equivalence of float64 training.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
