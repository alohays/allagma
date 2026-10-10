# AI-Scientist 2D diffusion template: selected source snapshot

Exact upstream code lineage of the retained denoiser and diffusion equations.

Verified metadata: 2025; SakanaAI. [Primary source](https://github.com/SakanaAI/AI-Scientist/tree/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/templates/2d_diffusion). Checked 9 October 2026.

experiment.py: MLPDenoiser at line 51 and NoiseScheduler at line 79; see separately retained datasets.py and ema_pytorch.py.

The template supplies a residual denoiser and diffusion equations. The separately retained EMA wrapper uses a time-dependent decay and configurable update interval.

Assessment: supports. The retained experiment is an adaptation with declared differences, not a byte-identical upstream reproduction.

Scope: The completed study changes dataset generation, metrics, diffusion-noise schedule and EMA update details; this is not an upstream result replication.

Study consequence: Retain the AI Scientist license and AI-use disclosure while describing the actual adaptations.

The source asset ID and SHA-256 are recorded in map.json and retrieval.json. Read the retained source on demand; this note is a critical paraphrase, not a substitute for the paper.
