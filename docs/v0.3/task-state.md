# v0.3 continuation state

The full goal in [GOAL.md](../../GOAL.md) remains active and incomplete. Use the
[acceptance ledger](requirements.md) for release requirements and
`evals/research-v0.3/progress.json` for the current live handle. Historical
receipts and frozen bundles remain unchanged.

## Current comparison

Eight of twelve native sessions are terminal. Seven reviews are complete; five
original packages meet all
required evidence items:

| Run | Assignment | Numerical checks | Evidence | Verified package |
| --- | --- | ---: | ---: | --- |
| r01 | CORE, Allagma, replicate 2 | 6/6 original | 8/8 | yes |
| r02 | CORE, plain, replicate 2 | 6/6 original | 8/8 | yes |
| r03 | Modular addition, plain, replicate 2 | 40/40 corrected parser | 7/8 | no: review lacks an explicit material revision |
| r04 | Modular addition, Allagma, replicate 2 | 40/40 original and compatible | 8/8 | yes |
| r05 | Modular addition, Allagma, replicate 1 | 40/40 corrected parser | 8/8 | yes |
| r06 | Modular addition, plain, replicate 1 | 40/40 corrected parser | 7/8 | no: review lacks an explicit material revision |
| r07 | EMA schedule, Allagma, replicate 2 | 240/240 original | 8/8 | yes |
| r08 | EMA schedule, plain, replicate 2 | 240/240 original | pending | pending substantive review |

**Active: r09, CORE CULP, plain Codex, replicate 1. Exec session 21363.**
The new native process has been launched under the frozen controls. Poll the known handle/process; do not restart based on an observation
timeout or a running-state file. Next is r10, then r11 and r12.
The pre-r09 account checkpoint permits ordinary use with 24% weekly usage.
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

1. Finish r08 substantive review and complete/score r09–r12. Preserve failed outcomes and all original
   packages. Apply the eight-item substantive rubric and independent science
   checks without changing candidate artifacts.
2. The three illustrative packages are now verified; finish any separately identified required repairs.
   Do not rewrite unsuccessful original comparison outcomes.
3. Generate the final comparison only when all twelve reviews are terminal.
   `comparison.py` reports all assigned runs, six paired contrasts, within-task
   ranges, failures, interventions and separate usage fields. The six-run
   snapshot is explicitly partial; it supports no broad superiority inference.
4. Correct the MPS environment in a new release revision, execute the real
   broker regression, complete migration/release notes and exact-final-source
   acceptance/conformance checks. Preserve historical bundle identities.
5. Commit coherent milestones, then push to `origin` only when all full-goal
   requirements pass. Mark the goal complete only after the authorized push.

## Fifth-run verification and transport follow-up

r05 completed all eight trajectories using an inspected C/Accelerate float32
implementation. The 40 endpoint checks, independent gradients/individual AdamW
updates, paired uncertainty, censoring and native optimizer states pass. Its
mean paired accuracy improvement is 59.78 percentage points; no generalization
threshold or grokking event occurred. The report preserves the preconfirmation
pilot-gate revision and explicitly disclaims long-horizon bitwise PyTorch identity.
Its first fully verified package does not replace r04 as the prespecified example.

Native wall time was 2442.58 seconds; charged compute 1403.91 seconds and setup
35.26 seconds, with 32 compute requests. Actual final receipt fields and failures
are retained under r05. Zero coordinator messages or candidate edits occurred.

The r05 transport initially rejected an absolute internal wheel-directory alias.
A new indexed link representation preserves the original literal target and
restores the same internal content through a relative alias. The candidate is
unchanged; the failed collection remains retained. Restore now passes all 575
active manifest files and 128 relative reviewed references. External or excluded
link targets remain rejected.

A controller hypothesis about reproduction-interpreter symlink resolution was
**disproved**: the staging helper creates a copied executable on this host. Both
actual interpreter probes use the correct fresh prefix and installed packages.
The failed assertion, original probe source, corrected probe and resolution are
retained; do not classify this controller investigation as a candidate defect.

