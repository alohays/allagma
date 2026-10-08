"""CPU qualification after an interrupted pilot and a failed MPS probe."""
import copy
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import study as s


def main():
    out = Path('artifacts/pilot/attempt-03')
    out.mkdir(parents=True, exist_ok=True)
    s.write_json(out / 'started.json', {'time': time.time(), 'seed': 61, 'phase': 'pilot'})
    s.imports()
    np, torch, F = s.np, s.torch, s.F
    x, y, tr, te = s.tensors(61, 'cpu')
    pairs, labels, tri, tei = s.dataset(61)
    assert len(tri) == 2822 and len(tei) == 6587
    assert np.array_equal(np.sort(np.r_[tri, tei]), np.arange(9409))
    assert np.all(labels == np.array([(int(a) + int(b)) % 97 for a, b in pairs]))
    for a, b, answer in [(0, 0, 0), (96, 96, 95), (96, 1, 0), (45, 52, 0), (96, 0, 96), (3, 4, 7)]:
        assert int(y[a * 97 + b]) == answer
    assert torch.all(x.sum(1) == 2) and x.dtype == torch.float32
    net = s.model(61, 'cpu')
    assert sum(p.numel() for p in net.parameters()) == 37248
    assert list(net.state_dict()) == ['0.weight', '2.weight']
    assert all(p.dtype == torch.float32 for p in net.parameters())
    # Explicit concatenated one-hot Linear output agrees with the algebraic lookup.
    z = net(x)
    h = torch.relu(net[0].weight[:, pairs[:, 0]].T + net[0].weight[:, 97 + pairs[:, 1]].T)
    assert torch.allclose(z, h @ net[2].weight.T, atol=1e-7, rtol=1e-5)
    # Paired initialization is byte-identical, and split is seed-dependent.
    twin = s.model(61, 'cpu')
    assert all(torch.equal(a, b) for a, b in zip(net.parameters(), twin.parameters()))
    assert not np.array_equal(tri, s.dataset(62)[2])
    # Compare the actual AdamW implementation against an independent first-update formula.
    tx, ty = x[tr], y[tr]
    first_update_errors = {}
    for wd in (0, 1):
        one = s.model(61, 'cpu')
        opt = torch.optim.AdamW(one.parameters(), lr=.001, betas=(.9, .98), eps=1e-8,
                                weight_decay=wd, fused=False, foreach=False)
        before = [p.detach().clone() for p in one.parameters()]
        F.cross_entropy(one(tx), ty).backward()
        expected = [p * (1 - .001 * wd) - .001 * v.grad / (v.grad.abs() + 1e-8)
                    for p, v in zip(before, one.parameters())]
        opt.step()
        err = max(float((a-b).abs().max()) for a, b in zip(one.parameters(), expected))
        assert err < 3e-8
        first_update_errors[str(wd)] = err
    # Long enough to measure steady-state CPU execution, with the exact evaluation cadence.
    opt = torch.optim.AdamW(net.parameters(), lr=.001, betas=(.9, .98), eps=1e-8,
                            weight_decay=1, fused=False, foreach=False)
    curve = [s.evaluate(net, x, y, tr, te, 0)]
    start = time.perf_counter()
    for update in range(1, 5001):
        s.step(net, opt, tx, ty)
        if update == 1000:
            torch.save({'model': net.state_dict(), 'optimizer': opt.state_dict(), 'step': update}, out / 'resume-test.pt')
        if update == 1100:
            reference = copy.deepcopy(net.state_dict())
        if update % 100 == 0:
            curve.append(s.evaluate(net, x, y, tr, te, update))
    seconds = time.perf_counter() - start
    torch.save({'model': net.state_dict(), 'optimizer': opt.state_dict(), 'step': 5000}, out / 'final.pt')
    s.write_json(out / 'curve.json', curve)
    resume = s.model(61, 'cpu')
    ropt = torch.optim.AdamW(resume.parameters(), lr=.001, betas=(.9, .98), eps=1e-8,
                             weight_decay=1, fused=False, foreach=False)
    saved = torch.load(out / 'resume-test.pt', weights_only=True)
    resume.load_state_dict(saved['model'])
    ropt.load_state_dict(saved['optimizer'])
    for _ in range(100):
        s.step(resume, ropt, tx, ty)
    assert all(torch.equal(reference[k], resume.state_dict()[k]) for k in reference)
    # Changing held-out labels cannot alter an update because only training tensors are passed.
    altered = y.clone()
    altered[te] = (altered[te] + 1) % 97
    assert torch.equal(ty, altered[tr])
    s.write_json(out / 'qualification.json', {
        'passed': True, 'seed': 61, 'device': 'cpu', 'fused': False,
        'checks': ['six_known_answer_labels', 'all_9409_labels_independent_loop',
                   'exact_disjoint_complete_split', 'one_hot_shape_and_values', '37248_bias_free_parameters',
                   'float32', 'linear_lookup_equivalence', 'paired_initialization',
                   'seed_dependent_partition', 'AdamW_first_update_formula_both_decays',
                   'checkpoint_resume_bitwise_100_steps', 'heldout_labels_excluded_from_train_tensors'],
        'adamw_first_update_max_errors': first_update_errors,
        'timing': {'updates': 5000, 'seconds': seconds, 'seconds_per_update': seconds / 5000,
                   'projected_800000_update_seconds': seconds / 5000 * 800000},
        'environment': {'python': sys.version, 'torch': torch.__version__, 'numpy': np.__version__,
                        'platform': platform.platform(), 'threads': torch.get_num_threads()},
        'source_sha256': {p.name: s.sha(p) for p in [Path(__file__), Path('src/study.py')]}})
    (out / 'pip-freeze.txt').write_text(subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True))
    print((out / 'qualification.json').read_text(), flush=True)


if __name__ == '__main__':
    main()
