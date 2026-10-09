# Reference research for a study

Every new Allagma study includes `references/map.json` and a short
`references/INDEX.md`. Scoping starts with this dossier. The protocol, scientific
implementation, analysis and manuscript use its located passages and recorded
decisions. On resumption, read the index and unresolved coverage limits, then
open the relevant notes and retained sources.

The default scaffold uses `provided-only` coverage. It does not silently search
the web or claim that the supplied sources represent the field. Change the mode
to `online` when recording an actual search, or `offline` when working from an
existing local collection. Record exact queries, sources, dates, selection
rationale and coverage limits. Assess primary papers, implementations, baselines,
competing findings and gaps separately.

```sh
python3 -m allagma reference init --directory /path/to/references \
  --question 'Which finding is this study testing?' --mode provided-only
python3 -m allagma reference add --directory /path/to/references \
  --record /path/to/one-reference.json
python3 -m allagma reference check --directory /path/to/references --require-review
python3 -m allagma reference snapshot --directory /path/to/references \
  --destination /path/to/new-reference-revision --require-review
```

`init` is for a new dossier; a newly initialized study already has one. Editing
the study-owned map and notes is supported. `index` regenerates the index and
`citations.bib`. `add` merges matching identities while preserving the existing
citation key. Conflicting metadata requires explicit resolution. A DOI or arXiv
identity matches across URL spellings or paper versions; different versions
still require a deliberate choice of which bytes were read.
Title matching also includes the first author and year, so unrelated works with
the same title remain distinct. Ambiguous matches require critical review.

## Record a critical reading

Each record has an `id` used as its citation key, `metadata` (title, authors,
year, URL and available identifiers), `roles`, `relevance`, `limitations`, and
`consequences` for planning, implementation, analysis and writing. Store longer
reading notes at the record's relative `note` path. Keep the index concise.

`bibliography.status` is `unverified`, `verified` or `conflict`. A verified entry
records when and where the title, authors and year were checked against primary
sources. Only verified entries enter the generated BibTeX. Verification is a
recorded researcher/agent judgment; a deterministic check cannot establish that
the source was interpreted correctly.

Each `passages` entry records a stable ID, source URL, page/section/code locator,
summary, claim, support assessment and limitation. Assessments are `supports`,
`contradicts`, `context` or `unassessed`. When a source asset is retained, include
its `asset_id` and SHA-256; the checker compares these with `retrieval.json`.
Use short permitted quotations or paraphrase. A correct title and DOI do not
show that a cited passage supports the claim.

The map's `decisions` link a phase and concrete choice to passage IDs such as
`Ho2020:training`. Record why a baseline was chosen, an implementation was
adapted, an analysis differs from prior work, or a claim needs narrower wording.
Keep competing findings and differences in methods or measurement visible.

`--require-review` rejects unverified metadata and unassessed passages. An empty
provided-only map may pass when its limitations are explicit and no category is
marked covered. This permits known-answer derivations and genuinely unavailable
literature without inventing citations. The output states that the check covers
record consistency, not independent scientific review.

## Versioned reading inputs

A snapshot copies only the selected notes, map, generated index/BibTeX and public
asset/retrieval manifests. It records their hashes and never traverses a raw
download cache. Snapshots use new destinations and cannot overwrite a prior
revision. Later reading belongs in the working dossier or a new snapshot.
Existing studies and frozen bundles keep their original methods until an
explicit compatible update is adopted. No migration rewrites historical science.

## Retain selected assets

Write `assets.json` in the dossier with format `allagma-reference-assets-v1`, a
stable `study_id`, and an `assets` list. Each asset records `id`, `kind`
(`paper-pdf`, `paper-source`, `code`, `model`, or `dataset`), public `url`, pinned
`revision`, `purpose`, `use` (`reading` or `execution`), `access`, and `license`
with a name, source URL and permitted-use note. Add known `sha256` and
`size_bytes` pins. Code, model and dataset revisions must be immutable hexadecimal
commit/revision IDs, bound through the URL or expected hash. Datasets also name
their selected `split`. Set `extract` to `tar` or `zip` only when the archive's
contents are needed; otherwise leave it `none`.

```sh
python3 -m allagma reference cache-init --directory /path/to/references \
  --cache /path/to/git-checkout/.allagma-reference-cache
python3 -m allagma reference acquire --directory /path/to/references \
  --cache /path/to/git-checkout/.allagma-reference-cache --online
python3 -m allagma reference verify-cache --directory /path/to/references \
  --cache /path/to/git-checkout/.allagma-reference-cache
```

For supplied files, replace `--online` with `--provided /path/to/local-bindings.json`.
The binding JSON maps each asset ID to a local file path and stays private.
Repeat `acquire` without either flag to reuse intact cached objects offline.
Unavailable or gated assets retain their explicit states and reasons; partial
success returns exit code 1. No request is made without `--online`.

The [acquisition adapter](../adapters/reference-assets/README.md) documents limits,
resumption, terms decisions and corruption handling. Defaults reserve 20 GiB free
disk and cap an asset at 256 MiB, expanded bytes at 512 MiB, a study at 1 GiB and
the cache at 4 GiB. Two attempts and 2 GiB cumulative transfers per study include
failed and repeated bytes. These defaults were chosen conservatively for the
development Mac's measured disk space; RAM is not permission to fill the disk.

Raw assets live under an excluded cache. Initialization resolves Git's actual
`info/exclude` and preserves existing entries, including in linked worktrees.
The exclusion is local configuration, not a tracked `.gitignore` edit. Version
the index, notes, citations, `assets.json` and public-safe `retrieval.json`.
Retrieval paths are relative to the cache and contain no home directory or
authentication data. Source-release packaging rejects force-tracked cache
markers; Pages copies only reviewed, tracked media and rejects raw cache images.

Pass `--references /path/to/references --reference-cache /path/to/cache` to
`research prepare`. It freezes the dossier and copies only assets marked
`execution` into `inputs/reference-assets/`, with hashes in
`inputs/REFERENCE-INPUTS.json`. Reading-only PDFs, sources, weights and data stay
in the reusable cache. Required input copies count against both acquisition
retention and workspace storage limits. Their directory is excluded through
Git's `info/exclude` too; a standalone workspace gets a local Git repository if
needed for that exclusion. Workers retain the same network denial and read-only
input protection. Changing an input prevents a native run; prepare a new revision
instead. The working dossier can accumulate later reading without editing its
frozen input snapshot.
