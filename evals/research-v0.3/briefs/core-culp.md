# Computational reproduction of CULP

Reproduce the supplied CULP research capsule locally, answer its original task
questions, and deliver a critically reviewed, reproducible English research
package. Read `task.txt` for the exact original task and question keys. The
capsule's scientific requirements and original scoring must remain intact.

Plan and implement the workflow yourself from this brief and the supplied
materials. Install an isolated environment, execute all three required scripts,
retain original and adapted source provenance, inspect outputs, critically
review the methods and interpretation, and verify the reported answers against
actual execution. Platform compatibility edits are allowed when documented;
changing scientific parameters, dataset partitions or algorithms to obtain
preferred answers is not. An upstream code limitation should be preserved and
explained. No original outputs or reference answers are provided.

Read `COMPUTE.md` and `RESOURCES.json` before execution. All environment setup and
scientific computation must use the common local computation client. Source
inspection, editing, bookkeeping and reading outputs may use ordinary shell
tools. The first marked scientific attempt will receive a controlled
interruption. Preserve that attempt and recover within the same ceilings. Do
not treat an observation timeout as evidence that a job stopped. No human
follow-up guidance is planned, and network access is unavailable.

Keep code and evidence in this workspace. Copy the read-only capsule into a
working directory before adapting it. The wheelhouse contains locally available
Python packages; infer needed dependencies from the source and record the
versions actually used. Scientific workloads run on this Mac only. Model usage
is accounted separately by the controller.

Deliver `report.json` with the exact original question strings and your answers;
an English `REPORT.md` with methods, results, source limitations and evidence
links; `review.json` documenting concrete checks, findings and resolutions at
the reviewed source/artifact revision; and `REPRODUCE.md` with commands for a
fresh environment, full execution and result recomputation. Keep raw stdout,
stderr, inputs, source revisions and failure/retry history. Produce an
`artifact-manifest.json` with relative file paths and SHA-256 hashes, excluding
environment caches and transient queue files.

Finally write `submission.json` containing `task_id: "core-culp"`,
`execution_status` (`complete`, `partial` or `blocked`), `report`, `manuscript`,
`review` and `artifact_manifest` (relative paths), and `reproduce` and `recompute`
objects, each with an `argv` string array and relative `cwd`. Reproduce must
cover fresh environment setup and all required code execution; recompute must
derive reported numbers from retained raw evidence without training or rerunning
the source experiments. State exactly what each check establishes. A CLI exit
code or finished document is not scientific verification. Report any unmet
requirement or budget stop honestly rather than claiming completion.
