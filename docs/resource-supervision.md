# Local resource supervision (v0.3 development)

`allagma resource` runs study-owned commands under a finite, frozen resource
profile. It contains no scientific model, metric, training loop or result
criterion. Existing v0.2 campaign budgets and historical bundle helpers keep
their original behavior. A study may wrap environment setup, campaigns and
independent analysis with this additional supervisor.

Create a profile using the [development example](../evals/research-v0.3/development/resource-profile.json),
then initialize a new ledger and launch a command:

```sh
python3 -m allagma resource init --ledger /path/to/ledger \
  --profile /path/to/profile.json --workdir /path/to/study
python3 -m allagma resource run --ledger /path/to/ledger \
  --category compute --label pilot-01 --timeout 120 --attempt -- \
  .venv/bin/python domain/runner.py inputs.json outputs.json
python3 -m allagma resource status --ledger /path/to/ledger
```

Categories have separate cumulative wall-time ceilings and per-command timeouts.
For `resource run`, `--workdir` may select a subdirectory of the budgeted study;
storage accounting still covers the entire frozen work directory. A path that
escapes that directory is rejected.
Use a separate setup category for dependency installation. Charge scientific
checks, training, sampling, analysis and recomputation to compute. Record Codex
tokens and account usage separately; an agent's entire deliberation time is not
scientific computation. `--attempt` counts a bounded computational job, not a
statistical replicate. The study must also enforce any scientific run/seed cap.

Before launch, the supervisor reserves the timeout, termination grace, polling
interval and four seconds of control overhead. Completed outcomes charge actual
elapsed time; a missing outcome charges the whole reservation. Jobs use distinct
directories with immutable `reservation.json`, `process.json` and `result.json`
files and retained stdout/stderr. Nonzero commands and interrupted attempts are
preserved. A concurrent operation or unresolved reservation prevents new work.

After a supervisor crash, inspect the recorded process and outputs. Do not
restart because a wait timed out. `resource recover --ledger /path/to/ledger`
refuses recovery when the recorded process group is still live. Once the work
is confirmed stopped, it retains an abandoned outcome charged at the full
reservation. It never fabricates scientific completion or restores budget for
unmeasured work. To adopt a changed ceiling, obtain the required authorization
and create a new, explicitly linked policy; do not edit an existing ledger.

The helper requires POSIX, `ps`, Python 3.11+ and a main-thread invocation. It
monitors sampled process-tree RSS and logical regular-file bytes inside the
work directory without following symlinks. An OS per-file size limit bounds
individual child writes. It terminates the process group and observed
descendants, including identity-checked individual signals where macOS rejects
group signals. Time, RSS and storage watchdogs have polling and termination
overshoot. RSS omits some GPU allocations; studies using MPS need a separate
device-allocation limit. Unobserved detached descendants and writes outside the
work directory require host isolation. This helper is not an adversarial
sandbox, a filesystem quota, or a guarantee of instantaneous hard limits.

The evaluation controller must keep the policy, ledger and scorer outside
candidate-writable paths. A study-owned ledger alone cannot prove resistance to
candidate tampering. Deterministic process tests cover failure/retry history,
timeout, RSS and storage termination, per-file limits, missing-outcome charging,
live-job recovery refusal, budget reservation, profile validation and CLI argv.
