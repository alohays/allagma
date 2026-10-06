# Offline conformance

Run `python3 -m unittest discover -s conformance -v`. The kit uses only Python's
standard library and temporary directories. It invokes actual bounded local
processes, injects failures and interruptions, and checks the resulting evidence.

| Suite | Coverage |
| --- | --- |
| `test_contracts` | Closed/versioned schemas, configuration provenance, capability narrowing, immutable references, path confinement and required context |
| `test_modules` | Portable metadata, role contracts, capability closure, lifecycle selection and one-module contribution |
| `test_versions` | Exact export, namespacing, central isolation, local variants, planned updates, conflicts, transactions, historical resume, rollback and scaffold migration |
| `test_research` | Complete toy workflow, recomputation, stale claims, manuscript revisions, budgets, retries and controller recovery |
| `test_worker` | Actual timeout and worker termination after controller death |
| `test_improvement` | Measured rejection versus an unevaluated backend failure, with retained candidate files |

The tests do not execute a hosted model. Host entrypoint fixtures establish
registration and artifact contracts, not native activation or model quality.
Study metrics are checked by the study-owned evaluator; method comparisons
measure their declared narrow fixture scope.

`python3 -m allagma acceptance --output build/acceptance` adds retained I1–I5
scenarios, artifacts, a per-test receipt and a source inventory. Existing output
directories are not overwritten. `tools/verify_external.py` optionally checks
the result with independently installed jsonschema and PyYAML; its requirements
are separate from the default runtime.
