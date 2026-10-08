"""Independent black-box checks of r05's inspected, retained CPU library.

No candidate Python module is imported. PyTorch autograd/AdamW provide the
reference for full-batch gradients and individual updates at varied optimizer
ages. This checks local equations, not bitwise long-horizon trajectory identity.
"""
import ctypes
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch
import torch.nn.functional as functional


root, output = (Path(p).resolve() for p in sys.argv[1:3])
if output.exists():
    raise RuntimeError('Use a new verification receipt')
protocol = json.loads((root / 'campaigns/modular-addition/protocol.json').read_text())
source = root / 'study/engine.c'
assert hashlib.sha256(source.read_bytes()).hexdigest() == protocol['training_source_hashes']['study/engine.c']
library = root / 'build/engine.dylib'
lib = ctypes.CDLL(str(library))
fp = ctypes.POINTER(ctypes.c_float)
ip = ctypes.POINTER(ctypes.c_int)
lib.engine_create.argtypes = [ctypes.c_int]
lib.engine_create.restype = ctypes.c_void_p
lib.engine_free.argtypes = [ctypes.c_void_p]
lib.engine_grad.argtypes = [ctypes.c_void_p, ip, ip, fp, fp, fp, fp]
lib.engine_steps.argtypes = [ctypes.c_void_p, ip, ip, fp, fp, fp, fp, fp, fp,
                             ctypes.c_int, ctypes.c_int, ctypes.c_float]

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
pairs = np.array([(a, b) for a in range(97) for b in range(97)], dtype=np.int32)
selected = np.random.default_rng(61).permutation(9409)[:2822]
pairs = np.ascontiguousarray(pairs[selected])
labels = np.ascontiguousarray(pairs.sum(axis=1) % 97, dtype=np.int32)
features = functional.one_hot(torch.from_numpy(pairs.astype(np.int64)), 97).float().reshape(-1, 194)
targets = torch.from_numpy(labels.astype(np.int64))
generator = np.random.default_rng(9102)
observations = []
work = lib.engine_create(len(pairs))
assert work


def ptr(value, dtype=fp):
    assert value.flags.c_contiguous
    return value.ctypes.data_as(dtype)


try:
    for start in (0, 19, 99999):
        for wd in (0, 1):
            torch.manual_seed(61)
            model = torch.nn.Sequential(torch.nn.Linear(194, 128, bias=False),
                                        torch.nn.ReLU(), torch.nn.Linear(128, 97, bias=False))
            optimizer = torch.optim.AdamW(model.parameters(), lr=.001, betas=(.9, .98),
                                          eps=1e-8, weight_decay=wd, foreach=False)
            u = np.ascontiguousarray(model[0].weight.detach().numpy().T)
            v = model[2].weight.detach().numpy().copy()
            moments = []
            for parameter, array, transpose in ((model[0].weight, u, True), (model[2].weight, v, False)):
                m = np.ascontiguousarray(generator.normal(0, .0001, array.shape), dtype=np.float32) if start else np.zeros_like(array)
                q = np.ascontiguousarray(generator.uniform(.00001, .00002, array.shape), dtype=np.float32) if start else np.zeros_like(array)
                optimizer.state[parameter] = {
                    'step': torch.tensor(float(start)),
                    'exp_avg': torch.from_numpy(m.T.copy() if transpose else m.copy()),
                    'exp_avg_sq': torch.from_numpy(q.T.copy() if transpose else q.copy()),
                }
                moments.extend((m, q))
            functional.cross_entropy(model(features), targets).backward()
            g1, g2 = np.empty_like(u), np.empty_like(v)
            lib.engine_grad(work, ptr(pairs, ip), ptr(labels, ip), ptr(u), ptr(v), ptr(g1), ptr(g2))
            reference_gradients = (model[0].weight.grad.numpy().T, model[2].weight.grad.numpy())
            for actual, expected in zip((g1, g2), reference_gradients):
                np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=1e-4)
            gradient_error = max(float(np.max(np.abs(a - b))) for a, b in zip((g1, g2), reference_gradients))
            optimizer.step()
            lib.engine_steps(work, ptr(pairs, ip), ptr(labels, ip), ptr(u), ptr(v),
                             *[ptr(m) for m in moments], start, 1, wd)
            expected_weights = (model[0].weight.detach().numpy().T, model[2].weight.detach().numpy())
            for actual, expected in zip((u, v), expected_weights):
                np.testing.assert_allclose(actual, expected, atol=1e-6, rtol=1e-5)
            expected_moments = []
            for parameter, transpose in ((model[0].weight, True), (model[2].weight, False)):
                for name in ('exp_avg', 'exp_avg_sq'):
                    value = optimizer.state[parameter][name].numpy()
                    expected_moments.append(value.T if transpose else value)
            for actual, expected in zip(moments, expected_moments):
                np.testing.assert_allclose(actual, expected, atol=1e-9, rtol=1e-5)
            observations.append({'prior_updates': start, 'weight_decay': wd,
                                 'maximum_gradient_error': gradient_error,
                                 'maximum_updated_weight_error': max(float(np.max(np.abs(a - b))) for a, b in zip((u, v), expected_weights))})
finally:
    lib.engine_free(work)

result = {'status': 'pass', 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'library_sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
          'observations': observations, 'pilot_seed': 61,
          'scope': 'Independent PyTorch gradients and one AdamW update from matched weights/moments at optimizer ages 0, 19 and 99999 for both decay conditions. Full 2822-example batch. Source/library were inspected; no candidate Python imported. This does not establish bitwise long-horizon equivalence or replay confirmation training.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'cases': len(observations), 'observations': observations}))
