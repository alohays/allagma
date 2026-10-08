# v0.3 continuation state

The full goal in [GOAL.md](../../GOAL.md) remains active and incomplete. Use the
[acceptance ledger](requirements.md) for release requirements and
`evals/research-v0.3/progress.json` for the current live handle. Historical
receipts and frozen bundles remain unchanged.

## Current comparison

Four of twelve native sessions are terminal. Three original packages meet all
required evidence items:

| Run | Assignment | Numerical checks | Evidence | Verified package |
| --- | --- | ---: | ---: | --- |
| r01 | CORE, Allagma, replicate 2 | 6/6 original | 8/8 | yes |
| r02 | CORE, plain, replicate 2 | 6/6 original | 8/8 | yes |
| r03 | Modular addition, plain, replicate 2 | 40/40 corrected parser | 7/8 | no: review lacks an explicit material revision |
| r04 | Modular addition, Allagma, replicate 2 | 40/40 original and compatible | 8/8 | yes |

**Active: r05, modular addition, Allagma, replicate 1. Exec session 20443.**
The actual process remains live and has started confirmation after pilot
recovery. Poll the known handle/process; do not restart based on an observation
timeout or a running-state file. Next is r06, then the remaining frozen order.
The pre-r05 account checkpoint permits ordinary use with 17% weekly usage.
Check account limits again before starting the next session.

Frozen source is `c369fe7`, with freeze commit `de6abce`. All twelve prepared
input inventories match within task. `evaluate.py verify` still passes after
postprocessing/documentation changes. Keep runs serial, candidate workspaces
isolated, and all frozen criteria, code, inputs, model/settings and ceilings
unchanged. No task-specific coordinator messages have been sent.

The first fully verified Allagma packages, selected by the prespecified rule,
are CORE r01 and modular addition r04. The latter completes all eight 100k
trajectories: all memorized, none reached the sustained 95% held-out threshold.
Mean paired held-out accuracy improvement is 67.46 percentage points, with
four independent seeds and explicitly limited inference. Repeated sessions do
not add scientific seeds. Detailed reports and reproduction instructions are in
`studies/core-culp/RESULTS.md` and `studies/modular-addition/RESULTS.md`.

## Passed and pending release gates

A clean Git clone at `a5ac168` restored the CORE r01 package and exact software
wheels, built a fresh environment, reran the full study and separately
recomputed the raw results. All six answers match. This passes the at-least-one
full clean-checkout reproduction requirement, not a second training replay for
modular addition or EMA.

The pre-freeze source passed all I1–I5 acceptance and 109 conformance checks.
Current version is 0.3.0rc1; no final v0.3 release qualification is claimed.
The standard-library defaults and scientific study separation remain required.

The separate controller-validation ledger retains a finite 1800-second compute,
600-second setup and 64-request allocation. Check its actual status before new
work. Scientific scoring/replay costs and native account usage are distinct.
Development's 24 marked-attempt ceiling has been reached; do not reuse that
allocation for new marked training or silently expand any ceiling.

## Defects and preservation rules

- The shared frozen broker sets MPS HIGH=0.2 but leaves LOW at its incompatible
  default 1.4. CPU recoveries remain part of the frozen outcomes. The optional
  question about restarting the cohort has received no new direction; continue
  the authorized frozen comparison, disclose the defect, then repair separately.
  Do not claim corrected GPU-path performance from this cohort.
- The frozen curve parser disagrees with the inline-list measurement contract.
  Preserve original scoring receipts. The separate compatibility scorer changes
  only that loader, applies uniformly, and reproduces the original calculations
  on equivalent path-based data.
- The initial archive transport omitted terminal `.compute/` evidence. Its
  correction retains exact queue bytes in supplements for r01–r04, preserves
  original archives/indexes, and includes them directly in future collections.
  Actual r04 restoration verifies all 548 manifest files and 87 direct reviewed
  references. This is controller transport repair, not candidate assistance.

`docs/v0.3/defects.md` retains the reproduced infrastructure defects. The actual
full-broker MPS regression is prepared in `validation/check_mps_broker.py` and
`mps_broker_canary.py`; syntax/help only have passed. Execute it after the
post-cohort source repair and retain actual outcomes. Its test does not set the
watermarks itself or claim native-agent qualification.

## Remaining work

1. Complete and honestly score r05–r12. Preserve failed outcomes and all original
   packages. Apply the eight-item substantive rubric and independent science
   checks without changing candidate artifacts.
2. Finish the EMA task package and any separately identified package repairs.
   Do not rewrite unsuccessful original comparison outcomes.
3. Generate the final comparison only when all twelve reviews are terminal.
   `comparison.py` reports all assigned runs, six paired contrasts, within-task
   ranges, failures, interventions and separate usage fields. The four-run
   snapshot is explicitly partial; it supports no broad superiority inference.
4. Correct the MPS environment in a new release revision, execute the real
   broker regression, complete migration/release notes and exact-final-source
   acceptance/conformance checks. Preserve historical bundle identities.
5. Commit coherent milestones, then push to `origin` only when all full-goal
   requirements pass. Mark the goal complete only after the authorized push.
