# Reference research and paper output implementation

The feature branch is `codex/reference-research-arxiv`. The full objective and
owner decisions are retained in [GOAL.md](../GOAL.md). Development began at
`694f13c1b923ff8e8a58442dd203baf613f76205`; the owner's subsequent main changes
through `2db830a9bb289ddd7e4cb454464cd5dd9d666b2c` were merged without altering
other contributor branches. The PR remains unmerged and deployment waits for merge.

The [completed-study demonstration](../studies/ema-schedule/publications/reference-r2/README.md)
links the eight-entry reference index, paper, portable source archive, exact
scientific inputs, reviews and validation receipts. The configured demonstration
author is `allagma`, explicitly selected by the owner. Other studies configure
their own attribution. No native model session, new scientific training campaign,
arXiv submission, formal release or feature deployment was performed.

## Requirement-by-requirement evidence

| Requirement | Authoritative evidence | Status |
| --- | --- | --- |
| Default reference research | New-study reference scaffold, scope/protocol/experiment/analysis/writing/context methods, generated entrypoint; `conformance/test_references.py` | Pass |
| Critical literature map | [Eight entries](../studies/ema-schedule/publications/reference-r2/references/map.json), seven full primary papers, exact code lineage, baselines, competing findings and stated gaps | Pass |
| Bibliography versus support | Separate metadata verification and located passage assessments, asset hashes, critical notes and generated BibTeX; strict checks reject unreviewed or unknown links | Pass |
| Continued use and resumption | Phase-specific consequences and decisions; concise index and notes; frozen preparation snapshot and instructions to recover it on resumption | Pass |
| Offline/provided-only operation | Explicit scaffold coverage limits, provided file import, new-process offline reuse of all 19 real assets, no transfer increase | Pass |
| Every supported asset type | Seven PDFs, seven available source archives, three commit-pinned repository files, a real saved model and a pinned evaluation split | Pass |
| Acquisition provenance | [Public-safe retrieval manifest](../studies/ema-schedule/publications/reference-r2/references/retrieval.json): versions, purpose, licenses, relative paths, hashes, sizes and status; explicit unavailable/gated cases | Pass |
| Git/worktree exclusion | Actual `info/exclude` rule; preserved entries and linked-worktree conformance; no tracked raw cache paths | Pass |
| Cache stays out of bundles/releases/Pages | Distribution guard, committed-source release test, tracked-media Pages filter and raw-cache marker checks | Pass |
| Configurable limits | Per-asset, expanded, per-study, total-cache, free-space, cumulative transfer, attempt, file-count and elapsed-time limits; bound decision required for expansion | Pass |
| Recovery and integrity | Loopback truncated-transfer resumption, retained reservations, interrupted extraction, offline reuse, corruption/quarantine/repair and budget failures | Pass |
| Immutable scientific inputs | Selective materialization, frozen hashes and [actual broker probe](../studies/ema-schedule/publications/reference-r2/evidence/reference-input-inspection.json): network, input writes and cache reads denied | Pass |
| Per-study optional paper | `paper.json`, protected author request and configurable named/anonymous attribution; report default starts no compiler | Pass |
| Complete English manuscript | Seven required sections, references and appendices; generated empirical values/tables, exact figure, scoped claims, negative/inconclusive findings and critical literature context | Pass |
| Humanizer and scientific review | Separate [revision-bound reviews](../studies/ema-schedule/publications/reference-r2/scientific-review.json), with a stale-review regression; same-assistant scope stated | Pass |
| Portable sources and template | 42-file archive includes TeX, BibTeX/bbl, exact figure, required custom style, standalone builder, notes and provenance; custom template interface | Pass |
| Clean compilation | Identical source archive compiled and recompiled after unpacking with network/cache access denied; local TeX Live 2024 and [supported TeX Live 2023 CI](https://github.com/alohays/allagma/actions/runs/37950653898) | Pass |
| PDF inspection | Eight pages inspected; table widths, pagination and metadata repaired; [digest-bound visual record](../studies/ema-schedule/publications/reference-r2/evidence/pdf-review.json), text/metadata/log checks | Pass |
| Offline core boundary | 151 conformance tests and complete I1–I5 acceptance, including the toy workflow; TeX and network acquisition are separate adapters | Pass |
| Preserve historical science/history | [Preservation audit](../studies/ema-schedule/publications/reference-r2/evidence/preservation.json); no old study, frozen evaluation, media or project-model-config changes | Pass |
| Real completed-study integration | r07 selected outputs match the frozen package index; 114 statistical summaries recomputed from retained seed measurements; no new training | Pass |
| Public documentation | Reference and paper guides, workspace/native/CLI guidance, study page and index; 43 pages, 2,809 checked links, 18 desktop/mobile browser tests | Pass |
| Commit/push/review handoff | Coherent commits, pushed feature branch and current-main merge; [regular, unmerged PR #14](https://github.com/alohays/allagma/pull/14) provides authoritative current-head CI | See PR checks |

## Resource and acquisition record

The initial inspection found 48 GiB unified RAM and about 59 GiB free disk on
this M4 Pro Mac. Adopted defaults are 256 MiB downloaded per asset, 512 MiB
expanded per asset, 1 GiB retained per study, 4 GiB per cache and 20 GiB minimum
free disk. Cumulative transfers are capped at 2 GiB per acquisition study, with
two attempts per asset identity, finite request/asset deadlines and an extraction
file-count limit. Lower limits are allowed; expansion and gated terms need an
explicit researcher decision. None was requested or accepted in this work.

The 19 selected assets transferred 139,596,456 bytes; extracted source files use
86,420,758 bytes. The cache reuses content by hash. Only two selected execution
assets are copied into protected study inputs. An initial Python TLS trust-store
failure is retained; the correction uses the existing OS CA bundle and preserves
certificate/hostname verification. Pin adoption reused existing bytes. A separate
preparation revision corrected the evaluation split description after actual NPZ
header inspection; both preparation records remain intact.

[Integration evidence](../studies/ema-schedule/publications/reference-r2/evidence/integration.json)
records unchanged transfer totals after process restart, input hashes and the
real broker probe. The local-only ledger retains failed/interrupted attempts and
budget reservations. Public manifests contain no authentication values or local
home-directory paths. A code asset may be selected repository files or a pinned
HTTP archive; acquisition does not execute code or accept provider terms.

## Validation and limits

[Validation results](../studies/ema-schedule/publications/reference-r2/evidence/validation-complete.json)
retain the offline acceptance, documentation/browser and compact-source release
checks. The production docs preview was inspected, including the new paper
preview and navigation to the reference index. Documentation fallback links now
bind to the build commit, so a PR preview can link to files before merge.

The final local PDF has SHA-256
`7aea0bb5cac8bd0a108a977aaf48c70cdd23cbbde5a08b97b4eed9c34d0c98ce`.
The portable source archive has SHA-256
`d3f64553bba07a9501a89ac75dbebf99a149c81eaca19d13e4958cbd3046b2b2`.
The same archive compiled under TeX Live 2023 in CI. Each environment reproduced
its own PDF bytes after unpacking; PDF bytes differ across TeX releases. A local
XeLaTeX smoke test also passed. No arXiv server processing or acceptance is claimed.

Deterministic checks prove recorded structure, byte integrity, declared links,
resource behavior and the actual boundaries they exercise. They do not establish
that a citation proves an assertion. The literature map is targeted, retrospective
and not exhaustive; the paper retains scientific uncertainty. Scientific and
humanizer reviews are same-assistant judgments, not independent peer review.
The new helpers and methods were not given a new native-model qualification run;
existing frozen qualification and model-usage limits remain unchanged.

## Review handoff

[PR #14](https://github.com/alohays/allagma/pull/14) is open as a regular review-ready PR against `main` and remains unmerged. The PR checks are the authoritative status for its latest head; the retained receipts bind earlier implementation checkpoints without a recursive evidence-only commit cycle. The final audit corrected terminal state reporting for failed or abandoned protected-input copies and tightened the minimum-free-space regression. Partial inputs and their reserved bytes remain retained.

The final boundary audit also verifies a complete provided-only paper with no external citations and an explicit References section. [Cache metadata evidence](../studies/ema-schedule/publications/reference-r2/evidence/cache-metadata-budget.json) reproduces and corrects an overrun caused by extraction manifests and indexes. Atomic metadata writes now obey cache/free-space admission. The final complete acceptance receipt is [retained separately](../studies/ema-schedule/publications/reference-r2/evidence/acceptance-complete.json); earlier checkpoints remain intact.
