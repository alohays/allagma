# Offline conformance

Run `python3 -m unittest discover -s conformance -v`. The kit uses only Python's
standard library and temporary directories. It invokes actual bounded local
processes, injects failures and interruptions, and checks the resulting evidence.
The optional acquisition integration cases use an installed Git executable and
loopback HTTP, without external network access; they are skipped when Git is
unavailable. No TeX installation or third-party Python package is needed for
this command. Actual TeX compilation has its own optional CI workflow.

| Suite | Coverage |
| --- | --- |
| `test_contracts` | Closed/versioned schemas, configuration provenance, capability narrowing, immutable references, path confinement and required context |
| `test_record_validation` | Public CLI rejection without writes or tracebacks, malformed record roots, attempt outcome consistency and supported-claim evidence requirements |
| `test_modules` | Portable metadata, role contracts, capability closure, lifecycle selection and one-module contribution |
| `test_versions` | Exact export, namespacing, central isolation, local variants, planned updates, conflicts, transactions, historical resume, rollback and scaffold migration |
| `test_research` | Complete toy workflow, recomputation, stale claims, manuscript revisions, budgets, retries and controller recovery |
| `test_worker` | Actual timeout and worker termination after controller death |
| `test_improvement` | Measured rejection versus an unevaluated backend failure, with retained candidate files |
| `test_references` | Critical map identity, metadata/support separation, snapshots, source links and cache boundaries |
| `test_reference_assets` | Optional Git/worktree exclusions, bounded transfers/extraction, restart reuse, corruption and immutable preparation |
| `test_papers` | Report default, configurable attribution, evidence/citation links, review freshness and portable source assembly without TeX |

The tests do not execute a hosted model. Host entrypoint fixtures establish
registration and artifact contracts, not native activation or model quality.
Study metrics are checked by the study-owned evaluator; method comparisons
measure their declared narrow fixture scope.

`python3 -m allagma acceptance --output build/acceptance` adds retained I1–I5
scenarios, artifacts, a per-test receipt and a source inventory. Existing output
directories are not overwritten. `tools/verify_external.py` optionally checks
the result with independently installed jsonschema and PyYAML; its requirements
are separate from the default runtime.
