"""Condense verified numerical evidence for the manuscript, through the broker."""
import json
from pathlib import Path
import study as s


def main():
    result = json.loads(Path('analysis/results.json').read_text())
    verification = json.loads(Path('analysis/verification.json').read_text())
    sensitivity = json.loads(Path('analysis/sensitivity.json').read_text())
    charges = {'setup': 0., 'compute': 0.}
    counts = {'setup': 0, 'compute': 0}
    statuses = {}
    for path in Path('.compute/requests').glob('*.json'):
        request = json.loads(path.read_text())
        response = Path('.compute/responses') / (request['request_id'] + '.json')
        if not response.exists():
            continue
        response = json.loads(response.read_text())
        category = request['category']
        charges[category] += response['result'].get('charged_seconds', 0.)
        counts[category] += 1
        status = response['result']['status']
        statuses[status] = statuses.get(status, 0) + 1
    checks = verification['checks']
    obj = {
        'source_results': 'analysis/results.json', 'source_verification': 'analysis/verification.json',
        'source_sensitivity': 'analysis/sensitivity.json',
        'mean_endpoint_accuracy_by_decay': {str(w): sum(r['test_accuracy'] for r in result['per_seed'] if r['weight_decay'] == w) / 4 for w in [0, 1]},
        'mean_endpoint_loss_by_decay': {str(w): sum(r['test_loss'] for r in result['per_seed'] if r['weight_decay'] == w) / 4 for w in [0, 1]},
        'maximum_sensitivity_generalization_event_count': max(r['generalization_events'] for r in sensitivity),
        'maximum_sensitivity_grokking_event_count': max(r['delayed_grokking_events'] for r in sensitivity),
        'sensitivity_rows': len(sensitivity),
        'max_endpoint_recomputation_error': max(max(c['summary_metric_absolute_errors'].values()) for c in checks),
        'max_torch_reload_logit_error': max(c['torch_reload_max_logit_error'] for c in checks),
        'max_numpy_forward_logit_error': max(c['numpy_float64_max_logit_error'] for c in checks),
        'max_numpy_forward_test_loss_difference_absolute': max(abs(c['numpy_float64_forward_metric_differences']['test_loss']) for c in checks),
        'max_numpy_error_to_roundoff_bound_ratio': max(c['numpy_max_error_to_roundoff_bound_ratio'] for c in checks),
        'numpy_prediction_disagreements_total': sum(c['numpy_prediction_disagreements'] for c in checks),
        'numpy_correctness_disagreements_total': sum(c['numpy_correctness_disagreements'] for c in checks),
        'reverse_pair_overlap_by_seed': {str(c['seed']): c['heldout_reverse_pair_in_training_count'] for c in checks},
        'diagnostics': [{'seed': c['seed'], 'weight_decay': c['weight_decay'], **c['diagnostics_posthoc']} for c in checks],
        'resource_snapshot_before_this_reporting_request': {'charged_seconds': charges, 'request_counts': counts, 'statuses': statuses}}
    s.write_json('analysis/report-numbers.json', obj)
    print(json.dumps(obj, indent=2))


if __name__ == '__main__':
    main()
