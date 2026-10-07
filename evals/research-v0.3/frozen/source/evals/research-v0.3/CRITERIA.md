# Evaluation criteria — candidate for freeze

Status: development. No final run may start until the freeze manifest covers
this document, scorers, task inputs, workflow, controller, resource profiles,
model/settings observations and the complete 12-run order.

## Design

Three fixed tasks × plain Codex or Codex plus Allagma × two fresh sessions per
condition produce 12 runs. Each task's common input hashes, scientific
requirements, package availability, tools and resource ceilings must match
across conditions and replicates. The Allagma condition adds the installed
locked workflow and an explicit invocation instruction. The baseline receives
the same computation broker and measurement interface; it is plain Codex under
common experimental instrumentation, not an uninstrumented interactive chat.

Run order is randomized in task/replicate blocks, with within-block condition
order counterbalanced. Runs execute serially on this Mac. Initial contexts do
not include other runs, development outputs, reference answers or evaluator
code. Underlying requested model, reasoning settings and CLI version must match;
record actual native observations. Backend revisions not exposed by the service
cannot be claimed controlled.
Each trial uses one agent session; nested model/subagent execution is disabled
in the common runtime. Scientific subprocesses remain available through the broker.

Each run starts from its initial brief. No task-specific follow-up instruction
is planned. A first marked scientific attempt receives a controlled interruption;
retain whether the interruption actually occurred and how the agent recovered.
Any later coordinator assistance, environment repair or changed ceiling is
recorded with its scope and timing. Agent self-corrections are not human
interventions. Do not exclude unsuccessful or noncompliant assigned runs from
the comparison. Infrastructure failures are separately identified and retained;
an invalid start does not substitute for a required fresh evaluation session.

## Correctness and scientific controls

Keep these dimensions separate rather than treating a zero process exit as a
scientific score:

| Task | Deterministic numerical checks | Required substantive controls |
| --- | --- | --- |
| CORE CULP | Exact original six-question CORE-Bench scoring function and references, unchanged | All three original scripts executed; source/data/scientific parameters preserved except documented portability edits; original label bug disclosed; no substitution of corrected CN/AA experiments |
| EMA schedule | 96 SW1 values, 48 GMM8 mode/count/inlier checks, 96 checkpoint sample replays; paired held-out/noise identity and required-cell coverage | Correct 2×2 duration/policy design, reference architecture/optimizer/sampling, training and initialization pairing, four independent confirmation seeds per dataset, pilot exclusion, seed-level contrasts/uncertainty and schedule-versus-duration interpretation |
| Modular addition | 32 endpoint metric checks, eight checkpoint/logit consistency checks; exact labels, partitions and curve coverage | Fixed architecture/optimizer/100k horizon, matching initial states/partitions across decay conditions, no held-out-label optimization or selection, four confirmation seeds, declared sustained thresholds, right-censoring and paired seed-level uncertainty |

The numerical scorer consumes data, not candidate evaluator code. Protocol,
training history and inferential claims also require source/trace review. Record
review findings with exact artifact/source locations. A numerical pass does not
prove that a declared training history happened. Same-model author critique or
controller review is provisional, not independent scientific peer review.

Scientific success does not depend on a favorable EMA effect, a grokking event,
statistical significance or Allagma outperforming the baseline. An honest
negative result can receive full correctness and completion credit.

## Evidence completeness

Score each item present-and-verified (1) or missing/insufficient (0), with a
supporting evidence reference and reason. Publish all eight items separately as
well as their sum; file existence alone is insufficient.

1. Question, source identity, exact inputs and relevant licenses are preserved.
2. Scientific protocol and analysis definitions precede confirmation; meaningful
   controls, pilot exclusions and stopping rules are explicit.
3. Required execution is supported by source/configuration snapshots, retained
   raw outputs, failed/interrupted attempts and authoritative process receipts.
4. Reported measurements independently recompute from raw evidence; required
   checkpoint/prediction or direct-execution checks pass.
5. Uncertainty uses the correct independent unit; censoring, multiplicity,
   source defects and negative findings are handled accurately.
6. English report and required figures/tables trace empirical claims to evidence
   and avoid unsupported generalization or novelty claims.
7. Environment locks, full reproduction and raw-only recomputation entry points
   are executable and documented; the artifact manifest's covered hashes match.
8. Substantive critique names actual findings, resolutions and remaining limits
   at the reviewed material revision, with assurance scoped to checks performed.

## Completion, interventions and resources

Completion is true only when the task's required package and science are actually
executed and verified within the declared scope. Report the agent's claimed
status separately from the controller's determination. A terminal failed run is
a valid comparison outcome, but it is not a complete research package.

Record planned interruptions separately from all subsequent assistance. Report
whether the agent recognized the authoritative prior outcome, preserved it and
used a new request/attempt. Allagma method activation/lock routing is an
additional treatment-compliance observation, not a baseline requirement.

For every run report compute/setup seconds, computational requests and failures,
native wall time, input/cached/output/reasoning token counts, measured RSS and
storage, and any ceiling or accounting violation. Explain watchdog sampling and
MPS-memory limitations. Controller validation work is a separate cost and does
not improve an agent's original outcome. No remote scientific compute, paid
experiment service, account reset or credit purchase is authorized by the run.

## Comparison and uncertainty

Publish all twelve outcomes and the six within-task/replicate contrasts. Compare
correctness, evidence completeness, completion, interventions and resource use
without selecting only successes. Report task-specific regressions and every
material failure. Two sessions per condition and three selected task families
cannot establish broad research superiority. Show within-task variability and
paired differences; qualify any interval's assumptions and population. Do not
pool repeated agent outputs as additional independent scientific seeds.

The task families were used during development; final sessions and confirmation
seeds are separate, but this is not evaluation on unseen task families. CULP is
a locally adapted selected CORE-Bench training task with a curated wheelhouse
and added evidence requirements, not a leaderboard run. These limits remain in
the comparison report regardless of outcome.

Post-evaluation fixes and repaired packages retain their own revisions and
assistance records. They never overwrite frozen comparison outcomes. Designate
the first fully verified Allagma package in run order for each task as the
illustrative package; if none qualifies, produce and label a separate repair.
