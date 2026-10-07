# Defects found after the evaluation freeze

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
