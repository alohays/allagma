# v0.3 continuation state

The full [goal](../../GOAL.md) is active and incomplete. The
[requirement ledger](requirements.md) governs completion. The last turn made
verified implementation/evaluation progress; this is not a blocked state.

## Current assigned runs

| Run | Assignment | Numerical | Evidence /8 | Required execution | Package complete |
| --- | --- | ---: | ---: | --- | --- |
| r01 | CORE, Allagma, replicate 2 | 6/6 | 8 | verified | yes |
| r02 | CORE, plain, replicate 2 | 6/6 | 8 | verified | yes |
| r03 | Modular addition, plain, replicate 2 | 40/40 corrected loader | 7 | verified | no: review revision binding |
| r04 | Modular addition, Allagma, replicate 2 | 40/40 | 8 | verified | yes |
| r05 | Modular addition, Allagma, replicate 1 | 40/40 corrected loader | 8 | verified | yes |
| r06 | Modular addition, plain, replicate 1 | 40/40 corrected loader | 7 | verified | no: review revision binding |
| r07 | EMA schedule, Allagma, replicate 2 | 240/240 | 8 | verified | yes |
| r08 | EMA schedule, plain, replicate 2 | 240/240 | 8 | verified | yes |
| r09 | CORE, plain, replicate 1 | 6/6 | 8 | verified | yes |
| r10 | CORE, Allagma, replicate 1 | 6/6 | pending | pending review | pending |
| r11 | EMA schedule, plain, replicate 1 | pending | pending | active | pending |
| r12 | EMA schedule, Allagma, replicate 1 | pending | pending | not started | pending |

**Active native run: r11; exec session 54217. Next: r12.** Poll that handle or
its actual process, never restart from a running-state file or observation timeout.
`evals/research-v0.3/progress.json` retains the current handle. The pre-r11 account
checkpoint allows ordinary usage with 27% of the weekly window consumed.

All ten terminal sessions have unchanged common inputs and matching observed
model/settings, with one fresh session each. No task-specific coordinator
messages or candidate edits have occurred. Keep the source/criteria/model/CLI
freeze unchanged until all twelve sessions are terminal. `evaluate.py verify`
checks the current launch guard. Frozen source is `c369fe7`, freeze `de6abce`.

## Verified task packages and release evidence

The prespecified first verified Allagma examples are CORE r01, modular addition
r04 and EMA schedule r07. Their study `RESULTS.md` files link exact packages and
verification; the EMA summary includes its original figure. All three task
families have complete original packages. This is not completion of the whole
12-run comparison or a general workflow-superiority claim.

A clean Git clone at `a5ac168` restored CORE r01, installed a fresh environment,
reran its complete study and separately recomputed raw results. Both answer sets
match. This passes the at-least-one full clean-checkout study gate for that
recorded source/package; it is not an EMA/modular-addition retraining claim.
Pre-freeze I1–I5 acceptance and 109 conformance checks passed. Current framework
version remains 0.3.0rc1; exact-final-source release qualification is still needed.

The independent controller validation profile is unchanged: 1800 compute seconds,
600 setup seconds, 64 compute requests and finite per-command/memory/storage/file
limits. Consult its actual ledger before new work. Development's 24 marked
attempts are exhausted; do not reuse or expand that allocation. The default
conformance kit and toy remain offline and standard-library-only.

## Preserved defects and corrections

- The frozen broker sets MPS HIGH=0.2 but omits LOW, whose default 1.4 is invalid.
  r03–r06 used CPU. r07/r08 independently set LOW=.1 in their study runners while
  preserving HIGH=.2, and completed actual MPS science. These are candidate
  recoveries, not a repair of the shared broker. Fix the new release after the
  cohort and run the prepared actual `validation/check_mps_broker.py` regression.
  Only syntax/help have been checked for that regression so far.
- Original inline-curve scorer errors are preserved. The separate compatible
  scorer changes only list/path loading and is applied uniformly; numerical
  criteria are unchanged. Original and corrected receipts remain separate.
- Controller retention now preserves terminal queue evidence, explicitly
  relocates confined internal dependency aliases, accepts `files`/`artifacts`
  manifest containers, and streams large archives. Failed collection/restoration
  attempts and old indexes remain. The actual 829 MB r07 restore passed under
  the unchanged 512 MiB per-file ceiling; six transport regressions pass.
- A suspected r05 reproduction-interpreter defect was disproved: its staging
  helper uses copied interpreters on this host. Failed/corrected controller
  probes are retained; do not count that investigation as a candidate defect.

See `docs/v0.3/defects.md` and the per-run controller receipts. No locked bundle,
original attempt, candidate source or outcome has been repaired in place.

## Latest verified outcomes

r08: all 32 EMA cells, 24 trajectories and 200000 updates; original 240/240 score.
Independent inputs/initializations and 66 paired summaries, eight absolute rows
and twelve coverage rows pass. Review binds report-v1, explicitly responds with
report-v2, and both retained revisions verify. Scientific artifacts are unchanged
between revisions. All 356 manifest entries pass after restoration. Source and
report scopes distinguish full learning-rate policy from endpoint rate and
retain the small-n/multiplicity limits. Eight evidence items pass.

r09: original CORE 6/6; only two source path edits/imports. Controller checks
independently reproduce every predictor vector from saved graphs, fixed splits
and Wine normalization, and compare all 96 arrays/348 predictions with the
actually executed fresh-environment rerun. All 349 manifest entries and 227
reviewed material hashes pass after restoration. Source-label defects and
transductive/duplicate/tie limitations remain explicit. Eight evidence items pass.

r10: native completed; original score 6/6 and package collection finished (594
regular files plus 13 external wheels, one archive part, no manifest errors).
Substantive source/execution/review, independent checks and restoration still
need inspection. Candidate is `work/v03-evaluation/runs/r10/candidate`.

## Remaining work

1. Finish r10's substantive review; complete and score r11/r12 in frozen order.
   Preserve all failed outcomes and record all eight evidence items honestly.
2. Generate the complete comparison only after all twelve reviews. Keep required
   execution distinct from package completion: r03/r06 ran correct science but
   lack explicit review/material revision binding. Latest interim comparison is
   `comparisons/after-r09-reviewed/`. Two sessions per condition support only
   descriptive task-specific comparisons, not broad superiority.
3. Repair the shared MPS prefix in a separately versioned release, execute the
   real broker regression without a worker-side workaround, and retain all
   before/after evidence. Complete release/migration notes, historical bundle
   integrity and exact-final-source catalog/conformance/I1–I5 acceptance.
4. Commit coherent milestones and push to origin only after all required work
   passes. The goal cannot be marked complete before the authorized push.
