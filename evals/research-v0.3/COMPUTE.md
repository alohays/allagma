# Common local computation interface

This interface is identical for plain Codex and Codex plus Allagma. It supplies
resource supervision, isolation and observation, not a research workflow.

Use `python3 inputs/compute.py` from the workspace root. Put the command after
`--`, use a descriptive label, and request only the timeout needed:

```sh
python3 inputs/compute.py --category setup --label environment --timeout 60 -- python3 -m venv .venv
python3 inputs/compute.py --category setup --label packages --timeout 120 -- .venv/bin/python -m pip install --no-index --find-links inputs/wheels PACKAGE_NAMES
python3 inputs/compute.py --category compute --label first-run --timeout 60 --attempt -- .venv/bin/python your_runner.py
```

`--cwd relative/directory` runs inside a workspace subdirectory. A relative
executable is resolved from that directory; an absolute interpreter path inside
this workspace is often clearer. All commands run without network access and
cannot write outside the workspace or modify protected input/workflow files.
The worker supports CPU and MPS; direct native shell commands may not initialize
MPS. Python thread counts are one and the MPS allocation ratio is capped at 0.2.
Use only one scientific worker at a time and avoid nested parallel experiments.

The client prints the authoritative outcome and stdout/stderr. Convenience
copies are under `.compute/responses/`. The controller retains separate,
protected receipts and source snapshots. Every compute-category request counts
against the attempt cap, even if `--attempt` is omitted. Use `--attempt` to mark
the first substantive experiment for the scheduled interruption. Setup is
accounted separately. Checks, analysis, plots and recomputation are computation.

An interrupted or failed request is permanent history. Correct the cause and
submit a new request when appropriate; never overwrite or relabel the old one.
If the client reports `observation_timeout`, inspect that same request's
response and process state rather than automatically starting another job.
The controller will not repeat a request because its delivery file disappeared.
Do not inspect controller directories or attempt to access scoring answers.

Read `RESOURCES.json` for this run's ceiling and deadline. Reservations include
timeout, termination grace, polling and control overhead. Large timeout requests
can be rejected even when a shorter job would fit. A resource stop requires an
honest partial package. Do not expand the declared ceilings.
