---
name: allagma-analysis
description: Recompute study results from raw artifacts with uncertainty.
---

Read relevant reference notes before comparing the study with prior findings.
Record analysis consequences and competing evidence in the literature map.
Distinguish differences in metrics, datasets and budgets from contradictions.

Build an immutable raw manifest from eligible successful attempts. Identify failed attempts, pilot data and other exclusions with reasons. Execute the study-owned analysis using recorded code and configuration. Link every output and uncertainty estimate in AnalysisRecord.

Declare the independent unit and justify the uncertainty method in the study protocol. An execution record is not automatically an independent replicate. A single fixed computational reproduction can support deterministic agreement without supporting population uncertainty; do not invent extra observations to satisfy a helper. The local helper accepts a study-owned `minimum_confirmation_runs` threshold (default one). Paired conditions may explicitly declare `paired_seeds` with distinct `condition_id` values; their shared seeds do not create independent observations. Pilot and confirmation seed boundaries still apply.

Recompute from the same raw inputs in a separate output directory and compare the numerical results. Investigate disagreements before reporting. Report negative and inconclusive findings. Distinguish deterministic verification from statistical uncertainty and do not promote unverified prose numbers to results.
