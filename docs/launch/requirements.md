# Public launch acceptance ledger

The authoritative scope is the public-launch goal in [GOAL.md](../../GOAL.md).
The baseline is release source `608f34e276aefc00c39ffb6f28c9c63bd420af95`.
No source qualification is inferred for later edits. The repository remains private.

| Gate | Required outcome | Status and evidence |
| --- | --- | --- |
| L1 Positioning | Precise README, opening visual, use cases, outputs, verified first result, progressive architecture and honest support boundaries | Implemented; [clean local onboarding](evidence/clean-onboarding-initial.json) and [independent toy check](evidence/toy-independent.json) pass; final remote download check pending |
| L2 Visual system | Original identity, workflow, real figures and artifact previews; mobile and both themes | Implemented; [desktop light](evidence/desktop-light-home.png), [desktop dark](evidence/desktop-dark-home.png), [mobile light](evidence/mobile-light-home.png), [mobile dark](evidence/mobile-dark-home.png); final asset review pending |
| L3 Flagship demonstration | Actual working software in a polished 60–120 second video; truthful edits/time/reuse labels; captions, transcript, linked preview, editable sources and repeatable capture | Actual ~100-second capture completed; [capture sources/instructions](../../media/CAPTURE.md), [transcript](../../media/demo/transcript.md), [provenance](../../media/demo/provenance.json); final source-bound capture encoding/verification in progress |
| L4 Documentation | Astro Starlight, landing, search, full first study, guides, CLI/concepts, three real studies, limitations, troubleshooting, contributing; canonical content reused | 38 built pages, canonical map and generated CLI help; production search, all-route render and mobile checks pass locally |
| L5 Deployment | Actual `/allagma/` Pages base, automated build/link checks, fork-safe CI, deployment prepared without activation, runnable local preview | Local production build passes; private-gated Pages workflow prepared; sparse CI checkout and remote jobs still to verify |
| L6 Community | Description/topics/social preview, citation, roadmap, release/support/security/contribution docs, issue/PR forms, Discussions plan, concrete starter tasks and launch copy | Implemented/prepared; [repository settings](evidence/repository-settings.json) remain private; [owner activation actions](owner-actions.md) are explicit |
| L7 Publication review | Tracked content and full reachable history reviewed for secrets/private material and redistribution; frozen records preserved, practical artifacts/distribution | [Initial full-history scan](evidence/history-review-initial.json) passes its documented coverage; owner accepted metadata exposures; final committed-state scan and redistribution inventory pending |
| L8 Validation | Clean-checkout onboarding, desktop/mobile/browser/keyboard/search/media/link/command/production verification; actual repairs and retained evidence | 113 conformance tests and fresh I1–I5 [acceptance](evidence/acceptance/acceptance.json) pass; [archive checked](evidence/acceptance-archive-check.json); native onboarding wall-time limits and final distribution checks still under review |
| L9 Handoff | Coherent commits and final push, private visibility confirmed, exact owner actions, full requirement-by-requirement completion audit | Two coherent launch commits made; final push and remote CI await complete local qualification |

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
