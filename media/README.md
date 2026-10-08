# Allagma launch media

`workflow-*.svg`, `mark.svg` and `social-preview.svg` are original editable
Allagma graphics under the core MIT license. Regenerate them with
`python3 tools/generate_launch_assets.py --study /path/to/completed-toy-study`.
Do not replace a scientific figure with an illustration that implies new data.

`evidence/` contains exact selected scientific artifacts with a SHA-256
provenance index. The toy files come from a fresh offline execution. They are
previews, not a self-contained copy of the full study: original relative
references inside the raw Markdown/JSON resolve in the full generated study.
The site adds navigation around these unchanged files. Run the tutorial to
obtain and audit the complete package.

**EMA disclosure:** `evidence/ema-r07.png` is a retained, machine-generated
figure from the r07 study, produced with scientific code adapted from The AI
Scientist. It is not a fresh training result. The accompanying
[AI Scientist Source Code License](evidence/EMA-LICENSE.txt) and the
[study's source attribution](../studies/ema-schedule/REFERENCE.md) apply to the
adapted study materials. Do not label this scientific adaptation uniformly MIT.

The final video, captions, transcript, capture sources and instructions will be
added as the actual capture is completed. No video completion is implied by
the current graphic sources.
