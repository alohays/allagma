"""Resumable, paired, full-batch modular-addition experiment.

Run only through inputs/compute.py. See protocol.json for frozen choices.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def revision():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def deps():
    global np, torch, F
    import numpy as np
    import torch
    import torch.nn.functional as F
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)

class Net:
    def __new__(cls, device='cpu', implementation='dense'):
        class Model(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.input = torch.nn.Linear(194, 128, bias=False)
                self.output = torch.nn.Linear(128, 97, bias=False)
                self.implementation = implementation

            def forward(self, x):
                if self.implementation == 'gather':
                    h = self.input.weight[:, x[:, 0]].T + self.input.weight[:, 97 + x[:, 1]].T
                else:
                    h = self.input(x)
                return self.output(F.relu(h))
        return Model().to(device=device, dtype=torch.float32)

def data(seed):
    pairs = np.array([(a, b) for a in range(97) for b in range(97)], dtype=np.int64)
    labels = (pairs[:, 0] + pairs[:, 1]) % 97
    p = np.random.Generator(np.random.PCG64(seed)).permutation(len(pairs))
    return pairs, labels, p[:2822].copy(), p[2822:].copy()

def inputs(pairs, device, implementation):
    p = torch.as_tensor(pairs.copy(), device=device)
    if implementation == 'gather':
        return p
    return torch.cat((F.one_hot(p[:, 0], 97), F.one_hot(p[:, 1], 97)), dim=1).float()

def sync(device):
    if device == 'mps':
        torch.mps.synchronize()

def state_cpu(state):
    if torch.is_tensor(state):
        return state.detach().cpu()
    if isinstance(state, dict):
        return {k: state_cpu(v) for k, v in state.items()}
    if isinstance(state, list):
        return [state_cpu(x) for x in state]
    return state

def save_checkpoint(path, model, optimizer, step, config, curve):
    tmp = Path(str(path) + '.tmp')
    torch.save(dict(model=state_cpu(model.state_dict()), optimizer=state_cpu(optimizer.state_dict()),
                    step=step, config=config, curve=curve), tmp)
    tmp.replace(path)

def evaluate(model, x, y, train_idx, test_idx, step):
    with torch.no_grad():
        logits = model(x)
        result = dict(step=step)
        for prefix, idx in [('train', train_idx), ('test', test_idx)]:
            z, target = logits[idx], y[idx]
            result[prefix + '_loss'] = float(F.cross_entropy(z, target).cpu())
            result[prefix + '_accuracy'] = float((z.argmax(1) == target).float().mean().cpu())
    return result

def run(args):
    folder = Path(args.output) / ('pilot' if args.seed == 61 else 'confirmation') / f'seed_{args.seed}_wd_{args.wd}'
    folder.mkdir(parents=True, exist_ok=True)
    config = dict(seed=args.seed, weight_decay=args.wd, horizon=100000, dtype='float32',
                  device=args.device, implementation=args.implementation, learning_rate=.001,
                  betas=[.9, .98], epsilon=1e-8, full_batch=True,
                  architecture='Linear(194,128,bias=False),ReLU,Linear(128,97,bias=False)',
                  evaluation_interval=100, source_revision=revision())
    if args.seed != 61:
        protocol = json.loads(Path(args.protocol).read_text())
        assert protocol['frozen'] is True
        assert protocol['backend']['device'] == args.device
        assert protocol['backend']['implementation'] == args.implementation
        config['protocol_sha256'] = sha(args.protocol)
    pairs, labels, train, test = data(args.seed)
    torch.manual_seed(args.seed)
    model = Net('cpu', args.implementation)
    init_path = folder / 'initial_weights.npz'
    if not init_path.exists():
        np.savez(init_path, input_weight=model.input.weight.detach().numpy(), output_weight=model.output.weight.detach().numpy())
        np.savez(folder / 'partition.npz', pairs=pairs, labels=labels, train_indices=train, test_indices=test)
    config['initial_weights_sha256'] = sha(init_path)
    model = model.to(args.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, betas=(.9, .98), eps=1e-8,
                                 weight_decay=args.wd, foreach=False)
    x = inputs(pairs, args.device, args.implementation)
    y = torch.as_tensor(labels, device=args.device)
    ti = torch.as_tensor(train, device=args.device)
    vi = torch.as_tensor(test, device=args.device)
    xt, yt = x[ti], y[ti]
    checkpoint = folder / 'checkpoint.pt'
    if checkpoint.exists():
        ck = torch.load(checkpoint, map_location=args.device, weights_only=False)
        for k in ('seed', 'weight_decay', 'device', 'implementation', 'source_revision'):
            assert ck['config'][k] == config[k], (k, ck['config'][k], config[k])
        model.load_state_dict(ck['model'])
        optimizer.load_state_dict(ck['optimizer'])
        step, curve = ck['step'], ck['curve']
    else:
        step, curve = 0, [evaluate(model, x, y, ti, vi, 0)]
        save_checkpoint(checkpoint, model, optimizer, step, config, curve)
    dump(folder / 'config.json', config)
    dump(folder / 'curve.json', curve)
    start_step = step
    sync(args.device)
    begin = time.monotonic()
    print(json.dumps(dict(event='started', seed=args.seed, wd=args.wd, start_step=step, target=args.target)), flush=True)
    while step < args.target:
        optimizer.zero_grad(set_to_none=True)
        F.cross_entropy(model(xt), yt).backward()
        optimizer.step()
        step += 1
        if step % 100 == 0:
            curve.append(evaluate(model, x, y, ti, vi, step))
            if step % 1000 == 0:
                save_checkpoint(checkpoint, model, optimizer, step, config, curve)
                dump(folder / 'curve.json', curve)
                print(json.dumps(dict(event='checkpoint', step=step, elapsed_seconds=time.monotonic()-begin)), flush=True)
            if time.monotonic() - begin >= args.seconds:
                break
    sync(args.device)
    elapsed = time.monotonic()-begin
    save_checkpoint(checkpoint, model, optimizer, step, config, curve)
    dump(folder / 'curve.json', curve)
    with torch.no_grad():
        logits = model(x).cpu().numpy()
    np.savez(folder / 'arrays.npz', pairs=pairs, labels=labels, train_indices=train, test_indices=test,
             logits=logits, predictions=logits.argmax(1))
    np.savez(folder / 'weights.npz', input_weight=model.input.weight.detach().cpu().numpy(),
             output_weight=model.output.weight.detach().cpu().numpy())
    summary = dict(seed=args.seed, weight_decay=args.wd, start_step=start_step, updates=step,
                   target=args.target, elapsed_seconds=elapsed, seconds_per_update=elapsed/max(1,step-start_step),
                   metrics=curve[-1], config=config, attempt_label=args.label)
    dump(folder / 'endpoint.json', summary)
    log = Path(args.output) / 'segments.jsonl'
    with log.open('a') as f:
        f.write(json.dumps(summary)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('config','metrics')}), flush=True)

def qualify(args):
    """Only pilot data; never uses held-out outcomes for tuning."""
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    pairs, labels, train, test = data(61)
    assert pairs.shape == (9409, 2)
    assert len(train) == 2822 and len(test) == 6587
    assert len(np.unique(np.r_[train,test])) == 9409
    assert not np.intersect1d(train,test).size
    for a,b,c in [(0,0,0),(96,96,95),(96,1,0),(48,49,0),(10,20,30),(0,96,96)]:
        assert labels[a*97+b] == c
    for a in range(97):
        for b in range(97):
            assert int(labels[a*97+b]) == (a+b)%97
    rows=[]
    reference=None
    for device in ['cpu','mps']:
        if device=='mps' and not torch.backends.mps.is_available():
            continue
        for implementation in ['dense','gather']:
            torch.manual_seed(61)
            model=Net('cpu',implementation).to(device)
            x=inputs(pairs[train],device,implementation)
            y=torch.as_tensor(labels[train],device=device)
            opt=torch.optim.AdamW(model.parameters(),lr=.001,betas=(.9,.98),eps=1e-8,weight_decay=1,foreach=False)
            with torch.no_grad():
                z=model(x).cpu().numpy()
            initial_diff=0.0 if reference is None else float(np.max(np.abs(z-reference)))
            if reference is None: reference=z.copy()
            assert initial_diff < 2e-6, initial_diff
            sync(device)
            begin=time.monotonic()
            for i in range(args.benchmark_steps):
                opt.zero_grad(set_to_none=True)
                F.cross_entropy(model(x),y).backward()
                opt.step()
            sync(device)
            duration=time.monotonic()-begin
            rows.append(dict(device=device,implementation=implementation,steps=args.benchmark_steps,
                             seconds=duration,seconds_per_update=duration/args.benchmark_steps,
                             initial_logits_max_abs_difference=initial_diff))
            print(json.dumps(rows[-1]),flush=True)
    dump(out/'qualification.json',dict(known_answer_checks='passed; six explicit examples and all 9409 labels',
        partition_checks='passed; 2822 train, 6587 held out, disjoint exhaustive',
        benchmark=rows,torch_version=torch.__version__,numpy_version=np.__version__,
        threads=torch.get_num_threads(),source_revision=revision()))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['run','qualify'])
    p.add_argument('--output',default='artifacts')
    p.add_argument('--seed',type=int,default=61)
    p.add_argument('--wd',type=int,choices=[0,1],default=1)
    p.add_argument('--device',choices=['cpu','mps'],default='cpu')
    p.add_argument('--implementation',choices=['dense','gather'],default='dense')
    p.add_argument('--target',type=int,default=100000)
    p.add_argument('--seconds',type=float,default=120)
    p.add_argument('--benchmark-steps',type=int,default=300)
    p.add_argument('--protocol',default='protocol.json')
    p.add_argument('--label',default='unspecified')
    args=p.parse_args()
    print(json.dumps(dict(event='importing',mode=args.mode,label=args.label)),flush=True)
    deps()
    run(args) if args.mode=='run' else qualify(args)

if __name__ == '__main__':
    main()
