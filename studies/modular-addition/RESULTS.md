# Verified modular-addition study

A native Codex session compared weight decay in a small modular-addition MLP.
It returned training curves, checkpoints, paired statistics and a report:
held-out accuracy improved, but no trajectory met the prespecified grokking
threshold. These are retained results from run r04.

All eight prescribed trajectories completed 100,000 full-batch AdamW updates on
the fixed 37,248-parameter MLP. Within each of four independent seeds, weight
decay 0 and 1 share the same initialization and 30% training partition. All eight
memorized the training set. None reached 95% held-out accuracy for three
consecutive evaluations, so generalization onsets and grokking lags are censored.

| Seed | Held-out accuracy, decay 0 | Held-out accuracy, decay 1 | Paired difference |
| --- | ---: | ---: | ---: |
| 1001 | 0.000000 | 0.665402 | 0.665402 |
| 1002 | 0.000000 | 0.652346 | 0.652346 |
| 1003 | 0.000000 | 0.820252 | 0.820252 |
| 1004 | 0.000152 | 0.560498 | 0.560346 |

The mean paired accuracy change is **67.46 percentage points**, with a 95%
Student t interval of 50.31–84.61 points (four seeds, three degrees of freedom).
The mean held-out cross-entropy change is −158.62 nats, with interval
[−165.78, −151.45]. Each exact two-sided sign-flip calculation gives p=0.125;
four seeds cannot resolve smaller two-sided p-values by this enumeration. The
t intervals rely on fragile small-sample distributional assumptions. Endpoint
improvement does not establish a delayed 95%-accuracy grokking transition.

## Execution and verification

The first fully verified Allagma package in frozen run order is **r04**
(replicate 2). This is the illustrative package required by the prespecified
criteria. The [complete comparison](../../docs/v0.3/COMPARISON.md) reports the
observed workflow differences and their substantial uncertainty.

The original scorer passes **40/40 checks**; the controller's eight evidence
requirements also pass. Independent checks reproduce the paired statistics,
censoring and sensitivity outcomes, and verify all optimizer counters and
checkpoint-to-NPZ identities. See [numerical scoring](../../evals/research-v0.3/runs/r04/score.json),
[independent analysis](../../evals/research-v0.3/runs/r04/independent-analysis.json)
and the [substantive review](../../evals/research-v0.3/runs/r04/substantive-review.json).

The agent preserved an interrupted pilot, an MPS initialization failure from the
shared frozen broker, and an initial loss-tolerance check failure. It qualified
CPU training and amended only the float32/float64 validation tolerance before
continuing, with no coordinator messages or resource expansion. The numerical
amendment and original source remain retained. Computation consumed 1,186.59
seconds, setup 14.73 seconds and the native session 1,942.91 seconds. Full usage
and observed resource fields are in the [session receipt](../../evals/research-v0.3/runs/r04/sessions/evaluation/native/session.json).

The result applies to these paired seeds, architecture, optimizer, split
fraction and horizon. It does not replicate the source paper's transformer
experiments or establish a general law of regularization. Scientific critique
and controller review are provisional, not independent scientific peer review.

## Restore the complete research package

The [package index](../../evals/research-v0.3/runs/r04/package/package-index.json)
identifies the original report, protocol, source, curves, checkpoints, analysis,
review and pinned dependency wheels. The transport supplement preserves terminal
queue references omitted by the original archive without changing that archive
or any candidate artifact.

```sh
python3 evals/research-v0.3/retention.py restore \
  --source evals/research-v0.3/runs/r04/package \
  --destination /path/to/new-modular-addition-package --download-wheels
```

An exact local wheel cache can replace downloads. Restoration of all 548
candidate manifest entries and 87 reviewed references has [passed](../../evals/research-v0.3/runs/r04/package-restoration.json).
Read the restored `REPORT.md`, `REPRODUCE.md` and `submission.json`. Use a new
[standalone broker driver](../../docs/research-workspaces.md) and finite resource
profile to service `python3 scripts/driver.py reproduce`. It sets up a fresh
environment, runs qualification and all eight full trajectories, and analyzes
the results. The documented raw-only entry point uses the isolated study
environment and a new output directory. Raw reanalysis was executed and matched;
a second complete training replay was not performed or claimed. The release's
separate full clean-checkout execution gate passed on CORE CULP.
