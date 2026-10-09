# Averaging Weights Leads to Wider Optima and Better Generalization

Provides a competing averaging baseline and shows why the averaging rule and learning-rate path need separate names.

Verified metadata: 2018; Izmailov, Pavel, Podoprikhin, Dmitrii, Garipov, Timur, Vetrov, Dmitry, Wilson, Andrew Gordon. [Primary source](https://arxiv.org/abs/1803.05407v3). Checked 9 October 2026.

Sections 2 and 3.1-3.2; Algorithm 1.

The method uses averaging of weights sampled along SGD trajectories with nonvanishing or cyclical learning rates. The paper analyzes the resulting geometry and classification generalization.

Assessment: supports. Weight averaging results depend on the averaging rule and the trajectory that supplied the weights.

Scope: SWA averages selected SGD iterates under constant/cyclical schedules. It is not the same estimator or optimizer as fixed-decay EMA over AdamW steps in the retained study.

Study consequence: Describe SWA as related work and state its different averaging rule and optimization setting.

The source asset ID and SHA-256 are recorded in map.json and retrieval.json. Read the retained source on demand; this note is a critical paraphrase, not a substitute for the paper.
