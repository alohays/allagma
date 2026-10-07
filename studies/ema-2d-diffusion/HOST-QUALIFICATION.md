# Native Codex qualification: weight EMA diffusion study

**Disclosure:** this report, study code, analyses and manuscript were
machine-generated with OpenAI Codex, using the pinned AI-Scientist reference.
Recorded experiments provide the measurements. This is not independent
scientific peer review.

Qualification is scoped to the recorded **Codex CLI 0.160.1, inherited
`gpt-6-astra` / `max`, macOS/M4 Pro environment and this study workflow**.
The [machine-checkable receipt](evidence/host-qualification.json) identifies
the exact traces and scope. It does not qualify every model, automatic skill
trigger, desktop UI interaction, or research problem.

## Environment and identity

The [host receipt](evidence/setup/host.json) records Apple M4 Pro, 48 GiB
unified memory (51,539,607,552 bytes), macOS on arm64 and Python 3.11.6.
The study owns its isolated `.venv`, [dependency lock](requirements.lock),
scientific programs and data. Actual runners report PyTorch 2.14.1, device
`mps`, and disabled CPU fallback. Metrics run on CPU in float64; training and
sampling run on MPS in float32. Python environment isolation is not an OS
security sandbox. Native CLI sessions used the authorized local
`danger-full-access` mode; bounded workers enforce attempt lifetimes.

The executable was the desktop app's bundled CLI:
`/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`.
The older shell-PATH CLI, version 0.151.0, returned an actual backend error
requiring a newer CLI for the inherited model. That failed launch is retained
in [session 01](evidence/native/01-interrupted/session.json) and its
[trace](evidence/native/01-interrupted/events.jsonl). No study execution occurred
there. Selecting the already installed compatible executable solved the issue.

[Model observations](evidence/native/model-observations.json) retain only
relevant non-secret fields from each native session's `turn_context`. Launch
arguments contain no model or reasoning override. No project `.codex` model
pin was added and the GUI selection was not changed. Existing ChatGPT CLI
authentication was used; credentials were neither copied nor committed.
Native token usage is in completed session receipts. Subscription/model usage
is separate from the study's local-computation clock; no monetary cost is
inferred from token counts.

The frozen framework bundle is `b-2b63431e34a085598aaade78`, with lock ID
`7287e278da3e264dc83704d42c334dd5845da048f59c9967343545fc4ec6c329` and source
revision `sha256:fe61419ac78231ab0fcc0d70f77714f6946cbdb1bd72ce3a360313850855e100`.
This is the audited Allagma source. The study did not need a framework-code
change. Scientific setup fixes addressed a parameter-count assertion,
floating-point comparison tolerance and unsupported MPS foreach gradient
clipping before pilot execution.

## Observed native behavior

| Native session | Actual behavior and evidence |
| --- | --- |
| [02: interruption](evidence/native/02-interrupted/session.json) | Read local protocol/experiment skill wrappers and canonical contracts, resolved the frozen campaign, ran 100 real MPS updates, retained the terminated attempt; then received SIGINT |
| [03: fresh continuation](evidence/native/03-fresh-pilots/session.json) | A distinct fresh thread recovered from campaign artifacts, verified 128 initial digests, preserved the interruption and completed four pilots; [continuation report](evidence/pilot-resumption-20261008/report.md) |
| [04: confirmation](evidence/native/04-confirmation/session.json) | Checked pilots and untouched seeds, wrote the confirmation freeze, completed ten trajectories serially and verified their evaluator outputs; [report](evidence/confirmation-20261008/report.md) |
| [05: analysis and critique](evidence/native/05-analysis/session.json) | Activated analysis/writing/audit methods; ran analysis, deterministic audit, independent verification and disclosed publication; identified reporting gaps in [its review](evidence/finalization-20261008/report.md) |
| [06: reporting revision](evidence/native/06-reporting-revision/session.json) | Correctly stopped on a supporting-verifier launcher import error and retained [failure evidence](evidence/reporting-revision-20261008/) |
| [07: reporting repair](evidence/native/07-reporting-repair/session.json) | Retried the repaired launcher, checked supporting diagnostics and the revised manuscript/claims; [repair review](evidence/reporting-repair-20261008/) |

Each directory contains the exact input prompt, JSONL command/tool events,
session ID, CLI version, exit status and transcript digest. The qualification
checker verifies successful wrapper reads, campaign-specific `entry` outputs,
canonical skill digests and the actual pinned helper paths. The explicitly
activated methods were protocol, experiment, analysis, writing and audit.
This establishes explicit invocation and subsequent method use, not implicit
trigger reliability. Reading/writing study artifacts and actual local execution
demonstrate the declared capability mapping.

The recovery sequence is deliberately precise: Allagma first terminated a
100-update pilot through its bounded interruption mechanism. The outer harness
then interrupted the native Codex process after the attempt and compute
receipt were durable. A new `codex exec` thread, without resumed conversation
history, read those artifacts and ran `pilot-moons-11-a002`. Attempt `a001`
remains `interrupted`, has no eligible raw output, and records
`scientific_evidence: false`. This does not claim that the native-host test
killed Codex in the middle of an unbounded training process; the separate
framework conformance suite tests controller-loss cleanup.

