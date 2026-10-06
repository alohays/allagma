# Evidence contracts

Every record carries `schema_version: "0.2"` and a `record_type`. JSON Schema
documents are in `contracts/`. Records are closed: missing fields, unknown
fields, incompatible versions, nonfinite numbers and invalid statuses fail.

| Record | Meaning |
| --- | --- |
| StudySpec | Question, resources, constraints, release lock, profile and configuration origins, frozen protocol |
| ExperimentSpec | Hypothesis, exact inputs, runner/evaluator digests, seeds, budget, expected artifacts and edit boundaries |
| RunRecord | Run/attempt identity, times, commands, environment, model/data revision, usage, status, errors and exact artifact references |
| AnalysisRecord | Raw manifest, code/configuration, outputs, exclusions, dependencies and uncertainty |
| ClaimRecord | Text, supporting/contradicting evidence, dependency closure, scope, limitations and current interpretation |
| ReviewRecord | Backend, exact material revision, criteria, verdict, findings, trace and assurance coverage |
| ImprovementRecord | Target, hypothesis, lineage, baseline/candidate, controlled comparison, outcome, cost and release decision |
| ContextRecord | Required/selected/omitted IDs, actual context content and limitations |

Artifact references contain a study-relative path, SHA-256 digest, media type
and retention policy. Paths cannot escape the study or traverse symlinks.
This release uses `retain-with-study`: retain all referenced small evidence and
bundles. Large-data stores need an explicit storage adapter and retention policy;
they are not silently substituted by this implementation.

`python3 -m allagma validate-record PATH` checks a record. `campaign audit`
checks transitive evidence and reproduction. Schema validation alone cannot
establish the meaning or scientific validity of a result.

Configuration files named `.yaml` use the JSON subset of YAML. This keeps the
default runtime dependency-free and avoids implicit YAML scalar coercions.
Use double-quoted keys/strings and no YAML-only comments or tags.

The built-in validator implements exactly the JSON Schema vocabulary used by
the supplied draft-2020-12 schemas: objects/properties/required/additional
properties, arrays/items/length/uniqueness, primitive types, enum/const, numeric
bounds, string length/pattern, timestamp format, internal `$defs` references,
`anyOf` and `oneOf`. Unsupported validation keywords fail closed. It is not a
general-purpose JSON Schema implementation. The release checks also exercise
these schemas with an independent validator when available; that validator is
not a runtime dependency. Cross-record semantic checks remain in the helpers.

Earlier and future schema versions are rejected until an explicit migration
exists. Migration emits new records and references; it must not rewrite raw
attempts or re-label old evidence as new results.
