# Launch editorial and visual direction

Allagma helps a coding agent leave an inspectable research record: the question,
frozen plan, exact methods, every attempt, measured results and claims linked to
their evidence. Lead with that benefit, then a useful first result. Keep the
method/recipe/adapter architecture one level deeper.

The release is **0.3.0rc2**, a source release candidate. Do not silently relabel
it stable, imply a package-index install, or turn a twelve-session local
comparison into a general quality/speed claim. Six of six Allagma and four of
six plain-Codex packages met the full evidence requirements; all twelve executed
the required science. Preserve the explanation of the two review-binding gaps.

Take editorial cues from [uv](https://github.com/astral-sh/uv) (precise opening,
immediate command, concrete output) and [marimo](https://github.com/marimo-team/marimo)
(show working software, make examples easy to find). No upstream graphics,
branding, copy, or adoption claims are reused.

## Identity

Use a restrained laboratory-notebook aesthetic: warm paper, ink, teal for
verified links and amber for retained attempts/uncertainty. A small open-frame
mark connects an input card to an evidence card. Typography combines a clear
system sans-serif with a monospace evidence index; no remote font requests.
Large statements, generous spacing and visible provenance carry the identity.

The main visual follows one question through Brief → Plan → Attempts → Findings,
with a visible connection back to the original record. Color is never the only
carrier of status. SVG sources remain editable. Use raster previews for social
sharing and a static GitHub-compatible video poster.

## Demonstration truthfulness

Record actual commands and actual rendered artifacts. The offline toy is a
known-answer workflow, not an LLM benchmark. Historical native study outputs
are labeled as retained results, with run IDs and source links. Any time
compression, transitions or omitted waiting are labeled in the video and
transcript. No simulated model reasoning, fabricated terminal output, or new
claims of successful native execution from a screenshot.

## Content ownership

Maintain prose in existing repository documents and new canonical `docs/`
guides. Generate site copies during build with explicit source links; do not
hand-edit two versions. The site is a separate Node toolchain in `site/` and
does not change Python runtime dependencies. Publish a small selected evidence
preview; keep full archival packages opt-in and hash-addressed.
