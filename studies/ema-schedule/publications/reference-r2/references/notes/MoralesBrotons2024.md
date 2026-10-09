# Exponential Moving Average of Weights in Deep Learning: Dynamics and Benefits

Directly connects the benefit of EMA with the learning-rate schedule and offers a comparison to the retained endpoint findings.

Verified metadata: 2024; Morales-Brotons, Daniel, Vogels, Thijs, Hendrikx, Hadrien. [Primary source](https://arxiv.org/abs/2411.18704v1). Checked 9 October 2026.

Sections 3.1-3.3, PDF pp. 4-5, and Figure 1.

The experiments show strong EMA performance before the learning rate is fully reduced and convergence toward the current iterate as updates become small. Section 3.3 reports that their tested bootstrapping from EMA did not help.

Assessment: supports. Averaging and learning-rate reduction can interact; a strong intermediate EMA result does not imply a large advantage at a fully cooled endpoint.

Section 3.3, PDF p. 5, and Appendix C.

Replacing training weights with their average did not provide a benefit in the tested bootstrapping setting.

Assessment: context. Benefits from swapping training weights cannot be assumed across protocols.

Scope: Most evidence concerns classification with SGD, validation-based early stopping and batch-normalization choices. Those conditions differ from the fixed-endpoint AdamW diffusion experiment.

Study consequence: Describe agreement in qualitative pattern with explicit optimizer, data and selection differences.

The source asset ID and SHA-256 are recorded in map.json and retrieval.json. Read the retained source on demand; this note is a critical paraphrase, not a substitute for the paper.
