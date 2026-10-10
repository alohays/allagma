# Manuscript revision outline

This revision uses the completed r07 experiment. The literature search and paper
were added after that experiment. No historical results or protocols are changed.

- Abstract: report the factorial design, paired seed count, directional estimates
  and wide uncertainty. State that this is a revision of retained results.
- Introduction: separate relative EMA benefit, absolute sample quality and the
  complete learning-rate path. Describe the narrow question without novelty claims.
- Related work: DDPM and cosine diffusion noise; SWA versus EMA; Morales-Brotons
  on schedule dependence; Karras on averaging profiles; Ajroldi's directly related
  newer benchmark; Switch EMA counterexamples and intervention differences.
- Methods: fixed protocol, paired streams, separate cosine trajectories, constant
  trajectory reuse, SW1 and coverage, seed-level intervals and multiplicity.
- Results: exact retained figure and generated tables; all paired estimates,
  schedule contrasts, duration and interaction uncertainty; absolute raw quality
  and the mode-coverage ceiling.
- Discussion: qualitative agreement with prior schedule findings, no endpoint-only
  mechanism, no conclusion that ordinary EMA always helps or that one decay wins.
- Limitations: small n, two synthetic datasets, few decays, no SWA/switching/profile
  comparisons, retrospective literature search, provisional agent-assisted review.
- Appendices: remaining contrasts, source lineage, literature coverage, selected
  reference assets, author configuration, reproducible paper build and study links.

The critical readings and consequences are in [references/INDEX.md](references/INDEX.md).
The script `derive.py` verifies every selected scientific input against the frozen
package index and recomputes the 114 retained statistical summaries from the
retained seed-level measurements.
