"""Bounded modular-addition experiment. All execution goes through inputs/compute.py."""
import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def imports():
    global np, torch, F
    import numpy as np
    import torch
    import torch.nn.functional as F
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)


def dataset(seed):
    pairs = np.array([(a, b) for a in range(97) for b in range(97)], dtype=np.int64)
    labels = (pairs[:, 0] + pairs[:, 1]) % 97
    order = np.random.Generator(np.random.PCG64(seed)).permutation(9409)
    return pairs, labels, order[:2822], order[2822:]


def model(seed, device):
    torch.manual_seed(seed)
    net = torch.nn.Sequential(torch.nn.Linear(194, 128, bias=False), torch.nn.ReLU(),
                              torch.nn.Linear(128, 97, bias=False))
    return net.to(device)


def tensors(seed, device):
    pairs, labels, tr, te = dataset(seed)
    p = torch.tensor(pairs, device=device)
    x = torch.cat((F.one_hot(p[:, 0], 97), F.one_hot(p[:, 1], 97)), 1).float()
    y = torch.tensor(labels, device=device)
    return x, y, torch.tensor(tr, device=device), torch.tensor(te, device=device)


def sync(device):
    if device == 'mps':
        torch.mps.synchronize()


def step(net, opt, x, y):
    opt.zero_grad(set_to_none=True)
    loss = F.cross_entropy(net(x), y)
    loss.backward()
    opt.step()


def evaluate(net, x, y, tr, te, update):
    with torch.no_grad():
        logits = net(x)
        result = {'step': update}
        for prefix, idx in [('train', tr), ('test', te)]:
            z, target = logits[idx], y[idx]
            result[prefix + '_loss'] = float(F.cross_entropy(z, target).item())
            result[prefix + '_accuracy'] = float((z.argmax(1) == target).float().mean().item())
    return result


def pilot(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'started.json', {'seed': 61, 'phase': 'pilot', 'time': time.time(),
                                     'argv': sys.argv, 'source_sha256': sha(__file__)})
    print('Pilot attempt started; evidence directory: ' + str(out), flush=True)
    imports()
    pairs, labels, tr, te = dataset(61)
    assert len(tr) == 2822 and len(te) == 6587
    assert len(np.unique(np.concatenate((tr, te)))) == 9409
    assert len(set(map(tuple, pairs))) == 9409
    for a, b, answer in [(0, 0, 0), (96, 96, 95), (96, 1, 0), (45, 52, 0), (96, 0, 96), (3, 4, 7)]:
        assert labels[a * 97 + b] == answer
    np.savez(out / 'partition.npz', pairs=pairs, labels=labels, train_indices=tr, test_indices=te)
    environment = {'python': sys.version, 'torch': torch.__version__, 'numpy': np.__version__,
                   'platform': platform.platform(), 'machine': platform.machine(),
                   'torch_threads': torch.get_num_threads(), 'mps_available': torch.backends.mps.is_available()}
    write_json(out / 'environment.json', environment)
    results = []
    for device in ['cpu', 'mps']:
        if device == 'mps' and not torch.backends.mps.is_available():
            continue
        for fused in ([False, True] if device == 'cpu' else [False]):
            x, y, ti, vi = tensors(61, device)
            net = model(61, device)
            opt = torch.optim.AdamW(net.parameters(), lr=.001, betas=(.9, .98), eps=1e-8,
                                    weight_decay=1, fused=fused, foreach=False)
            train_x, train_y = x[ti], y[ti]
            curve = [evaluate(net, x, y, ti, vi, 0)]
            torch.save({'model': net.state_dict(), 'optimizer': opt.state_dict(), 'step': 0}, out / (device + str(fused) + '-initial.pt'))
            sync(device)
            start = time.perf_counter()
            for i in range(1, args.steps + 1):
                step(net, opt, train_x, train_y)
                if i % 100 == 0:
                    curve.append(evaluate(net, x, y, ti, vi, i))
                    write_json(out / (device + str(fused) + '-curve.json'), curve)
            sync(device)
            seconds = time.perf_counter() - start
            result = {'device': device, 'fused': fused, 'steps': args.steps, 'seconds': seconds,
                      'seconds_per_update_including_evaluation': seconds / args.steps,
                      'projected_800000_updates_seconds': seconds / args.steps * 800000}
            results.append(result)
            write_json(out / 'timing.json', results)
            torch.save({'model': net.state_dict(), 'optimizer': opt.state_dict(), 'step': args.steps}, out / (device + str(fused) + '-final.pt'))
            print(json.dumps(result), flush=True)
    write_json(out / 'checks.json', {'known_answer_labels': True, 'full_disjoint_split': True,
                                     'unique_ordered_pairs': True, 'train_n': 2822, 'test_n': 6587})


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('pilot')
    p.add_argument('--output', required=True)
    p.add_argument('--steps', type=int, default=300)
    args = parser.parse_args()
    if args.command == 'pilot':
        pilot(args)


if __name__ == '__main__':
    main()
