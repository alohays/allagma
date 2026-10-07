# Reference, modifications and license

The reference is [SakanaAI/AI-Scientist, templates/2d_diffusion](https://github.com/SakanaAI/AI-Scientist/tree/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/templates/2d_diffusion)
at exactly commit `1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb`.
[provenance.json](reference/provenance.json) records the retrieved file bytes,
URLs and SHA-256 hashes. The study retains the original files for inspection;
they are not executed as the study runner.

`domain/science.py` adapts the sinusoidal residual denoiser and DDPM equations
from `experiment.py`. `domain/runner.py` adapts its noise-prediction training
workflow. The reference files and these adaptations are subject to the included
[AI Scientist Source Code License](reference/LICENSE), rather than the parent
repository's blanket MIT license. Other study orchestration, metrics, tests and
documentation are original Allagma work. The upstream license is retained with
every frozen campaign's scientific materials.

The study retains the 128-dimensional embeddings, width 256, three residual
blocks, AdamW settings, clipping, batch256 and 10,000-update cosine learning-rate
schedule. It changes device selection to required MPS, uses seeded independent
training/held-out data, samples minibatches with replacement, precomputes
training noise and noisy inputs for efficiency, and evaluates paired raw and
constant EMA0.99/EMA0.999 weights at 5k and10k. EMA updates every optimizer step
without the upstream wrapper's warmup or sparse updates. It replaces the
reference's estimated KL metric with prespecified held-out Sliced W1 and mode
coverage, and adds the eight-Gaussian dataset. It retains model checkpoints and
samples in non-pickle NPZ/JSON artifacts.

The diffusion schedule is the cosine schedule (offset0.008, beta cap0.999)
from [Nichol and Dhariwal (2021)](https://arxiv.org/abs/2102.09672), with 100
steps and predicted-clean-sample clipping to [-6,6]. This is a declared choice
before pilots: the upstream unscaled linear beta range 0.0001–0.02 at100steps
has cumulative alpha around0.36, so its terminal state is not close to the
standard Gaussian sampling prior. This study is not a reproduction of the
upstream reported results.

[Ho, Jain and Abbeel (2020)](https://arxiv.org/abs/2006.11239) supply the DDPM
context. [PyTorch's MPS documentation](https://docs.pytorch.org/docs/2.14/notes/mps.html)
describes the device backend; [its reproducibility guidance](https://docs.pytorch.org/docs/2.14/notes/randomness.html)
limits promises about identical training across releases and platforms.
