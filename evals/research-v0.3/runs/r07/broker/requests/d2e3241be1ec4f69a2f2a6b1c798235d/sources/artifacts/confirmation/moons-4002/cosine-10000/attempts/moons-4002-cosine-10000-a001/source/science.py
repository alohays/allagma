"""Study-owned DDPM and metrics; adapted from the pinned AI-Scientist reference.

The residual denoiser and DDPM equations follow reference/experiment.py.
See reference/LICENSE and REFERENCE.md for attribution and modifications.
"""
from __future__ import annotations

import math
import numpy as np
import torch
from torch import nn


def dataset(name, n, seed):
    """Independent draws, with no train/evaluation data reuse."""
    rng = np.random.default_rng(seed)
    if name == "moons":
        theta = rng.uniform(0, np.pi, n)
        side = rng.integers(0, 2, n)
        x = np.column_stack((np.where(side == 0, np.cos(theta), 1-np.cos(theta)),
                             np.where(side == 0, np.sin(theta), .5-np.sin(theta))))
        x += rng.normal(0, .03, x.shape)
        x[:, 0] = (x[:, 0]+.3)*2-1
        x[:, 1] = (x[:, 1]+.3)*3-1
    elif name == "gmm8":
        centers = mixture_centers()
        x = centers[rng.integers(0, 8, n)] + rng.normal(0, .15, (n, 2))
    else:
        raise ValueError(name)
    return x.astype(np.float32)


def mixture_centers():
    theta = np.arange(8)*2*np.pi/8
    return 2*np.column_stack((np.cos(theta), np.sin(theta)))


def projections(n=128):
    theta = np.random.default_rng(7321).uniform(0, 2*np.pi, n)
    return np.column_stack((np.cos(theta), np.sin(theta)))


def sliced_wasserstein(x, y, directions=None):
    """Mean projected empirical W1; equal sample size, float64 arithmetic."""
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != 2:
        raise ValueError("Equal (n,2) samples required")
    directions = projections() if directions is None else directions
    # Small chunks avoid BLAS thread launch overhead and large scratch arrays.
    values = []
    for direction in directions:
        values.append(np.abs(np.sort(x @ direction)-np.sort(y @ direction)).mean())
    return float(np.mean(values))


def mode_coverage(x):
    """Modes with >=1% of ALL draws within 3 sigma of their nearest center."""
    x = np.asarray(x, dtype=np.float64)
    distances = np.linalg.norm(x[:, None, :]-mixture_centers()[None, :, :], axis=2)
    nearest = distances.argmin(axis=1)
    valid = distances[np.arange(len(x)), nearest] <= .45
    counts = np.bincount(nearest[valid], minlength=8)
    return {"covered": int((counts >= math.ceil(.01*len(x))).sum()),
            "counts": counts.tolist(), "inlier_fraction": float(valid.mean()),
            "total_variation": float(.5*np.abs(counts/len(x)-1/8).sum())}


class Embedding(nn.Module):
    def __init__(self, dim=128, scale=1.):
        super().__init__()
        self.scale = scale
        self.register_buffer("frequencies", torch.exp(-math.log(10000)*torch.arange(dim//2)/(dim//2-1)))

    def forward(self, x):
        v = (x*self.scale).unsqueeze(-1)*self.frequencies
        return torch.cat((v.sin(), v.cos()), dim=-1)


class Residual(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.ff = nn.Linear(width, width)

    def forward(self, x):
        return x+self.ff(torch.relu(x))


class Denoiser(nn.Module):
    def __init__(self):
        super().__init__()
        self.time = Embedding()
        self.coord = Embedding(scale=25.)
        self.network = nn.Sequential(nn.Linear(384, 256), *[Residual(256) for _ in range(3)],
                                     nn.ReLU(), nn.Linear(256, 2))

    def forward(self, x, t):
        return self.network(torch.cat((self.coord(x[:, 0]), self.coord(x[:, 1]), self.time(t)), dim=-1))


def schedule(steps=100):
    # The upstream linear schedule leaves alpha_bar_T ~0.36 at T=100.
    # Use the standard cosine DDPM schedule so N(0,I) is a suitable endpoint.
    grid = np.arange(steps+1, dtype=np.float64)/steps
    abar = np.cos((grid+.008)/1.008*np.pi/2)**2
    abar /= abar[0]
    beta = np.minimum(1-abar[1:]/abar[:-1], .999)
    alpha = 1-beta
    abar = np.cumprod(alpha)
    previous = np.r_[1., abar[:-1]]
    return {"beta": beta, "abar": abar,
            "sqrt_abar": np.sqrt(abar), "sqrt_one_minus": np.sqrt(1-abar),
            "inverse": 1/np.sqrt(abar), "inverse_noise": np.sqrt(1/abar-1),
            "posterior_x0": beta*np.sqrt(previous)/(1-abar),
            "posterior_xt": (1-previous)*np.sqrt(alpha)/(1-abar),
            "posterior_std": np.sqrt(beta*(1-previous)/(1-abar))}


@torch.no_grad()
def draw(model, noises, coefficients):
    x = noises[0].clone()
    n = x.shape[0]
    for t in range(99, -1, -1):
        prediction = model(x, torch.full((n,), t, device=x.device, dtype=torch.float32))
        x0 = (coefficients["inverse"][t]*x-coefficients["inverse_noise"][t]*prediction).clamp(-6, 6)
        x = coefficients["posterior_x0"][t]*x0+coefficients["posterior_xt"][t]*x
        if t:
            x = x+coefficients["posterior_std"][t]*noises[100-t]
    return x.cpu().numpy()
