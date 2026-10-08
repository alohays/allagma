# Defects found after the evaluation freeze

## Inline learning-curve parser — corrected in a separate evaluator

The frozen measurement document defines `curve` as a JSON list. Run r03 supplied
that list correctly, plus the same curve in a separate artifact. The frozen
scorer instead treated the field as a path and reported an unscorable result.
That original result remains at `runs/r03/score.json`; it is an evaluator defect,
not a missing candidate measurement.

`evals/research-v0.3/score_curve_compat.py` is a separate protected correction.
It changes only curve loading: accept the specified inline list, while retaining
the original relative-path branch. All formulas, tolerances, controls, totals,
task requirements and frozen source remain unchanged. The exact replacement and
both code hashes are retained in
`evals/research-v0.3/postprocess-checks/curve-parser-correction.json`.

The corrected scorer passes all 40 r03 numerical checks. A separate equivalence
check supplied the original frozen scorer with existing curve-file references
whose contents equal the inline lists; its complete result equals the corrected
scorer result. The compatibility correction applies uniformly to every applicable
run. Summaries retain the original scoring outcome and explicitly mark use of
the correction. No candidate artifact was modified.

The current release scorer is byte-identical to the qualified compatibility
scorer, recorded in `postprocess-checks/release-scorer-equivalence.json`. The
frozen source and every original scoring receipt remain unchanged.

## MPS allocator watermarks — corrected and tested on actual MPS

The common broker in frozen source `c369fe7` sets
`PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.2` without setting the low watermark. On this
unified-memory Mac, PyTorch 2.14.1 defaults the low watermark to 1.4 and rejects
the combination when MPS initializes. Run r03 reproduced
`RuntimeError: invalid low watermark ratio 1.4`, retained the failed probe and
continued on CPU without coordinator guidance.

The [native failure receipt](../../evals/research-v0.3/postprocess-checks/frozen-mps-watermark-defect.json)
identifies the exact request and logs. The installed allocator header and
[PyTorch's environment-variable documentation](https://docs.pytorch.org/docs/2.14/mps_environment_variables.html)
require a low watermark between zero and the high watermark. Commit `5910b36`
sets the low watermark to 0.1 while retaining high 0.2 and disabled fallback.

Earlier validation established that the scientific worker's filesystem/network
sandbox permits MPS and that a per-process memory fraction works. It did not
exercise the broker's complete environment prefix. That validation gap is now
explicit. The [actual full-broker regression](../../evals/research-v0.3/validation/mps-broker-rc2/validation.json)
now passes with a fresh environment: known forward/gradient values, AdamW,
checkpoint reload, resumed-training agreement and finite optimizer states. The
worker does not modify the allocator environment. Actual input-write,
protected-read, outside-workspace-write and live-listener network denials pass.

This defect is shared by both comparison conditions. It can affect backend
choice and throughput, so the comparison must disclose it and cannot support
claims about corrected GPU-path performance. The frozen source, criteria and
candidate work remain unchanged. All twelve assigned sessions completed under
the original freeze; the repair and regression followed the cohort. The result
qualifies this local broker/GPU path, not another model session, other hardware
or instantaneous GPU-memory accounting.

## Storage sampling at process exit — corrected with retained regressions

A supervised worker can finish after the last storage sample but before the
exit-status check. The frozen supervisor then reports `completed` using the
earlier footprint. A controlled sampling/exit interleaving with an actual
subprocess reproduces this: the final workspace is 2,002 bytes against a
1,000-byte cap, while the result says `completed` and its sampled peak is zero.
The source hash, policy, real process receipts and probe are retained at
`evals/research-v0.3/postprocess-checks/final-storage-before/`.

This is a supervisor regression, not a mocked native-host qualification. The
hook reads the actual pre-write size and waits for the actual worker's exit
before returning that earlier sample. It makes a permissible scheduling race
repeatable. It does not establish that a research candidate exceeded its cap.
Separate final-size checks of r01–r10 pass in
`postprocess-checks/final-workspace-sizes-r01-r10.json`; these are current final
footprints, not continuous historical peak observations.

After the cohort, commit `5910b36` adds final persistent-storage measurement to
both supervisors. The unchanged actual-worker probe now returns
`storage_exceeded`, with final and peak 2,002 bytes, in
`postprocess-checks/final-storage-after/`. Existing failure reasons remain
unchanged while a separate flag records any final storage violation. Conformance
also covers this failure-preservation case. Polling limitations remain explicit.

The native session adapter has the analogous gap in its one-second storage
sampling loop. A separately labeled offline fake-CLI fixture reproduces
`completed` with 203,539 final bytes against a 100,000-byte cap. Its actual local
process and controlled interleaving test only the adapter's lifecycle logic;
they are not a hosted model run or native-host qualification. Evidence is at
`postprocess-checks/native-final-storage-before/`. The same fixture against rc2
returns `storage_exceeded`, with final and peak 203,533 bytes, in
`postprocess-checks/native-final-storage-after/`. All twelve actual terminal
workspace-plus-runtime totals are within their assigned limits in
`postprocess-checks/cohort-controls-final.json`. Only aggregate byte totals are
retained; private runtime contents are not exported.

## Retention and release metadata

Controller retention fixes preserve terminal queue references, restore declared
internal directory aliases, recognize the documented manifest entry forms and
stream multi-part archives under per-file limits. Original archives and the
failed oversized-intermediate restoration remain retained. Supplements bind the
original archive index rather than replacing it. The exact cases are documented
in [RETENTION.md](../../evals/research-v0.3/RETENTION.md); six transport regressions
and the final twelve-package archive audit pass.

The final audit also found that the acceptance receipt hard-coded release
`0.2.0`. It now reads the inspected source's `release.json`; the rc2 receipt
records `0.3.0rc2`. This changes release identification, not contract version or
acceptance criteria. The [final I1–I5 run](evidence/rc2/acceptance/acceptance.json)
passes all milestones and 113 conformance tests. No reproduced critical defect
remains open within the documented release scope.
