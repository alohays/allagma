# Issue triage — 10 October 2026

Main was inspected at `f235f1868eec7f6cc9518e5d59053a236b876358`, including the
reference/paper feature and its four repaired review findings. The subsequent
documentation audit merge `14c2fba9c54b636a34c0e8da10155c1f66bef6c8` was included
before updating this queue. It changes documentation and receipts, not the
implementation used by the probes below.

Only two new issues were selected. Both are available, unassigned and in the
[first contributor milestone](https://github.com/alohays/allagma/milestone/1).

| Order | Issue | Why it is next |
| --- | --- | --- |
| 1 | [#18: required adapter regressions](https://github.com/alohays/allagma/issues/18) | The new acquisition and paper adapters have dedicated regression suites that the required change selector omits for adapter-only diffs. Make the existing pre-merge check cover them. |
| 2 | [#19: runnable toy-to-paper walkthrough](https://github.com/alohays/allagma/issues/19) | The merged guides describe contracts and placeholder commands. A small example should let contributors follow actual toy results through explicit reference coverage, attribution, review and optional paper compilation. |

This is agent-assisted maintainer triage. The issues distinguish a reproduced
CI selection gap from an observed documentation gap; neither claims an external
user incident or broader scientific/native-host qualification. Their acceptance
criteria and validation are in the issues. This task selects the work, rather
than implementing the newly opened issues.

## Reconciled queue

Issues #2–#5 were already closed as completed through #11, #10, #12 and #15,
respectively. Their introductions now say the work is on main, while preserving
the original problem and acceptance evidence. No completed issue was reopened,
deleted or falsely closed by this triage.

[#6](https://github.com/alohays/allagma/issues/6) had an unanswered contributor
claim. Its proposed scope was confirmed, it was assigned to `codedbypraneetha`,
and its status became `in progress`. The `help wanted` and `good first issue`
labels were removed; `accessibility` was added. The reply clarifies that the
contributor's Windows/Node environment can handle the documentation task without
qualifying the POSIX runtime. Assignment does not imply a completed contribution.

[#7](https://github.com/alohays/allagma/issues/7) remains available. Current CI
uses Python 3.11 for targeted checks and 3.12 for push acceptance, so the requested
literal Linux/Python 3.13 tutorial receipt is still missing. The issue now links
the current main baseline and distinguishes this gap from #18 and #19.

[#8](https://github.com/alohays/allagma/issues/8) remains blocked and assigned to
the owner. Its wording recognizes the authorized completed merges without
claiming historical-audio clearance. Public visibility, the current licensed
movie, and successful engineering checks do not resolve that existing issue.

The [pinned overview](https://github.com/alohays/allagma/issues/9), milestone
description, [starter list](starter-tasks.md), [roadmap](../../ROADMAP.md) and
[community guidance](../launch/community-plan.md) identify the same work.
Current owner/feature guidance no longer calls merged work pending. Historical
audit receipts are preserved; historical narrative is explicitly labeled.

## Evidence and alternatives considered

The [selector probe](evidence/issue-triage/selector-probe.json) runs the real
selector with each adapter path as a synthetic one-file Git diff and captures
the selected unittest invocation. Catalog and documentation checks run; the
captured test commands are not executed by that probe. Both cases select only
`test_modules`, `test_research` and `test_versions`, omitting the dedicated suites.
The separate TeX job covers arXiv builds, but not an acquisition-only change.
Full push acceptance provides later coverage and is not a required PR check.

The [archive probe](evidence/issue-triage/archive-probe.json) packages committed
main source, extracts it under a path with spaces, and runs the catalog and full
conformance from the extracted tree: **184 tests pass** on macOS/Python 3.11.6.
The 209,954-byte archive has SHA-256
`0269727ce8515b0866ac5af1bfe11d1a436e0b2e9ebb68541610f9465ad6ec68`.
This verifies the existing compact distribution in that environment; it does
not qualify Linux/Python 3.13 or publish a release.

No duplicate issue was added for Linux qualification or historical rights.
No distribution defect was inferred from an absent formal GitHub release.
New native providers, larger studies, package-index publication and remote
artifact infrastructure were deferred: they add scope or owner/cost decisions
without addressing these immediate contribution gaps. The four #14 findings
were already repaired and merged, so they were not reopened.

The [validation receipt](evidence/issue-triage/validation.json) records 410
canonical links, 43 built pages with 2,848 internal links/assets, 18 passing
browser tests and the desktop/light and mobile/dark review of the updated task
page. The [manifest](evidence/issue-triage/manifest.json) binds the compact
receipts. Later issue changes belong in GitHub rather than rewriting this dated
triage snapshot.
