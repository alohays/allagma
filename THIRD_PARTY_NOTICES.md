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

## v0.3 study development sources

`studies/ema-schedule/development/science.py` copies the preceding study's
adaptation; the same license is retained at `studies/ema-schedule/reference/LICENSE`.
Its follow-up runner also uses those adapted mechanisms. The
[follow-up disclosure](studies/ema-schedule/REFERENCE.md) identifies the source
and AI-generated material.

`studies/core-culp/reference/` retains CORE-Bench scoring/prompt files from
`siegelz/core-bench` commit `e32a2980e72fe6eb04ee04eb749458f570625663` under its
included MIT license and the original `capsule-6460826` archive. Capsule code is
accompanied by its MIT license; dataset files retain their CC0 1.0 dedication.
The [provenance record](studies/core-culp/reference/provenance.json) identifies
the exact archive. These are study/evaluation resources, not dependencies of
the default conformance kit. Original reference answers and scorer code remain
outside evaluated agents' writable/readable workspaces.

The modular-addition pilot is an original small MLP implementation inspired by
[Power et al.](https://arxiv.org/abs/2201.02177), with the adaptation stated in
its [study README](studies/modular-addition/README.md). No upstream transformer
implementation is copied into that pilot.

The frozen v0.3 modular-addition evaluation additionally supplies selected
reference files from `openai/grok` at commit
`3d64b1d8c1d595dd8ebdb7771998823f1b14c7b3`, with the OpenAI copyright notice
and MIT license, inside candidate packages' `inputs/materials/openai-grok-reference/`.
The [freeze manifest](evals/research-v0.3/frozen/freeze.json) pins those bytes.
They are reference materials for a bounded MLP study, not evidence that the
original transformer experiments or training horizons were reproduced.

## Documentation and launch media

The separate `site/` project uses Astro Starlight and its locked Node development
dependencies. Those dependencies retain their upstream package licenses and do
not enter the default Python runtime. The site build includes their shipped
copyright and license notices in `generated/third-party-licenses.txt`, linked
from the page metadata. That appendix includes build-time dependencies as well
as browser code; it does not relicense Allagma or the scientific archives.
The workflow graphics, mark and social
preview are original Allagma assets; uv and marimo supplied editorial inspiration,
with no copied branding or graphics.

The flagship film captures actual local software. Narration is synthesized
locally with Kokoro-82M v1.0's `af_heart` voice (Apache-2.0 model) and
`kokoro-onnx` (MIT engine). The model and rendering dependencies are not
redistributed in the film or core. The [narration notices](media/demo/NARRATION-NOTICES.md)
retain pinned source links, attributions and a full Apache license copy.
Earlier private Git history retains superseded Apple-voice renders; the
publication review records that separate history issue.
The film's final chapter and `media/evidence/ema-r07.png` reuse the
machine-generated EMA figure produced with AI Scientist-adapted code. The full
study license accompanies that figure and the [video distribution](media/demo/EMA-LICENSE.txt),
and the video, transcript and site disclose the reuse and machine generation.
The compact core source archive excludes third-party study adaptations and
scientific dependency wheels. See [artifact distribution](docs/launch/artifact-distribution.md).