The new archive verifier checks historical frozen bytes after a later source
repair, without altering the original launch guard. The latest partial archive
check passes 127 frozen source files, all 12 prepared inputs/profiles, and all
five retained packages. Final verification must require all twelve packages.

## Sixth-run result and initial EMA recovery

r06 completed all eight 100k CPU trajectories. It independently diagnosed five
auxiliary float64 near-tie class changes, all between wrong held-out classes,
and retained the failed exact-argmax check, source and numerical amendment.
Controller checks confirm all 40 required endpoint checks, all optimizer states,
paired statistics, 108 sensitivity rows and the propagated numerical bound.
The report and substantive critique are detailed, but the review does not name
its reviewed material revision. Apply the same E8 gap as r03: required execution
verified, 7/8 evidence, original package completion false. Do not conflate this
binding gap with missing experiments or absent scientific critique.

r06 used 1320.09 compute seconds, 16.53 setup seconds and 2663.10 native seconds,
with 23 compute requests. Its manifest uses an `artifacts` list, which the first
collector did not recognize. The original index notice remains; a separate
identical hash check now verifies all 456 entries before and after restoration.
This is controller parser support, not candidate repair.

r07 independently set `PYTORCH_MPS_LOW_WATERMARK_RATIO` to 0.1 in its study runner
before importing torch, while the broker's high limit stays 0.2. Its corrected
MPS pilot and qualification passed, and GPU confirmation subsequently completed. No coordinator
hint was supplied. This candidate-local recovery does not repair the frozen
shared broker. The later r07 verification establishes its study completion. The release still
requires the separately versioned full-broker repair and prepared actual test.

## Seventh package verified; eighth review pending

r07 is the prespecified EMA example: 32 cells, 96 states and 200000 updates across
24 trajectories. Original scoring passes 240/240; controller checks independently
regenerate all paired inputs/initializations, verify optimizer counters and LR
traces, and reproduce 114 summary rows. All eight evidence items pass, including
explicit report-r1 review binding. The supplied science module is unchanged.
The three illustrative study summaries now exist, including the EMA figure.

Its 829100336-byte archive exposed an actual controller restore bug: combining
parts into a temporary file exceeded the unchanged 512 MiB file cap. Streamed
extraction now passes with all 901 declared manifest hashes and 272 reviewed
references verified. Preserve the failed job/manifest check and v2 resolution;
do not classify this transport defect as a candidate failure. The six transport
regressions include a real POSIX small-file-limit test and altered-part rejection.

r08 is terminal and its original EMA scorer also passes 240/240. Its package is
collected (16 parts, 525 regular files plus 22 external wheels, no manifest
errors), but source/statistical/visual/review and restoration checks remain.
Do not mark its package complete until those are inspected. Candidate:
`work/v03-evaluation/runs/r08/candidate`; controller: `evals/research-v0.3/runs/r08`.

The current native run is r09, handle 21363. Source freeze verification still
passes. No final release fix or push has occurred. Full remaining requirements,
MPS repair/canary, final-source conformance/acceptance and origin push still apply.

## Current postprocessing milestone

r07 now passes all eight evidence items, including 901 restored manifest entries
and 272 restored reviewed references. Its original failed restoration and failed
manifest check remain retained alongside the successful streaming correction.
The illustrative EMA summary and original figure are in `studies/ema-schedule/`.
`after-r07-reviewed` is the latest interim comparison: eight sessions terminal,
seven reviews complete, five packages fully verified. r08 review remains pending.

r08's original numerical score is 240/240 and its package is already collected.
No substantive completion claim has been made. Current active handle remains
**r09 / 21363**. Next r10, r11, r12. Check actual handles/processes before actions;
never restart from a stale state file or observation timeout. Keep the full goal
active through release fixes, final checks, commits and the authorized push.
