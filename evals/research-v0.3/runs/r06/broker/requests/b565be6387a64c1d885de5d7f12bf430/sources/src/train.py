"""Frozen CPU training, atomic segment recovery, and complete evidence retention."""
import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import study as s


def rel(path):
    return str(Path(path).as_posix())


def freeze(root):
    folder = root / 'frozen'
    if folder.exists():
        raise RuntimeError('Refusing to overwrite a frozen protocol')
    qualification = json.loads(Path('artifacts/pilot/attempt-03/qualification.json').read_text())
    assert qualification['passed']
    folder.mkdir(parents=True)
    sources = {}
    for name in ['src/study.py', 'src/train.py', 'src/qualify.py', 'PROTOCOL.md']:
        path = Path(name)
        dest = folder / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        sources[name] = s.sha(path)
    revision = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    protocol = {
        'format': 'modular-addition-protocol-v1', 'task_id': 'modular-addition',
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_revision': 'sha256:' + revision, 'source_hashes': sources,
        'specification': rel(folder / 'source/PROTOCOL.md'),
        'qualification': 'artifacts/pilot/attempt-03/qualification.json',
        'seeds': [1001, 1002, 1003, 1004], 'weight_decays': [0, 1],
        'horizon': 100000, 'evaluation_interval': 100, 'checkpoint_interval': 5000,
        'device': 'cpu', 'dtype': 'float32', 'train_size': 2822, 'test_size': 6587,
        'split_generator': 'numpy.Generator(PCG64(seed))',
        'initialization': 'torch.manual_seed(seed); default bias-free Linear initialization',
        'optimizer': {'name': 'AdamW', 'lr': .001, 'betas': [.9, .98], 'eps': 1e-8,
                      'fused': False, 'foreach': False},
        'primary': {'memorization_threshold': .99, 'generalization_threshold': .95,
                    'sustain_evaluations': 3, 'lag_minimum': 1000,
                    'test_accuracy_at_memorization_maximum': .50,
                    'training_must_persist_at_generalization': True},
        'uncertainty': 'paired Student-t 95% CI and exact two-sided sign-flip reference test',
        'qualification_timing': qualification['timing']}
    s.write_json(folder / 'protocol.json', protocol)
    shutil.copyfile('artifacts/pilot/attempt-03/qualification.json', folder / 'qualification.json')
    shutil.copyfile('artifacts/pilot/attempt-03/pip-freeze.txt', folder / 'requirements-lock.txt')
    print(json.dumps(protocol, indent=2), flush=True)


def request_id(segment):
    for p in Path('.compute/requests').glob('*.json'):
        obj = json.loads(p.read_text())
        argv = obj.get('argv', [])
        if '--segment' in argv and argv[argv.index('--segment') + 1] == segment:
            return obj['request_id']
    return segment


def initialize(root, seed):
    np, torch = s.np, s.torch
    folder = root / 'inputs' / ('seed-' + str(seed))
    if not folder.exists():
        folder.mkdir(parents=True)
        pairs, labels, tr, te = s.dataset(seed)
        np.savez(folder / 'partition.npz', pairs=pairs, labels=labels, train_indices=tr, test_indices=te)
        net = s.model(seed, 'cpu')
        torch.save(net.state_dict(), folder / 'initial.pt')
        np.savez(folder / 'initial.npz', input_weight=net[0].weight.detach().numpy(),
                 output_weight=net[2].weight.detach().numpy())
        s.write_json(folder / 'provenance.json', {
            'seed': seed, 'partition_sha256': s.sha(folder / 'partition.npz'),
            'initial_weights_sha256': s.sha(folder / 'initial.npz'),
            'torch_initial_sha256': s.sha(folder / 'initial.pt')})
    return folder


def checkpoint(folder, segment, net, opt, curve, update, history):
    torch = s.torch
    target = folder / 'checkpoints' / ('step-%06d-%s.pt' % (update, segment))
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix('.tmp')
    torch.save({'model': net.state_dict(), 'optimizer': opt.state_dict(), 'step': update,
                'curve': curve, 'attempt_ids': history}, tmp)
    tmp.replace(target)
    s.write_json(folder / 'curve.json', curve)
    s.write_json(folder / 'state.json', {'step': update, 'checkpoint': rel(target),
                                        'attempt_ids': history, 'complete': False})
    return target


