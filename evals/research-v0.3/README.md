# Research workflow evaluation (v0.3)

This directory is the evaluation controller's material. Candidate workspaces
receive frozen task inputs, a common resource interface, and (only in the
Allagma condition) the frozen workflow. They must not receive development
outputs, reference answers, scorer code or another candidate's work.

The frozen design is three tasks, two conditions and two fresh sessions per
condition. Development decisions and evidence are in `development/`. The
`frozen/freeze.json` manifest enumerates exact inputs, scorers, workflow source,
resource ceilings, model/settings observations and run order. Current progress
is in `progress.json`; terminal outcomes and complete traces are in `runs/`.
Four sessions are terminal and three original packages are fully verified at
the latest milestone. The remaining eight sessions and release audit are pending.
Native sessions use the existing Codex account; scientific processes run only
on the local Mac. Final evaluation results are preserved even if later repaired
packages are needed for release.

The selected CORE-Bench task is CULP capsule `capsule-6460826`, from the public
training split at commit `e32a2980e72fe6eb04ee04eb749458f570625663`. It retains
its original task prompt, questions and numerical scoring rule.
This is a local evaluation of a selected task, not a CORE-Bench leaderboard run
or an estimate for the full benchmark.

Keep the original scorer outcomes, any documented compatibility correction and
the substantive evidence review separate. `summarize.py` aggregates these
receipts without treating a native process exit as scientific completion.
See [defects found after freezing](../../docs/v0.3/defects.md) for the shared MPS
configuration problem and inline-curve parser correction. The comparison cannot
measure the performance of a subsequently repaired GPU path.

The [retention procedure](RETENTION.md) preserves original scientific artifacts,
terminal requests/receipts and exact dependency identities. Archive supplements
repair transport omissions; they do not change candidate outcomes. Package
restoration, deterministic checks, substantive controller review and full
scientific reproduction establish different kinds of evidence and remain
separately labeled.
