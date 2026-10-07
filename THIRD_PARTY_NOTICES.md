# Third-party notices and design attribution

Allagma's core implementation is original code and prose under the repository's
MIT license. The Python interpreter is a prerequisite, not redistributed here.
The default runtime has no third-party Python dependencies. No ARIS, RRSI or
AntOmniEvo source code or skill text is vendored.

The adopted design draws on ARIS (MIT), RRSI (Apache-2.0), AntOmniEvo
(Apache-2.0), Agent Skills, Copier, uv and nf-core. These are design references,
not installed runtime dependencies or claims of integration. Pinned mechanisms
and local adaptations are listed in [design lineage](docs/design-lineage.md).
The license descriptions are the findings of the supplied design audit, not a
new legal review of every upstream file. Any future source reuse must retain
the applicable file-level license and notices.

The planning specifications in `docs/specification/` were supplied by the
repository owner and copied with a digest provenance record. External links
inside them identify their own sources.

## Native Codex weight EMA diffusion study

`studies/ema-2d-diffusion/reference/` retains selected source files from
SakanaAI/AI-Scientist at commit `1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb`,
with a [retrieval and digest record](studies/ema-2d-diffusion/reference/provenance.json).
The reference files and the adaptations in `domain/science.py` and
`domain/runner.py` are subject to the [AI Scientist Source Code License,
version 1.0](studies/ema-2d-diffusion/reference/LICENSE). This source is outside
the core's default runtime. The license accompanies frozen scientific materials.

[REFERENCE.md](studies/ema-2d-diffusion/REFERENCE.md) identifies the adapted
mechanisms and modifications. The study's
[machine-generation disclosure](studies/ema-2d-diffusion/DISCLOSURE.md) applies
to its code, analyses, manuscript drafts and reports; the final published
manuscript repeats that disclosure prominently. Python packages are installed
only into an ignored study-owned environment; their versions are pinned in
`requirements.lock` and their package licenses apply to those installations.
