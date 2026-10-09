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
