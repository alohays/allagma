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

## Next concrete work

1. Finish broker restart reconciliation: a controller crash after recording a
   request must reconcile the associated resource receipt before deciding
   whether the request launched, remains live, completed, or was abandoned.
   Never infer restart permission from an observation timeout or missing reply.
2. Prepare candidate input builders and an offline package wheelhouse. Keep
   controller scorers, original answers, all pilot outputs and other candidate
   work unreadable. Match all common input manifests and tools between arms.
3. Run a complete fresh native development study from only its initial brief,
   source materials and resource profile. Use the same common computation broker
   that will serve both final conditions. Record every subsequent assistance.
   Extract necessary generic workflow/bootstrap improvements from this run.
4. Finish protected scientific scorers and frozen manual-review criteria. The
   original CORE-Bench score must remain separate from additional execution and
   evidence measures. EMA/grokking checks must independently recompute saved raw
   evidence and verify protocol controls, uncertainty and honest conclusions.
5. Freeze workflow, inputs, protocol, model/settings, run order, ceilings and
   interventions. Execute all 12 fresh evaluation runs, then complete three
   critically reviewed task packages, clean-checkout full-study reproduction,
   comparison, fixes and release-candidate/migration audit. Preserve failed
   comparison outcomes when making later repairs. Commit increments and push
   origin only when the full goal is achieved.

No clarification or resource expansion is currently required. Historical v0.2
bundles, attempts and publications have not been changed.
