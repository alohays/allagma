# Reference research and paper output implementation

This feature is developed on `codex/reference-research-arxiv`, starting from
`694f13c1b923ff8e8a58442dd203baf613f76205`. The complete owner objective is
retained in [GOAL.md](../GOAL.md). The branch will be pushed and opened as a
review-ready PR against `main`. Deployment waits for merge. Existing contributor
branches, historical science, locked bundles and attempts remain unchanged.

## Acceptance ledger

| Requirement | Evidence required | Status |
| --- | --- | --- |
| Default reference research | New-study scaffold, concise portable method, preparation and resume integration | Pending |
| Critical literature map | Deduplication; primary papers, implementations, baselines, competing findings and gaps; explicit search coverage | Pending |
| Bibliography and support | Verified metadata separately from located supporting passages, limitations and study consequences | Pending |
| Continued use | Planning, implementation, analysis, writing and resumed-session references with a concise index | Pending |
| Offline operation | Provided-only example and explicit coverage limits without network dependency | Pending |
| Retained reference assets | Real paper PDF, available TeX source, commit-pinned code, revision-pinned model and dataset/split | Pending |
| Acquisition provenance | Status, local resolution, hash, size, license, reason for selection and explicit unavailable states | Pending |
| Cache exclusion | Git-resolved info/exclude, preserved entries, linked worktrees, release and Pages exclusions | Pending |
| Bounded acquisition | Per-asset, per-study, cache and free-space limits; retries, interrupted transfer and expanded bytes | Pending |
| Cache integrity | Restart reuse, corruption detection, interrupted acquisition and deterministic failure checks | Pending |
| Immutable inputs | Preparation snapshots and integrity checks; scientific-worker network denial remains in force | Pending |
| Optional paper output | Per-study option and configurable attribution; existing report behavior remains the default | Pending |
| Complete manuscript | English sections, negative/inconclusive results, verified citations and claims/results/figures/table links | Pending |
| Portable sources | Configurable template, TeX/BibTeX/bbl, figures, required styles, instructions and provenance | Pending |
| Clean build | Unpack archive and compile without reference cache or network; inspect every PDF page | Pending |
| Integration boundary | Network acquisition and TeX are optional integrations; core conformance remains offline and standard-library-only | Pending |
| Completed-study demonstration | New manuscript revision using retained science without altering its records | Pending |
| Documentation and delivery | Public guides, configuration, migration, limitations, tests, coherent commits, pushed PR, runnable commands | Pending |

## Resource decision

The initial inspection found 48 GiB unified RAM and approximately 59 GiB free
on this M4 Pro Mac. Adopt conservative initial defaults: 256 MiB downloaded per
asset, 512 MiB expanded per asset, 1 GiB retained per study, 4 GiB total per cache,
and at least 20 GiB disk space remaining. Transfer accounting will include
retries, with a 2 GiB cumulative transfer ceiling per study and two attempts per
asset. Extraction also limits file count. No new model sessions or scientific
training are required for this feature's demonstration. Limits may be lowered;
raising adopted limits or accepting gated terms requires an explicit researcher
decision retained in the acquisition policy.

## Implementation sequence

1. Add the offline literature records, index, validation and default methods.
2. Add bounded acquisition, cache exclusion, recovery and immutable preparation.
3. Add optional paper configuration, evidence validation and portable TeX build.
4. Retain real references, write a new completed-study manuscript revision,
   inspect its PDF, and verify clean compilation and cache behavior.
5. Complete public documentation, full relevant checks and preservation audit;
   push and open the PR with exact-head validation.

Deterministic record checks establish structural integrity and traceability.
They do not establish that a passage proves a scientific claim or that a paper
will be accepted by arXiv. The demonstration will retain a separate critical
reading and manuscript review.
