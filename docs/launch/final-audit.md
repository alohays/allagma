# Final audit before public release

**Audit completed on 8 October 2026. Public launch remains blocked by historical
audio clearance.** The owner explicitly chose to retain the full history
unchanged and finish this audit with that blocker. The current demo uses a
replacement voice; the repository must remain private until the older recordings
are cleared or a later authorized publication strategy resolves their exposure.

The implementation audited here is `7606f87a21b3aceb077166a44a93143deb996374`.
Evidence and reporting commits follow it. The scientific framework source remains
`sha256:a7a67e09548e40442f2ff72ba63898f66e02368046132a183588ebebdbc1a196`.
This report supersedes the earlier launch-readiness assessment where they differ.

## Findings and repairs

| Finding | Result |
| --- | --- |
| **Release archive could include private local files.** The generator recursively copied workspace directories, including untracked and ignored files. | Fixed in `07a19ab`: packaging reads committed HEAD blobs only, rejects symlinks, preserves previous outputs and records its source policy. A [synthetic before probe](evidence/final-audit/packaging-before-probe.json) and [six passing regression tests](evidence/final-audit/package-tests.log) establish the boundary. No real secret was used in the probe. |
| **Archive documentation pointed to omitted local files.** The compact asset retained README links and images whose targets were absent. | Fixed in `07a19ab`: omitted targets link to the exact source commit; image sources use raw URLs. Original document digests and transformations are recorded. Core bundle bytes remain unchanged. The extracted archive has no missing local documentation targets. |
| **The demo's Apple system-voice narration was not cleared for public sharing.** The earlier review incorrectly treated absence of a redistributed voice model as sufficient. | Current asset fixed in `7606f87`: Kokoro-82M v1.0 / af_heart, Apache-2.0 model and MIT engine, with [pinned sources and notices](../../media/demo/NARRATION-NOTICES.md). The video stream is byte-identical, the new narration has 22 synchronized caption cues, and playback passes. |
| **Two restricted older movie versions remain in Git and GitHub PR history.** Updating the current MP4 does not remove them. | **Open public-launch blocker, explicitly retained by owner decision.** The [exact historical blobs](evidence/final-audit/historical-audio.json) and [license basis](publication-review.md#final-audit-correction-narration-rights) are recorded. No history rewrite or rights clearance is claimed. |

## Requirement-by-requirement verification

| Area | Current evidence and scope |
| --- | --- |
| I1–I5 and offline behavior | [Fresh acceptance](evidence/final-audit/acceptance/acceptance.json): all five scenarios and **113 tests**, no skips. Generic/Codex/Claude packaging uses the same bundle and scientific outputs; native model behavior is not inferred from those fixtures. |
| Complete toy science | 26 successful attempts, one failure, one interruption, 24 confirmation seeds and **521 evidence checks**. [Independent rational arithmetic](evidence/final-audit/independent-toy.json) confirms mean difference **25/384**, three negative seeds and one tie, and all 24 positive leave-one-seed-out means. |
| Retained audit evidence | [Independent archive check](evidence/final-audit/acceptance-archive-check.json) verifies all **5,944 files** and the exact member set. [Independent schema validation](evidence/final-audit/external-validation.json) passes eight schemas, 643 record occurrences and 290 skills. |
| Compact source onboarding | [Committed-source archive](evidence/final-audit/source-distribution.json): **137,542 bytes**, extracted into a new directory. Actual extracted code passes I1–I5, 113 conformance tests, six release-boundary tests and its local documentation links. No wheels, models or scientific archives are included. |
| Production documentation | [Build](evidence/final-audit/site-final-build.log): **38 pages**, **2,168 local links**, no errors under `/allagma/`. [Browser checks](evidence/final-audit/browser.json): **14 pass**, covering mobile/desktop, themes, keyboard, search, canonical routes, figures and real video playback/seeking/captions. The local in-app browser also played the replacement movie successfully. |
| Media and attribution | [Media verification](evidence/final-audit/media-verification.json): H.264/AAC, 1600×900, **100.433 seconds**, **2,875,851 bytes**, exact script/caption match and unchanged scientific footage. Narration synthesis used local CPU and no paid API; its [generation receipt](evidence/final-audit/narration.json) is retained. |
| Dependencies and links | [npm audit](evidence/final-audit/npm-audit.json): zero reported vulnerabilities. [External link check](evidence/final-audit/external-links.json): four external endpoints pass; 177 owned/prelaunch URLs are classified separately rather than falsely counted as live public endpoints. |
| Privacy and redistribution | [Full reachable-history scan](evidence/final-audit/history.json): **73 commits**, **7,736 blob versions**, **54,889 archive members**, **12 multipart archives**, no credential-pattern matches or unhandled archive errors. Accepted historical metadata remains. [Built-site check](evidence/final-audit/site-privacy.json) finds no owner home-directory prefix. Existing MIT/CC0/AI Scientist boundaries remain documented; the historical narration issue is open. |
| Preserved invariants | [Exact baseline comparison](evidence/final-audit/preservation.json): framework, modules, contracts, conformance, studies and evaluations unchanged from `608f34e`. Frozen records and original failures are intact. No project model configuration added, no native continuation run, and no expanded study budget. |
| GitHub/publication controls | [Repository settings](evidence/final-audit/repository-settings.json): private, Pages off, Discussions off, no releases and no launch-enabling variable. [Workflow metadata](evidence/final-audit/metadata.json) has read-only default permissions and no privileged fork trigger. Hosted checks and push identities are recorded separately after the audit commit. |

## Publication decision and limits

The audit is complete; the repository is **not cleared for public visibility**.
Follow the [owner checklist](owner-actions.md), beginning with historical audio
clearance. The current film's license repair does not override that blocker.

Pattern scanning cannot prove absence of every secret. Structural checks do not
establish scientific validity outside the specific independently recomputed toy,
and automated accessibility checks do not cover every assistive technology.
This audit preserves the earlier twelve-session native qualification rather than
rerunning it. The extra bounded native onboarding probe remains an incomplete
handoff at the owner's chosen limit. No general model superiority, unrestricted
MIT license for the entire archive, or active public deployment is asserted.
