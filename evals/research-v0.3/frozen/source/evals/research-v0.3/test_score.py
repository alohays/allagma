"""Optional scientific scorer qualification; outside the stdlib conformance kit."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import score


class ScorerQualification(unittest.TestCase):
    def test_original_core_rule_accepts_exact_answers_and_rejects_wrong_value(self):
        reference=score.read(score.ROOT/'studies/core-culp/reference/controller-task.json')
        answers=dict(reference['results'][0])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/'report.json';path.write_text(json.dumps(answers))
            self.assertEqual(score.original_core_score(root,{'report':'report.json'})['correct'],6)
            answers[next(iter(answers))]=-10000;path.write_text(json.dumps(answers))
            self.assertEqual(score.original_core_score(root,{'report':'report.json'})['correct'],5)

    def test_projected_wasserstein_matches_analytic_translation(self):
        x=np.zeros((8,2));y=np.tile([2.,0.],(8,1))
        angles=np.random.default_rng(7321).uniform(0,2*np.pi,128)
        self.assertAlmostEqual(score.sw1(x,y),float(2*np.abs(np.cos(angles)).mean()),places=13)
        self.assertEqual(score.sw1(x,x),0)

    def test_logit_loss_uses_stable_logsumexp(self):
        logits=np.array([[1000.,1000.],[-1000.,-1000.]])
        accuracy,loss=score.accuracy_and_loss(logits,np.array([0,1]),np.array([0,1]))
        self.assertEqual(accuracy,.5);self.assertAlmostEqual(loss,np.log(2),places=14)

    def test_object_arrays_and_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);np.savez(root/'bad.npz',bad=np.array([{}],dtype=object))
            with self.assertRaises(ValueError):score.npz(root,'bad.npz')
            with self.assertRaises(ValueError):score.confined(root,'../outside.json')

    def test_actual_development_checkpoint_replays_without_candidate_code(self):
        base=score.ROOT/'studies/ema-schedule/development/evidence'
        raw=score.read(base/'ema-gmm8-constant-5000-seed31.json')
        with np.load(base/'ema-gmm8-constant-5000-seed31.npz',allow_pickle=False) as archive:
            weights={k:archive[k] for k in archive.files}
        noise=np.random.default_rng(31+3_000_000).normal(size=(100,2048,2)).astype(np.float32)
        actual=score.replay_checkpoint(weights,'raw',noise,'mps')
        np.testing.assert_allclose(actual,np.array(raw['variants']['raw']['samples']),rtol=1e-4,atol=1e-5)


if __name__=='__main__':unittest.main(verbosity=2)
