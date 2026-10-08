# Weight EMA, training duration and learning-rate schedules

Status: the first fully verified Allagma package is r07; see
[results and reproduction](RESULTS.md). The [workflow comparison](../../docs/v0.3/COMPARISON.md)
and [release audit](../../docs/releases/0.3.0rc2.md) are complete. This follow-up addresses the duration/schedule
confounding documented in the [completed EMA study](../ema-2d-diffusion/publication/v2/manuscript.md).
It crosses terminal training duration (5,000 or 10,000 updates) with constant
learning rate or cosine decay over that duration. Paired raw/EMA effects at a
fixed duration compare schedule policies; duration contrasts under constant
learning rate avoid the earlier decay-position confound. Cosine runs compare
endpoints at the same normalized schedule position. The intervention is an
entire learning-rate policy, not just its terminal value.

The study reuses the prior study's denoiser, DDPM schedule, datasets,
sampling and metrics, with explicit provenance. All trajectories for one seed
use identical initialization, data and training-noise prefixes and matched
sampling noise. The completed package retains seed-level uncertainty and
duration-by-schedule interaction estimates. Pilot seeds are excluded from final
confirmation and from evaluated sessions' untouched scientific seeds.

See [reference and license](REFERENCE.md). Final scientific requirements, inputs,
workflow and finite resource ceilings were frozen before the comparison.
