"""Investigate float64/float32 argmax differences without changing the experiment."""
import json
import shutil
from pathlib import Path
import study as s


def main():
    folder = Path('provenance/sources')
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / 'analyze-failed-float64-argmax.py'
    assert not target.exists()
    shutil.copyfile('src/analyze.py', target)
    s.imports()
    np = s.np
    output = []
    for summary in sorted(Path('artifacts/runs').glob('*/summary.json')):
        run = json.loads(summary.read_text())
        with np.load(run['arrays'], allow_pickle=False) as f:
            a = {k: f[k] for k in f.files}
        with np.load(run['weights'], allow_pickle=False) as f:
            wi, wo = f['input_weight'].astype(np.float64), f['output_weight'].astype(np.float64)
        p = a['pairs']
        hidden = np.maximum(wi[:, p[:, 0]].T + wi[:, 97 + p[:, 1]].T, 0)
        independent = hidden @ wo.T
        difference = independent - a['logits'].astype(np.float64)
        predicted = independent.argmax(1)
        mismatch = np.flatnonzero(predicted != a['predictions'])
        details = []
        for i in mismatch:
            fp32, fp64 = int(a['predictions'][i]), int(predicted[i])
            details.append({'index': int(i), 'pair': p[i].tolist(), 'label': int(a['labels'][i]),
                            'split': 'train' if i in a['train_indices'] else 'test',
                            'fp32_prediction': fp32, 'fp64_prediction': fp64,
                            'fp32_winner_logit': float(a['logits'][i, fp32]),
                            'fp32_alternative_logit': float(a['logits'][i, fp64]),
                            'fp32_margin': float(a['logits'][i, fp32] - a['logits'][i, fp64]),
                            'fp64_margin_for_fp64_winner': float(independent[i, fp64] - independent[i, fp32]),
                            'row_max_absolute_logit_error': float(np.abs(difference[i]).max())})
        result = {'seed': run['seed'], 'weight_decay': run['weight_decay'],
                  'max_absolute_logit_error': float(np.abs(difference).max()),
                  'number_prediction_disagreements': len(mismatch),
                  'number_correctness_disagreements': int(np.count_nonzero((predicted == a['labels']) != (a['predictions'] == a['labels']))),
                  'details': details}
        output.append(result)
    s.write_json('analysis/precision-diagnostic.json', {'analysis_source_sha256': s.sha(target), 'runs': output})
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
