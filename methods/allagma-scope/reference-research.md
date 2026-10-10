# Critical reference research

Read `references/INDEX.md` at study entry and on every resumed session. Read the
specific notes and source passages needed for the current decision, rather than
loading all PDFs into context. The map is study-owned; frozen input snapshots
and historical campaign records are immutable.

1. Record the question, search mode, exact queries, primary search sources,
   dates, filters/selection rationale and coverage limits. Cover primary papers,
   implementations, baselines, competing findings and gaps. Record why a category
   is limited or inapplicable. Follow citations and code links where relevant.
2. Deduplicate by DOI, arXiv identity across versions, and normalized title.
   Combine normalized titles with author/year identity; different works can share
   a title. Preserve one citation key. Resolve conflicting authors, versions or years by
   checking primary publication metadata; do not silently merge conflicts.
3. Read the relevant source. Record a page/section/code locator, a concise
   paraphrase (or short permitted excerpt), its claim, support assessment and
   limitation. Confirm metadata independently of this assessment. A title match,
   abstract or citation count does not establish support for a detailed claim.
4. Explain relevance and the consequences for planning, implementation,
   analysis and writing. Include mismatched populations, budgets, metrics,
   assumptions and negative or competing findings. Keep hypotheses distinct
   from established results. Link phase decisions to individual passage IDs.
5. Select assets for understanding or planned reproduction. Retain important
   paper PDFs and available source; pin code to commits and model/data files or
   splits to revisions and hashes. Record licenses and unavailable/gated states.
   Use the acquisition adapter outside scientific workers. Do not fetch entire
   model/dataset repositories when selected files suffice.
6. Run `reference check --require-review` and refresh the index/BibTeX. The
   check validates the record and its links, not the correctness of scientific
   interpretation. Review that interpretation explicitly.

Preparation can snapshot a completed dossier into `inputs/references/` and
materialize only explicitly selected execution assets into immutable inputs.
Maintain later reading in the study's working `references/`; freeze a new
snapshot for a revised protocol or manuscript. Do not rewrite prior inputs.

At planning, cite which sources establish baselines or expose a gap. During
implementation, check pinned code and assumptions against the protocol. During
analysis, compare outcomes with prior findings while preserving differences in
design. During writing, recheck each cited passage and each claim's result links.
On resumption, read the index, the current snapshot identity and unresolved
coverage/contradiction notes before acting.
