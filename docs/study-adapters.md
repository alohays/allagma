# Study-owned program interfaces

The toy study is an executable example. To connect a different computational
study, supply `brief.json`, `protocol.json` and the programs declared by that
protocol. Use `examples/toy-study/` as a small reference, keeping your scientific
logic outside the Allagma bundle.

`protocol.json` contains a revision, hypothesis, uncertainty method, finite
`runs` list, `max_failures_per_run`, program paths and `code` list. Each run has
a unique safe ID, a split (`pilot`, `confirmation`, `discovery`) and JSON input
with an explicit integer seed. The declared `code` list includes every local
program, import, source document and configuration file needed by the study.
At campaign creation those files are copied under `materials/` and hashed.

| Program | Command arguments after the Python script | Output |
| --- | --- | --- |
| Runner | `INPUT_JSON RAW_JSON` | Exact raw observations in the supplied new file |
| Evaluator | `INPUT_JSON RAW_JSON EVALUATION_JSON` | JSON with `valid: true` only when the declared scientific checks pass |
| Analyzer | `STUDY_ROOT RAW_MANIFEST_JSON OUTPUT_DIRECTORY` | Deterministic, recomputable JSON/CSV analysis files |
| Writer | `STUDY_ROOT ANALYSIS_RECORD_JSON OUTPUT_DIRECTORY` | `claims.json` containing ClaimRecords, and `manuscript.md` |

The helper invokes argument arrays without a shell. Runner/evaluator stdout and
stderr are retained, as are commands and worker receipts. The evaluator is
separate from the runner. The toy evaluator checks seeded data, arithmetic and
known-answer controls; another study must supply its own appropriate checks.

The toy runner recognizes deliberate `fault` inputs for the conformance
walkthrough. `failure` raises before producing observations. `interrupt` writes
an `interrupt-ready` checkpoint and waits; the adapter then terminates it. These
are execution fault fixtures, not scientific measurements. Normal retries use
the original frozen inputs with a new attempt ID.

Analysis defaults to a complete run plan. `--allow-partial` permits an explicitly
limited package when at least two eligible confirmation observations exist.
The analysis and manuscript must identify this limitation. A budget stop with
too little evidence still writes a partial execution report. Never invent a
statistical result to fill an incomplete package.

Use a new `--analysis-id` for a changed analysis. The same identifier cannot
overwrite an earlier record. Review histories similarly retain each verdict
and its exact material revision. External reviewer adapters can implement the
same handoff later; a same-model-family fresh-context review is provisional.
