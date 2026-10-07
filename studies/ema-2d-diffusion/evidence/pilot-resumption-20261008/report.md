# Fresh native pilot resumption: ema-v1

Both local wrappers and the exact campaign-pinned canonical skills and module contracts were read. Both entry commands resolved to bundle `b-2b63431e34a085598aaade78` with exit code 0.

Four sequential `python3 manage.py pilot` commands completed. Each actual command was awaited to termination and its terminal attempt, evaluation, and referenced file digests were inspected before the next launch.

| Attempt | Status | Evaluation checks | Attempt seconds | Ledger seconds |
| --- | --- | ---: | ---: | ---: |
| [pilot-moons-11-a002](../../campaigns/ema-v1/runs/pilot-moons-11/attempts/002/record.json) | succeeded | 21 passed | 14.311593 | 14.435189 |
| [pilot-moons-12-a001](../../campaigns/ema-v1/runs/pilot-moons-12/attempts/001/record.json) | succeeded | 21 passed | 14.214661 | 14.325514 |
| [pilot-gmm8-21-a001](../../campaigns/ema-v1/runs/pilot-gmm8-21/attempts/001/record.json) | succeeded | 27 passed | 14.040583 | 14.155808 |
| [pilot-gmm8-22-a001](../../campaigns/ema-v1/runs/pilot-gmm8-22/attempts/001/record.json) | succeeded | 27 passed | 14.333776 | 14.475631 |

Four-pilot ledger charge: **57.392141 seconds**. Total study charge: **100.372780 / 1800 seconds**. Remaining: **1699.627220 seconds**. The total retains all earlier setup charges, the interrupted attempt and the 15.3-second feasibility estimate. Five of 18 training attempts have been used, including the retained interruption.

Local runner receipts record $0.00; native model usage is accounted separately. No model override or additional model session was used.

All 151 protected files match the preflight hashes, including the lock, protocol, bundle, materials, study code and all files from interrupted attempt `pilot-moons-11-a001`. Its `partial-training.json` still records 100 updates, seed 11 and `scientific_evidence: false`; no raw result or evaluation was manufactured for it.

All 96 per-pilot evaluation checks passed. The latest retained known-answer check passed six tests; it was inspected, not rerun in this session. The evaluator covers complete native MPS trajectories, seeded held-out reconstruction, checkpoint hashes, finite output, SciPy projected W1 cross-checks and mixture coverage consistency. This is not independent scientific peer review; campaign assurance remains `unreviewed`.

The campaign remains paused in the pilot phase at the requested checkpoint. `confirmation-freeze.json` is absent and no confirmation attempt has started. The next planned run is `confirm-moons-1001`; neither freeze nor confirmation was invoked.

Exact commands, receipt paths, hashes and costs are in [result.json](result.json), with the initial protected-file snapshot in [preflight.json](preflight.json).
