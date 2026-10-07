# From a brief to a local research workspace

The v0.3 development interface prepares the same basic inputs used by the native
workflow: a research brief, supplied source materials and a finite resource
profile. It does not supply scientific hypotheses, runners, metrics or answers.
The fresh agent develops those within the brief, using the pinned Allagma methods.

Prepare an empty workspace and a separate controller directory:

```sh
python3 -m allagma research prepare --study /path/to/study \
  --control /path/to/study-control --id my-study \
  --brief /path/to/brief.md --materials /path/to/materials \
  --profile /path/to/resource-profile.json
```

Materials are copied to `inputs/materials/`; the brief, resource description and
common computation client are placed in `inputs/`. Include required offline
package wheels in the supplied materials. Links, credentials, nested output
locations, unbounded limits and an existing nonempty study are rejected. No model
session is launched by preparation. The controller directory retains the frozen
policy and authoritative receipts outside candidate access.

Explicitly launch a fresh native session using the installed compatible CLI:

```sh
python3 -m allagma research run --study /path/to/study \
  --control /path/to/study-control --session session-001 \
  --codex /absolute/path/to/codex --timeout 3600
```

This optional command currently targets macOS. It references existing Codex
authentication, preserves the selected user model in a temporary runtime home,
and writes no project model pins. Execution dispatches through the study's
pinned helper. Each session ID is new; prior sessions, computation requests and
scientific attempts are retained. Model wall time, RSS, workspace storage and
scientific compute are bounded separately. A CLI success means the native
session exited normally, not that its scientific claims passed review.

The native tools can inspect and edit the workspace. All setup and scientific
computation goes through the local broker. Its worker supports CPU/MPS while
denying network connections and writes outside the study. Read-only inputs and
generated methods remain protected. The resource client is infrastructure rather
than a scientific method. Record commands, inputs, source revisions and observed
outcomes; distinguish retries from new independent observations.

Use `research status --study ... --control ...` to inspect records. A missing
client response does not permit a retry: controller recovery checks the resource
receipt and live processes, then restores completion, retains abandonment with
the full reservation charged, or records that no process launched. A deliberately
requested interruption test is available with `--interrupt-first-attempt`.

The study's protocol declares its independent unit and scientific uncertainty.
`minimum_confirmation_runs` is a positive study-owned availability threshold;
the new helper defaults to one rather than imposing an uncertainty method.
Explicit `paired_seeds: true` allows conditions to share a seed when their run
entries have unique nonempty `condition_id` labels. It does not allow pilot seeds
to masquerade as untouched confirmation or make paired cells independent.

This interface is under v0.3 qualification. Native CORE-Bench development has
demonstrated the underlying brief-to-package workflow with no follow-up guidance;
the full controlled comparison and release audit remain pending. Existing v0.2
campaigns keep their original bundle helpers. Prepare a new v0.3 workspace or
adopt a compatible update at a campaign boundary; do not rewrite historical locks.

## Run a delivered reproduction command without another model session

A delivered study may use the common computation client in its reproduction
driver. Initialize a new, explicitly bounded resource ledger, then service the
driver through the local broker:

```sh
python3 -m allagma resource init --ledger /path/to/replay-control/resources \
  --profile /path/to/replay-profile.json --workdir /path/to/delivered-study
python3 adapters/local-process/broker.py --workspace /path/to/delivered-study \
  --ledger /path/to/replay-control/resources --record /path/to/replay-control/broker \
  --output /path/to/replay-control/driver-001 --timeout 600 \
  --readonly /path/to/delivered-study/inputs -- \
  python3 scripts/reproduce.py
```

Use the command declared by that study, not an assumed script name. The driver
coordinates requests while the controller services them; it is not launched
inside its own computation request. The driver and its scientific jobs retain
separate timings and outcomes. A newly created controller preserves but ignores
requests left by a different controller, preventing accidental replay. Reuse the
same controller record for an actual controller restart and inspect/reconcile
its existing resource receipts first.
