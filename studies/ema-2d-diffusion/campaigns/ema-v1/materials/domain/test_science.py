"""Known-answer checks before pilot data can qualify the implementation."""
import copy
import unittest

import numpy as np
import torch
from scipy.stats import wasserstein_distance
from science import Denoiser, dataset, mode_coverage, mixture_centers, schedule, sliced_wasserstein


class ScienceTests(unittest.TestCase):
    def test_projected_w1_known_translation(self):
        x = np.array([[0.,0.],[1.,0.],[2.,0.]])
        dirs = np.array([[1.,0.],[0.,1.]])
        self.assertEqual(sliced_wasserstein(x, x, dirs), 0.)
        self.assertEqual(sliced_wasserstein(x, x+[2.,0.], dirs), 1.)
        self.assertAlmostEqual(wasserstein_distance(x[:,0], x[:,0]+2), 2.)

    def test_mode_coverage_controls(self):
        self.assertEqual(mode_coverage(np.repeat(mixture_centers(), 100, axis=0))["covered"], 8)
        self.assertEqual(mode_coverage(np.repeat(mixture_centers()[:1], 100, axis=0))["covered"], 1)
        self.assertEqual(mode_coverage(np.full((100,2), 100.))["covered"], 0)

    def test_data_partitions(self):
        for name in ("moons", "gmm8"):
            a = dataset(name, 200, 1)
            self.assertTrue(np.array_equal(a, dataset(name, 200, 1)))
            self.assertFalse(np.array_equal(a, dataset(name, 200, 2)))

    def test_schedule_known_inversion(self):
        s = schedule()
        self.assertLess(s["abar"][-1], 1e-6)
        self.assertEqual(s["posterior_std"][0], 0.)
        for t in (0,50,99):
            x0, noise = np.array([1.,-2.]), np.array([.5,-.7])
            xt = s["sqrt_abar"][t]*x0+s["sqrt_one_minus"][t]*noise
            np.testing.assert_allclose(s["inverse"][t]*xt-s["inverse_noise"][t]*noise, x0, atol=1e-10)

    def test_ema_exact_constant_decay(self):
        for decay in (.99, .999):
            ema = [torch.tensor([0.,2.])]
            expected = np.array([0.,2.])
            for update in ([1.,4.], [5.,-1.], [3.,3.]):
                torch._foreach_lerp_(ema, [torch.tensor(update)], 1-decay)
                expected = decay*expected+(1-decay)*np.array(update)
                np.testing.assert_allclose(ema[0].numpy(), expected, atol=1e-6)

    def test_mps_model_and_ema(self):
        self.assertTrue(torch.backends.mps.is_available())
        torch.set_num_threads(1)
        torch.manual_seed(51)
        cpu = Denoiser()
        self.assertEqual(sum(p.numel() for p in cpu.parameters()), 296450)
        gpu = copy.deepcopy(cpu).to("mps")
        x, t = torch.randn(16,2), torch.arange(16).float()
        np.testing.assert_allclose(cpu(x,t).detach().numpy(), gpu(x.to("mps"),t.to("mps")).detach().cpu().numpy(), atol=2e-4, rtol=2e-4)
        ema = copy.deepcopy(gpu).requires_grad_(False)
        before = [p.detach().cpu().numpy().copy() for p in gpu.parameters()]
        optimizer = torch.optim.AdamW(gpu.parameters(), lr=3e-4, foreach=True)
        gpu(x.to("mps"),t.to("mps")).square().mean().backward()
        torch.nn.utils.clip_grad_norm_(gpu.parameters(), .5, foreach=False)
        optimizer.step()
        with torch.no_grad():
            torch._foreach_lerp_(list(ema.parameters()), list(gpu.parameters()), .01)
        for initial, p, averaged in zip(before, gpu.parameters(), ema.parameters()):
            np.testing.assert_allclose(averaged.cpu().numpy(), .99*initial+.01*p.detach().cpu().numpy(), atol=2e-7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
