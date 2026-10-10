# Improved Denoising Diffusion Probabilistic Models

Explains the fixed cosine diffusion-noise schedule, which must not be confused with the optimizer schedule under study.

Verified metadata: 2021; Nichol, Alex, Dhariwal, Prafulla. [Primary source](https://arxiv.org/abs/2102.09672v1). Checked 9 October 2026.

Section 3.2, Equation 17 and Figure 5; Appendix A, architecture and training details.

A cosine schedule is defined for cumulative signal retention in the forward diffusion process. The experimental details also report parameter EMA at decay 0.9999.

Assessment: supports. Cosine diffusion noise and cosine optimizer learning rate are distinct design choices.

Scope: The noise schedule changes corruption over diffusion time. The retained factorial study varies optimizer learning rate over training time, so this paper is not evidence for its schedule contrast.

Study consequence: Define both schedules explicitly and cite this source only for the diffusion-noise choice.

The source asset ID and SHA-256 are recorded in map.json and retrieval.json. Read the retained source on demand; this note is a critical paraphrase, not a substitute for the paper.
