# Analyzing and Improving the Training Dynamics of Diffusion Models

Shows that averaging length interacts with architecture and training duration in diffusion models.

Verified metadata: 2024; Karras, Tero, Aittala, Miika, Lehtinen, Jaakko, Hellsten, Janne, Aila, Timo, Laine, Samuli. [Primary source](https://arxiv.org/abs/2312.02696v2). Checked 9 October 2026.

Sections 3.1-3.3, PDF pp. 5-7; Figure 5 and Appendix C.

Post-hoc reconstruction permits comparisons of averaging profiles. Figure 5 shows that the preferred profile varies with architecture and shifts as training progresses.

Assessment: supports. A single decay should not be treated as universally optimal across training durations and architectures.

Scope: The paper uses image synthesis, FID, large architectures and power-function/post-hoc averaging. Its optimal averaging lengths cannot be transferred to two fixed EMA decays in a small 2D model.

Study consequence: Cite the profile dependence and distinguish post-hoc tuning from this study's prespecified comparisons.

The source asset ID and SHA-256 are recorded in map.json and retrieval.json. Read the retained source on demand; this note is a critical paraphrase, not a substitute for the paper.
