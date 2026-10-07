# Research workflow evaluation (v0.3 development)

This directory is the evaluation controller's material. Candidate workspaces
will receive frozen task inputs, a common resource interface, and (only in the
Allagma condition) the frozen workflow. They must not receive development
outputs, reference answers, scorer code or another candidate's work.

The planned final design is three tasks, two conditions and two fresh sessions
per condition. No final runs have started. Development decisions and evidence
are in `development/`. A later freeze will enumerate exact inputs, scorers,
workflow source, resource ceilings, model/settings observations and run order.
Native sessions use the existing Codex account; scientific processes run only
on the local Mac. Final evaluation results are preserved even if later repaired
packages are needed for release.

The CORE-Bench preflight starts from the public training split at upstream
commit `e32a2980e72fe6eb04ee04eb749458f570625663`. A successful selected capsule
will retain its original task prompt, questions and numerical scoring rule.
This is a local evaluation of a selected task, not a CORE-Bench leaderboard run
or an estimate for the full benchmark.