def endpoint(folder, seed, wd, net, x, inputs, config, update, checkpoint_path, history):
    np, torch = s.np, s.torch
    with torch.no_grad():
        logits = net(x).numpy()
    predictions = logits.argmax(1)
    with np.load(inputs / 'partition.npz', allow_pickle=False) as data:
        retained = {k: data[k] for k in data.files}
    np.savez(folder / 'arrays.npz', **retained, logits=logits, predictions=predictions)
    np.savez(folder / 'weights.npz', input_weight=net[0].weight.detach().numpy(),
             output_weight=net[2].weight.detach().numpy())
    metrics = {}
    for prefix, key in [('train', 'train_indices'), ('test', 'test_indices')]:
        idx = retained[key]
        z = logits[idx].astype(np.float64)
        target = retained['labels'][idx]
        m = z.max(1)
        metrics[prefix + '_loss'] = float(np.mean(m + np.log(np.exp(z - m[:, None]).sum(1)) - z[np.arange(len(idx)), target]))
        metrics[prefix + '_accuracy'] = float(np.mean(predictions[idx] == target))
    summary = {'seed': seed, 'weight_decay': wd, 'updates': update, 'phase': 'confirmation',
               'device': 'cpu', 'arrays': rel(folder / 'arrays.npz'), 'weights': rel(folder / 'weights.npz'),
               'curve': rel(folder / 'curve.json'), 'checkpoint': rel(checkpoint_path), 'metrics': metrics,
               'initial_weights_sha256': config['initial_weights_sha256'],
               'initial_weights': rel(inputs / 'initial.npz'), 'partition': rel(inputs / 'partition.npz'),
               'source_revision': config['source_revision'], 'attempt_id': history[-1],
               'attempt_ids': history, 'config': rel(folder / 'config.json'), 'complete': update == 100000}
    s.write_json(folder / 'summary.json', summary)
    s.write_json(folder / 'state.json', {'step': update, 'checkpoint': rel(checkpoint_path),
                                        'attempt_ids': history, 'complete': update == 100000})
    print(json.dumps({'seed': seed, 'weight_decay': wd, 'updates': update, 'metrics': metrics}), flush=True)


def train(args):
    root = Path(args.root)
    protocol = json.loads((root / 'frozen/protocol.json').read_text())
    for name, expected in protocol['source_hashes'].items():
        assert s.sha(name) == expected, 'Frozen source changed: ' + name
    attempt = root / 'attempts' / args.segment
    attempt.mkdir(parents=True, exist_ok=False)
    aid = request_id(args.segment)
    s.write_json(attempt / 'started.json', {'attempt_id': aid, 'segment': args.segment,
                                          'started_at_utc': datetime.now(timezone.utc).isoformat(),
                                          'source_revision': protocol['source_revision'], 'argv': sys.argv})
    s.imports()
    torch = s.torch
    start = time.perf_counter()
    work = []
    for seed in protocol['seeds']:
        for wd in protocol['weight_decays']:
            folder = root / 'runs' / ('seed-%d-wd-%d' % (seed, wd))
            state = json.loads((folder / 'state.json').read_text()) if (folder / 'state.json').exists() else None
            if state and state['complete']:
                continue
            if time.perf_counter() - start > args.seconds - 5:
                break
            inputs = initialize(root, seed)
            folder.mkdir(parents=True, exist_ok=True)
            config = dict(protocol)
            config.update({'seed': seed, 'weight_decay': wd, 'phase': 'confirmation',
                           'initial_weights_sha256': s.sha(inputs / 'initial.npz'),
                           'partition_sha256': s.sha(inputs / 'partition.npz')})
            if not (folder / 'config.json').exists():
                s.write_json(folder / 'config.json', config)
            net = s.model(seed, 'cpu')
            net.load_state_dict(torch.load(inputs / 'initial.pt', weights_only=True))
            opt = torch.optim.AdamW(net.parameters(), lr=.001, betas=(.9, .98), eps=1e-8,
                                    weight_decay=wd, fused=False, foreach=False)
            x, y, tr, te = s.tensors(seed, 'cpu')
            tx, ty = x[tr], y[tr]
            if state:
                saved = torch.load(state['checkpoint'], weights_only=True)
                net.load_state_dict(saved['model'])
                opt.load_state_dict(saved['optimizer'])
                update, curve, history = saved['step'], saved['curve'], saved['attempt_ids']
            else:
                update, curve, history = 0, [s.evaluate(net, x, y, tr, te, 0)], []
            history = history + [aid]
            first = update
            checkpoint_path = checkpoint(folder, args.segment, net, opt, curve, update, history)
            trace = attempt / ('seed-%d-wd-%d.jsonl' % (seed, wd))
            with trace.open('w') as log:
                log.write(json.dumps(curve[-1]) + '\n')
                log.flush()
                while update < protocol['horizon']:
                    s.step(net, opt, tx, ty)
                    update += 1
                    if update % 100 == 0:
                        point = s.evaluate(net, x, y, tr, te, update)
                        curve.append(point)
                        log.write(json.dumps(point) + '\n')
                        log.flush()
                        if update % 5000 == 0:
                            checkpoint_path = checkpoint(folder, args.segment, net, opt, curve, update, history)
                            print(json.dumps({'seed': seed, 'wd': wd, 'step': update,
                                              'segment_elapsed': time.perf_counter() - start}), flush=True)
                        if time.perf_counter() - start >= args.seconds - 3:
                            break
            if update % 5000 != 0:
                checkpoint_path = checkpoint(folder, args.segment, net, opt, curve, update, history)
            endpoint(folder, seed, wd, net, x, inputs, config, update, checkpoint_path, history)
            work.append({'seed': seed, 'weight_decay': wd, 'from_update': first, 'to_update': update,
                         'trace': rel(trace), 'checkpoint': rel(checkpoint_path)})
    s.write_json(attempt / 'completed.json', {'attempt_id': aid, 'work': work,
                                             'seconds': time.perf_counter() - start})
    print(json.dumps({'segment': args.segment, 'work': work}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('freeze')
    p.add_argument('--root', default='artifacts')
    p = sub.add_parser('train')
    p.add_argument('--root', default='artifacts')
    p.add_argument('--segment', required=True)
    p.add_argument('--seconds', type=float, default=155)
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze(Path(args.root))
    else:
        train(args)


if __name__ == '__main__':
    main()
