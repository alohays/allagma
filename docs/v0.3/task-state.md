# v0.3 continuation state

Status: active development. The full goal in [GOAL.md](../../GOAL.md) is unchanged.
The [requirement ledger](requirements.md) remains the completion standard.
There are **zero final evaluation runs**, no comparison report, and no v0.3
release-candidate completion claim. This goal turn made implementation and
experimental progress; it was not a blocked or no-progress turn.

## Completed development work

- The finite standard-library resource supervisor has real process tests and
  preserved development receipts. A real setup run exposed and motivated a fix
  for stale process snapshots being mistaken for live orphaned children.
- CULP (`capsule-6460826`) passed CPU preflight with original science and scoring:
  6/6 original answers, with only two container data-path changes. First-import
  failure and diagnostic evidence are retained. Its original Iris/Zoo label bug
  remains a disclosed limitation. A custom external-task fallback is unnecessary.
- EMA pilots completed all four duration/schedule cells on GMM8, plus both
  schedules at 10,000 updates on moons. Independent SciPy calculations reproduce
  all 18 variant SW1 metrics and mixture counts; matching input hashes and
  learning-rate schedules were checked. These are pilot results only.
- Grokking pilots completed 100,000 updates with weight decay 0 and 1 for seeds
  17 and 29, following an earlier 10,000-update probe. Both seeds memorized the
  training partition. Regularized final test accuracy was about 67–70%; the
  unregularized runs were near zero. No run reached the proposed 95% grokking
  threshold. Aggregate-curve/partition checks pass; endpoint predictions and
  checkpoints were not saved by these feasibility pilots and must be retained
  in final study runs.
- Native filesystem isolation and a separate sandboxed MPS computation-worker
  prototype passed scoped canaries. All failed attempts remain recorded. The
  common resource broker has passed a real interrupted-attempt/retry integration
  check. See [native isolation](native-isolation.md).

The study-compute ceiling is still 1,800 seconds for development, with a separate
900-second setup ceiling and at most 24 marked computational attempts. Consult
`allagma resource status --ledger evals/research-v0.3/development/resource-ledger`
for current authoritative usage. The last account checkpoint permits normal
Codex use and records 6% weekly usage. Model usage is separate from study compute.

## Native development and current interface

A complete fresh native CORE study finished with zero follow-up messages. It
preserved and recovered the controlled interruption, repaired a fresh-environment
verification timeout, and delivered a critically reviewed package. The original
CORE-Bench scorer accepts 6/6 answers, and all 365 declared artifact hashes were
verified before archiving the exact package. Evidence is under
`evals/research-v0.3/development/sessions/dev-core-01/`.

The source now provides `research prepare/run/status`, a standalone broker driver,
explicit broker restart reconciliation and baseline preparation for controlled
evaluation. The native task exposed a generic-helper two-observation assumption;
analysis minima are now study-owned, and paired seed reuse requires explicit
condition identities. Historical bundles remain unchanged. The release candidate
is 0.3.0rc1. A full I1–I5 acceptance run and 109 conformance tests passed; subsequent
focused control checks passed. The protected scorer's five scientific checks pass,
including an actual development-checkpoint replay. The last account checkpoint
permits ordinary use with 9% weekly usage consumed.

## Next concrete work

1. Commit the candidate controls/evidence, then freeze `evaluate.py`, `score.py`,
   criteria, profiles, briefs, exact common materials, workflow source, CLI/model
   settings and the counterbalanced 12-run order. No final run has started yet.
2. Prepare and launch runs through `evals/research-v0.3/evaluate.py`, using the
   public research workspace API for both arms (methods installed only for
   Allagma). Check account limits before each run. Keep sessions serial and do
   not change frozen control code or criteria during the comparison.
3. Score all outcomes and complete the frozen substantive/evidence review;
   preserve failures and distinguish model completion from task completion.
   Retain software-wheel hashes without placing individual >100 MB files in Git;
   provide verified hydration or chunked archives as appropriate.
4. Complete all three task packages, a clean-checkout full-study reproduction,
   raw-data recomputation, comparison report and final release/migration audit.
   Preserve frozen outcomes when making later repairs. Push origin only when
   the full goal is achieved.

The original development attempt cap has been reached (24 marked attempts);
no additional marked development experiment is authorized under that same
policy. Bounded checks/recomputation and setup still have time remaining. Final
run allocations are new, explicit profiles chosen from the completed pilots,
not edits to the development ledger. No unresolved user choice is currently
required. Do not mark the goal complete before all remaining gates pass.

## Frozen evaluation started

The controls are committed at `de6abce`; the frozen source is `c369fe7` plus the
exact files in `evals/research-v0.3/frozen/freeze.json`. All twelve workspaces are
prepared, and their common inputs match exactly within each task. Read the
frozen run order and `evals/research-v0.3/progress.json` before continuing.

Run **r01 (CORE CULP, Allagma, replicate 2)** is active under exec session
**57392**. Poll that handle and inspect its authoritative process state; do not
restart it just because an observation times out. Its controller/runtime files
are under `evals/research-v0.3/runs/r01/`. Actual final-runtime probes deny reads
of original answers, writes to the scorer, and reads of the other workspace.
They changed no candidate or protected file content.

No final run is complete yet. After r01 terminates, retain/score its outcome and
check account limits before launching r02. The prepared runs use the public
research interface, matching model/CLI/tools and finite per-task ceilings. No
frozen code, criterion or input may be edited during the comparison. All prior
work and remaining full-goal requirements still apply.
