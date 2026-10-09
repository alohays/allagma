# Optional arXiv paper output

This adapter produces an additional paper PDF and portable source archive from
study-owned English prose, a critically reviewed literature map and retained
scientific evidence. It never submits anything. The default study option is
`output: report`; no TeX process runs for that option.

Set `paper.json` to `allagma-paper-output-v1` with `output: arxiv`. Author
attribution is configured per study and must name its researcher source and date.
No maintainer, Git identity or agent name is copied into a paper automatically.
Named authors may include affiliation, email and ORCID. Anonymous draft mode is
explicit. Authorship eligibility and a future submission remain researcher decisions.

Write the required abstract, introduction, related work, methods, results,
discussion and limitations as TeX section files. Declare relevant appendices.
Use `\cite{KEY}` for verified reference keys and `\AllagmaValue{ID}`,
`\AllagmaClaim{ID}`, `\AllagmaFigure{ID}` and `\AllagmaTable{ID}` for generated
evidence. Values and table cells resolve through JSON pointers into hashed
analysis files. Claims carry result locators, source-passage links, status and
limitations. Figures copy the exact hashed PDF/PNG/JPEG. Scientific and humanizer
reviews are retained evidence; validation checks their existence and declared
scope, not whether an agent's judgment is correct.

Reviews are JSON records bound to a content fingerprint of prose, author
metadata, citations and selected results. Editing that content makes a review
stale. The final PDF also records the configured title and authors in its metadata.
Set `breakable: false` on a short table to keep its rows on one page.

The configurable default is a small single-column `article` preprint style with
standard TeX packages. A custom template declares its main template digest and
each required `.sty`, `.cls` or `.bst` file. Every template must include the
`@@TITLE@@`, `@@AUTHORS@@`, `@@DATE@@`, `@@BODY@@` and `@@APPENDICES@@` slots and
include `sections/abstract.tex` and `evidence-macros.tex`. Custom templates remain
subject to clean compilation and visual review.

`paper build` compiles in a fresh temporary directory, includes the generated
BibTeX `.bbl`, creates `paper-source.tar.gz`, unpacks that archive in another new
directory and compiles it again with network and reference-cache access denied.
It checks final logs for unresolved references and overfull boxes. Inspect every
PDF page separately before delivery. Failed builds remain in their output
directory; use a new revision for the next attempt.

The archive contains `main.tex`, section sources, the bibliography, `.bbl`,
figures, required custom styles, and an `anc/` directory with build instructions,
the standalone builder, reference notes and provenance. Its total expanded size
is capped at 25 MiB. Raw downloaded papers, code archives, model weights and
dataset files belong in the excluded reference cache and cannot be copied as
paper evidence. No build log, auxiliary file or final paper PDF enters the source
archive. The final paper PDF is delivered separately.

The standalone builder uses installed TeX and OS isolation: macOS Seatbelt or
Linux bubblewrap. It does not install packages and has no unsandboxed fallback.
`pdflatex` and `xelatex` are supported engine choices. Current official arXiv
guidance, checked 2026-10-09, supports TeX Live 2023 and 2025 (default 2025).
The build receipt states the actual tested compiler. A successful local build
does not prove successful arXiv processing, acceptance or independent peer review.

Official sources: [TeX submission requirements](https://info.arxiv.org/help/submit_tex.html),
[supported TeX systems](https://info.arxiv.org/help/faq/texlive.html), and
[ancillary files](https://info.arxiv.org/help/ancillary_files.html).
