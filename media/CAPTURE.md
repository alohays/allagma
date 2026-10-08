# Repeat the flagship capture

The film uses actual Allagma execution in the supplied local recording
workbench. The workbench is a demonstration utility, not the native agent UI.
It exposes two fixed commands and serves selected files on loopback only.
The final EMA chapter explicitly reuses retained r07 results.

## Inline playback in the README

The README opens with the current film uploaded as a GitHub repository
attachment. Its permanent `https://github.com/user-attachments/assets/...` URL
occupies its own paragraph, which GitHub renders as an expanded video player.
The [attachment receipt](demo/github-attachment.json) records the original MP4
digest, repository and upload date. The committed MP4, transcript, captions and
source/license notices remain the maintained distribution files.

When replacing the film, upload the reviewed MP4 through the README editor's
attachment control, put the returned permanent URL in the opening paragraph,
and update the receipt. Verify playback on the repository's rendered README.
GitHub's Markdown API can also verify the generated video element using the
repository as its rendering context. Private rendering may return temporary
signed media URLs: never commit those URLs or the unredacted rendered HTML.
Use only the permanent attachment URL in maintained documents.

The attachment was uploaded while the repository was private, as recorded in
the unchanged upload receipt. On 9 October 2026 the owner intentionally kept
the repository public and authorized public documentation activation. The
README video has now been verified while signed out, including its exact MP4
digest. This does not publish a software release or resolve the
[retained historical-audio rights issue](https://github.com/alohays/allagma/issues/8). See GitHub's
[attachment documentation](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files).

## Prerequisites

Use Python 3.11+, Node 22.12+, the site's locked development dependencies,
Chromium from Playwright, and FFmpeg/ffprobe. Narration uses Kokoro's Apache-2.0
model and the MIT-licensed `kokoro-onnx` engine in a separate environment.
No API account, remote rendering,
scientific dependency installation or GPU is required for the offline capture.

If you began with the small quickstart checkout, expand it from the repository
root before using the capture tools:

```sh
git sparse-checkout add site docs media studies/core-culp studies/modular-addition studies/ema-schedule
```

```sh
cd site
npm ci
npx playwright install chromium
node scripts/capture-demo.mjs ../work/launch/my-new-capture
cd ..
python3 -m venv work/launch/narration-env
work/launch/narration-env/bin/python -m pip install -r media/source/narration-requirements.txt
mkdir -p work/launch/narration-model
curl --fail --location \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx \
  --output work/launch/narration-model/kokoro-v1.0.onnx
curl --fail --location \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin \
  --output work/launch/narration-model/voices-v1.0.bin
work/launch/narration-env/bin/python tools/narrate_demo.py \
  --model work/launch/narration-model/kokoro-v1.0.onnx \
  --voices work/launch/narration-model/voices-v1.0.bin \
  --output work/launch/my-new-narration
python3 tools/render_demo.py \
  --capture work/launch/my-new-capture \
  --narration work/launch/my-new-narration \
  --output work/launch/my-new-render
```

Choose new output directories. Capture launches a loopback server on port 4331,
opens an isolated 1600×900 browser, clicks the real execution/audit controls and
records all scene timings. The server is stopped on completion. The initial
manual-preview server on a different port is not required.

The model and voices download is about 354 MB; these optional dependencies stay
under ignored `work/` and never enter the core distribution. The narrator verifies
both SHA-256 digests from `source/narration-model.json` before loading them. The
voice is `af_heart`, generated on CPU with two inference threads. Keep the
[narration source and license notices](demo/NARRATION-NOTICES.md) with the film.

The Python CLI has a 120-second outer bound per demonstration command, with the
toy retaining its own 60-second/28-attempt execution ceiling. Successful capture
requires 26 successful attempts and a passing 521-reference audit. Failed captures
must remain available and must not be described as passing footage.

## Editable sources and retained evidence

- `source/workbench.html`: actual functional local viewer and command controls.
- `source/scenes.json`: narration, chapter durations and concise on-screen descriptions.
- `site/scripts/capture-demo.mjs`: repeatable browser interactions and scene timing.
- `tools/demo_server.py`: bounded real command dispatch and artifact serving.
- `tools/narrate_demo.py`: hash-verified Kokoro synthesis and per-sentence clip receipts.
- `source/narration-model.json` and `source/narration-requirements.txt`: reviewed sources and pinned media-only environment.
- `tools/render_demo.py`: H.264/AAC encoding, VTT/SRT captions, transcript and provenance.
- `source/demo-poster.svg`: editable poster with an embedded actual capture frame.
- `demo/capture-timeline.json` and `demo/capture-state.json`: the actual recorded timings and selected results.

The raw WebM, fresh study, exact command receipts, audio clips and intermediate
frames stay under ignored `work/`. The repository ships
the small final MP4 plus caption/transcript/provenance assets. The movie's digest
and original footage digest are recorded; regeneration may differ with browser,
font, voice and machine timing versions. Scientific values must still verify.

The public `capture-state.json` preview omits the local execution-directory
field. Its source digest and this transformation are recorded in video
provenance. The original state and scientific values remain unchanged in the
capture directory; do not edit them to remove local metadata.

## Editing rules

The current film is continuous, with no accelerated computation. Only synthetic
narration tempo is adjusted to fit each actual scene; those factors are recorded.
Narration text can be edited without replacing footage: rendering reads the
current `scenes.json` against the frozen observed scene times. Public timeline
previews omit superseded draft narration; the original capture plan remains in
the capture directory. Final speech and captions are recorded in the transcript.
If future editing removes waits or speeds up footage, label that explicitly in
the video, transcript and manifest. Do not manufacture terminal output, a model
thought process, or successful results.

When replacing the final movie, render into a new directory, inspect every
chapter, listen to the narration, verify captions/playback and rerun the captured
study audit. Then copy the reviewed outputs to `media/demo/`, retain the old
capture privately, regenerate the poster, and rebuild/test the site. The social
preview and poster PNGs are rendered from their SVGs at 1280×640 and 1280×720.
Keep the EMA source license/disclosure with its figure and video use.

From `site/`, run `node scripts/render-graphics.mjs` to rasterize those two
editable SVGs. The poster embeds an actual captured result frame; when a future
recording changes its contents, replace that embedded frame before rendering.
