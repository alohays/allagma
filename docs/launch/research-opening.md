# Research outputs in the public opening

The README and public docs now explain the research work before the machinery
that preserves it. The verified presentation is
[eb88886](https://github.com/alohays/allagma/commit/eb888865f1d5bc380e3b5b1d81788255ae3eebcc),
built on baseline `420e38adb174ded8c476a7a6ffd63c70b8672bf7`.
The following evidence commit retains this review and its screenshots; it does
not change the presented content. The current deployment identifies itself at
[build-info.json](https://alohays.github.io/allagma/build-info.json).

[Live opening](https://alohays.github.io/allagma/) ·
[README](https://github.com/alohays/allagma#readme) ·
[Demo](https://alohays.github.io/allagma/demo/) ·
[Example outputs](https://alohays.github.io/allagma/explore/) ·
[Completed study](https://alohays.github.io/allagma/studies/ema-schedule/)

## What changed and why

The opening names the audience, supplied inputs, agent work and returned files.
A visitor can read a completed study or start the local example directly.
The README's workflow illustration now follows the opening movie instead of
appearing after the quickstart, use cases and evaluation.

The landing page plays the existing licensed recording in its opening section.
Its poster pairs the unchanged toy plot with an exact manuscript sentence and
a counterexample annotation. This makes the output recognizable before playback.
The poster is a presentation graphic, not a product-interface screenshot.
The native player appears when playback starts; keyboard access, captions and
native controls remain available. Without JavaScript, the video retains native
controls. A content digest in the poster URL prevents stale artwork after updates.

The native-study preview shows the actual EMA figure beside an excerpt from the
agent's report. The small report download is byte-identical to the retained
package, with a provenance receipt and license notice. Qualifications about four
seeds, inconclusive duration/interaction estimates and reproduction scope stay
beside the result. Full-size figures and complete results are direct links.

The explorer starts on the result and shows the manuscript's actual abstract,
instead of describing the report. Its report and claim panels have stable
fragment links and support arrow-key navigation. The study index and individual
result summaries now lead with the question and finding. Their source selection,
scoring, resource use and reproduction details remain below and on linked pages.
Existing site routes and panel IDs are preserved; changed README section anchors
and the old EMA heading retain explicit aliases.

The installed humanizer workflow was applied to the edited prose: review the
source, rewrite paragraphs, then check for stock phrasing and changed claims.
The new text removes repeated slogans and sentence fragments. Scientific
quotations, data, citations and licensing text keep their original meaning.
Engineering and evaluation details remain in their canonical linked documents.
The offline example is labeled as supplied code; retained native-agent results
are identified separately.

## Visual and editorial assessment

| Surface | Before | After | Effect |
| --- | --- | --- | --- |
| Docs opening | [Desktop](evidence/research-opening/before-home-desktop-light.jpg) | [Desktop](evidence/research-opening/after-home-desktop-light.jpg) | An isolated toy number is replaced by a figure/report preview and a playable demo. Inputs, work and outputs are explicit. |
| Phone opening | [390 × 844](evidence/research-opening/before-home-mobile-light.jpg) | [390 × 844](evidence/research-opening/after-home-mobile-light.jpg) | Primary actions and video precede supporting text. The play button also fits a 390 × 664 viewport. |
| README | [Opening](evidence/research-opening/before-readme-desktop.jpg) | [Opening](evidence/research-opening/after-readme-desktop.jpg) and [workflow](evidence/research-opening/after-readme-workflow.jpg) | Working inline video stays near the top; the workflow and a completed native result appear before setup and engineering detail. |
| Demo | [Before](evidence/research-opening/before-demo-desktop.jpg) | [After](evidence/research-opening/after-demo-desktop.jpg) | The poster shows outputs, and the next actions lead to those outputs or the tutorial. |
| Artifact explorer | [Brief first](evidence/research-opening/before-explorer-desktop.jpg) | [Actual report excerpt](evidence/research-opening/after-report-desktop-light.jpg) | The default is now the plot; the report tab contains readable source text and a full download. |
| Native result | [Before](evidence/research-opening/before-study-desktop.jpg) | [Featured figure and report](evidence/research-opening/after-native-preview-desktop.jpg) | The figure, interpretation, limitations and source report can be assessed together. |

The existing paper/teal palette and Starlight navigation remain. Text is larger
in the explorer, unnecessary tab spacing is removed, figures have full-size
links, and action styling distinguishes the main next step from supporting
links. Scientific figures keep their original colors and scales in both themes.

This assessment is an editorial and visual inspection, not a measured usability
study. Phone checks use responsive viewports and browser emulation, not a
physical handset. Small scientific axis labels still benefit from the full-size
links on phones.

## Requirement-by-requirement evidence

| Requirement | Current evidence | Result |
| --- | --- | --- |
| Explain audience, inputs, agent work and outputs | Published README and landing; desktop/phone screenshots | Pass |
| Show real outputs before engineering concepts | Plot/report poster; actual EMA figure and exact report excerpt; full-result links | Pass |
| Promote the workflow illustration | README screenshot and responsive light/dark SVG sources | Pass |
| Play a demo in the opening and preserve GitHub playback | Native controls, keyboard play, seeking, visible captions, anonymous README playback | Pass |
| Distinguish offline and native work | Opening caption, demo chapters, study labels, nearby limitations and unchanged movie transcript | Pass |
| Improve demo, explorer, studies and navigation | Live routes, report deep link, keyboard tabs, mobile menu, search and tutorial route | Pass |
| Apply natural English prose and keep meaning | Humanizer review; preserved scientific outputs and source quotations | Pass |
| Inspect desktop/phone and both themes | Live Pages screenshots; signed-out light README and existing dark-theme Chrome README | Pass |
| Verify links, downloads and source bytes | 38 live content routes; 1,962 internal links/fragments; 34 README links; 10 exact assets | Pass |
| Preserve canonical sources, history, science and contributor work | Content map, legacy anchors, preservation audit, unchanged draft PR heads | Pass |
| Commit, push and publish the reviewed content | Exact-head successful Pages, Documentation and Conformance runs below | Pass |

## Validation

The [validation receipt](evidence/research-opening/validation.json) records a
39-page production build, 2,418 local link/asset checks and 18 passing Chromium
tests across desktop and iPhone 13 emulation. The tests cover both themes,
overflow, axe accessibility, production search, keyboard navigation, report
fragments, video decoding/playback/seeking/captions and exact download bytes.
The catalog check passes. Hosted npm audit reported zero vulnerabilities.

Exact presentation-commit runs:

- [Pages deployment](https://github.com/alohays/allagma/actions/runs/37879960484)
- [Documentation, accessibility and 18 browser tests](https://github.com/alohays/allagma/actions/runs/37879960488)
- [Conformance and offline acceptance](https://github.com/alohays/allagma/actions/runs/37879960498)

The [anonymous HTTP receipt](evidence/research-opening/public-http.json)
records the live build identity and byte comparisons, including the movie,
captions, poster, scientific figures and both report downloads.
[README link checks](evidence/research-opening/readme-links.json) cover all
34 Markdown links; private security submission intentionally requires sign-in.
The [browser observations](evidence/research-opening/live-browser.json) record
actual live interactions. The final mobile playback advanced past 62 seconds
with English captions showing; the signed-out README playback advanced past
35 seconds. Search reached both the tutorial and the EMA result.

The first phone check exposed a play control below the 390 × 664 viewport.
Reordering supporting copy fixed it. The in-app browser also displayed a
loading indicator on the paused poster. A stable poster cover now gives way
to the native player on play. Accessibility checks caught focusable fallback
links in an initially hidden video; using `inert` until playback fixed that.
All 18 checks passed after these repairs.

## Preservation and limits

The [preservation audit](evidence/research-opening/preservation-audit.json)
compares the final presentation with the starting commit. Core code, methods,
contracts, profiles, examples, frozen evaluation records, release metadata and
project configuration are unchanged. Within `studies/`, only the three public
result summaries changed. Fifteen existing scientific/media files, including
the movie, captions, transcript and upload/capture receipts, are byte-identical.

The native report copy matches its original package index; the poster uses
unchanged scientific inputs. Full Git history remains intact. Contributor
PRs #10, #11 and #12 are still drafts at their original heads, with no merges.
No new scientific campaign or native model session was run. Existing model,
compute and storage limits remain unchanged.

Report downloads retain their original relative references, which resolve in
the full restored study package. The existing native-onboarding timeout and
scientific/evaluation limits remain documented. The
[historical-audio rights issue](https://github.com/alohays/allagma/issues/8)
remains open; current published playback uses the unchanged cleared Kokoro film.

The [evidence manifest](evidence/research-opening/manifest.json) hashes the
retained screenshots and receipts. Screenshots were gathered during the
publication pass; the final opening captures show the deployed poster and player.