## Scientific and resource evidence

The [protocol](campaigns/ema-v1/protocol.json) freezes a 296,450-parameter
denoiser, batch 256, 100 diffusion steps, two datasets and paired raw/EMA0.99/
EMA0.999 evaluations at 5k and 10k. Four pilot trajectories completed before
the [confirmation freeze](confirmation-freeze.json). It binds their evidence,
scientific code, orchestration, ten new confirmation seeds and a 284.84-second
forecast against 1,699.63 seconds then remaining. All confirmation attempts
started after that receipt.

The complete plan contains **four successful pilots, ten successful
confirmation trajectories and one retained interrupted attempt**. No
confirmation retry was required. The analysis includes ten eligible raw
artifacts and excludes all four pilots and the interrupted attempt.

[The compute ledger](evidence/compute-summary.json) and individual receipts in
`evidence/compute/` retain every supervised scientific command, reservation,
actual duration, failure and timeout policy. The ceiling is 1,800 seconds,
with at most 18 training attempts and 150 seconds per attempt. A conservative
15.3-second charge for the earlier user-reported probe is included; it is not
scientific evidence. There are 15 training attempts. Installation, editing,
framework-only integrity checks and native model deliberation are outside
the scientific process wall-time clock. Native model session time is not
represented as GPU training time.

The first supporting-verifier launch failed before supervisor entry because
NumPy was imported under system Python. Its native failure trace is retained,
and [receipt 023](evidence/compute/023-supporting-startup-failure.json) charges
the full intended 47-second reservation conservatively; that charge is not a
measured duration. Scientific imports were moved into the isolated supervised
worker before the authorized retry. The final ledger therefore includes both
this conservative charge and the earlier probe estimate, alongside measured
scientific process durations.

The [campaign audit](campaigns/ema-v1/latest-audit.json) passed, checking 305
distinct transitive evidence references and regenerating the original
numerical analysis, figures, draft and eight initial claims. The
[primary independent verifier](evidence/independent-verification.json) checked
84 Sliced W1 values, 84 saved-weight state digests, 42 coverage results and
eight primary paired intervals. Twelve sample sets regenerated exactly from
saved weights for the first prespecified confirmation seed per dataset,
all variants and both checkpoints. Full training was not independently repeated.

The [supporting verifier](evidence/supporting-verification.json) separately
checks all 60 confirmation metric rows, 40 paired rows, ten independent
held-out controls, eight leave-one-seed-out ranges and eight supporting
mode/inlier intervals. This closes the first review's coverage concern; the
first verifier alone did not establish those supporting-diagnostic checks.
The [second publication](publication/v2/record.json) retains the earlier
publication, adds explicit Table 2 and checkpoint-pattern claim records, and
clarifies inferential limits. [All 13 claims](publication/v2/claims.json) link
their evidence. The final reporting revision has its own provenance and checks;
the original Allagma audit receipt applies to its original draft and records.

Both [figures were visually inspected](evidence/visual-review.json). All 75
framework conformance tests, six final scientific known-answer checks and four
budget-supervisor tests passed. Earlier setup failures are retained. A
[fresh replication skeleton](evidence/setup/reproduction-layout-delivery.json)
was created and verified without launching new training.
The [replication clarification](REPLICATION.md) explains that a new run receives
no inherited results and must interpret its own findings before reusing the
source study's reporting-specific revision.

## Delivery checks

The final ledger charges **324.560741 seconds of 1,800**
(about 5 minutes 25 seconds), leaving **1475.439259 seconds**.
That total includes the conservative startup and prior-probe charges described
above. The [technical completion checklist](evidence/completion-checklist.json)
maps the requested study requirements to inspected artifacts. Git delivery
and CI are verified against the remote repository separately.

## Interpretation and limits

The observed EMA advantage was concentrated at 5,000 updates. All four mean
comparisons favored EMA there; all four intervals at 10,000 updates included
zero. Mode counts were saturated at eight. Small seed counts, unadjusted
comparisons, finite sampling and the single learning-rate schedule limit
generalization. These are empirical findings for the declared study.

The native reviews are fresh-context critiques from the same model family.
They are not independent scientific peer review. The deterministic audit's
generic limitation about model-quality evaluation refers here to the host
language model's general research ability; the study does measure the declared
DDPM distribution-quality metrics. No claim is made for Claude Code activation,
other Codex versions/models, desktop UI behavior, implicit skill selection,
security isolation or broad autonomous research quality.

The native interface follows [official skill discovery documentation](https://learn.chatgpt.com/docs/build-skills)
and [Codex non-interactive JSONL mode](https://learn.chatgpt.com/docs/non-interactive-mode),
but qualification rests on the retained actual executions. See the
[manuscript](publication/v2/manuscript.md), [reproduction commands](README.md)
and [machine-checkable host receipt](evidence/host-qualification.json).
