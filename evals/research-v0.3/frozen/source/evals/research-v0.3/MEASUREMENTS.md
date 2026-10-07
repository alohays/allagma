# Task-owned interchange format for independent evaluation

This format is common to both conditions. It contains measurements and evidence
references, not a research workflow. Write it to the path named by
`submission.json` → `measurements`. Paths below are workspace-relative regular
files. NumPy archives must be loadable with `allow_pickle=False`.

Both scientific tasks use an object with `format: "research-measurements-v1"`,
`task_id`, `protocol` (path to the protocol frozen before confirmation), and
`runs` (a list). Retain additional study-owned artifacts as needed.

## EMA schedule task

Each run entry represents one dataset/seed/duration/schedule cell and contains:

- `dataset`: `moons` or `gmm8`; `seed`; `updates`: 5000 or 10000;
  `schedule`: `constant` or `cosine`; `phase`: `confirmation`.
- `device`: `cpu` or `mps`, matching the backend used for saved samples.
- `arrays`: NPZ path with `heldout` (2048×2), `generation_noise` (100×2048×2),
  and `raw`, `ema099`, `ema0999` generated sample arrays (each 2048×2).
- `weights`: NPZ path with reference state-dictionary keys prefixed by
  `raw__`, `ema099__` and `ema0999__`, respectively. Retain all state entries,
  including embedding buffers.
- `metrics`: a mapping from those three variant names to objects containing
  `sw1`. GMM8 entries also contain `mode_counts` (eight integer counts),
  `covered_modes` and `inlier_fraction`.
- `initial_weights_sha256`, `training_prefix_5000_sha256`, `heldout_sha256`,
  `generation_noise_sha256`; retain the corresponding inputs/initial weights so
  these provenance assertions can be inspected. `training_prefix_5000_sha256`
  identifies the same actual training input/noise/time-step prefix across cells.
- `source_revision`, `attempt_id`, `training_trace` (relative artifact path).

A shared constant-policy trajectory may produce both required duration cells.
Checkpoint/sampling artifacts must identify their actual optimizer update.
Never relabel a cosine intermediate checkpoint as a different schedule policy.

## Modular-addition task

Each run entry represents one seed/weight-decay condition and contains:

- `seed`; `weight_decay`: 0 or 1; `updates`: 100000; `phase`: `confirmation`.
- `arrays`: NPZ path with `pairs` (9409×2 integer ordered pairs), `labels`
  (9409 integers), `train_indices`, `test_indices`, `logits` (9409×97), and
  `predictions` (9409 integers). Logits/predictions must come from final weights.
- `weights`: NPZ path with `input_weight` (128×194) and `output_weight` (97×128).
- `curve`: JSON list with `step`, `train_accuracy`, `test_accuracy`, `train_loss`
  and `test_loss` per evaluation, including steps 0 and 100000. The interval is
  at most 100 updates. Retain any more detailed training trace separately.
- `metrics`: `train_accuracy`, `test_accuracy`, `train_loss` and `test_loss` at
  the final update. Use probabilities in [0,1] for accuracy, not percentages.
- `initial_weights_sha256`, `source_revision`, `attempt_id`; retain the initial
  weights and exact configuration in the accompanying package.

Analysis outputs should retain per-seed paired differences, uncertainty method,
transition definitions and censoring information. The independent evaluator
will recompute endpoint measurements from arrays and check saved weights. It
will separately inspect protocol controls, uncertainty, figures, critique and
reproduction. Passing one numerical check does not imply a complete package.
