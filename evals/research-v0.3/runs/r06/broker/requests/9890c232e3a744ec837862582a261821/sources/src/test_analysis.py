"""Known-answer tests for the scientific transition and uncertainty analysis."""
import json
from pathlib import Path
import analyze as a
import study as s


def main():
    s.imports()
    def curve(train, test):
        return [{'step': i * 100, 'train_accuracy': t, 'test_accuracy': v,
                 'train_loss': 0., 'test_loss': 0.} for i, (t, v) in enumerate(zip(train, test))]
    # Two crossings at the edge of the horizon do not satisfy three-evaluation persistence.
    c = curve([0., .99, 1., 1., 1.], [0., 0., 0., .95, .96])
    out = a.outcomes(c)
    assert out['memorization']['event_step'] == 100
    assert out['memorization']['confirmation_step'] == 300
    assert out['generalization']['event_step'] is None and out['generalization']['censor_step'] == 400
    assert out['lag_updates'] is None and not out['delayed_grokking']
    # Earliest qualifying run wins; isolated crossings are rejected.
    c = curve([1.] * 8, [.95, .1, .95, .96, .97, .2, .99, .99])
    event = a.transition(c, 'test_accuracy', .95, 3)
    assert event['event_step'] == 200 and event['confirmation_step'] == 400
    # Exactly the preregistered delay passes; 900 updates fails.
    c = curve([.99] * 15, [.2] * 10 + [.95] * 5)
    assert a.outcomes(c)['delayed_grokking']
    assert not a.outcomes(curve([.99] * 15, [.2] * 9 + [.95] * 6))['delayed_grokking']
    # Adequate lag alone is insufficient: low initial held-out score and persistent training matter.
    assert not a.outcomes(curve([.99] * 15, [.51] * 10 + [.95] * 5))['delayed_grokking']
    assert a.outcomes(curve([.99] * 15, [.51] * 10 + [.95] * 5), gate=None)['delayed_grokking']
    assert not a.outcomes(curve([.99] * 10 + [.8] * 5, [.2] * 10 + [.95] * 5))['delayed_grokking']
    # No event returns null, never an invented event at the horizon.
    out = a.outcomes(curve([.1] * 5, [.1] * 5))
    assert out['memorization']['event_step'] is None and out['generalization']['event_step'] is None
    summary = a.paired_summary([1., 1., 1., 1.])
    assert summary['mean'] == 1 and summary['ci95'] == [1., 1.]
    assert summary['sign_flip_p_two_sided'] == .125
    assert a.paired_summary([1., -1., 1., -1.])['sign_flip_p_two_sided'] == 1
    assert a.paired_summary([])['mean'] is None
    s.write_json('analysis/analysis-tests.json', {'passed': True,
        'coverage': ['sustain_count', 'edge_of_horizon_censoring', 'first_run_onset', 'confirmation_time',
                     'exact_lag_boundary', 'early_test_gate', 'training_persistence', 'null_events',
                     'four_seed_sign_flip_floor', 'zero_variance_t_interval', 'empty_pairs']})
    print('All scientific analysis known-answer checks passed.')


if __name__ == '__main__':
    main()
