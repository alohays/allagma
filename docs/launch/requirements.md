# Public launch acceptance ledger

This table records the **8 October 2026 launch-preparation audit** against the
public-launch goal in [GOAL.md](../../GOAL.md), using release source
`608f34e276aefc00c39ffb6f28c9c63bd420af95`. Its private-visibility and deferred-
activation statements describe that historical preparation, not current settings.
No source qualification is inferred for later edits.

On 9 October the owner confirmed intentional public visibility and authorized
Pages/community activation and contributor publication. See the current
[owner actions](owner-actions.md) and [contributor delivery ledger](../contributing/first-workflow.md).
Historical-audio rights remain unresolved in
[maintainer issue #8](https://github.com/alohays/allagma/issues/8). The current
Kokoro movie does not clear older recordings. The owner explicitly instructed
that this retained rights issue must not be treated as a renewed private-only
gate for the authorized public documentation and community work.

The [final audit](final-audit.md) and [publication review](publication-review.md)
retain the exact historical findings and evidence. Technical checks and public
activation do not themselves establish redistribution rights.

| Gate | Required outcome | Status and evidence |
| --- | --- | --- |
| L1 Positioning | Precise README, opening visual, use cases, outputs, verified first result, progressive architecture and honest support boundaries | Pass: README and visuals; clean local onboarding and the [actual remote quickstart](evidence/remote-onboarding.json) pass |
| L2 Visual system | Original identity, workflow, real figures and artifact previews; mobile and both themes | Pass: [desktop light](evidence/desktop-light-home.png), [desktop dark](evidence/desktop-dark-home.png), [mobile light](evidence/mobile-light-home.png), [mobile dark](evidence/mobile-dark-home.png); SVG text bounds and real figure provenance checked |
| L3 Flagship demonstration | Actual working software in a polished 60–120 second video; truthful edits/time/reuse labels; captions, transcript, linked preview, editable sources and repeatable capture | Pass: actual 100.43-second film, [capture sources/instructions](../../media/CAPTURE.md), [transcript](../../media/demo/transcript.md), [provenance](../../media/demo/provenance.json); playback, captions and corrected scientific wording verified |
| L4 Documentation | Astro Starlight, landing, search, full first study, guides, CLI/concepts, three real studies, limitations, troubleshooting, contributing; canonical content reused | Pass: 38 built pages, canonical map and generated CLI help; production search, every canonical route and mobile checks pass |
| L5 Deployment | Actual `/allagma/` Pages base, automated build/link checks, fork-safe CI, deployment prepared without activation, runnable local preview | Pass: exact sparse checkout, production base and all hosted docs/conformance/link/release-preparation jobs; [publication receipt](evidence/publication.json) |
| L6 Community | Description/topics/social preview, citation, roadmap, release/support/security/contribution docs, issue/PR forms, Discussions plan, concrete starter tasks and launch copy | Pass for preparation: metadata configured, social/citation/community assets ready, [owner activation actions](owner-actions.md) explicit; no public activation |
| L7 Publication review | Tracked content and full reachable history reviewed for secrets/private material and redistribution; frozen records preserved, practical artifacts/distribution | Audit complete, publication blocked: retained historical Apple-voice recordings lack clearance. Current narration replaced; source packaging now excludes all uncommitted files. See [publication review](publication-review.md). Earlier secret scans and accepted metadata policy remain valid within their scope |
| L8 Validation | Clean-checkout onboarding, desktop/mobile/browser/keyboard/search/media/link/command/production verification; actual repairs and retained evidence | Pass: I1–I5 and 113 tests, [extracted source qualification](evidence/source-distribution-final.json), [14 browser checks](evidence/browser-final.json), independent captured-toy math. The extra native probe remains explicitly incomplete at its model-wall-time limits |
| L9 Handoff | Coherent commits and final push, private visibility confirmed, exact owner actions, full requirement-by-requirement completion audit | Pass: coherent commits and private push, four successful hosted workflows, remote onboarding, runnable preview and explicit owner actions; final bookkeeping commit is checked separately |

## Invariants

- English public material. Python 3.11+ and standard library for the offline core.
- Scientific code belongs to each study. Historical bundles and attempts remain immutable.
- No GUI or personal model overrides. Existing authentication only; finite local workloads.
- No public activation, release publication, announcements, fabricated adoption or qualification.
- Native CLI qualification is scoped to the recorded host; offline example and model workflow are distinct.
- All acceptance claims must identify actual inspected evidence, not just a manifest or intended check.

## Working sequence

1. Inspect release/source/settings, audit publication risk, establish content and design.
2. Make a small first-use distribution, run the example and author canonical documentation.
3. Build and inspect the site, capture the actual demo, finish contribution surfaces.
4. Test clean onboarding, presentation/accessibility/media/search/links and production build.
5. Close every gate, commit and push; verify CI and private visibility. Record owner launch actions.
