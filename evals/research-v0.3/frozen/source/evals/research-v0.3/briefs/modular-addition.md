# Regularization, memorization and generalization in modular addition

Investigate whether weight decay changes generalization after memorization on
modular addition, and whether a delayed transition meeting an explicit grokking
criterion occurs within a finite training horizon. Design the protocol,
implement the study, execute it, critique it and deliver a reproducible English
research package. The original Power et al. source material provides context;
this bounded MLP study is not an exact replication of its transformer results.

Use ordered pairs `(a,b)` for integers from 0 through 96, with target `(a+b) mod
97`. For each seed, uniformly shuffle all 9,409 pairs and put the first
`floor(0.30*9409)` in training; all other pairs are held out. Use concatenated
one-hot inputs, bias-free Linear(194,128), ReLU, and bias-free Linear(128,97).
Use float32 training. Train full-batch cross-entropy with AdamW at learning rate 0.001, betas (0.9,0.98),
epsilon 1e-8 and weight decay 0 or 1. Compare both conditions with identical
initial weights and identical partitions within a seed. Do not use held-out
labels for optimization, stopping, architecture selection or tuning.

Qualify implementation and cost before confirmation, then freeze the protocol.
Pilot seed 61 is available for small checks. Final confirmation uses seeds
1001, 1002, 1003 and 1004, with 100,000 updates in each condition. Record training
and held-out loss/accuracy from step zero at intervals no coarser than 100
updates. Define memorization as training accuracy at least 99% and generalization
as held-out accuracy at least 95%, each sustained for three recorded evaluations.
Define and justify a delayed-grokking criterion before examining confirmation
curves; report both threshold times and their lag. If a threshold is not reached,
record right-censoring at the horizon, not an invented transition time. A lack of
grokking or an inconclusive regularization effect is a valid scientific result.

Report seed-level paired differences in final held-out accuracy/loss with
uncertainty, individual learning curves, transition/censoring outcomes, and
limitations of the small seed count and finite horizon. Separate claims about
memorization, improved generalization and grokking. Consider sensitivity to the
chosen transition definition without changing the frozen primary analysis.
Do not infer generalization from training accuracy.

Retain exact partitions, initial-state hashes, configurations, source revisions,
all attempts, learning curves, final predictions/logits for every pair and
loadable checkpoints. Include known-answer label/split checks and recompute
endpoint metrics from retained predictions; independently reload representative
checkpoints to verify predictions. Produce at least one reproducible learning
curve figure, machine-readable per-seed results, an evidence-linked English
report and substantive critique with resolved/unresolved findings.

Read `COMPUTE.md` and `RESOURCES.json`. Use the common local client for every
environment setup and scientific command. The first marked scientific attempt
will be interrupted; retain it and recover autonomously within the same ceilings.
Keep computation on this Mac, in an isolated environment, with no network or
paid experiment services. Respect the resource stops; do not select a shorter
confirmation horizon after seeing outcomes. Do not reuse pilots as confirmation.

Deliver `REPORT.md`, `review.json`, `REPRODUCE.md`, `artifact-manifest.json` and
`submission.json`. Include `task_id: "modular-addition"`, `execution_status`
(`complete`, `partial` or `blocked`), relative `manuscript`, `review`,
`artifact_manifest` and `measurements` paths, and `reproduce` and `recompute`
objects with `argv` string arrays and relative `cwd`. Reproduce must create a
fresh environment and train the complete study; recompute must derive reported
metrics and analyses from retained evidence. Use `MEASUREMENTS.md` for the common
measurement interchange format and document other formats and exact check
coverage. Do not pool repeated agent executions as additional independent seeds.
