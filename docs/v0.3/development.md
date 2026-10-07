# Development evidence and decisions

The acceptance ledger is [requirements.md](requirements.md). Nothing in this
development log counts as a final comparison run.

## Reusable resource supervision

The completed EMA study's `compute.py` demonstrated serial timeout reservations,
conservative crash accounting and separate model-deliberation cost. Its budget,
attempt count, working directory and initial charge are hard-coded. Its native
reporting repair also exposed the need to run dependency-using verification in
the study environment. These observed needs motivate a study-independent local
resource supervisor; scientific hypotheses and evaluators remain study-owned.

The new `allagma resource` helper freezes a supplied finite profile, retains
immutable reservations and separate outcomes, charges uncertain work fully,
refuses automatic restart of unresolved work, and distinguishes compute from
environment setup. It adds process-tree RSS and study-storage watchdogs plus a
per-file kernel limit. RSS is not exact MPS allocation accounting. Polling may
overshoot a threshold; this is operational resource control, not adversarial
containment. Evaluation isolation is a separate requirement.

Actual conformance probes initially exposed a macOS host restriction on process
group signaling. Direct signaling of observed, identity-checked child processes
works on this host. The supervisor now uses that path as well; it does not leave
a timed-out child running after declaring termination. Launch uncertainty keeps
the reservation charged until explicit recovery.

## Initial development ceiling

The [development profile](../../evals/research-v0.3/development/resource-profile.json)
allows 1,800 seconds of scientific computation and 900 seconds of environment
setup, at most 24 computational attempts, 180 seconds per computational command,
8 GiB observed process RSS, 6 GiB workspace storage and 512 MiB per file. The
polling interval is 0.25 seconds with a 0.5-second termination grace. This is a
development envelope, not an inherited final-evaluation budget. Final task
ceilings will be chosen from observed pilots and frozen before evaluation.

## External task preflight

The public CORE-Bench training metadata and four capsule HTTP manifests were
inspected. Two CPU candidates were downloaded for source/environment preflight:
BorderT-GRAANK (`capsule-2011424`, 246,776 compressed bytes) and CULP
(`capsule-6460826`, 13,752 compressed bytes). Archives were checked for unsafe
paths, special files, links and an expanded-size ceiling before extraction.
No original scientific run has yet been declared compatible. Original results
are excluded from candidate input packages. Legacy container dependency pins
need local compatibility checks; changing an API import or data path must be
disclosed and must not change scientific parameters or scoring.

Sources: [CORE-Bench](https://github.com/siegelz/core-bench),
[native Codex execution](https://learn.chatgpt.com/docs/non-interactive-mode),
[skill evaluation guidance](https://developers.openai.com/blog/eval-skills).

## Resource recovery correction from real setup

The first isolated Torch environment setup completed with exit code zero but
the supervisor labeled it `orphaned_children`. A process snapshot taken before
the root exited could still include an already-finished installer child. The
fix excludes zombies and obtains a fresh process snapshot after observing root
exit. Twelve resource tests now pass, including normal nested-process exit and
termination of an actually live detached descendant. The original setup receipt
is preserved. This correction does not relabel its historical outcome.

## CULP compatibility established

The initial CULP invocation timed out at 30 seconds during its first environment
use. A separate bounded import diagnostic captured the interpreter inside a
scikit-learn extension import. A fresh attempt with a 45-second per-script
timeout completed all three original scripts in about four seconds overall.
The exact upstream scoring function, original reference answers and unchanged
question strings gave **6/6 correct answers**. Only the Wine/Zoo absolute
container paths were adapted to capsule-relative data paths; algorithms,
dataset partitions, parameters and scoring tolerances were unchanged.

CULP is selected for the external task. The original source has a scientific
reporting caveat: Iris and Zoo loop over predictor labels but always call the
CS predictor. Preserving the source task means retaining this behavior and
disclosing it, rather than silently fixing it or treating its labels as proof
that CN and AA were actually compared. The preflight is a local compatibility
result, not a leaderboard score or final evaluation run.

## Complete native brief-to-package development run

`development/sessions/dev-core-01/` under the evaluation directory retains a
fresh `gpt-6-astra` / `max` session using existing authentication and the locked
Allagma recipe. It received only the initial brief, source capsule, wheelhouse
and finite resource description. There were **zero subsequent coordinator
messages or edits to candidate work**. The session independently identified the
printed-label defect, implemented study-owned execution and verification,
recovered the deliberate interruption, preserved a failed cold-environment
check, repaired its verification timeout within the existing ceiling, and
delivered reports, records, reproduction and recomputation entry points.

The native session took 1,738.77 seconds. Its recorded usage is 2,409,916 input
tokens (2,313,600 cached), 32,236 output tokens and 8,127 reasoning-output tokens.
These counts are separate from scientific computation. The unchanged upstream
scorer independently accepts all six answers. All 365 files in the candidate's
manifest were hash-verified before retention in `candidate-package.tar.gz`.
Its own substantive checks and author critique are accurately labeled; this is
not independent scientific peer review or a final comparison run.

The run exposed a shared-helper assumption: `analyze_campaign` required two
confirmation records even for a fixed single-case reproduction. The agent
correctly used the portable contracts without inventing replicates. The source
helper now accepts a positive study-owned `minimum_confirmation_runs` (default
one), and the toy protocol explicitly retains its minimum of two. A single-case
fixture executes analysis and audit successfully. Explicit paired-condition
seed reuse is also supported without weakening pilot/confirmation separation.

Repeated input preparation motivated the generic `research prepare/run/status`
interface, described in [research workspaces](../research-workspaces.md). A
standalone broker driver supports delivered reproduction commands without
starting another model session. Its actual macOS process integration check
passes. These changes are still under qualification; the final workflow and
evaluation criteria have not been frozen.
