# Repeat the flagship capture

The film uses actual Allagma execution in the supplied local recording
workbench. The workbench is a demonstration utility, not the native agent UI.
It exposes two fixed commands and serves selected files on loopback only.
The final EMA chapter explicitly reuses retained r07 results.

## Prerequisites

Use Python 3.11+, Node 22.12+, the site's locked development dependencies,
Chromium from Playwright, and FFmpeg/ffprobe. Narration rendering additionally
uses macOS `say` with its Samantha voice. No API account, remote rendering,
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
python3 tools/render_demo.py \
  --capture work/launch/my-new-capture \
  --output work/launch/my-new-render
```

Choose new output directories. Capture launches a loopback server on port 4331,
opens an isolated 1600×900 browser, clicks the real execution/audit controls and
records all scene timings. The server is stopped on completion. The initial
manual-preview server on a different port is not required.

The Python CLI has a 120-second outer bound per demonstration command, with the
toy retaining its own 60-second/28-attempt execution ceiling. Successful capture
requires 26 successful attempts and a passing 521-reference audit. Failed captures
must remain available and must not be described as passing footage.

## Editable sources and retained evidence

- `source/workbench.html`: actual functional local viewer and command controls.
- `source/scenes.json`: narration, chapter durations and concise on-screen descriptions.
- `site/scripts/capture-demo.mjs`: repeatable browser interactions and scene timing.
- `tools/demo_server.py`: bounded real command dispatch and artifact serving.
- `tools/render_demo.py`: H.264/AAC encoding, local voice, VTT/SRT captions, transcript and provenance.
- `source/demo-poster.svg`: editable poster with an embedded actual capture frame.
- `demo/capture-timeline.json` and `demo/capture-state.json`: the actual recorded timings and selected results.

The raw WebM, fresh study, exact command receipts, audio clips and intermediate
frames stay in the capture directory under ignored `work/`. The repository ships
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
