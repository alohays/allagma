"""Check assignment integrity, paired direction, and honest missing-value handling."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('comparison', Path(__file__).with_name('comparison.py'))
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def fixture():
    rows = []
    for task in comparison.TASKS:
        for replicate in (1, 2):
            for condition in comparison.CONDITIONS:
                treatment = condition == 'allagma'
                rows.append({'run_id': f'r{len(rows) + 1:02d}', 'task': task,
                             'replicate': replicate, 'condition': condition,
                             'native_status': 'completed', 'verified_completion': treatment,
                             'scientific_execution_verified': True,
                             'numerical': {'correct': 4 if treatment else 3, 'total': 4},
                             'evidence_completeness': [{'score': 1, 'reason': 'fixture'}] * (8 if treatment else 7),
                             'compute_seconds': 12 if treatment else 10,
                             'native_usage_events': [{'input_tokens': 100, 'cached_input_tokens': 90,
                                                      'output_tokens': 20, 'reasoning_output_tokens': 10}]})
    return {'runs': rows}


class ComparisonTests(unittest.TestCase):
    def test_all_assignments_and_paired_direction(self):
        result = comparison.compare(fixture())
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(result['runs']), 12)
        self.assertEqual(len(result['paired_contrasts']), 6)
        for pair in result['paired_contrasts']:
            self.assertEqual(pair['differences']['numerical_fraction'], .25)
            self.assertEqual(pair['differences']['evidence_score'], 1)
            self.assertEqual(pair['differences']['completed'], 1)
            self.assertEqual(pair['differences']['execution_verified'], 0)
            self.assertEqual(pair['differences']['compute_seconds'], 2)

    def test_missing_evidence_stays_missing_and_pending_is_not_final(self):
        data = fixture()
        data['runs'][0].update(native_status='running', verified_completion=None,
                               numerical=None, evidence_completeness=None, native_usage_events=[])
        with self.assertRaisesRegex(ValueError, 'Unfinished'):
            comparison.compare(data)
        result = comparison.compare(data, allow_partial=True)
        self.assertEqual(result['status'], 'partial')
        self.assertIsNone(result['runs'][0]['input_tokens'])
        self.assertIsNone(result['paired_contrasts'][0]['differences']['completed'])
        self.assertIsNone(result['paired_contrasts'][0]['differences']['numerical_fraction'])
        self.assertIsNone(result['paired_contrasts'][0]['differences']['compute_seconds'])
        self.assertEqual(result['within_task_variability'][0]['metrics']['compute_seconds']['observed'], 1)
        self.assertIn('not a completed evaluation', comparison.render(result))

    def test_duplicate_assignment_is_rejected(self):
        data = fixture()
        data['runs'][1] = copy.deepcopy(data['runs'][0])
        with self.assertRaisesRegex(ValueError, 'unique assigned'):
            comparison.compare(data)

    def test_usage_categories_are_not_double_counted(self):
        result = comparison.compare(fixture())
        self.assertEqual(result['runs'][0]['input_tokens'], 100)
        self.assertEqual(result['runs'][0]['output_tokens'], 20)
        self.assertEqual(result['runs'][0]['cached_input_tokens'], 90)
        self.assertEqual(result['runs'][0]['reasoning_output_tokens'], 10)


if __name__ == '__main__':
    unittest.main()
