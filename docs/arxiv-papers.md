# Add an arXiv paper to a study

Allagma's normal manuscript/report remains the default. A study can explicitly
request an additional English paper, compiled PDF and portable source archive.
The feature does not submit the paper to arXiv.

New studies contain `paper.json` with `output: report`. To request a paper while
preparing a native study, pass `research prepare --paper-config REQUEST.json`.
The request includes `format: allagma-paper-output-v1`, `output: arxiv` and
researcher-supplied `authors`. Preparation retains that attribution in protected
`inputs/PAPER.json`; the working paper configuration must agree with it.

For an existing study, initialize a new paper revision:

```sh
python3 -m allagma paper init --study /path/to/study \
  --title 'A precise title for the retained finding' \
  --authors /path/to/author-attribution.json
```

Attribution is configured per study. The JSON has `mode: named`, an `entries`
list (each entry has a `name` and optional `affiliation`, `email`, `orcid`),
`supplied_by` and `supplied_at`. Alternatively, explicitly choose `mode: anonymous`
with an empty entries list for an anonymous draft. No Git author, repository
owner or agent identity is inferred. The demonstration author `allagma` is an
explicit owner choice, not a default for other researchers.

## Write from retained results

The paper configuration names the reference dossier and TeX files for abstract,
introduction, related work, methods, results, discussion and limitations. Add
relevant appendices. The bibliography comes from verified metadata in the
critical literature map. Record how reading informed planning, implementation,
analysis and writing, including disagreements and limits of coverage.

Write the scientific paper in complete English paragraphs. Preserve negative
and inconclusive findings and distinguish a new manuscript revision from a new
experiment. First outline the scientific argument, then write and review it.
Apply humanizer to wording while preserving meaning, numerical values, citations,
attribution and uncertainty.

The configuration binds `evidence` IDs to study-relative paths and SHA-256
digests. Its `values` use an evidence ID, RFC 6901 JSON `pointer`, and a format
such as `d`, `.6f`, `.3g` or `text`. TeX uses `\AllagmaValue{ID}`. A `claims`
entry has an ID, text, status (`supported`, `negative`, `inconclusive`), result
locators, citation passage IDs and limitations. Its text can interpolate
`{{value:ID}}`; `\AllagmaClaim{ID}` inserts the resolved text.

`\AllagmaFigure{ID}` inserts an exact retained PDF, PNG or JPEG and its declared
caption. `\AllagmaTable{ID}` generates table cells directly from retained JSON
rows. Columns use JSON pointers, formats and optional numbered-value patterns
such as `{0} [{1}, {2}]` for an interval. Column widths and alignment are
configurable. Conversion of scientific figures happens before packaging, with
its own provenance and inspection; arXiv does not convert figures automatically.

`\cite{KEY}` and standard natbib variants use verified citation keys. Unknown
citations, source-passage IDs, claims, values and changed evidence fail the check.
Retain a scientific review and a humanizer review as hashed evidence and reference
them in `review`. These are scoped reviewer judgments. Deterministic checks
establish integrity and declared links, not that every prose assertion is true.
Each review record uses `format: allagma-paper-review-v1`, its `kind`, and
`reviewed_content_sha256` from `allagma.papers.review_fingerprint(study, config)`.
Changing prose, attribution, the reference map or selected scientific evidence
makes the review stale. This binding prevents an old review from silently
covering a new manuscript revision.

## Build and inspect

```sh
python3 -m allagma paper check --study /path/to/study
python3 -m allagma paper build --study /path/to/study \
  --destination /path/to/new-paper-revision
python3 /path/to/new-paper-revision/source/anc/build.py \
  --output /path/to/another-clean-build
```

Use `--config` for a configuration in a publication subdirectory. All evidence
and section paths are relative to `--study`. The optional adapter requires an
installed TeX distribution; the core installs nothing. The default compiler is
`pdflatex`; `--engine xelatex` is also supported. Each compiler command has a
finite timeout. macOS uses Seatbelt; Linux requires functional bubblewrap.
The builder has no unsandboxed fallback.

The output contains `paper.pdf`, `paper-source.tar.gz`, `delivery.json`, editable
sources and retained compiler receipts. The source archive contains TeX,
BibTeX and bbl, exact figure files, required custom styles and `anc/` with build
instructions, literature notes, claim/result links and provenance. It excludes
raw downloads, scientific weights/data, build logs, auxiliary files and the
compiled paper PDF. The optional source package has a 25 MiB expanded ceiling.

The adapter compiles once, packs the sources, unpacks them into a new directory
and compiles again without network or access to the reference cache. It rejects
unresolved references and overfull boxes. Render the PDF and inspect every page
for clipping, overlap, typography and legible figures/tables before delivery.
Keep that visual review separate from the build receipt.

## Template and compatibility

`template: {"name": "allagma-preprint"}` selects a compact single-column article
with standard TeX packages. The [adapter](../adapters/arxiv/README.md) documents
custom templates and required style files. A researcher can change presentation
without changing the retained results or attribution.

The [official arXiv TeX requirements](https://info.arxiv.org/help/submit_tex.html)
and [supported TeX systems](https://info.arxiv.org/help/faq/texlive.html), checked
9 October 2026, support TeX Live 2023 and 2025, with 2025 the default. Include
custom styles, use final figure formats and a fixed date, and retain bibliography
inputs plus the generated bbl. Ancillary instructions and provenance belong in
`anc/`. Inspect the PDF again if a researcher later uploads it to arXiv.

Existing studies, reports and frozen bundles remain unchanged. Adopt new methods
at a campaign boundary or add a new publication revision referencing the old
results. An older locked helper will not gain this command implicitly. Local
compilation does not establish arXiv acceptance, authorship eligibility or
independent scientific peer review. The delivery receipt names the actual
compiler used, rather than claiming a different TeX release was tested.

This increment exercises actual reference assets, protected preparation, offline
helper checks and a paper revision of a completed study. It does not add a fresh
native-model qualification run; the existing frozen native qualification and
onboarding session limits keep their recorded scope.
