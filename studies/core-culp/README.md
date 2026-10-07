# Local computational reproduction: CULP

Status: compatibility preflight and the first final Allagma run passed. Its
[verified results and retained package](RESULTS.md) are available; the remaining
controlled comparison and clean-checkout release gate are still in progress.

This study uses CORE-Bench's public training task `capsule-6460826`, **CULP:
Classification Using Link Prediction**. The original task requires execution
of `iris_sample.py`, `zoo_sample.py` and `wine_sample.py`, then answers six
questions about the resulting prediction accuracies. Original question strings,
reference answers and the upstream scoring function are retained in the
controller-only `reference/` directory. They must not be copied wholesale into
candidate workspaces.

The [preflight receipt](development/preflight.json) records actual CPU execution
on this Mac and 6/6 accepted answers using the unchanged upstream numerical
scoring function. The first cold invocation exceeded a 30-second script timeout;
an import diagnostic and a preserved second attempt established compatibility.
The accepted attempt changed only two absolute `/data/` paths to capsule-relative
paths. Scientific parameters and algorithms stayed intact. The isolated local
dependency set is retained in `development/requirements.lock`.

For final evaluation, use the CORE-Bench-Hard input exclusions: no original
results, `REPRODUCING.md`, environment directory or `code/run.sh`. Preserve the
upstream task prompt, question keys and scorer. The local Mac, curated package
availability and additional evidence requirements differ from the official
harness; report a **local selected CORE-Bench task evaluation**, not a leaderboard
score or full benchmark claim. Original correctness and additional execution,
evidence and review measures must be reported separately.

The source scripts for Iris and Zoo loop over predictor labels but always invoke
the CS predictor. A faithful computational reproduction preserves and discloses
this limitation. Its printed labels do not establish an actual CN-versus-AA
scientific comparison. A separate corrected algorithm experiment would require
a new question and must not replace this task's original scoring.

Source and exact archive provenance are in `reference/provenance.json`.
[CORE-Bench](https://github.com/siegelz/core-bench) uses MIT licensing, retained
as `reference/CORE-Bench-LICENSE`; capsule code and data retain their own license
files. Generated Allagma documentation and preflight code are AI-assisted.
