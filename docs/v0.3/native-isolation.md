# Native evaluation isolation and qualification

Subsequent qualification found an [MPS allocator configuration defect](defects.md)
in the broker environment prefix. The sandbox canary below remains valid for
its tested profile; it does not establish that the complete frozen broker can
initialize MPS with its high-watermark setting. The defect and its native
failure are retained. The [corrected full-broker regression](../../evals/research-v0.3/validation/mps-broker-rc2/validation.json)
now passes actual MPS work and access denials. It is distinct from the earlier
sandbox-only canary and from native-agent qualification.

These checks were performed before the final comparison. They validate parts
of the evaluation infrastructure; they do not by themselves establish
research-workflow quality. Current native outcomes are recorded in the
[acceptance ledger](requirements.md).

The Codex adapter uses CLI 0.160.1 with the existing authenticated account. It
copies only selected model controls from the user's current configuration into
a separate temporary runtime home. It does not write project model overrides,
import old chat history, enable personal plugins, or supply task answers. The
recorded actual model is `gpt-6-astra` with `max` effort. Personal/global skills
are disabled for these controlled sessions. Candidate-local Allagma methods
were supplied only in the Allagma condition.

Three native launch attempts are retained under
`evals/research-v0.3/development/native-isolation-*`. The first failed during
path canonicalization. The second started a real session but nested macOS
sandboxes prevented command execution. Its CLI exited zero while the task
remained unperformed, demonstrating why process completion is not a task score.
The third used the CLI's native permission profile and completed an actual
Python canary: allowed input read passed, input overwrite was denied, and a
controller-only answer file could not be read. Its first shell heredoc failed
because the profile denied temporary files; the agent independently used a
direct Python invocation. The current adapter gives each workspace its own
temporary directory. All three attempts remain part of development history.

The native permission profile could not initialize MPS, including after an
explicit system-library read experiment. A separate computation-worker profile
then passed actual MPS forward/backward known-answer checks while denying input
modification, reference-answer reads and writes, symlink access to the answer,
and network connections. This worker uses a macOS sandbox with local GPU access,
controller-owned resource supervision and workspace-only writes. Its initial
probe allowed read-only access to the existing isolated development environment;
final candidates must set up their own environment inside their workspace.

`adapters/local-process/broker.py` services requests from the common
`compute_client.py`. The same instrumentation was present in both comparison
conditions. It records requests, source snapshots, resource receipts and logs
outside the candidate workspace. A real process integration check timed out
the first attempt, retained it, and successfully executed a new request. This
is an actual process test, not a native-agent recovery qualification. Offline
broker contract tests use explicit mocks and are labeled accordingly.

A complete native CORE brief-to-package development run and controller restart
reconciliation were qualified before freezing. Common inputs, workflow, scorer,
ceilings and intervention rules are now frozen; protected-material checks pass
for the inspected native sessions. The [12-run evaluation is complete](COMPARISON.md).
A complete CORE study execution and raw recomputation from a clean Git checkout
have passed; this does not establish an untested second training replay for
the other two task families. Separately, r12 actually repeated its entire EMA
training in a fresh environment; this is distinct from a new Git clone.

Official references: [permission profiles](https://learn.chatgpt.com/docs/permissions),
[disabling personal skills](https://learn.chatgpt.com/docs/build-skills), and
[non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode).
