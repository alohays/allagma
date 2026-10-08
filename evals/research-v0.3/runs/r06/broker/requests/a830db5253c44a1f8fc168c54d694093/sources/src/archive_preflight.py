"""Resolve historical preflight paths to immutable checkpoint-derived snapshots."""
import copy
import json
from pathlib import Path
import analyze
import study as s


def main():
    s.imports()
    np, torch = s.np, s.torch
    original = Path('analysis/preflight/measurements.json')
    historical = json.loads(original.read_text())
    reconstructed = copy.deepcopy(historical)
    evidence = Path('analysis/preflight/checkpoint-derived-evidence')
    evidence.mkdir(parents=True, exist_ok=False)
    checks = []
    for section in ['runs', 'partial_runs']:
        for run in reconstructed[section]:
            folder = evidence / ('seed-%d-wd-%d-step-%d' % (run['seed'], run['weight_decay'], run['updates']))
            folder.mkdir()
            checkpoint = torch.load(run['checkpoint'], map_location='cpu', weights_only=True)
            assert checkpoint['step'] == run['updates']
            net = s.model(run['seed'], 'cpu')
            net.load_state_dict(checkpoint['model'])
            x, y, tr, te = s.tensors(run['seed'], 'cpu')
            with torch.no_grad():
                logits = net(x).numpy()
            with np.load(run['partition'], allow_pickle=False) as p:
                inputs = {key: p[key] for key in p.files}
            arrays = {**inputs, 'logits': logits, 'predictions': logits.argmax(1)}
            metrics = analyze.metrics_from_arrays(arrays)
            assert metrics == run['metrics']
            np.savez(folder / 'arrays.npz', **arrays)
            np.savez(folder / 'weights.npz', input_weight=net[0].weight.detach().numpy(),
                     output_weight=net[2].weight.detach().numpy())
            s.write_json(folder / 'curve.json', checkpoint['curve'])
            run['original_working_paths'] = {k: run[k] for k in ['arrays', 'weights', 'curve']}
            for key, name in [('arrays', 'arrays.npz'), ('weights', 'weights.npz'), ('curve', 'curve.json')]:
                run[key] = str(folder / name)
            checks.append({'seed': run['seed'], 'weight_decay': run['weight_decay'], 'updates': run['updates'],
                           'source_checkpoint': run['checkpoint'], 'endpoint_metrics_exactly_equal': True,
                           'curve_rows': len(checkpoint['curve'])})
    reconstructed['archival_note'] = 'Paths resolved after the preflight from retained exact-update checkpoints; original measurement JSON remains unchanged. This is reconstruction of historical evidence, not additional training or independent replication.'
    s.write_json('analysis/preflight/archival-measurements.json', reconstructed)
    s.write_json('analysis/preflight/archive-verification.json', {'passed': True, 'original_measurements_sha256': s.sha(original), 'checks': checks})
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
