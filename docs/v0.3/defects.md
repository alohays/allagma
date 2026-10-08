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

## MPS allocator watermarks — reproduced, correction pending

The common broker in frozen source `c369fe7` sets
`PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.2` without setting the low watermark. On this
unified-memory Mac, PyTorch 2.14.1 defaults the low watermark to 1.4 and rejects
the combination when MPS initializes. Run r03 reproduced
`RuntimeError: invalid low watermark ratio 1.4`, retained the failed probe and
continued on CPU without coordinator guidance.

The [native failure receipt](../../evals/research-v0.3/postprocess-checks/frozen-mps-watermark-defect.json)
identifies the exact request and logs. The installed allocator header and
[PyTorch's environment-variable documentation](https://docs.pytorch.org/docs/2.14/mps_environment_variables.html)
require a low watermark between zero and the high watermark. The proposed fix
sets the low watermark to 0.1 while retaining the high limit of 0.2.

Earlier validation established that the scientific worker's filesystem/network
sandbox permits MPS and that a per-process memory fraction works. It did not
exercise the broker's complete environment prefix. That validation gap is now
explicit. The release correction must include an actual broker-mediated MPS
allocation/training/checkpoint test, with both memory settings and the existing
protection checks; a configuration-string or mocked-process test is insufficient.

This defect is shared by both comparison conditions. It can affect backend
choice and throughput, so the comparison must disclose it and cannot support
claims about corrected GPU-path performance. The frozen source, criteria and
candidate work remain unchanged. A user-input question offers retaining the
current comparison with a separately validated correction, or archiving it and
restarting all twelve runs under a new freeze. In the meantime, the already
authorized run continues within its existing CPU-compatible limits.

No release completion claim is permitted while this reproduced defect remains
unresolved. Any correction and its validation retain a new source revision;
they must not overwrite or silently relabel the current frozen outcomes.

## Storage sampling at process exit — reproduced, correction pending

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

After the cohort, remeasure persistent storage after process termination,
retain that final measurement, and change a nominal successful result to
`storage_exceeded` when appropriate. Preserve existing failure reasons and
sampling limitations. The same actual-worker regression must then detect the
violation, alongside the affected offline resource checks and final acceptance.
