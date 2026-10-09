# When, Where and Why to Average Weights?

A newer, closely related benchmark explicitly compares averaging with learning-rate annealing and limits the novelty of the retained study.

Verified metadata: 2025; Ajroldi, Niccolò, Orvieto, Antonio, Geiping, Jonas. [Primary source](https://arxiv.org/abs/2502.06761v3). Checked 9 October 2026.

Section 6, Figure 7 (PDF p. 7), and Section 8 (limitations).

The study compares no, partial and full annealing. It reports that averaging gains shrink when the baseline is fully annealed and that combining averaging with annealing gives the strongest final performance in its tests.

Assessment: supports. The qualitative interaction between averaging and annealing is prior work, not a new general finding established by the Allagma example.

Scope: AlgoPerf workloads and the language-model experiments use different tasks and tuning budgets. The main baseline optimizers are NadamW and AdamW; there is no matched tiny-diffusion replication of this study.

Study consequence: Cite this newer source prominently in related work and discussion, including differences in domain and protocol.

The source asset ID and SHA-256 are recorded in map.json and retrieval.json. Read the retained source on demand; this note is a critical paraphrase, not a substitute for the paper.
